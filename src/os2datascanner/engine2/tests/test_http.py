import os
import os.path
import http.server
import unittest
import contextlib
import logging
import time
from datetime import datetime
from multiprocessing import Manager, Process
from requests import RequestException
from unittest import mock
from urllib3.util import connection

from os2datascanner.utils.system_utilities import time_now
from os2datascanner.engine2.model.core import Handle, SourceManager
from os2datascanner.engine2.model.http import (WebSource, WebHandle)
from os2datascanner.engine2.model.utilities.crawler import make_outlinks
from os2datascanner.engine2.model.utilities.sitemap import (
    process_sitemap_url, _get_url_data)
from os2datascanner.engine2.utilities.datetime import parse_datetime
from os2datascanner.engine2.conversions.types import Link, OutputType
from os2datascanner.engine2.conversions.registry import convert
from os2datascanner.engine2.rules.links_follow import check
from os2datascanner.engine2 import settings as engine2_settings

here_path = os.path.dirname(__file__)
test_data_path = os.path.join(here_path, "data", "www")

# depth of "redirect chain", TimeToLive
TTL: int = engine2_settings.model["http"]["ttl"]

# define Sources and what to expect from them
site = {
    "source": WebSource("http://localhost:64346"),
    "handles": [
        "http://localhost:64346/",
        "http://localhost:64346/vstkom.png",
        "http://localhost:64346/kontakt.html",
    ],
}
mapped_site = {
    "source": WebSource(
        "http://localhost:64346", sitemap="http://localhost:64346/sitemap.xml"),
    "handles": [
        "http://localhost:64346/",
        "http://localhost:64346/hemmeligheder.html",
        "http://localhost:64346/kontakt.html",
    ],
}
equivalent_mapped_site = {
    "source": WebSource(
        "http://www.localhost:64346", sitemap="http://www.localhost:64346/sitemap.xml"),
    "handles": [
        "http://www.localhost:64346/",
        "http://localhost:64346/",
        "http://localhost:64346/hemmeligheder.html",
        "http://localhost:64346/kontakt.html",
    ],
}
no_equivalent_mapped_site = {
    "source": WebSource(
        "http://a.www.localhost:64346", sitemap="http://a.www.localhost:64346/sitemap.xml"),
    "handles": [
        "http://a.www.localhost:64346/",
    ],
}
indexed_mapped_site = {
    "source": WebSource(
        "http://localhost:64346/", sitemap="http://localhost:64346/sitemap_index.xml"
    ),
    "handles": [
        "http://localhost:64346/",
        "http://localhost:64346/kontakt.html",
        "http://localhost:64346/hemmeligheder.html",
        "http://localhost:64346/hemmeligheder2.html",
    ],
}
embedded_mapped_site = {
    "source": WebSource(
        "http://localhost:64346/",
        sitemap='data:text/xml,<urlset xmlns="http://www.sitemaps.org/schemas'
        '/sitemap/0.9"><url><loc>http://localhost:64346/hemmeligheder'
        "2.html</loc></url></urlset>",
    ),
    "handles": [
        "http://localhost:64346/",
        "http://localhost:64346/hemmeligheder2.html",
    ],
}
compressed_mapped_site = {
    "source": WebSource(
        "http://localhost:64346/",
        sitemap="http://localhost:64346/sitemap_compressed.xml.gz",
    ),
    "handles": [
        "http://localhost:64346/",
        "http://localhost:64346/kontakt.html",
        "http://localhost:64346/hemmeligheder.html",
        "http://localhost:64346/hemmeligheder2.html",
    ],
}
external_links_mapped_site = {
    "source": WebSource(
        "http://localhost:64346/",
        sitemap="http://localhost:64346/sitemap_external.xml",
    ),
    "handles": [
        "http://localhost:64346/",
        "http://localhost:64346/external_links.html",
        "http://localhost:64346/does-not-exist",
    ],
    "follow": [
        "http://localhost:64346/",
        "http://localhost:64346/external_links.html",
    ],
    "no-follow": [
        "http://localhost:64346/does-not-exist",
    ],
}
excluded_mapped_site = {
    "source": WebSource(
        "http://localhost:64346/",
        sitemap="http://localhost:64346/sitemap_subpage.xml",
        exclude=[
            "http://localhost:64346/undermappe",
            "http://localhost:64346/kontakt.html",
        ],
    ),
    "handles": [
        "http://localhost:64346/",
        "http://localhost:64346/hemmeligheder.html",
    ],
}
links_from_handle = {
    "handle": WebHandle(
        WebSource("http://localhost:64346"), path="/external_links.html"
    ),
    "http-links": [
        Link("http://localhost:64346/", ""),
        Link("http://localhost:64346/vstkom.png", None),
        Link("https://datatracker.ietf.org/doc/html/rfc2606", "rfc2606"),
        Link("http://localhost:64346/intet", "et link, der peger på en intern side der ikke findes"),  # noqa
        Link("http://example.com", "et link, der peger på en ekstern side"),
        Link("http://example.com/nonexistent", "et link, der peger på en ekstern side der ikke findes"),  # noqa
        Link("http://this-side-does-not-exists.invalid", "et link, der ikke har et navneopslag"),  # noqa
    ],
}
infinite_links_site = {
    "source": WebSource("http://localhost:64346/redirect")
}
dead_links = {
    "404": Link("http://localhost:64346/not_found"),
    "410": Link("http://localhost:64346/gone"),
    "421": Link("http://localhost:64346/misdirected_request"),
    "423": Link("http://localhost:64346/locked"),
    "451": Link("http://localhost:64346/unavailable_for_legal_reasons")
}
alive_links = {
    "200": Link("http://localhost:64346/"),
    "403": Link("http://localhost:64346/forbidden"),
    "500": Link("http://localhost:64346/internal_server_error")
}


