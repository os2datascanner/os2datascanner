from zipfile import ZipFile
from datetime import datetime
from contextlib import contextmanager

from ...conversions.types import OutputType
from ...conversions.utilities.navigable import make_values_navigable
from ..core import Source, Handle, FileResource
from .derived import DerivedSource


@Source.mime_handler("application/zip")
class ZipSource(DerivedSource):
    type_label = "zip"

    def handles(self, sm):
        zipfile = sm.open(self)
        for i in zipfile.infolist():
            if i.flag_bits & 0x1:
                # This file is encrypted, so all of ZipResource's operations
                # will fail. Skip over it
                # (XXX: is this preferable to raising an exception? For now, we
                # claim it is: an encrypted file we can't decrypt necessarily
                # isn't a sensitive data problem...)
                continue
            name = i.filename
            if not name[-1] == "/":
                yield ZipHandle(self, name)

    def _generate_state(self, sm):
        with self.handle.follow(sm).make_path() as r, ZipFile(str(r)) as zp:
            yield zp


zipinfo_attributes = (
        "CRC", "comment", "compress_size", "compress_type", "create_system",
        "create_version", "date_time", "external_attr", "extra",
        "extract_version", "file_size", "filename", "flag_bits",
        "header_offset", "internal_attr", "orig_filename", "reserved",
        "volume")


class ZipResource(FileResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._mr = None

    def _get_raw_info(self):
        return self._get_cookie().getinfo(str(self.handle.relative_path))

    def check(self) -> bool:
        try:
            self._get_raw_info()
            return True
        except KeyError:
            return False

    def unpack_info(self):
        if not self._mr:
            raw_info = self._get_raw_info()
            self._mr = make_values_navigable(
                    {k: getattr(raw_info, k) for k in zipinfo_attributes} |
                    {OutputType.LastModified: datetime(*raw_info.date_time)})
        return self._mr

    def get_size(self):
        return self.unpack_info()["file_size"]

    def get_last_modified(self):
        return self.unpack_info().get(OutputType.LastModified,
                                      super().get_last_modified())

    @contextmanager
    def make_stream(self):
        with self._get_cookie().open(self.handle.relative_path) as s:
            yield s


@Handle.stock_json_handler("zip")
class ZipHandle(Handle):
    type_label = "zip"
    resource_type = ZipResource

    @property
    def presentation_name(self):
        return self.relative_path

    @property
    def sort_key(self):
        return self.source.handle.sort_key

    @property
    def presentation_place(self):
        return str(self.source.handle)

    def censor(self):
        return ZipHandle(self.source.censor(), self.relative_path)
