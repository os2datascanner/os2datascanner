"""
Contains utilities for compressing PDF files using GhostScript.
"""
from tempfile import TemporaryDirectory

from .....utils.system_utilities import run_custom
from .... import settings as engine2_settings

GS = engine2_settings.ghostscript


def gs_convert(path):
    '''Convert to a compressed form using GhostScript (gs).'''
    with TemporaryDirectory() as outputdir:
        converted_path = "{0}/gs-temporary.pdf".format(outputdir)
        run_custom(["gs", "-q",
                    GS["_base_arguments"],
                    f"-dPDFSETTINGS={GS['pdf_profile']}",
                    GS["extra_args"],
                    "-sOutputFile={0}".format(converted_path),
                    path],
                   timeout=GS["timeout"],
                   check=True, isolate_tmp=True)

        yield converted_path
