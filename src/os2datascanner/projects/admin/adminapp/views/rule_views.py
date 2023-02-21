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
# OS2datascanner is developed by Magenta in collaboration with the OS2 public
# sector open source network <https://os2.eu/>.
#
from django import forms
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from os2datascanner.projects.admin.organizations.models import Organization

from .views import RestrictedListView, RestrictedCreateView, \
    RestrictedUpdateView, RestrictedDeleteView
from ..models.sensitivity_level import Sensitivity
from ..models.rules.rule import Rule
from ..models.rules.cprrule import CPRRule
from ..models.rules.regexrule import RegexRule, RegexPattern
from ..models.rules.customrule import CustomRule
from ...utilities import UserWrapper


class RuleList(RestrictedListView):
    """Displays list of scanners."""

    model = Rule
    context_object_name = 'rules'
    template_name = 'os2datascanner/rules.html'

    def get_context_data(self):
        context = super().get_context_data()

        context["sensitivity"] = Sensitivity
        context["systemrule_list"] = self.get_queryset().filter(customrule__isnull=True)
        context["customrule_list"] = self.get_queryset().filter(customrule__isnull=False)

        return context


class RuleCreate(RestrictedCreateView):
    """Create a rule view."""

    model = Rule
    fields = ['name', 'description', 'sensitivity', 'organization']

    @staticmethod
    def _save_rule_form(form):
        rule = form.save(commit=False)
        rule.name = form.cleaned_data['name']
        rule.sensitivity = form.cleaned_data['sensitivity']
        rule.description = form.cleaned_data['description']
        if crule := form.cleaned_data.get('rule'):
            print("crule:", crule)
            rule._rule = crule
        rule.save()
        return rule

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = UserWrapper(self.request.user)
        org_qs = Organization.objects.filter(user.make_org_Q("uuid"))
        form.fields['organization'].queryset = org_qs
        form.fields['organization'].empty_label = None

        return form

    def form_valid(self, form):
        """
        validate all the form first
        :param form:
        :return:
        """
        try:
            with transaction.atomic():
                RuleCreate._save_rule_form(form)
                return super().form_valid(form)
        except Exception:
            return super().form_invalid(form)


class CustomRuleCreate(RuleCreate):
    model = CustomRule
    fields = ['name', 'description', 'sensitivity', 'organization']

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['rule'] = forms.JSONField()

        return form


class RegexRuleCreate(RuleCreate):
    model = RegexRule

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # Then a dynamic form to create multiple pattern fields
        # See - https://www.caktusgroup.com/blog/2018/05/07/creating-dynamic-forms-django/
        # (Creating a dynamic form)
        self.patterns = extract_pattern_fields(form.data)

        idx = 0
        for field_name, value in self.patterns:
            form.fields[field_name] = forms.CharField(
                    required=True, initial=value, label=_('Expression'))
            idx += 1

        return form

    def get_pattern_fields(self):
        yield ("pattern_0", "")

    def form_valid(self, form):
        """
        validate all the form first
        :param form:
        :return:
        """
        form_patterns = [form.cleaned_data[field_name]
                         for field_name in form.cleaned_data if
                         field_name.startswith('pattern_') and
                         form.cleaned_data[field_name] != '']

        try:
            with transaction.atomic():
                regexrule = RuleCreate._save_rule_form(form)
                for pattern in form_patterns:
                    r_ = RegexPattern.objects.create(
                            regex=regexrule, pattern_string=pattern)
                    r_.save()

                # Skip the RuleCreate implementation of form_valid -- we've
                # already created our (Regex)Rule object
                return super().form_valid(form)
        except Exception:
            return super().form_invalid(form)

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/rules/regex/%s/created/' % self.object.pk


class CPRRuleCreate(RuleCreate):
    model = CPRRule
    fields = RuleCreate.fields + [
            'do_modulus11', 'ignore_irrelevant', 'whitelist']

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/rules/cpr/%s/created/' % self.object.pk


