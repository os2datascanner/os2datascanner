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

from os.path import basename
from email.mime.image import MIMEImage
import argparse

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.template import loader

from ...views.views import RENDERABLE_RULES
from ...models.documentreport_model import DocumentReport
from os2datascanner.engine2.rules.rule import Sensitivity


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

    def handle(self, **options):
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
            "report_login_url": settings.NOTIFICATION_LOGIN_URL,
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

            if not results:
                print("Nothing for user {0}".format(user.name))
                continue

            # Filter out anything we don't know how to show in the UI
            data_results = []
            for result in results:
                if result.data and "matches" in result.data and result.data["matches"]:
                    mm = result.data["matches"]
                    renderable_matches = [cm for cm in mm["matches"]
                            if cm["rule"]["type"] in RENDERABLE_RULES]
                    if renderable_matches:
                        mm["matches"] = renderable_matches
                        data_results.append(result)

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
                    "Der ligger uhåndteret matches i OS2datascanner",
                    txt_mail_template.render(context),
                    settings.NOTIFICATION_FROM,
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
                msg.send()
