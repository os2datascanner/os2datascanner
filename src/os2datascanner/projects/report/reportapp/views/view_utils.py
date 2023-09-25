import requests
import structlog
from django.conf import settings
from django.core.exceptions import PermissionDenied

from os2datascanner.engine2.model.msgraph import MSGraphMailMessageHandle
from os2datascanner.engine2.model.msgraph.utilities import make_token, MSGraphSource
from os2datascanner.projects.report.organizations.models import Account
from os2datascanner.projects.report.reportapp.models.documentreport import DocumentReport

# Consider moving GraphCaller out of MSGraphSource.
GraphCaller = MSGraphSource.GraphCaller

logger = structlog.get_logger()


def is_owner(owner: str, account: Account):
    """ Checks if user has an alias with _value corresponding to owner value.
        Returns True/False"""
    return True if account.aliases.filter(_value=owner) else False


def handle_report(account: Account,
                  document_report: DocumentReport,
                  action: DocumentReport.ResolutionChoices):
    """ Given a User, DocumentReport and action (resolution choice),
    handles report accordingly and empties raw_problem."""
    try:
        account.update_last_handle()
    except Exception as e:
        logger.warning("Exception raised while trying to update last_handle field "
                       f"of account belonging to user {account}:", e)

    document_report.resolution_status = action
    document_report.raw_problem = None
    document_report.save()
    logger.info(f"Successfully handled DocumentReport {account} with "
                f"resolution_status {action}.")


def delete_email(document_report: DocumentReport, account: Account):
    """ Deletes an email through the MSGraph API and handles DocumentReport accordingly.
    Retrieves a new access token if not provided one."""

    def _make_token():
        return make_token(
            settings.MSGRAPH_APP_ID,
            tenant_id,
            settings.MSGRAPH_CLIENT_SECRET)

    # Return early scenarios
    if not settings.MSGRAPH_ALLOW_DELETION:
        logger.warning("System configuration does not allow MSGraph deletion.")
        raise PermissionDenied

    owner = document_report.owner
    if not is_owner(owner, account):
        logger.warning(f"User {account} tried to delete an email belonging "
                       f"to {owner}!")
        return

    # tenant_id isn't censored in metadata, which means we can grab it from there.
    tenant_id = None
    for handle in document_report.metadata.handle.walk_up():
        if isinstance(handle.source, MSGraphSource):
            # we might want to add an accessor for this to avoid the private member
            tenant_id = handle.source._tenant_id
            break

    if not tenant_id:
        logger.warning(f"Could not retrieve any tenant id from {document_report}")
        return

    # Open a session and start doing stuff
    with requests.Session() as session:
        gc = GraphCaller(
            _make_token,
            session)

        # Look to grab the handle that represents the email (to support matches in attachments)
        message_handle = next(
            (handle for handle in document_report.metadata.handle.walk_up()
             if isinstance(handle, MSGraphMailMessageHandle)), None)

        msg_id = message_handle.relative_path if message_handle else None

        delete_response = gc.delete_message(owner, msg_id)

        if delete_response.ok:
            logger.info(f"Successfully deleted email on behalf of {account}! "
                        f"Settings resolution status REMOVED")

            handle_report(account,
                          document_report=document_report,
                          action=DocumentReport.ResolutionChoices.REMOVED)
        else:
            logger.warning(f"Couldn't delete email! "
                           f"Got response: {delete_response}")
