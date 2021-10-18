from typing import List
from ..conversions.types import Link, OutputType
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

    def match(self, links: List[Link]):
        """Yield a match if a link could not be followed."""
        if links is None:
            return

        for link in links:
            followable, status_code = check(link)
            if not followable:
                context = f"Unable to follow link. Error code: {status_code}."
                if link.link_text is not None:
                    context = f"{context} Text: {link.link_text!r}"
                yield {
                    "match": OutputType.Links.encode_json_object(link),
                    "context": context,
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


# Ideally we would do requests.head(), but not all webservers responds correctly to
# head requests. Instead do a get requests, but ask only for the first byte of the
# page. Not all webservers respect this, but at least we get the correct repsonse
# code
__HEADERS = {"Range": "bytes=0-1"}
<<<<<<< HEAD
def check(link: Link) -> tuple[bool, int]:
=======


def check(link: str) -> bool:
>>>>>>> e58d558c ([#44827] lint python code and add ci job)
    """return True if link can be followed and the final response is less than 400

    Redirects are allowed and only the first byte is downloaded with get-call.

    """

    r = requests.get(link.url, allow_redirects=True, timeout=TIMEOUT, headers=__HEADERS)
    try:
<<<<<<< HEAD
        r.raise_for_status()
        return True, r.status_code
    except RequestException as e:
        return False, r.status_code
=======
        r = requests.get(link, allow_redirects=True, timeout=TIMEOUT, headers=__HEADERS)
        r.raise_for_status()
        return True
    except RequestException:
        return False
>>>>>>> e58d558c ([#44827] lint python code and add ci job)
