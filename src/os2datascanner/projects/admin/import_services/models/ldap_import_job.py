from django.db import models

from os2datascanner.utils.ldap import RDN

from os2datascanner.projects.admin.adminapp.signals import get_pika_thread
from ...core.models.background_job import BackgroundJob
from .realm import Realm


class LDAPImportJob(BackgroundJob):
    realm = models.ForeignKey(
        Realm,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name='importjob',
    )

    handled = models.IntegerField(null=True, blank=True)
    to_handle = models.IntegerField(null=True, blank=True)

    @property
    def progress(self):
        return (self.handled / self.to_handle
                if self.handled is not None and self.to_handle not in (0, None)
                else None)

    @property
    def job_label(self) -> str:
        return "Import Job"

    def run(self):
        from ...organizations.keycloak_actions import perform_import

        self.status = "Building LDAP hierarchy..."
        self.save()

        def _callback(action, *args):
            self.refresh_from_db()
            if action == "diff_computed":
                count = args[0]
                self.to_handle = count
                self.handled = 0
                self.save()
            elif action in ("diff_ignored", "diff_handled"):
                path = args[0]
                self.handled += 1
                self.status = "{1}\n{0}/{2}".format(
                        self.handled, RDN.sequence_to_dn(path), self.to_handle)
                self.save()

        perform_import(self.realm, progress_callback=_callback)

        from ..utils import post_import_cleanup
        post_import_cleanup()

    def finish(self):
        if (pe := get_pika_thread(init=False)):
            pe.synchronise(600.0)
