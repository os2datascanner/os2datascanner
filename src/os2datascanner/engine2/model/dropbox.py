from contextlib import contextmanager
from io import BytesIO

import dropbox
from dropbox.files import GetMetadataError
from dropbox.dropbox import create_session
from dropbox.exceptions import ApiError
from .core import Source, Handle, FileResource


class DropboxSource(Source):
    """See https://dropbox-sdk-python.readthedocs.io/en/latest/
    for implementation details for the dropbox api.
    """
    type_label = "dropbox"
    eq_properties = ("_token",)

    def __init__(self, token):
        self._token = token

    @property
    def token(self):
        return self._token

    def _generate_state(self, sm):
        # Default values for create_session method. Uses requests lib session object.
        with create_session(max_connections=8, proxies=None) as session:
            yield dropbox.Dropbox(self.token, session=session)

    def censor(self):
        return DropboxSource(self.token)

    def handles(self, sm):
        dbx = sm.open(self)
        user_account = dbx.users_get_current_account()

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
                    yield DropboxHandle(self, entry.path_lower,
                                        user_account.email)

    def to_json_object(self):
        return dict(**super().to_json_object(), token=self._token)

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        return DropboxSource(obj["token"])


class DropboxResource(FileResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._metadata = None

    def check(self) -> bool:
        try:
            self.metadata
            return True
        except ApiError as e:
            if (isinstance(e.error, GetMetadataError)
                    and e.error.is_path()
                    and e.error.get_path().is_not_found()):
                return False
            # If we weren't able to conclude that the file is missing, then
            # reraise this exception
            raise

    def open_file(self):
        metadata, res = self._get_cookie().files_download(
            self.handle.relative_path)
        return res

    @property
    def metadata(self):
        if self._metadata is None:
            self._metadata = self._get_cookie().files_get_metadata(
                self.handle.relative_path)
        return self._metadata

    @contextmanager
    def make_stream(self):
        with self.open_file() as res:
            yield BytesIO(res.content)

    def get_last_modified(self):
        return self.metadata.server_modified

    def get_size(self):
        return self.metadata.size


class DropboxHandle(Handle):
    type_label = "dropbox"
    resource_type = DropboxResource

    def __init__(self, source, relpath, email):
        super().__init__(source, relpath)
        self.email = email

    @property
    def presentation_name(self):
        return self.name

    @property
    def presentation_place(self):
        # We don't need to show the filename here, just the path it resides in.
        return (f"folder {self.relative_path.removesuffix(self.name)}"
                f" of account {self.email}")

    @property
    def presentation_url(self):
        path = self.relative_path.split('/')
        return "https://www.dropbox.com/home{0}?preview={1}".format(
            '/'.join(path[:-1]), path[-1])

    @property
    def sort_key(self):
        """Returns a string to sort by formatted as:
        EMAIL/PATH
        """
        return f'{self.email}/{self.relative_path}'

    def censor(self):
        return DropboxHandle(self.source.censor(),
                             self.relative_path, self.email)

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "email": self.email
        })

    @staticmethod
    @Handle.json_handler(type_label)
    def from_json_object(obj):
        return DropboxHandle(Source.from_json_object(obj["source"]),
                             obj["path"], obj["email"])
