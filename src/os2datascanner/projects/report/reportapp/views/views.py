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
import collections
import structlog

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import View, TemplateView, ListView

from ..models.documentreport_model import DocumentReport
from ..models.roles.defaultrole_model import DefaultRole

from os2datascanner.engine2.rules.cpr import CPRRule
from os2datascanner.engine2.rules.rule import Sensitivity
from os2datascanner.engine2.rules.regex import RegexRule

logger = structlog.get_logger()

RENDERABLE_RULES = (CPRRule.type_label, RegexRule.type_label,)


class LoginRequiredMixin(View):
    """Include to require login."""

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """Check for login and dispatch the view."""
        return super().dispatch(*args, **kwargs)


class LoginPageView(View):
    template_name = 'login.html'


class MainPageView(TemplateView, LoginRequiredMixin):
    template_name = 'index.html'
    data_results = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        # First attempt to make some usefull logging.
        # The report module task is to log every action the user makes
        # for the security of the user.
        # If the system can document the users actions the user can defend
        # them self against any allegations of wrong doing.
        logger.info('{} is watching {}.'.format(user, self.template_name))

        roles = user.roles.select_subclasses() or [DefaultRole(user=user)]
        results = DocumentReport.objects.none()
        for role in roles:
            results |= role.filter(DocumentReport.objects.all())

        # Calls func to do initial filtering
        filter_matches(results)
        # Results are grouped by the rule they where found with,
        # together with the count.
        sensitivities = {}
        for dr in results:
            if dr.matches:
                sensitivity = dr.matches.sensitivity
                if not sensitivity in sensitivities:
                    sensitivities[sensitivity] = 0
                sensitivities[sensitivity] += 1
        context['dashboard_results'] = sensitivities

        # Perform sorting based on highest sensitivity first.
        context['dashboard_results'] = collections.OrderedDict(
            sorted(context['dashboard_results'].items(), key=lambda x: x[0].value, reverse=True))
        return context


class SensitivityPageView(ListView, LoginRequiredMixin):
    template_name = 'sensitivity.html'
    paginate_by = 25  # Determines how many objects pr. page.
    context_object_name = "matches"  # object_list renamed to something more relevant

    def get_queryset(self):
        user = self.request.user
        roles = user.roles.select_subclasses() or [DefaultRole(user=user)]
        results = DocumentReport.objects.none()

        sensitivity = Sensitivity(int(self.request.GET.get('value')) or 0)

        for role in roles:
            batch = role.filter(DocumentReport.objects.all())
            results |= filter_matches(batch)

        # Exclude matches with None or other sensitivity value.
        # Sort matches after probability value if any.
        # If probability value is None the result will be shown last in the list.
        self.kwargs['matches'] = sorted(
            (r for r in results if r.matches
             and r.matches.sensitivity == sensitivity),
            key=lambda result: result.matches.probability, reverse=True)
        self.kwargs['sensitivity'] = sensitivity

        return self.kwargs['matches']

class StatisticsPageView(TemplateView):
    template_name = 'statistics.html'

class ApprovalPageView(TemplateView):
    template_name = 'approval.html'


class StatsPageView(TemplateView):
    template_name = 'stats.html'


class SettingsPageView(TemplateView):
    template_name = 'settings.html'


class AboutPageView(TemplateView):
    template_name = 'about.html'


# Function to do initial filtering in matches. Used at both index and sensitivity page.
def filter_matches(results):
    # Filter out anything we don't know how to show in the UI
    data_results = []
    for result in results:
        if (result.data
                and "matches" in result.data
                and result.data["matches"]):
            match_message_raw = result.data["matches"]
            renderable_fragments = [
                frag for frag in match_message_raw["matches"]
                if frag["rule"]["type"] in RENDERABLE_RULES
                   and frag["matches"]]
            if renderable_fragments:
                match_message_raw["matches"] = renderable_fragments
                # Rules are under no obligation to produce matches in any
                # particular order, but we want to display them in
                # descending order of probability
                for match_fragment in renderable_fragments:
                    match_fragment["matches"].sort(
                        key=lambda match_dict: match_dict.get(
                            "probability", 0.0),
                        reverse=True)
                data_results.append(result)
    data_results.sort(key=
                      lambda result: (result.matches.sensitivity.value, result.pk))
    return data_results
