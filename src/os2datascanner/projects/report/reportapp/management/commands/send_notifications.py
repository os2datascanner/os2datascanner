#!/usr/bin/env python
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
# OS2datascanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (https://os2.eu/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( https://os2.eu/ )
from datetime import timedelta
from os.path import basename
from email.mime.image import MIMEImage

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.template import loader

from os2datascanner.utils.system_utilities import time_now
from os2datascanner.engine2.rules.rule import Sensitivity
from ...views import views
from ...models.documentreport_model import DocumentReport
from ...models.roles.defaultrole_model import DefaultRole


class Command(BaseCommand):
    """Sends emails."""
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            "--header-banner",
            metavar="IMAGE_FILE",
            help="embed the specified image at the top of the email")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="summarise the emails that would be sent without sending"
                 " them")
        parser.add_argument(
            "--all-results",
            action="store_true",
            help="Allows result under 30 days old to be sent")

    def handle(self, **options):  # noqa: CCR001, too high cognitive complexity
        txt_mail_template = loader.get_template("mail/overview.txt")
        html_mail_template = loader.get_template("mail/overview.html")

        image_name = None
        image_content = None
        if options["header_banner"]:
            with open(options["header_banner"], "rb") as fp:
                image_content = fp.read()
            image_name = basename(options["header_banner"])

        shared_context = {
            "image_name": image_name,
            "report_login_url": settings.SITE_URL,
            "institution": settings.NOTIFICATION_INSTITUTION
        }
        for user in User.objects.all():
            context = shared_context.copy()
            context["full_name"] = user.get_full_name() or user.username

            # XXX: this is pretty much all cannibalised from MainPageView
            roles = user.roles.select_subclasses() or [DefaultRole(user=user)]
            results = DocumentReport.objects.none()
            for role in roles:
                results |= role.filter(DocumentReport.objects.all())

            matches = DocumentReport.objects.filter(
                data__matches__matched=True).filter(
                resolution_status__isnull=True)

            # Handles filtering by role + org and sets datasource_last_modified if non existing
            data_results = views.filter_inapplicable_matches(user, matches, roles)

            if not options['all_results']:
                # Exactly 30 days is deemed to be "older than 30 days"
                # and will therefore be shown.
                time_threshold = time_now() - timedelta(days=30)
                older_than_30_days = data_results.filter(
                    datasource_last_modified__lte=time_threshold)
                data_results = older_than_30_days

            if not results or not data_results:
                print("Nothing for user {0}".format(user.username))
                continue

            match_counts = {s: 0 for s in list(Sensitivity)}
            for dr in data_results:
                if dr.matches:
                    match_counts[dr.matches.sensitivity] += 1
            context["matches"] = {
                    k.presentation: v for k, v in match_counts.items()
                    if k != Sensitivity.INFORMATION}.items()
            context["match_count"] = sum(
                    [v for k, v in match_counts.items()
                     if k != Sensitivity.INFORMATION])

            msg = EmailMultiAlternatives(
                    "Der ligger uhåndterede matches i OS2datascanner",
                    txt_mail_template.render(context),
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email])
            msg.attach_alternative(
                    html_mail_template.render(context), "text/html")
            if image_name and image_content:
                mime_image = MIMEImage(image_content)
                mime_image.add_header("Content-Location", image_name)
                msg.attach(mime_image)

            if options["dry_run"]:
                print(user)
                print(msg.message().as_string())
                print("--")
            else:
                try:
                    msg.send()
                except Exception as ex:
                    print("Exception occured while trying to send an email: {0}".format(ex))
