"""Utilities for benchmarking"""
from pathlib import Path

# Root folder for benchmarking data.
DATA_ROOT = Path('/code/src/os2datascanner/engine2/tests/benchmarks/data/')

# This is the html of the longest page on Wikipedia:
# "List of victims of the September 11 attacks"
# which is 2.3MB of plain text where
# irrelevant images and scripts have been removed.
BIG_HTML = DATA_ROOT / 'list_9_11_victims.html'


def read_content(path):
    """Helper function that reads some content into memory."""
    content = ""
    with path.open("r", encoding="utf-8",
                   errors="ignore") as file_pointer:
        content = file_pointer.read()

    return content


# Read the contents into memory. Yes, this will hurt.
HTML_CONTENT = read_content(BIG_HTML)
