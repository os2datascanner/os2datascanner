"""Utilities for extraction based on configuration dictionaries."""

from abc import ABC, abstractmethod
from pathlib import Path
from hashlib import md5
from PIL import Image


def should_skip_images(configuration: dict) -> bool:
    """
    Checks if the 'image/*' mime type is in 'skip_mime_types' for a
    configuration dict.
    """

    if configuration and configuration["skip_mime_types"]:
        return "image/*" in configuration["skip_mime_types"]

    return False


class Filter(ABC):
    """A Filter postprocesses the output directory of an external tool to make
    it more suitable for OS2datascanner."""

    @abstractmethod
    def apply(self, tmpdir: str) -> str:
        """Filters the content of the specified temporary folder before
        returning it."""
        pass


class DeduplicationFilter(Filter):
    """A filter for removing duplicate output files."""

    def get_hash(self, filename):
        """
        Opens and calculates hash value for a file using
        the _checksum() function.
        """
        with open(filename, "rb") as fp:
            checksum = self._checksum(fp.read())
            return checksum.hexdigest()

    def __init__(self, checksum):
        self._checksum = checksum

    def _deduplicate(self, folder):
        """
        Traverses a folder and returns a dictionary of all
        duplicate files using their hash values.
        """
        hashes = {}
        for filename in Path(folder).glob("*"):
            hash_val = self.get_hash(filename)
            hashes.setdefault(hash_val, []).append(filename)

        return hashes

    def apply(self, tmpdir):
        """
        Removes duplicate images if their hash values match.
        """
        for paths in self._deduplicate(tmpdir).values():
            for dup in paths[1:]:
                dup.unlink()

        return tmpdir


MD5DeduplicationFilter = DeduplicationFilter(checksum=md5)


class ImageSizeFilter(Filter):
    """A filter for removing images that are too small to contain any text."""
    def __init__(self, x_dim, y_dim):
        self.dimensions = (x_dim, y_dim)

    def _image_too_small(self, image):
        """
        Checks whether an image is too small to contain
        any (OCR) readable text using dimensions specified
        in constructor.
        """
        return Image.open(image).size <= self.dimensions

    def apply(self, tmpdir):
        """
        Removes images that are too small to contain (OCR) readable text.
        """

        for image in Path(tmpdir).glob("*.png"):
            if self._image_too_small(image):
                image.unlink()

        return tmpdir


TinyImageFilter = ImageSizeFilter(8, 8)
