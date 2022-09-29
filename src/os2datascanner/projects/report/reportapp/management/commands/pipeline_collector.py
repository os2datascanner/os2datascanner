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
from django.db import transaction
from django.db.models.deletion import ProtectedError

from os2datascanner.engine2.conversions.types import OutputType
from os2datascanner.engine2.model.core import Handle, Source
from os2datascanner.engine2.pipeline import messages
from os2datascanner.engine2.pipeline.run_stage import _loglevels
from os2datascanner.engine2.pipeline.utilities.pika import PikaPipelineThread
from os2datascanner.engine2.rules.last_modified import LastModifiedRule

from os2datascanner.projects.report.organizations.models import \
    Account, AccountSerializer,\
    Alias, AliasSerializer, \
    Organization, OrganizationSerializer,\
    OrganizationalUnit, OrganizationalUnitSerializer, \
    Position, PositionSerializer

from os2datascanner.utils.system_utilities import time_now
from prometheus_client import Summary, start_http_server

from ...models.documentreport import DocumentReport
from ...utils import hash_handle, prepare_json_object, create_alias_and_match_relations

logger = structlog.get_logger(__name__)
SUMMARY = Summary("os2datascanner_pipeline_collector_report",
                  "Messages through report collector")


def result_message_received_raw(body):
    """Method for restructuring and storing result body.

    The agreed structure is as follows:
    {'scan_tag': {...}, 'matches': null, 'metadata': null, 'problem': null}
    """
    reference = body.get("handle") or body.get("source")
    path = hash_handle(reference)
    tag, queue = _identify_message(body)
    if not reference or not tag or not queue:
        return
    tag = messages.ScanTagFragment.from_json_object(tag)

    # XXX: ideally we would only log once in this file. When all is done, log the
    # following AND what actions were taken.
    logger.debug(
        "msg received",
        queue=queue,
        tag=tag.scanner.to_json_object(),
        handle=Handle.from_json_object(reference).censor().to_json_object()
        if body.get("handle") else None,
        source=Source.from_json_object(reference).censor().to_json_object()
        if not body.get("handle") else None,
    )

    if queue == "matches":
        handle_match_message(path, tag, body)
    elif queue == "problem":
        handle_problem_message(path, tag, body)
    elif queue == "metadata":
        handle_metadata_message(path, tag, body)

    yield from []


def event_message_received_raw(body):
    event_type = body.get("type")
    model_class = body.get("model_class")
    instance = body.get("instance")

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


def handle_metadata_message(path, scan_tag, result):
    # Evaluate the queryset that is updated later to lock it.
    DocumentReport.objects.select_for_update(
        of=('self',)
    ).filter(
        path=path,
        scanner_job_pk=scan_tag.scanner.pk
    ).first()

    message = messages.MetadataMessage.from_json_object(result)

    lm = None
    if "last-modified" in message.metadata:
        lm = OutputType.LastModified.decode_json_object(
                message.metadata["last-modified"])
    else:
        # If no scan_tag time is found, default value to current time as this
        # must be some-what close to actual scan_tag time.
        # If no datasource_last_modified value is ever set, matches will not be
        # shown.
        lm = scan_tag.time or time_now()

    dr, _ = DocumentReport.objects.update_or_create(
            path=path, scanner_job_pk=scan_tag.scanner.pk,
            defaults={
                "scan_time": scan_tag.time,
                "raw_scan_tag": prepare_json_object(
                        scan_tag.to_json_object()),

                "raw_metadata": prepare_json_object(result),
                "datasource_last_modified": lm,
                "scanner_job_name": scan_tag.scanner.name,
                "only_notify_superadmin": scan_tag.scanner.test,
                "resolution_status": None,
                "organization": get_org_from_scantag(scan_tag)
            })
    create_aliases(dr)
    return dr


