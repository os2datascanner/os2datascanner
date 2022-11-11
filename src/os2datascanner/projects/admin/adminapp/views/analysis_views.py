from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from os2datascanner.projects.admin.adminapp.models.scannerjobs.scanner import Scanner


class AnalysisPageView(LoginRequiredMixin, TemplateView):
    context_object_name = 'scanner_list'
    scanners = None

    def get_template_names(self):
        return "partials/analysis-template.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.scanners is None:
            self.scanners = Scanner.objects.all()

        context["scanners"] = (self.scanners, self.request.GET.get('scannerjob', 'all'))
        # is_htmx = self.request.headers.get('HX-Request') == "true"

        context["bar_list"] = ["x", "y", "z"]
        context["pie_list"] = ["a", "b"]
        return context
