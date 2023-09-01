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
        command = ["gs", "-q",
                   *GS["_base_arguments"].split(),
                   f"-dPDFSETTINGS={GS['pdf_profile']}",
                   "-sOutputFile={0}".format(converted_path)]

        extra_args = GS["extra_args"]
        if extra_args:
            command.append(extra_args)

        command.append(path)

        run_custom(command,
                   timeout=GS["timeout"],
                   check=True, isolate_tmp=True)

        yield converted_path
