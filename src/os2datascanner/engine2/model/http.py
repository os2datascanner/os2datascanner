from io import BytesIO
from time import sleep
from lxml.html import document_fromstring
from urllib.parse import urljoin, urlsplit, urlunsplit
from requests.sessions import Session
from requests.exceptions import ConnectionError
from contextlib import contextmanager

from ..conversions.types import OutputType
from ..conversions.utilities.results import SingleResult, MultipleResults
from .core import Source, Handle, FileResource, ResourceUnavailableError
from .utilities import NamedTemporaryResource
from .utilities.sitemap import SitemapError, process_sitemap_url
from .utilities.datetime import parse_datetime


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
        try:
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
                    referrer_map.setdefault(new_url, set()).add(here)
                    new_handle = WebHandle(self, new_url[len(self._url):])
                    if new_handle not in known_addresses:
                        new_handle.set_last_modified_hint(lm_hint)
                        new_handle.set_referrer_urls(
                                referrer_map.get(here, set()))
                        known_addresses.add(new_handle)
                        to_visit.append(new_handle)

            if self._sitemap:
                try:
                    for address, last_modified in process_sitemap_url(
                            self._sitemap):
                        handle_url(None, address, last_modified)
                except SitemapError as e:
                    raise ResourceUnavailableError(self, *e.args)

            while to_visit:
                here, to_visit = to_visit[0], to_visit[1:]

                response = session.head(here.presentation_url)
                if response.status_code == 200:
                    ct = response.headers['Content-Type']
                    if simplify_mime_type(ct) == 'text/html':
                        response = session.get(here.presentation_url)
                        sleep(SLEEP_TIME)
                        for li in make_outlinks(response.content, here.presentation_url):
                            handle_url(here.presentation_url, li)
                elif response.is_redirect and response.next:
                    handle_url(here.presentation_url, response.next.url)
                    # Don't yield WebHandles for redirects
                    continue

                yield here
        except ConnectionError as e:
            raise ResourceUnavailableError(self, *e.args)

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
        self._status = None
        self._mr = None

    def _make_url(self):
        handle = self.handle
        base = handle.source.to_url()
        return base + str(handle.relative_path)

    def get_status(self):
        self.unpack_header()
        return self._status

    def unpack_header(self, check=False):
        if not self._status:
            response = self._get_cookie().head(self._make_url())
            self._status = response.status_code
            header = response.headers

            self._mr = MultipleResults(
                    {k.lower(): v for k, v in header.items()})
            try:
                self._mr[OutputType.LastModified] = parse_datetime(
                        self._mr["last-modified"].value)
            except (KeyError, ValueError):
                pass
        if check:
            if self._status != 200:
                raise ResourceUnavailableError(self.handle, self._status)
        return self._mr

    def get_size(self):
        return self.unpack_header(check=True).get("content-length", 0).map(int)

    def get_last_modified(self):
        lm_hint = self.handle.get_last_modified_hint()
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
        if response.status_code != 200:
            raise ResourceUnavailableError(self.handle, response.status_code)
        else:
            with BytesIO(response.content) as s:
                yield s


class WebHandle(Handle):
    type_label = "web"
    resource_type = WebResource

    eq_properties = Handle.BASE_PROPERTIES

    def __init__(self, source, path):
        super().__init__(source, path)
        self._referrer_urls = set()
        self._lm_hint = None

    def set_referrer_urls(self, referrer_urls):
        self._referrer_urls = referrer_urls

    def get_referrer_urls(self):
        return self._referrer_urls

    def set_last_modified_hint(self, lm_hint):
        self._lm_hint = lm_hint

    def get_last_modified_hint(self):
        return self._lm_hint

    @property
    def presentation(self):
        return self.presentation_url

    @property
    def presentation_url(self):
        p = self.source.to_url()
        if p[-1] != "/":
            p += "/"
        return p + self.relative_path

    def censor(self):
        return WebHandle(self.source.censor(), self.relative_path)

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "last_modified": OutputType.LastModified.encode_json_object(
                    self._lm_hint)
        })

    @staticmethod
    @Handle.json_handler(type_label)
    def from_json_object(obj):
        handle = WebHandle(Source.from_json_object(obj["source"]), obj["path"])
        lm_hint = obj["last_modified"]
        if lm_hint:
            handle.set_last_modified_hint(
                    OutputType.LastModified.decode_json_object(lm_hint))
        return handle


def make_outlinks(content, where):
    doc = document_fromstring(content)
    doc.make_links_absolute(where, resolve_base_href=True)
    for el, _, li, _ in doc.iterlinks():
        if el.tag in ("a", "img",):
            yield li
