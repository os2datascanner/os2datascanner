from io import BytesIO
from lxml import etree
from typing import Tuple, Iterable, Optional, List
from datetime import datetime
import structlog
import requests
from os2datascanner.engine2.model.data import unpack_data_url

from .datetime import parse_datetime
from .utilities import convert_data_to_text
from ... import settings as engine2_settings

# disable xml vulnerabilities, as described here
# https://github.com/tiran/defusedxml#external-entity-expansion-local-file
# https://lxml.de/api/lxml.etree.XMLParser-class.html
_PARSER = etree.XMLParser(resolve_entities=False)
TIMEOUT = engine2_settings.model["http"]["timeout"]
logger = structlog.getLogger(__name__)


def _xp(e, path: str) -> List[str]:
    """Parse an `ElementTree` using a namespace with sitemap prefix.

    Example
    r = requests.get('https://www.magenta.dk/sitemap_index.xml')
    root = etree.parse(BytesIO(r.content))
    print(etree.tostring(root, pretty_print=True).decode("utf8"))
    # Then use the /sitemap namespace
    ns = {"sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9}
    root2.xpath("/sitemap:sitemapindex", namespaces=ns)

    """
    return e.xpath(path,
                   namespaces={
                       "sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9"
                   })


def _get_url_data(url: str, context=requests) -> Optional[bytes]:
    try:
        r = context.get(url, timeout=TIMEOUT)
        if r.status_code == 200:
            content_type = r.headers["content-type"]
            simple_content_type = content_type.split(";", 1)[0].strip()
            if simple_content_type in ("text/xml", "application/xml"):
                return r.content
            else:
                # the server served a file that needs to be unpacked
                return convert_data_to_text(r.content, mime=content_type)
        else:
            return None
    except requests.exceptions.RequestException:
        return None


def process_sitemap_url(url: str, *, context=requests,
                        allow_sitemap: bool = True) -> Iterable[Tuple[str, Optional[datetime]]]:

    """Retrieves and parses the sitemap or sitemap index at the given URL and
    yields zero or more (URL, last-modified) tuples.

    The given URL can use the "http", "https" or "data" schemes."""

    logger.debug("trying to download/unpack", sitemap=url)
    if url.startswith("data:"):
        _, sitemap = unpack_data_url(url)
    else:
        sitemap = _get_url_data(url)

    if sitemap is None:
        raise SitemapMissingError(url)

    try:
        root = etree.parse(BytesIO(sitemap), parser=_PARSER)
        if _xp(root, "/sitemap:urlset"):
            # This appears to be a normal sitemap: iterate over all of the
            # valid <url /> elements and yield their addresses and last
            # modification dates
            i = 0
            base_url = url
            for i, url in enumerate(
                    _xp(root, "/sitemap:urlset/sitemap:url[sitemap:loc]"),
                    start=1):
                loc = _xp(url, "sitemap:loc/text()")[0].strip()
                lm = None
                for lastmod in _xp(url, "sitemap:lastmod/text()"):
                    lm = parse_datetime(lastmod.strip())
                yield (loc, lm)
            logger.debug("done processing", lines=i, sitemap=base_url)
        elif _xp(root, "/sitemap:sitemapindex") and allow_sitemap:
            # This appears to be a sitemap index: iterate over all of the valid
            # <sitemap /> elements and recursively yield from them
            for sitemap in _xp(root,
                               "/sitemap:sitemapindex/sitemap:sitemap[sitemap:loc]"):
                loc = _xp(sitemap, "sitemap:loc/text()")[0].strip()
                # Sitemap indexes aren't allowed to reference other sitemap
                # indexes, so forbid that to avoid infinite loops
                yield from process_sitemap_url(loc,
                                               context=context, allow_sitemap=False)
        else:
            raise SitemapMalformedError(url)
    except etree.XMLSyntaxError:
        raise SitemapMalformedError(url)


class SitemapError(Exception):
    # print the Exception type and not only the Exception message.
    def __str__(self):
        return repr(self)


class SitemapMissingError(SitemapError):
    """If a problem occurred while trying to retrieve a sitemap file from a
    particular URL, then a SitemapMissingError will be raised. Its only
    associated value is the URL in question."""


class SitemapMalformedError(SitemapError):
    """When process_sitemap_url msucceeds in retrieving a file, but can't parse
    it as XML or can't understand the XML as a sitemap, a SitemapMalformedError
    will be raised. Its only associated value is the URL of the malformed
    sitemap."""
