from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist

from exchangelib.errors import ErrorNonExistentMailbox

from os2datascanner.engine2.model.ews import *
from os2datascanner.engine2.model.core import SourceManager

from os2datascanner.projects.admin.adminapp.models.scannerjobs.\
    exchangescanner_model import ExchangeScanner


class Command(BaseCommand):
    """Command for starting a pipeline collector process."""
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            "id",
            type=int,
            help="The id of the exchange scannerjob.",
            default=None)

    def handle(self, id, *args, **options):
        try:
            exchange_scanner = ExchangeScanner.objects.get(pk=id)
        except ObjectDoesNotExist:
            print("No exchange scannerjob exists with id {0}".format(id))
            exit(0)

        user_list = [u.decode("utf-8").strip()
                     for u in exchange_scanner.userlist if u.strip()]
        for user_name in user_list:
            account = EWSAccountSource(
                domain=exchange_scanner.url.lstrip('@'),
                server=exchange_scanner.service_endpoint,
                admin_user=exchange_scanner.authentication.username,
                admin_password=exchange_scanner.authentication.get_password(),
                user=user_name
            )

            with SourceManager() as sm:
                try:
                    exchangelib_object = sm.open(account)
                    if exchangelib_object.msg_folder_root:
                        print("OS2datascanner has access to mailbox {0}".format(
                            account.address)
                        )
                except ErrorNonExistentMailbox:
                    print("Mailbox {0} does not exits".format(account.address))
