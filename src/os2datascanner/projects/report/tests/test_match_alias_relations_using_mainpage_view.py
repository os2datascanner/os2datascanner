from datetime import timedelta
from django.test import RequestFactory, TestCase
from django.contrib.auth.models import User

from os2datascanner.utils.system_utilities import (
        time_now, parse_isoformat_timestamp)
from os2datascanner.engine2.model.ews import (
    EWSMailHandle, EWSAccountSource)
from os2datascanner.engine2.rules.regex import RegexRule, Sensitivity
from os2datascanner.engine2.pipeline import messages

from ..reportapp.management.commands import pipeline_collector
from ..reportapp.management.commands.update_match_alias_relation_table import \
    update_match_alias_relations

from ..reportapp.models.aliases.emailalias_model import EmailAlias
from ..reportapp.models.roles.remediator_model import Remediator
from ..reportapp.utils import create_alias_and_match_relations
from ..reportapp.views.views import MainPageView

"""Shared data"""
time0 = parse_isoformat_timestamp("2020-11-11T11:11:59+02:00")  # noqa
time1 = parse_isoformat_timestamp("2020-10-28T14:21:27+01:00")

# Used to always have a recent date in test.
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
# A timestamp which will always be 30 days old.
# 30 days old is deemed to be older than 30 days.
time_30_days = time_now() - timedelta(days=30)
# A timestamp which will always be 29 days old.
time_29_days = time_now() - timedelta(days=29)

# A 400 day old time stamp. ( could be anything older than 30 days )
# used in scan_tag0 which is used in match with no last-modified metadata
# this assures that if a match with no last-modified metadata slips through,
# it will get assigned the value of scan_tag[time].
# time0 and time1 do not follow correct time format for above to occur
time_400_days = time_now() - timedelta(days=400)

scan_tag0 = messages.ScanTagFragment(
    time=time_400_days,
    scanner=messages.ScannerFragment(pk=14, name="Dummy test scanner"),
    user=None, organisation=None)
scan_tag1 = messages.ScanTagFragment(
    time=time1,
    scanner=messages.ScannerFragment(pk=11, name="Dummy test scanner2"),
    user=None, organisation=None)
scan_tag2 = messages.ScanTagFragment(
    time=time0,
    scanner=messages.ScannerFragment(pk=11, name="Dummy test scanner2"),
    user=None, organisation=None)

common_rule = RegexRule(
    expression="Vores hemmelige adgangskode er",
    sensitivity=Sensitivity.PROBLEM
)

common_rule_2 = RegexRule(
    expression="Vores hemmelige adgangskode er",
    sensitivity=Sensitivity.CRITICAL
)

"""EGON DATA"""
egon_email_handle = EWSMailHandle(
    source=EWSAccountSource(
        domain='olsen.com',
        server=None,
        admin_user=None,
        admin_password=None,
        user='egon'),
    path='TDJHGFIHDIJHSKJGHKFUGIUHIUEHIIHE',
    mail_subject='Jeg har en plan',
    folder_name='Hundehoveder',
    entry_id=None
)

egon_email_handle_1 = EWSMailHandle(
    source=EWSAccountSource(
        domain='olsen.com',
        server=None,
        admin_user=None,
        admin_password=None,
        user='egon'),
    path='DLFIGHDSLUJKGFHEWIUTGHSLJHFGBSVDKJFHG',
    mail_subject='TI STILLE SINDSSYGE KVINDEMENNESKE!',
    folder_name='Hundehoveder',
    entry_id=None
)

egon_email_handle_2 = EWSMailHandle(
    source=EWSAccountSource(
        domain='olsen.com',
        server=None,
        admin_user=None,
        admin_password=None,
        user='egon'),
    path='DLFIGHDSLUJKGFHEWIUTGHSLJHFGBSVDKJFHG',
    mail_subject='Må jeg da lige have lov til at være her?',
    folder_name='Hundehoveder',
    entry_id=None
)

