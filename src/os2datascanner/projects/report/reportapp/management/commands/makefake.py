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
import random
import string
from faker import Faker
from django.core.management.base import BaseCommand
from os2datascanner.engine2.model.dropbox import DropboxHandle, DropboxSource
from os2datascanner.engine2.model.ews import EWSAccountSource, EWSMailHandle
from os2datascanner.engine2.model.file import FilesystemHandle, FilesystemSource
from os2datascanner.engine2.model.googledrive import (
    GoogleDriveHandle,
    GoogleDriveSource,
)
from os2datascanner.engine2.model.msgraph.files import (
    MSGraphDriveHandle,
    MSGraphFilesSource,
)
from os2datascanner.engine2.model.sbsys import SbsysHandle, SbsysSource
from os2datascanner.engine2.model.smb import SMBHandle, SMBSource
from os2datascanner.projects.report.reportapp.models.documentreport_model import DocumentReport


from os2datascanner.utils.system_utilities import time_now
from os2datascanner.engine2.model import http
from os2datascanner.engine2.rules.cpr import CPRRule
from os2datascanner.engine2.rules.rule import Sensitivity
from os2datascanner.engine2.pipeline import messages
from ...models.organization_model import Organization
from .pipeline_collector import result_message_received_raw


def emit_message(queue, m):
    m = m.to_json_object()
    m["origin"] = queue
    for k in result_message_received_raw(m):
        pass


class Command(BaseCommand):
    """Create realistic (but fake) DocumentReports in the database."""

    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            "--page-count",
            type=int,
            metavar="NUM",
            default=random.randrange(5, 10),
            help="the number of sites to be scanned per source, each site will produce 1 handle"
            " (default: random amount between 5 and 10) ",
        )
        parser.add_argument(
            "--scan-type",
            type=str,
            default=None,
            help="Run on a specific scan, choose between"
            "FileSystemScan, WebSourceScan, DropboxScan,"
            "MSGraphScan, GoogleDriveScan, EWSScan, SMBScan, SBSYSScan",
        )
        parser.add_argument(
            "--scan-count",
            type=int,
            metavar="NUM",
            default=random.randrange(5, 10),
            help="Amount of different scans that are simulated"
            " (default: random amount between 5 and 10) ",
        )

    def handle(self, *, page_count, scan_count, scan_type, **options):
        organization = Organization.objects.first()
        handle_types = {
            "FileSystemScan": make_fake_filesystem_handle,
            "WebSourceScan": make_fake_websource_handle,
            "DropboxScan": make_fake_dropbox_handle,
            "MSGraphScan": make_fake_msgraph_file_handle,
            "GoogleDriveScan": make_fake_google_drive_handle,
            "EWSScan": make_fake_ews_mail_handle,
            "SMBScan": make_fake_smb_handle,
            "SBSYSScan": make_fake_sbsys_handle,
        }
        stats = {"scans": 0, "handles": 0, "matches": 0}
        for scan in range(0, scan_count):

            if not scan_type:
                scan_type, handle_generator_function = random.choice(
                    list(handle_types.items())
                )
            else:
                handle_generator_function = handle_types[scan_type]

            scan_name = "{0}.{1}".format(scan, scan_type)
            scan_spec = make_fake_scan_type(organization, scan_name)

            for page in range(0, page_count):
                handle = handle_generator_function()
                scan_spec = scan_spec._replace(
                    source=handle._source,
                )
                match_here, match_stats = make_fake_match(scan_spec, handle)
                stats["matches"] += match_stats["matches"]
                for match in match_here:
                    emit_message(
                        "os2ds_metadata",
                        messages.MetadataMessage(
                            scan_tag=scan_spec.scan_tag,
                            handle=handle,
                            metadata={"is it a fake scan": "yes it is"},
                        ),
                    )
                emit_message("os2ds_matches", match_here)
                stats["handles"] += 1

            stats["scans"] += 1
        self.stdout.write(
            self.style.SUCCESS(
                f'Generated {stats["matches"]} matches '
                f'from {stats["handles"]} handles '
                f'in {stats["scans"]} scans'
            )
        )


def make_fake_scan_type(organization, scan_name):
    """Create and save a random fake scan"""
    pk = random.randrange(1000, 2**15)
    while DocumentReport.objects.filter(data__scan_tag__scanner__pk=pk).exists():
        pk = random.randrange(1000, 2**15)

    scanner_fragment = messages.ScannerFragment(
        name=scan_name,
        pk=pk,
    )
    organisation_fragment = messages.OrganisationFragment(
        name=organization.name,
        uuid=organization.uuid,
    )
    scan_tag = messages.ScanTagFragment(
        time=time_now(),
        user="dummy",
        organisation=organisation_fragment,
        scanner=scanner_fragment,
    )
    scan_specification = messages.ScanSpecMessage(
        scan_tag=scan_tag,
        source=None,
        rule=make_fake_rule(),
        configuration={},
        progress=None,
    )
    return scan_specification


