import json
from contextlib import contextmanager
from io import BytesIO
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
from .core import Source, Handle, FileResource
from ..conversions.utilities.results import SingleResult


class GoogleDriveSource(Source):
    """Implements Google Drive API using a service account.
    The organization must create a project, a service account, enable G Suite Domain-wide Delegation
     for the service account, download the credentials in .json format
     and enable the Google Drive API for the account to use this feature.

     Guidance to complete the above can be found at:
      https://support.google.com/a/answer/7378726?hl=en
     List of users in organization downloadable by admin from: https://admin.google.com/ac/users
    """

    type_label = "googledrive"

    def __init__(self, service_account_file, user_email):
        self._service_account_file = service_account_file
        self._user_email = user_email

    def _generate_state(self, source_manager):
        SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
        service_account_info = json.loads(self._service_account_file)
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=SCOPES).with_subject(self._user_email)

        service = build(serviceName='drive', version='v3', credentials=credentials)
        yield service

    def handles(self, sm):
        service = sm.open(self)
        page_token = None
        while True:
            files = service.files().list(q="mimeType !='application/vnd.google-apps.folder'",
                                         fields='nextPageToken, files(id, name, mimeType)',
                                         pageToken=page_token).execute()
            for file in files.get('files', []):
                yield GoogleDriveHandle(self, file.get('id'), name=file.get('name'))
            page_token = files.get('nextPageToken', None)
            if page_token is None:
                break

    # Censoring service account file info and user email.
    def censor(self):
        return GoogleDriveSource(None, self._user_email)

    def to_json_object(self):
        return dict(
            **super().to_json_object(),
            service_account_file=self._service_account_file,
            user_email=self._user_email,
        )

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        return GoogleDriveSource(obj["service_account_file"], obj["user_email"])


class GoogleDriveResource(FileResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._metadata = None

    def check(self) -> bool:
        try:
            self.metadata
            return True
        except HttpError as e:
            if e.resp.status in (404, 410,):
                return False
            raise

    @contextmanager
    def open_file(self):
        service = self._get_cookie()
        metadata = service.files().get(fileId=self.handle.relative_path).execute()
        # Export and download Google-type files to pdf
        if 'vnd.google-apps' in metadata.get('mimeType'):
            request = service.files().export_media(
                fileId=self.handle.relative_path,
                fields='files(id, name)',
                mimeType='application/pdf')
        # Download files where no export needed
        else:
            request = service.files().get_media(
                fileId=self.handle.relative_path,
                fields='files(id, name)')

        fh = BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()

        # Seek(0) points back to the beginning of the file as it appears to not do this by it self.
        fh.seek(0)
        yield fh

    @contextmanager
    def make_stream(self):
        with self.open_file() as res:
            yield res

    @property
    def metadata(self):
        if not self._metadata:
            self._metadata = self._get_cookie().files().get(
                    fileId=self.handle.relative_path,
                    fields='name, size, quotaBytesUsed').execute()

        return self._metadata

    def get_size(self):
        return SingleResult(None, 'size', self.metadata.get(
            'size', self.metadata.get('quotaBytesUsed')))


class GoogleDriveHandle(Handle):
    type_label = "googledrive"
    resource_type = GoogleDriveResource

    def __init__(self, source, relpath, name):
        super().__init__(source, relpath)
        self._name = name

    @property
    def presentation_name(self):
        return self._name

    @property
    def presentation_place(self):
        return (f"folder {self.relative_path.strip(' ')}"
                f" of account {self.source._user_email}")

    @property
    def name(self):
        return self.presentation_name

    @property
    def sort_key(self):
        """Returns a string to sort by formatted as:
        DOMAIN/ACCOUNT/PATH/FILE_NAME"""
        account, domain = self.source._user_email.split("@", 1)
        return f'{domain}/{account}/{self.relative_path}/{self._name}'

    def censor(self):
        return GoogleDriveHandle(self.source.censor(), relpath=self.relative_path, name=self._name)

    def to_json_object(self):
        return dict(**super().to_json_object(), name=self._name)

    @staticmethod
    @Handle.json_handler(type_label)
    def from_json_object(obj):
        return GoogleDriveHandle(Source.from_json_object(obj["source"]),
                                 obj["path"], obj.get('name'))
