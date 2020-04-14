from io import BytesIO
from lxml import etree
from typing import Tuple, Iterable
from datetime import datetime
from dateutil.parser import parse as parse_date
import requests

from os2datascanner.engine2.model.data import unpack_data_url


def _xp(e, path):
    return e.xpath(path,
            namespaces={
                "sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9"
            })


def process_sitemap_url(url: str, *, context=requests,
        allow_sitemap: bool=True) -> Iterable[Tuple[str, datetime]]:
    """Retrieves and parses the sitemap or sitemap index at the given URL and
    yields zero or more (URL, last-modified) tuples.

    The given URL can use the "http", "https" or "data" schemes."""

    def get_url_data(url):
        return context.get(url).content

    if url.startswith("data:"):
        _, sitemap = unpack_data_url(url)
    else:
        sitemap = get_url_data(url)

    try:
        root = etree.parse(BytesIO(sitemap))
        if _xp(root, "/sitemap:urlset"):
            # This appears to be a normal sitemap: iterate over all of the
            # valid <url /> elements and yield their addresses and last
            # modification dates
            for url in _xp(root, "/sitemap:urlset/sitemap:url[sitemap:loc]"):
                loc = _xp(url, "sitemap:loc/text()")[0].strip()
                lm = None
                for lastmod in _xp(url, "sitemap:lastmod/text()"):
                    lm = parse_date(lastmod.strip())
                yield (loc, lm)
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
            pass
    except etree.XMLSyntaxError:
        pass