egon_scan_spec = messages.ScanSpecMessage(
    scan_tag=None,  # placeholder
    source=egon_email_handle.source,
    rule=common_rule,
    configuration={},
    progress=None)

egon_positive_match = messages.MatchesMessage(
    scan_spec=egon_scan_spec._replace(scan_tag=scan_tag0),
    handle=egon_email_handle,
    matched=True,
    matches=[messages.MatchFragment(
        rule=common_rule_2,
        matches=[{"dummy": "match object"}])]
)

egon_positive_match_1 = messages.MatchesMessage(
    scan_spec=egon_scan_spec._replace(scan_tag=scan_tag1),
    handle=egon_email_handle_1,
    matched=True,
    matches=[messages.MatchFragment(
        rule=common_rule_2,
        matches=[{"dummy": "match object"}])]
)


egon_positive_match_2 = messages.MatchesMessage(
    scan_spec=egon_scan_spec._replace(scan_tag=scan_tag2),
    handle=egon_email_handle_2,
    matched=True,
    matches=[messages.MatchFragment(
        rule=common_rule_2,
        matches=[{"dummy": "match object"}])]
)

egon_metadata = messages.MetadataMessage(
    scan_tag=scan_tag0,
    handle=egon_email_handle,
    metadata={"email-account": "egon@olsen.com"
              }
)

egon_metadata_1 = messages.MetadataMessage(
    scan_tag=scan_tag1,
    handle=egon_email_handle_1,
    metadata={"email-account": "egon@olsen.com",
              "last-modified": time_29_days.strftime(DATE_FORMAT)
              }
)

egon_metadata_2 = messages.MetadataMessage(
    scan_tag=scan_tag2,
    handle=egon_email_handle_2,
    metadata={"email-account": "egon@olsen.com",
              }
)

"""KJELD DATA"""
kjeld_email_handle = EWSMailHandle(
    source=EWSAccountSource(
        domain='jensen.com',
        server=None,
        admin_user=None,
        admin_password=None,
        user='kjeld'),
    path='TDJHGFIHDIJHSKJGHKFUGIUHIUEHIIHE',
    mail_subject='Er det farligt?',
    folder_name='Indbakke',
    entry_id=None
)

kjeld_scan_spec = messages.ScanSpecMessage(
    scan_tag=None,  # placeholder
    source=kjeld_email_handle.source,
    rule=common_rule,
    configuration={},
    progress=None)

kjeld_positive_match = messages.MatchesMessage(
    scan_spec=kjeld_scan_spec._replace(scan_tag=scan_tag0),
    handle=kjeld_email_handle,
    matched=True,
    matches=[messages.MatchFragment(
        rule=common_rule,
        matches=[{"dummy": "match object"}])]
)

kjeld_metadata = messages.MetadataMessage(
    scan_tag=scan_tag0,
    handle=kjeld_email_handle,
    metadata={"email-account": "kjeld@jensen.com",
              "last-modified": time_30_days.strftime(DATE_FORMAT)}
)


class MatchAliasRelationTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.generate_kjeld_data()
        cls.generate_egon_data()

    @classmethod
    def generate_kjeld_data(cls):
        cls.generate_match(kjeld_positive_match)
        cls.generate_metadata(kjeld_metadata)

    @classmethod
    def generate_egon_data(cls):
        cls.generate_match(egon_positive_match)
        cls.generate_metadata(egon_metadata)

        cls.generate_match(egon_positive_match_1)
        cls.generate_metadata(egon_metadata_1)

    @classmethod
    def generate_new_egon_data(cls):
        cls.generate_match(egon_positive_match_2)
        cls.generate_metadata(egon_metadata_2)

    @classmethod
    def generate_match(cls, match):
        prev, new = pipeline_collector.get_reports_for(
            match.handle.to_json_object(),
            match.scan_spec.scan_tag)
        pipeline_collector.handle_match_message(
            prev, new, match.to_json_object())

    @classmethod
    def generate_metadata(cls, metadata):
        prev, new = pipeline_collector.get_reports_for(
            metadata.handle.to_json_object(),
            metadata.scan_tag)
        pipeline_collector.handle_metadata_message(
            new, metadata.to_json_object())

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='kjeld', email='kjeld@jensen.com', password='top_secret')

    def tearDown(self):
        self.user.delete()
        del self.user
        del self.factory

    def test_mainpage_view_as_default_role_with_no_matches(self):
        qs = self.mainpage_get_queryset()
        self.assertEqual(len(qs), 0)

    def test_mainpage_view_as_remediator_role_with_matches(self):
        remediator = Remediator.objects.create(user=self.user)
        qs = self.mainpage_get_queryset()
        self.assertEqual(len(qs), 3)
        remediator.delete()

    def test_mainpage_view_with_emailalias_egon(self):
        emailalias = EmailAlias.objects.create(
            user=self.user,
            address='EGON@olsen.com'
        )
        create_alias_and_match_relations(emailalias)
        qs = self.mainpage_get_queryset()
        self.assertEqual(len(qs), 2)
        emailalias.delete()

    def test_mainpage_view_with_emailalias_kjeld(self):
        emailalias = EmailAlias.objects.create(
            user=self.user,
            address='kjeld@jensen.com'
        )
        create_alias_and_match_relations(emailalias)
        qs = self.mainpage_get_queryset()
        self.assertEqual(len(qs), 1)
        emailalias.delete()

    def test_mainpage_view_with_emailaliases_egon_kjeld(self):
        emailalias, emailalias1 = self.create_email_alias_kjeld_and_egon()
        create_alias_and_match_relations(emailalias)
        create_alias_and_match_relations(emailalias1)
        qs = self.mainpage_get_queryset()
        self.assertEqual(len(qs), 3)
        emailalias.delete()
        emailalias1.delete()

    def test_mainpage_view_as_remediator_with_emailalias_kjeld(self):
        emailalias = EmailAlias.objects.create(
            user=self.user,
            address='kjeld@jensen.com'
        )
        remediator = Remediator.objects.create(user=self.user)
        qs = self.mainpage_get_queryset()
        self.assertEqual(len(qs), 3)
        remediator.delete()
        emailalias.delete()

    def test_mainpage_view_filter_by_scannerjob(self):
        params = '?scannerjob=14&sensitivities=all'
        emailalias, emailalias1 = self.create_email_alias_kjeld_and_egon()
        create_alias_and_match_relations(emailalias)
        create_alias_and_match_relations(emailalias1)
        qs = self.mainpage_get_queryset(params)
        self.assertEqual(len(qs), 2)
        emailalias.delete()
        emailalias1.delete()

    def test_mainpage_view_filter_by_sensitivities(self):
        params = '?scannerjob=all&sensitivities=1000'
        emailalias, emailalias1 = self.create_email_alias_kjeld_and_egon()
        create_alias_and_match_relations(emailalias)
        create_alias_and_match_relations(emailalias1)
        qs = self.mainpage_get_queryset(params)
        self.assertEqual(len(qs), 2)
        emailalias.delete()
        emailalias1.delete()

    def test_mainpage_view_filter_by_all(self):
        params = '?scannerjob=all&sensitivities=all'
        emailalias, emailalias1 = self.create_email_alias_kjeld_and_egon()
        create_alias_and_match_relations(emailalias)
        create_alias_and_match_relations(emailalias1)
        qs = self.mainpage_get_queryset(params)
        self.assertEqual(len(qs), 3)
        emailalias.delete()
        emailalias1.delete()

    def test_mainpage_view_filter_by_scannerjob_and_sensitivities(self):
        params = '?scannerjob=14&sensitivities=1000'
        emailalias, emailalias1 = self.create_email_alias_kjeld_and_egon()
        create_alias_and_match_relations(emailalias)
        create_alias_and_match_relations(emailalias1)
        qs = self.mainpage_get_queryset(params)
        self.assertEqual(len(qs), 1)
        emailalias.delete()
        emailalias1.delete()

    def test_mainpage_view_filter_by_datasource_age_true(self):
        params = '?30-days=true'
        remediator = Remediator.objects.create(user=self.user)
        qs = self.mainpage_get_queryset(params)
        self.assertEqual(len(qs), 3)
        remediator.delete()

    def test_mainpage_view_filter_by_datasource_age_false(self):
        params = '?30-days=false'
        remediator = Remediator.objects.create(user=self.user)
        qs = self.mainpage_get_queryset(params)
        self.assertEqual(len(qs), 2)
        remediator.delete()

    def test_mainpage_view_filter_by_datasource_age_true_emailalias_egon(self):
        params = '?30-days=true'
        emailalias = EmailAlias.objects.create(
            user=self.user,
            address='egon@olsen.com'
        )
        create_alias_and_match_relations(emailalias)
        qs = self.mainpage_get_queryset(params)
        self.assertEqual(len(qs), 2)
        emailalias.delete()

    def test_mainpage_view_filter_by_scannerjob_and_sensitivities_and_datasource_age(
            self):
        params = '?scannerjob=11&sensitivities=1000&30-days=true'
        remediator = Remediator.objects.create(user=self.user)
        qs = self.mainpage_get_queryset(params)
        self.assertEqual(len(qs), 1)
        remediator.delete()

    def test_mainpage_view_filter_by_sensitivities_and_datasource_age(self):
        params = '?sensitivities=1000&30-days=true'
        remediator = Remediator.objects.create(user=self.user)
        qs = self.mainpage_get_queryset(params)
        self.assertEqual(len(qs), 2)
        remediator.delete()

    def test_mainpage_view_filter_by_scannerjob_and_datasource_age(self):
        params = '?scannerjob=11&30-days=true'
        remediator = Remediator.objects.create(user=self.user)
        qs = self.mainpage_get_queryset(params)
        self.assertEqual(len(qs), 1)
        remediator.delete()

    def test_mainpage_view_with_relation_table(self):
        emailalias, created = EmailAlias.objects.get_or_create(
            user=self.user,
            address='egon@olsen.com'
        )
        create_alias_and_match_relations(emailalias)
        qs = self.mainpage_get_queryset()
        self.assertEqual(len(qs), 2)
        emailalias.delete()

    def test_mainpage_view_with_relation_table_and_incoming_new_matches(self):
        emailalias, created = EmailAlias.objects.get_or_create(
            user=self.user,
            address='egon@olsen.com'
        )
        create_alias_and_match_relations(emailalias)
        qs = self.mainpage_get_queryset()
        self.assertEqual(len(qs), 2)
        MatchAliasRelationTest.generate_new_egon_data()
        qs1 = self.mainpage_get_queryset()
        self.assertEqual(len(qs1), 3)
        emailalias.delete()

    def test_update_relation_management_command(self):
        emailalias, created = EmailAlias.objects.get_or_create(
            user=self.user,
            address='egon@olsen.com'
        )
        qs = self.mainpage_get_queryset()
        self.assertEqual(len(qs), 0)
        MatchAliasRelationTest.generate_new_egon_data()
        update_match_alias_relations()
        qs1 = self.mainpage_get_queryset()
        self.assertEqual(len(qs1), 3)
        emailalias.delete()

# Helper methods
    def create_email_alias_kjeld_and_egon(self):
        emailalias = EmailAlias.objects.create(
            user=self.user,
            address='kjeld@jensen.com'
        )
        emailalias1 = EmailAlias.objects.create(
            user=self.user,
            address='egon@olsen.com'
        )
        return emailalias, emailalias1

    def mainpage_get_queryset(self, params=''):
        request = self.factory.get('/' + params)
        request.user = self.user
        view = MainPageView()
        view.setup(request)
        qs = view.get_queryset()
        return qs
