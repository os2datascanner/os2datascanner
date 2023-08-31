import requests
from django.conf import settings

from reportapp.models.documentreport import DocumentReport
from reportapp.views.report_views import logger
from os2datascanner.engine2.utilities.backoff import WebRetrier
from os2datascanner.utils.oauth2 import mint_cc_token


def is_owner(owner: str, user):
    """ Checks if user has an alias with _value corresponding to owner value.
        Returns True/False"""
    return True if user.aliases.filter(_value=owner) else False


def handle_report(user, report, action):
    """ Given a User, DocumentReport and action (resolution choice),
    handles report accordingly and empties raw_problem."""
    try:
        user.account.update_last_handle()
    except Exception as e:
        logger.warning("Exception raised while trying to update last_handle field "
                       f"of account belonging to user {user}:", e)

    report.resolution_status = action
    report.raw_problem = None
    report.save()
    logger.info(f"Successfully handled DocumentReport {report} with "
                f"resolution_status {action}.")


def delete_email(document_report: DocumentReport, user, access_token=None):
    """ Deletes an email through the MSGraph API and handles DocumentReport accordingly.
    Retrieves a new access token if not provided one."""

    if not access_token:
        access_token = make_token()

    owner = document_report.owner
    if not is_owner(owner, user):
        logger.warning(f"User {user} tried to delete an email belonging "
                       f"to {owner}!")
        return

    try:
        msg_id = document_report.raw_metadata["handle"]["source"]["handle"]["path"]
        headers = {"authorization": "Bearer {0}".format(access_token)}

        response = requests.delete(url=f"https://graph.microsoft.com/v1.0/users/"
                                       f"{owner}/messages/{msg_id}",
                                   headers=headers)
        if response.ok:
            logger.info(f"Successfully deleted email on behalf of {user}!")

            handle_report(user,
                          report=document_report,
                          action=DocumentReport.ResolutionChoices.REMOVED)
        else:
            logger.warning(f"Couldn't delete email! "
                           f"Got response: {response}")

    except KeyError as e:
        logger.warning("KeyError in raw_metadata!: Unable to find message id.")
        logger.debug(f"Exception trace: {e}")


def make_token():
    """ Helper function to retrieve a token, provided that MSGraph Tenant-, App-ID & Client Secret
    is set."""
    return mint_cc_token(
        f"https://login.microsoftonline.com/{settings.MSGRAPH_TENANT_ID}/oauth2/v2.0/token",
        settings.MSGRAPH_APP_ID, settings.MSGRAPH_CLIENT_SECRET,
        scope="https://graph.microsoft.com/.default",
        wrapper=WebRetrier().run)
