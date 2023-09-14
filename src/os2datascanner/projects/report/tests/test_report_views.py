from os2datascanner.engine2.model.smbc import SMBCHandle, SMBCSource
from os2datascanner.projects.report.organizations.models import (
    Alias, AliasType, Account, Organization)
from datetime import timedelta
from django.test import RequestFactory, TestCase
from django.conf import settings

from os2datascanner.utils.system_utilities import time_now
from os2datascanner.engine2.rules.regex import RegexRule, Sensitivity
from os2datascanner.engine2.pipeline import messages
from os2datascanner.engine2.utilities.datetime import parse_datetime

from ..reportapp.models.documentreport import DocumentReport
from ..reportapp.utils import create_alias_and_match_relations
from ..reportapp.views.report_views import (
    UserReportView, RemediatorView,
    UserArchiveView, RemediatorArchiveView, UndistributedArchiveView)

from .generate_test_data import record_match, record_metadata

"""Shared data"""
time0 = parse_datetime("2020-11-11T11:11:59+02:00")  # noqa
time1 = parse_datetime("2020-10-28T14:21:27+01:00")

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

org_frag = messages.OrganisationFragment(
    name="test_org", uuid="d92ff0c9-f066-40dc-a57e-541721b6c23e")

scan_tag0 = messages.ScanTagFragment(
    time=time_400_days,
    scanner=messages.ScannerFragment(pk=14, name="Dummy test scanner"),
    user=None, organisation=org_frag)
scan_tag1 = messages.ScanTagFragment(
    time=time1,
    scanner=messages.ScannerFragment(pk=11, name="Dummy test scanner2"),
    user=None, organisation=org_frag)
scan_tag2 = messages.ScanTagFragment(
    time=time0,
    scanner=messages.ScannerFragment(pk=11, name="Dummy test scanner2"),
    user=None, organisation=org_frag)
scan_tag_test = messages.ScanTagFragment(
    time=time1,
    scanner=messages.ScannerFragment(pk=20, name="Test scanner", test=True),
    user=None, organisation=org_frag)

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

egon_positive_match_3 = messages.MatchesMessage(
    scan_spec=egon_scan_spec._replace(scan_tag=scan_tag_test),
    handle=egon_adsid_handle_1,
    matched=True,
    matches=[messages.MatchFragment(
        rule=common_rule_2,
        matches=[{"dummy": "match object"}])]
)

