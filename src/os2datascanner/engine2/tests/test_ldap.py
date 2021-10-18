import copy
import unittest

from os2datascanner.utils.ldap import RDN, LDAPNode, group_dn_selector


ENKI = LDAPNode.make(
        RDN.dn_to_sequence("CN=Enki"),
        distinguishedName="CN=Enki,L=Eridu,L=Sumer",
        memberOf=[
                "CN=WhoDecree,CN=Gods,L=Sumer"
        ],
        title="Lord of the Earth")


NINHURSAG = LDAPNode.make(
        RDN.dn_to_sequence("CN=Ninhursag"),
        distinguishedName="CN=Ninhursag,L=Eridu,L=Sumer",
        memberOf=[
                "CN=WhoDecree,CN=Gods,L=Sumer"
        ])


GILGAMESH = LDAPNode.make(
        RDN.dn_to_sequence("CN=Gilgamesh"),
        distinguishedName="CN=Gilgamesh,L=Uruk,L=Sumer",
        memberOf=[
                "CN=Demigods,CN=Gods,L=Sumer",
                "CN=Heroes,L=Sumer"
        ])


ENKIDU = LDAPNode.make(
        RDN.dn_to_sequence("CN=Enkidu"),
        distinguishedName="CN=Enkidu,L=Uruk,L=Sumer",
        memberOf=[
                "CN=Heroes,L=Sumer"
        ])


SUMER = LDAPNode.make(
        RDN.dn_to_sequence("L=Sumer"),
        LDAPNode.make(RDN.dn_to_sequence("L=Eridu"), ENKI, NINHURSAG),
        LDAPNode.make(RDN.dn_to_sequence("L=Uruk"), GILGAMESH, ENKIDU))


SUMER_GROUPS = LDAPNode.make(
        RDN.dn_to_sequence("L=Sumer"),
        LDAPNode.make(
                RDN.dn_to_sequence("CN=Gods"),
                LDAPNode.make(
                        RDN.dn_to_sequence("CN=WhoDecree"), ENKI, NINHURSAG),
                LDAPNode.make(
                        RDN.dn_to_sequence("CN=Demigods"), GILGAMESH)),
        LDAPNode.make(
                RDN.dn_to_sequence("CN=Heroes"),
                GILGAMESH, ENKIDU))


SUMER_ITERATOR = [
    {
        "distinguishedName": "CN=Enki,L=Eridu,L=Sumer",
        "title": "Lord of the Earth",
        "memberOf": ["CN=WhoDecree,CN=Gods,L=Sumer"]
    },
    {
        "distinguishedName": "CN=Ninhursag,L=Eridu,L=Sumer",
        "memberOf": ["CN=WhoDecree,CN=Gods,L=Sumer"]
    },
    {
        "distinguishedName": "CN=Gilgamesh,L=Uruk,L=Sumer",
        "memberOf": ["CN=Demigods,CN=Gods,L=Sumer", "CN=Heroes,L=Sumer"]
    },
    {
        "distinguishedName": "CN=Enkidu,L=Uruk,L=Sumer",
        "memberOf": ["CN=Heroes,L=Sumer"]
    },
]

POST_FLOOD = copy.deepcopy(SUMER)
POST_FLOOD.children.append(
        LDAPNode.make(
                RDN.dn_to_sequence("L=Kish"),
                LDAPNode.make(
                        RDN.dn_to_sequence("CN=Etana"),
                        distinguishedName="CN=Etana,L=Kish,L=Sumer")))

POST_EPIC = copy.deepcopy(SUMER)
del POST_EPIC.children[1].children[1]  # The death of Enkidu


KEYCLOAK_USER = {
    "id": "b458a8a0-ca3a-479e-bb7a-ee9be8cdc593",
    "createdTimestamp": 1619701032883,
    "username": "enkidu wildman",
    "enabled": True,
    "totp": False,
    "emailVerified": False,
    "firstName": "Enkidu",
    "lastName": "Wildman",
    "email": "ew@uruk",
    "federationLink": "67f8323e-3682-40f3-acb8-18f568b010cf",
    "attributes": {
        "LDAP_ENTRY_DN": [
            "cn=Enkidu Wildman,ou=Employees,dc=uruk"
        ],
        "modifyTimestamp": [
            "20210429124502Z"
        ],
        "createTimestamp": [
            "20210429124502Z"
        ],
        "LDAP_ID": [
            "461c6b17-9516-4513-ad50-f9185962cb4f"
        ]
    },
    "disableableCredentialTypes": [],
    "requiredActions": [],
    "notBefore": 0,
    "access": {
        "manageGroupMembership": True,
        "view": True,
        "mapRoles": True,
        "impersonate": True,
        "manage": True
    }
}


