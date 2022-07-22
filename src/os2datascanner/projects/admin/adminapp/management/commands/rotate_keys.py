"""Rotate DECRYPTION_HEX and all encrypted values in the database."""
from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.db import connection, transaction

# from os2datascanner.projects.admin.import_services.models.keycloak import KeycloakServer
from os2datascanner.projects.admin.import_services.models.ldap_configuration import LDAPConfig
from os2datascanner.projects.admin.adminapp.models.authentication import Authentication
from os2datascanner.projects.admin.adminapp.aescipher import (generate_new_hex,
                                                              get_key)
LOCK_MODE = 'ACCESS EXCLUSIVE'


def _censor_hex(secret):
    as_hex = bytes.hex(secret)
    hex_len = len(as_hex) - 4
    last_four = as_hex[-4:]
    return f"{hex_len * '*'}{last_four}"


class Command(BaseCommand):
    """Rotate DECRYPTION_HEX and all encrypted values in the database along with it."""
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            help="Generate new hex and show the number of objects to reencrypt."
        )

    def handle(self, *args, **options):  # noqa
        # Get the old hex and generate a new one.
        old_hex = get_key()
        new_hex = generate_new_hex()

        self.stdout.write(self.style.NOTICE(
            f"Old DECRYPTION_HEX: {_censor_hex(old_hex)}\n" +
            f"New DECRYPTION_HEX: {new_hex}"
        ))

        cursor = connection.cursor()

        try:
            with transaction.atomic():
                # Lock the database tables for LDAPConfig and Authentication.
                cursor.execute(f"LOCK TABLE {LDAPConfig._meta.db_table} IN {LOCK_MODE} MODE")
                cursor.execute(f"LOCK TABLE {Authentication._meta.db_table} IN {LOCK_MODE} MODE")

                # Query the database for all objects with encrypted data.
                # keycloaks = KeycloakServer.objects.all()
                ldap_configs = LDAPConfig.objects.select_for_update()
                authentications = Authentication.objects.select_for_update()

                count = ldap_configs.count() + authentications.count()

                # Check that there are some objects to update
                if count > 0:
                    self.stdout.write(self.style.WARNING(
                        "Make sure you take a note of the above key! " +
                        "It will not be printed again and\nit is not recoverable - without it" +
                        " ALL ENCRYPTED PASSWORDS WILL BE LOST."))

                    if options.get('--dry-run'):
                        # Just output the number of objects to update if the '--dry-run' flag is
                        # used.
                        self.stdout.write(f"Info: {count} password(s) would be re-encrypted.")
                    else:
                        # Ask for confirmation
                        choice = input("Continue? [y/N]: ")

                        if choice.lower() == "y":
                            self.stdout.write("Initiating reencryption.")
                            # Query the database, reencrypt the data and update the progres bar
                            with tqdm(total=count, desc="Reencrypting") as bar:
                                for conf in ldap_configs:
                                    conf.rotate_credential(key=bytes.fromhex(new_hex))
                                    bar.update()
                                    conf.save()

                                for auth in authentications:
                                    password = auth.get_password()
                                    auth.set_password(password=password, key=bytes.fromhex(new_hex))
                                    bar.update()
                                    auth.save()

                            self.stdout.write(self.style.SUCCESS(
                                f"Done. {count} password(s) re-encrypted."
                                ))
                        else:
                            self.stdout.write("Process abandoned. Exiting.")
                else:
                    # Otherwise don't do anything
                    self.stdout.write("No encrypted values in the database - nothing to do")

                self.stdout.write(self.style.WARNING(
                        "Remember to change Django's DECRYPTION_HEX setting to the new key."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"An error occured while trying to re-encrypt password(s): "
                f"{e}.\nProcess abandoned. Exiting."))
