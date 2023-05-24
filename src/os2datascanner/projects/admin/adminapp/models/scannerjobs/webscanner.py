# The contents of this file are subject to the Mozilla Public License
# Version 2.0 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
#    http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# OS2datascanner is developed by Magenta in collaboration with the OS2 public
# sector open source network <https://os2.eu/>.
#

import urllib

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from os2datascanner.engine2.model.http import WebSource
from os2datascanner.engine2.rules.links_follow import LinksFollowRule
from os2datascanner.engine2.rules.rule import Sensitivity

from .scanner import Scanner
from ...utils import upload_path_webscan_sitemap

import structlog

logger = structlog.get_logger(__name__)


class WebScanner(Scanner):
    """Web scanner for scanning websites."""

    url = models.CharField(max_length=2048, blank=False, verbose_name='URL')

    linkable = True

    do_link_check = models.BooleanField(
        default=False,
        verbose_name=_("check dead links")
    )

    ROBOTSTXT = 0
    WEBSCANFILE = 1
    METAFIELD = 2

    validation_method_choices = (
        (ROBOTSTXT, "robots.txt"),
        (WEBSCANFILE, "webscan.html"),
        (METAFIELD, "Meta-felt"),
    )

    validation_method = models.IntegerField(
        choices=validation_method_choices,
        default=ROBOTSTXT,
        verbose_name=_("validation method"),
    )

    sitemap = models.FileField(
        upload_to=upload_path_webscan_sitemap,
        blank=True,
        verbose_name=_("sitemap file"),
    )

    sitemap_url = models.CharField(
        max_length=2048,
        blank=True,
        default="",
        verbose_name=_("sitemap url")
    )

    download_sitemap = models.BooleanField(
        default=True,
        verbose_name=_("download Sitemap from server")
    )

    reduce_communication = models.BooleanField(
        default=False,
        verbose_name=_("reduce communication"),
        help_text=_(
                "reduce the number of HTTP requests made to the server by"
                " unconditionally trusting the content of the sitemap")
    )

    exclude_urls = models.CharField(
        max_length=2048,
        blank=True,
        default="",
        verbose_name=_("comma-separated list of urls to exclude"),
        help_text=_(
            "Be sure to include a trailing '/'to enforce path matching, i.e. "
            "https://example.com/images/ instead of https://example.com/images"),
    )

    extended_hints = models.BooleanField(
        default=False,
        verbose_name=_("extended hint support"),
        help_text=_(
                "present pages by their HTML titles and allow the "
                "presentation of links to be overridden")
    )

    def local_all_rules(self) -> list:
        if self.do_link_check:
            rule = LinksFollowRule(sensitivity=Sensitivity.INFORMATION)
            return [
                rule,
            ]
        return []

    @property
    def display_name(self):
        """The name used when displaying the domain on the web page."""
        return f"Domain {self.root_url}"

    @property
    def root_url(self):
        """Return the root url of the domain."""
        url = self.url.replace("*.", "")
        if not self.url.startswith(("http://", "https://")):
            return f"http://{url}"
        else:
            return url

    @property
    def sitemap_full_path(self):
        """Get the absolute path to the uploaded sitemap.xml file."""
        return f"{settings.MEDIA_ROOT}/{self.sitemap.url}"

    @property
    def default_sitemap_path(self):
        return "/sitemap.xml"

    @property
    def needs_revalidation(self):
        try:
            return WebScanner.objects.get(pk=self.pk).url != self.url
        except WebScanner.DoesNotExist:
            return False

    def get_sitemap_url(self):
        """Get the URL of the sitemap.xml file.

        This will be the URL specified by the user, or if not present, the
        URL of the default sitemap.xml file.
        If downloading of the sitemap.xml file is disabled, this will return
        None.
        """
        if not self.download_sitemap:
            return None
        else:
            sitemap_url = self.sitemap_url or self.default_sitemap_path
            return urllib.parse.urljoin(self.root_url, sitemap_url)

    def get_excluded_urls(self):
        """Convert the comma-delimited exclude string to list and validate the urls"""
        # "".split returns [""]. If exlcude_urls is empty, initialize with []
        urls = (
            [url.strip() for url in self.exclude_urls.split(",")] if
            self.exclude_urls else [])
        return urls

    def get_type(self):
        return "web"

    def get_absolute_url(self):
        """Get the absolute URL for scanners."""
        return "/webscanners/"

    def generate_sources(self):
        yield WebSource(self.root_url, sitemap=self.get_sitemap_url(),
                        exclude=self.get_excluded_urls(),
                        sitemap_trusted=self.reduce_communication,
                        extended_hints=self.extended_hints)
