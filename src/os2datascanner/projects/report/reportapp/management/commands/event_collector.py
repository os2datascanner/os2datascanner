#!/usr/bin/env python
# The contents of this file are subject to the Mozilla Public License
# Version 2.0 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
#    http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# OS2datascanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (https://os2.eu/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( https://os2.eu/ )

import json
import logging
import structlog

from django.db import IntegrityError
from django.contrib.auth.models import User
from django.core.exceptions import FieldError
from django.core.management.base import BaseCommand
from django.db.models.deletion import ProtectedError

from os2datascanner.utils import debug
from os2datascanner.utils.log_levels import log_levels
from os2datascanner.engine2.pipeline.utilities.pika import PikaPipelineThread

from os2datascanner.projects.report.organizations.models import \
    Account, AccountSerializer,\
    Alias, AliasSerializer, \
    Organization, OrganizationSerializer,\
    OrganizationalUnit, OrganizationalUnitSerializer, \
    Position, PositionSerializer
from os2datascanner.projects.report.reportapp.models.documentreport import DocumentReport

from prometheus_client import Summary, start_http_server

from ...utils import create_alias_and_match_relations

logger = structlog.get_logger(__name__)
SUMMARY = Summary("os2datascanner_event_collector_report",
                  "Messages through event collector report")


def event_message_received_raw(body):
    event_type = body.get("type")
    model_class = body.get("model_class")
    instance = body.get("instance")

    if event_type == "clean_document_reports":
        handle_clean_message(body)
        return

    org_struct_model_and_serializer = {'Account': (Account, AccountSerializer),
                                       'Alias': (Alias, AliasSerializer),
                                       'Organization': (Organization, OrganizationSerializer),
                                       'OrganizationalUnit': (OrganizationalUnit,
                                                              OrganizationalUnitSerializer),
                                       'Position': (Position, PositionSerializer),
                                       }

    if not event_type or not model_class or not instance:
        return

    # Version 3.9.0 switched to using django.core.serializers for
    # ModelChangeEvent messages and so has a completely different wire format.
    # Rather than attempting to handle both, we detect messages from older
    # versions and drop them on the floor
    if not (isinstance(instance, str)
            and instance.startswith("[") and instance.endswith("]")):
        logger.warning("Ignoring old-style ModelChangeEvent")
        return
    else:
        instance = json.loads(instance)[0]

    if model_class in org_struct_model_and_serializer:
        handle_event(event_type=event_type,
                     instance=instance,
                     cls=org_struct_model_and_serializer.get(model_class)[0],
                     cls_serializer=org_struct_model_and_serializer.get(model_class)[1]
                     )
    else:
        logger.debug("event_message_received_raw:"
                     f" unknown model_class {model_class} in event")
        return

    yield from []


def handle_clean_message(body):
    """Accepts a CleanMessage JSON-object, and deletes all document reports
    related to the given account and scanner job."""
    logger.info(f"CleanMessage published by {body.get('publisher')}.")

    account_uuids = body.get("account_uuid", [])
    scanner_pks = body.get("scanner_pk", [])

    for account_uuid in account_uuids:
        account = Account.objects.filter(uuid=account_uuid).first()

        if account:
            related_reports = DocumentReport.objects.filter(
                alias_relation__account=account_uuid,
                scanner_job_pk__in=scanner_pks)

            _, deleted_reports_dict = related_reports.delete()
            deleted_reports = deleted_reports_dict.get("os2datascanner_report.DocumentReport", 0)

            logger.info(
                f"Deleted {deleted_reports} document reports belonging "
                f"to {account.get_full_name()}.")
        else:
            logger.info(
                f"Account with UUID {account_uuid} not found."
            )


