from os import listdir
import magic
from tempfile import TemporaryDirectory
from subprocess import run, PIPE

from ... import settings as engine2_settings
from ..core import Handle, Source, Resource, SourceManager
from ..file import FilesystemResource
from .derived import DerivedSource


def libreoffice(*args):
    """Invokes LibreOffice with a fresh settings directory (which will be
    deleted as soon as the program finishes) and returns a CompletedProcess
    with both stdout and stderr captured."""
    with TemporaryDirectory() as settings:
        return run(
                ["libreoffice",
                        "-env:UserInstallation=file://{0}".format(settings),
                        *args], stdout=PIPE, stderr=PIPE,
                        timeout=engine2_settings.subprocess["timeout"],
                        check=True)


# These filter names come from /usr/lib/libreoffice/share/registry/PROG.xcd
_actually_supported_types = {
    "application/msword": "MS Word 97",
    "application/vnd.oasis.opendocument.text": "writer8",
    "application/vnd.ms-excel": "MS Excel 97",
    "application/vnd.oasis.opendocument.spreadsheet": "calc8",

    # XXX: libmagic usually can't detect OOXML files -- see the special
    # handling of these types in in LibreOfficeSource._generate_state
    "application/vnd.openxmlformats-officedocument"
            ".wordprocessingml.document": "Office Open XML Text",
    "application/vnd.openxmlformats-officedocument"
            ".spreadsheetml.sheet": "Calc Office Open XML"
}


@Source.mime_handler(
        "application/CDFV2",
        *_actually_supported_types.keys())
class LibreOfficeSource(DerivedSource):
    type_label = "lo"

    def _generate_state(self, sm):
        with self.handle.follow(sm).make_path() as p:
            # To filter out application/CDFV2 files that we don't actually
            # support, we compute the type of the whole file by calling
            # libmagic directly on the local filesystem path...
            best_mime_guess = magic.from_file(p, mime=True)
            # ... and, just to be extra safe, we tell LibreOffice what sort of
            # file we're passing it so it can do its own sanity checks
            filter_name = _actually_supported_types.get(best_mime_guess)

            # (... with special handling for OOXML files, since libmagic has
            # problems detecting them)
            if (not filter_name and best_mime_guess in
                    ("application/octet-stream", "application/zip")):
                mime_guess = self.handle.guess_type()
                if mime_guess.startswith(
                        "application/vnd.openxmlformats-officedocument."):
                    filter_name = _actually_supported_types.get(mime_guess)

            if filter_name is not None:
                with TemporaryDirectory() as outputdir:
                    result = libreoffice(
                            "--infilter={0}".format(filter_name),
                            "--convert-to", "html",
                            "--outdir", outputdir, p)
                    yield outputdir

    def handles(self, sm):
        for name in listdir(sm.open(self)):
            yield LibreOfficeObjectHandle(self, name)


@Handle.stock_json_handler("lo-object")
class LibreOfficeObjectHandle(Handle):
    type_label = "lo-object"
    resource_type = FilesystemResource

    # All LibreOfficeObjectHandles point at generated temporary files
    is_synthetic = True

    @property
    def presentation(self):
        return self.source.handle.presentation

    def censor(self):
        return LibreOfficeObjectHandle(
                self.source.censor(), self.relative_path)
