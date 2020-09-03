from contextlib import contextmanager
from io import BytesIO
from urllib.parse import urlsplit
import oauth2client
import httplib2
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload



from .core import Source, Handle, FileResource
from .utilities import NamedTemporaryResource
from ..conversions.utilities.results import SingleResult
from ...projects.admin import settings


class GoogleDriveSource(Source):
    type_label = "googledrive"

    def __init__(self, access_code):
        self._access_code = access_code

    def _generate_state(self, source_manager):
        credentials = oauth2client.client.OAuth2Credentials(access_token=self._access_token,
                                                            client_id=settings.GOOGLEDRIVE_CLIENT_ID,
                                                            client_secret=settings.GOOGLEDRIVE_CLIENT_SECRET,
                                                            refresh_token=settings.GOOGLEDRIVE_REFRESH_TOKEN,
                                                            token_expiry=settings.GOOGLEDRIVE_TOKEN_EXPIRY,
                                                            token_uri=settings.GOOGLEDRIVE_TOKEN_URI,
                                                            user_agent=settings.GOOGLEDRIVE_USER_AGENT)
        #credentials = oauth2client.client.AccessTokenCredentials(self._access_token, 'user')
        http = httplib2.Http()
        http = credentials.authorize(http)
        service = build(serviceName='drive', version='v3', http=http)
        yield service

    def handles(self, sm):
        service = sm.open(self)
        page_token = None
        while True:
            files = service.files().list(q="mimeType !='application/vnd.google-apps.folder'",
                                         fields='nextPageToken, files(id, name, mimeType)',
                                         pageToken=page_token).execute()
            for file in files.get('files', []):
                yield GoogleDriveHandle(self, file.get('id'), file.get('name'))
            page_token = files.get('nextPageToken', None)
            if page_token is None:
                break

    def censor(self):
        return GoogleDriveSource(access_code=None)

    @staticmethod
    @Source.url_handler("googledrive")
    def from_url(url):
        scheme, token, _, _, _ = urlsplit(url)
        return GoogleDriveSource(access_code=token)

    def to_url(self):
        return "googledrive://{0}".format(self._access_code)

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "access_code": self._access_code
        })

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        return GoogleDriveSource(obj["access_code"])


class GoogleDriveResource(FileResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._metadata = None

    @contextmanager
    def open_file(self):
        service = self._get_cookie()
        metadata = service.files().get(fileId=self.handle.relative_path).execute()

        if 'vnd.google-apps' in metadata.get('mimeType'):
            request = service.files().export_media(fileId=self.handle.relative_path,
                                                   mimeType='application/pdf')
            fh = BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print("Export and Download %d%%." % int(status.progress() * 100))

        else:
            request = service.files().get_media(fileId=self.handle.relative_path)
            fh = BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print("Download %d%%." % int(status.progress() * 100))

        # Seek(0) points back to the beginning of the file as it appears to not do this by it self.
        fh.seek(0)
        yield fh

    @contextmanager
    def make_path(self):
        with NamedTemporaryResource(self.handle.name) as ntr:
            with ntr.open("wb") as res:
                with self.make_stream() as s:
                    res.write(s.read())
            yield ntr.get_path()

    @contextmanager
    def make_stream(self):
        with self.open_file() as res:
            yield res

    @property
    def metadata(self):
        self._metadata = self._get_cookie().files().get(
            fileId=self.handle.relative_path,
            fields='size, quotaBytesUsed').execute()

        return self._metadata

    def get_size(self):
        return SingleResult(None, 'size', self.metadata.get('size', self.metadata.get('quotaBytesUsed')))


class GoogleDriveHandle(Handle):
    type_label = "googledrive"
    resource_type = GoogleDriveResource

    def __init__(self, source, relpath, name=None):
        super().__init__(source, relpath)
        self._name = name or ''

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "name": self._name
        })

    @staticmethod
    @Handle.json_handler(type_label)
    def from_json_object(obj):
        return GoogleDriveHandle(Source.from_json_object(obj["source"]),
                             obj["path"], obj['name'])

    def censor(self):
        return GoogleDriveHandle(self.source.censor(), relpath=self.relative_path)

    @property
    def presentation(self):
        return self._name
