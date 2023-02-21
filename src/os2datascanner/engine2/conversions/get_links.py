import logging
from lxml.etree import ParserError

from .types import OutputType
from .registry import conversion
from ..model.utilities.crawler import make_outlinks

logger = logging.getLogger(__name__)


@conversion(OutputType.Links, "text/html")
def links_processor(r, **kwargs):
    """return a list of links found on the given resource"""
    with r.make_stream() as fp:
        try:
            content = fp.read().decode()
            return [
                    link for link in make_outlinks(content, str(r.handle))
                    if link.url.startswith("http")]
        except ParserError:
            logger.error("Conversion error while extracting links",
                         exc_info=True)
            return None
