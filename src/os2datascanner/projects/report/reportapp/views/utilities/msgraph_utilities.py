from enum import Enum

import requests
import structlog
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.exceptions import PermissionDenied

from os2datascanner.engine2.model.msgraph import MSGraphMailMessageHandle
from os2datascanner.engine2.model.msgraph.utilities import make_token, MSGraphSource
from os2datascanner.projects.report.organizations.models import (Account, AccountOutlookSetting,
                                                                 Organization)
from os2datascanner.projects.report.reportapp.models.documentreport import DocumentReport
from os2datascanner.projects.report.reportapp.views.utilities.document_report_utilities \
    import is_owner, handle_report
from os2datascanner.core_organizational_structure.models import MSGraphWritePermissionChoices


logger = structlog.get_logger()

# Consider moving GraphCaller out of MSGraphSource.
GraphCaller = MSGraphSource.GraphCaller


class OutlookCategoryName(Enum):
    """ Enum used to set Outlook category names """
    # Don't translate these - it'll give you proxy objects which aren't serializable,
    # and we need to be able to trust their values.
    Match = "OS2datascanner Match"
    FalsePositive = "OS2datascanner False Positive"


def create_outlook_category_for_account(account: Account,
                                        category_name: OutlookCategoryName,
                                        category_colour: AccountOutlookSetting.OutlookCategoryColour
                                        ):
    """ Creates outlook category for given account
     Requires MailboxSettings.ReadWrite """

    def _make_token():
        return make_token(
            settings.MSGRAPH_APP_ID,
            tenant_id,
            settings.MSGRAPH_CLIENT_SECRET)

    # Return early scenarios
    required_permissions = (MSGraphWritePermissionChoices.ALL,
                            MSGraphWritePermissionChoices.CATEGORIZE)
    check_msgraph_settings(required_permissions, account.organization)
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
                                                                  category_colour.value,
                                                                  )
            if create_category_response.ok:
                logger.info(f"Successfully created Outlook Category for {account}! "
                            f"Category name: {category_name} & Colour {category_colour}")
                return create_category_response

        except requests.HTTPError as ex:
            create_category_failed_message = _("Couldn't create category! "
                                               "Please make sure category {category_name} doesn't "
                                               "already exist in Outlook! "
                                               "Code: {status_code}").format(
                category_name=category_name.value, status_code=ex.response.status_code)
            logger.warning(f"Couldn't create category! Got response: {ex.response}")
            # PermissionDenied is a bit misleading here, as it may not represent what went wrong.
            # But sticking to this exception, makes handling it in the view easier.
            raise PermissionDenied(create_category_failed_message)


def update_outlook_category_for_account(account: Account,
                                        category_id: str,
                                        category_colour: AccountOutlookSetting.OutlookCategoryColour
                                        ):
    """ Updates outlook category color for given account
     Requires MailboxSettings.ReadWrite """

    def _make_token():
        return make_token(
            settings.MSGRAPH_APP_ID,
            tenant_id,
            settings.MSGRAPH_CLIENT_SECRET)

    # Return early scenarios
    required_permissions = (MSGraphWritePermissionChoices.ALL,
                            MSGraphWritePermissionChoices.CATEGORIZE)
    check_msgraph_settings(required_permissions, account.organization)
    document_report = get_msgraph_mail_document_reports(account).last()
    tenant_id = get_tenant_id_from_document_report(document_report)

    # Open a session and start doing stuff
    with requests.Session() as session:
        gc = GraphCaller(
            _make_token,
            session)

        owner = account.username

        try:
            update_category_response = gc.update_category_colour(owner,
                                                                 category_id,
                                                                 category_colour.value,
                                                                 )
            if update_category_response.ok:
                logger.info(f"Successfully updated Outlook Category for {account}! "
                            f"Category id: {category_id} is now colour {category_colour}")
                return update_category_response

        except requests.HTTPError as ex:
            update_category_failed_message = _("Couldn't update category! "
                                               "Code: {status_code}").format(
                status_code=ex.response.status_code)
            logger.warning(f"Couldn't create category! Got response: {ex.response}")
            # PermissionDenied is a bit misleading here, as it may not represent what went wrong.
            # But sticking to this exception, makes handling it in the view easier.
            raise PermissionDenied(update_category_failed_message)


