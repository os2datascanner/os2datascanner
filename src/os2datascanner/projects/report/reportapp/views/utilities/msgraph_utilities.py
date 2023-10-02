from enum import Enum

import requests
import structlog
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.exceptions import PermissionDenied

from os2datascanner.engine2.model.msgraph import MSGraphMailMessageHandle
from os2datascanner.engine2.model.msgraph.utilities import make_token, MSGraphSource
from os2datascanner.projects.report.organizations.models import Account
from os2datascanner.projects.report.reportapp.models.documentreport import DocumentReport
from os2datascanner.projects.report.reportapp.views.utilities.document_report_utilities \
    import is_owner, handle_report

logger = structlog.get_logger()

# Consider moving GraphCaller out of MSGraphSource.
GraphCaller = MSGraphSource.GraphCaller


class OutlookCategoryColour(Enum):
    # Available colour presets are defined here:
    # https://learn.microsoft.com/en-us/graph/api/resources/outlookcategory?view=graph-rest-1.0#properties
    Red = "Preset0"
    Orange = "Preset1"
    Brown = "Preset2"
    Yellow = "Preset3"
    Green = "Preset4"
    Teal = "Preset5"
    Olive = "Preset6"
    Blue = "Preset7"
    Purple = "Preset8"
    Cranberry = "Preset9"
    Steel = "Preset10"
    DarkSteel = "Preset11"
    Gray = "Preset12"
    DarkGray = "Preset13"
    Black = "Preset14"
    DarkRed = "Preset15"
    DarkOrange = "Preset16"
    DarkBrown = "Preset17"
    DarkYellow = "Preset18"
    DarkGreen = "Preset19"
    DarkTeal = "Preset20"
    DarkOlive = "Preset21"
    DarkBlue = "Preset22"
    DarkPurple = "Preset23"
    DarkCranberry = "Preset24"


class OutlookCategoryName(Enum):
    Match = _("OS2datascanner Match")
    FalsePositive = _("OS2datascanner False Positive")


def create_outlook_category_for_account(account: Account,
                                        category_name: OutlookCategoryName,
                                        category_colour: OutlookCategoryColour):
    """ Creates outlook category for given account
     Requires MailboxSettings.ReadWrite """

    def _make_token():
        return make_token(
            settings.MSGRAPH_APP_ID,
            tenant_id,
            settings.MSGRAPH_CLIENT_SECRET)

    # Return early scenarios
    check_msgraph_settings()
    document_report = get_msgraph_mail_document_reports(account).last()
    tenant_id = get_tenant_id_from_document_report(document_report)

    # Open a session and start doing stuff
    with requests.Session() as session:
        gc = GraphCaller(
            _make_token,
            session)

        owner = account.username

        try:
            create_category_response = gc.create_outlook_category(owner,
                                                                  category_name.value,
                                                                  category_colour.value,)
            if create_category_response.ok:
                logger.info(f"Successfully created Outlook Category for {account}! "
                            f"Category name: {category_name} & Colour {category_colour}")

        except requests.HTTPError as ex:
            create_category_failed_message = _("Couldn't create category! "
                                               "Code: {status_code}").format(
                status_code=ex.response.status_code)
            logger.warning(f"Couldn't create category! Got response: {ex.response}")
            # PermissionDenied is a bit misleading here, as it may not represent what went wrong.
            # But sticking to this exception, makes handling it in the view easier.
            raise PermissionDenied(create_category_failed_message)


def categorize_emails(account: Account, category_name: OutlookCategoryName):
    """
    Adds category to emails of account.
    Requires Mail.ReadWrite
    """
    # TODO: This uses PATCH to update the category on given mail - this will
    # remove any existing label set on the email, such that only the one provided here is set.
    # Is that OK? Otherwise, we'll have to fetch the email's existing categories first..

    def _make_token():
        return make_token(
            settings.MSGRAPH_APP_ID,
            tenant_id,
            settings.MSGRAPH_CLIENT_SECRET)

    # Return early scenarios
    check_msgraph_settings()
    document_reports = get_msgraph_mail_document_reports(account)
    tenant_id = get_tenant_id_from_document_report(document_reports.last())

    # Open a session and start doing stuff
    with requests.Session() as session:
        gc = GraphCaller(
            _make_token,
            session)

        owner = account.username
        for document_report in document_reports:
            message_handle = get_mail_message_handle_from_document_report(document_report)
            msg_id = message_handle.relative_path if message_handle else None

            try:
                categorize_email_response = gc.categorize_mail(owner,
                                                               msg_id,
                                                               category_name.value,)
                if categorize_email_response.ok:
                    logger.info(f"Successfully added category {category_name} "
                                f"to email for: {account}!")

            except requests.HTTPError as ex:
                # We don't want to raise anything here, as we're iterating emails.
                # The most likely scenario is just that the mail doesn't exist anymore.
                logger.warning(f"Couldn't categorize email! Got response: {ex.response}")


