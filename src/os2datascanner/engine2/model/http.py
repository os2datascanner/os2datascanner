from io import BytesIO
from urllib.parse import urlsplit, urlunsplit
import structlog
from requests.sessions import Session
from contextlib import contextmanager
from typing import Optional, Union
from datetime import datetime
import re

from .. import settings as engine2_settings
from ..utilities.backoff import WebRetrier
from ..utilities.datetime import parse_datetime
from ..conversions.types import OutputType
from ..conversions.utilities.navigable import (
        make_navigable, make_values_navigable)
from .core import Source, Handle, FileResource
from .utilities.sitemap import process_sitemap_url

from .utilities import crawler


logger = structlog.getLogger(__name__)
TIMEOUT: int = engine2_settings.model["http"]["timeout"]
TTL: int = engine2_settings.model["http"]["ttl"]
_equiv_domains = set({"www", "www2", "m", "ww1", "ww2", "en", "da", "secure"})
# match whole words (\bWORD1\b | \bWORD2\b) and escape to handle metachars.
# It is important to match whole words; www.magenta.dk should be .magenta.dk, not
# .agta.dk
_equiv_domains_re = re.compile(
    r"\b" + r"\b|\b".join(map(re.escape, _equiv_domains)) + r"\b"
)


def rate_limit(request_function):
    """ Wrapper function to force a proces to sleep by a requested amount,
    when a certain amount of requests are made by it """
    def _rate_limit(*args, **kwargs):
        return WebRetrier().run(
            request_function,
            *args,
            **kwargs)

    return _rate_limit


def simplify_mime_type(mime):
    r = mime.split(';', maxsplit=1)
    return r[0]


def netloc_normalize(hostname: Union[str, None]) -> str:
    "remove common subdomains from a hostname"
    if hostname:
        return _equiv_domains_re.sub("", hostname).strip(".")

    return ""


def make_head_fallback(context):
    """Returns a function equivalent to context.head -- unless the resulting
    HEAD request fails with HTTP/1.1 405 Method Not Supported, in which case
    it converts the request to a GET."""
    def _make_head_fallback(url, **kwargs):
        r = context.head(url, **kwargs)
        if r.status_code == 405:
            logger.warning(
                    f"HTTP HEAD method not available for {url},"
                    " trying GET instead")
            r = context.get(url, **kwargs)
        return r

    return _make_head_fallback


def fix(new_url, base_url):
    nurls = urlsplit(new_url)
    url_split = urlsplit(base_url)

    # ensure hostnames and optionally path(if the source were created with a
    # nonempty path) matches
    if (nurls.hostname == url_split.hostname and
            nurls.path.startswith(url_split.path)):
        # exactly same hostname and same path
        return (base_url, new_url.removeprefix(base_url))
    elif (netloc_normalize(nurls.hostname) == url_split.hostname and
            nurls.path.startswith(url_split.path)):
        # hostnames and are equivalent. Create new Source from "new" hostname but
        # retain original path, if present
        base_url = urlunsplit(
            (nurls.scheme, nurls.netloc, url_split.path, "", "")
        )
        return (base_url, new_url.removeprefix(base_url))
    else:
        logger.debug("hostname outside current source", url=new_url)
        return None


class WebSource(Source):
    type_label = "web"
    eq_properties = ("_url",)

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
            session.headers.update(
                {"User-Agent": f"OS2datascanner/{__version__}"
                               f" ({session.headers['User-Agent']})"
                               " (+https://os2datascanner.dk/agent)"}
            )
            yield session

    def censor(self) -> "WebSource":
        # XXX: we should actually decompose the URL and remove authentication
        # details from netloc
        return self

    def handles(self, sm):
        session = sm.open(self)
        wc = crawler.WebCrawler(
                self._url, session=session, timeout=TIMEOUT, ttl=TTL)
        if self._exclude:
            wc.exclude(*self._exclude)

        wc.add(self._url)

        if self._sitemap:
            for (address, last_modified) in process_sitemap_url(self._sitemap):
                if wc.is_crawlable(address):
                    wc.add(address, lm_hint=last_modified)
            wc.freeze()

        for hints, url in wc.visit():
            referrer = hints.get("referrer")
            lm_hint = hints.get("lm_hint")
            r = WebHandle.make_handle(
                    referrer, self._url) if referrer else None
            yield WebHandle.make_handle(
                    url, self._url, referrer=r, last_modified_hint=lm_hint)

    @property
    def url(self):
        '''
        This method simply returns the _url property.
        Many of the tests and WebHandle.presentation_url depend on this.
        '''
        return self._url

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
        _, netloc, _, _, _ = urlsplit(self.handle.source.url)
        yield "web-domain", netloc
        yield from super()._generate_metadata()

    def _get_head_raw(self):
        throttled_session_head = rate_limit(
                make_head_fallback(self._get_cookie()))
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

            self._mr = make_values_navigable(
                    {k.lower(): v for k, v in header.items()})
            try:
                self._mr[OutputType.LastModified] = make_navigable(
                        parse_datetime(self._mr["last-modified"]),
                        parent=self._mr)
            except (KeyError, ValueError):
                pass
        if check:
            self._response.raise_for_status()
        return self._mr

    def get_size(self):
        return int(self.unpack_header(check=True).get("content-length", 0))

    def get_last_modified(self):
        lm_hint = self.handle.last_modified_hint
        if not lm_hint:
            return self.unpack_header(check=True).setdefault(
                    OutputType.LastModified, super().get_last_modified())
        else:
            return lm_hint

    def compute_type(self):
        # At least for now, strip off any extra parameters the media type might
        # specify
        return self.unpack_header(check=True).get(
            "content-type", "application/octet-stream").split(";", maxsplit=1)[0]

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
    def presentation_name(self):
        return self.presentation_url

    @property
    def presentation_place(self):
        split = urlsplit(self.presentation_url)
        return split.hostname

    def __str__(self):
        return self.presentation_url

    @property
    def presentation_url(self) -> str:
        path = self.relative_path
        if path and not path.startswith("/"):
            path = "/" + path
        # .removesuffix is probably unnecessary, as it is already done on source._url
        return self.source.url.removesuffix("/") + path

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

    @classmethod
    def make_handle(
            cls, url: str, base_url: str = None, **kwargs) -> "WebHandle":
        su = sp = None
        if base_url:
            fv = fix(url, base_url)
            if fv:
                su, sp = fv
        if su is None and sp is None:
            split_url = urlsplit(url)
            su = f"{split_url.scheme}://{split_url.netloc}"
            sp = split_url.path
        return WebHandle(
                WebSource(su), sp, **kwargs)
