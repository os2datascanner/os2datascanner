import dateutil.parser
from datetime import datetime, timedelta
from typing import List, Tuple

from django.test import RequestFactory, TestCase
from django.contrib.auth.models import User
from django.utils import timezone

from os2datascanner.utils.system_utilities import parse_isoformat_timestamp
from os2datascanner.engine2.model.ews import (
        EWSMailHandle, EWSAccountSource)
from os2datascanner.engine2.rules.regex import RegexRule, Sensitivity
from os2datascanner.engine2.pipeline import messages

from ..reportapp.models.aliases.emailalias_model import EmailAlias
from ..reportapp.models.documentreport_model import DocumentReport
from ..reportapp.models.roles.leader_model import Leader
from ..reportapp.models.roles.dpo_model import DataProtectionOfficer
from ..reportapp.utils import create_alias_and_match_relations
from ..reportapp.views.views import StatisticsPageView, LeaderStatisticsPageView
from ..reportapp.utils import iterate_queryset_in_batches

from .generate_test_data import record_match, record_metadata


"""Shared data"""
time0 = "2020-11-11T11:11:59+02:00"
time1 = "2020-10-28T14:21:27+01:00"
time2 = "2020-09-22T04:07:12+03:00"

scan_tag0 = messages.ScanTagFragment(
        time=parse_isoformat_timestamp(time0),
        scanner=messages.ScannerFragment(pk=14, name="Dummy test scanner"),
        user=None, organisation=None)

scan_tag1 = messages.ScanTagFragment(
        time=parse_isoformat_timestamp(time1),
        scanner=messages.ScannerFragment(pk=11, name="Dummy test scanner2"),
        user=None, organisation=None)

scan_tag2 = messages.ScanTagFragment(
        time=parse_isoformat_timestamp(time2),
        scanner=messages.ScannerFragment(pk=17, name="Dummy test scanner3"),
        user=None, organisation=None)

common_rule = RegexRule(
    expression="Vores hemmelige adgangskode er",
    sensitivity=Sensitivity.PROBLEM
)

common_rule_2 = RegexRule(
    expression="Vores hemmelige adgangskode er",
    sensitivity=Sensitivity.CRITICAL
)

common_rule_3 = RegexRule(
    expression="Vores hemmelige adgangskode er",
    sensitivity=Sensitivity.WARNING
)

