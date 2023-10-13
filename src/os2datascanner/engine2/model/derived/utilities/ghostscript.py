"""
Contains utilities for compressing PDF files using GhostScript.
"""
import shlex

from tempfile import TemporaryDirectory

from .....utils.system_utilities import run_custom
from .... import settings as engine2_settings

GS = engine2_settings.ghostscript


def gs_convert(path):
    '''Convert to a compressed form using GhostScript (gs).'''
    with TemporaryDirectory() as outputdir:
        converted_path = "{0}/gs-temporary.pdf".format(outputdir)
        command = ["gs", "-q",
                   *shlex.split(GS["_base_arguments"]),
                   f"-dPDFSETTINGS={GS['pdf_profile']}",
                   "-sOutputFile={0}".format(converted_path)]

        extra_args = shlex.split(GS["extra_args"])
        if extra_args:
            command.extend(extra_args)

        command.append(path)

        run_custom(command,
                   timeout=GS["timeout"],
                   check=True, isolate_tmp=True)

        yield converted_path
