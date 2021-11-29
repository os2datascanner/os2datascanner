from abc import ABC, abstractmethod
from sys import stderr
import magic
from traceback import print_exc

from os2datascanner.utils.system_utilities import time_now
from ...conversions.types import OutputType
from ...conversions.utilities.results import SingleResult


class Resource(ABC):
    """A Resource is a concrete embodiment of an object: it's the thing a
    Handle points to. If you have a Resource, then you have some way of getting
    to the data (and metadata) behind a Handle. Most kinds of Resource behave,
    or can behave, like files; these are represented by the FileResource
    subclass.

    Resources normally have functions that retrieve individual property values
    from an object. To minimise wasted computation, these values are wrapped in
    the SingleResult class, which allows them to include by reference other
    values that were computed at the same time.

    Resources are short-lived -- they should only be used when you actually
    need to get to content. As such, they are not serialisable."""
    def __init__(self, handle, sm):
        self._handle = handle
        self._sm = sm

    @property
    def handle(self):
        """Returns this Resource's Handle."""
        return self._handle

    @abstractmethod
    def check(self) -> bool:
        """Checks that this Resource is available by interacting with it in an
        unspecified, lightweight way. Returns True if the resource exists, and
        False if it doesn't.

        This method will only return False if the Resource cannot be accessed
        and is not expected to be accessible in future. In particular,
        transient issues like locked files or connectivity problems will not
        cause False to be returned."""

    def _generate_metadata(self):
        """Yields zero or more (key, value) pairs of metadata properties. (Keys
        must be strings, and values must be suitable for JSON
        serialisation.)"""
        # (This function is implemented as a generator to make error recovery
        # easier -- an unexpected error when extracting one metadata property
        # shouldn't result in all the others being dropped as well.)
        yield from ()

    def get_metadata(self):
        """Returns an object suitable for JSON serialisation that represents
        the metadata known for this object."""

        metadata = {}

        # Files in the real world can be malformed in a wide array of exciting
        # ways. To make sure we collect as much metadata as possible, even if
        # one of the later extraction stages does go wrong, store metadata
        # values as soon as they're produced by our helper function
        try:
            for k, v in self._generate_metadata():
                metadata[k] = v
        except Exception:
            print("warning: Resource.get_metadata:"
                  " continuing after unexpected exception", file=stderr)
            print_exc(file=stderr)

        if self.handle.source.handle:
            metadata.update(
                    self.handle.source.handle.follow(self._sm).get_metadata())

        return metadata

    def _get_cookie(self):
        """Returns the magic cookie produced when the Source behind this
        Resource's Handle is opened in the associated StateManager. (Note that
        each Source will only be opened once by a given StateManager.)"""
        return self._sm.open(self.handle.source)


class TimestampedResource(Resource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._lm_timestamp = None

    def get_last_modified(self):
        """Returns the last modification date of this TimestampedResource as a
        wrapped Python datetime.datetime; this may be used to decide whether or
        not a FileResource's content should be re-examined. Multiple calls to
        this method should normally return the same value.

        The default implementation of this method returns the time this
        method was first called on this TimestampedResource."""
        if not self._lm_timestamp:
            self._lm_timestamp = SingleResult(
                    None, OutputType.LastModified, time_now())
        return self._lm_timestamp


class FileResource(TimestampedResource):
    """A FileResource is a TimestampedResource that can be viewed as a file: a
    sequence of bytes with a size."""

    GENERIC_TYPES = ("application/zip", "application/CDFV2",
                     "text/plain", "text/html",)
    # The computed types that should be discarded in favour of the guessed
    # type, which is likely to be more specific. (Not used if the guessed type is
    # the completely generic value "application/octet-stream").

    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._lm_timestamp = None

    @abstractmethod
    def get_size(self):
        """Returns the wrapped number of bytes advertised as the download size
        of this FileResource's content. (Note that this is not necessarily the
        same as the *actual* size of that content: some Sources support
        transparent compression and decompression.)"""

    @abstractmethod
    def make_path(self):
        """Returns a context manager that, when entered, returns a path through
        which the content of this FileResource can be accessed until the
        context is exited. (Do not attempt to write to this path -- the result
        is undefined.)"""

    @abstractmethod
    def make_stream(self):
        """Returns a context manager that, when entered, returns a read-only
        Python stream through which the content of this FileResource can be
        accessed until the context is exited."""

    def _generate_metadata(self):
        yield "last-modified", OutputType.LastModified.encode_json_object(
                self.get_last_modified().value)

    def compute_type(self):
        """Guesses the type of this file, possibly examining its content in the
        process. By default, this is computed by giving libmagic the first 512
        bytes of the file."""
        guessed = self.handle.guess_type()
        with self.make_stream() as s:
            computed = magic.from_buffer(s.read(512), True)
        if guessed == computed:
            # If the guess and the computed values agree, then this isn't a
            # hard problem
            return computed
        elif (computed in self.GENERIC_TYPES
                and guessed != "application/octet-stream"):
            # If the first 512 bytes of the file look like a generic format and
            # the guessed type doesn't look completely contentless, then prefer
            # the guess
            return guessed
        else:
            # Otherwise, we prefer the computed type
            return computed
