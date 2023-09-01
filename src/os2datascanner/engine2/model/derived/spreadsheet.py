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
ROW_TYPE = "application/x.os2datascanner.spreadsheet.row"

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


@Handle.stock_json_handler("ss-sheet")
class SpreadsheetSheetHandle(Handle):
    type_label = "ss-sheet"
    resource_type = SpreadsheetSheetResource

    @property
    def presentation_name(self) -> str:
        return f"sheet {self.relative_path}"

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


@Source.mime_handler(SHEET_TYPE)
class SpreadsheetSheetSource(DerivedSource):
    type_label = "ss-sheet"

    def _generate_state(self, sm):
        sheet_name = self.handle.relative_path
        yield sm.open(self.handle.source).parse(sheet_name=sheet_name)

    def handles(self, sm):
        df = sm.open(self)

        if not df.columns.empty:
            yield SpreadsheetRowHandle(self, 0)

        rows = df.shape[0] + 1
        for i in range(1, rows):
            yield SpreadsheetRowHandle(self, i)


class SpreadsheetRowResource(Resource):
    def _generate_metadata(self):
        yield from ()

    def get_last_modified(self):
        sheet_source = self.handle.source
        document_source = sheet_source.handle.source
        res = document_source.handle.follow(self._sm)
        return res.get_last_modified()

    def check(self) -> bool:
        i = int(self.handle.relative_path)
        rows = self._sm.open(self.handle.source).shape[0] + 1
        return 0 <= i < rows

    def compute_type(self):
        return ROW_TYPE


@Handle.stock_json_handler("ss-row")
class SpreadsheetRowHandle(Handle):
    type_label = "ss-row"
    resource_type = SpreadsheetRowResource

    def censor(self):
        return SpreadsheetRowHandle(self.source.censor(), self.relative_path)

    @property
    def sort_key(self) -> str:
        return self.source.handle.sort_key

    @property
    def presentation_name(self):
        row = int(self.relative_path)
        sheet = str(self.source.handle.presentation_name)
        container = self.source.handle.source.handle.presentation_name

        return f"row {row + 1} in {sheet} of {container}"

    @property
    def presentation_place(self) -> str:
        return str(self.source.handle.source.handle.presentation_place)

    def guess_type(self):
        return ROW_TYPE

    @classmethod
    def make(cls, handle: Handle, sheet_name, row):
        return SpreadsheetRowHandle(
            SpreadsheetSheetSource(SpreadsheetSheetHandle.make(handle, sheet_name)),
            row)
