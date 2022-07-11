from ..core import Source, Handle
import inspect


class DerivedSource(Source):
    """A DerivedSource is a convenience class for a Source backed by a Handle.
    It provides sensible default implementations of Source.handle,
    Source.censor, Source.remap, and Source.to_json_object, and automatically
    registers the constructor of every subclass as a JSON object decoder for
    Sources."""

    def __init__(self, handle):
        self._handle = handle

    @property
    def handle(self):
        return self._handle

    def censor(self):
        return type(self)(self.handle.censor())

    def to_json_object(self):
        return dict(**super().to_json_object(), handle=self.handle.to_json_object())

    @classmethod
    def __init_subclass__(cls, **kwargs):
        """Class creation controller. Whenever a concrete subclass is
        initialised, registers its constructor as a JSON object decoder for
        Sources."""
        super().__init_subclass__(**kwargs)

        if not inspect.isabstract(cls):
            @Source.json_handler(cls.type_label)
            def _from_json_object(obj):
                return cls(Handle.from_json_object(obj["handle"]))

    def remap(self, mapping) -> Source:
        return type(self)(self.handle.remap(mapping))
