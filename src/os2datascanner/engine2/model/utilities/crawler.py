import re
from abc import ABC, abstractmethod
from lxml.html import HtmlElement, document_fromstring
from lxml.etree import ParserError
from urllib.parse import urlsplit, urlunsplit, SplitResult
import logging
import requests

from os2datascanner.engine2.conversions.types import Link
from ...utilities.backoff import WebRetrier

logger = logging.getLogger(__name__)


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

        Once an object has been added, there is an expectation that it will
        eventually be yielded by Crawler.visit. To avoid that, subclasses can
        override this method to add additional checks.

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
        """Recursively visits all of the objects added to this Crawler."""
        while self.to_visit:
            (head, ttl, hints), *self.to_visit = self.to_visit
            self._visiting = head
            try:
                adapted = self._adapt(head)
                if ttl > 0 and adapted not in self.visited:
                    yield from self.visit_one(head, ttl, hints)
                    self.visited.add(adapted)
            finally:
                self._visiting = None


def parse_html(content: str, where: str) -> HtmlElement:
    try:
        doc = document_fromstring(content)
        doc.make_links_absolute(where, resolve_base_href=True)
        return doc
    except ParserError:
        # Silently drop ParserErrors, but only for empty documents
        if content and not content.isspace():
            logger.error("{0}: unexpected ParserError".format(where),
                         exc_info=True)


def make_outlinks(root: HtmlElement):
    if root is not None:
        for element, _attr, link, _pos in root.iterlinks():
            if (element.tag in ("a", "img",)
                    and element.get("rel") != "nofollow"):
                yield (element, Link(link, link_text=element.text))


_equiv_domains = set({"www", "www2", "m", "ww1", "ww2", "en", "da", "secure"})
# match whole words (\bWORD1\b | \bWORD2\b) and escape to handle metachars.
# It is important to match whole words; www.magenta.dk should be .magenta.dk, not
# .agta.dk
_equiv_domains_re = re.compile(
    r"\b" + r"\b|\b".join(map(re.escape, _equiv_domains)) + r"\b"
)


def netloc_normalize(netloc: str) -> str:
    return _equiv_domains_re.sub("", netloc).strip(".")


def simplify_mime_type(mime):
    return mime.split(';', maxsplit=1)[0]


class WebCrawler(Crawler):
    def __init__(
            self, url: str, session: requests.Session, timeout: float = None,
            *args, allow_element_hints=False, **kwargs):
        super().__init__(*args, **kwargs)
        self._url = url
        self._split_url = urlsplit(url)
        self._session = session
        self._timeout = timeout
        self._retrier = WebRetrier()
        self._allow_element_hints = allow_element_hints
        self.exclusions = set()

    def get(self, *args, **kwargs):
        return self._retrier.run(self._session.get, *args, **kwargs)

    def head(self, *args, **kwargs):
        return self._retrier.run(self._session.head, *args, **kwargs)

    def exclude(self, *exclusions):
        self.exclusions.update(exclusions)

    def _adapt(self, url: str):
        url_s = urlsplit(url)
        return urlunsplit(
                SplitResult(
                        url_s.scheme,
                        url_s.netloc,
                        url_s.path or "/",
                        url_s.query,
                        ""))  # Drop the fragment -- we don't care about it

    def add(self, url: str, ttl: int = None, **hints):
        # Unconditionally drop URL fragments whereever we find them
        if (hp := url.find("#")) != -1:
            url = url[:hp]

        if (any(url.startswith(f"{scheme}:") for scheme in ("http", "https",))
                and not any(url.startswith(excl) for excl in self.exclusions)):
            return super().add(url, ttl, **hints)

    def is_local(self, url: str):
        """Indicates whether or not the given URL belongs to the same domain
        as the base URL of this WebCrawler (or a sufficiently similar one)."""
        url_s = urlsplit(url)
        surl_s = self._split_url
        return (
            url_s.scheme in ("http", "https")
            and (url_s.scheme == surl_s.scheme
                 or (surl_s.scheme == "http" and url_s.scheme == "https"))
            and netloc_normalize(
                    url_s.netloc) == netloc_normalize(surl_s.netloc))

    def is_crawlable(self, url: str):
        """Indicates whether or not the given URL is potentially a target for
        recursive exploration by this WebCrawler."""
        url_s = urlsplit(url)
        surl_s = self._split_url
        return (
            self.is_local(url)
            and (not surl_s.path
                 or url_s.path.startswith(surl_s.path)))

    def _handle_outlink(self, new_ttl, element, link):
        # We only care about local links *covered by this crawler* (and remote
        # links, so they can be checked)
        if self.is_crawlable(link.url) or not self.is_local(link.url):
            extra_hints = {}
            if self._allow_element_hints:
                if (title := element.get("data-title")):
                    extra_hints["title"] = title
                if (true_url := element.get("data-true-url")):
                    extra_hints["true_url"] = true_url
            self.add(link.url, new_ttl, **extra_hints)

    def visit_one(self, url: str, ttl: int, hints):  # noqa CCR001
        if ttl > 0 and self.is_crawlable(url) and not self._frozen:
            response = self.head(url, timeout=self._timeout)

            if response.status_code == 405:
                # The server doesn't support HEAD requests? That's odd. Oh,
                # well, let's use GET instead
                response = self.get(url, timeout=self._timeout)

            if response.status_code == 200:
                ct = response.headers.get(
                        "Content-Type", "application/octet-stream")
                if simplify_mime_type(ct).lower() == "text/html":
                    if not response.content:
                        response = self.get(url, timeout=self._timeout)
                    doc = parse_html(response.content, url)

                    if self._allow_element_hints and not hints.get("title"):
                        # We have to download the page anyway to crawl its
                        # links, so let's extract the title while we're here,
                        # eh?
                        for title in doc.xpath("/html/head/title/text()"):
                            title = title.strip()
                            if title:
                                hints["title"] = title

                    for element, link in make_outlinks(doc):
                        self._handle_outlink(ttl - 1, element, link)
            elif response.is_redirect and response.next:
                # Redirects cost a TTL point *and* don't produce anything
                self.add(response.next.url, ttl - 1)
                return

        yield (hints, url)
