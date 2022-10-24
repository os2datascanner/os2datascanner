from io import BytesIO
from os import fsync
from base64 import b64decode, b64encode
from urllib.parse import unquote
from tempfile import NamedTemporaryFile
from contextlib import contextmanager
from typing import Tuple

from .core import Source, Handle, FileResource


@Source.url_handler('data')
class DataSource(Source):
    type_label = "data"

    def __init__(self, content, mime="application/octet-stream", name=None):
        self._content = content
        self._mime = mime
        self._name = name

    @property
    def mime(self):
        return self._mime

    @property
    def name(self):
        return self._name

    def handles(self, sm):
        if self._content:
            yield DataHandle(self, self.name or "file")
        else:
            raise ValueError("Can't explore a DataSource with no content")

    def _generate_state(self, sm):
        yield

    def censor(self):
        return DataSource(None, self._mime, self._name)

    def to_json_object(self):
        return dict(
            **super().to_json_object(),
            content=b64encode(self._content).decode(encoding="ascii") if self._content else None,
            mime=self.mime,
            name=self.name,
        )

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        content = obj["content"]
        return DataSource(
            b64decode(content) if content else None,
            obj["mime"], obj.get("name"))


class DataResource(FileResource):
    def check(self) -> bool:
        return True

    def get_size(self):
        return len(self.handle.source._content)

    def get_last_modified(self):
        # This is not redundant -- the superclass's default implementation is
        # an abstract method that can only be called explicitly
        return super().get_last_modified()

    @contextmanager
    def make_path(self):
        with NamedTemporaryFile() as fp, self.make_stream() as s:
            fp.write(s.read())
            fp.flush()
            fsync(fp.fileno())

            yield fp.name

    @contextmanager
    def make_stream(self):
        with BytesIO(self.handle.source._content) as s:
            yield s

    def compute_type(self):
        return self.handle.source.mime


@Handle.stock_json_handler("data")
class DataHandle(Handle):
    type_label = "data"
    resource_type = DataResource

    @property
    def name(self):
        if self.source.name:
            return self.source.name
        else:
            return super().name

    @property
    def sort_key(self):
        return self.name

    @property
    def presentation_name(self):
        if self.source.name:
            return f"{self.source.name}"
        else:
            return f"(anonymous file of type {self.guess_type()})"

    @property
    def presentation_place(self):
        return "(embedded)"

    def __str__(self):
        return f"{self.presentation_name} {self.presentation_place}"

    def censor(self):
        return DataHandle(self.source.censor(), self.relative_path)

    def guess_type(self):
        return self.source.mime


def unpack_data_url(url: str) -> Tuple[str, bytes]:
    """Unpack data from url-string

    URLs are of the form
         data:[mimetype][;base64],content

    If "mimetype" is absent, then it should be assumed to be "text/plain" (well,
    actually "text/plain;charset=US-ASCII", but we don't really support MIME
    type parameters).

    """
    _, rest = url.split(':', maxsplit=1)
    # The actual content is always after the first comma
    lead, content = rest.split(",", maxsplit=1)
    base64 = False
    mime = "text/plain"
    # The lead-in sequence is optional as a whole, and both of its parts are
    # also optional
    if lead:
        if lead.endswith(";base64"):
            base64 = True
            lead = lead[:-7]
        # Both Firefox and Chromium think that "data:;base64,VGVzdGluZwo=" is a
        # valid data: URL for a text/plain file, so make sure we don't
        # overwrite our default MIME type with emptiness
        if lead:
            mime = lead
    content = unquote(content)
    # Our input was a normal Python string, and we expect our content to be raw
    # bytes. b64decode produces those already, but a plain string must be
    # explicitly converted
    return mime, b64decode(content) if base64 else content.encode()