class LDAPTest(unittest.TestCase):
    def test_iterator_construction(self):
        """LDAPNode.from_iterator should be able to construct a hierarchy from
        a flat list of users."""
        self.assertEqual(
                SUMER,
                LDAPNode.from_iterator(SUMER_ITERATOR).collapse(),
                "LDAP iterator construction failed")

    def test_iterator_construction_group(self):
        """LDAPNode.from_iterator should be able to construct a hierarchy from
        the group information present in a flat list of users."""
        self.assertEqual(
                SUMER_GROUPS,
                LDAPNode.from_iterator(
                        SUMER_ITERATOR,
                        name_selector=group_dn_selector
                        ).collapse(),
                "LDAP iterator group construction failed")

    def test_iterator_skipping(self):
        """LDAPNode.from_iterator should skip over objects that don't have an
        identifiable distinguished name."""
        self.assertEqual(
                LDAPNode.from_iterator([
                    {"distinguishedName": "CN=Enki"},
                    {"extinguishedName": "CN=Enkidu"},
                    {"distinguishedName": "CN=Ninhursag"}
                ]),
                LDAPNode.make(
                    (),
                    LDAPNode.make(
                            RDN.dn_to_sequence("CN=Enki"),
                            distinguishedName="CN=Enki"),
                    LDAPNode.make(
                            RDN.dn_to_sequence("CN=Ninhursag"),
                            distinguishedName="CN=Ninhursag")
                ),
                "missing DN should have been ignored")

    def test_iterator_skipping_group(self):
        """LDAPNode.from_iterator should skip over objects that don't have at
        least one identifiable group name."""
        self.assertEqual(
                LDAPNode.from_iterator([
                    # memberOf structurally valid but with no valid groups
                    {"distinguishedName": "CN=Enki",
                        "memberOf": [""]},
                    # memberOf valid
                    {"distinguishedName": "CN=Enkidu",
                        "memberOf": ["CN=Heroes,L=Sumer"]},
                    # memberOf missing
                    {"distinguishedName": "CN=Ninhursag"}
                ], name_selector=group_dn_selector),
                LDAPNode.make(
                    (),
                    LDAPNode.make(
                            RDN.dn_to_sequence("L=Sumer"),
                            LDAPNode.make(
                                    RDN.dn_to_sequence("CN=Heroes"),
                                    LDAPNode.make(
                                            RDN.dn_to_sequence("CN=Enkidu"),
                                            distinguishedName="CN=Enkidu",
                                            memberOf=["CN=Heroes,L=Sumer"])))
                ),
                "objects without groups should have been ignored")

    def test_addition(self):
        """LDAPNode.diff should notice when an object is added to the
        hierarchy."""
        self.assertEqual(
                list(SUMER.diff(POST_FLOOD, only_leaves=True)),
                [
                    (
                        RDN.dn_to_sequence("CN=Etana,L=Kish,L=Sumer"),
                        None,
                        POST_FLOOD.children[-1].children[-1]
                    )
                ],
                "additive diff failed")

    def test_removal(self):
        """LDAPNode.diff should notice when an object is removed from the
        hierarchy."""
        self.assertEqual(
                list(SUMER.diff(POST_EPIC, only_leaves=True)),
                [
                    (
                        RDN.dn_to_sequence("CN=Enkidu,L=Uruk,L=Sumer"),
                        SUMER.children[1].children[1],
                        None
                    )
                ],
                "negative diff failed")

    def test_property_change(self):
        """LDAPNode.diff should notice when the properties of an object
        change."""
        s2 = copy.deepcopy(SUMER)
        s2.children[0].children[0].properties["title"] = "Lord of the Waters"
        self.assertEqual(
                list(SUMER.diff(s2, only_leaves=True)),
                [
                    (
                        RDN.dn_to_sequence("CN=Enki,L=Eridu,L=Sumer"),
                        SUMER.children[0].children[0],
                        s2.children[0].children[0]
                    )
                ],
                "property diff failed")

    def test_custom_import(self):
        """LDAPNode.from_iterator should be able to select distinguished names
        from Keycloak's JSON serialisation of users."""

        def select_keycloak_dn(user_dict):
            yield user_dict.get(
                    "attributes", {}).get("LDAP_ENTRY_DN", [None])[0]
        node = LDAPNode.from_iterator(
                [KEYCLOAK_USER],
                name_selector=select_keycloak_dn).children[0]

        # For the moment, we don't care about the properties here -- just the
        # structure
        node.children[0].children[0].properties.clear()

        self.assertEqual(
                node,
                LDAPNode.make(
                        RDN.dn_to_sequence("dc=uruk"),
                        LDAPNode.make(
                                RDN.dn_to_sequence("ou=Employees"),
                                LDAPNode.make(
                                        RDN.dn_to_sequence(
                                            "cn=Enkidu Wildman")))),
                "construction from Keycloak JSON object failed")

    def test_complicated_name(self):
        """RDN.dn_to_sequence should be able to handle Unicode characters and
        escape sequences."""
        dadi = (RDN("C", "DK"),
                RDN("L", "Ærøskøbing, Ærø"),
                RDN("ST", "Baggårde 497"),
                RDN("O", "フィクショナル・エンタープライゼズ株式会社"),
                RDN("OU", "🍪🎩"),
                RDN("CN", "Daði Ólafsson, General Manager"),)

        self.assertEqual(
                RDN.dn_to_sequence(
                        "CN=Daði Ólafsson\\, General Manager,"
                        "OU=🍪🎩,"
                        "O=フィクショナル・エンタープライゼズ株式会社,"
                        "ST=Baggårde 497,"
                        "L=Ærøskøbing\\, Ærø,"
                        "C=DK"),
                dadi,
                "parsing of complex RDN failed")

        self.assertEqual(
                RDN.dn_to_sequence(
                        "CN=Da\\c3\\b0i \\c3\\93lafsson\\, General Manager,OU="
                        "\\f0\\9f\\8d\\aa\\f0\\9f\\8e\\a9,O=\\e3\\83\\95\\e3\\"
                        "82\\a3\\e3\\82\\af\\e3\\82\\b7\\e3\\83\\a7\\e3\\83\\8"
                        "a\\e3\\83\\ab\\e3\\83\\bb\\e3\\82\\a8\\e3\\83\\b3\\e3"
                        "\\82\\bf\\e3\\83\\bc\\e3\\83\\97\\e3\\83\\a9\\e3\\82"
                        "\\a4\\e3\\82\\bc\\e3\\82\\ba\\e6\\a0\\aa\\e5\\bc\\8f"
                        "\\e4\\bc\\9a\\e7\\a4\\be,ST=Bagg\\c3\\a5rde 497,L=\\"
                        "c3\\86r\\c3\\b8sk\\c3\\b8bing\\, \\c3\\86r\\c3\\b8,C"
                        "=DK"),
                dadi,
                "parsing of escaped complex RDN failed")

    def test_round_trip(self):
        """Converting a RDN sequence to and from a string representation should
        produce an equivalent RDN, even when escape sequences are involved."""

        with self.subTest():
            enki = (RDN("CN", "𒀭𒂗𒆠, Enki"),
                    RDN("L", "𒉣𒆠, Eridu"),
                    RDN("L", "𒆠𒂗𒄀, Sumer"))
            self.assertEqual(
                    enki,
                    RDN.dn_to_sequence(RDN.sequence_to_dn(enki)),
                    "RDN round trip failed")

        with self.subTest():
            worst_case = (RDN("CN", """ "#+\\,;<=>"""), RDN("L", "Test"))
            self.assertEqual(
                    worst_case,
                    RDN.dn_to_sequence(RDN.sequence_to_dn(worst_case)),
                    "RDN round trip failed")

    def test_escape_exceptions(self):
        """Converting a RDN sequence to a string representation should not
        escape more special characters than necessary."""

        self.assertEqual(
                RDN.sequence_to_dn((RDN("#CN#", " 1 2 3 4 5 "),)),
                "\\#CN#=\\ 1 2 3 4 5\\ ",
                "overzealous escape")

    def test_raw_escape(self):
        self.assertEqual(
                RDN.sequence_to_dn(
                        (
                                RDN("OU", "🍪🎩"),
                                RDN("CN", "Daði Ólafsson, General Manager"),
                        ), codec=None),
                "CN=Daði Ólafsson\\, General Manager,OU=🍪🎩",
                "Unicode characters incorrectly escaped in raw mode")
