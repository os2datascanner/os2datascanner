"""Utilities for extraction based on configuration dictionaries."""

import shutil
from os import listdir, remove
from pathlib import Path
from hashlib import md5
from tempfile import TemporaryDirectory
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


class PDFImageFilter:
    '''Filter for removing duplicates and images that are too
    small to contain any text in PDF files.'''
    dimensions: (int, int) = (8, 8)

    def checksum(self, filename):
        return md5(open(filename, "rb")).hexdigest()

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
        prefix = path.removesuffix('.pdf').split("/")[-1]
        print(f"path: {path}\nparent: {parent}\nprefix: {prefix}")

        with TemporaryDirectory() as outdir:
            run_custom(
                ["pdfimages", "-q", "-png", "-j", "-p", path, f"{outdir}/{prefix}"],
                timeout=engine2_settings.subprocess["timeout"],
                check=True, isolate_tmp=True)

            self.__filter(outdir)

            return outdir

    def __move_images(self, outdir, parent):
        for image in listdir(outdir):
            imagename = outdir.split('/').last()
            dest = parent + "/" + imagename
            print(f"dest: {dest}")
            shutil.move(outdir + "/" + image, dest)

        shutil.rmtree(outdir, ignore_errors=True)

    def __image_too_small(self, image):
        return Image.open(image).size <= self.dimensions

    def __filter(self, path) -> str:
        """Removes duplicate images if their md5sum matches.
        Also removes images that are too small to contain readable text."""
        hash_stack = []

        for item in listdir(path):
            if item.endswith(".png"):
                image = path + "/" + item
                checksum = self.checksum(image)

                if checksum in hash_stack:  # or self.__image_too_small(image):
                    print(f"removing: {image}")
                    remove(image)
                else:
                    hash_stack.append(checksum)

        print(f"hash_stack: {hash_stack}")
