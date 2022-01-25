from os import listdir
import PyPDF2
import string
from tempfile import TemporaryDirectory

from ....utils.system_utilities import run_custom
from ... import settings as engine2_settings
from ..core import Handle, Source, Resource
from ..file import FilesystemResource
from .derived import DerivedSource


PAGE_TYPE = "application/x.os2datascanner.pdf-page"
WHITESPACE_PLUS = string.whitespace + "\0"


def _open_pdf_wrapped(obj):
    reader = PyPDF2.PdfFileReader(obj)
    if reader.getIsEncrypted():
        # Some PDFs are "encrypted" with an empty password: give that a shot...
        try:
            if reader.decrypt("") == 0:  # the document has a real password
                reader = None
        except NotImplementedError:  # unsupported encryption algorithm
            reader = None
    return reader


@Source.mime_handler("application/pdf")
class PDFSource(DerivedSource):
    type_label = "pdf"

    def _generate_state(self, sm):
        with self.handle.follow(sm).make_path() as p:
            # Explicitly download the file here for the sake of PDFPageSource,
            # which needs a local filesystem path to pass to pdftohtml
            yield p

    def handles(self, sm):
        reader = _open_pdf_wrapped(sm.open(self))
        for i in range(1, reader.getNumPages() + 1 if reader else 0):
            yield PDFPageHandle(self, str(i))


class PDFPageResource(Resource):
    def _generate_metadata(self):
        with self.handle.source.handle.follow(self._sm).make_stream() as fp:
            reader = _open_pdf_wrapped(fp)
            info = reader.getDocumentInfo() if reader else None
            # Some PDF authoring tools helpfully stick null bytes into the
            # author field. Make sure we remove these
            author = (
                    info.get("/Author").strip(WHITESPACE_PLUS)
                    if info and info.get("/Author") else None)
        if author:
            yield "pdf-author", str(author)

    def check(self) -> bool:
        page = int(self.handle.relative_path)
        with self.handle.source._make_stream(self._sm) as fp:
            reader = _open_pdf_wrapped(fp)
            return page in range(1, reader.getNumPages() + 1 if reader else 0)

    def compute_type(self):
        return PAGE_TYPE


@Handle.stock_json_handler("pdf-page")
class PDFPageHandle(Handle):
    type_label = "pdf-page"
    resource_type = PDFPageResource

    @property
    def presentation(self):
        return self.source.handle.presentation

    @property
    def sort_key(self):
        "Return the file path of the document"
        return self.base_handle.sort_key

    @property
    def presentation_name(self):
        """Return the filename of the document or, if originating from a container, the
        filename of the container + (filename of document)"""
        if self.base_handle == self.source.handle:
            return self.base_handle.name + f" (page {self.relative_path})"

        # document originates from container
        return (
            self.base_handle.name +
            f" (file {self.source.handle.relative_path} (page {self.relative_path}))"
        )

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
            run_custom(
                    [
                            "pdfimages", "-q", "-png", "-f", page, "-l", page,
                            path, "{0}/image".format(outputdir)
                    ],
                    timeout=engine2_settings.subprocess["timeout"],
                    check=True, isolate_tmp=True)
            yield outputdir

    def handles(self, sm):
        for p in listdir(sm.open(self)):
            yield PDFObjectHandle(self, p)


class PDFObjectResource(FilesystemResource):
    def _generate_metadata(self):
        # Suppress the superclass implementation of this method -- generated
        # files have no interesting metadata
        yield from ()


@Handle.stock_json_handler("pdf-object")
class PDFObjectHandle(Handle):
    type_label = "pdf-object"
    resource_type = PDFObjectResource

    @property
    def presentation(self):
        return self.source.handle.presentation

    def censor(self):
        return PDFObjectHandle(self.source.censor(), self.relative_path)

    @property
    def sort_key(self):
        return self.source.handle.sort_key

    @property
    def presentation_name(self):
        "Return from the parent PDFPage handle"
        return self.source.handle.presentation_name

    @classmethod
    def make(cls, handle: Handle, page: int, name: str):
        return PDFObjectHandle(
                PDFPageSource(PDFPageHandle.make(handle, page)), name)
