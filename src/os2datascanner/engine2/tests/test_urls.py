import unittest

from os2datascanner.engine2.demo.utils import DemoSourceWrapper as TestSourceWrapper
from os2datascanner.engine2.model.data import DataSource
from os2datascanner.engine2.model.file import FilesystemSource
from os2datascanner.engine2.model.http import SecureWebSource, WebSource
from os2datascanner.engine2.model.smb import SMBSource
from os2datascanner.engine2.model.smbc import SMBCSource


class URLTests(unittest.TestCase):
    def test_sources(self):
        sources_and_urls = [
            (FilesystemSource("/usr"), "file:///usr"),
            (
                SMBSource("//10.0.0.30/Share$/Documents"),
                "smb://10.0.0.30/Share%24/Documents",
            ),
            (
                SMBSource("//10.0.0.30/Share$/Documents", "FaithfullA"),
                "smb://FaithfullA@10.0.0.30/Share%24/Documents",
            ),
            (
                SMBSource(
                    "//10.0.0.30/Share$/Documents",
                    "FaithfullA",
                    "secretpassword",
                ),
                "smb://FaithfullA:secretpassword@10.0.0.30/Share%24/Documents",
            ),
            (
                SMBSource(
                    "//10.0.0.30/Share$/Documents",
                    "FaithfullA",
                    "secretpassword",
                    "SYSGRP",
                ),
                "smb://SYSGRP;FaithfullA:secretpassword@10.0.0.30/Share%24"
                "/Documents",
            ),
            (
                SMBSource(
                    "//10.0.0.30/Share$/Documents",
                    "FaithfullA",
                    None,
                    "SYSGRP",
                ),
                "smb://SYSGRP;FaithfullA@10.0.0.30/Share%24/Documents",
            ),
            (
                SMBCSource(
                    "//INT-SRV-01/Q$",
                    "FaithfullA",
                    None,
                    "SYSGRP",
                ),
                "smbc://SYSGRP;FaithfullA@INT-SRV-01/Q%24",
            ),
            (
                SMBCSource(
                    "//INT-SRV-01.intern.vstkom.dk/Q$",
                    "FaithfullA",
                    "secretpassword",
                    None,
                ),
                "smbc://intern.vstkom.dk;FaithfullA:secretpassword@INT-SRV-01.intern.vstkom.dk/Q%24",  # noqa
            ),
            (
                SMBCSource(
                    "//INT-SRV-01.intern.vstkom.dk/Q$",
                    "FaithfullA",
                    "secretpassword",
                    "SYSGRP",
                ),
                "smbc://SYSGRP;FaithfullA:secretpassword@INT-SRV-01.intern.vstkom.dk/Q%24",
            ),
            (
                SMBCSource(
                    "//INT-SRV-01.intern.vstkom.dk/Q$",
                    "FaithfullA",
                    None,
                    "",
                ),
                "smbc://FaithfullA@INT-SRV-01.intern.vstkom.dk/Q%24",
            ),
            # Remove trailing / on base url if present. / should be part of the path
            (WebSource("http://www.example.com/"), "http://www.example.com"),
            (
                SecureWebSource("https://www.example.com"),
                "https://www.example.com",
            ),
            (
                DataSource(b"This is a test", "text/plain"),
                "data:text/plain;base64,VGhpcyBpcyBhIHRlc3Q=",
            ),
        ]

        for source, url in sources_and_urls:
            with self.subTest(url):
                generated_url = TestSourceWrapper.to_url(source)
                self.assertEqual(url, generated_url)
