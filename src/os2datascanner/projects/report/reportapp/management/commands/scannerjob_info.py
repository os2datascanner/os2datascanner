from collections import defaultdict
from django.core.management.base import BaseCommand
from ...models.documentreport_model import DocumentReport


class Command(BaseCommand):
    """ Provided a PK of a scanner job finds associated document reports and
    prints scanner job name, total message count, problem message count, match message count
    and provide mimetype info for these messages."""

    help = "Provide a scanner job PK to get match and problem message details"

    def add_arguments(self, parser):
        parser.add_argument(
            "pk",
            type=int,
            help="Primary key of scanner job",
            default=None,
        )


    def handle(self, pk, *args, **options):
        scanner_name = None
        problem_msgs = 0
        match_msgs = 0
        data_mime_type_problems = defaultdict(int)
        data_mime_type_matches = defaultdict(int)

        doc_reps = DocumentReport.objects.filter(data__scan_tag__scanner__pk=pk)

        if doc_reps:
            for doc_rep in doc_reps:
                if doc_rep.problem:
                    scanner_name = doc_rep.scan_tag.scanner.name
                    handle = doc_rep.problem.handle
                    problem_msgs += 1

                    if handle:
                        while handle.source.handle:
                            handle = handle.source.handle

                        data_mime_type_problems[handle.guess_type()] += 1

                if doc_rep.matches:
                    scanner_name = doc_rep.scan_tag.scanner.name
                    handle = doc_rep.matches.handle
                    match_msgs += 1

                    if handle:
                        while handle.source.handle:
                            handle = handle.source.handle
                        data_mime_type_matches[handle.guess_type()] += 1


            self.stdout.write(self.style.SUCCESS(f'{scanner_name} (PK: {pk})\n'
                                                 f'Total message count: {match_msgs+problem_msgs}\n'
                                                 f' * Matches {match_msgs}\n'
                                                 f' * Problems {problem_msgs}'))


            if data_mime_type_problems:
                self.stdout.write(self.style.SUCCESS(f'--------------------\n'
                                                     f'Problem Messages Mimetypes'))
                for key in data_mime_type_problems:
                    self.stdout.write(self.style.SUCCESS(f' * {key} : {data_mime_type_problems[key]}'))

            if data_mime_type_matches:
                self.stdout.write(self.style.SUCCESS(f'--------------------\n'
                                                     f'Match Messages Mimetypes'))
                for key in data_mime_type_matches:
                    self.stdout.write(self.style.SUCCESS(f' * {key} : {data_mime_type_matches[key]}'))

        else:
            self.stdout.write(self.style.WARNING("No scanner job PK matching in DocumentReports found"))