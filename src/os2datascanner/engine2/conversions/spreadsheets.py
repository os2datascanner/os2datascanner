from .types import OutputType
from .registry import conversion
from ..model.core import Resource

ROW_TYPE = "application/x.os2datascanner.spreadsheet.row"


@conversion(OutputType.Text, ROW_TYPE)
def pandas_dataframe_processor(r: Resource, **kwargs):
    """
    Converts Rows from Excel-like files to text using efficient pandas.Dataframes.
    """
    df = r._sm.open(r.handle.source)
    i = int(r.handle.relative_path)

    if i == 0:
        return df.columns.astype('string').str.cat(sep='\t', na_rep='\t')
    else:
        return df.iloc[i - 1].astype('string').str.cat(sep='\t', na_rep='\t')
