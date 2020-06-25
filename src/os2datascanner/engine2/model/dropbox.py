from contextlib import contextmanager
from io import BytesIO

from urllib.parse import urlsplit

import dropbox
from .core import Source, Handle, FileResource
from .utilities import NamedTemporaryResource


class DropboxSource(Source):
    """See https://dropbox-sdk-python.readthedocs.io/en/latest/
    for implementation details for the dropbox api.
    """
    type_label = "dropbox"
    eq_properties = ("_token",)

    def __init__(self, token):
        # Consider using a list of tokens for access to multiple dropbox accounts.
        self._token = token
        self._user_account = None

    @property
    def token(self):
        return self._token

    @property
    def user_account(self):
        return self._user_account

    def _generate_state(self, sm):
        dbx = dropbox.Dropbox(self.token)
        yield dbx

    def censor(self):
        dbs = DropboxSource(self.token)
        dbs._user_account = self.user_account
        return dbs

    def handles(self, sm):
        dbx = sm.open(self)
        self._user_account = dbx.users_get_current_account()

        has_more = True
        cursor = None
        while has_more:
            if cursor is None:
                result = dbx.files_list_folder('', recursive=True,
                                               include_mounted_folders=True,
                                               include_non_downloadable_files=False
                                               )
            else:
                result = dbx.files_list_folder_continue(cursor)

            has_more = result.has_more
            cursor = result.cursor
            for entry in result.entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    yield DropboxHandle(self.user_account.email,
                                        self, entry.path_lower)

    @staticmethod
    @Source.url_handler("dropbox")
    def from_url(url):
        scheme, token, _, _, _ = urlsplit(url)
        return DropboxSource(token=token)

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "token": self._token
        })

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        return DropboxSource(obj["token"])


class DropboxResource(FileResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._dbx = None
        self._metadata = None

    def open_file(self):
        metadata, res = self.dbx.files_download(
            self.handle.relative_path)
        return res

    @property
    def dbx(self):
        if self._dbx is None:
            self._dbx = self._sm.open(
                self.handle.source)
        return self._dbx

    @property
    def metadata(self):
        if self._metadata is None:
            self._metadata = self.dbx.files_get_metadata(
                self.handle.relative_path)
        return self._metadata

    def get_size(self):
        return self.metadata.size

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
            yield BytesIO(res.content)

    def get_last_modified(self):
        return self.metadata.server_modified


class DropboxHandle(Handle):
    resource_type = DropboxResource
    type_label = "dropbox"

    def __init__(self, email, source, relpath):
        super().__init__(source, relpath)
        self.email = email

    @property
    def presentation(self):
        return "\"{0}\" (of account {1})".format(
            self.relative_path, self.email)

    @property
    def presentation_url(self):
        path = self.relative_path.split('/')
        return "https://www.dropbox.com/home{0}?preview={1}".format(
            '/'.join(path[:-1]), path[-1])

    def censor(self):
        return DropboxHandle(self.email, self.source.censor(),
                             self.relative_path)

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "email": self.email
        })

    @staticmethod
    @Handle.json_handler(type_label)
    def from_json_object(obj):
        return DropboxHandle(obj["email"], Source.from_json_object(obj["source"]), obj["path"])
