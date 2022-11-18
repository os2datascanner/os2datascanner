from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from os2datascanner.projects.admin.adminapp.models.scannerjobs.scanner import Scanner


class AnalysisPageView(LoginRequiredMixin, TemplateView):
    context_object_name = 'scanner_list'
    scanners = None

    def get_template_names(self):
        is_htmx = self.request.headers.get('HX-Request') == 'true'
        if is_htmx:
            return "components/analysis-template.html"
        else:
            return "components/analysis.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.scanners is None:
            self.scanners = Scanner.objects.all()

        context["scanners"] = (self.scanners, self.request.GET.get('scannerjob', 'none'))

        pk = context["scanners"][1]
        if pk == 'none':
            context["selected_scanner"] = None
        else:
            context["selected_scanner"] = self.scanners.filter(pk=int(pk))

        context["bar_list"] = ["PNG", "JPEG", "PDF", "XLS", "TXT"]
        context["pie_list"] = ["a", "b"]
        return context