def create_aliases(obj):
    tm = Alias.match_relation.through
    new_objects = []

    metadata = obj.metadata
    if not metadata:
        return

    if (email := metadata.metadata.get("email-account")):
        email_alias = Alias.objects.filter(_alias_type="email", _value__iexact=email)
        add_new_relations(email_alias, new_objects, obj, tm)
    if (adsid := metadata.metadata.get("filesystem-owner-sid")):
        adsid_alias = Alias.objects.filter(_alias_type="SID", _value=adsid)
        add_new_relations(adsid_alias, new_objects, obj, tm)
    if (web_domain := metadata.metadata.get("web-domain")):
        web_domain_alias = Alias.objects.filter(_alias_type="generic", _value=web_domain)
        add_new_relations(web_domain_alias, new_objects, obj, tm)

    try:
        tm.objects.bulk_create(new_objects, ignore_conflicts=True)
    except Exception:
        logger.error("Failed to create match_relation", exc_info=True)


def add_new_relations(adsid_alias, new_objects, obj, tm):
    for alias in adsid_alias:
        new_objects.append(
            tm(documentreport_id=obj.pk, alias_id=alias.pk))


def handle_match_message(path, scan_tag, result):  # noqa: CCR001, E501 too high cognitive complexity
    locked_qs = DocumentReport.objects.select_for_update(of=('self',))
    new_matches = messages.MatchesMessage.from_json_object(result)
    # The queryset is evaluated and locked here.
    previous_report = (locked_qs.filter(
            path=path, scanner_job_pk=scan_tag.scanner.pk).
            exclude(scan_time=scan_tag.time).order_by("-scan_time").first())

    matches = [(match.rule.presentation, match.matches) for match in new_matches.matches]
    logger.debug(
        "new matchMsg",
        handle=new_matches.handle.presentation,
        msgtype="matches",
        matches=matches,
    )
    if previous_report and previous_report.resolution_status is None:
        # There are existing unresolved results; resolve them based on the new
        # message
        if not new_matches.matched:
            # No new matches. Be cautiously optimistic, but check what
            # actually happened
            if (len(new_matches.matches) == 1
                    and isinstance(new_matches.matches[0].rule,
                                   LastModifiedRule)):
                # The file hasn't been changed, so the matches are the same
                # as they were last time. Instead of making a new entry,
                # just update the timestamp on the old one
                logger.debug("Resource not changed: updating scan timestamp",
                             report=previous_report)
                DocumentReport.objects.filter(pk=previous_report.pk).update(
                        scan_time=scan_tag.time)
            else:
                # The file has been edited and the matches are no longer
                # present
                logger.debug("Resource changed: no matches, status is EDITED",
                             report=previous_report)
                DocumentReport.objects.filter(pk=previous_report.pk).update(
                        resolution_status=(
                                DocumentReport.ResolutionChoices.
                                EDITED.value))
        else:
            # The file has been edited, but matches are still present.
            # Resolve the previous ones
            logger.debug("matches still present, status is EDITED",
                         report=previous_report)
            DocumentReport.objects.filter(pk=previous_report.pk).update(
                    resolution_status=(
                            DocumentReport.ResolutionChoices.EDITED.value))

    if new_matches.matched:
        # Collect and store the top-level type label from the matched object
        source = new_matches.handle.source
        while source.handle:
            source = source.handle.source

        dr, _ = DocumentReport.objects.update_or_create(
                path=path, scanner_job_pk=scan_tag.scanner.pk,
                defaults={
                    "scan_time": scan_tag.time,
                    "raw_scan_tag": prepare_json_object(
                            scan_tag.to_json_object()),

                    "source_type": source.type_label,
                    "name": prepare_json_object(
                            new_matches.handle.presentation_name),
                    "sort_key": prepare_json_object(
                            new_matches.handle.sort_key),
                    "sensitivity": new_matches.sensitivity.value,
                    "probability": new_matches.probability,
                    "raw_matches": prepare_json_object(
                            sort_matches_by_probability(result)),
                    "scanner_job_name": scan_tag.scanner.name,
                    "only_notify_superadmin": scan_tag.scanner.test,
                    "resolution_status": None,
                    "organization": get_org_from_scantag(scan_tag)
                })

        logger.debug("matches, saved DocReport", report=dr)
        return dr
    else:
        logger.debug("No new matches.")
        return None


