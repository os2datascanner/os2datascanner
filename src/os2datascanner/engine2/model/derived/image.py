from ..core import Source
from .derived import DerivedSource


@Source.mime_handler("image/*")
class ImageSource(DerivedSource):
    type_label = "image"

    def _generate_state(self, sm):
        yield ""

    def handles(self, sm):
        return None
