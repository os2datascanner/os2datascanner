"""Utilities for extraction based on configuration dictionaries."""

import os
import shutil
from os import listdir, remove
from pathlib import Path
from hashlib import md5
from PIL import Image

from ...core.utilities import SourceManager
from .....utils.system_utilities import run_custom
from .... import settings as engine2_settings


def should_skip_images(configuration: dict) -> bool:
    """Checks if the 'image/*' mime type is in 'skip_mime_types' for a
    configuration dict."""

    if configuration and configuration["skip_mime_types"]:
        return "image/*" in configuration["skip_mime_types"]

    return False


def _calculate_md5(filename):
    """Calculates the md5 sum of a file 4kb at a time."""
    md5sum = md5()

    with open(filename, "rb") as filehandle:
        for chunk in iter(lambda: filehandle.read(4096), b""):
            md5sum.update(chunk)

    return md5sum.hexdigest()


class PDFImageFilter:
    '''Filter for removing duplicates and images that are too
    small to contain any text in PDF files.'''
    dimensions: (int, int) = (8, 8)
    checksum = _calculate_md5

    def __init__(self, source_manager, x_dim=8, y_dim=8):
        self.dimensions = (x_dim, y_dim)
        self._source_manager = source_manager

    @property
    def source_manager(self):
        '''Getter for _source_manager property.'''
        return self._source_manager

    @source_manager.setter
    def source_manager(self, value: SourceManager):
        '''Setter for _source_manager property. Does not allow
        None values.'''
        if value is not None:
            self._source_manager = value

    def apply(self, path) -> str:
        """Extracts all images for a pdf
        and puts it in a temporary output directory."""
        parent = str(Path(path).parent)
        outdir = parent + "/image"

        if not os.path.exists(outdir):
            os.makedirs(outdir)

        run_custom(
            ["pdfimages", "-q", "-png", "-j", path, f"{outdir}"],
            timeout=engine2_settings.subprocess["timeout"],
            check=True, isolate_tmp=True)

        self.__filter(outdir)
        self.__move_images(outdir, parent)

        return parent

    def __move_images(self, outdir, parent):
        for image in listdir(outdir):
            shutil.move(outdir + "/" + image, parent + "/" + image)

        shutil.rmtree(outdir)

    def __image_too_small(self, image):
        return Image.open(image).size <= self.dimensions

    def __filter(self, path) -> str:
        """Removes duplicate images if their md5sum matches.
        Also removes images that are too small to contain readable text."""
        hash_stack = []

        for item in listdir(path):
            if item.endswith(".png"):
                image = path + "/" + item
                checksum = _calculate_md5(image)

                if checksum in hash_stack or self.__image_too_small(image):
                    remove(image)
                else:
                    hash_stack.append(checksum)
