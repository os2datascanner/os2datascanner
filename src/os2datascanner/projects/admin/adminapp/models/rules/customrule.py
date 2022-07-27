# -*- coding: UTF-8 -*-
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

from django.db import models

from os2datascanner.engine2.rules.rule import Rule as E2Rule
from .rule import Rule


class CustomRule(Rule):
    """CustomRule is an escape hatch that allows for the JSON representation of
    an arbitrary engine2 rule to be stored in the administration system's
    database."""
    _rule = models.JSONField()

    @property
    def rule(self):
        return E2Rule.from_json_object(self._rule)

    @rule.setter
    def set_rule(self, r: E2Rule):
        self._rule = r.to_json_object()

    def make_engine2_rule(self) -> E2Rule:
        return self.rule
