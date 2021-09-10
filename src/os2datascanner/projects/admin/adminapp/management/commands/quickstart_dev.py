import sys

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.conf import settings
from django.core.management.base import BaseCommand
from recurrence import Recurrence

from os2datascanner.projects.admin.adminapp.models.authentication_model import (
    Authentication,
)
from os2datascanner.projects.admin.adminapp.models.scannerjobs.filescanner_model import (
    FileScanner,
)
from os2datascanner.projects.admin.adminapp.models.rules.cprrule_model import (
    CPRRule,
)
from os2datascanner.projects.admin.organizations.models.organization import (
    Organization,
)


class Command(BaseCommand):
    """Configure the admin app as a dev environment. This includes:

    * Creating a superuser called "dev" with password "dev"
    * Setting up the samba share from the docker-compose dev env as a file scan
    """

    help = __doc__

    def handle(self, *args, **options):
        if not settings.DEBUG or settings.PRODUCTION:
            self.stdout.write(self.style.NOTICE("Aborting! This may not be a developer machine."))
            sys.exit(1)

        # If the need arise, feel free to add these as parameters. For now we
        # just KISS
        username = password = "dev"
        email = "dev@example.org"
        smb_user = "os2"
        smb_password = "swordfish"
        smb_name = "Lille Samba"
        smb_url = "//samba/e2test"

        self.stdout.write("Creating superuser dev/dev!")
        User(
            username=username,
            password=make_password(password),
            email=email,
            is_superuser=True,
            is_staff=True,
        ).save()
        self.stdout.write(self.style.SUCCESS("Superuser dev/dev created successfully!"))

        self.stdout.write("Creating file scanner for samba share")
        auth = Authentication(username=smb_user)
        auth.set_password(smb_password)
        auth.save()
        org = Organization.objects.first()
        recurrence = Recurrence()
        share = FileScanner.objects.create(
            name=smb_name,
            url=smb_url,
            do_ocr=True,
            validation_status=True,
            do_last_modified_check=False,
            authentication=auth,
            organization=org,
            schedule=recurrence,
        )
        cpr = CPRRule.objects.first()
        share.rules.set([cpr])
        self.stdout.write(self.style.SUCCESS("Samba share file scanner created successfully!"))

        self.stdout.write(self.style.SUCCESS("Done! Remember to run the same cmd in the Report module"))
