from os import unlink, listdir, scandir
import magic
from tempfile import TemporaryDirectory
from contextlib import closing
from subprocess import DEVNULL

from ....utils.system_utilities import run_custom
from ... import settings as engine2_settings
from ..core import Handle, Source, Resource, SourceManager
from ..file import FilesystemResource
from .derived import DerivedSource
from .utilities import office_metadata


def libreoffice(*args):
    """Invokes LibreOffice with a fresh settings directory (which will be
    deleted as soon as the program finishes) and returns a CompletedProcess
    with both stdout and stderr captured."""
    with TemporaryDirectory() as settings:
        return run_custom(
                ["libreoffice",
                        "-env:UserInstallation=file://{0}".format(settings),
                        *args],
                stdout=DEVNULL, stderr=DEVNULL, kill_group=True,
                timeout=engine2_settings.subprocess["timeout"], check=True)


# CSV handling requres a really complicated filter name which includes some
# options. "9" means "separate fields with U+0009 CHARACTER TABULATION", "34"
# means "wrap string values in U+0022 QUOTATION MARK", and "76" means UTF-8
# output
__csv = "csv:Text - txt - csv (StarCalc):9,34,76"


# Filter name keys come from /usr/lib/libreoffice/share/registry/PROG.xcd;
# the dictionary's values specify the input filter name and a fallback output
# filter to be used after HTML processing
_actually_supported_types = {
    "application/msword": ("MS Word 97", "txt"),
    "application/vnd.oasis.opendocument.text": ("writer8", "txt"),
    "application/vnd.ms-excel": ("MS Excel 97", __csv),
    "application/vnd.oasis.opendocument.spreadsheet": ("calc8", __csv),

    # XXX: libmagic usually can't detect OOXML files -- see the special
    # handling of these types in in LibreOfficeSource._generate_state
    "application/vnd.openxmlformats-officedocument"
            ".wordprocessingml.document": ("Office Open XML Text", "txt"),
    "application/vnd.openxmlformats-officedocument"
            ".spreadsheetml.sheet": ("Calc Office Open XML", __csv)
}


def _replace_large_html(
        input_filter, input_file, output_filter, output_directory):
    """If one of the files in the provided is an excessively large HTML file,
    deletes it and replaces it with a simpler representation of the input
    file."""
    size_threshold = engine2_settings.model["libreoffice"]["size_threshold"]
    with closing(scandir(output_directory)) as file_iterator:
        for entry in file_iterator:
            if entry.name.endswith(".html"):
                if entry.stat().st_size >= size_threshold:
                    libreoffice(
                            "--infilter={0}".format(input_filter),
                            "--convert-to", output_filter,
                            "--outdir", output_directory, input_file)
                    unlink(entry.path)
                break



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
            filter_name, backup_filter = _actually_supported_types.get(
                    best_mime_guess, (None, None))

            # (... with special handling for OOXML files, since libmagic has
            # problems detecting them)
            if (not filter_name and best_mime_guess in
                    ("application/octet-stream", "application/zip")):
                mime_guess = self.handle.guess_type()
                if mime_guess.startswith(
                        "application/vnd.openxmlformats-officedocument."):
                    filter_name = _actually_supported_types.get(mime_guess)
            if filter_name is None:
                return

            with TemporaryDirectory() as outputdir:
                libreoffice(
                        "--infilter={0}".format(filter_name),
                        "--convert-to", "html",
                        "--outdir", outputdir, p)
                if backup_filter:
                    _replace_large_html(
                            filter_name, p, backup_filter, outputdir)
                yield outputdir

    def handles(self, sm):
        for name in listdir(sm.open(self)):
            yield LibreOfficeObjectHandle(self, name)


class LibreOfficeObjectResource(FilesystemResource):
    def _generate_metadata(self):
        parent = self.handle.source.handle.follow(self._sm)
        # Ideally we'd say parent.make_stream() here instead, but libmagic
        # can't cope with Python file-like objects -- it needs either a file
        # descriptor (which we can't guarantee) or a filesystem path
        with parent.make_path() as fp:
            mime = magic.from_file(fp, mime=True)
            if mime in ("application/msword", "application/vnd.ms-excel",
                    "application/vnd.ms-powerpoint",):
                yield from office_metadata.generate_ole_metadata(fp)
            elif mime.startswith(
                    "application/vnd.openxmlformats-officedocument."):
                yield from office_metadata.generate_ooxml_metadata(fp)
            elif mime.startswith(
                    "application/vnd.oasis.opendocument."):
                yield from office_metadata.generate_opendocument_metadata(fp)
        # We deliberately don't yield from the superclass implementation --
        # filesystem metadata is useless for a generated file


@Handle.stock_json_handler("lo-object")
class LibreOfficeObjectHandle(Handle):
    type_label = "lo-object"
    resource_type = LibreOfficeObjectResource

    @property
    def presentation(self):
        return self.source.handle.presentation

    def censor(self):
        return LibreOfficeObjectHandle(
                self.source.censor(), self.relative_path)
