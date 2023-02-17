from abc import ABC, abstractmethod


class Crawler(ABC):
    """A Crawler recursively explores objects."""

    def __init__(self, ttl=10):
        self.ttl = ttl
        self.visited = set()
        self.to_visit = list()
        self._visiting = None
        self._frozen = False

    def _adapt(self, obj):
        """Converts a candidate object into a form suitable for insertion into
        a set. The default implementation returns it unchanged.

        Subclasses may override this method."""
        return obj

    def add(self, obj, ttl: int = None, **hints):
        """Adds an object to be visited.

        Subclasses should err on the side of calling this function too often
        than not often enough: Crawler.visit will take care of the details of
        filtering repeated objects out.

        Any keyword arguments passed to this function will be passed on (in a
        dict) to the Crawler.visit_one function."""
        if not self._frozen:
            hints["referrer"] = self._visiting
            self.to_visit.append(
                    (obj, ttl if ttl is not None else self.ttl, hints))

    def freeze(self):
        """Prevents the addition of more objects to this Crawler."""
        self._frozen = True

    @abstractmethod
    def visit_one(self, obj, ttl: int, hints):
        """Visits a single object discovered by this Crawler (or manually fed
        to it by the Crawler.add method). Subclasses should override this
        method to explore the object, and should call self.add for every object
        that they discover in the process."""
        yield from ()

    def visit(self):
        """Visits all of the objects added to this Crawler, and recursively
        visits """
        while self.to_visit:
            (head, ttl, hints), *self.to_visit = self.to_visit
            self._visiting = head
            try:
                adapted = self._adapt(head)
                if ttl > 0 and adapted not in self.visited:
                    print("***", head, ttl, hints)
                    yield from self.visit_one(head, ttl, hints)
                    self.visited.add(adapted)
            finally:
                self._visiting = None
