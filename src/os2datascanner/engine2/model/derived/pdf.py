from os import listdir
import pypdf
import string
from tempfile import TemporaryDirectory

from ....utils.system_utilities import run_custom
from ... import settings as engine2_settings
from ..core import Handle, Source, Resource
from ..file import FilesystemResource
from .derived import DerivedSource
from .utilities.extraction import (should_skip_images,
                                   MD5DeduplicationFilter,
                                   TinyImageFilter)
from .utilities.ghostscript import gs_convert


PAGE_TYPE = "application/x.os2datascanner.pdf-page"
WHITESPACE_PLUS = string.whitespace + "\0"


def _open_pdf_wrapped(obj):
    reader = pypdf.PdfReader(obj)
    if reader.is_encrypted:
        # Some PDFs are "encrypted" with an empty password: give that a shot...
        if reader.decrypt("") == 0:  # the document has a real password
            raise pypdf.errors.PdfReadError("File cannot be decrypted")
    return reader


@Source.mime_handler("application/pdf")
class PDFSource(DerivedSource):
    type_label = "pdf"

    def _generate_state(self, sm):
        with self.handle.follow(sm).make_path() as path:
            # Explicitly download the file here for the sake of PDFPageSource,
            # which needs a local filesystem path to pass to pdftohtml
            if engine2_settings.ghostscript["enabled"]:
                yield from gs_convert(path)
            else:
                yield path

    def handles(self, sm):
        reader = _open_pdf_wrapped(sm.open(self))
        for i in range(1, len(reader.pages) + 1 if reader else 0):
            yield PDFPageHandle(self, str(i))


class PDFPageResource(Resource):
    def _generate_metadata(self):
        with self.handle.source.handle.follow(self._sm).make_stream() as fp:
            reader = _open_pdf_wrapped(fp)
            # Some PDF authoring tools helpfully stick null bytes into the
            # author field. Make sure we remove these
            author = reader.metadata.get("/Author", "").strip(WHITESPACE_PLUS)

        if author:
            yield "pdf-author", str(author)

    def check(self) -> bool:
        page = int(self.handle.relative_path)
        with self.handle.source._make_stream(self._sm) as fp:
            reader = _open_pdf_wrapped(fp)
            return page in range(1, len(reader.pages) + 1 if reader else 0)

    def compute_type(self):
        return PAGE_TYPE


@Handle.stock_json_handler("pdf-page")
class PDFPageHandle(Handle):
    type_label = "pdf-page"
    resource_type = PDFPageResource

    @property
    def presentation_name(self):
        return f"page {self.relative_path}"

    @property
    def presentation_place(self):
        return str(self.source.handle)

    def __str__(self):
        return f"{self.presentation_name} of {self.presentation_place}"

    @property
    def sort_key(self):
        "Return the file path of the document"
        return self.base_handle.sort_key

    def censor(self):
        return PDFPageHandle(self.source.censor(), self.relative_path)

    def guess_type(self):
        return PAGE_TYPE

    @classmethod
    def make(cls, handle: Handle, page: int):
        return PDFPageHandle(PDFSource(handle), str(page))


@Source.mime_handler(PAGE_TYPE)
class PDFPageSource(DerivedSource):
    type_label = "pdf-page"

    def _generate_state(self, sm):
        # As we produce FilesystemResources, we need to produce a cookie of the
        # same format as FilesystemSource: a filesystem directory in which to
        # interpret relative paths
        page = self.handle.relative_path
        path = sm.open(self.handle.source)
        with TemporaryDirectory() as outputdir:
            # Run pdftotext and pdfimages separately instead of running
            # pdftohtml. Not having to parse HTML is a big performance win by
            # itself, but what's even better is that pdfimages doesn't produce
            # uncountably many texture images for embedded vector graphics
            run_custom(
                    [
                            "pdftotext", "-q", "-nopgbrk", "-eol", "unix",
                            "-f", page, "-l", page, path,
                            "{0}/page.txt".format(outputdir)
                    ],
                    timeout=engine2_settings.subprocess["timeout"],
                    check=True, isolate_tmp=True)

            if not should_skip_images(sm.configuration):
                run_custom(
                    [
                            "pdfimages", "-q", "-png", "-j", "-f", page, "-l", page,
                            path, "{0}/image".format(outputdir)
                    ],
                    timeout=engine2_settings.subprocess["timeout"],
                    check=True, isolate_tmp=True)

            yield TinyImageFilter.apply(
                    MD5DeduplicationFilter.apply(outputdir))

    def handles(self, sm):
        for p in listdir(sm.open(self)):
            yield PDFObjectHandle(self, p)


class PDFObjectResource(FilesystemResource):
    def _generate_metadata(self):
        # Suppress the superclass implementation of this method -- generated
        # files have no interesting metadata
        yield from ()

    def get_last_modified(self):
        page_source: PDFPageSource = self.handle.source
        document_source: PDFSource = page_source.handle.source
        res = document_source.handle.follow(self._sm)
        return res.get_last_modified()


@Handle.stock_json_handler("pdf-object")
class PDFObjectHandle(Handle):
    type_label = "pdf-object"
    resource_type = PDFObjectResource

    def censor(self):
        return PDFObjectHandle(self.source.censor(), self.relative_path)

    @property
    def sort_key(self):
        return self.source.handle.sort_key

    @property
    def presentation_name(self):
        mime = self.guess_type()
        page = str(self.source.handle.presentation_name)
        container = self.source.handle.source.handle.presentation_name
        if mime.startswith("text/"):
            return f"text on {page} of {container}"
        elif mime.startswith("image/"):
            return f"image on {page} of {container}"
        else:
            return f"unknown object on {page} of {container}"

    @property
    def presentation_place(self):
        return str(self.source.handle.source.handle.presentation_place)

    @classmethod
    def make(cls, handle: Handle, page: int, name: str):
        return PDFObjectHandle(
                PDFPageSource(PDFPageHandle.make(handle, page)), name)
