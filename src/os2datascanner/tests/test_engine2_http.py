import os
import os.path
import http.server
from datetime import datetime
import unittest
import contextlib
from multiprocessing import Manager, Process

from os2datascanner.engine2.model.core import (Handle,
        Source, SourceManager, UnknownSchemeError)
from os2datascanner.engine2.model.http import WebSource, WebHandle
from os2datascanner.engine2.model.utilities.datetime import parse_datetime
from os2datascanner.engine2.conversions.types import OutputType
from os2datascanner.engine2.conversions.utilities.results import SingleResult


here_path = os.path.dirname(__file__)
test_data_path = os.path.join(here_path, "data", "www")


def run_web_server(started):
    cwd = os.getcwd()
    try:
        os.chdir(test_data_path)
        server = http.server.HTTPServer(
                ('', 64346),
                http.server.SimpleHTTPRequestHandler)

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


site = WebSource("http://localhost:64346/")
mapped_site = WebSource("http://localhost:64346/",
        sitemap="http://localhost:64346/sitemap.xml")
indexed_mapped_site = WebSource("http://localhost:64346/",
        sitemap="http://localhost:64346/sitemap_index.xml")
embedded_mapped_site = WebSource("http://localhost:64346/",
        sitemap="data:text/xml,<urlset xmlns=\"http://www.sitemaps.org/schemas"
                "/sitemap/0.9\"><url><loc>http://localhost:64346/hemmeligheder"
                "2.html</loc></url></urlset>")


class Engine2HTTPTest(unittest.TestCase):
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

    def test_exploration(self):
        count = 0
        with SourceManager() as sm:
            for h in site.handles(sm):
                count += 1
        self.assertEqual(
                count,
                3,
                "embedded site should have 3 handles")

    def test_exploration_sitemap(self):
        count = 0
        with SourceManager() as sm:
            for h in mapped_site.handles(sm):
                count += 1
        self.assertEqual(
                count,
                5,
                "embedded site with sitemap should have 5 handles")

    def test_exploration_data_sitemap(self):
        count = 0
        with SourceManager() as sm:
            for h in embedded_mapped_site.handles(sm):
                count += 1
        self.assertEqual(
                count,
                4,
                "embedded site with data: sitemap should have 4 handles")

    def test_exploration_index(self):
        count = 0
        with SourceManager() as sm:
            for h in indexed_mapped_site.handles(sm):
                count += 1
        self.assertEqual(
                count,
                6,
                "embedded site with sitemap index should have 6 handles")

    def test_sitemap_lm(self):
        count = 0
        with SourceManager() as sm:
            for h in indexed_mapped_site.handles(sm):
                if h.relative_path == "hemmeligheder2.html":
                    lm = h.follow(sm).get_last_modified().value
                    self.assertEqual(
                            (lm.year, lm.month, lm.day),
                            (2011, 12, 1),
                            "secret file's modification date is too late")
                    break
            else:
                self.fail("secret file missing")

    def test_resource(self):
        with SourceManager() as sm:
            first_thing = None
            with contextlib.closing(site.handles(sm)) as handles:
                first_thing = next(handles)
            r = first_thing.follow(sm)
            self.assertIsInstance(
                    r.get_last_modified(),
                    SingleResult,
                    ("{0}: last modification date is not a"
                            " SingleResult").format(first_thing))
            self.assertIsInstance(
                    r.get_last_modified().value,
                    datetime,
                    ("{0}: last modification date value is not a"
                            " datetime.datetime").format(first_thing))
            with r.make_stream() as fp:
                stream_raw = fp.read()
            with r.make_path() as p:
                with open(p, "rb") as fp:
                    file_raw = fp.read()
            self.assertEqual(stream_raw, file_raw,
                    "{0}: file and stream not equal".format(first_thing))

    def test_referrer_urls(self):
        with SourceManager() as sm:
            second_thing = None
            with contextlib.closing(site.handles(sm)) as handles:
                # We know nothing about the first page (maybe it has a link to
                # itself, maybe it doesn't), but the second page is necessarily
                # something we got to by following a link
                next(handles)
                second_thing = next(handles)
            self.assertTrue(
                    second_thing.get_referrer_urls(),
                    "{0}: followed link doesn't have a referrer".format(
                            second_thing))

    def test_error(self):
        no_such_file = WebHandle(site, "404.404")
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
                with r.make_path() as p:
                    pass
            with self.assertRaises(Exception):
                with r.make_stream() as s:
                    pass

    def test_sitemap_error(self):
        # Extant file, valid XML, not a sitemap
        s1 = WebSource("http://localhost:64346/",
                sitemap="http://localhost:64346/not_a_sitemap.xml")
        # Extant file, invalid XML
        s2 = WebSource("http://localhost:64346/",
                sitemap="http://localhost:64346/broken_sitemap.xml")
        # Missing file
        s3 = WebSource("http://localhost:64346/",
                sitemap="http://localhost:64346/missing_sitemap.xml")
        with SourceManager() as sm:
            for source in (s1, s2, s3,):
                with self.assertRaises(Exception):
                    list(source.handles(sm))

    def test_missing_headers(self):
        with SourceManager() as sm:
            first_thing = None
            with contextlib.closing(site.handles(sm)) as handles:
                first_thing = next(handles)
            r = first_thing.follow(sm)

            now = datetime.now()

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
                    r.get_last_modified().value,
                    now,
                    "{0}: Last-Modified not fresh".format(first_thing))

    def test_lm_hint_json(self):
        h = WebHandle(
                WebSource("http://localhost:64346/"),
                "hemmeligheder2.html")
        h.set_last_modified_hint(parse_datetime("2011-12-01"))

        h2 = Handle.from_json_object(h.to_json_object())
        # WebHandle equality doesn't include the referrer map or the
        # Last-Modified hint, so explicitly check that here
        self.assertEqual(
                h.get_last_modified_hint(),
                h2.get_last_modified_hint(),
                "Last-Modified hint didn't survive serialisation")
