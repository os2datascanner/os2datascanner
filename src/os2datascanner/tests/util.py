"""Unit-test util for tests os2webscanner.tests"""
# flake8: noqa pydocstyle:noqa
from os2datascanner.projects.admin.adminapp.models.organization_model import Organization


class CreateOrganization(object):

    def create_organization(self):
        return Organization.objects.create(
            name='Magenta',
            contact_email='info@magenta.dk',
            contact_phone='39393939'
        )
