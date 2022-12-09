from .scanner import Scanner
from django.db import models
from django.utils.translation import ugettext_lazy as _
from os2datascanner.projects.admin.core.models import BackgroundJob
from os2datascanner.engine2.model.core import SourceManager


class AnalysisJob(BackgroundJob):
    """
    Model for running analysis job to get sizes of files
    """

    scanner = models.ForeignKey(Scanner,
                                on_delete=models.CASCADE)

    def run(self):
        sm = SourceManager()

        try:
            source = list(
                Scanner.objects.select_subclasses().get(
                    pk=self.scanner.pk).generate_sources())[0]
            self.save()
        except Exception:
            print("Source not found")

        for handle in source.handles(sm):
            if isinstance(handle, tuple) and handle[1]:
                continue

            try:
                size = handle.follow(sm).get_size()
            except OSError:
                continue

            mime = handle.guess_type()
            if mime == "application/octet-stream":
                continue

            type_object, created = TypeStats.objects.get_or_create(analysis_job=self,
                                                                   mime_type=mime)

            if created:
                type_object.sizes = [size]
            else:
                type_object.sizes.append(size)
            type_object.save()

    def __str__(self):
        return f'Analysis for {self.scanner}'


class TypeStats(models.Model):
    """
    Model object for storing sizes of files for analysis
    """

    analysis_job = models.ForeignKey(AnalysisJob,
                                     related_name="types",
                                     on_delete=models.CASCADE)

    mime_type = models.TextField(
        verbose_name=_("Mime type")
    )

    sizes = models.JSONField(
        null=True,
        blank=True
    )

    @property
    def count(self):
        return len(self.sizes)

    def __str__(self):
        return f'{self.analysis_job}: {self.mime_type} ({self.count})'
