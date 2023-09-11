import datetime
from io import StringIO
from django.conf import settings
from django.core.mail.message import EmailMultiAlternatives
from django.core.management import call_command
from django.template import loader
from django.test.testcases import TestCase
from os2datascanner.engine2.model.ews import EWSAccountSource, EWSMailHandle
from os2datascanner.engine2.pipeline import messages
from os2datascanner.engine2.rules.regex import RegexRule
from os2datascanner.engine2.rules.rule import Sensitivity
from os2datascanner.engine2.utilities.datetime import parse_datetime
from os2datascanner.projects.report.reportapp.management.commands.send_notifications import \
    Command
from os2datascanner.projects.report.organizations.models.aliases import Alias, AliasType
from os2datascanner.projects.report.reportapp.models.documentreport import DocumentReport
from os2datascanner.projects.report.reportapp.utils import create_alias_and_match_relations
from os2datascanner.projects.report.tests.generate_test_data import \
    record_match
from os2datascanner.utils.system_utilities import time_now
from os2datascanner.projects.report.organizations.models.organization import Organization
from os2datascanner.projects.report.organizations.models.account import Account

from ..reportapp.management.commands import result_collector

time = "2020-11-11T11:11:59+02:00"

org_frag = messages.OrganisationFragment(
    name="test_org", uuid="d92ff0c9-f066-40dc-a57e-541721b6c23e")

scan_tag = messages.ScanTagFragment(
        time=parse_datetime(time),
        scanner=messages.ScannerFragment(pk=14, name="Dummy test scanner"),
        user=None, organisation=org_frag)

scan_tag_1 = messages.ScanTagFragment(
        time=time_now(),
        scanner=messages.ScannerFragment(pk=15, name="Dummy test scanner 1"),
        user=None, organisation=org_frag)

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
    filter_rule=None,
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

metadata_1 = messages.MetadataMessage(
    scan_tag=scan_tag_1,
    handle=email_handle_1,
    metadata={"email-account": "idont@exist.com"}
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
        self.Command.shared_context = {
            "image_name": None,
            "report_login_url": settings.SITE_URL,
            "institution": settings.NOTIFICATION_INSTITUTION
        }
        self.Command.debug_message = {}
        self.Command.debug_message["estimated_amount_of_users"] = 0
        self.Command.debug_message["successful_amount_of_users"] = 0
        self.Command.debug_message["unsuccessful_users"] = []
        self.Command.debug_message["successful_users"] = []

        self.org = Organization.objects.create(
            uuid="d92ff0c9-f066-40dc-a57e-541721b6c23e", name="test_org")

        account_1 = Account.objects.create(username="trofast",
                                           first_name="Alexander",
                                           organization=self.org)

        self.user = account_1.user

        Alias.objects.create(user=self.user, account=account_1,
                             _alias_type=AliasType.REMEDIATOR, _value=0)

        account_2 = Account.objects.create(username="faithfull",
                                           first_name="Alejandro",
                                           organization=self.org)

        self.user_2 = account_2.user

        alias = Alias.objects.create(
            account=account_2,
            user=self.user_2,
            _value="af@pink.com",
            _alias_type=AliasType.EMAIL
        )
        record_match(match)
        record_metadata(metadata)
        create_alias_and_match_relations(alias)

        record_match(match_1)
        record_metadata(metadata_1)
        # get only the reports that have matches, and which have not been resolved
        self.document_reports = DocumentReport.objects.only(
                    "organization", "number_of_matches", "resolution_status"
                ).filter(
                    number_of_matches__gte=1, resolution_status__isnull=True
                )

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
        msg = self.Command.create_email_message(
            None,
            None,
            self.Command.shared_context,
            self.user)

        excpected_msg = EmailMultiAlternatives(
            subject="Der ligger uhåndterede resultater i OS2datascanner",
            body=loader.get_template("mail/overview.txt").render(self.Command.shared_context),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[self.user.email],
            attachments=[],
        )

        self.assertEqual(msg.subject, excpected_msg.subject)
        self.assertEqual(msg.body, excpected_msg.body)
        self.assertEqual(msg.from_email, excpected_msg.from_email)
        self.assertEqual(msg.to, excpected_msg.to)
        self.assertEqual(msg.attachments, excpected_msg.attachments)

    def test_count_user_results_remediator(self):
        """ Asserts that the command counts the correct amount of matches
            for a remediator
        """

        # user has one match, through Remediator alias.
        result_user1 = self.Command.count_user_results(all_results=True,
                                                       results=self.document_reports,
                                                       user=self.user)

        self.assertEqual(result_user1["user_alias_bound_results"], 0)
        self.assertEqual(result_user1["remediator_bound_results"], 1)
        self.assertEqual(result_user1["total_result_count"], 1)

    def test_count_user_results_alias(self):
        # user_2 has one match, through an alias.
        result_user2 = self.Command.count_user_results(all_results=True,
                                                       results=self.document_reports,
                                                       user=self.user_2)

        self.assertEqual(result_user2["user_alias_bound_results"], 1)
        self.assertEqual(result_user2.get("remediator_bound_results"), None)  # Key won't be present
        self.assertEqual(result_user2["total_result_count"], 1)

    def test_schedule_check(self):
        self.org.email_notification_schedule = "RRULE:FREQ=DAILY"
        self.org.save()

        # Check that a daily schedule will return True.
        self.assertTrue(
            self.Command.schedule_check(self.org),
            f'The naive datetime.now() date is: {datetime.datetime.now()}' +
            f'and the aware time_now date is: {time_now()}')

        # Check that a not scheduled day will return False.
        # weekday returns 0 indexed mon-sun day count, we use this to make test consistent.
        # i.e. this test won't "randomly" fail on mondays.
        today_day = time_now().weekday()
        if today_day != 0:
            self.org.email_notification_schedule = "RRULE: FREQ = WEEKLY; BYDAY = MO"
        else:
            self.org.email_notification_schedule = "RRULE: FREQ = WEEKLY; BYDAY = TU"

        self.org.save()
        self.assertFalse(self.Command.schedule_check(self.org))

        # Check that no schedule means we return false.
        self.org.email_notification_schedule = None
        self.org.save()
        self.assertFalse(self.Command.schedule_check(self.org))


def record_metadata(metadata):
    return result_collector.handle_metadata_message(
            metadata.scan_tag,
            metadata.to_json_object())
