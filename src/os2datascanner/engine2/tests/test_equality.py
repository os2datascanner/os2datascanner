import unittest
from parameterized import parameterized

from os2datascanner.engine2.model.smbc import SMBCSource, SMBCHandle
from os2datascanner.engine2.model.derived.pdf import (
        PDFObjectHandle, PDFPageSource, PDFPageHandle, PDFSource)
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
        (Equal1(), "Equal1(_prop=2)", None),
        (Equal1a("b"), "Equal1a(_prop=2;_other=b)", None),
        (Equal1a(None), "Equal1a(_prop=2)", None),
        (Equal3("b"), "Equal3(_prop=4)", None),

        # More realistic tests
        (SMBCHandle(
                SMBCSource("//SHARE/FILE"),
                "path/to/document.txt"),
         "SMBCHandle(_source=(SMBCSource(_unc=//SHARE/FILE));"
         "_relpath=path/to/document.txt)",
         None),
        (SMBCHandle(
                SMBCSource("//SHARE/FILE", driveletter="X"),
                "path/to/document.txt"),
         "SMBCHandle(_source=(SMBCSource(_unc=//SHARE/FILE));"
         "_relpath=path/to/document.txt)",
         None),

        # The nightmares
        (MailPartHandle(
                mail_source := MailSource(
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
         "_relpath=1/Copy of Copy of FINAL (3) (EDITED) (FIXED2).doc.docx)",
         None),
        (PDFObjectHandle(
                PDFPageSource(
                        PDFPageHandle(
                                PDFSource(
                                        MailPartHandle(
                                                mail_source,
                                                "2/OUTPUT.PDF",
                                                "application/pdf")),
                                "14")),
                "text.html"),
         "PDFObjectHandle(_source=(PDFPageSource(_handle=(PDFPageHandle(_sourc"
         "e=(PDFSource(_handle=(MailPartHandle(_source=(MailSource(_handle=(MS"
         "GraphMailMessageHandle(_source=(MSGraphMailAccountSource(_handle=(MS"
         "GraphMailAccountHandle(_source=(MSGraphMailSource(_tenant_id=NRTIDV)"
         ");_relpath=testuser@example.invalid))));_relpath=bWVzc2FnZTI=))));_r"
         "elpath=2/OUTPUT.PDF))));_relpath=14))));_relpath=text.html)",
         "87ba0c0266c59ed1f9b33d52336db3765fba80336f141249efaa2e505d924f835ead"
         "0361f26b39bea409da6f6e673fed365ed0ce92525d61e42097d11b237001"),
    ])
    def test_crunch(self, obj, crunch, hashed):
        self.assertEqual(
                obj.crunch(),
                crunch,
                "unexpected crunched representation")
        if hashed:
            self.assertEqual(
                    obj.crunch(hash=True),
                    hashed,
                    "unexpected hashed crunched representation")