source_with_path_site = {
    "source": WebSource("http://localhost:64346/undermappe"),
    "handles": [
        "http://localhost:64346/undermappe/",
        "http://localhost:64346/undermappe/vstkom.png",
        "http://localhost:64346/undermappe/rel-page.html",
    ]
}
source_with_path_mapped_site = {
    "source": WebSource(
        "http://localhost:64346/undermappe",
        sitemap="http://localhost:64346/sitemap_subpage.xml"),
    "handles": [
        "http://localhost:64346/undermappe/",
        "http://localhost:64346/undermappe/index.html",
    ]
}
source_with_anchors = {
    "source": WebSource("http://localhost:64346/anchors"),
    "handles": [
        "http://localhost:64346/anchors/",
        "http://localhost:64346/anchors/index2.html",
    ]
}


# mock is way to control what a function returns. By setting e.g.
# @mock.patch('os2datascanner.engine2.model.utilities.sitemap.requests.get',
# side_effect=mocked_requests_get), all invocations of requests.get from sitemap.py
# will return a response based on the url-path and the definitions below.
def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, headers, status_code):
            self.headers = headers
            self.status_code = status_code
            self.content = "Success"
    if args[0] == "https://some-website.com/content-type-application-xml":
        return MockResponse(
            headers={
                'content-type': 'application/xml; charset=UTF-8'},
            status_code=200
        )
    elif args[0] == "https://some-website.com/content-type-text-xml":
        return MockResponse(
            headers={
                'content-type': 'text/xml; charset=UTF-8'},
            status_code=200)
    elif args[0] == "https://some-website.com/content-type-fancy-compressor":
        return MockResponse(
            headers={
                'content-type': 'application/fancy-compressor; original=text/xml'},
            status_code=200)
    elif args[0] == "https://some-website.com/content-type-many-spaces":
        return MockResponse(
            headers={
                'content-type': "application/xml    ; charset=UTF-8"},
            status_code=200)

    return MockResponse(None, 404)


