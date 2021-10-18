import binascii
from typing import Optional, Union
from base64 import b64decode, b64encode
from contextlib import closing

from os2datascanner.engine2.model.core import SourceManager, Source
from os2datascanner.engine2.conversions.types import OutputType
from os2datascanner.engine2.conversions import convert


def convert_data_to_text(
        content: bytes, mime: str, text_readable: bool = True
) -> Optional[bytes]:
    """Convert data to text representation

    The `content` shall be base64 encoded and `mime` represent the type of the
    decoded content. A list of registrered MIME converters can be found with
    `Source._Source__mime_handlers`

    With `text_readable = True`, `text` means any vaguely "human-readable" format
    like `text/html` or `text/xml`.
    """

    if not is_base64(content):
        content = b64encode(content)

    json = {
        "type": "data",
        "content": content,
        "mime": mime,
        "name": "data_conversion"
    }

    sm = SourceManager()
    source = Source.from_json_object(json)
    representation = None
    while source and representation is None:
        # It's important that the Source.handles() generator gets a chance to
        # clean up properly, which means using contextlib.closing() if it's not
        # going to run to completion
        with closing(source.handles(sm)) as generator:
            h = next(generator)
        r = h.follow(sm)

        # if content is human-readable(ie. "text/txt", "text/html" ,...), return it
        if r.compute_type().startswith("text/") and text_readable:
            with r.make_stream() as fp:
                return fp.read()

        source = None
        try:
            # The conversion will succeed for registrered converters
            # from os2datascanner.engine2.conversions import registry
            # registry.__converters
            representation = convert(r, OutputType.Text)
            return representation.value
        except KeyError:
            # Try to reinterpret the Handle as a new Source
            source = Source.from_handle(h)
            if not source:
                # Explicitly rethrow the error from convert() if we've hit a
                # dead end
                raise


def is_base64(sb: Union[str, bytes]) -> bool:
    """Test if a string or byte object appears to be Base64 encoded"""
    try:
        if isinstance(sb, str):
            # If there's any unicode here, an exception will be thrown and the
            # function will return false
            sb_bytes = bytes(sb, 'ascii')
        elif isinstance(sb, bytes):
            sb_bytes = sb
        else:
            raise ValueError("Argument must be string or bytes")

        b64decode(sb_bytes, validate=True)
        return True
    except binascii.Error:
        return False
