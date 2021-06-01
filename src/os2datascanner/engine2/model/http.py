from io import BytesIO
from time import sleep
from lxml.html import document_fromstring
from lxml.etree import ParserError
from urllib.parse import urljoin, urlsplit, urlunsplit
import logging
from requests.sessions import Session
from requests.exceptions import ConnectionError
from contextlib import contextmanager
from typing import Optional, Set
from datetime import datetime

from ..conversions.types import OutputType
from ..conversions.utilities.results import SingleResult, MultipleResults
from .core import Source, Handle, FileResource
from .utilities import NamedTemporaryResource
from .utilities.sitemap import SitemapError, process_sitemap_url
from .utilities.datetime import parse_datetime

logger = logging.getLogger(__name__)
MAX_REQUESTS_PER_SECOND = 10
SLEEP_TIME = 1 / MAX_REQUESTS_PER_SECOND


def simplify_mime_type(mime):
    r = mime.split(';', maxsplit=1)
    return r[0]


class WebSource(Source):
    type_label = "web"

    def __init__(self, url, sitemap=None):
        assert url.startswith("http:") or url.startswith("https:")
        self._url = url
        self._sitemap = sitemap

    def _generate_state(self, sm):
        with Session() as session:
            yield session

    def censor(self):
        # XXX: we should actually decompose the URL and remove authentication
        # details from netloc
        return self

    def handles(self, sm):
        session = sm.open(self)
        to_visit = [WebHandle(self, "")]
        known_addresses = set(to_visit)
        referrer_map = {}

        scheme, netloc, path, query, fragment = urlsplit(self._url)

        def handle_url(here, new_url, lm_hint=None):
            new_url = urljoin(here, new_url)
            n_scheme, n_netloc, n_path, n_query, _ = urlsplit(new_url)
            if n_scheme == scheme and n_netloc == netloc:
                new_url = urlunsplit(
                        (n_scheme, n_netloc, n_path, n_query, None))
                referrer_map.setdefault(new_url, set()).add(
                    here if here is not None else self._sitemap)
                new_handle = WebHandle(self, new_url[len(self._url):],
                                       referrer_map[new_url], lm_hint)
                if new_handle not in known_addresses:
                    known_addresses.add(new_handle)
                    to_visit.append(new_handle)

        if self._sitemap:
            i = 0  # prevent i from being undefined if sitemap is empty
            for i, (address, last_modified) in enumerate(
                    process_sitemap_url(self._sitemap), start=1):
                handle_url(None, address, last_modified)
            # first entry in `to_visit` is `self`(ie. mainpage). If the mainpage
            # is not listed in sitemap this result in +1 in to_visit
            logger.info("sitemap {0} processed. #entries {1}, #urls to_visit {2}".
                         format(self._sitemap, i, len(to_visit)))


        while to_visit:
            here, to_visit = to_visit[0], to_visit[1:]

            response = session.head(here.presentation_url)
            if response.status_code == 200:
                ct = response.headers['Content-Type']
                if simplify_mime_type(ct) == 'text/html':
                    response = session.get(here.presentation_url)
                    sleep(SLEEP_TIME)
                    i = 0
                    for i, li in enumerate(
                            make_outlinks(response.content,
                                          here.presentation_url), start=1):
                        handle_url(here.presentation_url, li)
                    logger.debug("site {0} has {1} links".format(here.presentation, i))
            elif response.is_redirect and response.next:
                handle_url(here.presentation_url, response.next.url)
                # Don't yield WebHandles for redirects
                continue

            yield here

    def to_url(self):
        return self._url

    @staticmethod
    @Source.url_handler("http", "https")
    def from_url(url):
        return WebSource(url)

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "url": self._url,
            "sitemap": self._sitemap
        })

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        return WebSource(
                url=obj["url"],
                sitemap=obj.get("sitemap"))


SecureWebSource = WebSource


