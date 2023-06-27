from .types import OutputType
from .registry import conversion

from os2datascanner.engine2.model.core import Handle, Source


@conversion(OutputType.Manifest)
def manifest_processor(resource):
    source = Source.from_handle(resource.handle)
    return [h for h in source.handles(resource._sm)
            if isinstance(h, Handle)] if source else None
