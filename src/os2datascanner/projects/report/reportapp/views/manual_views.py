from django.views.generic import TemplateView


class ManualMainView(TemplateView):
    template_name = "manual.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # We want to return true here, if the user has access to the admin module.
        context["user_is_admin"] = self.request.user.is_superuser
        return context
