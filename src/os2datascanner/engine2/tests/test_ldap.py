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
                LDAPNode.from_iterator(SUMER_ITERATOR,
                        name_selector=group_dn_selector).collapse(),
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
                        "memberOf": [""] },
                    # memberOf valid
                    {"distinguishedName": "CN=Enkidu",
                        "memberOf": ["CN=Heroes,L=Sumer"] },
                    # memberOf missing
                    {"distinguishedName": "CN=Ninhursag" }
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
                list(SUMER.diff(POST_FLOOD)),
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
                list(SUMER.diff(POST_EPIC)),
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
                list(SUMER.diff(s2)),
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