def delete_email(document_report: DocumentReport, account: Account):
    """ Deletes an email through the MSGraph API and handles DocumentReport accordingly.
    Retrieves a new access token if not provided one."""

    def _make_token():
        return make_token(
            settings.MSGRAPH_APP_ID,
            tenant_id,
            settings.MSGRAPH_CLIENT_SECRET)

    # Return early scenarios
    check_msgraph_settings()

    owner = document_report.owner
    if not is_owner(owner, account):
        logger.warning(f"User {account} tried to delete an email belonging to {owner}!")
        not_owner_message = (_("Not allowed! You tried to delete an email belonging to {owner}!").
                             format(owner=owner))
        raise PermissionDenied(not_owner_message)

    tenant_id = get_tenant_id_from_document_report(document_report)

    # Open a session and start doing stuff
    with requests.Session() as session:
        gc = GraphCaller(
            _make_token,
            session)

        message_handle = get_mail_message_handle_from_document_report(document_report)
        msg_id = message_handle.relative_path if message_handle else None

        try:
            delete_response = gc.delete_message(owner, msg_id)

            if delete_response.ok:
                logger.info(f"Successfully deleted email on behalf of {account}! "
                            "Settings resolution status REMOVED")

                handle_report(account,
                              document_report=document_report,
                              action=DocumentReport.ResolutionChoices.REMOVED)
        except requests.HTTPError as ex:
            delete_failed_message = _("Couldn't delete email! Code: {status_code}").format(
                status_code=ex.response.status_code)
            logger.warning(f"Couldn't delete email! Got response: {ex.response}")
            # PermissionDenied is a bit misleading here, as it may not represent what went wrong.
            # But sticking to this exception, makes handling it in the view easier.
            raise PermissionDenied(delete_failed_message)


def get_mail_message_handle_from_document_report(document_report: DocumentReport) \
        -> MSGraphMailMessageHandle or None:
    """ Walks up a DocumentReport's metadata chain to return MSGraphMailMessageHandle
    or None. """
    # Look to grab the handle that represents the email (to support matches in attachments)
    message_handle = next(
        (handle for handle in document_report.metadata.handle.walk_up()
         if isinstance(handle, MSGraphMailMessageHandle)), None)
    return message_handle


def check_msgraph_settings():
    if not settings.MSGRAPH_ALLOW_DELETION:
        allow_deletion_message = _("System configuration does not allow mail deletion.")
        logger.warning(allow_deletion_message)
        raise PermissionDenied(allow_deletion_message)
    if not settings.MSGRAPH_APP_ID or not settings.MSGRAPH_CLIENT_SECRET:
        msgraph_app_settings_message = _("System configuration is missing"
                                         " Azure-application credentials. ")
        logger.warning(msgraph_app_settings_message)
        raise PermissionDenied(msgraph_app_settings_message)


def get_tenant_id_from_document_report(document_report: DocumentReport) -> str or PermissionDenied:
    tenant_id = None
    # tenant_id isn't censored in metadata, which means we can grab it from there.
    for handle in document_report.metadata.handle.walk_up():
        if isinstance(handle.source, MSGraphSource):
            # we might want to add an accessor for this to avoid the private member
            tenant_id = handle.source._tenant_id
            return tenant_id
    if not tenant_id:
        logger.warning(f"Could not retrieve any tenant id from {document_report}")
        no_tenant_message = _("Could not find your Microsoft tenant!")
        # PermissionDenied is a bit misleading here, as it may not represent what went wrong.
        # But sticking to this exception, makes handling it in the view easier.
        raise PermissionDenied(no_tenant_message)


def get_msgraph_mail_document_reports(account):
    document_report = DocumentReport.objects.filter(
        alias_relation__account=account,
        source_type="msgraph-mail",
        number_of_matches__gte=1)
    if not document_report:
        logger.warning("Found no MSGraph mail DocumentReports.")
        no_dr_message = _("You currently have no Outlook reports. Can't create categories!")
        # PermissionDenied is a bit misleading here, as it may not represent what went wrong.
        # But sticking to this exception, makes handling it in the view easier.
        raise PermissionDenied(no_dr_message)
    return document_report