class RuleUpdate(RestrictedUpdateView):
    """Update a rule view."""

    model = Rule
    edit = True
    fields = ['name', 'description', 'sensitivity', 'organization']

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = UserWrapper(self.request.user)
        org_qs = Organization.objects.filter(user.make_org_Q("uuid"))
        form.fields['organization'].queryset = org_qs
        form.fields['organization'].empty_label = None

        return form

    def form_valid(self, form):
        """
        validate all the form first
        :param form:
        :return:
        """
        try:
            with transaction.atomic():
                RuleCreate._save_rule_form(form)
                return super().form_valid(form)
        except Exception:
            return super().form_invalid(form)


class CustomRuleUpdate(RuleUpdate):
    model = CustomRule
    fields = ['name', 'description', 'sensitivity', 'organization']

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['rule'] = forms.JSONField(initial=self.object._rule)

        return form


class RegexRuleUpdate(RuleUpdate):
    model = RegexRule

    def get_form(self, form_class=None):
        """Get the form for the view.

        All form fields will have the css class 'form-control' added.
        """
        if form_class is None:
            form_class = self.get_form_class()

        form = super().get_form(form_class)
        regex_patterns = self.object.patterns.all().order_by('-id')

        if not form.data:
            # create extra fields to hold the pattern strings
            for i in range(len(regex_patterns)):
                field_name = 'pattern_%s' % (i,)
                form.fields[field_name] = forms.CharField(
                        required=True,
                        initial=regex_patterns[i].pattern_string,
                        label=_('Expression'))
        else:
            self.patterns = extract_pattern_fields(form.data)

            idx = 0
            for field_name, value in self.patterns:
                form.fields[field_name] = forms.CharField(
                        required=True, initial=value, label=_('Expression'))
                idx += 1

        # assign class attribute to all fields
        for fname in form.fields:
            f = form.fields[fname]
            f.widget.attrs['class'] = 'form-control'

        return form

    def form_valid(self, form):
        """
        validate all the form first
        :param form:
        :return:
        """
        form_patterns = [form.cleaned_data[field_name]
                         for field_name in form.cleaned_data if
                         field_name.startswith('pattern_') and
                         form.cleaned_data[field_name] != '']

        try:
            with transaction.atomic():
                regexrule = RuleCreate._save_rule_form(form)
                self.object.patterns.all().delete()
                for pattern in form_patterns:
                    r_ = RegexPattern.objects.create(
                            regex=regexrule, pattern_string=pattern)
                    r_.save()

                # Skip the RuleUpdate implementation of form_valid -- we've
                # already created our (Regex)Rule object
                return super(RuleUpdate, self).form_valid(form)
        except Exception:
            return super().form_invalid(form)

    def get_pattern_fields(self):
        """
        Used in the template to get the field names and their values
        :return:
        """
        for index, f in enumerate(self.get_object().patterns.all()):
            yield ("pattern_{0}".format(index), f.pattern_string)

    def get_success_url(self):
        """The URL to redirect to after successful update."""
        return '/rules/regex/%s/saved/' % self.object.pk


class CPRRuleUpdate(RuleUpdate):
    model = CPRRule
    fields = RuleUpdate.fields + [
            'do_modulus11', 'ignore_irrelevant', 'whitelist']

    def get_success_url(self):
        """The URL to redirect to after successful update."""
        return '/rules/cpr/%s/saved/' % self.object.pk


class RuleDelete(RestrictedDeleteView):
    """Delete a rule view."""
    model = Rule
    success_url = '/rules/'


class CustomRuleDelete(RuleDelete):
    model = CustomRule


class RegexRuleDelete(RuleDelete):
    model = RegexRule


class CPRRuleDelete(RuleDelete):
    model = CPRRule


'''============ Methods required by multiple views ============'''


def extract_pattern_fields(form_fields):
    if not form_fields:
        return [('pattern_0', '')]

    return [(field_name, form_fields[field_name]) for field_name in form_fields if
            field_name.startswith('pattern_')]