"""EGON DATA"""
egon_email_handle = EWSMailHandle(
    source=EWSAccountSource(
        domain='@olsen.com',
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
        domain='@olsen.com',
        server=None,
        admin_user=None,
        admin_password=None,
        user='egon'),
    path='DLFIGHDSLUJKGFHEWIUTGHSLJHFGBSVDKJFHG',
    mail_subject='TI STILLE SINDSSYGE KVINDEMENNESKE!',
    folder_name='Fnatmider',
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

egon_metadata = messages.MetadataMessage(
    scan_tag=scan_tag0,
    handle=egon_email_handle,
    metadata={"email-account": "egon@olsen.com"}
)

egon_metadata_1 = messages.MetadataMessage(
    scan_tag=scan_tag1,
    handle=egon_email_handle_1,
    metadata={"email-account": "egon@olsen.com"}
)


"""KJELD DATA"""
kjeld_email_handle = EWSMailHandle(
    source=EWSAccountSource(
        domain='@jensen.com',
        server=None,
        admin_user=None,
        admin_password=None,
        user='kjeld'),
    path='TDJHGFIHDIJHSKJGHKFUGIUHIUEHIIHE',
    mail_subject='Er det farligt?',
    folder_name='Favorit',
    entry_id=None
)

kjeld_email_handle_1 = EWSMailHandle(
    source=EWSAccountSource(
        domain='@jensen.com',
        server=None,
        admin_user=None,
        admin_password=None,
        user='kjeld'),
    path='ASDGYSDFSDFSDFDSFDFSASD',
    mail_subject='Hvad skal jeg sige til Yvonne?',
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

kjeld_positive_match_1 = messages.MatchesMessage(
        scan_spec=kjeld_scan_spec._replace(scan_tag=scan_tag2),
        handle=kjeld_email_handle_1,
        matched=True,
        matches=[messages.MatchFragment(
                rule=common_rule,
                matches=[{"dummy": "match object"}])]
)

kjeld_metadata = messages.MetadataMessage(
    scan_tag=scan_tag0,
    handle=kjeld_email_handle,
    metadata={"email-account": "kjeld@jensen.com"}
)

kjeld_metadata_1 = messages.MetadataMessage(
    scan_tag=scan_tag2,
    handle=kjeld_email_handle_1,
    metadata={"email-account": "kjeld@jensen.com"}
)

"""BENNY DATA"""
benny_email_handle = EWSMailHandle(
    source=EWSAccountSource(
        domain='@frandsen.com',
        server=None,
        admin_user=None,
        admin_password=None,
        user='benny'),
    path='HJKFHSDJKFDFKSLASDGHJ',
    mail_subject="Du' smælderfed mand!",
    folder_name='Vigtigt',
    entry_id=None
)

benny_email_handle_1 = EWSMailHandle(
    source=EWSAccountSource(
        domain='@frandsen.com',
        server=None,
        admin_user=None,
        admin_password=None,
        user='benny'),
    path='HJKFHSDJKFDFKSLASDGHJ',
    mail_subject="Så så Kjeld, det var jo ikke sådan ment",
    folder_name='Spam',
    entry_id=None
)

benny_scan_spec = messages.ScanSpecMessage(
    scan_tag=None,  # placeholder
    source=benny_email_handle.source,
    rule=common_rule,
    configuration={},
    progress=None)

benny_positive_match = messages.MatchesMessage(
        scan_spec=benny_scan_spec._replace(scan_tag=scan_tag0),
        handle=benny_email_handle,
        matched=True,
        matches=[messages.MatchFragment(
                rule=common_rule_2,
                matches=[{"dummy": "match object"}])]
)

benny_positive_match_1 = messages.MatchesMessage(
        scan_spec=benny_scan_spec._replace(scan_tag=scan_tag1),
        handle=benny_email_handle_1,
        matched=True,
        matches=[messages.MatchFragment(
                rule=common_rule_3,
                matches=[{"dummy": "match object"}])]
)

benny_metadata = messages.MetadataMessage(
    scan_tag=scan_tag0,
    handle=benny_email_handle,
    metadata={"email-account": "benny@frandsen.com"}
)

benny_metadata_1 = messages.MetadataMessage(
    scan_tag=scan_tag1,
    handle=benny_email_handle_1,
    metadata={"email-account": "benny@frandsen.com"}
)

"""YVONNE DATA"""
yvonne_email_handle = EWSMailHandle(
    source=EWSAccountSource(
        domain='@jensen.com',
        server=None,
        admin_user=None,
        admin_password=None,
        user='yvonne'),
    path='SDFYSDFUYSDFIUASDM;AMSD',
    mail_subject='Los fiskos, los salatos, los kotelettos, los vinos blancos og Los Coca Colos',
    folder_name='Spanien',
    entry_id=None
)

yvonne_scan_spec = messages.ScanSpecMessage(
    scan_tag=None,  # placeholder
    source=yvonne_email_handle.source,
    rule=common_rule,
    configuration={},
    progress=None)

yvonne_positive_match = messages.MatchesMessage(
        scan_spec=yvonne_scan_spec._replace(scan_tag=scan_tag0),
        handle=yvonne_email_handle,
        matched=True,
        matches=[messages.MatchFragment(
                rule=common_rule_2,
                matches=[{"dummy": "match object"}])]
)

yvonne_metadata = messages.MetadataMessage(
    scan_tag=scan_tag0,
    handle=yvonne_email_handle,
    metadata={"email-account": "yvonne@jensen.com"}
)


class StatisticsPageViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.generate_kjeld_data()
        cls.generate_egon_data()
        cls.generate_yvonne_data()
        cls.generate_benny_data()

    @classmethod
    def generate_kjeld_data(cls):
        record_match(kjeld_positive_match)
        record_metadata(kjeld_metadata)

        record_match(kjeld_positive_match_1)
        record_metadata(kjeld_metadata_1)

    @classmethod
    def generate_egon_data(cls):
        record_match(egon_positive_match)
        record_metadata(egon_metadata)

        record_match(egon_positive_match_1)
        record_metadata(egon_metadata_1)

    @classmethod
    def generate_yvonne_data(cls):
        record_match(yvonne_positive_match)
        record_metadata(yvonne_metadata)

    @classmethod
    def generate_benny_data(cls):
        record_match(benny_positive_match)
        record_metadata(benny_metadata)

        record_match(benny_positive_match_1)
        record_metadata(benny_metadata_1)

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.kjeld = User.objects.create_user(
            first_name='Kjeld', username='kjeld',
            email='kjeld@jensen.com', password='top_secret')
        self.egon = User.objects.create_user(
            first_name='Egon', username='egon',
            email='egon@olsen.com', password='top_secret')
        self.yvonne = User.objects.create_user(
            first_name='Yvonne', username='yvonne',
            email='yvonne@jensen.com', password='top_secret')
        self.benny = User.objects.create_user(
            first_name='Benny', username='benny',
            email='benny@frandsen.com', password='top_secret')

    # Tests are done as Kjeld
    # count_all_matches_grouped_by_sensitivity()
    def test_statisticspage_count_all_matches_grouped_by_sensitivity_as_leader(self):
        leader = Leader.objects.create(user=self.kjeld)
        view = self.get_statisticspage_object()
        sens_list, total = view.count_all_matches_grouped_by_sensitivity()
        self.assertListEqual(sens_list,
                             [['Kritisk', 4], ['Problem', 2],
                              ['Advarsel', 1], ['Notifikation', 0]])
        self.assertEquals(total, 7)
        leader.delete()

    def test_statisticspage_count_all_matches_grouped_by_sensitivity_as_dpo(self):
        dpo = DataProtectionOfficer.objects.create(user=self.kjeld)
        view = self.get_statisticspage_object()
        sens_list, total = view.count_all_matches_grouped_by_sensitivity()
        self.assertListEqual(sens_list,
                             [['Kritisk', 4], ['Problem', 2],
                              ['Advarsel', 1], ['Notifikation', 0]])
        self.assertEquals(total, 7)
        dpo.delete()

    # count_by_source_types
    def test_statisticspage_count_by_source_types_as_dpo(self):
        dpo = DataProtectionOfficer.objects.create(user=self.kjeld)
        view = self.get_statisticspage_object()
        self.assertListEqual(view.count_by_source_types(),
                             [['Andet', 0], ['Webscan', 0],
                              ['Filscan', 0], ['Mailscan', 7]])
        dpo.delete()

    # count_handled_matches_grouped_by_sensitivity()
    def test_statisticspage_count_handled_matches_grouped_by_sensitivity_as_leader(self):
        leader = Leader.objects.create(user=self.kjeld)
        view = self.get_statisticspage_object()
        sens_list, total = view.count_handled_matches_grouped_by_sensitivity()
        self.assertListEqual(sens_list,
                             [['Kritisk', 0], ['Problem', 0],
                              ['Advarsel', 0], ['Notifikation', 0]])
        self.assertEquals(total, 0)
        leader.delete()

    def test_statisticspage_count_handled_matches_grouped_by_sensitivity_as_dpo(self):
        dpo = DataProtectionOfficer.objects.create(user=self.kjeld)
        view = self.get_statisticspage_object()
        sens_list, total = view.count_handled_matches_grouped_by_sensitivity()
        self.assertListEqual(sens_list,
                             [['Kritisk', 0], ['Problem', 0],
                              ['Advarsel', 0], ['Notifikation', 0]])
        dpo.delete()

    # created_timestamp
    def test_statisticspage_created_timestamp_as_dpo(self):
        dpo = DataProtectionOfficer.objects.create(user=self.kjeld)
        view = self.get_statisticspage_object()
        created_timestamp = [m.created_timestamp.date() for m in view.matches][:2]

        self.assertEquals(created_timestamp, [timezone.now().date(), timezone.now().date()])
        dpo.delete()

    # count_new_matches_by_month()
    def test_statisticspage_count_new_matches_by_month_as_dpo(self):
        dpo = DataProtectionOfficer.objects.create(user=self.kjeld)
        view = self.get_statisticspage_object()
        test_date = dateutil.parser.parse("2020-11-28T14:21:59+05:00")

        # Overrides timestamps static dates and saves the old ones
        original_timestamps = static_timestamps()

        self.assertListEqual(view.count_new_matches_by_month(test_date),
                             [['Dec', 0], ['Jan', 0], ['Feb', 0],
                              ['Mar', 0], ['Apr', 0], ['May', 0],
                              ['Jun', 0], ['Jul', 0], ['Aug', 0],
                              ['Sep', 1], ['Oct', 2], ['Nov', 4]])

        # Reset to old values
        reset_timestamps(original_timestamps)
        dpo.delete()

    def test_statisticspage_count_new_matches_by_month_old_matches_as_dpo(self):
        dpo = DataProtectionOfficer.objects.create(user=self.kjeld)
        view = self.get_statisticspage_object()
        test_date = dateutil.parser.parse("2021-09-28T14:21:59+05:00")

        # Overrides timestamps static dates and saves the old ones
        original_timestamps = static_timestamps()

        self.assertListEqual(view.count_new_matches_by_month(test_date),
                             [['Oct', 2], ['Nov', 4], ['Dec', 0],
                              ['Jan', 0], ['Feb', 0], ['Mar', 0],
                              ['Apr', 0], ['May', 0], ['Jun', 0],
                              ['Jul', 0], ['Aug', 0], ['Sep', 0]])

        # Reset to old values
        reset_timestamps(original_timestamps)
        dpo.delete()

    def test_statisticspage_five_most_unhandled_employees(self):
        dpo = DataProtectionOfficer.objects.create(user=self.kjeld)
        view = self.get_leader_statisticspage_object()
        kjeld_emailalias, created = EmailAlias.objects.get_or_create(
            user=self.kjeld,
            address='kjeld@jensen.com')
        yvonne_emailalias, created = EmailAlias.objects.get_or_create(
            user=self.yvonne,
            address='yvonne@jensen.com')
        egon_emailalias, created = EmailAlias.objects.get_or_create(
            user=self.egon,
            address='egon@olsen.com')
        benny_emailalias, created = EmailAlias.objects.get_or_create(
            user=self.benny,
            address='benny@frandsen.com')
        create_alias_and_match_relations(kjeld_emailalias)
        create_alias_and_match_relations(yvonne_emailalias)
        create_alias_and_match_relations(egon_emailalias)
        create_alias_and_match_relations(benny_emailalias)

        self.assertListEqual(view.five_most_unhandled_employees(),
                             [['Benny', 2, True], ['Egon', 2, True],
                              ['Kjeld', 2, True], ['Yvonne', 1, True]])

        dpo.delete()
        kjeld_emailalias.delete()
        yvonne_emailalias.delete()
        egon_emailalias.delete()
        benny_emailalias.delete()

    def test_statisticspage_count_unhandled_matches_by_month(self):
        dpo = DataProtectionOfficer.objects.create(user=self.kjeld)
        view = self.get_statisticspage_object()
        test_date = dateutil.parser.parse("2021-4-28T14:21:59+05:00")

        # Saves old timestamps and overrides
        original_created_timestamps = static_timestamps('created_timestamp')
        original_resolution_time = static_timestamps('resolution_time')

        self.assertListEqual(view.count_unhandled_matches_by_month(test_date),
                             [['May', 0], ['Jun', 0], ['Jul', 0],
                              ['Aug', 0], ['Sep', 1], ['Oct', 3],
                              ['Nov', 7], ['Dec', 7], ['Jan', 7],
                              ['Feb', 7], ['Mar', 0], ['Apr', 0]])

        # Resets back to old values
        reset_timestamps(original_created_timestamps, 'created_timestamp')
        reset_timestamps(original_resolution_time, 'resolution_time')

        dpo.delete()

    # StatisticsPageView()
    def get_statisticspage_object(self):
        request = self.factory.get('/statistics')
        request.user = self.kjeld
        view = StatisticsPageView()
        return view

    # StatisticsPageView()
    def get_leader_statisticspage_object(self):
        request = self.factory.get('/statistics/leader')
        request.user = self.kjeld
        view = LeaderStatisticsPageView()
        return view


# Helper functions
# Overrides timestamps to have static data
def static_timestamps(time_type: str = 'created_timestamp',
                      added_days: int = 0) -> List[Tuple[int, datetime]]:
    original_timestamps = []

    if time_type == 'created_timestamp':  # Default
        for match in DocumentReport.objects.all():
            original_timestamps.append((match.pk, match.created_timestamp))
            match.created_timestamp = match.scan_time + timedelta(days=added_days)
            match.save()

    elif time_type == 'resolution_time':
        for batch in iterate_queryset_in_batches(10000, DocumentReport.objects.all()):
            for match in batch:
                original_timestamps.append((match.pk, match.resolution_time))
                match.resolution_status = 3
                match.resolution_time = dateutil.parser.parse("2021-3-28T14:21:59+05:00")
            DocumentReport.objects.bulk_update(batch, ['resolution_status', 'resolution_time'])
    else:
        print("Typo in argument 'time_type' in static_timestamps()")

    return original_timestamps


# Reset to old values
def reset_timestamps(arg: List[Tuple[int, datetime]],  # noqa: CCR001, E501 too high cognitive complexity
                     time_type: str = 'created_timestamp'):

    if time_type == 'created_timestamp':  # Default
        for match in DocumentReport.objects.all():
            for a in arg:
                if a[0] == match.pk:
                    match.created_timestamp = a[1]
            match.save()

    elif time_type == 'resolution_time':
        for match in DocumentReport.objects.all():
            for a in arg:
                if a[0] == match.pk:
                    match.resolution_status = None
                    match.resolution_time = a[1]
            match.save()

    else:
        print("Typo in argument 'time_type' in reset_timestamps()")
