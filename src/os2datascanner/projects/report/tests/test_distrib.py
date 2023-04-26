from django.test import TestCase
from django.contrib.auth.models import User

from os2datascanner.engine2.model.file import (
        FilesystemSource, FilesystemHandle)
from os2datascanner.engine2.rules.dummy import AlwaysMatchesRule
from os2datascanner.engine2.pipeline import messages
from ..reportapp.utils import create_alias_and_match_relations
from ..reportapp.models.documentreport import DocumentReport
from ..organizations.models import Alias, Account, Organization
from .generate_test_data import record_match, record_metadata


# https://en.wikipedia.org/wiki/Category:19th-century_Danish_botanists, edited
# to be in the same form as imported customer data with capitalised usernames
raw_botanists = """\
ANOE,Anders Sandøe,Ørsted,ANOE@vstkom.dk
AUME,August,Mentz,AUME@vstkom.dk
CACH,Carl Frederik Albert,Christensen,CACH@vstkom.dk
CAOS,Carl Hansen,Ostenfeld,CAOS@vstkom.dk
CARA,Carl Gottlob,Rafn,CARA@vstkom.dk
CARO,Caroline,Rosenberg,CARO@vstkom.dk
CHEC,Christian Friedrich,Ecklon,CHEC@vstkom.dk
CHJE,Christian E.O.,Jensen,CHJE@vstkom.dk
CHOL,Christian Søren Marcus,Olrik,CHOL@vstkom.dk
CHRA,Christen C.,Raunkiær,CHRA@vstkom.dk
CHVA,Christian,Vaupell,CHVA@vstkom.dk
EMRO,Emil,Rostrup,EMRO@vstkom.dk
EROE,Ernst,Østrup,EROE@vstkom.dk
ERVI,Erik,Viborg,ERVI@vstkom.dk
EUWA,Eugenius,Warming,EUWA@vstkom.dk
FEDI,Ferdinand,Didrichsen,FEDI@vstkom.dk
FRBO,Frederik,Børgesen,FRBO@vstkom.dk
FRLI,Frederik,Liebmann,FRLI@vstkom.dk
FRRA,Frederik Christian,Raben,FRRA@vstkom.dk
GESA,Georg F.L.,Sarauw,GESA@vstkom.dk
HALY,Hans Christian,Lyngbye,HALY@vstkom.dk
HEEG,Henrik Franz Alexander von,Eggers,HEEG@vstkom.dk
HESC,Heinrich Christian Friedrich,Schumacher,HESC@vstkom.dk
HJKI,Hjalmar,Kiærskou,HJKI@vstkom.dk
JEHO,Jens Wilken,Hornemann,JEHO@vstkom.dk
JEJA,Jens Peter,Jacobsen,JEJA@vstkom.dk
JEVA,Jens,Vahl,JEVA@vstkom.dk
JOLA,Johan,Lange,JOLA@vstkom.dk
JOSC,Joakim Frederik,Schouw,JOSC@vstkom.dk
JOVO,Joachim Otto,Voigt,JOVO@vstkom.dk
LARO,Lauritz Kolderup,Rosenvinge,LARO@vstkom.dk
MAVA,Martin,Vahl,MAVA@vstkom.dk
MOWO,Morten,Wormskjold,MOWO@vstkom.dk
NAWA,Nathaniel,Wallich,NAWA@vstkom.dk
OTGE,Otto,Gelert,OTGE@vstkom.dk
PEDE,Peter Vogelius,Deinboll,PEDE@vstkom.dk
PENI,Peter,Nielsen,PENI@vstkom.dk
PESC,Peter,Schousboe,PESC@vstkom.dk
PETH,Peter,Thonning,PETH@vstkom.dk
SADR,Salomon,Drejer,SADR@vstkom.dk
THHO,Theo,Holm,THHO@vstkom.dk
WIJO,Wilhelm,Johannsen,WIJO@vstkom.dk"""


def create_botanists(org: Organization):
    for r in raw_botanists.splitlines():
        username, first_name, last_name, email = r.split(",")

        user = User.objects.create(
                username=username,
                first_name=first_name,
                last_name=last_name)
        account = Account.objects.create(
                username=username,
                first_name=first_name,
                last_name=last_name,
                organization=org,
                user=user)
        alias = Alias.objects.create(
                _alias_type="email",
                _value=email,
                account=account,
                user=user)
        create_alias_and_match_relations(alias)


lucky_file = FilesystemHandle(
        FilesystemSource("/home/caro/Documents"),
        "Haandbog i den danske Flora.wp")


scan_spec = messages.ScanSpecMessage(
        scan_tag=messages.ScanTagFragment.make_dummy(),
        source=lucky_file.source,
        rule=AlwaysMatchesRule(),
        configuration={}, progress=None, filter_rule=None)


match_message = messages.MatchesMessage(
        scan_spec=scan_spec,
        handle=lucky_file,
        matched=True,
        matches=[
                messages.MatchFragment(
                        AlwaysMatchesRule(),
                        matches=[{"match": True}])
        ])


metadata_message = messages.MetadataMessage(
        scan_tag=scan_spec.scan_tag,
        handle=lucky_file,
        metadata={
            "email-account": "CARO@vstkom.dk"
        })


class MatchDistributionTest(TestCase):
    def test_distribution(self):
        """Results received after organisational information has been created
        are correctly assigned to the relevant accounts."""
        org = Organization.objects.create(name="Vejstrand Kommune")
        create_botanists(org)
        record_match(match_message._deep_replace(
                scan_spec__scan_tag__organisation__uuid=org.uuid))
        record_metadata(metadata_message._deep_replace(
                scan_tag__organisation__uuid=org.uuid))

        self.assertEqual(
                DocumentReport.objects.count(),
                1,
                "too many DocumentReports")
        dr = DocumentReport.objects.get()

        caro = Account.objects.get(username="CARO")
        self.assertIn(
                dr,
                caro.aliases.get().match_relation.all(),
                "alias not connected to user metadata")

    def test_retroactive_distribution(self):
        """Results received before organisational information are correctly
        assigned to the relevant accounts upon their creation."""
        org = Organization.objects.create(name="Vejstrand Kommune")
        record_match(match_message._deep_replace(
                scan_spec__scan_tag__organisation__uuid=org.uuid))
        record_metadata(metadata_message._deep_replace(
                scan_tag__organisation__uuid=org.uuid))
        create_botanists(org)

        self.assertEqual(
                DocumentReport.objects.count(),
                1,
                "too many DocumentReports")
        dr = DocumentReport.objects.get()

        caro = Account.objects.get(username="CARO")
        self.assertIn(
                dr,
                caro.aliases.get().match_relation.all(),
                "alias not retroactively connected to user metadata")
