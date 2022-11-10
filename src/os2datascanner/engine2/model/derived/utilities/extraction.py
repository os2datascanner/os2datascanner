"""Utilities for extraction based on configuration dictionaries."""

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


class PDFImageFilter:
    '''
    Filter for removing duplicates and images that are too
    small to contain any text in PDF files.
    '''
    dimensions: (int, int) = (8, 8)

    def get_hash(self, filename):
        """
        Opens and calculates hash value for a file using
        the _checksum() function.
        """
        with open(filename, "rb") as fp:
            checksum = self._checksum(fp.read())
            return checksum.hexdigest()

    def __init__(self, checksum=md5, x_dim=8, y_dim=8):
        self.dimensions = (x_dim, y_dim)
        self._checksum = checksum

    def _image_too_small(self, image):
        """
        Checks whether an image is too small to contain
        any (OCR) readable text using dimensions specified
        in constructor.
        """
        return Image.open(image).size <= self.dimensions

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
        Also removes images that are too small to contain (OCR) readable text.
        """
        for paths in self._deduplicate(tmpdir).values():
            for dup in paths[1:]:
                dup.unlink()

        for image in Path(tmpdir).glob("*.png"):
            if self._image_too_small(image):
                image.unlink()

        return tmpdir
