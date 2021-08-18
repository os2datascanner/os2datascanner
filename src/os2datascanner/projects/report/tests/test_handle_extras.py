from django.test import TestCase
from parameterized import parameterized

from ..reportapp.templatetags.handle_extras import find_svg_icon


class HandleExtraTest(TestCase):

    @parameterized.expand([
        ('web', 'web', "components/svg-icons/icon-web.svg"),
        ('smbc', 'smbc', "components/svg-icons/icon-smbc.svg"),
        ('msgraph-mail', 'msgraph-mail', "components/svg-icons/icon-msgraph-mail.svg"),
        ('googledrive', 'googledrive', "components/svg-icons/icon-googledrive.svg"),
        ('gmail', 'gmail', "components/svg-icons/icon-gmail.svg"),
        ('dropbox', 'dropbox', "components/svg-icons/icon-dropbox.svg"),
        ('sbsys', 'sbsys', "components/svg-icons/icon-default.svg"),
        ('ews', 'ews', "components/svg-icons/icon-ews.svg"),
    ])
    def test_find_svg_icon(self, _, type_label, expected):
        self.assertEqual(find_svg_icon(type_label=type_label), expected)
