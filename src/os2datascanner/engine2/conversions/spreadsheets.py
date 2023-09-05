from .types import OutputType
from .registry import conversion
from ..model.core import Resource

# ROW_TYPE = "application/x.os2datascanner.spreadsheet.row"
SHEET_TYPE = "application/x.os2datascanner.spreadsheet"


@conversion(OutputType.Text, SHEET_TYPE)
def pandas_dataframe_processor(r: Resource, **kwargs):
    """
    Converts Sheets from Excel-like files to text using efficient pandas.Dataframes.
    """
    sheet_name = r.handle.relative_path
    return r._sm.open(r.handle.source).parse(sheet_name=sheet_name).to_string(na_rep='')