@contextlib.contextmanager
def resolve_any_to_localhost():
    """Wrap urllib3's create_connection to resolve any host to point to 127.0.0.1"""

    _orig_create_connection = connection.create_connection

    def patched_create_connection(address, *args, **kwargs):
        _, port = address
        hostname = "127.0.0.1"
        return _orig_create_connection((hostname, port), *args, **kwargs)

    connection.create_connection = patched_create_connection
    yield

    # restore create_connection at contextmanager exit
    connection.create_connection = _orig_create_connection


class HTTPTestRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Redirect all *.localhost to localhost"""

    def _normal_response(self):
        "just ack and smile"
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def _infinite_redirects(self):
        "return a html-page with one link. Try to follow it..."

        body = \
            f"""
<!doctype html>
<html lang="da">
<head><meta charset="utf-8">
  <title>infinite redirects</title>
</head>
<body>
  <p>Oh no, you fell down the rabbit hole.
     <a href="/redirect?q={time.time()}">click this link to get out!</a>
  </p>
</body>
</html>
"""

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body.encode())
        return

    def _redirect_response(self):
        self.send_response(302)
        self.send_header("Location", "http://localhost:64346" + self.path)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _forbidden_response(self):
        self.send_response(403)
        self.end_headers()

    def _not_found_response(self):
        self.send_response(404)
        self.end_headers()

    def _gone_response(self):
        self.send_response(410)
        self.end_headers()

    def _misdirected_request_response(self):
        self.send_response(421)
        self.end_headers()

    def _locked_response(self):
        self.send_response(423)
        self.end_headers()

    def _unavailable_for_legal_reasons_response(self):
        self.send_response(451)
        self.end_headers()

    def _internal_server_error_response(self):
        self.send_response(500)
        self.end_headers()

    def do_GET(self):
        host = self.headers.get("host")
        if not host.startswith("localhost"):
            self._redirect_response()
        elif self.path.startswith("/redirect"):
            self._infinite_redirects()
        elif self.path.startswith("/not_found"):
            self._not_found_response()
        elif self.path.startswith("/gone"):
            self._gone_response()
        elif self.path.startswith("/misdirected_request"):
            self._misdirected_request_response()
        elif self.path.startswith("/locked"):
            self._locked_response()
        elif self.path.startswith("/unavailable_for_legal_reasons"):
            self._unavailable_for_legal_reasons_response()
        elif self.path.startswith("/forbidden"):
            self._forbidden_response()
        elif self.path.startswith("/internal_server_error"):
            self._internal_server_error_response()
        else:
            super().do_GET()

    def do_HEAD(self):
        host = self.headers.get("host")
        if not host.startswith("localhost"):
            self._redirect_response()
        elif self.path.startswith("/redirect"):
            self._normal_response()
        else:
            super().do_HEAD()


def run_web_server(started):
    cwd = os.getcwd()
    try:
        os.chdir(test_data_path)
        server = http.server.HTTPServer(("", 64346), HTTPTestRequestHandler)

        # The web server is started and listening; let the test runner know
        started.acquire()
        try:
            started.notify()
        finally:
            started.release()

        while True:
            server.handle_request()
    finally:
        os.chdir(cwd)


class Engine2HTTPSetup():
    @classmethod
    def setUpClass(cls):
        with Manager() as manager:
            started = manager.Condition()
            started.acquire()
            try:
                cls._ws = Process(target=run_web_server, args=(started,))
                cls._ws.start()

                # Wait for the web server to check in and notify us that it's
                # ready to be used
                started.wait()
            finally:
                started.release()

    @classmethod
    def tearDownClass(cls):
        cls._ws.terminate()
        cls._ws.join()
        cls._ws = None

    def setUp(self):
        # list all loggers, just example
        loggers = [logging.getLogger(name) for name in  # noqa
                   logging.root.manager.loggerDict]

        # we only want the module and log message
        fmt = "[%(name)s] - [%(message)s]"
        logging.basicConfig(format=fmt)
        logger = logging.getLogger("os2datascanner")
        logger.setLevel(logging.INFO)
        # we have no handler in os2ds (except the NullHandler)
        # logger.addHandler(logging.StreamHandler())


class Engine2HTTPExplorationTest(Engine2HTTPSetup, unittest.TestCase):
    "Explore a source and compare the found handles to a list of expected handles"

    def test_exploration(self):
        "scrape links without using sitemap"

        with SourceManager() as sm:
            presentation = [str(h) for h in site["source"].handles(sm)]
        self.assertCountEqual(
            presentation,
            site["handles"],
            "embedded site without sitemap should have 3 handles",
        )

    def test_exploration_sitemap(self):
        "Use sitemap and no scraping"

        with SourceManager() as sm:
            presentation = [str(h) for h in mapped_site["source"].handles(sm)]
        self.assertCountEqual(
            presentation,
            mapped_site["handles"],
            "embedded site with sitemap should have 3 handles",
        )

    def test_exploration_site_wrong_subdomain(self):
        "Testing for a subdomain that is not part of the _equiv_domains in http.py "

        with resolve_any_to_localhost(), SourceManager() as sm:
            presentation = [str(h) for h in no_equivalent_mapped_site["source"].handles(sm)]
        self.assertCountEqual(
            presentation,
            no_equivalent_mapped_site["handles"],
            "embedded a.www.localhost site with sitemap should have 1 handles",
        )

    def test_exploration_site_agnostic_subdomain(self):
        "Redirect http://www.localhost to http://localhost"

        with resolve_any_to_localhost(), SourceManager() as sm:
            presentation = [str(h) for h in equivalent_mapped_site["source"].handles(sm)]
        self.assertCountEqual(
            presentation,
            equivalent_mapped_site["handles"],
            "embedded redirect site with sitemap should have 4 handles",
        )

    def test_exploration_data_sitemap(self):
        "use a data-sitemap"

        with SourceManager() as sm:
            presentation = [
                str(h) for h in embedded_mapped_site["source"].handles(sm)
            ]
        self.assertCountEqual(
            presentation,
            embedded_mapped_site["handles"],
            "embedded site with data: sitemap should have 2 handles"
        )

    def test_exploration_index(self):
        "use a sitemap that links to other sitemaps"

        with SourceManager() as sm:
            presentation = [
                str(h) for h in indexed_mapped_site["source"].handles(sm)
            ]
        self.assertCountEqual(
            presentation,
            indexed_mapped_site["handles"],
            "embedded site with sitemap index should have 4 handles",
        )

    def test_compressed_sitemap(self):
        "gzip-compressed sitemap"

        # sitemap_index.xml as gzip compressed
        # requests.get("http://localhost:64346/compressed_sitemap.xml.gz").headers
        # > 'Content-type': 'application/gzip', 'Content-Length': '157'
        with SourceManager() as sm:
            presentation = [
                str(h) for h in compressed_mapped_site["source"].handles(sm)
            ]
        self.assertCountEqual(
            presentation,
            compressed_mapped_site["handles"],
            "embedded site with compressed sitemap index should have 4 handles",
        )

    def test_excluded_sites(self):
        "Source with excluded site and path"

        with SourceManager() as sm:
            presentation = [
                str(h) for h in excluded_mapped_site["source"].handles(sm)
            ]
        self.assertCountEqual(
            presentation,
            excluded_mapped_site["handles"],
            "WebSource with excluded sites should have 2 handles"
        )

    def test_external_links_sitemap(self):
        "site mixed with external-, unresponsive- and non-http links"

        with SourceManager() as sm:
            presentation = [
                str(h) for h in external_links_mapped_site["source"].handles(sm)
            ]
        self.assertCountEqual(
            presentation,
            external_links_mapped_site["handles"],
            "site with mixed internal, external and non-http links should have 3 "
            "handles that does not produce an exception")

    def test_infinite_self_links(self):
        """Site that returns a new link in the format /redirect?q=time.time()

        This test both TTL and that the query-part of the url is kept
        """
        i = 0
        with SourceManager() as sm:
            for i, _h in enumerate(infinite_links_site["source"].handles(sm), start=1):
                if i > TTL+2:
                    # prevent infinite redirects if something is broken i http.py
                    break
        self.assertEqual(i, TTL, "Wrong number of links scraped. TTL not respected")

    def test_source_with_path(self):
        "Test that new handles are created correctly if the source contains a path"
        with SourceManager() as sm:
            presentation = [
                str(h) for h in source_with_path_site["source"].handles(sm)
            ]
        self.assertCountEqual(
            presentation,
            source_with_path_site["handles"],
            "Source with path should produce 3 handles")

    def test_source_with_path_sitemap(self):
        "Test that new handles are created correctly if the source contains a path"
        with SourceManager() as sm:
            presentation = [
                str(h) for h in source_with_path_mapped_site["source"].handles(sm)
            ]
        self.assertCountEqual(
            presentation,
            source_with_path_mapped_site["handles"],
            "mapped Source with path should produce 2 handles")

    def test_page_with_anchor_links(self):
        with SourceManager() as sm:
            presentation = [
                str(h) for h in source_with_anchors["source"].handles(sm)
            ]
        self.assertCountEqual(
            presentation,
            source_with_anchors["handles"],
            "links identical but for their anchors should be unified")


class Engine2HTTPSitemapTest(Engine2HTTPSetup, unittest.TestCase):
    def test_sitemap_lm(self):
        "Get LastModified from secret_sitemap.xml"

        with SourceManager() as sm:
            for h in indexed_mapped_site["source"].handles(sm):
                if h.relative_path == "/hemmeligheder2.html":
                    lm = h.follow(sm).get_last_modified()
                    self.assertEqual(
                            (lm.year, lm.month, lm.day),
                            (2011, 12, 1),
                            "secret file's modification date is too late")
                    break
            else:
                self.fail("secret file missing")

    def test_sitemap_error(self):
        "Ensure there's an exception if the sitemap doesn't exist or is malformed"

        # Extant file, valid XML, not a sitemap
        s1 = WebSource(
            "http://localhost:64346/",
            sitemap="http://localhost:64346/not_a_sitemap.xml")
        # Extant file, invalid XML
        s2 = WebSource(
            "http://localhost:64346/",
            sitemap="http://localhost:64346/broken_sitemap.xml")
        # Missing file
        s3 = WebSource(
            "http://localhost:64346/",
            sitemap="http://localhost:64346/missing_sitemap.xml")
        with SourceManager() as sm:
            for source in (s1, s2, s3,):
                with self.assertRaises(Exception):
                    list(source.handles(sm))

    def test_sitemap_xxe(self):
        "Test if the sitemap-parsing is vulnerable to xxe-injection"

        sitemap = "http://localhost:64346/sitemap_xxe.xml"
        self.assertEqual(
            list(process_sitemap_url(sitemap)),
            [('http://localhost:64346/?', None)],
            "sitemap xml-parser is vulnerable to XXE(XML External Entity) injection."
            "Make sure to disable `resolve_entities` in the xml parser"
        )

    @mock.patch('os2datascanner.engine2.model.utilities.sitemap.requests.get',
                side_effect=mocked_requests_get)
    def test_sitemap_content_type_success(self, mock_get):
        "Test successful parsing of different content-types for xml-files"

        url_text_xml = "https://some-website.com/content-type-text-xml"
        url_application_xml = "https://some-website.com/content-type-application-xml"
        url_many_space = "https://some-website.com/content-type-many-spaces"
        self.assertEqual(
            (_get_url_data(url_text_xml),
             _get_url_data(url_application_xml),
             _get_url_data(url_many_space)),
            ("Success", "Success", "Success"),
            "Content-type headers are not recognized as expected.",
        )

    @mock.patch('os2datascanner.engine2.model.utilities.sitemap.requests.get',
                side_effect=mocked_requests_get)
    def test_sitemap_content_type_failure(self, mock_get):
        "Test failed parsing of specific content-types for xml-files"

        url_fancy_compressor = \
            "https://some-website.com/content-type-fancy-compressor"
        with self.assertRaises(TypeError) as context:
            _get_url_data(url_fancy_compressor)

        self.assertTrue(isinstance(context.exception, TypeError),
                        "wrong exceptionType")


class Engine2HTTPResourceTest(Engine2HTTPSetup, unittest.TestCase):
    "Test resources by following handles"

    def test_resource(self):
        "Get content and last-modified of a resource"

        with SourceManager() as sm:
            first_thing = None
            with contextlib.closing(site["source"].handles(sm)) as handles:
                first_thing = next(handles)
            r = first_thing.follow(sm)
            self.assertIsInstance(
                    r.get_last_modified(),
                    datetime,
                    ("{0}: last modification date value is not a"
                     " datetime.datetime").format(first_thing))
            with r.make_stream() as fp:
                stream_raw = fp.read()
            with r.make_path() as p:
                with open(p, "rb") as fp:
                    file_raw = fp.read()
            self.assertEqual(
                stream_raw, file_raw,
                "{0}: file and stream not equal".format(first_thing))

    def test_error(self):
        "Try to follow a handle to a resource that does not exist"

        no_such_file = WebHandle(site["source"], "404.404")
        with SourceManager() as sm:
            r = no_such_file.follow(sm)
            self.assertEqual(
                    r.get_status(),
                    404,
                    "{0}: broken link doesn't have status 404".format(
                            no_such_file))
            with self.assertRaises(Exception):
                r.get_size()
            with self.assertRaises(Exception):
                with r.make_path():
                    pass
            with self.assertRaises(Exception):
                with r.make_stream():
                    pass

    def test_missing_headers(self):
        with SourceManager() as sm:
            first_thing = None
            with contextlib.closing(site["source"].handles(sm)) as handles:
                first_thing = next(handles)
            r = first_thing.follow(sm)

            now = time_now()

            # It is not documented anywhere that WebResource.get_header()
            # returns a live dictionary, so don't depend on this behaviour
            header = r.unpack_header()
            for name in ("content-type", OutputType.LastModified, ):
                if name in header:
                    del header[name]

            self.assertEqual(
                    r.compute_type(),
                    "application/octet-stream",
                    "{0}: unexpected backup MIME type".format(first_thing))
            self.assertGreaterEqual(
                    r.get_last_modified(),
                    now,
                    "{0}: Last-Modified not fresh".format(first_thing))

    def test_mixed_links_resource(self):
        "site mixed with external-, unresponsive- and non-http links"

        follow = []
        nfollow = []
        nerror = []
        with SourceManager() as sm:
            for h in external_links_mapped_site["source"].handles(sm):
                try:
                    if h.follow(sm).check():
                        follow.append(str(h))
                    else:
                        nfollow.append(str(h))
                except RequestException as e:
                    print(
                        f"got an expected exception for {str(h)}:\n{e}")
                    nerror.append(str(h))

        # We could use unittest internal Exception handling
        # with self.assertRaises(RequestException) as e:
        #  ...
        # exception = e.exception
        # if exception:

        # In case we catch an generic Exception, we could test the type, msg, code
        # self.assertTrue(type(exception) in (RequestException, ))
        # self.assertEqual(exception.msg, "timeout ... ", "wrong exception msg")
        self.assertCountEqual(
            follow,
            external_links_mapped_site["follow"],
            "site with broken internal and external links should have 2 "
            "good links")
        self.assertCountEqual(
            nfollow,
            external_links_mapped_site["no-follow"],
            "site with broken internal and external links should have 1 "
            "links that cannot be followed. Either by returning (404 or 410) "
            "or domain-not-found(dns) or another Requests.RequestsException")
        self.assertCountEqual(
            nerror,
            [],
            "site with broken internal and external links should have 0 link that "
            "produces an exception")


class Engine2HTTPTest(Engine2HTTPSetup, unittest.TestCase):
    def test_referrer_urls(self):
        "Assert that second handle's referrer is the first handle"

        with SourceManager() as sm:
            first_thing = None
            second_thing = None
            with contextlib.closing(site["source"].handles(sm)) as handles:
                # We know nothing about the first page (maybe it has a link to
                # itself, maybe it doesn't), but the second page is necessarily
                # something we got to by following a link
                first_thing = next(handles)
                second_thing = next(handles)

            self.assertIsNone(
                first_thing.referrer,
                "{0}: base url without sitemap have a referrer".format(
                    first_thing))
            self.assertTrue(
                second_thing.referrer,
                "{0}: followed link doesn't have a referrer".format(
                    second_thing))
            self.assertEqual(
                second_thing.referrer,
                first_thing,
                "{0}: followed link doesn't have base url as referrer".format(
                    second_thing))
            self.assertEqual(
                second_thing.base_referrer,
                first_thing,
                "{0}: followed link doesn't have base url as base_referrer".format(
                    second_thing))

    def test_old_fashioned_referrers(self):
        """Assert that a WebHandle only have one referrer. The old WebHandle-specific
        implementation allowed for a list with multiple. Now referrer is generic for
        all Handle's

        """

        handle = Handle.from_json_object({
            "type": "web",
            "source": {
                "type": "web",
                "url": "https://www.example.com/"
            },
            "path": "index3.html",
            "referrer": [
                "https://www.example.com/index.html",
                "https://www.example.com/index_old.html"
            ]
        })
        self.assertEqual(
                handle.referrer,
                WebHandle(WebSource("https://www.example.com/"), "index.html"),
                "old-fashioned referrer list not handled correctly")

    def test_lm_hint_json(self):
        h = WebHandle(
            source=WebSource("http://localhost:64346"),
            path="/hemmeligheder2.html",
            last_modified_hint=parse_datetime("2011-12-01"))

        h2 = Handle.from_json_object(h.to_json_object())
        # WebHandle equality doesn't include the referrer map or the
        # Last-Modified hint, so explicitly check that here
        self.assertEqual(
                h.last_modified_hint,
                h2.last_modified_hint,
                "Last-Modified hint didn't survive serialisation")

    def test_empty_page_handling(self):
        self.assertEqual(
                list(make_outlinks("", "http://localhost:64346/empty.html")),
                [],
                "empty page with non-empty list of outgoing links")

    def test_broken_page_handling(self):
        h = WebHandle(
                WebSource("http://localhost:64346"),
                "/broken.html")
        with SourceManager() as sm, h.follow(sm).make_stream() as fp:
            content = fp.read().decode()

        self.assertEqual(
                [link.url for link in make_outlinks(
                        content, "http://localhost:64346/broken.html")],
                ["http://localhost:64346/kontakt.html"],
                "expected one link to be found in broken document")

    def test_links_follow_check(self):
        """Make sure that links which respond with 404, 410, 421, 423, or 451
        status codes are correctly identified by the "check"-function, and that
        other status codes are not."""
        self.assertEqual(check(dead_links['404']), (False, 404))
        self.assertEqual(check(dead_links['410']), (False, 410))
        self.assertEqual(check(dead_links['421']), (False, 421))
        self.assertEqual(check(dead_links['423']), (False, 423))
        self.assertEqual(check(dead_links['451']), (False, 451))
        self.assertEqual(check(alive_links['200']), (True, 200))
        self.assertEqual(check(alive_links['403']), (True, 403))
        self.assertEqual(check(alive_links['500']), (True, 500))


class Engine2HTTPConversionTests(Engine2HTTPSetup, unittest.TestCase):
    def test_links_conversion(self):
        with SourceManager() as sm:
            lr = links_from_handle["handle"].follow(sm)
            links = convert(lr, OutputType.Links, mime_override="text/html")

        self.assertCountEqual(
            links,
            links_from_handle["http-links"],
            "Conversion from html to links did not produce the expected links"
        )