def handle_event(event_type, instance, cls, cls_serializer):  # noqa: CCR001, C901, E501 too high cognitive complexity
    cn = cls.__name__

    # We go through objects received and handle special quirks and relations first.
    # Then, we use rest_framework.serializers to perform create and update actions.
    # Each model has implemented its own serializer, which we receive as a parameter.

    # Copy over just the fields of model received
    instance_fields = instance['fields']
    # The primary key is stored in its own key originally, save it as a variable, sometimes needed.
    # This is because there is a difference between PK's for certain models, some using a
    # UUID as PK in the admin module and an Integer PK in the report module.
    instance_pk = instance['pk']

    if cn == "Account":
        # Organization has an integer PK in the report module and a UUID PK in the admin module.
        # Being explicit here, to check on the UUID field.
        org, created = Organization.objects.get_or_create(uuid=instance_fields["organization"][0])
        instance_fields["organization"] = org.pk

        # TODO: Out-phase User in favor of Account
        # This is because User and Account co-exist, but a User doesn't have any
        # unique identifier that makes sense from an Account.. This means that we risk
        # creating multiple User objects, if attributes change.
        # But its the best we can do for now, until we out-phase User objects entirely
        user_obj, created = User.objects.update_or_create(
            username=instance_fields["username"],
            defaults={
                "username": instance_fields["username"],
                "first_name": instance_fields["first_name"] or '',
                "last_name": instance_fields["last_name"] or ''
            })

        instance_fields["user"] = user_obj.pk

        if instance_fields["manager"]:
            instance_fields["manager"] = instance_fields["manager"][0]

    elif cn == "Alias":
        org, created = Organization.objects.get_or_create(uuid=instance_fields["account"][2],
                                                          defaults={
                                                              "name": instance_fields["account"][3]
                                                          })
        # TODO: Preferably objects should have the same datatype of primary key
        account, created = Account.objects.get_or_create(uuid=instance_fields["account"][0],
                                                         defaults={
                                                             "username":
                                                                 instance_fields["account"][1],
                                                             "organization": org
                                                         })
        instance_fields["account"] = account.pk

        user_obj, created = User.objects.update_or_create(username=account.username,
                                                          defaults={
                                                              "is_staff": True
                                                          })
        instance_fields["user"] = user_obj.pk

    elif cn == "OrganizationalUnit":
        # TODO: Preferably objects should have the same datatype of primary key
        org, created = Organization.objects.get_or_create(uuid=instance_fields["organization"][0],
                                                          defaults={
                                                              "name":
                                                                  instance_fields["organization"][1]
                                                          })
        instance_fields["organization"] = org.pk

    elif cn == "Position":
        instance_fields["pk"] = instance_pk

        org, created = Organization.objects.get_or_create(uuid=instance_fields["account"][2],
                                                          defaults={
                                                              "name": instance_fields["account"][3]
                                                          })
        acc, created = Account.objects.get_or_create(uuid=instance_fields["account"][0],
                                                     defaults={
                                                         "organization": org
                                                     })

        instance_fields["account"] = acc.pk

    try:
        if hasattr(cls, "uuid"):
            instance_fields["uuid"] = instance_pk
            existing = cls.objects.get(uuid=instance_pk)

        else:
            existing = cls.objects.get(pk=instance_pk)

        # If we get this far, the object existed
        # go ahead and update or delete
        if event_type == "object_delete":
            # TODO: This check on "User" when deleting an account should become out-phased when
            # we switch to Account as being the "User".
            if cls == Account:
                User.objects.filter(username=existing.username).delete()

            logger.debug(f"handle_event: deleted {cn} {existing}")
            existing.delete()

        elif event_type == "object_update":
            existing_serialized_obj = cls_serializer(existing, data=instance_fields)

            # TODO: This check on "User" when deleting an account should become out-phased when
            # we switch to Account as being the "User".
            if cls == Account:
                existing_user = User.objects.filter(username=existing.username)
                # This is a quirk, because User model allows blank=True, but has null=False
                # Instance fields explicitly returns a "null" value, which can't be inserted in db.
                # Hence, checking for it and making it an empty string before trying to update.
                fn = instance_fields.get("first_name") or ""
                ln = instance_fields.get("last_name") or ""

                existing_user.update(first_name=fn, last_name=ln)

            # TODO: this wont raise an exception if data is invalid. Is that desired?
            if not existing_serialized_obj.is_valid(raise_exception=False):
                logger.warning(f"Error in serialized object! {existing_serialized_obj.errors}")
                return

            existing_serialized_obj.save()
            logger.debug(f"handle_event: updated {cn} {existing}")

        else:
            logger.warning("handle_event: unexpected event_type"
                           f" {event_type} for {cn} {existing}")

    except cls.DoesNotExist:
        if event_type == "object_delete":
            # Take no action if we're being asked to delete an object that
            # already doesn't exist
            logger.debug(f"handle_event: not creating deleted {cn}")
            return

        # The object didn't exist -- save it. Note that we might also end up
        # here with an update event if the initial create event didn't get
        # propagated over to the report module

        # Use provided class serializer to create a new record.
        serialized_obj = cls_serializer(data=instance_fields)

        if not serialized_obj.is_valid(raise_exception=False):
            logger.warning(f"Error in serialized object! {serialized_obj.errors}")
            return

        # Perform save operation through serializer
        try:
            serialized_obj.save()
        except IntegrityError:
            logger.warning(f"Integrity error on save for {cn}-type object, "
                           f"PK: {instance_pk}. Doing nothing.", exc_info=True)
            return

        if cn == "Alias":
            # One more thing... We have to make sure alias-match relations are in order.
            create_alias_and_match_relations(Alias.objects.get(uuid=instance_pk))

        logger.debug(f"handle_event: created {cn} {instance_pk}")

    except FieldError as e:
        logger.debug(f"handle_event: FieldError when handling {instance_pk}: {e}")
    except AttributeError as e:
        logger.debug(f"handle_event: AttributeError when handling {instance_pk}: {e}")
    except ProtectedError as e:
        logger.debug(
                f"handle_event: couldn't delete {cn} {instance_pk}: {e}")


class EventCollectorRunner(PikaPipelineThread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        start_http_server(9091)

    def handle_message(self, routing_key, body):
        with SUMMARY.time():
            logger.debug(
                "Event collector received a raw message ",
                routing_key=routing_key,
                body=body)
            if routing_key == "os2ds_events":
                yield from event_message_received_raw(body)


class Command(BaseCommand):
    """Command for starting an event collector process."""
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
                "--log",
                default="info",
                help="change the level at which log messages will be printed",
                choices=log_levels.keys())

    def handle(self, *args, log, **options):
        debug.register_backtrace_signal()

        # change formatting to include datestamp
        fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        logging.basicConfig(format=fmt, datefmt='%Y-%m-%d %H:%M:%S')
        # set level for root logger
        logging.getLogger("os2datascanner").setLevel(log_levels[log])

        EventCollectorRunner(
                read=["os2ds_events"],
                prefetch_count=8).run_consumer()
