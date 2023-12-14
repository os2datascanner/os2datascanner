import sys

from django.contrib.auth.models import User
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    """Configure the report app as a dev environment. This includes:

    * Creating a superuser called "dev" with password "dev"
    * Making "dev" a remediator, so they can see all matches
    """

    help = __doc__

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            self.stdout.write(self.style.NOTICE("Aborting! This may not be a developer machine."))
            sys.exit(1)

        username = password = "dev"

        self.stdout.write("Looking for superuser dev..")
        try:
            user = User.objects.get(username=username)
            user.is_staff = True  # A bit funny, we should be superuser because of the account,
            # but it doesn't set is_staff which is Django admin login.
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS("Superuser dev/dev created successfully!"))
        except User.DoesNotExist:
            self.stdout.write(self.style.WARNING("User does not exist! "
                                                 "Did you run this command in the admin module?"))
