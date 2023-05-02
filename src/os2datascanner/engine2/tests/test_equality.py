import unittest
from parameterized import parameterized

from os2datascanner.engine2.model.smbc import SMBCSource, SMBCHandle
from os2datascanner.engine2.model.derived.mail import (
        MailSource, MailPartHandle)
from os2datascanner.engine2.model.msgraph.mail import (
        MSGraphMailSource, MSGraphMailAccountHandle,
        MSGraphMailAccountSource, MSGraphMailMessageHandle)

from os2datascanner.engine2.utilities.equality import TypePropertyEquality


class Plain:
    def __init__(self):
        self._prop = 1


class Equal1(TypePropertyEquality):
    def __init__(self):
        self._prop = 2


class Equal1a(TypePropertyEquality):
    def __init__(self, other):
        self._prop = 2
        self._other = other


class Equal2(TypePropertyEquality):
    eq_properties = ('_prop', )

    def __init__(self, other):
        self._prop = 3
        self._other = other


class Equal3(TypePropertyEquality):
    def __init__(self, other):
        self._prop = 4
        self._other = other

    def __getstate__(self):
        return {"_prop": self._prop}


class Engine2EqualityTest(unittest.TestCase):
    def test(self):
        self.assertNotEqual(
                Plain(),
                Plain(),
                "object equality is weirdly defined")
        self.assertEqual(
                Equal1(),
                Equal1(),
                "TypePropertyEquality(__dict__) is broken")
        self.assertNotEqual(
                Equal1a(2),
                Equal1a(3),
                "TypePropertyEquality(__dict__) claims that 2 == 3")
        self.assertEqual(
                Equal2(4),
                Equal2(5),
                "TypePropertyEquality(eq_properties) is broken")
        self.assertEqual(
                Equal3(4),
                Equal3(5),
                "TypePropertyEquality(__getstate__) is broken")

    @parameterized.expand([
        # The basics
        (Equal1(), "Equal1(_prop=2)"),
        (Equal1a("b"), "Equal1a(_prop=2;_other=b)"),
        (Equal1a(None), "Equal1a(_prop=2)"),
        (Equal3("b"), "Equal3(_prop=4)"),

        # More realistic tests
        (SMBCHandle(
                SMBCSource("//SHARE/FILE"),
                "path/to/document.txt"),
         "SMBCHandle(_source=(SMBCSource(_unc=//SHARE/FILE));"
         "_relpath=path/to/document.txt)"),
        (SMBCHandle(
                SMBCSource("//SHARE/FILE", driveletter="X"),
                "path/to/document.txt"),
         "SMBCHandle(_source=(SMBCSource(_unc=//SHARE/FILE));"
         "_relpath=path/to/document.txt)"),

        # The nightmares
        (MailPartHandle(
                MailSource(
                        MSGraphMailMessageHandle(
                                MSGraphMailAccountSource(
                                        MSGraphMailAccountHandle(
                                                MSGraphMailSource(
                                                        "NRCIDV",
                                                        "NRTIDV",
                                                        "NRCLSV",
                                                        True),
                                                "testuser@example.invalid")),
                                "bWVzc2FnZTI=",
                                "Re: Submission deadline",
                                "https://example.invalid/view/bWVzc2FnZTI=")),
                "1/Copy of Copy of FINAL (3) (EDITED) (FIXED2).doc.docx",
                "application/vnd.openxmlformats-officedocument"
                ".wordprocessingml.document"),
         "MailPartHandle(_source=(MailSource(_handle=(MSGraphMailMessageHandle"
         "(_source=(MSGraphMailAccountSource(_handle=(MSGraphMailAccountHandle"
         "(_source=(MSGraphMailSource(_tenant_id=NRTIDV));_relpath=testuser@"
         "example.invalid))));_relpath=bWVzc2FnZTI=))));"
         "_relpath=1/Copy of Copy of FINAL (3) (EDITED) (FIXED2).doc.docx)"),
    ])
    def test_crunch(self, obj, crunch):
        self.assertEqual(
                obj.crunch(),
                crunch,
                "unexpected crunched representation")
