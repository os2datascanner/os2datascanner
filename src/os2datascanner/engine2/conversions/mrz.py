from os2datascanner.utils.resources import get_resource_folder

from .types import OutputType
from .registry import conversion
from .text.ocr import tesseract


@conversion(OutputType.MRZ, "image/png", "image/jpeg")
def image_processor(r):
    with r.make_path() as p:
        return tesseract(p, "stdout",
                         "--oem", "1",
                         "--tessdata-dir", str(get_resource_folder() / "tessdata"),
                         "-l", "mrz")
