import logging
import requests
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from os2datascanner.projects.admin.adminapp.signals import get_pika_thread
from ...core.models.background_job import BackgroundJob

logger = logging.getLogger(__name__)


class OS2moImportJob(BackgroundJob):
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        verbose_name=_('organization'),
        related_name='os2moimport'
    )

    def _make_token(self):
        return {
            "grant_type": "client_credentials",
            "client_id": settings.OS2MO_CLIENT_ID,
            "client_secret": settings.OS2MO_CLIENT_SECRET
        }

    def _get_next_cursor(self, json_query_response: dict) -> str:
        """Given a JSON response of a OS2mo GraphQL query for org_units,
           returns the next_cursor value."""
        logger.info("Fetching next_cursor...")
        return json_query_response["data"][
                                    "org_units"][
                                        "page_info"][
                                            "next_cursor"]

    def _get_org_unit_data(self, json_query_response: dict) -> list:
        """ Given a JSON response of a OS2mo GraphQL query for org_units,
            returns a list of objects."""
        logger.info("Fetching org_unit objects for iteration...")
        return json_query_response["data"][
                                    "org_units"][
                                        "objects"]

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

    def run(self):  # noqa CCR001
        with requests.Session() as session:
            self.status = "Initializing OS2mo Import..."
            self.save()

            token_response = session.post(url=settings.OS2MO_TOKEN_URL, data=self._make_token())
            try:
                token = token_response.json().get("access_token")
                logger.info("Fetched access token..")

                headers = {
                    "content-type": "application/json; charset=UTF-8",
                    'Authorization': f'Bearer {token}'}
                query_response = session.post(
                    settings.OS2MO_ENDPOINT_URL,
                    json={
                        "query": self.QueryOrgUnitsManagersEmployees,
                        "variables": {
                            "limit": settings.OS2MO_PAGE_SIZE,
                            "email_type": settings.OS2MO_EMAIL_ADDRESS_TYPE
                        }},
                    headers=headers)
                query_response.raise_for_status()

                if query_response.status_code != 204:
                    json_query_response = query_response.json()
                else:
                    json_query_response = {}

            except requests.exceptions.JSONDecodeError:
                logger.exception("Unable to decode JSON")
            except requests.exceptions.HTTPError:
                logger.exception("HTTP exception thrown!")

        if json_query_response:
            self.status = "First query successful. Continuing.."
            logger.info("Successfully received query response from OS2mo. Continuing.. \n")

            org_unit_list = []
            next_cursor = self._get_next_cursor(json_query_response)

            for ou_data in self._get_org_unit_data(json_query_response):
                logger.info("Appending OU data to internal list")
                org_unit_list.append(ou_data)

            if next_cursor:
                logger.info("Received a paginated response. Continuing..")
                with requests.Session() as session:
                    while next_cursor:
                        paginated_query_response = session.post(
                            settings.OS2MO_ENDPOINT_URL,
                            json={
                                "query": self.QueryOrgUnitsManagersEmployees,
                                "variables": {
                                    "cursor": next_cursor,
                                    "limit": settings.OS2MO_PAGE_SIZE,
                                    "email_type": settings.OS2MO_EMAIL_ADDRESS_TYPE
                                }},
                            headers=headers)

                        paginated_query_response.raise_for_status()

                        if paginated_query_response.status_code != 204:
                            json_paginated_query_response = paginated_query_response.json()
                            next_cursor = self._get_next_cursor(json_paginated_query_response)

                        for ou_data in self._get_org_unit_data(json_paginated_query_response):
                            org_unit_list.append(ou_data)

                    logger.info("Reached last page!")
        else:
            self.status = "No data received!"
            # Raising exception to mark job as failed
            raise ValueError("No data received! Nothing will be imported, job status failed.")

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
        if (pe := get_pika_thread(init=False)):
            pe.synchronise(600.0)
