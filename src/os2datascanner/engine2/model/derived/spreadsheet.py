import logging
import magic
import pandas as pd

from ..core import Handle, Source, Resource
from .derived import DerivedSource
from .utilities import office_metadata


logger = logging.getLogger(__name__)

"""

"""

SHEET_TYPE = "application/x.os2datascanner.spreadsheet"

_actually_supported_types = [
    "application/vnd.ms-excel",
    "application/vnd.oasis.opendocument.spreadsheet",
    "application/vnd.openxmlformats-officedocument"
    ".spreadsheetml.sheet",
]


@Source.mime_handler(*_actually_supported_types)
class SpreadsheetSource(DerivedSource):
    type_label = "spreadsheet"

    def _generate_state(self, sm):
        with self.handle.follow(sm).make_path() as path:
            yield pd.ExcelFile(path)

    def handles(self, sm):
        for sheet_name in sm.open(self).sheet_names:
            yield SpreadsheetSheetHandle(self, sheet_name)


class SpreadsheetSheetResource(Resource):

    def _generate_metadata(self):
        parent = self.handle.source.handle.follow(self._sm)
        with parent.make_path() as fp:
            mime = magic.from_file(fp, mime=True)
            if mime == "application/vnd.ms-excel":
                yield from office_metadata.generate_ole_metadata(fp)
            elif mime.startswith("application/vnd.openxmlformats-officedocument."):
                yield from office_metadata.generate_ooxml_metadata(fp)
            elif mime.startswith("application/vnd.oasis.opendocument."):
                yield from office_metadata.generate_opendocument_metadata(fp)
        return super()._generate_metadata()

    def get_last_modified(self):
        parent_source = self.handle.source
        res = parent_source.handle.follow(self._sm)
        return res.get_last_modified()

    def check(self) -> bool:
        sheet_name = str(self.handle.relative_path)
        with self._sm.open(self.handle.source) as path:
            sheet_names = pd.ExcelFile(path).sheet_names
            return sheet_name in sheet_names

    def compute_type(self):
        return SHEET_TYPE


@Handle.stock_json_handler(SHEET_TYPE)
class SpreadsheetSheetHandle(Handle):
    type_label = SHEET_TYPE
    resource_type = SpreadsheetSheetResource

    @property
    def presentation_name(self) -> str:
        container = self.source.handle.presentation_name
        return f"sheet {self.relative_path} of {container}"

    @property
    def presentation_place(self) -> str:
        return str(self.source.handle)

    def __str__(self):
        return f"{self.presentation_name} of {self.presentation_place}"

    @property
    def sort_key(self) -> str:
        return self.base_handle.sort_key

    def censor(self):
        return SpreadsheetSheetHandle(self.source.censor(), self.relative_path)

    def guess_type(self):
        return SHEET_TYPE

    @classmethod
    def make(cls, handle: Handle, sheet_name: str):
        return SpreadsheetSheetHandle(SpreadsheetSource(handle), sheet_name)
