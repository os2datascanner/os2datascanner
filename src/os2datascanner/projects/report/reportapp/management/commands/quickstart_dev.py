import sys

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.conf import settings
from django.core.management.base import BaseCommand

from os2datascanner.projects.report.reportapp.models.roles.remediator_model import (
    Remediator,
)


class Command(BaseCommand):
    """Configure the report app as a dev environment. This includes:

    * Creating a superuser called "dev" with password "dev"
    * Making "dev" a remediator, so they can see all matches
    """

    help = __doc__

    def handle(self, *args, **options):
        if not settings.DEBUG:
            self.stdout.write(self.style.NOTICE("Aborting! This may not be a developer machine."))
            sys.exit(1)

        username = password = "dev"
        email = "dev@example.org"

        self.stdout.write("Creating superuser dev/dev!")
        user = User(
            username=username,
            password=make_password(password),
            email=email,
            is_superuser=True,
            is_staff=True,
        )
        user.save()
        self.stdout.write(self.style.SUCCESS("Superuser dev/dev created successfully!"))

        self.stdout.write("Making dev remediator")
        Remediator.objects.create(user=user)

        self.stdout.write(self.style.SUCCESS("Done! Remember to run the same cmd in the Admin module"))