def delete_outlook_category_for_account(account: Account, category_id: str,):
    """ Updates outlook category color for given account
     Requires MailboxSettings.ReadWrite """

    def _make_token():
        return make_token(
            settings.MSGRAPH_APP_ID,
            tenant_id,
            settings.MSGRAPH_CLIENT_SECRET)

    # Return early scenarios
    required_permissions = (MSGraphWritePermissionChoices.ALL,
                            MSGraphWritePermissionChoices.CATEGORIZE)
    check_msgraph_settings(required_permissions, account.organization)
    document_report = get_msgraph_mail_document_reports(account).last()
    tenant_id = get_tenant_id_from_document_report(document_report)

    # Open a session and start doing stuff
    with requests.Session() as session:
        gc = GraphCaller(
            _make_token,
            session)

        owner = account.username

        try:
            delete_category_response = gc.delete_category(owner, category_id)
            if delete_category_response.ok:
                logger.info(f"Successfully deleted Outlook Category for {account}! "
                            f"Category id: {category_id}")
                return delete_category_response

        except requests.HTTPError as ex:
            delete_category_failed_message = _("Couldn't delete category! "
                                               "Code: {status_code}").format(
                status_code=ex.response.status_code)
            logger.warning(f"Couldn't delete category! Got response: {ex.response}")
            # PermissionDenied is a bit misleading here, as it may not represent what went wrong.
            # But sticking to this exception, makes handling it in the view easier.
            raise PermissionDenied(delete_category_failed_message)


def categorize_email_from_report(document_report: DocumentReport,
                                 category_name: str,
                                 gc: GraphCaller):
    """
    Adds category to a specific email retrieved from a DocumentReport.
    Requires Mail.ReadWrite
    """

    # Return early scenarios
    required_permissions = (MSGraphWritePermissionChoices.ALL,
                            MSGraphWritePermissionChoices.CATEGORIZE)
    check_msgraph_settings(required_permissions, document_report.organization)

    # Fetch what categories are already set on this email.
    email_categories = get_msgraph_mail_categories_from_document_report(document_report)
    # Append OS2datascanner category
    email_categories.append(category_name)

    owner = document_report.owner
    message_handle = get_mail_message_handle_from_document_report(document_report)
    msg_id = message_handle.relative_path if message_handle else None

    try:
        categorize_email_response = gc.categorize_mail(owner,
                                                       msg_id,
                                                       email_categories)
        if categorize_email_response.ok:
            logger.info(f"Successfully added category {category_name} "
                        f"to email: {document_report}!")

    except requests.HTTPError as ex:
        # We don't want to raise anything here
        # The most likely scenario is just that the mail doesn't exist anymore.
        logger.warning(f"Couldn't categorize email! Got response: {ex.response}")


def categorize_existing_emails_from_account(account: Account,
                                            category_name: OutlookCategoryName):
    """
    Adds category to emails of account, based on existing DocumentReports
    Requires Mail.ReadWrite
    """

    def _make_token():
        return make_token(
            settings.MSGRAPH_APP_ID,
            tenant_id,
            settings.MSGRAPH_CLIENT_SECRET)

    # Return early scenarios
    required_permissions = (MSGraphWritePermissionChoices.ALL,
                            MSGraphWritePermissionChoices.CATEGORIZE)
    check_msgraph_settings(required_permissions, account.organization)
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
                existing_categories_response = gc.get(
                    f"users/{owner}/messages/{msg_id}?$select=categories").json()
                email_categories = existing_categories_response.get("categories", [])

                # Only append if it's not already marked False Positive.
                if OutlookCategoryName.FalsePositive.value not in email_categories:
                    email_categories.append(category_name.value)

                categorize_email_response = gc.categorize_mail(owner,
                                                               msg_id,
                                                               email_categories)
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
    required_permissions = (MSGraphWritePermissionChoices.ALL,
                            MSGraphWritePermissionChoices.DELETE)
    check_msgraph_settings(required_permissions, account.organization)

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


def check_msgraph_settings(required_permissions: tuple, org: Organization):
    if not settings.MSGRAPH_ALLOW_WRITE:
        allow_deletion_message = _("System configuration does not allow mail deletion.")
        logger.warning(allow_deletion_message)
        raise PermissionDenied(allow_deletion_message)
    if not settings.MSGRAPH_APP_ID or not settings.MSGRAPH_CLIENT_SECRET:
        msgraph_app_settings_message = _("System configuration is missing"
                                         " Azure-application credentials. ")
        logger.warning(msgraph_app_settings_message)
        raise PermissionDenied(msgraph_app_settings_message)
    if org.msgraph_write_permissions not in required_permissions:
        org_permission_message = _("Your organization does not allow this operation.")
        logger.warning(org_permission_message)
        raise PermissionDenied(org_permission_message)


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
    # TODO: Should this return only unresolved reports?
    # When used before trying to get a tenant id, it lowers our odds of getting one.
    # On the other hand, it might be annoying for the user to have an email cateogorized
    # if they've already handled the result in OS2datascanner.
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


def get_msgraph_mail_categories_from_document_report(document_report: DocumentReport) -> list:
    return document_report.metadata.metadata.get("outlook-categories", [])
