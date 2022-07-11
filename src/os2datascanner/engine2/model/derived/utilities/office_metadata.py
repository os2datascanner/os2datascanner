from codecs import lookup as lookup_codec
import olefile
from zipfile import ZipFile, BadZipFile
from defusedxml.ElementTree import parse


def _codepage_to_codec(cp):
    """Retrieves the Python text codec corresponding to the given Windows
    codepage."""

    # In principle, this isn't hard: Python has lots of inbuilt codecs with
    # predictable names ("cp" followed by the string representation of the
    # codepage number), but...
    try:
        # ... codepage 65001 is an interesting special case: it's "whatever
        # WideCharToMultiByte returns when you ask it for UTF-8" (which is,
        # at least in some versions of Windows, known not to be proper UTF-8).
        # As a result, Python can only expose it as a codec on Windows! For
        # now, we treat it as normal UTF-8...
        if cp == 65001:
            return lookup_codec("utf-8")
        else:
            # All codepages must be represented with at least three digits:
            # this is only a problem for "cp037", but we may as well keep
            # things general
            return lookup_codec("cp{:03}".format(cp))
    except LookupError:
        return None


def _get_ole_metadata(fp):  # noqa: CCR001, too high cognitive complexity
    try:
        raw = olefile.OleFileIO(fp).get_metadata()

        # Check that the codepage attribute has been set. If it hasn't, then
        # the document didn't define a SummaryInformation stream and so doesn't
        # have the metadata we want
        if raw.codepage is not None:
            tidied = {}
            # The value we get here is a signed 16-bit quantity, even though
            # the file format specifies values up to 65001
            tidied["codepage"] = raw.codepage
            if tidied["codepage"] < 0:
                tidied["codepage"] += 65536
            codec = _codepage_to_codec(tidied["codepage"])
            if codec:
                for name in olefile.OleMetadata.SUMMARY_ATTRIBS:
                    if name in tidied:
                        continue
                    value = getattr(raw, name)
                    if isinstance(value, bytes):
                        value, _ = codec.decode(value)
                    tidied[name] = value
            return tidied
        else:
            return None
    # CodecInfo.decode raises a ValueError (or a subclass) on failure
    except (FileNotFoundError, ValueError):
        return None


def _process_zip_resource(fp, member, func):
    try:
        with ZipFile(fp, "r") as z, z.open(member, "r") as f:
            return func(f)
    except (KeyError, BadZipFile, FileNotFoundError):
        return None


def generate_opendocument_metadata(fp):
    f = _process_zip_resource(fp, "meta.xml", parse)
    if f:
        content = f.find(
                "{urn:oasis:names:tc:opendocument:"
                "xmlns:office:1.0}meta")
        if content:
            lm = content.find(
                    "{http://purl.org/dc/elements/1.1/}creator")
            if lm is not None and lm.text:
                yield "od-modifier", lm.text.strip()
            c = content.find(
                    "{urn:oasis:names:tc:opendocument:"
                    "xmlns:meta:1.0}initial-creator")
            if c is not None and c.text:
                yield "od-creator", c.text.strip()


def generate_ooxml_metadata(fp):
    f = _process_zip_resource(fp, "docProps/core.xml", parse)
    if f:
        lm = f.find(
                "{http://schemas.openxmlformats.org/package/"
                "2006/metadata/core-properties}lastModifiedBy")
        if lm is not None and lm.text:
            yield "ooxml-modifier", lm.text.strip()
        c = f.find("{http://purl.org/dc/elements/1.1/}creator")
        if c is not None and c.text:
            yield "ooxml-creator", c.text.strip()


def generate_ole_metadata(fp):
    m = _get_ole_metadata(fp)
    if m:
        if "last_saved_by" in m:
            yield "ole-modifier", m["last_saved_by"]
        if "author" in m:
            yield "ole-creator", m["author"]
