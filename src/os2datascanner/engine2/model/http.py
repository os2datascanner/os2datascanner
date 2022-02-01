from io import BytesIO
from time import sleep
from lxml.html import document_fromstring
from lxml.etree import ParserError
from urllib.parse import urljoin, urlsplit, urlunsplit, urldefrag
import structlog
from requests.sessions import Session
from requests.exceptions import RequestException
from contextlib import contextmanager
from typing import Optional, Union
from datetime import datetime
import re

from .. import settings as engine2_settings
from ..conversions.types import Link, OutputType
from ..conversions.utilities.results import SingleResult, MultipleResults
from .core import Source, Handle, FileResource
from .utilities import NamedTemporaryResource
from .utilities.sitemap import process_sitemap_url
from .utilities.datetime import parse_datetime

logger = structlog.getLogger(__name__)
SLEEP_TIME: float = 1 / engine2_settings.model["http"]["limit"]
TIMEOUT: int = engine2_settings.model["http"]["timeout"]
TTL: int = engine2_settings.model["http"]["ttl"]
LIMIT: int = engine2_settings.model["http"]["limit"]
_equiv_domains = set({"www", "www2", "m", "ww1", "ww2", "en", "da", "secure"})
# match whole words (\bWORD1\b | \bWORD2\b) and escape to handle metachars.
# It is important to match whole words; www.magenta.dk should be .magenta.dk, not
# .agta.dk
_equiv_domains_re = re.compile(
    r"\b" + r"\b|\b".join(map(re.escape, _equiv_domains)) + r"\b"
)

# Used in __requests_per_second to count amount of requests made.
# Will be incremented and then reset to 0 when LIMIT is met.
http_requests_made = 0


def rate_limit(request_function):
    """ Wrapper function to force a proces to sleep by a set amount, when a set amount of
    requests are made by it """
    def _rate_limit(*args, **kwargs):
        global http_requests_made
        if http_requests_made == LIMIT:
            sleep(SLEEP_TIME)
            http_requests_made = 0

        response = request_function(*args, **kwargs)
        http_requests_made += 1
        return response

    return _rate_limit


def simplify_mime_type(mime):
    r = mime.split(';', maxsplit=1)
    return r[0]


def netloc_normalize(hostname: Union[str, None]) -> str:
    "remove common subdomains from a hostname"
    if hostname:
        return _equiv_domains_re.sub("", hostname).strip(".")

    return ""


