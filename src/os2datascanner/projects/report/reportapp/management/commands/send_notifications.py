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

    def handle(self, **options):
        self.txt_mail_template = loader.get_template("mail/overview.txt")
        self.html_mail_template = loader.get_template("mail/overview.html")
        self.debug_message = {}

        image_name = None
        image_content = None
        if options["header_banner"]:
            with open(options["header_banner"], "rb") as fp:
                image_content = fp.read()
            image_name = basename(options["header_banner"])

        self.shared_context = {
            "image_name": image_name,
            "report_login_url": settings.SITE_URL,
            "institution": settings.NOTIFICATION_INSTITUTION
        }

        # filter all document reports objects that are matched and is not resoluted.
        document_reports = DocumentReport.objects.only(
            'organization', 'data', 'resolution_status'
            ).filter(
            data__matches__matched=True
            ).filter(
            resolution_status__isnull=True)

        self.debug_message['estimated_amount_of_users'] = 0
        self.debug_message['successful_amount_of_users'] = 0
        self.debug_message['unsuccessful_users'] = []
        self.debug_message['successful_users'] = []

        for user in User.objects.all():
            context = self.shared_context.copy()
            context["full_name"] = user.get_full_name() or user.username

            if not (data_results := self.get_filtered_results(
                    user, document_reports, options['all_results'])
                    ).exists():
                print("Nothing for user {0}".format(user.username))
                continue

            self.debug_message['estimated_amount_of_users'] += 1

            context = self.count_matches_in_batches(context, data_results)
            msg = self.create_msg(image_name, image_content, context, user)
            self.send_to_user(user, msg, options["dry_run"])

        _ = self.debug_message
        if not _["unsuccessful_users"]:
            debug = self.style.SUCCESS(
                f'successfully sent {_["successful_amount_of_users"]} Email to following users'
                f': {_["successful_users"]}'
            )
        else:
            debug = self.style.ERROR(
                f'successfully sent to {_["successful_amount_of_users"]} '
                f'out of {_["estimated_amount_of_users"]} \n'
                f'successful users: {_["successful_users"]} \n'
                f'unsuccessful users: {_["unsuccessful_users"]}'
            )

        self.stdout.write(debug)

    def get_filtered_results(self, user, matches, all_results=False):
        """ Finds results based on the users role and organization
        NOTE: do not iterate over the queryset unless in batches, as
        it will cache all the items and might lead to too high ram usage.
        """
        roles = user.roles.select_subclasses() or [DefaultRole(user=user)]
        data_results = views.filter_inapplicable_matches(user, matches, roles)
        if not all_results:
            # Exactly 30 days is deemed to be "older than 30 days"
            # and will therefore be shown.
            # todo remove this from loop : no reason to keep assigning it
            time_threshold = time_now() - timedelta(days=30)
            data_results = data_results.filter(
                datasource_last_modified__lte=time_threshold)

        return data_results

    def count_matches_in_batches(self, context, data_results):
        """ Iterates over batches and counts them by severity, this is added to the given context.
        matches: all matches with a severity above informational.
        match count: how many matches sorted by each severity.
        """
        match_counts = {s: 0 for s in list(Sensitivity)}
        matches = {}
        match_count = 0

        for document_report in data_results.iterator():
            if document_report.matches:
                match_counts[document_report.matches.sensitivity] += 1

        for k, v in match_counts.items():
            if k != Sensitivity.INFORMATION:
                matches[k.presentation] = v

        match_count += sum([v for k, v in match_counts.items()
                            if k != Sensitivity.INFORMATION])

        # unpack the matches, else the context cannot be rendered
        context['matches'] = matches.items()
        context['match_count'] = match_count
        return context

    def create_msg(self, image_name, image_content, context, user):
        """ Creates a msg ready to send to a user
        If a image have been supplied, it will be used at the top of the mail.
        """

        msg = EmailMultiAlternatives(
            "Der ligger uhåndterede matches i OS2datascanner",
            self.txt_mail_template.render(context),
            settings.DEFAULT_FROM_EMAIL,
            [user.email])
        msg.attach_alternative(self.html_mail_template.render(context), "text/html")

        if image_name and image_content:
            mime_image = MIMEImage(image_content)
            mime_image.add_header("Content-Location", image_name)
            msg.attach(mime_image)

        return msg

    def send_to_user(self, user, msg, dry_run=False):
        try:
            if not dry_run:
                msg.send()
            self.debug_message['successful_users'].append({str(user): user.email})
            self.debug_message['successful_amount_of_users'] += 1
        except Exception as ex:
            self.stdout.write(self.style.ERROR(
                f'Exception occurred while trying to send an email: '
                f'{ex} to user {user}'))
            self.debug_message['unsuccessful_users'].append({str(user): user.email})
