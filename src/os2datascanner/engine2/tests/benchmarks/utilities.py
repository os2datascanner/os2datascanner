"""Utilities for benchmarking"""
from pathlib import Path

DATA_ROOT = Path('/code/src/os2datascanner/engine2/tests/data/')

BIG_HTML = DATA_ROOT / 'html' / 'Midler-til-frivilligt-arbejde.html'


def read_content(path):
    """Helper function that reads some content into memory."""
    content = ""
    with path.open("r", encoding="utf-8",
                   errors="ignore") as file_pointer:
        content = file_pointer.read()

    return content


CONTENT = read_content(BIG_HTML)
