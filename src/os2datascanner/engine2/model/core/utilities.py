import structlog

logger = structlog.get_logger(__name__)


class _SourceDescriptor:
    def __init__(self, *, source, parent=None):
        self.source = source
        self.parent = parent
        self.generator = None
        self.cookie = None
        self.children = []


class SourceManager:
    """A SourceManager is responsible for tracking all of the state associated
    with one or more Sources. Operations on Sources and Handles that require
    persistent state use a SourceManager to keep track of that state.

    When used as a context manager, a SourceManager will automatically clean up
    all of the state that it's been tracking at context exit time. This might
    mean, for example, automatically disconnecting from remote resources,
    unmounting drives, or closing file handles.

    SourceManagers have an optional property called their "width", which is the
    number of open sub-Sources that can be below a Source at any given time.
    For example, a SourceManager with a width of 3 can have three open
    connections, each of which can have three open files, each of which can
    have three open pages, and so on. When opening a new Source would cause
    the width to be exceeded, the least-recently-used Source at that level will
    be closed. (Opening an already-open Source marks it as the most recently
    used one.)

    SourceManagers track arbitrary state objects and so are not usefully
    serialisable or shareable."""

    def __init__(self, *, width=3, configuration: dict = None):
        """Initialises this SourceManager."""
        self._width = width

        self._opened = {}
        self._opening = []

        # A synthetic _SourceDescriptor used as the parent for top-level
        # objects
        self._top = _SourceDescriptor(source=None)

        # Configuration obtained from a ScanSpec
        self.configuration = configuration

    def _make_descriptor(self, source):
        return self._opened.setdefault(
                source, _SourceDescriptor(source=source, parent=self._top))

    def _reparent(self, child_d, parent_d):
        if (child_d.parent
                and child_d in child_d.parent.children):
            child_d.parent.children.remove(child_d)
        # Don't reparent to the dummy top element -- this case happens if the
        # path is incomplete, and actually doing it will throw away the
        # complete path
        if parent_d != self._top:
            child_d.parent = parent_d
        child_d.parent.children.append(child_d)

        # If the new parent can't have any more open Sources, then close the
        # least-recently-used one
        if self._width and len(child_d.parent.children) > self._width:
            self.close(child_d.parent.children[0].source)

        # Also perform a dummy reparent operation all the way up the hierarchy
        # to ensure that the rightmost child is always the most recently used
        # one
        if parent_d.parent:
            self._reparent(parent_d, parent_d.parent)

    def _register_path(self, path):
        """Registers a path, a partial or complete reverse-ordered list of
        Sources of the form [child, parent, grandparent, ...], with this
        SourceManager. Paths are used to free resources in a sensible order.

        Paths are an internal implementation detail, and this function is
        intended for use only by SourceManager.open."""
        path = list(reversed(path))
        parent_d = self._top
        for child in path:
            child_d = self._make_descriptor(child)
            self._reparent(child_d, parent_d)
            parent_d = child_d
        return parent_d

    def open(self, source):
        """Returns the cookie returned by opening the given Source."""
        self._opening.append(source)
        self._register_path(self._opening)
        try:
            # Calling _make_descriptor will add this source to the open list if
            # it's not already there
            desc = self._make_descriptor(source)
            if not desc.cookie:
                desc.generator = source._generate_state(self)
                try:
                    desc.cookie = next(desc.generator)
                except BaseException:
                    self.close(source)
                    raise
            logger.debug(
                    "SourceManager.open",
                    source=source, cookie=desc.cookie)
            return desc.cookie
        finally:
            self._opening = self._opening[:-1]

    def close(self, source):
        """Closes a Source opened in this SourceManager, in the process closing
        all other open Sources that depend upon it."""
        logger.debug(
                "SourceManager.close",
                source=source)
        if source in self._opened:
            desc = self._opened[source]

            if desc.children:
                # Clear up descendants of this Source
                for child in desc.children.copy():
                    self.close(child.source)
                desc.children.clear()

            # Clear up the state and the generator
            if desc.cookie:
                desc.cookie = None
            if desc.generator:
                try:
                    desc.generator.close()
                except Exception:
                    logger.warning(
                            "Bug! Closing _generate_state failed.",
                            source=type(source).__name__,
                            exc_info=True)

            if desc.parent:
                # Detach this Source from its parent
                desc.parent.children.remove(desc)
            del self._opened[source]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, backtrace):
        self.clear()

    def __contains__(self, item):
        return item in self._opened

    def clear(self):
        """Closes all of the Sources presently open in this SourceManager."""
        logger.debug("SourceManager.clear")
        for child in self._top.children.copy():
            self.close(child.source)

    def clear_dependents(self):
        """Closes all of the dependent Sources presently open in this
        SourceManager."""
        logger.debug("SourceManager.clear_dependents")
        for child in self._top.children:
            for subchild in child.children.copy():
                self.close(subchild.source)

    @property
    def configuration(self) -> dict:
        """Returns the configuration dictionary, if there is one. Configuration
        dictionaries contain parameters that Sources can use to adjust their
        behaviour."""
        return self._configuration

    @configuration.setter
    def configuration(self, value: dict):
        """Sets the configuration dictionary. (SourceManager instantiators
        should make sure that an appropriate configuration dictionary is in
        place before calling methods on a Source.)"""
        self._configuration = value
