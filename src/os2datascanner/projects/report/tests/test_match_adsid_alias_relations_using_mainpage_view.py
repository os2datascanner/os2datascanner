from os2datascanner.engine2.model.smb import SMBHandle, SMBSource
from os2datascanner.engine2.model.smbc import SMBCHandle, SMBCSource
from os2datascanner.projects.report.organizations.models.aliases import Alias, AliasType
from os2datascanner.projects.report.reportapp.templatetags.handle_extras import (
    find_file_folder, find_parent)
from parameterized import parameterized
from datetime import timedelta
from django.test import RequestFactory, TestCase
from django.contrib.auth.models import User

from os2datascanner.utils.system_utilities import (
    time_now, parse_isoformat_timestamp)
from os2datascanner.engine2.rules.regex import RegexRule, Sensitivity
from os2datascanner.engine2.pipeline import messages

from ..reportapp.management.commands.update_match_alias_relation_table import \
    update_match_alias_relations

from ..reportapp.models.roles.remediator_model import Remediator
from ..reportapp.utils import create_alias_and_match_relations
from ..reportapp.views.views import MainPageView

from .generate_test_data import record_match, record_metadata


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
egon_adsid_handle = SMBCHandle(
    source=SMBCSource(
                "//172.16.20.106/1234/",
                "username"),
    relpath="os2datascanner.pdf"
)

egon_adsid_handle_1 = SMBCHandle(
    source=SMBCSource(
                "//172.16.20.107/toender/",
                "username"),
    relpath="os2datascanner.png"
)

egon_adsid_handle_2 = SMBCHandle(
    source=SMBCSource(
                "//172.16.20.108/toender/presentations",
                "username"),
    relpath="os2datascanner.txt"
)

egon_scan_spec = messages.ScanSpecMessage(
    scan_tag=None,  # placeholder
    source=egon_adsid_handle.source,
    rule=common_rule,
    configuration={},
    filter_rule=None,
    progress=None)

egon_positive_match = messages.MatchesMessage(
    scan_spec=egon_scan_spec._replace(scan_tag=scan_tag0),
    handle=egon_adsid_handle,
    matched=True,
    matches=[messages.MatchFragment(
        rule=common_rule_2,
        matches=[{"dummy": "match object"}])]
)

egon_positive_match_1 = messages.MatchesMessage(
    scan_spec=egon_scan_spec._replace(scan_tag=scan_tag1),
    handle=egon_adsid_handle_1,
    matched=True,
    matches=[messages.MatchFragment(
        rule=common_rule_2,
        matches=[{"dummy": "match object"}])]
)


egon_positive_match_2 = messages.MatchesMessage(
    scan_spec=egon_scan_spec._replace(scan_tag=scan_tag2),
    handle=egon_adsid_handle_2,
    matched=True,
    matches=[messages.MatchFragment(
        rule=common_rule_2,
        matches=[{"dummy": "match object"}])]
)

egon_metadata = messages.MetadataMessage(
    scan_tag=scan_tag0,
    handle=egon_adsid_handle,
    metadata={"filesystem-owner-sid": "S-1-5-21-1180699209-877415012-3182924384-1004"
              }
)

egon_metadata_1 = messages.MetadataMessage(
    scan_tag=scan_tag1,
    handle=egon_adsid_handle_1,
    metadata={"filesystem-owner-sid": "S-1-5-21-1180699209-877415012-3182924384-1004",
              "last-modified": time_29_days.strftime(DATE_FORMAT)
              }
)

egon_metadata_2 = messages.MetadataMessage(
    scan_tag=scan_tag2,
    handle=egon_adsid_handle_2,
    metadata={"filesystem-owner-sid": "S-1-5-21-1180699209-877415012-3182924384-1004",
              }
)

"""KJELD DATA"""
kjeld_adsid_handle = SMBCHandle(
    source=SMBCSource(
                "//172.16.20.108/toender/presentations",
                "username"),
    relpath="os2datascanner.pdf"
)

kjeld_scan_spec = messages.ScanSpecMessage(
    scan_tag=None,  # placeholder
    source=kjeld_adsid_handle.source,
    rule=common_rule,
    configuration={},
    filter_rule=None,
    progress=None)

