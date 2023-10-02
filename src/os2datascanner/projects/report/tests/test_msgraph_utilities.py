import pytest
from django.core.exceptions import PermissionDenied

from os2datascanner.engine2.model.msgraph import MSGraphMailMessageHandle

from ..reportapp.views.utilities.msgraph_utilities import \
    get_mail_message_handle_from_document_report, get_tenant_id_from_document_report
from ..reportapp.models.documentreport import DocumentReport

scan_tag_origin_metadata = {
    "origin": "os2ds_metadata",
    "metadata": {
        "email-account": "jean@claude.sky",
        "last-modified": "2022-11-07T12:05:51+0000"
    },
    "scan_tag": {
        "time": "2023-08-30T08:00:35+02:00",
        "user": "Cloudministrator",
        "scanner": {
            "pk": 24,
            "name": "Scan",
            "test": True
        },
        "destination": "pipeline_collector",
        "organisation": {
            "name": "Vejstrand kommune",
            "uuid": "0cdaf868-e877-4d92-bc36-1187cdff1233"
        }
    }
}


@pytest.fixture(scope="class")
def msgraph_mail_reports():  # noqa: ECE001
    flat_metadata = {  # noqa: ECE001
        "handle": {
            "mime": "text/html",
            "path": "1/",
            "type": "mail-part",
            "hints": "null",
            "source": {
                "type": "mail",
                "handle": {
                    "path": "very long email path",
                    "type": "msgraph-mail-message",
                    "hints": "null",
                    "folder": "Test/Inner",
                    "source": {
                        "type": "msgraph-mail-account",
                        "handle": {
                            "path": "claude@sky.com",
                            "type": "msgraph-mail-account",
                            "hints": "null",
                            "source": {
                                "type": "msgraph-mail",
                                "client_id": "not_a_real_client",
                                "tenant_id": "not_a_real_tenant",
                                "client_secret": "null"
                            }
                        }
                    },
                    "weblink": "Link",
                    "mail_subject": "Sygemelding"
                }
            }
        },
    }

    nested_metadata = {  # noqa: ECE001
        "handle": {
            "path": "page.txt",
            "type": "pdf-object",
            "hints": "null",
            "source": {
                "type": "pdf-page",
                "handle": {
                    "path": "1",
                    "type": "pdf-page",
                    "hints": "null",
                    "source": {
                        "type": "pdf",
                        "handle": {
                            "mime": "application/pdf",
                            "path": "1/1111111118.pdf",
                            "type": "mail-part",
                            "hints": "null",
                            "source": {
                                "type": "mail",
                                "handle": {
                                    "path": "very long email path",
                                    "type": "msgraph-mail-message",
                                    "source": {
                                        "type": "msgraph-mail-account",
                                        "handle": {
                                            "path": "jean@claude.sky",
                                            "type": "msgraph-mail-account",
                                            "source": {
                                                "type": "msgraph-mail",
                                                "client_id": "not_a_real_client",
                                                "tenant_id": "not_a_real_tenant",
                                                "client_secret": "null"
                                            }
                                        }
                                    },
                                    "weblink": "fakelink",
                                    "mail_subject": "Læs venligst"
                                }
                            }
                        }
                    }
                }
            }
        },
    }

    flat_metadata.update(scan_tag_origin_metadata)
    nested_metadata.update(scan_tag_origin_metadata)

    return [DocumentReport(
        name="Report-nested",
        owner="jean@claude.sky",
        scanner_job_pk=1,
        path="docx",
        raw_metadata=flat_metadata),
        DocumentReport(
            name="Report-nested",
            owner="jean@claude.sky",
            scanner_job_pk=1,
            path="docx",
            raw_metadata=nested_metadata)
    ]


@pytest.fixture(scope="class")
def not_msgraph_reports():
    filescan_metadata = {
        "handle": {
            "path": "Sundhedsjournal.html",
            "type": "lo-object",
            "hints": "null",
            "source": {
                "type": "lo",
                "handle": {
                    "path": "Sundhedsjournal.doc",
                    "type": "smbc",
                    "hints": "null",
                    "source": {
                        "unc": "//samba/e2test",
                        "type": "smbc",
                        "user": "null",
                        "domain": "null",
                        "password": "null",
                        "driveletter": "null",
                        "unc_is_home_root": False,
                        "skip_super_hidden": False
                    }
                }
            }
        },
    }

    filescan_metadata.update(scan_tag_origin_metadata)
    return DocumentReport(
        name="Report-nested",
        owner="jean@claude.sky",
        scanner_job_pk=1,
        path="docx",
        raw_metadata=filescan_metadata)


class TestMSGraphUtils:
    def test_get_mail_message_handle_from_document_report(self, msgraph_mail_reports):
        # Checks that we're able to retrieve an MSGraphMailMessageHandle from DocumentReport
        # Metadata regarding email body matches & an attached file.
        for dr in msgraph_mail_reports:
            assert isinstance(get_mail_message_handle_from_document_report(dr),
                              MSGraphMailMessageHandle), "Didn't return MSGraphMailMessageHandle!"

    def test_get_mail_message_handle_from_document_report_not_msgraph(self, not_msgraph_reports):
        # Checks that if we aren't able to find any MSGraphMailMessageHandle, we don't crash, but
        # return None.
        assert get_mail_message_handle_from_document_report(not_msgraph_reports) is None, \
            "Didn't return None when no MSGraphMailMessageHandle found!"

    def test_get_tenant_id_from_document_report(self, msgraph_mail_reports):
        # Check that we get the str value of the tenant id, provided there is one.
        for dr in msgraph_mail_reports:
            assert get_tenant_id_from_document_report(dr) == "not_a_real_tenant", ("Didn't find "
                                                                                   "tenant id in "
                                                                                   "DocumentReport!"

                                                                                   )

    def test_get_tenant_id_from_document_report_no_tenant(self, not_msgraph_reports):
        # Check that we raise PermissionDenied when no tenant id is found.
        with pytest.raises(PermissionDenied):
            get_tenant_id_from_document_report(not_msgraph_reports)
