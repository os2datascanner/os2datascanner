import logging
import magic
from os import unlink, listdir, scandir
from tempfile import TemporaryDirectory
from contextlib import closing
from subprocess import DEVNULL

from ....utils.system_utilities import run_custom
from ... import settings as engine2_settings
from ..core import Handle, Source
from ..file import FilesystemResource
from .derived import DerivedSource
from .utilities import office_metadata
from .utilities.extraction import TinyImageFilter

logger = logging.getLogger(__name__)

"""Helper functions for converting Office documents

The document is converted to html using libreoffice. If some of the resulting html
files are larger than @size_treshold, specified in the config file under
We use LibreOffice to convert Office documents to HTML versions that we can
then process into plain text. (Just asking directly for a plain text version
doesn't give us any of the embedded resources, which we also need to scan.)

When the resulting HTML files are too big (according to the
"model.libreoffice.size_threshold" preference), they're automatically deleted,
and LibreOffice is invoked again to produce a simpler plain text version.

Later, the html is converted to the representation needed by the rule thats is being
applied. This is done by the more generic convertes found in the
src/engine2/conversions folder

"""


def libreoffice(*args):
    """Invokes LibreOffice with a fresh settings directory (which will be
    deleted as soon as the program finishes) and returns a CompletedProcess
    with both stdout and stderr captured."""
    with TemporaryDirectory() as tmpdir:
        return run_custom(
                ["libreoffice",
                 "-env:UserInstallation=file://{0}".format(tmpdir),
                 *args],
                stdout=DEVNULL, stderr=DEVNULL, check=True,
                timeout=engine2_settings.subprocess["timeout"],
                kill_group=True, isolate_tmp=True,)


# The fallback CSV filter, used when HTML representations of spreadsheets are
# too big.
# CSV handling requres a really complicated filter name which includes some
# options. The syntax is
# (filtername):'field sep','text delim','char set', ...[more options]
# "9" means "separate fields with U+0009 CHARACTER TABULATION", "34" means "wrap
# string values in U+0022 QUOTATION MARK", and "76" means UTF-8 output
# The fields are described here
# https://wiki.openoffice.org/wiki/Documentation/DevGuide/Spreadsheets/Filter_Options#Filter_Options_for_the_CSV_Filter
# The filter name is found by looking at "oor:name" inside the relevant .xcu file
# https://cgit.freedesktop.org/libreoffice/core/tree/filter/source/config/fragments/filters
# The format of --convert-to is then <TargetFileExtension>:<NameOfFilter>:<Options>
# As pr. LibreOffice 7.2, the 12th numeric parameter determines behaviour when encountering
# spreadsheets with multiple sheets/tabs. (-1 will convert each tab to a csv file named accordingly)
__csv = "csv:Text - txt - csv (StarCalc):9,34,76,UTF8,1,,0,false,true,false,false,-1"


# Filter name keys come from /usr/lib/libreoffice/share/registry/PROG.xcd;
# OR from
# https://help.libreoffice.org/latest/ro/text/shared/guide/convertfilters.html
# The dictionary's values specify the input filter name and a fallback output
# filter to be used after HTML processing
_actually_supported_types = {
    "application/msword": ("MS Word 97", "txt", True),
    "application/vnd.oasis.opendocument.text": ("writer8", "txt", True),
    "application/vnd.ms-excel": ("MS Excel 97", __csv, False),
    "application/vnd.oasis.opendocument.spreadsheet": ("calc8", __csv, False),

    # XXX: libmagic usually can't detect OOXML files -- see the special
    # handling of these types in in LibreOfficeSource._generate_state
    "application/vnd.openxmlformats-officedocument"
    ".wordprocessingml.document": ("Office Open XML Text", "txt", True),
    "application/vnd.openxmlformats-officedocument"
    ".spreadsheetml.sheet": ("Calc Office Open XML", __csv, False)
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
                    logger.info(f"{entry.name} is larger than {size_threshold}. "
                                "Replacing it with a simpler representation "
                                f"[{output_filter}]")
                    # --headless Starts in "headless mode"
                    # which allows using the application without GUI.
                    # This special mode can be used when the application is controlled
                    # by external clients via the API.
                    libreoffice(
                            "--infilter={0}".format(input_filter),
                            "--convert-to", output_filter,
                            "--outdir", output_directory, input_file,
                            "--headless")
                    unlink(entry.path)
                break


class UnrecognisedFormatError(LookupError):
    pass


@Source.mime_handler(
        "application/CDFV2",
        # LibreOffice is in the unusual position of supporting a few MIME types
        # for which it's no longer responsible *and* of performing sanity
        # checks to make sure that its input files' types are supported. To
        # make the older references work, we need to distinguish between
        # "supported and claimed" and "supported but not claimed"
        *(k for k, (_, _, should_handle)
          in _actually_supported_types.items()
          if should_handle))
class LibreOfficeSource(DerivedSource):
    type_label = "lo"

    def _generate_state(self, sm):
        with self.handle.follow(sm).make_path() as p:
            # Office files are special instances of generic formats (CDFV2 for
            # old Microsoft Office files and Zip for everything else). To make
            # sure that we get a MIME guess we can actually use, we need to
            # operate on the whole file...
            best_mime_guess = magic.from_file(p, mime=True)
            # ... and, just to be extra safe, we tell LibreOffice what sort of
            # file we're passing it so it can do its own sanity checks
            filter_name, backup_filter, _ = _actually_supported_types.get(
                    best_mime_guess, (None, None, None))

            # (... although, if that produced something totally generic, we
            # should have one last shot based on the name)
            if (not filter_name and best_mime_guess in
                    ("application/octet-stream", "application/zip")):
                mime_guess = self.handle.guess_type()
                filter_name, backup_filter, _ = _actually_supported_types.get(
                        mime_guess, (None, None, None))

            if filter_name is None:
                raise UnrecognisedFormatError(
                        str(self.handle), best_mime_guess)

            with TemporaryDirectory() as outputdir:
                libreoffice(
                        "--infilter={0}".format(filter_name),
                        "--convert-to", "html",
                        "--outdir", outputdir, p)
                if backup_filter:
                    _replace_large_html(
                            filter_name, p, backup_filter, outputdir)
                yield TinyImageFilter.apply(outputdir)

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
            elif mime.startswith("application/vnd.openxmlformats-officedocument."):
                yield from office_metadata.generate_ooxml_metadata(fp)
            elif mime.startswith(
                    "application/vnd.oasis.opendocument."):
                yield from office_metadata.generate_opendocument_metadata(fp)
        # We deliberately don't yield from the superclass implementation --
        # filesystem metadata is useless for a generated file

    def get_last_modified(self):
        parent_source = self.handle.source
        res = parent_source.handle.follow(self._sm)
        return res.get_last_modified()


@Handle.stock_json_handler("lo-object")
class LibreOfficeObjectHandle(Handle):
    type_label = "lo-object"
    resource_type = LibreOfficeObjectResource

    @property
    def presentation_name(self):
        mime = self.guess_type()
        container = self.source.handle.presentation_name
        if mime.startswith("text/"):
            return f"text of {container}"
        elif mime.startswith("image/"):
            return f"image in {container}"
        else:
            return f"unknown object in {container}"

    @property
    def presentation_place(self):
        return self.source.handle.presentation_place

    def censor(self):
        return LibreOfficeObjectHandle(self.source.censor(), self.relative_path)

    @property
    def sort_key(self):
        "Return the file path of the document"
        return self.base_handle.sort_key
