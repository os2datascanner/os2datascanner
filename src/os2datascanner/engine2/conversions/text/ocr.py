from tempfile import NamedTemporaryFile
from subprocess import run, PIPE, DEVNULL

from ..types import OutputType
from ..registry import conversion


def tesseract(path, **kwargs):
    result = run(
            ["tesseract", path, "stdout"],
            universal_newlines=True,
            stdout=PIPE,
            stderr=DEVNULL, **kwargs)
    if result.returncode == 0:
        return result.stdout.strip()
    else:
        return None


@conversion(OutputType.Text, "image/png", "image/jpeg")
def image_processor(r, **kwargs):
    with r.make_path() as p:
        return tesseract(p)


# Some ostensibly-supported image formats are handled badly by tesseract, so
# turn them into PNGs with ImageMagick's convert(1) command to make them more
# palatable
@conversion(OutputType.Text, "image/gif", "image/x-ms-bmp")
def intermediate_image_processor(r, **kwargs):
    with r.make_path() as p:
        with NamedTemporaryFile("rb", suffix=".png") as ntf:
            run(["convert", p, "png:{0}".format(ntf.name)],
                    check=True, **kwargs)
            return tesseract(ntf.name)
