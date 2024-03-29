# -*- coding: utf-8 -*-
# encoding: utf-8
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
# OS2Webscanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (http://www.os2web.dk/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( http://www.os2web.dk/ )


from os2datascanner.engine2.rules.experimental.health_rule import TurboHealthRule as HealthTwule
from .rule import Rule


class TurboHealthRule(Rule):
    """
    Django model representation of engine2s TurboHealthRule,
    which is designed to search for health terms.
    """

    def make_engine2_rule(self):
        return HealthTwule(
                name=self.name,
                sensitivity=self.make_engine2_sensitivity())
