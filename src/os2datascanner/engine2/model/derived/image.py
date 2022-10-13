from tempfile import TemporaryDirectory
from ..core import Source, Handle
from .derived import DerivedSource
from ..file import FilesystemResource
from ...conversions.text.ocr import tesseract


IMAGE_TYPE = "image/png"


@Source.mime_handler("image/png")
class ImageSource(DerivedSource):
    type_label = "image"

    def _generate_state(self, sm):
        with self.handle.follow(sm).make_path() as p:
            with TemporaryDirectory() as outdir:
                dest = outdir + p.replace('.png', '.txt').split('/').pop()
                print(f"dest: {dest}")
                tesseract(p, dest)
                yield dest

    def handles(self, sm):
        yield ImageTextHandle(self, sm.open(self))


class ImageTextResource(FilesystemResource):
    def _generate_metadata(self):
        yield from ()

    def get_last_modified(self):
        return None


@Handle.stock_json_handler("image")
class ImageTextHandle(Handle):
    type_label = "image"
    resource_type = ImageTextResource

    @property
    def presentation_name(self):
        return f"image {self.relative_path} in {self.source.handle}"

    @property
    def presentation_place(self):
        return str(self.source.handle)

    def censor(self):
        return ImageTextHandle(self.source.censor(), self.relative_path)

    def __str__(self):
        return self.presentation_name

    @property
    def sort_key(self):
        return self.base_handle.sort_key

    def guess_type(self):
        return IMAGE_TYPE