egon_positive_match_4 = messages.MatchesMessage(
    scan_spec=egon_scan_spec._replace(scan_tag=scan_tag_test),
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

egon_metadata_3 = messages.MetadataMessage(
    scan_tag=scan_tag_test,
    handle=egon_adsid_handle_1,
    metadata={"filesystem-owner-sid": "S-1-5-21-1180699209-877415012-3182924384-1004",
              }
)

egon_metadata_4 = messages.MetadataMessage(
    scan_tag=scan_tag_test,
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

kjeld_positive_match_3 = messages.MatchesMessage(
    scan_spec=kjeld_scan_spec._replace(scan_tag=scan_tag_test),
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

kjeld_metadata_3 = messages.MetadataMessage(
    scan_tag=scan_tag_test,
    handle=kjeld_adsid_handle,
    metadata={"filesystem-owner-sid": "S-1-5-21-82206942009-31-1004",
              "last-modified": time_30_days.strftime(DATE_FORMAT)}
)


class UserReportViewTest(TestCase):

    def generate_kjeld_data(self):
        record_match(kjeld_positive_match)
        record_metadata(kjeld_metadata)

    def generate_egon_data(self):
        record_match(egon_positive_match)
        record_metadata(egon_metadata)

        record_match(egon_positive_match_1)
        record_metadata(egon_metadata_1)

    def setUp(self):
        self.factory = RequestFactory()
        self.org = Organization.objects.create(
            name='test_org', uuid="d92ff0c9-f066-40dc-a57e-541721b6c23e")
        self.account = Account.objects.create(username='egon', organization=self.org)
        self.generate_kjeld_data()
        self.generate_egon_data()

    def test_userreportview_as_default_role_with_no_matches(self):
        qs = self.userreport_get_queryset()
        self.assertFalse(qs.exists())

    def test_userreportview_as_default_role_with_matches(self):
        kjeld_alias, egon_alias = self.create_adsid_alias_kjeld_and_egon()
        create_alias_and_match_relations(egon_alias)
        qs = self.userreport_get_queryset()
        self.assertEqual(qs.count(), 2)
        egon_alias.delete()
        create_alias_and_match_relations(kjeld_alias)
        # No need to define the queryset again, as it is lazily evaluated.
        self.assertEqual(qs.count(), 1)

    def test_userreportview_as_default_role_with_matches_multiple_aliases(self):
        kjeld_alias, egon_alias = self.create_adsid_alias_kjeld_and_egon()
        create_alias_and_match_relations(egon_alias)
        create_alias_and_match_relations(kjeld_alias)
        qs = self.userreport_get_queryset()
        self.assertEqual(qs.count(), 3)

    def test_userreportview_as_default_role_with_matches_filter_by_scannerjob(self):
        params = '?scannerjob=14&sensitivities=all'
        kjeld_alias, egon_alias = self.create_adsid_alias_kjeld_and_egon()
        create_alias_and_match_relations(egon_alias)
        create_alias_and_match_relations(kjeld_alias)
        qs = self.userreport_get_queryset(params)
        self.assertEqual(qs.count(), 2)

    def test_userreportview_as_default_role_with_matches_filter_by_sensitivity(self):
        params = '?scannerjob=all&sensitivities=1000'
        kjeld_alias, egon_alias = self.create_adsid_alias_kjeld_and_egon()
        create_alias_and_match_relations(egon_alias)
        create_alias_and_match_relations(kjeld_alias)
        qs = self.userreport_get_queryset(params)
        self.assertEqual(qs.count(), 2)

    def test_userreportview_as_default_role_with_matches_filter_by_scannerjob_and_sensitivity(self):
        params = '?scannerjob=14&sensitivities=1000'
        kjeld_alias, egon_alias = self.create_adsid_alias_kjeld_and_egon()
        create_alias_and_match_relations(egon_alias)
        create_alias_and_match_relations(kjeld_alias)
        qs = self.userreport_get_queryset(params)
        self.assertEqual(qs.count(), 1)

    def test_userreportview_as_default_role_with_matches_filter_by_datasource_age_true(self):
        params = '?30-days=true'
        kjeld_alias, egon_alias = self.create_adsid_alias_kjeld_and_egon()
        create_alias_and_match_relations(egon_alias)
        create_alias_and_match_relations(kjeld_alias)
        qs = self.userreport_get_queryset(params)
        self.assertEqual(qs.count(), 3)

    def test_userreportview_as_default_role_with_matches_filter_by_datasource_age_false(self):
        params = '?30-days=false'
        kjeld_alias, egon_alias = self.create_adsid_alias_kjeld_and_egon()
        create_alias_and_match_relations(egon_alias)
        create_alias_and_match_relations(kjeld_alias)
        qs = self.userreport_get_queryset(params)
        self.assertEqual(qs.count(), 2)

    # Helper methods
    def create_adsid_alias_kjeld_and_egon(self):
        kjeld_alias = Alias.objects.create(
            user=self.account.user,
            account=self.account,
            _value='S-1-5-21-82206942009-31-1004',
            _alias_type=AliasType.SID
        )
        egon_alias = Alias.objects.create(
            user=self.account.user,
            account=self.account,
            _value='S-1-5-21-1180699209-877415012-3182924384-1004',
            _alias_type=AliasType.SID
        )
        return kjeld_alias, egon_alias

    def userreport_get_queryset(self, params=''):
        request = self.factory.get('/' + params)
        request.user = self.account.user
        view = UserReportView()
        view.setup(request)
        qs = view.get_queryset()
        return qs


class RemediatorViewTest(TestCase):

    def generate_kjeld_data(self):
        record_match(kjeld_positive_match)
        record_metadata(kjeld_metadata)

    def generate_egon_data(self):
        record_match(egon_positive_match)
        record_metadata(egon_metadata)

        record_match(egon_positive_match_1)
        record_metadata(egon_metadata_1)

    def setUp(self):
        self.factory = RequestFactory()
        self.org = Organization.objects.create(
            name='test_org', uuid="d92ff0c9-f066-40dc-a57e-541721b6c23e")
        self.account = Account.objects.create(username='egon', organization=self.org)
        # Create remediator Alias
        Alias.objects.create(account=self.account, user=self.account.user,
                             _alias_type=AliasType.REMEDIATOR, _value=0)
        self.generate_kjeld_data()
        self.generate_egon_data()

    def test_remediatorview_as_non_remediator(self):
        """Accessing the RemediatorView with no remediator alias should redirect the user
        to the main page."""
        # Delete remediator Alias.
        self.account.aliases.filter(_alias_type=AliasType.REMEDIATOR).delete()

        request = self.factory.get('/remediator/')
        request.user = self.account.user
        response = RemediatorView.as_view()(request)
        self.assertEqual(response.status_code, 302)

    def test_remediatorview_as_remediator(self):
        """Accessing the RemediatorView with a Remediator-role should show all
        reports with no alias relation."""

        request = self.factory.get('/remediator/')
        request.user = self.account.user
        response = RemediatorView.as_view()(request)
        self.assertEqual(response.status_code, 200)

        qs = self.remediator_get_queryset()

        self.assertEqual(qs.count(), 3)

        kjeld_alias, egon_alias = self.create_adsid_alias_kjeld_and_egon()
        create_alias_and_match_relations(egon_alias)
        self.assertEqual(qs.count(), 1)

        create_alias_and_match_relations(kjeld_alias)
        self.assertEqual(qs.count(), 0)

    def test_remediatorview_as_superuser_but_not_remediator(self):
        """Accessing the RemediatorView as a superuser is allowed, but
        will not show any results."""

        # Assign superuser
        self.account.user.is_superuser = True
        self.account.user.save()

        # Verify that there's something for the user
        qs = self.remediator_get_queryset()
        self.assertEqual(qs.count(), 3)

        # Remove remediator alias.
        self.account.aliases.all().delete()

        request = self.factory.get('/remediator/')
        request.user = self.account.user
        response = RemediatorView.as_view()(request)

        # Verify that there's now nothing for the user.
        qs = self.remediator_get_queryset()
        self.assertEqual(qs.count(), 0)

        # Verify that the page can still be visited
        self.assertEqual(response.status_code, 200)

    # Helper functions
    def create_adsid_alias_kjeld_and_egon(self):
        kjeld_alias = Alias.objects.create(
            user=self.account.user,
            account=self.account,
            _value='S-1-5-21-82206942009-31-1004',
            _alias_type=AliasType.SID
        )
        egon_alias = Alias.objects.create(
            user=self.account.user,
            account=self.account,
            _value='S-1-5-21-1180699209-877415012-3182924384-1004',
            _alias_type=AliasType.SID
        )
        return kjeld_alias, egon_alias

    def remediator_get_queryset(self, params=''):
        request = self.factory.get('/remediator/' + params)
        request.user = self.account.user
        view = RemediatorView()
        view.setup(request)
        qs = view.get_queryset()
        return qs


class UserArchiveViewTest(TestCase):
    def generate_kjeld_data(self):
        record_match(kjeld_positive_match)
        record_metadata(kjeld_metadata)

    def generate_egon_data(self):
        record_match(egon_positive_match)
        record_metadata(egon_metadata)

        record_match(egon_positive_match_1)
        record_metadata(egon_metadata_1)

    def setUp(self):
        self.factory = RequestFactory()
        self.org = Organization.objects.create(
            name='test_org', uuid="d92ff0c9-f066-40dc-a57e-541721b6c23e")
        self.account = Account.objects.create(username='egon', organization=self.org)
        self.generate_kjeld_data()
        self.generate_egon_data()

    def test_userarchiveview_as_default_role_with_no_matches(self):
        qs = self.userreport_get_queryset()
        self.assertFalse(qs.exists())

    def test_userarchiveview_as_default_role_with_matches(self):
        kjeld_alias, egon_alias = self.create_adsid_alias_kjeld_and_egon()
        create_alias_and_match_relations(egon_alias)
        qs = self.userreport_get_queryset()
        self.assertEqual(qs.count(), 0)
        DocumentReport.objects.update(resolution_status=0)
        # No need to define the queryset again, as it is lazily evaluated.
        self.assertEqual(qs.count(), 2)
        egon_alias.delete()
        create_alias_and_match_relations(kjeld_alias)
        # No need to define the queryset again, as it is lazily evaluated.
        self.assertEqual(qs.count(), 1)

    def test_userarchiveview_as_default_role_with_matches_multiple_aliases(self):
        kjeld_alias, egon_alias = self.create_adsid_alias_kjeld_and_egon()
        create_alias_and_match_relations(egon_alias)
        create_alias_and_match_relations(kjeld_alias)
        qs = self.userreport_get_queryset()
        self.assertEqual(qs.count(), 0)
        DocumentReport.objects.update(resolution_status=0)
        # No need to define the queryset again, as it is lazily evaluated.
        self.assertEqual(qs.count(), 3)

    def test_userarchiveview_as_default_role_with_matches_filter_by_scannerjob(self):
        params = '?scannerjob=14&sensitivities=all'
        kjeld_alias, egon_alias = self.create_adsid_alias_kjeld_and_egon()
        create_alias_and_match_relations(egon_alias)
        create_alias_and_match_relations(kjeld_alias)
        qs = self.userreport_get_queryset(params)
        self.assertEqual(qs.count(), 0)
        DocumentReport.objects.update(resolution_status=0)
        # No need to define the queryset again, as it is lazily evaluated.
        self.assertEqual(qs.count(), 2)

    def test_userarchiveview_as_default_role_with_matches_filter_by_sensitivity(self):
        params = '?scannerjob=all&sensitivities=1000'
        kjeld_alias, egon_alias = self.create_adsid_alias_kjeld_and_egon()
        create_alias_and_match_relations(egon_alias)
        create_alias_and_match_relations(kjeld_alias)
        qs = self.userreport_get_queryset(params)
        self.assertEqual(qs.count(), 0)
        DocumentReport.objects.update(resolution_status=0)
        # No need to define the queryset again, as it is lazily evaluated.
        self.assertEqual(qs.count(), 2)

    def test_userarchiveview_as_default_role_with_matches_filter_by_scannerjob_and_sensitivity(
            self):
        params = '?scannerjob=14&sensitivities=1000'
        kjeld_alias, egon_alias = self.create_adsid_alias_kjeld_and_egon()
        create_alias_and_match_relations(egon_alias)
        create_alias_and_match_relations(kjeld_alias)
        qs = self.userreport_get_queryset(params)
        self.assertEqual(qs.count(), 0)
        DocumentReport.objects.update(resolution_status=0)
        # No need to define the queryset again, as it is lazily evaluated.
        self.assertEqual(qs.count(), 1)

    def test_userarchiveview_as_default_role_with_matches_filter_by_datasource_age_true(self):
        params = '?30-days=true'
        kjeld_alias, egon_alias = self.create_adsid_alias_kjeld_and_egon()
        create_alias_and_match_relations(egon_alias)
        create_alias_and_match_relations(kjeld_alias)
        qs = self.userreport_get_queryset(params)
        self.assertEqual(qs.count(), 0)
        DocumentReport.objects.update(resolution_status=0)
        # No need to define the queryset again, as it is lazily evaluated.
        self.assertEqual(qs.count(), 3)

    def test_userarchiveview_as_default_role_with_matches_filter_by_datasource_age_false(self):
        params = '?30-days=false'
        kjeld_alias, egon_alias = self.create_adsid_alias_kjeld_and_egon()
        create_alias_and_match_relations(egon_alias)
        create_alias_and_match_relations(kjeld_alias)
        qs = self.userreport_get_queryset(params)
        self.assertEqual(qs.count(), 0)
        DocumentReport.objects.update(resolution_status=0)
        # No need to define the queryset again, as it is lazily evaluated.
        self.assertEqual(qs.count(), 2)

    # Helper methods

    def create_adsid_alias_kjeld_and_egon(self):
        kjeld_alias = Alias.objects.create(
            user=self.account.user,
            account=self.account,
            _value='S-1-5-21-82206942009-31-1004',
            _alias_type=AliasType.SID
        )
        egon_alias = Alias.objects.create(
            user=self.account.user,
            account=self.account,
            _value='S-1-5-21-1180699209-877415012-3182924384-1004',
            _alias_type=AliasType.SID
        )
        return kjeld_alias, egon_alias

    def userreport_get_queryset(self, params=''):
        request = self.factory.get('/archive/reports' + params)
        request.user = self.account.user
        view = UserArchiveView()
        view.setup(request)
        qs = view.get_queryset()
        return qs


class RemediatorArchiveViewTest(TestCase):
    def generate_kjeld_data(self):
        record_match(kjeld_positive_match)
        record_metadata(kjeld_metadata)

    def generate_egon_data(self):
        record_match(egon_positive_match)
        record_metadata(egon_metadata)

        record_match(egon_positive_match_1)
        record_metadata(egon_metadata_1)

    def setUp(self):
        settings.ARCHIVE_TAB = True
        self.factory = RequestFactory()
        self.org = Organization.objects.create(
            name='test_org', uuid="d92ff0c9-f066-40dc-a57e-541721b6c23e")
        self.account = Account.objects.create(username='egon', organization=self.org)
        # Create remediator Alias
        Alias.objects.create(account=self.account, user=self.account.user,
                             _alias_type=AliasType.REMEDIATOR, _value=0)
        self.generate_kjeld_data()
        self.generate_egon_data()

    def test_remediatorarchiveview_not_enabled(self):
        """If the archive tab is not enabled in the configurations, the view
        should redirect the user, even if they are a remediator."""
        settings.ARCHIVE_TAB = False

        request = self.factory.get('/archive/remediator/')
        request.user = self.account.user
        response = RemediatorArchiveView.as_view()(request)
        self.assertEqual(response.status_code, 302)

    def test_remediatorarchiveview_as_non_remediator(self):
        """Accessing the RemediatorView with no role should redirect the user
        to the main page."""
        # Delete remediator Alias.
        self.account.aliases.filter(_alias_type=AliasType.REMEDIATOR).delete()

        request = self.factory.get('/archive/remediator/')
        request.user = self.account.user
        response = RemediatorArchiveView.as_view()(request)
        self.assertEqual(response.status_code, 302)

    def test_remediatorarchiveview_as_remediator(self):
        """Accessing the RemediatorView with a Remediator-role should show all
        reports with no alias relation."""
        request = self.factory.get('/archive/remediator/')
        request.user = self.account.user
        response = RemediatorArchiveView.as_view()(request)
        self.assertEqual(response.status_code, 200)

        qs = self.remediator_get_queryset()
        self.assertEqual(qs.count(), 0)
        DocumentReport.objects.update(resolution_status=0)

        # No need to define the queryset again, as it is lazily evaluated.
        self.assertEqual(qs.count(), 3)

        kjeld_alias, egon_alias = self.create_adsid_alias_kjeld_and_egon()
        create_alias_and_match_relations(egon_alias)
        self.assertEqual(qs.count(), 1)

        create_alias_and_match_relations(kjeld_alias)
        self.assertEqual(qs.count(), 0)

    def test_remediatorview_as_superuser_but_not_remediator(self):
        """Accessing the RemediatorView as a superuser is allowed, but
        will not show any results."""

        # Assign superuser
        self.account.user.is_superuser = True
        self.account.user.save()
        request = self.factory.get('/archive/remediator/')
        request.user = self.account.user
        response = RemediatorArchiveView.as_view()(request)

        # Resolve reports
        DocumentReport.objects.update(resolution_status=0)

        # Verify that there's something for the user.
        qs = self.remediator_get_queryset()
        self.assertEqual(qs.count(), 3)

        # Remove remediator alias.
        self.account.aliases.all().delete()

        # Verify that the page can still be visited
        self.assertEqual(response.status_code, 200)

        # Verify that there's now nothing
        self.assertEqual(qs.count(), 0)

    # Helper functions
    def create_adsid_alias_kjeld_and_egon(self):
        kjeld_alias = Alias.objects.create(
            user=self.account.user,
            account=self.account,
            _value='S-1-5-21-82206942009-31-1004',
            _alias_type=AliasType.SID
        )
        egon_alias = Alias.objects.create(
            user=self.account.user,
            account=self.account,
            _value='S-1-5-21-1180699209-877415012-3182924384-1004',
            _alias_type=AliasType.SID
        )
        return kjeld_alias, egon_alias

    def remediator_get_queryset(self, params=''):
        request = self.factory.get('/archive/remediator' + params)
        request.user = self.account.user
        view = RemediatorArchiveView()
        view.setup(request)
        qs = view.get_queryset()
        return qs


class UndistributedArchiveViewTest(TestCase):
    def generate_kjeld_data(self):
        record_match(kjeld_positive_match_3)
        record_metadata(kjeld_metadata_3)

    def generate_egon_data(self):
        record_match(egon_positive_match_3)
        record_metadata(egon_metadata_3)

        record_match(egon_positive_match_4)
        record_metadata(egon_metadata_4)

    def setUp(self):
        settings.ARCHIVE_TAB = True
        self.factory = RequestFactory()
        self.org = Organization.objects.create(
            name='test_org', uuid="d92ff0c9-f066-40dc-a57e-541721b6c23e")
        self.account = Account.objects.create(username='egon', organization=self.org)
        self.generate_kjeld_data()
        self.generate_egon_data()

    def test_undistributedarchiveview_as_default_role(self):
        """A user without superuser privileges should be redirected when trying
        to access this view."""
        request = self.factory.get('/archive/undistributed')
        request.user = self.account.user
        response = UndistributedArchiveView.as_view()(request)
        self.assertEqual(response.status_code, 302)

    def test_undistributedarchiveview_as_superuser(self):
        """Accessing the UndistributedArchiveView with a superuser-role should
        show all reports with no alias relation."""
        self.account.user.is_superuser = True
        self.account.user.save()

        request = self.factory.get('/archive/undistributed')
        request.user = self.account.user
        response = UndistributedArchiveView.as_view()(request)
        self.assertEqual(response.status_code, 200)

        qs = self.remediator_get_queryset()
        self.assertEqual(qs.count(), 0)
        DocumentReport.objects.update(resolution_status=0)

        # No need to define the queryset again, as it is lazily evaluated.
        self.assertEqual(qs.count(), 3)

    # Helper functions

    def create_adsid_alias_kjeld_and_egon(self):
        kjeld_alias = Alias.objects.create(
            user=self.account.user,
            account=self.account,
            _value='S-1-5-21-82206942009-31-1004',
            _alias_type=AliasType.SID
        )
        egon_alias = Alias.objects.create(
            user=self.account.user,
            account=self.account,
            _value='S-1-5-21-1180699209-877415012-3182924384-1004',
            _alias_type=AliasType.SID
        )
        return kjeld_alias, egon_alias

    def remediator_get_queryset(self, params=''):
        request = self.factory.get('/archive/undistributed' + params)
        request.user = self.account.user
        view = UndistributedArchiveView()
        view.setup(request)
        qs = view.get_queryset()
        return qs
