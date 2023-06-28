from ..core import Source
from .files import MSGraphDriveHandle
from .utilities import MSGraphSource


class MSGraphTeamsFilesSource(MSGraphSource):
    type_label = 'msgraph-teams-files'

    def __init__(self, client_id, tenant_id, client_secret,):
        super().__init__(client_id, tenant_id, client_secret)

    def _make_drive_handle(self, obj):
        owner_name = None
        if "owner" in obj:
            if "user" in obj["owner"]:
                owner_name = obj["owner"]["user"]["displayName"]
            elif "group" in obj:
                owner_name = obj["owner"]["group"]["displayName"]
        return MSGraphDriveHandle(self, obj["id"], obj["name"], owner_name)

    def handles(self, sm):
        teams = sm.open(self).get("/teams")
        for team in teams["value"]:
            channels = sm.open(self).get(f"teams/{team['id']}/channels")
            for channel in channels["value"]:
                files_folder = sm.open(self).get(
                    f"teams/{team['id']}/channels/{channel['id']}/filesFolder")
                match files_folder.get("parentReference"):
                    case {"driveId": drive_id}:
                        yield MSGraphDriveHandle(self, drive_id, files_folder["name"], None)
                    case _:
                        pass

    def to_json_object(self):
        return dict(
            **super().to_json_object(),
        )

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        return MSGraphTeamsFilesSource(
            client_id=obj["client_id"],
            tenant_id=obj["tenant_id"],
            client_secret=obj["client_secret"],
        )
