from saml2 import saml
from saml2.s_utils import factory
from saml2.metadata import create_metadata_string

from django.conf import settings
from django.http import HttpResponse
from django_saml2_auth import views as dsa_views


def metadata(request):
    client = dsa_views._get_saml_client(
            dsa_views.get_current_domain(request))
    config = client.config
    am = settings.SAML2_AUTH["ATTRIBUTES_MAP"]

    config.load({
        "name": "OS2datascanner for {ni}".format(
                ni=settings.NOTIFICATION_INSTITUTION),
        "service": {
            "sp": {
                # pysaml2 has a lot of complicated infrastructure for mapping
                # attribute types backwards and forwards, but none of them
                # actually do what we want. Substitute in a dummy value to
                # switch this infrastructure off; we'll fix it in post...
                "requested_attribute_name_format": "!placeholder!",
                "optional_attributes": [
                    factory(
                        saml.Attribute,
                        name=am["sid"],
                        friendly_name="sid"
                    ),
                ],
                "required_attributes": [
                    factory(
                        saml.Attribute,
                        name=am["email"],
                        friendly_name="email"
                    ),
                    factory(
                        saml.Attribute,
                        name=am["username"],
                        friendly_name="username"
                    ),
                    factory(
                        saml.Attribute,
                        name=am["first_name"],
                        friendly_name="first_name"
                    ),
                    factory(
                        saml.Attribute,
                        name=am["last_name"],
                        friendly_name="last_name"
                    ),
                ],
            },
        },
        "organization": {
            "name": ["Magenta ApS"],
            "display_name": "Magenta",
            "url": ["https://www.magenta.dk/"],
        },
    })

    mr = create_metadata_string(None, config=client.config)
    return HttpResponse(
            # Get rid of our dummy value
            mr.replace(
                    b"!placeholder!",
                    b"urn:oasis:names:tc:SAML:2.0:attrname-format:uri"),
            content_type="application/xml")
