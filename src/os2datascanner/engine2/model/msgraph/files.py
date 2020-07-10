from io import BytesIO
from contextlib import contextmanager

from ...conversions.utilities.results import SingleResult
from ..core import Handle, Source, Resource, FileResource
from ..derived.derived import DerivedSource
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
                site_drives=obj["site_drives"],
                user_drives=obj["user_drives"])


DUMMY_MIME = "application/vnd.os2.datascanner.graphdrive"


class MSGraphDriveResource(Resource):
    def compute_type(self):
        return DUMMY_MIME


class MSGraphDriveHandle(Handle):
    type_label = "msgraph-drive"
    resource_type = MSGraphDriveResource
    eq_properties = Handle.BASE_PROPERTIES

    def __init__(self, source, path, folder_name=None, owner_name=None):
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
