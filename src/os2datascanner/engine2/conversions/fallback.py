from .types import OutputType
from .registry import conversion


@conversion(OutputType.AlwaysTrue)
def fallback_processor(r, **kwargs):
    return True
