from os import listdir
import pdfrw
from tempfile import TemporaryDirectory
from subprocess import run

from ... import settings as engine2_settings
from ..core import Handle, Source, Resource, SourceManager
from ..file import FilesystemResource
from .derived import DerivedSource


PAGE_TYPE = "application/x.os2datascanner.pdf-page"


@Source.mime_handler("application/pdf")
class PDFSource(DerivedSource):
    type_label = "pdf"

    def _generate_state(self, sm):
        with self.handle.follow(sm).make_path() as p:
            # Explicitly download the file here for the sake of PDFPageSource,
            # which needs a local filesystem path to pass to pdftohtml
            yield p

    def handles(self, sm):
        reader = pdfrw.PdfReader(sm.open(self))
        for i in range(1, len(reader.pages) + 1):
            yield PDFPageHandle(self, str(i))


class PDFPageResource(Resource):
    def check(self) -> bool:
        page = int(self.handle.relative_path)
        with self.handle.source.handle.follow(self._sm).make_stream() as fp:
            reader = pdfrw.PdfReader(fp)
            return page in range(1, len(reader.pages) + 1)

    def compute_type(self):
        return PAGE_TYPE


@Handle.stock_json_handler("pdf-page")
class PDFPageHandle(Handle):
    type_label = "pdf-page"
    resource_type = PDFPageResource

    # A PDFPageHandle is an internal reference to a fragment of a document
    is_synthetic = True

    @property
    def presentation(self):
        return "page {0} of {1}".format(self.relative_path, self.source.handle)

    def censor(self):
        return PDFPageHandle(self.source.censor(), self.relative_path)

    def guess_type(self):
        return PAGE_TYPE


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
            run(["pdftotext",
                    "-q", "-nopgbrk",
                    "-eol", "unix",
                    "-f", page, "-l", page,
                    path, "{0}/page.txt".format(outputdir)],
                    timeout=engine2_settings.subprocess["timeout"],
                    check=True)
            run(["pdfimages",
                    "-q", "-all",
                    "-f", page, "-l", page,
                    path, "{0}/image".format(outputdir)],
                    timeout=engine2_settings.subprocess["timeout"],
                    check=True)
            yield outputdir

    def handles(self, sm):
        for p in listdir(sm.open(self)):
            yield PDFObjectHandle(self, p)


@Handle.stock_json_handler("pdf-object")
class PDFObjectHandle(Handle):
    type_label = "pdf-object"
    resource_type = FilesystemResource

    # All PDFObjectHandles point at generated temporary files
    # (XXX: we don't care about this metadata at the moment, so this isn't an
    # issue, but what if an extracted file is nevertheless a real file and
    # carries useful metadata, like a JPEG image with XMP properties?)
    is_synthetic = True

    @property
    def presentation(self):
        return self.source.handle.presentation

    def censor(self):
        return PDFObjectHandle(self.source.censor(), self.relative_path)
