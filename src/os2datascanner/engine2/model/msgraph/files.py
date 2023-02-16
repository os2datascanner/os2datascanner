from io import BytesIO
from contextlib import contextmanager
from dateutil.parser import isoparse
from ..core import Handle, Source, Resource, FileResource
from ..derived.derived import DerivedSource
from .utilities import MSGraphSource, warn_on_httperror


class MSGraphFilesSource(MSGraphSource):
    type_label = "msgraph-files"

    eq_properties = ("_site_drives", "_user_drives", "_userlist", "_tenant_id")

    def __init__(self, client_id, tenant_id, client_secret,
                 site_drives=True, user_drives=True, userlist=None):
        super().__init__(client_id, tenant_id, client_secret)
        self._site_drives = site_drives
        self._user_drives = user_drives
        self._userlist = userlist

    def _make_drive_handle(self, obj):
        owner_name = None
        if "owner" in obj:
            if "user" in obj["owner"]:
                owner_name = obj["owner"]["user"]["displayName"]
            elif "group" in obj:
                owner_name = obj["owner"]["group"]["displayName"]
        return MSGraphDriveHandle(self, obj["id"], obj["name"], owner_name)

    def handles(self, sm):  # noqa
        if self._site_drives:
            with warn_on_httperror("SharePoint drive check"):
                drives = sm.open(self).get("sites/root/drives")
                for drive in drives["value"]:
                    yield self._make_drive_handle(drive)
        if self._user_drives:
            if self._userlist is None:
                for user in self._list_users(sm):
                    pn = user["userPrincipalName"]
                    with warn_on_httperror(f"drive check for {pn}"):
                        drive = sm.open(self).get("users/{0}/drive".format(pn))
                        yield self._make_drive_handle(drive)

            else:
                for pn in self._userlist:
                    with warn_on_httperror(f"drive check for {pn}"):
                        drive = sm.open(self).get(f"users/{pn}/drive")
                        yield self._make_drive_handle(drive)

    def to_json_object(self):
        return dict(
            **super().to_json_object(),
            site_drives=self._site_drives,
            user_drives=self._user_drives,
            userlist=list(self._userlist) if self._userlist is not None else None
        )

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        userlist = obj.get("userlist")
        return MSGraphFilesSource(
                client_id=obj["client_id"],
                tenant_id=obj["tenant_id"],
                client_secret=obj["client_secret"],
                site_drives=obj["site_drives"],
                user_drives=obj["user_drives"],
                userlist=frozenset(userlist) if userlist is not None else None)


DUMMY_MIME = "application/vnd.os2.datascanner.graphdrive"


class MSGraphDriveResource(Resource):
    def check(self) -> bool:
        response = self._get_cookie().get_raw(
                "drives/{0}?$select=id".format(self.handle.relative_path))
        return response.status_code not in (404, 410,)

    def compute_type(self):
        return DUMMY_MIME


class MSGraphDriveHandle(Handle):
    type_label = "msgraph-drive"
    resource_type = MSGraphDriveResource
    eq_properties = Handle.BASE_PROPERTIES

    def __init__(self, source, path, folder_name, owner_name):
        super().__init__(source, path)
        self._folder_name = folder_name
        self._owner_name = owner_name

    @property
    def presentation_name(self):
        if self._owner_name:
            return "\"{0}\" (owned by {1})".format(
                    self._folder_name, self._owner_name)
        else:
            return "\"{0}\"".format(self._folder_name)

    @property
    def presentation_place(self):
        return "Office 365"

    def guess_type(self):
        return DUMMY_MIME

    def censor(self):
        return MSGraphDriveHandle(self.source.censor(), self.relative_path,
                                  self._folder_name, self._owner_name)

    def to_json_object(self):
        return dict(
            **super().to_json_object(),
            folder_name=self._folder_name,
            owner_name=self._owner_name,
        )

    @staticmethod
    @Handle.json_handler(type_label)
    def from_json_object(obj):
        return MSGraphDriveHandle(
                Source.from_json_object(obj["source"]), obj["path"],
                obj["folder_name"], obj["owner_name"])


@Source.mime_handler(DUMMY_MIME)
class MSGraphDriveSource(DerivedSource):
    type_label = "msgraph-drive"

    def _generate_state(self, sm):
        yield sm.open(self.handle.source)

    def handles(self, sm):

        def _explore_folder(components, folder):
            for obj in folder:
                name = obj["name"]
                if "file" in obj:
                    web_url = obj.get("webUrl", None)
                    yield MSGraphFileHandle(
                            self, "/".join([] + components + [name]), weblink=web_url)
                elif "folder" in obj:
                    subfolder = sm.open(self).get(
                            "/drives/{0}/items/{1}/children".format(
                                    self.handle.relative_path,
                                    obj["id"]))
                    yield from _explore_folder(
                            components + [name], subfolder["value"])
        root = sm.open(self).get(
                "drives/{0}/root/children".format(
                        self.handle.relative_path))["value"]
        yield from _explore_folder([], root)


class MSGraphFileResource(FileResource):
    def __init__(self, sm, handle):
        super().__init__(sm, handle)
        self._metadata = None

    def _generate_metadata(self):
        msgraph_metadata = self.get_file_metadata()
        yield "msgraph-owner-account", msgraph_metadata["createdBy"]["user"]["email"]
        yield "msgraph-last-modified-by", msgraph_metadata["lastModifiedBy"]["user"]["email"]
        yield "msgraph-last-modified-date-time", msgraph_metadata["lastModifiedDateTime"]
        yield from super()._generate_metadata()

    def check(self) -> bool:
        response = self._get_cookie().get_raw("drives/{0}/root:/{1}".format(
                self.handle.source.handle.relative_path,
                self.handle.relative_path))
        return response.status_code not in (404, 410,)

    def make_object_path(self):
        return "drives/{0}/root:/{1}".format(
                self.handle.source.handle.relative_path,
                self.handle.relative_path)

    def get_file_metadata(self):
        if not self._metadata:
            self._metadata = self._get_cookie().get(self.make_object_path())
        return self._metadata

    def get_last_modified(self):
        timestamp = self.get_file_metadata().get("lastModifiedDateTime")
        return isoparse(timestamp) if timestamp else None

    def get_size(self):
        return self.get_file_metadata()["size"]

    @contextmanager
    def make_stream(self):
        response = self._get_cookie().get(
                self.make_object_path() + ":/content", json=False)
        with BytesIO(response) as fp:
            yield fp


class MSGraphFileHandle(Handle):
    type_label = "msgraph-drive-file"
    resource_type = MSGraphFileResource

    def __init__(self, source, path, weblink=None):
        super().__init__(source, path)
        self._weblink = weblink
        self._path = path

    @property
    def path(self):
        return self._path

    @property
    def presentation_name(self):
        return str(self.name)

    @property
    def presentation_url(self):
        return self._weblink

    @property
    def presentation_place(self):
        return f"{str(self.path.removesuffix(self.name))} of {str(self.source.handle)}"

    def censor(self):
        return MSGraphFileHandle(self.source.censor(), self.relative_path, self._weblink)

    def to_json_object(self):
        return dict(
            **super().to_json_object(),
            weblink=self._weblink)

    @staticmethod
    @Handle.json_handler(type_label)
    def from_json_object(obj):
        return MSGraphFileHandle(
            Source.from_json_object(obj["source"]),
            obj["path"], obj.get("weblink"))
