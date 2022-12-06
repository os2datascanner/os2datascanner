import logging
import requests
import json
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

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

    @property
    def job_label(self) -> str:
        return "OS2mo Import Job"

    def run(self):
        query_org_accounts = """
      query MyQuery {
        org_units {
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
                addresses(address_types: "f376deb8-4743-4ca6-a047-3241de8fe9d2") {
                  name
                }
              }
            }
            associations {
              employee {
                givenname
                surname
                user_key
                uuid
                addresses(address_types: "f376deb8-4743-4ca6-a047-3241de8fe9d2") {
                  name
                }
              }
            }
          }
        }
      }
      """
        # Address_types has an email-adresses uuid, which means only employee emails will be shown
        # Org_units inherit managers from their parents

        from ...organizations.os2mo_import_actions import perform_os2mo_import
        with requests.Session() as session:
            self.status = "Initializing OS2mo Import..."
            self.save()

            res = session.post(url=settings.OS2MO_TOKEN_URL, data=self._make_token())
            token = res.json().get("access_token")
            headers = {
                "content-type": "application/json; charset=UTF-8",
                'Authorization': f'Bearer {token}'}

            res = session.post(
                settings.OS2MO_ENDPOINT_URL,
                json={
                    "query": query_org_accounts},
                headers=headers)
            res = json.loads(res.text)

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

            self.status = "OK.. Data received, build and store relations..."
            logger.info("Received data from OS2mo. Processing.. \n")

            perform_os2mo_import(res, self.organization, progress_callback=_callback)
