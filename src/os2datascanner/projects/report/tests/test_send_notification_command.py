from io import StringIO
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail.message import EmailMultiAlternatives
from django.core.management import call_command
from django.template import loader
from django.test.testcases import TestCase
from os2datascanner.engine2.model.ews import EWSAccountSource, EWSMailHandle
from os2datascanner.engine2.pipeline import messages
from os2datascanner.engine2.rules.regex import RegexRule
from os2datascanner.engine2.rules.rule import Sensitivity
from os2datascanner.projects.report.reportapp.management.commands.send_notifications import \
    Command
from os2datascanner.projects.report.reportapp.models.aliases.emailalias_model import EmailAlias
from os2datascanner.projects.report.reportapp.models.documentreport_model import DocumentReport
from os2datascanner.projects.report.reportapp.models.roles.remediator_model import Remediator
from os2datascanner.projects.report.reportapp.utils import create_alias_and_match_relations
from os2datascanner.projects.report.tests.generate_test_data import \
    generate_match
from os2datascanner.utils.system_utilities import parse_isoformat_timestamp, time_now
from ..reportapp.management.commands import pipeline_collector

time = "2020-11-11T11:11:59+02:00"
scan_tag = messages.ScanTagFragment(
        time=parse_isoformat_timestamp(time),
        scanner=messages.ScannerFragment(pk=14, name="Dummy test scanner"),
        user=None, organisation=None)

scan_tag_1 = messages.ScanTagFragment(
        time=time_now(),
        scanner=messages.ScannerFragment(pk=15, name="Dummy test scanner 1"),
        user=None, organisation=None)

common_rule = RegexRule(
    expression="Vores hemmelige adgangskode er",
    sensitivity=Sensitivity.CRITICAL
)


common_rule_1 = RegexRule(
    expression="Vores hemmelige adgangskode er",
    sensitivity=Sensitivity.PROBLEM
)

email_handle = EWSMailHandle(
    source=EWSAccountSource(
        domain='@magenta.com',
        server=None,
        admin_user=None,
        admin_password=None,
        user='trofast'),
    path='TDJHGFIHDIJHSKJGHKFUGIUHIUEHIIHE',
    mail_subject='Er det farligt?',
    folder_name='Favorit',
    entry_id=None
)

email_handle_1 = EWSMailHandle(
    source=EWSAccountSource(
        domain='@magewta.com',
        server=None,
        admin_user=None,
        admin_password=None,
        user='trofast'),
    path='TDJHGFIHDIJHSKJGHKFUGIwwUHIUEHIIHE',
    mail_subject='Er det farlwgt?',
    folder_name='Favowrit',
    entry_id=None
)

scan_spec = messages.ScanSpecMessage(
    scan_tag=None,  # placeholder
    source=email_handle.source,
    rule=common_rule,
    configuration={},
    progress=None)

match = messages.MatchesMessage(
        scan_spec=scan_spec._replace(scan_tag=scan_tag),
        handle=email_handle,
        matched=True,
        matches=[messages.MatchFragment(
                rule=common_rule,
                matches=[{"dummy": "match object"}])]
)


match_1 = messages.MatchesMessage(
        scan_spec=scan_spec._replace(scan_tag=scan_tag_1),
        handle=email_handle_1,
        matched=True,
        matches=[messages.MatchFragment(
                rule=common_rule_1,
                matches=[{"dummy": "match object"}])]
)

metadata = messages.MetadataMessage(
    scan_tag=scan_tag,
    handle=email_handle,
    metadata={"email-account": "af@pink.com"}
)


class EmailNotificationTest(TestCase):

    def call_command(self, *args, **kwargs):
        out = StringIO()
        call_command(
            "send_notifications",
            *args,
            stdout=StringIO(),
            stderr=StringIO(),
            **kwargs,
        )
        return out.getvalue()

    def setUp(self):
        self.Command = Command()
        self.Command.txt_mail_template = loader.get_template("mail/overview.txt")
        self.Command.html_mail_template = loader.get_template("mail/overview.html")

        self.user, _ = User.objects.get_or_create(
            username='trofast',
            email='af@purple.com',
            password='top_secret')

        Remediator.objects.create(user=self.user)

        self.user_2, _ = User.objects.get_or_create(
            username='faithfull',
            email='af@pink.com',
            password='top_secret')

        alias = EmailAlias.objects.create(
            user=self.user_2,
            address=self.user_2.email
        )
        generate_match(match)
        generate_metadata(metadata)
        create_alias_and_match_relations(alias)

        generate_match(match_1)
        # get only the reports that have matches, and which have not been resolved
        self.document_reports = DocumentReport.objects.only(
            'organization', 'raw_matches', 'resolution_status'
            ).filter(
            raw_matches__matched=True
            ).filter(
            resolution_status__isnull=True)

        self.context = {
            "image_name": None,
            "report_login_url": settings.SITE_URL,
            "institution": settings.NOTIFICATION_INSTITUTION
        }

    def tearDown(self) -> None:
        self.user.delete()
        del self.user
        self.document_reports.delete()
        del self.document_reports

    def test_handle_(self):
        # test that it runs
        self.call_command('--all-results', '--dry-run')

    def test_create_msg_without_image(self):
        """ Asserts that a created email has the same properties,
             that we expect it to.
        """
        msg = self.Command.create_msg(
            None,
            None,
            self.context,
            self.user)

        excpected_msg = EmailMultiAlternatives(
            subject="Der ligger uhåndterede matches i OS2datascanner",
            body=loader.get_template("mail/overview.txt").render(self.context),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[self.user.email],
            attachments=[],
        )

        self.assertEqual(msg.subject, excpected_msg.subject)
        self.assertEqual(msg.body, excpected_msg.body)
        self.assertEqual(msg.from_email, excpected_msg.from_email)
        self.assertEqual(msg.to, excpected_msg.to)
        self.assertEqual(msg.attachments, excpected_msg.attachments)

    def test_count_matches_in_batches(self):
        """ Asserts that the command counts the correct amount of matches
             and that those matches have been sorted correctly
        """
        result = self.Command.count_matches_in_batches(self.context, self.document_reports)
        expected_result = {
            'Notifikation': 0,
            'Advarsel': 0,
            'Problem': 1,
            'Kritisk': 1,
        }.items()

        self.assertEqual(result['matches'], expected_result)
        self.assertEqual(result['match_count'], 2)

    def test_get_filtered_results(self):
        """ Asserts that the class filters the correct document reports
             based on the users role and organization.
        """
        # remidator should have 1 report as the other one is already assigned
        new_document_reports = self.Command.get_filtered_results(
            self.user, self.document_reports, True)
        self.assertEqual(new_document_reports.count(), 1)

        # .. however, it should not have 1 when the time limit is on:
        new_document_reports = self.Command.get_filtered_results(
            self.user, self.document_reports, False)
        self.assertEqual(new_document_reports.count(), 0)

        # user 2 should have 1 doc report connected through alias
        new_document_reports = self.Command.get_filtered_results(
            self.user_2, self.document_reports, True)
        self.assertEqual(new_document_reports.count(), 1)


def generate_metadata(metadata):
    _, new = pipeline_collector.get_reports_for(
        metadata.handle.to_json_object(),
        metadata.scan_tag)
    pipeline_collector.handle_metadata_message(
        new, metadata.to_json_object())