def make_fake_match(scan_spec, handle):
    """Make a fake match object with the cpr rule"""
    num_matches = random.randint(1, 10)
    fake = Faker()
    match_here = messages.MatchesMessage(
        scan_spec=scan_spec, handle=handle, matched=num_matches, matches=[]
    )
    for i in range(0, num_matches):
        unique_seed = scan_spec.scan_tag.scanner.name + str(handle)
        fragment = messages.MatchFragment(
            make_fake_rule(),
            [
                {
                    "offset": match * 100,
                    "match": random_cpr(unique_seed + str(i * 100 + match)),
                    "context": "{0} {1} {2}".format(
                        fake.paragraph(nb_sentences=1),
                        random_cpr(unique_seed + str(i * 100 + match)),
                        fake.paragraph(nb_sentences=1),
                    ),
                    "context_offset": 15,
                    "probability": random.uniform(0, 1),
                }
                for match in range(1, num_matches + 1)
            ],
        )
        match_here = match_here._replace(matched=True, matches=[fragment])
    return match_here, {"matches": num_matches}


def random_cpr(seed):
    """Create a cpr like string randomly generated by a seed"""
    random.seed(seed)
    match_id = str(random.randrange(100000, 999999))
    match_id += "-" + str(random.randrange(1000, 9999))
    return match_id


def make_fake_rule():
    sensitivity = [
        Sensitivity.INFORMATION,
        Sensitivity.NOTICE,
        Sensitivity.WARNING,
        Sensitivity.PROBLEM,
        Sensitivity.CRITICAL,
    ]
    rule = CPRRule(sensitivity=random.choice(sensitivity))
    return rule


def generate_fake_data(prefix=None, paths=None, file_names=None, file_types=None):
    """Generate fake data with predetermined arrays and Faker"""
    if not paths:
        paths = [
            "/home",
            "/admin",
            "/user",
            "/data",
            "/archives",
            "/downloads",
            "/documents",
        ]
    if not file_names:
        file_names = [
            "employees",
            "danni-data",
            "secure_data",
            "hidden",
            "information",
            "users",
            "passwords_plain",
            "carls-secret-repository",
            "the_truth_behind_datascanner",
        ]
    if not file_types:
        file_types = [".html", ".pdf", ".txt", ".jpg"]
    path_name = ""
    if prefix:
        path_name = prefix[random.randrange(0, len(prefix)) - 1]
    path_lenght = random.randrange(1, 5)
    for i in range(0, path_lenght):
        path_name += paths[random.randrange(0, len(paths))]
    file_name = (
        file_names[random.randrange(0, len(file_names) - 1)]
        + file_types[random.randrange(0, len(file_types) - 1)]
    )
    fake = Faker()
    user = fake.name()
    mail = fake.email()
    return path_name, file_name, mail, user


def make_fake_websource_handle():
    domains = [
        "magenta.dk",
        "google.com",
        "os2.dk",
        "it-site.org",
        "kbh.dk",
        "aarhus.dk",
    ]
    path_name, file_name, mail, user = generate_fake_data(prefix=domains)
    source = http.WebSource(url="https://www." + path_name)
    handle = http.WebHandle(source, file_name)
    return handle


def make_fake_filesystem_handle():
    domains = [
        "/usr",
        "/root",
        "/danni-data",
    ]
    path_name, file_name, mail, user = generate_fake_data(prefix=domains)
    source = FilesystemSource(path_name)
    handle = FilesystemHandle(source, file_name)
    return handle


def make_fake_msgraph_file_handle():
    domains = ["c:/", "./", "/", "f:/", "d:/", "g:/"]
    path_name, file_name, mail, user = generate_fake_data(domains)
    source = MSGraphFilesSource(path_name, 2, 3)
    handle = MSGraphDriveHandle(source, path_name, file_name, user)
    return handle


def make_fake_dropbox_handle():
    domains = ["dropbox:/", "boxdrop:/"]
    path_name, file_name, mail, user = generate_fake_data(domains)
    file_source = DropboxSource(path_name)
    file_handle = DropboxHandle(file_source, path_name + "/" + file_name, mail)
    return file_handle


def make_fake_google_drive_handle():
    path_name, file_name, mail, user = generate_fake_data()
    file_source = GoogleDriveSource(path_name, mail)
    file_handle = GoogleDriveHandle(file_source, path_name, file_name)
    return file_handle


def make_fake_ews_mail_handle():
    path_name, file_name, mail, user = generate_fake_data()
    source = EWSAccountSource(path_name, "magenta.dk", user, "1234", user)
    handle = EWSMailHandle(
        source,
        path_name,
        file_name,
        "/" + path_name.split("/")[0],
        random.randrange(1000, 9999),
    )
    return handle


def make_fake_smb_handle():
    unc = ["\\\\SERVER01", "\\\\COMPANY_SERVER", "\\\\SERVER"]
    path_name, file_name, mail, user = generate_fake_data(prefix=unc)
    source = SMBSource(path_name)
    handle = SMBHandle(source, file_name)
    return handle


def make_fake_sbsys_handle():
    path_name, file_name, mail, user = generate_fake_data()
    source = SbsysSource("client_id", "client_key", file_name, path_name)
    range = random.randrange
    sbsys_id = "{0}.{1}.{2}-{3}-{4}-{5}".format(
        range(10, 99),
        range(10, 99),
        range(10, 99),
        (random.choice(string.ascii_uppercase) + str(range(10, 99))),
        range(1, 9999),
        range(10, 99),
    )
    handle = SbsysHandle(source, sbsys_id)
    return handle