kjeld_positive_match = messages.MatchesMessage(
    scan_spec=kjeld_scan_spec._replace(scan_tag=scan_tag0),
    handle=kjeld_adsid_handle,
    matched=True,
    matches=[messages.MatchFragment(
        rule=common_rule,
        matches=[{"dummy": "match object"}])]
)

kjeld_metadata = messages.MetadataMessage(
    scan_tag=scan_tag0,
    handle=kjeld_adsid_handle,
    metadata={"filesystem-owner-sid": "S-1-5-21-82206942009-31-1004",
              "last-modified": time_30_days.strftime(DATE_FORMAT)}
)


class MatchADSIDAliasRelationTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.generate_kjeld_data()
        cls.generate_egon_data()

    @classmethod
    def generate_kjeld_data(cls):
        record_match(kjeld_positive_match)
        record_metadata(kjeld_metadata)

    @classmethod
    def generate_egon_data(cls):
        record_match(egon_positive_match)
        record_metadata(egon_metadata)

        record_match(egon_positive_match_1)
        record_metadata(egon_metadata_1)

    @classmethod
    def generate_new_egon_data(cls):
        record_match(egon_positive_match_2)
        record_metadata(egon_metadata_2)

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='egon', email='egon@olsen.com', password='top_secret')

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

    def test_mainpage_view_with_alias_egon(self):
        _, egon_alias = self.create_adsid_alias_kjeld_and_egon()
        create_alias_and_match_relations(egon_alias)
        qs = self.mainpage_get_queryset()
        self.assertEqual(len(qs), 2)
        egon_alias.delete()

    def test_mainpage_view_with_adsidalias_kjeld(self):
        kjeld_alias, _ = self.create_adsid_alias_kjeld_and_egon()
        create_alias_and_match_relations(kjeld_alias)
        qs = self.mainpage_get_queryset()
        self.assertEqual(len(qs), 1)
        kjeld_alias.delete()

    def test_mainpage_view_with_adsidaliases_egon_kjeld(self):
        kjeld_alias, egon_alias = self.create_adsid_alias_kjeld_and_egon()
        create_alias_and_match_relations(kjeld_alias)
        create_alias_and_match_relations(egon_alias)
        qs = self.mainpage_get_queryset()
        self.assertEqual(len(qs), 3)
        kjeld_alias.delete()
        egon_alias.delete()

    def test_mainpage_view_as_remediator_with_adsidalias_kjeld(self):
        kjeld_alias, _ = self.create_adsid_alias_kjeld_and_egon()
        remediator = Remediator.objects.create(user=self.user)
        qs = self.mainpage_get_queryset()
        self.assertEqual(len(qs), 3)
        remediator.delete()
        kjeld_alias.delete()

    def test_mainpage_view_filter_by_scannerjob(self):
        params = '?scannerjob=14&sensitivities=all'
        kjeld_alias, egon_alias = self.create_adsid_alias_kjeld_and_egon()
        create_alias_and_match_relations(kjeld_alias)
        create_alias_and_match_relations(egon_alias)
        qs = self.mainpage_get_queryset(params)
        self.assertEqual(len(qs), 2)
        kjeld_alias.delete()
        egon_alias.delete()

    def test_mainpage_view_filter_by_sensitivities(self):
        params = '?scannerjob=all&sensitivities=1000'
        kjeld_alias, egon_alias = self.create_adsid_alias_kjeld_and_egon()
        create_alias_and_match_relations(kjeld_alias)
        create_alias_and_match_relations(egon_alias)
        qs = self.mainpage_get_queryset(params)
        self.assertEqual(len(qs), 2)
        kjeld_alias.delete()
        egon_alias.delete()

    def test_mainpage_view_filter_by_all(self):
        params = '?scannerjob=all&sensitivities=all'
        kjeld_alias, egon_alias = self.create_adsid_alias_kjeld_and_egon()
        create_alias_and_match_relations(kjeld_alias)
        create_alias_and_match_relations(egon_alias)
        qs = self.mainpage_get_queryset(params)
        self.assertEqual(len(qs), 3)
        kjeld_alias.delete()
        egon_alias.delete()

    def test_mainpage_view_filter_by_scannerjob_and_sensitivities(self):
        params = '?scannerjob=14&sensitivities=1000'
        kjeld_alias, egon_alias = self.create_adsid_alias_kjeld_and_egon()
        create_alias_and_match_relations(kjeld_alias)
        create_alias_and_match_relations(egon_alias)
        qs = self.mainpage_get_queryset(params)
        self.assertEqual(len(qs), 1)
        kjeld_alias.delete()
        egon_alias.delete()

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

    def test_mainpage_view_filter_by_datasource_age_true_adsidalias_egon(self):
        params = '?30-days=true'
        _, egon_alias = self.create_adsid_alias_kjeld_and_egon()
        create_alias_and_match_relations(egon_alias)
        qs = self.mainpage_get_queryset(params)
        self.assertEqual(len(qs), 2)
        egon_alias.delete()

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
        alias, created = Alias.objects.get_or_create(
            user=self.user,
            _value='S-1-5-21-1180699209-877415012-3182924384-1004',
            _alias_type=AliasType.SID
        )
        create_alias_and_match_relations(alias)
        qs = self.mainpage_get_queryset()
        self.assertEqual(len(qs), 2)
        alias.delete()

    @parameterized.expand([
        ("Normal match", 'S-1-5-21-1180699209-877415012-3182924384-1004', 2, 3),
        ("Normal match", '', 0, 0)])
    def test_mainpage_view_with_relation_table_and_incoming_new_matches(
            self, _, sid, expected1, expected2):
        alias, created = Alias.objects.get_or_create(
            user=self.user,
            _value=sid,
            _alias_type=AliasType.SID
        )
        create_alias_and_match_relations(alias)
        qs = self.mainpage_get_queryset()
        self.assertEqual(len(qs), expected1)
        MatchADSIDAliasRelationTest.generate_new_egon_data()
        qs = self.mainpage_get_queryset()
        self.assertEqual(len(qs), expected2)
        alias.delete()

    def test_update_relation_management_command(self):
        alias, created = Alias.objects.get_or_create(
            user=self.user,
            _value='S-1-5-21-1180699209-877415012-3182924384-1004',
            _alias_type=AliasType.SID
        )
        qs = self.mainpage_get_queryset()
        self.assertEqual(len(qs), 0)
        MatchADSIDAliasRelationTest.generate_new_egon_data()
        update_match_alias_relations()
        qs1 = self.mainpage_get_queryset()
        self.assertEqual(len(qs1), 3)
        alias.delete()

    def test_find_file_folder_filter_on_handle(self):
        handle1 = SMBHandle(
            SMBSource(
                "//172.16.20.108/toender/presentations",
                "username"),
            "os2datascanner.pdf")
        handle1 = find_parent(handle1, handle1.type_label)
        converted_handle1 = find_file_folder(handle1, force=True)
        handle2 = SMBHandle(
            SMBSource(
                "\\\\172.16.20.108\\toender\presentations",  # noqa: W605
                "username", "topsecret", "WORKGROUP8"),
            "os2datascanner.pdf")
        handle2 = find_parent(handle2, handle2.type_label)
        converted_handle2 = find_file_folder(handle2, force=True)
        self.assertEqual(
            converted_handle1, 'file://172.16.20.108/toender/presentations')
        self.assertEqual(
            converted_handle2, 'file://172.16.20.108/toender/presentations')

# Helper methods
    def create_adsid_alias_kjeld_and_egon(self):
        kjeld_alias = Alias.objects.create(
            user=self.user,
            _value='S-1-5-21-82206942009-31-1004',
            _alias_type=AliasType.SID
        )
        egon_alias = Alias.objects.create(
            user=self.user,
            _value='S-1-5-21-1180699209-877415012-3182924384-1004',
            _alias_type=AliasType.SID
        )
        return kjeld_alias, egon_alias

    def mainpage_get_queryset(self, params=''):
        request = self.factory.get('/' + params)
        request.user = self.user
        view = MainPageView()
        view.setup(request)
        qs = view.get_queryset()
        return qs
