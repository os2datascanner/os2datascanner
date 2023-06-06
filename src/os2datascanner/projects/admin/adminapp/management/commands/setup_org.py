import logging
import sys

from django.core.management.base import BaseCommand

from ....core.models.client import Client
from ....organizations.broadcast_bulk_events import BulkCreateEvent, BulkUpdateEvent
from ....organizations.publish import publish_events
from ....organizations.models.organization import Organization, OrganizationSerializer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """ Helper command for setting up new installations.

        Running setup_org --name 'Magenta ApS' will rename existing Client and
        Organization to Magenta ApS, set Organization contact info to None and send a
        BulkCreateEvent with the Organization to the report module.

        If an Organization already exist in both admin and report, run with the --update flag
        to instead send a BulkUpdateEvent.
      """

    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            "-n", "--name",
            type=str,
            metavar="Name",
            help="Desired name of client & organization",
            default=False
        )
        parser.add_argument(
            "-u", "--update",
            default=False,
            action="store_true",
            help="Update Client and Organization name in the admin module and "
                 "send an update message for Organization to the report module."
        )

    def handle(self, *args, name, update, **options):
        if Client.objects.count() > 1 or Organization.objects.count() > 1:
            logger.warning("Can't run command when multiple Clients or Organizations exist!")
            sys.exit(1)

        client = Client.objects.first()
        org = Organization.objects.first()

        client.name = name
        org.name = name

        if not update:
            org.contact_email = None
            org.contact_phone = None

        client.save()
        org.save()
        logger.info(f"Saved Client & Org with name: {name}")

        if update:
            update_dict = {"Organization": OrganizationSerializer(
                Organization.objects.all(), many=True).data}
            publish_events([BulkUpdateEvent(update_dict)])
            return

        creation_dict = {"Organization": OrganizationSerializer(
            Organization.objects.all(), many=True).data}
        publish_events([BulkCreateEvent(creation_dict)])
        logger.info("Sent create message for Organization to the report module. \n"
                    "Be aware that this is NOT an update message.")
