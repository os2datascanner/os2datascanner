import time
from django.core.management.base import BaseCommand
import requests
import urllib.parse
import structlog
from os2datascanner.projects.admin.adminapp.models.rules.cprrule_model import CPRRule
from os2datascanner.projects.admin.adminapp.models.scannerjobs.scanner_model import ScanStatus
from os2datascanner.projects.admin.adminapp.models.scannerjobs.webscanner_model import WebScanner
from os2datascanner.projects.admin.organizations.models.organization import Organization
import cProfile
import pstats

logger = structlog.get_logger(__name__)


class Command(BaseCommand):
    """A command to measure performance on a scannerjob
    """
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            'report_location',
            nargs='?',
            default=None,
            help='used for gitlab ci',
        )

    def handle(self, report_location, **options):
        """ Tests the performance of a webscan
        will fail if the average time of a scan goes above the given uncertainty factor
        """
        allowed_time_per_scan = 900
        uncertainty_factor = 0.2
        uncertainty = allowed_time_per_scan*uncertainty_factor

        total_time, average_scan_time = self.run_performance_scan(report_location)

        if average_scan_time - uncertainty > allowed_time_per_scan:
            self.stdout.write(self.style.ERROR(f"average: {average_scan_time}"))
            raise AssertionError("The average time of a scan took too long "
                                 + f"total time: {total_time}, average_time:{average_scan_time}")
        else:
            self.stdout.write(self.style.SUCCESS(f"average: {average_scan_time}"))

    def run_performance_scan(self, report_location=None):
        """ Runs a performance scan 5 times and measures the average time from start to finish

            NOTE: There are however some caveats:
            - since the scan runs asynchronous it is hard to measure how much time that is spent
                within datascanner and how much time that is spent with generating the data.
        """
        params = {"seed": "os2datascanner",
                  "sub_files": 100,
                  "matches": {"010180-0008": 1000},
                  # 10 mb
                  "size": 10_000_000,
                  "depth": 5
                  }

        params = urllib.parse.urlencode(params)

        response = requests.get(f"http://datasynth:5010/websource?{params}").json()
        stats = requests.get(f"http://datasynth:5010/websource?{params}").json()
        logger.info(f"response -> {response}")

        scan_url = response["reference"]

        org = Organization.objects.first()
        webscanner, created = WebScanner.objects.get_or_create(
            name="Performance scan",
            url=scan_url,
            organization=org,
            download_sitemap=False,
        )
        if created:
            cpr = CPRRule.objects.first()
            webscanner.rules.set([cpr])
            self.stdout.write(self.style.SUCCESS(scan_url))
        start = time.process_time()

        iterations = 2
        with cProfile.Profile() as profile:
            for _ in range(iterations):
                scan_start = time.process_time()
                scantag = webscanner.run()
                while not (ScanStatus.objects.filter(scan_tag=scantag).first()).finished:
                    continue
                logger.info(f"took {time.process_time() - scan_start} sec")
        stats = pstats.Stats(profile)
        logger.info(f"total time: {time.process_time() - start} sec")

        now = time.process_time()
        total_time = now - start
        average = total_time/iterations
        stats.sort_stats(pstats.SortKey.TIME)
        stats.reverse_order()
        if report_location:
            stats.dump_stats(filename=f"{report_location}/performance.prof")
        else:
            stats.dump_stats(filename="/code/src/os2datascanner/performance.prof")
        return total_time, average