def sort_matches_by_probability(body):
    """The scanner engine have some internal rules
    and the matches they produce are also a part of the message.
    These matches are not necessary in the report module.
    An example of an internal rule is, images below a certain size are
    ignored."""

    # Rules are under no obligation to produce matches in any
    # particular order, but we want to display them in
    # descending order of probability
    for match_fragment in body["matches"]:
        if match_fragment["matches"]:
            match_fragment["matches"].sort(
                key=lambda match_dict: match_dict.get(
                    "probability", 0.0),
                reverse=True)
    return body


def handle_problem_message(path, scan_tag, result):
    locked_qs = DocumentReport.objects.select_for_update(of=('self',))
    problem = messages.ProblemMessage.from_json_object(result)
    # Queryset is evaluated and locked here.
    previous_report = (locked_qs.filter(
            path=path, scanner_job_pk=scan_tag.scanner.pk).
            exclude(scan_time=scan_tag.time).order_by("-scan_time").first())

    handle = problem.handle if problem.handle else None
    presentation = str(handle) if handle else "(source)"
    if (previous_report
            and previous_report.resolution_status in [0, None]
            and problem.missing):
        # The file previously had matches, but is now removed.
        logger.debug(
            "Resource deleted, status is REMOVED",
            report=previous_report,
            handle=presentation,
            msgtype="problem",
        )
        DocumentReport.objects.filter(pk=previous_report.pk).update(resolution_status=(
                DocumentReport.ResolutionChoices.REMOVED.value))
        return None
    else:

        # Collect and store the top-level type label from the failing object
        source = problem.handle.source if problem.handle else problem.source
        while source.handle:
            source = source.handle.source

        dr, _ = DocumentReport.objects.update_or_create(
                path=path, scanner_job_pk=scan_tag.scanner.pk,
                defaults={
                    "scan_time": scan_tag.time,
                    "raw_scan_tag": prepare_json_object(
                            scan_tag.to_json_object()),

                    "source_type": source.type_label,
                    "name": prepare_json_object(
                            handle.presentation_name) if handle else "",
                    "sort_key": prepare_json_object(
                            handle.sort_key if handle else "(source)"),
                    "raw_problem": prepare_json_object(result),
                    "scanner_job_name": scan_tag.scanner.name,
                    "only_notify_superadmin": scan_tag.scanner.test,
                    "resolution_status": None,
                    "organization": get_org_from_scantag(scan_tag)
                })

        logger.debug(
            "Unresolved, saving new report",
            report=dr,
            handle=presentation,
            msgtype="problem",
        )
        return dr


def _identify_message(result):
    origin = result.get('origin')

    if origin == 'os2ds_problems':
        return result.get("scan_tag"), "problem"
    elif origin == 'os2ds_metadata':
        return result.get("scan_tag"), "metadata"
    elif origin == "os2ds_matches":
        return result["scan_spec"].get("scan_tag"), "matches"
    else:
        return None, None


def get_org_from_scantag(scan_tag):
    return Organization.objects.filter(uuid=scan_tag.organisation.uuid).first()


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
                           f"PK: {instance_pk}. Doing nothing.")
            pass

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


class CollectorRunner(PikaPipelineThread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        start_http_server(9091)

    def handle_message(self, routing_key, body):
        with SUMMARY.time():
            logger.debug(
                "raw message received",
                routing_key=routing_key,
                body=body)
            if routing_key == "os2ds_results":
                with transaction.atomic():
                    yield from result_message_received_raw(body)
            elif routing_key == "os2ds_events":
                yield from event_message_received_raw(body)


class Command(BaseCommand):
    """Command for starting a pipeline collector process."""
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
                "--log",
                default="info",
                help="change the level at which log messages will be printed",
                choices=_loglevels.keys())

    def handle(self, *args, log, **options):
        # change formatting to include datestamp
        fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        logging.basicConfig(format=fmt, datefmt='%Y-%m-%d %H:%M:%S')
        # set level for root logger
        logging.getLogger("os2datascanner").setLevel(_loglevels[log])

        CollectorRunner(
                read=["os2ds_results", "os2ds_events"],
                prefetch_count=8).run_consumer()
