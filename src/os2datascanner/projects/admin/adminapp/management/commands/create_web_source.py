import uuid
from django.core.management.base import BaseCommand
from recurrence.base import Recurrence
import requests
import urllib.parse
from os2datascanner.projects.admin.adminapp.models.rules.cprrule_model import CPRRule

from os2datascanner.projects.admin.adminapp.models.scannerjobs.webscanner_model import WebScanner
from os2datascanner.projects.admin.organizations.models.organization import Organization


class Command(BaseCommand):
    """A command to generate a websource that can be configured in various ways
    It depends on the service called datasynth in the docker-compose.yml in project root
    If you wish to see the current source replace the 'datasynth' in the link with 0.0.0.0
    ie. http://datasynth:5005/index/?seed=90667
    should be changed to http://0.0.0.0:5005/index/?seed=

    Example usage:
    `create_web_source --matches '{"010180-0008":300}' --sub_files 10 --depth 2 --size 100000`
    """
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            "--seed",
            default=None,
            help="When generating a web-source it will always be generated"
            " with the same random data if a seed has been supplied."
            " if none is supplied, it will generate a random one.\n",
        )
        parser.add_argument(
            "--sub_files",
            default=None,
            help="how many sub files should be included in the source,"
            " the landing/index page is not included in this number, so if"
            " you set it to 0, there will be no links to other pages."
            " Default is a number randomly chosen between 0 and 15.\n",
        )
        parser.add_argument(
            "--size",
            default=None,
            help="The size of the source in bytes, accurate to a 1 percent at 10mb."
            " if none is supplied it will not have a constraint on the size it needs.\n",

        )
        parser.add_argument(
            "--matches",
            default={"010180-0008": 100},
            help="Define which matches should be included in the source"
            " if none is supplied, it will supply this: `{'010180-0008':100}`.\n"
            "NOTE: when suppliying a dict though the terminal it has to be enveloped in quotes",
        )
        parser.add_argument(
            "--depth",
            default=None,
            help="How deep the files can be nested, if there is a depth of 0, "
            "subfiles cant have nested files. If it is set to 1, subfiles can "
            "have a nested file, but that file cant have a nested file etc.. "
            "Default is randomly generated between 0 and 8.\n",
        )

    def handle(self, seed, sub_files, matches, size, depth, **options):
        params = {}
        if seed:
            params["seed"] = seed
        if matches:
            params["matches"] = matches
        if sub_files:
            params["sub_files"] = sub_files
        if size:
            params["size"] = size
        if depth:
            params["depth"] = depth
        params = urllib.parse.urlencode(params)

        response = requests.get(f"http://datasynth:5010/websource?{params}").json()

        scan_url = response["reference"]

        name = f"datasynth webscan: {uuid.uuid1()}"

        org = Organization.objects.first()
        recurrence = Recurrence()
        webscanner, created = WebScanner.objects.get_or_create(
            name=name,
            url=scan_url,
            validation_status=True,
            do_last_modified_check=False,
            organization=org,
            schedule=recurrence,
            download_sitemap=False,
        )
        if created:
            cpr = CPRRule.objects.first()
            webscanner.rules.set([cpr])
            self.stdout.write(self.style.SUCCESS("Webscanner created successfully!"))
            self.stdout.write(self.style.SUCCESS(scan_url))

        else:
            self.stdout.write("Webscanner already exists!")
