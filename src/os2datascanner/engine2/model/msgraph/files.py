from io import BytesIO
from contextlib import contextmanager

from ...conversions.utilities.results import SingleResult
from ..core import Handle, Source, Resource, FileResource
from ..derived.derived import DerivedSource
from ..utilities import NamedTemporaryResource
from .utilities import MSGraphSource, ignore_responses


class MSGraphFilesSource(MSGraphSource):
    type_label = "msgraph-files"

    def __init__(self, client_id, tenant_id, client_secret,
            site_drives=True, user_drives=True):
        super().__init__(client_id, tenant_id, client_secret)
        self._site_drives = site_drives
        self._user_drives = user_drives

    def _make_drive_handle(self, obj):
        owner_name = None
        if "owner" in obj:
            if "user" in obj["owner"]:
                owner_name = obj["owner"]["user"]["displayName"]
            elif "group" in obj:
                owner_name = obj["owner"]["group"]["displayName"]
        return MSGraphDriveHandle(self, obj["id"], obj["name"], owner_name)

    def handles(self, sm):
        if self._site_drives:
            with ignore_responses(404):
                drives = sm.open(self).get("sites/root/drives")
                for drive in drives["value"]:
                    yield self._make_drive_handle(drive)
        if self._user_drives:
            for user in self._list_users(sm)["value"]:
                pn = user["userPrincipalName"]
                with ignore_responses(404):
                    drive = sm.open(self).get("users/{0}/drive".format(pn))
                    yield self._make_drive_handle(drive)

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "site_drives": self._site_drives,
            "user_drives": self._user_drives
        })

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        return MSGraphFilesSource(
                client_id=obj["client_id"],
                tenant_id=obj["tenant_id"],
                client_secret=obj["client_secret"],
                site_drives=obj["site_drives"],
                user_drives=obj["user_drives"])


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
    def presentation(self):
        if self._owner_name:
            return "\"{0}\" (owned by {1})".format(
                    self._folder_name, self._owner_name)
        else:
            return "\"{0}\"".format(self._folder_name)

    def guess_type(self):
        return DUMMY_MIME

    def censor(self):
        return MSGraphDriveHandle(self.source.censor(), self.relative_path,
                self._folder_name, self._owner_name)

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "folder_name": self._folder_name,
            "owner_name": self._owner_name
        })

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
                    yield MSGraphFileHandle(
                            self, "/".join([] + components + [name]))
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
        return super().get_last_modified()

    def get_size(self):
        return SingleResult(None, 'size', 1024)

    @contextmanager
    def make_path(self):
        with NamedTemporaryResource(self.handle.name) as ntr:
            with ntr.open("wb") as res:
                with self.make_stream() as s:
                    res.write(s.read())
            yield ntr.get_path()

    @contextmanager
    def make_stream(self):
        response = self._get_cookie().get(
                self.make_object_path() + ":/content", json=False)
        with BytesIO(response) as fp:
            yield fp


@Handle.stock_json_handler("msgraph-drive-file")
class MSGraphFileHandle(Handle):
    type_label = "msgraph-drive-file"
    resource_type = MSGraphFileResource

    @property
    def presentation(self):
        return "{0} (in {1})".format(
                self.relative_path, self.source.handle.presentation)

    def censor(self):
        return MSGraphFileHandle(self.source.censor(), self.relative_path)