class WebSource(Source):
    type_label = "web"
    eq_properties = ("_url", "_sitemap",)

    def __init__(self, url: str, sitemap: str = "", exclude=None):

        if exclude is None:
            exclude = []

        assert url.startswith("http:") or url.startswith("https:")
        self._url = url.removesuffix("/")
        self._sitemap = sitemap
        self._exclude = exclude

    def _generate_state(self, sm):
        from ... import __version__
        with Session() as session:
            throttled_session_headers_update = rate_limit(session.headers.update)
            throttled_session_headers_update(
                {'User-Agent': f'OS2datascanner {__version__} ({session.headers["User-Agent"]})'
                               ' (+https://os2datascanner.dk/agent)'}
            )
            yield session

    def censor(self) -> "WebSource":
        # XXX: we should actually decompose the URL and remove authentication
        # details from netloc
        return self

    def handles(self, sm):  # noqa: CCR001, C901 too high complexity
        session = sm.open(self)
        origin = WebHandle(self, "")
        to_visit = [(origin, TTL)]
        known_addresses = {origin, }

        # Assign session HTTP methods to variables, wrapped to constrain requests per second
        throttled_session_get = rate_limit(session.get)
        throttled_session_head = rate_limit(session.head)

        # initial check that url can be reached. After this point, continue
        # exploration at all cost
        try:
            r = throttled_session_head(origin.presentation_url, timeout=TIMEOUT)
            r.raise_for_status()
        except RequestException as err:
            raise RequestException(
                f"{origin.presentation_url} is not available: {err}")

        # scheme://netloc/path?query#fragment
        # https://example.com:80/some/path?query=foo#fragment
        url_split = urlsplit(self._url)
        # remove common subdomains from hostname(hostname is like netloc.lower()
        # but without port-number, ect)
        hostname = netloc_normalize(url_split.hostname)

        def handle_url(here: "WebHandle", new_url: str, ttl: int = TTL,
                       lm_hint: datetime = None, from_sitemap: bool = False):

            here_url = "" if from_sitemap else here.presentation_url
            new_url, frag = urldefrag(urljoin(here_url, new_url))
            nurls = urlsplit(new_url)
            referrer = WebHandle(self, self._sitemap) if from_sitemap else here

            if ttl == 0:
                logger.debug("max TTL reached. Not appending url", url=new_url,
                             referrer=referrer.presentation_url, ttl=ttl)
                return
            # ensure the new url actually is a url and not mailto:, etc
            if nurls.scheme not in ("http", "https"):
                return
            for exclude in self._exclude:
                if new_url.startswith(exclude):
                    logger.debug("excluded", url=new_url)
                    return

            # ensure hostnames and optionally path(if the source were created with a
            # nonempty path) matches
            if (
                    nurls.hostname == url_split.hostname and
                    nurls.path.startswith(url_split.path)
            ):
                # exactly same hostname and same path
                rel_path = new_url.removeprefix(self._url)
                new_handle = WebHandle(self, rel_path, referrer, lm_hint)
            elif (
                    netloc_normalize(nurls.hostname) == hostname and
                    nurls.path.startswith(url_split.path)
            ):
                # hostnames and are equivalent. Create new Source from "new" hostname but
                # retain original path, if present
                base_url = urlunsplit(
                    (nurls.scheme, nurls.netloc, url_split.path, "", "")
                )
                rel_path = new_url.removeprefix(base_url)
                new_handle = WebHandle(WebSource(base_url), rel_path, referrer, lm_hint)
            else:
                logger.debug("hostname outside current source", url=new_url)
                return

            if new_handle not in known_addresses:
                known_addresses.add(new_handle)
                to_visit.append((new_handle, ttl-1))
                logger.debug("appended new url to visit", url=new_handle.presentation_url,
                             referrer=new_handle.referrer.presentation_url,
                             ttl=ttl)

        if self._sitemap:
            _i = 0  # prevent i from being undefined if sitemap is empty
            for _i, (address, last_modified) in enumerate(
                    process_sitemap_url(self._sitemap), start=1):
                handle_url(origin, address, lm_hint=last_modified, from_sitemap=True)
            # first entry in `to_visit` is `self`(ie. mainpage). If the mainpage
            # is not listed in sitemap this result in +1 in to_visit
            logger.debug("sitemap {0} processed. #entries {1}, #urls to_visit {2}".
                         format(self._sitemap, _i, len(to_visit)))
            yield from known_addresses
            return

        # scrape the handle(here) for all links and submit them to `handle_url`
        # (which appends the handles to `to_visit`)
        while to_visit:
            (here, ttl), to_visit = to_visit[0], to_visit[1:]
            if ttl == 0:
                continue

            try:
                response = throttled_session_head(here.presentation_url, timeout=TIMEOUT)
                if response.status_code == 200:
                    ct = response.headers.get("Content-Type",
                                              "application/octet-stream")
                    if simplify_mime_type(ct) == 'text/html':
                        response = throttled_session_get(here.presentation_url, timeout=TIMEOUT)
                        i = 0
                        for _i, link in enumerate(
                                make_outlinks(response.content,
                                              here.presentation_url),
                                start=1):
                            handle_url(here, link.url, ttl)
                        logger.debug("url scraped for links", url=here.presentation,
                                     links=i, ttl=ttl)

                elif response.is_redirect and response.next:
                    handle_url(here, response.next.url)
                    # Don't yield WebHandles for redirects
                    continue

            # There should newer be a ConnectionError, as only handles
            # originating from Source are requested. But just in case..
            except RequestException:
                logger.error(f"error while getting head of {here.presentation}",
                             exc_info=True)
            yield here

    def to_url(self):
        return self._url

    @staticmethod
    @Source.url_handler("http", "https")
    def from_url(url):
        return WebSource(url)

    def to_json_object(self):
        return dict(
            **super().to_json_object(),
            url=self._url,
            sitemap=self._sitemap,
            exclude=self._exclude,
        )

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        return WebSource(
            url=obj["url"],
            sitemap=obj.get("sitemap"),
            exclude=obj.get("exclude"),
        )


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
        throttled_session_head = rate_limit(self._get_cookie().head)
        return throttled_session_head(
            self.handle.presentation_url, timeout=TIMEOUT)

    def check(self) -> bool:
        # This might raise an RequestsException, fx.
        # [Errno -2] Name or service not known' (dns)
        # [Errno 110] Connection timed out'     (no response)
        response = self._get_head_raw()
        return response.status_code not in (404, 410,)

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
        return self.unpack_header(check=True).get(
            "content-type", "application/octet-stream").value.split(";", maxsplit=1)[0]

    @contextmanager
    def make_path(self):
        with NamedTemporaryResource(self.handle.name) as ntr:
            with ntr.open("wb") as res:
                with self.make_stream() as s:
                    res.write(s.read())
            yield ntr.get_path()

    @contextmanager
    def make_stream(self):
        # Assign session HTTP methods to variables, wrapped to constrain requests per second
        throttled_session_get = rate_limit(self._get_cookie().get)
        response = throttled_session_get(
            self.handle.presentation_url, timeout=TIMEOUT)
        response.raise_for_status()
        with BytesIO(response.content) as s:
            yield s


