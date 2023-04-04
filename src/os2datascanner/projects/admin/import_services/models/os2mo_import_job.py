import logging
import requests
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

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

    def request_org_unit_accounts(self, org_unit_uuid: str, session: requests.Session()):
        query_org_accounts = """
        query MyQuery {
          org_units(uuids: "%s"){
            objects {
              name
              uuid
              parent {
                name
                uuid
              }
              managers(inherit: true) {
                employee {
                  givenname
                  surname
                  user_key
                  uuid
                  addresses(address_types: "%s") {
                    name
                  }
                }
              }
              engagements {
                employee {
                  givenname
                  surname
                  user_key
                  uuid
                  addresses(address_types: "%s") {
                    name
                  }
                }
              }
            }
          }
        }
        """ % (org_unit_uuid, settings.OS2MO_EMAIL_ADDRESS_TYPE, settings.OS2MO_EMAIL_ADDRESS_TYPE)
        # Address_types has an email-adresses uuid, which means only employee emails will be shown
        # Org_units inherit managers from their parents
        try:
            token = None
            res = session.post(url=settings.OS2MO_TOKEN_URL, data=self._make_token())

            # Raise an exception if statuscode isn't in 2xx range
            res.raise_for_status()
            if res.status_code != 204:  # 204 No Content
                token = res.json().get("access_token")

            if not token:
                logger.warning("No token available!")
                return None

            headers = {
                "content-type": "application/json; charset=UTF-8",
                'Authorization': f'Bearer {token}'}

            res = session.post(
                settings.OS2MO_ENDPOINT_URL,
                json={
                    "query": query_org_accounts},
                headers=headers)

            # Raise an exception if statuscode isn't in 2xx range
            res.raise_for_status()
            if res.status_code != 204:  # 204 No Content
                return res.json()

        except requests.exceptions.JSONDecodeError:
            logger.exception("Unable to decode JSON")
        except requests.exceptions.HTTPError:
            logger.exception(f"HTTP exception thrown! \n"
                             f"Cannot process org unit with id: {org_unit_uuid}")

    @property
    def job_label(self) -> str:
        return "OS2mo Import Job"

    def run(self):  # noqa CCR001
        # TODO: We don't need to have "objects" in the query here, when we're only concerned
        # with UUID's. It will however change the response structure a little.
        query_org_units = """
        query MyQuery {
          org_units {
            objects {
              uuid
            }
          }
        }
        """

        with requests.Session() as session:
            self.status = "Initializing OS2mo Import..."
            self.save()

            res = session.post(url=settings.OS2MO_TOKEN_URL, data=self._make_token())
            try:
                token = res.json().get("access_token")
                headers = {
                    "content-type": "application/json; charset=UTF-8",
                    'Authorization': f'Bearer {token}'}

                res = session.post(
                    settings.OS2MO_ENDPOINT_URL,
                    json={
                        "query": query_org_units},
                    headers=headers)
                res.raise_for_status()

                if res.status_code != 204:
                    res = res.json()
                else:
                    res = {}

            except requests.exceptions.JSONDecodeError:
                logger.exception("Unable to decode JSON")
            except requests.exceptions.HTTPError:
                logger.exception("HTTP exception thrown!")

        if res:
            self.status = "OK.. Data received, requesting org_units..."
            logger.info("Received data from OS2mo. Sending queries.. \n")

            org_unit_uuids = []
            for org_unit_objects in res.get("data").get("org_units"):
                for org_unit in org_unit_objects.get("objects"):
                    org_unit_uuids.append(org_unit.get("uuid"))

            org_unit_list = []
            for uuid in org_unit_uuids:
                with requests.Session() as session:
                    logger.info(f"Querying for org_unit with uuid: {uuid}")
                    org_unit_list.append(self.request_org_unit_accounts(uuid, session))
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
