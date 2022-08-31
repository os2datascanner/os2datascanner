from django.views.generic import TemplateView


class ManualMainView(TemplateView):
    template_name = "manual.html"
