#!/usr/bin/env python3

from sys import stderr
from traceback import print_exc


def guess_responsible_party(handle, sm):
    """Returns a dictionary of labelled speculations about the person
    responsible for the (Resource at the) given Handle.

    These labels are highly likely to indicate the person responsible for the
    path, but are ambiguous and must be compared against other organisational
    data:

    * "od-modifier", the plaintext name of the last person to modify an
      OpenDocument document
    * "ooxml-modifier", the plaintext name of the last person to modify an
      Office Open XML document
    * "ole-modifier", the plaintext name of the last person to modify an OLE-
      based Microsoft Office document (.doc, .ppt, .xls, etc.)

    These labels are both ambiguous and less likely to indicate the person
    responsible for the path, but can be compared with other data to increase
    the confidence of the guess:

    * "od-creator", the plaintext name of the person who initially created an
      OpenDocument document
    * "ooxml-creator", the plaintext name of the person who initially created
      an Office Open XML document
    * "ole-creator", the plaintext name of the person who initially created an
      OLE-based Microsoft Office document
    * "pdf-author", the plaintext author name given in a PDF document's
      metadata

    These labels refer unambiguously to an individual person, but are less
    likely to indicate the person responsible for the file's content:

    * "filesystem-owner-sid", the SID of the owner of a CIFS filesystem object
    * "filesystem-owner-uid", the UID of the owner of a Unix filesystem object"""

    def _extract_guesses(handle, sm):
        if handle.is_synthetic:
            # Don't waste time extracting metadata from synthetic objects -- if
            # there is any metadata here, it'll be higher up the tree
            return

        yield from handle.follow(sm)._generate_metadata()

    guesses = {}
    # Files in the real world can be malformed in a wide array of exciting
    # ways. To make sure we collect as much metadata as possible, even if one
    # of the later extraction stages does go wrong, store metadata values as
    # soon as they're produced by our helper function
    try:
        for k, v in _extract_guesses(handle, sm):
            guesses[k] = v
    except Exception:
        print("warning: guess_responsible_party:"
                " continuing after unexpected exception", file=stderr)
        print_exc(file=stderr)

    if handle.source.handle:
        guesses.update(guess_responsible_party(handle.source.handle, sm))
    return guesses
