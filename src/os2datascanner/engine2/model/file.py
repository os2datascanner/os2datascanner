from .core import Source, Handle, FileResource
import os.path
from pathlib import Path
from datetime import datetime
from dateutil.tz import gettz
from contextlib import contextmanager

from ..conversions.types import OutputType
from ..conversions.utilities.navigable import make_values_navigable


class FilesystemSource(Source):
    type_label = "file"

    def __init__(self, path):
        if not os.path.isabs(path):
            raise ValueError("Path {0} is not absolute".format(path))
        self._path = path

    @property
    def path(self):
        return self._path

    def handles(self, sm):
        pathlib_path = Path(self.path)
        for d in pathlib_path.glob("**"):
            try:
                for f in d.iterdir():
                    if f.is_file():
                        yield FilesystemHandle(
                            self, str(f.relative_to(pathlib_path)))
            except PermissionError:
                continue

    def _generate_state(self, sm):
        """Yields a path to the directory against which relative paths should
        be resolved.

        Other classes can also produce FilesystemResources if they have a
        compatible implementation of this function."""
        yield self.path

    def censor(self):
        return self

    def to_json_object(self):
        return dict(**super().to_json_object(), path=self.path)

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        return FilesystemSource(path=obj["path"])


stat_attributes = (
    "st_mode", "st_ino", "st_dev", "st_nlink", "st_uid",
    "st_gid", "st_size", "st_atime", "st_mtime", "st_ctime",)
#    "st_blksize", "st_blocks", "st_rdev", "st_flags",)


class FilesystemResource(FileResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._full_path = os.path.join(
                self._get_cookie(), self.handle.relative_path)
        self._mr = None

    def _generate_metadata(self):
        yield from super()._generate_metadata()
        yield "filesystem-owner-uid", self.unpack_stat()["st_uid"]

    def check(self) -> bool:
        return os.path.exists(self._full_path)

    def unpack_stat(self):
        if not self._mr:
            stat = os.stat(self._full_path)
            ts = datetime.fromtimestamp(stat.st_mtime, gettz())
            self._mr = make_values_navigable(
                    {attr: getattr(stat, attr) for attr in stat_attributes} |
                    {OutputType.LastModified: ts})
        return self._mr

    def get_size(self):
        return self.unpack_stat()["st_size"]

    def get_last_modified(self):
        return self.unpack_stat().setdefault(
                OutputType.LastModified, super().get_last_modified())

    @contextmanager
    def make_path(self):
        yield self._full_path


@Handle.stock_json_handler("file")
class FilesystemHandle(Handle):
    type_label = "file"
    resource_type = FilesystemResource

    @property
    def _full_path(self):
        return Path(self.source.path).joinpath(self.relative_path)

    @property
    def presentation_name(self):
        # return path, shouldn't need filename here
        return self._full_path.name

    @property
    def presentation_place(self):
        return str(self._full_path.parent)

    @property
    def sort_key(self):
        # return the full path including filename
        return str(self._full_path)

    def __str__(self):
        return str(self._full_path)

    def censor(self):
        return FilesystemHandle(self.source.censor(), self.relative_path)

    @classmethod
    def make_handle(cls, path):
        """Given a local filesystem path, returns a FilesystemHandle pointing
        at it."""
        head, tail = os.path.split(path)
        if not tail:
            raise ValueError("FilesystemHandles must have a non-empty Path")
        return FilesystemHandle(FilesystemSource(head), tail)
