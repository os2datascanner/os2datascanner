from sys import stderr
import json
import logging
import requests
from tenacity import Retrying, stop_after_attempt, wait_exponential
from collections import deque

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from os2datascanner.utils.oauth2 import mint_cc_token
from os2datascanner.projects.admin.adminapp.signals import get_pika_thread
from ...core.models.background_job import JobState, BackgroundJob


logger = logging.getLogger(__name__)


message_buffer = deque(maxlen=5)


def walk_mo_json_response(response: dict, *path):
    here, steps = response, path
    try:
        while steps:
            head, *steps = steps
            here = here[head]
            if steps and not isinstance(here, dict):
                # We still have dictionary keys left, but the object we have
                # here isn't a dictionary. Something has gone wrong
                raise TypeError(
                        f"for key \"{head}\": expected dict,"
                        f" got {type(here).__name__}")
        return here
    except (KeyError, TypeError) as ex:
        errors = response.get("errors")
        error_texts = []
        if errors:
            for error in errors:
                message = error.get("message")
                if message:
                    error_texts.append(message)
        raise ValueError(
                f"couldn't walk JSON path {path}",
                error_texts or None) from ex


retry = Retrying(
        reraise=True,
        wait=wait_exponential(multiplier=1, min=4, max=10),
        stop=stop_after_attempt(10))


def make_token():
    return mint_cc_token(
            settings.OS2MO_TOKEN_URL, settings.OS2MO_CLIENT_ID,
            settings.OS2MO_CLIENT_SECRET, wrapper=retry)


class OS2moImportJob(BackgroundJob):
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        verbose_name=_('organization'),
        related_name='os2moimport'
    )

    def _get_next_cursor(self, json_query_response: dict) -> str:
        """Given a JSON response of a OS2mo GraphQL query for org_units,
        returns the next_cursor value."""
        return walk_mo_json_response(
                json_query_response,
                "data", "org_units", "page_info", "next_cursor")

    def _get_org_unit_data(self, json_query_response: dict) -> list:
        """Given a JSON response of a OS2mo GraphQL query for org_units,
        returns a list of objects."""
        return walk_mo_json_response(
                json_query_response,
                "data", "org_units", "objects")

    # Query for Org units, their parent, managers, Employees in form of Engagements and their
    # email. Using cursor pagination (cursor and limit variables), and takes email_type as a
    # variable as well.
    QueryOrgUnitsManagersEmployees = """
    query QueryOrgUnitsManagersEmployees($cursor: Cursor, $limit: int, $email_type: [UUID!]) {
      org_units(limit: $limit, cursor: $cursor) {
        objects {
          objects {
            uuid
            name
            parent {
              uuid
              name
            }
            managers(inherit: true) {
              employee {
                uuid
                givenname
                surname
                user_key
                addresses(address_types: $email_type) {
                  name
                }
              }
            }
            engagements {
              employee {
                uuid
                givenname
                surname
                user_key
                addresses(address_types: $email_type) {
                  name
                }
              }
            }
          }
        }
        page_info {
            next_cursor
        }
      }
    }
    """

    @property
    def job_label(self) -> str:
        return "OS2mo Import Job"

    def _retry_post_query(
            self,
            session: requests.Session,
            token: str,
            os2mo_url_endpoint: str,
            next_cursor: str) -> dict:
        for attempt in retry:
            with attempt:
                resp = session.post(
                        os2mo_url_endpoint,
                        json={
                            "query": self.QueryOrgUnitsManagersEmployees,
                            "variables": {
                                "cursor": next_cursor,
                                "limit": settings.OS2MO_PAGE_SIZE,
                                "email_type": (
                                        settings.OS2MO_EMAIL_ADDRESS_TYPE)
                             }
                        },
                        headers={
                            "content-type": (
                                    "application/json; charset=UTF-8"),
                            "authorization": f"Bearer {token}"
                        })
                resp.raise_for_status()
                return resp
        else:
            raise Exception(
                    "OS2moImportJob._retry_post_query didn't fail, but didn't"
                    " succeed (huh?)")

    def run(self):  # noqa CCR001
        message_buffer.clear()

        # To ensure graphql version consistency with os2mo-endpoint
        os2mo_url_endpoint = settings.OS2MO_ENDPOINT_BASE + "v7"

        count = 0
        org_unit_list = []

        with requests.Session() as session:
            self.status = "Initializing OS2mo Import..."
            self.save()

            token = make_token()
            try:
                next_cursor = None
                while True:
                    page_response = self._retry_post_query(
                            session, token, os2mo_url_endpoint, next_cursor)
                    page_json = page_response.json()
                    message_buffer.append(page_json)

                    if page_response.status_code == 204:
                        # No more entries
                        break

                    if (not page_json.get("data")
                            and (errors := page_json.get("errors"))):
                        # Unhelpfully, MO returns HTTP 200 and not 401 or 403
                        # when our token runs out, so we need to do a string
                        # comparison
                        token_expired = any(
                                "expired" in e.get("message") for e in errors)
                        if token_expired:
                            token = make_token()
                            # Just run the current cursor again
                            continue
                        else:
                            # _get_org_unit_data will fail with a vaguely
                            # intelligible error message in this case
                            pass

                    ou_data = self._get_org_unit_data(page_json)
                    count += len(ou_data)
                    for org_unit in ou_data:
                        org_unit_list.append(org_unit)

                    logger.info(
                            f"Got {len(ou_data)} org units,"
                            f" new total {count}")

                    if not (next_cursor := self._get_next_cursor(page_json)):
                        # No more pages after this one
                        break
            except requests.exceptions.JSONDecodeError:
                logger.exception("Unable to decode JSON")
            except requests.exceptions.HTTPError:
                logger.exception("HTTP exception thrown!")

        logger.info(f"Done retrieving {count} org units, processing")

        def _callback(action, *args):
            self.refresh_from_db()
            if action == "org_unit_count":
                count = args[0]
                self.to_handle = count
                self.handled = 0
                self.save()
            elif action == "org_unit_handled":
                org_unit_name = args[0]
                self.handled += 1
                self.status = f"Handled {self.handled}/{self.to_handle} org_units \n" \
                              f"Last org_unit handled: {org_unit_name}"
                self.save()

        from ...organizations.os2mo_import_actions import perform_os2mo_import
        perform_os2mo_import(org_unit_list, self.organization, progress_callback=_callback)

        from ..utils import post_import_cleanup
        post_import_cleanup()

    def finish(self):
        if self.exec_state == JobState.FAILED and message_buffer:
            print(
                    "OS2moImportJob failed,"
                    f" printing last {len(message_buffer)} JSON responses:",
                    file=stderr)
            for msg in message_buffer:
                for line in json.dumps(msg, indent=True).split("\n"):
                    print(f"\t{line}", file=stderr)
                print("--", file=stderr)
        message_buffer.clear()

        if (pe := get_pika_thread(init=False)):
            pe.synchronise(600.0)
