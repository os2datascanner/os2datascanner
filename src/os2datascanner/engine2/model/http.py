from io import BytesIO
from time import sleep
from lxml.html import document_fromstring
from lxml.etree import ParserError
from urllib.parse import urljoin, urlsplit, urlunsplit
import logging
from requests.sessions import Session
from requests.exceptions import RequestException
from contextlib import contextmanager
from typing import Optional, Set
from datetime import datetime

from .. import settings as engine2_settings
from ..conversions.types import OutputType
from ..conversions.utilities.results import SingleResult, MultipleResults
from .core import Source, Handle, FileResource
from .utilities import NamedTemporaryResource
from .utilities.sitemap import SitemapError, process_sitemap_url
from .utilities.datetime import parse_datetime

logger = logging.getLogger(__name__)
SLEEP_TIME = 1 / engine2_settings.model["http"]["limit"]
TIMEOUT = engine2_settings.model["http"]["timeout"]


def simplify_mime_type(mime):
    r = mime.split(';', maxsplit=1)
    return r[0]


class WebSource(Source):
    type_label = "web"
    eq_properties = ("_url", "_sitemap",)

    def __init__(self, url: str, sitemap : str = "", exclude = []):
        assert url.startswith("http:") or url.startswith("https:")
        self._url = url if url.endswith("/") else url + "/"
        self._sitemap = sitemap
        self._exclude = exclude

    def _generate_state(self, sm):
        with Session() as session:
            session.headers.update(
                {'User-Agent': f'OS2datascanner ({session.headers["User-Agent"]})'
                               ' (+https://os2datascanner.dk/agent)'}
            )
            yield session

    def censor(self) -> "WebSource":
        # XXX: we should actually decompose the URL and remove authentication
        # details from netloc
        return self

    def handles(self, sm):
        session = sm.open(self)
        to_visit = [WebHandle(self, "")]
        known_addresses = set(to_visit)

        # initial check that url can be reached. After this point, continue
        # exploration at all cost
        try:
            r = session.head(to_visit[0].presentation_url)
            r.raise_for_status()
        except RequestException as err:
            raise RequestException(
                f"{to_visit[0].presentation_url} is not available: {err}")

        # scheme://netloc/path?query
        # https://example.com/some/path?query=foo
        scheme, netloc, path, query, fragment = urlsplit(self._url)

        def handle_url(here: "WebHandle", new_url: str,
                       lm_hint: datetime = None, from_sitemap: bool = False):

            here_url = None if from_sitemap else here.presentation_url
            referrer = WebHandle(self, self._sitemap) if from_sitemap else here
            new_url = urljoin(here_url, new_url)
            n_scheme, n_netloc, n_path, n_query, _ = urlsplit(new_url)
            new_url = urlunsplit(
                    (n_scheme, n_netloc, n_path, n_query, None))

            # urlsplit assigns the trailing slash after the netloc to the
            # path, while WebSource treats it as part of the base URL. Make
            # sure it isn't present in both to avoid conflicts
            if n_path.startswith("/"):
                n_path = n_path[1:]

            # ensure the new_url actually is a url and not mailto:, etc
            if n_scheme not in ("http", "https"):
                return
            for exclude in self._exclude:
                if new_url.startswith(exclude):
                    logger.info(f"excluded {new_url}")
                    return

            if n_netloc == netloc:
                # we dont care about whether scheme is http or https
                # new_url is under same hirachy as here(referrer)
                new_handle = WebHandle(self, n_path, referrer, lm_hint)
            else:
                # new_url is external from here. Create a new handle from a new
                # Source.
                base_url = urlunsplit((n_scheme, n_netloc, "", None, None))
                new_handle = WebHandle(WebSource(base_url), n_path, referrer,
                        lm_hint)
            if new_handle not in known_addresses:
                known_addresses.add(new_handle)
                to_visit.append(new_handle)

        if self._sitemap:
            i = 0  # prevent i from being undefined if sitemap is empty
            for i, (address, last_modified) in enumerate(
                    process_sitemap_url(self._sitemap), start=1):
                handle_url(to_visit[0], address, last_modified, from_sitemap=True)
            # first entry in `to_visit` is `self`(ie. mainpage). If the mainpage
            # is not listed in sitemap this result in +1 in to_visit
            logger.info("sitemap {0} processed. #entries {1}, #urls to_visit {2}".
                         format(self._sitemap, i, len(to_visit)))

        # If the handle(here) originates from the Source, then scrape the
        # resource for all links and submit them to `handle_url` (which appends
        # the handles to `to_visit`)
        # If the handle is external, then just yield and let processor check
        # if the page is available.
        while to_visit:
            here, to_visit = to_visit[0], to_visit[1:]
            # only search for links on `here` if it belongs to base Source
            if here in self:
                try:
                    response = session.head(here.presentation_url)
                    if response.status_code == 200:
                        ct = response.headers.get("Content-Type",
                                                "application/octet-stream")
                        if simplify_mime_type(ct) == 'text/html':
                            response = session.get(here.presentation_url)
                            sleep(SLEEP_TIME)
                            i = 0
                            for i, li in enumerate(
                                    make_outlinks(response.content,
                                                  here.presentation_url),
                                    start=1):
                                handle_url(here, li)
                            logger.info(f"site {here.presentation} has {i} links")
                    elif response.is_redirect and response.next:
                        handle_url(here, response.next.url)
                        # Don't yield WebHandles for redirects
                        continue

                # There should newer be a ConnectionError, as only handles
                # originating from Source are requested. But just in case..
                except RequestException as e:
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
        return dict(**super().to_json_object(), **{
            "url": self._url,
            "sitemap": self._sitemap,
            "exclude": self._exclude,
        })

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
        return self._get_cookie().head(
            self._make_url(), timeout=TIMEOUT)

    def check(self) -> bool:
        # This might raise an RequestsException, fx.
        # [Errno -2] Name or service not known' (dns)
        # [Errno 110] Connection timed out'     (no response)
        response = self._get_head_raw()
        return response.status_code not in (404, 410,)

    def _make_url(self):
        return self.handle.presentation_url

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
        response = self._get_cookie().get(
            self._make_url(), timeout=TIMEOUT)
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
        super().__init__(source, path, referrer)
        self._lm_hint = last_modified_hint

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
        if p[-1] != "/" and not self.relative_path.startswith("/"):
            p += "/"
        return p + self.relative_path

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
                    logger.warning(f"discarding secondary referrers for {obj}")

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
        for el, _, li, _ in doc.iterlinks():
            if el.tag in ("a", "img",):
                yield li
    except ParserError as e:
        # Silently drop ParserErrors, but only for empty documents
        if content and not content.isspace():
            logger.error("{0}: unexpected ParserError".format(where),
                         exc_info=True)