class WebHandle(Handle):
    type_label = "web"
    resource_type = WebResource

    eq_properties = Handle.BASE_PROPERTIES

    def __init__(self, source: WebSource, path: str,
                 referrer: Optional["WebHandle"] = None,
                 last_modified_hint: Optional[datetime] = None):
        # path = path if path.startswith("/") else ("/" + path if path else "")
        path = path if path.startswith("/") else "/" + path
        super().__init__(source, path, referrer)
        self._lm_hint = last_modified_hint

    @property
    def last_modified_hint(self) -> Optional[datetime]:
        return self._lm_hint

    @last_modified_hint.setter
    def last_modified_hint(self, lm_hint: datetime):
        self._lm_hint = lm_hint

    @property
    def presentation(self):
        return self.presentation_url

    @property
    def presentation_url(self) -> str:
        path = self.relative_path
        if path and not path.startswith("/"):
            path = "/" + path
        # .removesuffix is probably unnecessary, as it is already done on source._url
        return self.source.to_url().removesuffix("/") + path

    @property
    def sort_key(self):
        """ Returns a string to sort by.
        For a website the URL makes sense"""
        return self.presentation

    def censor(self):
        return WebHandle(source=self.source.censor(), path=self.relative_path,
                         referrer=self.referrer,
                         last_modified_hint=self.last_modified_hint)

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "last_modified": OutputType.LastModified.encode_json_object(
                    self.last_modified_hint),
        })

    @staticmethod
    @Handle.json_handler(type_label)
    def from_json_object(obj):
        lm_hint = obj.get("last_modified", None)
        if lm_hint:
            lm_hint = OutputType.LastModified.decode_json_object(lm_hint)
        referrer = obj.get("referrer", None)
        if referrer:
            if isinstance(referrer, list):
                # Prior to the 25th of June, the "referrer" field was a
                # WebHandle-only property and contained a list of URLs: after
                # that point, it became a feature of Handles in general and
                # now contains a serialised Handle. Make sure we still support
                # the old format
                if len(referrer) > 1:
                    logger.warning("discarding secondary referrers",
                                   obj=obj)

                url = referrer[0]
                scheme, netloc, path, query, fragment = urlsplit(url)
                source_url = urlunsplit((scheme, netloc, "/", "", ""))
                handle_path = urlunsplit(("", "", path[1:], query, fragment))
                referrer = WebHandle(WebSource(source_url), handle_path)
            else:
                referrer = WebHandle.from_json_object(referrer)
        return WebHandle(
                Source.from_json_object(obj["source"]), obj["path"],
                referrer=referrer, last_modified_hint=lm_hint)


def make_outlinks(content, where):
    try:
        doc = document_fromstring(content)
        doc.make_links_absolute(where, resolve_base_href=True)
        for element, _attr, link, _pos in doc.iterlinks():
            # ignore e.g. <a href="" rel="nofollow">
            if element.tag in ("a", "img",) and element.get("rel") != "nofollow":
                yield Link(link, link_text=element.text)
    except ParserError:
        # Silently drop ParserErrors, but only for empty documents
        if content and not content.isspace():
            logger.error("{0}: unexpected ParserError".format(where),
                         exc_info=True)