class WebResource(FileResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._response = None
        self._mr = None

    def _generate_metadata(self):
        _, netloc, _, _, _ = urlsplit(self.handle.source.to_url())
        yield "web-domain", netloc
        yield from super()._generate_metadata()

    def _get_head_raw(self):
        return self._get_cookie().head(self._make_url())

    def check(self) -> bool:
        response = self._get_head_raw()
        return response.status_code not in (404, 410,)

    def _make_url(self):
        handle = self.handle
        base = handle.source.to_url()
        return base + str(handle.relative_path)

    def get_status(self):
        self.unpack_header()
        return self._response.status_code

    def unpack_header(self, check=False):
        if not self._response:
            self._response = self._get_head_raw()
            header = self._response.headers

            self._mr = MultipleResults(
                    {k.lower(): v for k, v in header.items()})
            try:
                self._mr[OutputType.LastModified] = parse_datetime(
                        self._mr["last-modified"].value)
            except (KeyError, ValueError):
                pass
        if check:
            self._response.raise_for_status()
        return self._mr

    def get_size(self):
        return self.unpack_header(check=True).get("content-length", 0).map(int)

    def get_last_modified(self):
        lm_hint = self.handle.last_modified_hint
        if not lm_hint:
            return self.unpack_header(check=True).setdefault(
                    OutputType.LastModified, super().get_last_modified())
        else:
            return SingleResult(None, OutputType.LastModified, lm_hint)

    def compute_type(self):
        # At least for now, strip off any extra parameters the media type might
        # specify
        return self.unpack_header(check=True).get("content-type",
                "application/octet-stream").value.split(";", maxsplit=1)[0]

    @contextmanager
    def make_path(self):
        with NamedTemporaryResource(self.handle.name) as ntr:
            with ntr.open("wb") as res:
                with self.make_stream() as s:
                    res.write(s.read())
            yield ntr.get_path()

    @contextmanager
    def make_stream(self):
        response = self._get_cookie().get(self._make_url())
        response.raise_for_status()
        with BytesIO(response.content) as s:
            yield s


class WebHandle(Handle):
    type_label = "web"
    resource_type = WebResource

    eq_properties = Handle.BASE_PROPERTIES

    def __init__(self, source: WebSource, path: str,
                 referrer_urls: Set[str]=set(),
                 last_modified_hint: Optional[datetime]=None):
        super().__init__(source, path)
        self._referrer_urls = referrer_urls
        self._lm_hint = last_modified_hint

    @property
    def referrer_urls(self) -> set:
        return self._referrer_urls

    @referrer_urls.setter
    def referrer_urls(self, referrer_urls: Set[str]):
        self._referrer_urls = referrer_urls

    @property
    def last_modified_hint(self) -> Optional[datetime]:
        return self._lm_hint

    @last_modified_hint.setter
    def last_modified_hint(self, lm_hint: datetime):
        self._lm_hint = lm_hint

    @property
    def presentation(self) -> str:
        return self.presentation_url

    @property
    def presentation_url(self) -> str:
        p = self.source.to_url()
        if p[-1] != "/":
            p += "/"
        return p + self.relative_path

    def censor(self):
        return WebHandle(source=self.source.censor(), path=self.relative_path,
                         referrer_urls=self.referrer_urls,
                         last_modified_hint=self.last_modified_hint)

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "last_modified": OutputType.LastModified.encode_json_object(
                    self._lm_hint),
            "referrer": list(self._referrer_urls)
        })

    @staticmethod
    @Handle.json_handler(type_label)
    def from_json_object(obj):
        lm_hint = obj.get("last_modified", None)
        if lm_hint:
                lm_hint = OutputType.LastModified.decode_json_object(lm_hint)
        referrer = set(obj.get("referrer", set()))
        handle = WebHandle(Source.from_json_object(obj["source"]), obj["path"],
                           referrer_urls=referrer, last_modified_hint=lm_hint)
        return handle


def make_outlinks(content, where):
    try:
        doc = document_fromstring(content)
        doc.make_links_absolute(where, resolve_base_href=True)
        for el, _, li, _ in doc.iterlinks():
            if el.tag in ("a", "img",):
                yield li
    except ParserError:
        # Silently drop ParserErrors, but only for empty documents
        if content and not content.isspace():
            logging.exception("{0}: unexpected ParserError".format(where))
