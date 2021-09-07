from typing import List
from ..conversions.types import OutputType
from .rule import Rule, SimpleRule, Sensitivity
from .. import settings as engine2_settings

import requests
from requests.exceptions import RequestException
TIMEOUT = engine2_settings.model["http"]["timeout"]

class LinksFollowRule(SimpleRule):
    """Rule to find links on a webpage that does not resolve or respond"""

    operates_on = OutputType.Links
    type_label = "links"

    @property
    def presentation_raw(self):
        return "Check if links resolve"

    def match(self, content: List[str]):
        """Yield a mach if a link could not be followed"""
        if content is None:
            return

        for link in content:
            if not check(link):
                yield {
                    "match": link,
                    "context": "unable to follow links",
                    "sensitivity": (
                        self.sensitivity.value
                        if self.sensitivity
                        else self.sensitivity
                    ),
                }

    def to_json_object(self):
        return dict(**super().to_json_object())

    @staticmethod
    @Rule.json_handler(type_label)
    def from_json_object(obj):
        return LinksFollowRule(
                sensitivity=Sensitivity.make_from_dict(obj),
                name=obj["name"] if "name" in obj else None)


def check(link: str) -> bool:
    """return True if link can be followed

    Redirects are allowed and only the headers are retrieved
    """
    try:
        r =requests.head(link, allow_redirects=True, timeout=TIMEOUT)
        r.raise_for_status()
        return True
        # return response.status_code not in (404, 410,)
    except RequestException as e:
        return False
