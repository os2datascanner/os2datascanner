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

from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.managers import InheritanceManager

from ..sensitivity_level import Sensitivity

from os2datascanner.engine2.rules.rule import Rule as Twule
from os2datascanner.engine2.rules.rule import Sensitivity as Twensitivity


_sensitivity_mapping = {
    Sensitivity.OK: Twensitivity.NOTICE,
    Sensitivity.LOW: Twensitivity.WARNING,
    Sensitivity.HIGH: Twensitivity.PROBLEM,
    Sensitivity.CRITICAL: Twensitivity.CRITICAL
}


class Rule(models.Model):
    objects = InheritanceManager()

    name = models.CharField(
        max_length=256,
        unique=True,
        null=False,
        verbose_name=_('name'),
    )

    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='rule',
        verbose_name=_('organization'),
        default=None,
        null=True,
    )

    description = models.TextField(
        verbose_name=_('description')
    )

    sensitivity = models.IntegerField(
        choices=Sensitivity.choices,
        default=Sensitivity.HIGH,
        verbose_name=_('sensitivity'),
    )

    @property
    def display_name(self):
        """The name used when displaying the regexrule on the web page."""
        return "Regel '%s'" % self.name

    def get_absolute_url(self):
        """Get the absolute URL for rules."""
        return '/rules/'

    def __str__(self):
        """Return the name of the rule."""
        return self.name

    def make_engine2_rule(self) -> Twule:
        """Construct an engine2 Rule corresponding to this Rule."""
        # (this can't use the @abstractmethod decorator because of metaclass
        # conflicts with Django, but subclasses should override this method!)
        raise NotImplementedError("Rule.make_engine2_rule")

    def make_engine2_sensitivity(self) -> Twensitivity:
        return _sensitivity_mapping[self.sensitivity]
