import json

from django.test import RequestFactory, TestCase
from django.contrib.auth.models import User

from ..reportapp.models.documentreport_model import DocumentReport
from ..reportapp.models.aliases.emailalias_model import EmailAlias
from ..reportapp.models.roles.remediator_model import Remediator
from ..reportapp.views.views import MainPageView

scan_time = "2020-11-11T11:11:59+02:00"
path = '4b012c5e20a6770cb0713b540f71af281eeb6f0c0b776267cc48294f13cf7cdbcf2b1642fd11da687c7c49fc11f3394eea59dcaec739072929e53dac8a16b76d'
data = '{"matches": {"handle": {"mime": "text/html", "path": "1/", "type": "mail-part", "source": {"type": "mail", "handle": {"path": "LKSDLDSJFOEWIROEWYSMBD", "type": "ews", "source": {"type": "ews", "user": "kjeld", "domain": "jensen.com", "server": "", "admin_user": null, "admin_password": null}, "folder_name": "Inbox", "mail_subject": "Sv: GDPR f\u00f8lsom data"}}}, "origin": "os2ds_matches", "matched": true, "matches": [{"rule": {"name": null, "type": "conversion", "target": "image-dimensions", "sensitivity": null}, "matches": null}, {"rule": {"name": null, "type": "conversion", "target": "image-dimensions", "sensitivity": null}, "matches": null}, {"rule": {"name": null, "type": "cpr", "modulus_11": true, "sensitivity": 750, "ignore_irrelevant": true}, "matches": [{"match": "1111XXXXXX", "offset": 1133, "context": "elle cpr nummer man m\u00e5 bruge som test cpr nummer: XXXXXX-XXXX Du m\u00e5 meget gerne svare p\u00e5 denne mail med noget a", "probability": 1.0, "sensitivity": 750, "context_offset": 0}]}], "scan_spec": {"rule": {"name": null, "type": "and", "components": [{"name": null, "type": "or", "components": [{"name": null, "type": "and", "components": [{"name": null, "type": "conversion", "target": "image-dimensions", "sensitivity": null}, {"name": null, "type": "dimensions", "width": [32, 16385], "height": [32, 16385], "minimum": 128, "sensitivity": null}], "sensitivity": null}, {"name": null, "rule": {"name": null, "type": "conversion", "target": "image-dimensions", "sensitivity": null}, "type": "not", "sensitivity": null}], "sensitivity": null}, {"name": null, "type": "cpr", "modulus_11": true, "sensitivity": 750, "ignore_irrelevant": true}], "sensitivity": null}, "source": {"type": "mail", "handle": {"path": "LKSDLDSJFOEWIROEWYSMBD", "type": "ews", "source": {"type": "ews", "user": "kjeld", "domain": "jensen.com", "server": "", "admin_user": null, "admin_password": null}, "folder_name": "Inbox", "mail_subject": "Sv: GDPR f\u00f8lsom data"}}, "progress": null, "scan_tag": {"time": "2020-11-11T11:11:59+02:00", "user": "kjeld", "scanner": {"pk": 6, "name": "CPR scan"}, "destination": "pipeline_collector", "organisation": "Olsenbanden ApS"}, "configuration": {}}}, "metadata": {"handle": {"mime": "text/html", "path": "1/", "type": "mail-part", "source": {"type": "mail", "handle": {"path": "LKSDLDSJFOEWIROEWYSMBD", "type": "ews", "source": {"type": "ews", "user": "kjeld", "domain": "jensen.com", "server": "", "admin_user": null, "admin_password": null}, "folder_name": "Inbox", "mail_subject": "Sv: GDPR f\u00f8lsom data"}}}, "origin": "os2ds_metadata", "metadata": {"email-account": "kjeld@jensen.com"}, "scan_tag": {"time": "2020-11-11T11:11:59+02:00", "user": "kjeld", "scanner": {"pk": 6, "name": "CPR scan"}, "destination": "pipeline_collector", "organisation": "Olsenbanden ApS"}}, "scan_tag": {"time": "2020-11-11T11:11:59+02:00", "user": "kjeld", "scanner": {"pk": 6, "name": "CPR scan"}, "destination": "pipeline_collector", "organisation": "Olsenbanden ApS"}}'
path2 = 'ef57aa18e938ca9b11ff41408a29c9f110dd9efe4e8dd17b42ff98d7e8d6e68183880a85a4a9a0238bcd938058c742b28c0dab85e082cba96b78b5edcf80d69d'
data2 = '{"matches": {"handle": {"mime": "text/html", "path": "1/", "type": "mail-part", "source": {"type": "mail", "handle": {"path": "TDJHGFIHDIJHSKJGHKFUGIUHIUEHIIHE", "type": "ews", "source": {"type": "ews", "user": "egon", "domain": "olsen.com", "server": "", "admin_user": null, "admin_password": null}, "folder_name": "Indbakke", "mail_subject": "GDPR f\u00f8lsom data"}}}, "origin": "os2ds_matches", "matched": true, "matches": [{"rule": {"name": null, "type": "conversion", "target": "image-dimensions", "sensitivity": null}, "matches": null}, {"rule": {"name": null, "type": "conversion", "target": "image-dimensions", "sensitivity": null}, "matches": null}, {"rule": {"name": null, "type": "cpr", "modulus_11": true, "sensitivity": 750, "ignore_irrelevant": true}, "matches": [{"match": "1111XXXXXX", "offset": 248, "context": "elle cpr nummer man m\u00e5 bruge som test cpr nummer: XXXXXX-XXXX Du m\u00e5 meget gerne svare p\u00e5 denne mail med noget a", "probability": 1.0, "sensitivity": 750, "context_offset": 0}]}], "scan_spec": {"rule": {"name": null, "type": "and", "components": [{"name": null, "type": "or", "components": [{"name": null, "type": "and", "components": [{"name": null, "type": "conversion", "target": "image-dimensions", "sensitivity": null}, {"name": null, "type": "dimensions", "width": [32, 16385], "height": [32, 16385], "minimum": 128, "sensitivity": null}], "sensitivity": null}, {"name": null, "rule": {"name": null, "type": "conversion", "target": "image-dimensions", "sensitivity": null}, "type": "not", "sensitivity": null}], "sensitivity": null}, {"name": null, "type": "cpr", "modulus_11": true, "sensitivity": 750, "ignore_irrelevant": true}], "sensitivity": null}, "source": {"type": "mail", "handle": {"path": "TDJHGFIHDIJHSKJGHKFUGIUHIUEHIIHE", "type": "ews", "source": {"type": "ews", "user": "egon", "domain": "olsen.com", "server": "", "admin_user": null, "admin_password": null}, "folder_name": "Indbakke", "mail_subject": "GDPR f\u00f8lsom data"}}, "progress": null, "scan_tag": {"time": "2020-11-11T11:11:59+02:00", "user": "egon", "scanner": {"pk": 6, "name": "CPR scan"}, "destination": "pipeline_collector", "organisation": "Olsenbanden ApS"}, "configuration": {}}}, "metadata": {"handle": {"mime": "text/html", "path": "1/", "type": "mail-part", "source": {"type": "mail", "handle": {"path": "TDJHGFIHDIJHSKJGHKFUGIUHIUEHIIHE", "type": "ews", "source": {"type": "ews", "user": "egon", "domain": "olsen.com", "server": "", "admin_user": null, "admin_password": null}, "folder_name": "Indbakke", "mail_subject": "GDPR f\u00f8lsom data"}}}, "origin": "os2ds_metadata", "metadata": {"email-account": "egon@olsen.com"}, "scan_tag": {"time": "2020-11-11T11:11:59+02:00", "user": "egon", "scanner": {"pk": 6, "name": "CPR scan"}, "destination": "pipeline_collector", "organisation": "Olsenbanden ApS"}}, "scan_tag": {"time": "2020-11-11T11:11:59+02:00", "user": "egon", "scanner": {"pk": 6, "name": "CPR scan"}, "destination": "pipeline_collector", "organisation": "Olsenbanden ApS"}}'


class MainPageViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        number_of_kjeld_matches = 7
        cls.generate_matches(number_of_kjeld_matches, path, data)
        number_of_egon_matches = 5
        cls.generate_matches(number_of_egon_matches, path2, data2)

    @classmethod
    def generate_matches(cls, number_of_matches, path, data):
        for number in range(number_of_matches):
            DocumentReport.objects.create(scan_time=scan_time,
                                          path=path,
                                          data=json.loads(data),
                                          resolution_status=None)

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='kjeld', email='kjeld@jensen.com', password='top_secret')

    def test_mainpage_view_as_default_role_with_no_matches(self):
        qs = self.mainpage_get_queryset()
        self.assertEqual(len(qs), 0)

    def test_mainpage_view_as_remediator_role_with_matches(self):
        remediator = Remediator.objects.create(user=self.user)
        qs = self.mainpage_get_queryset()
        self.assertEqual(len(qs), 12)
        remediator.delete()

    def test_mainpage_view_with_emailalias_with_matches(self):
        emailalias = EmailAlias.objects.create(user=self.user, address='kjeld@jensen.com')
        qs = self.mainpage_get_queryset()
        self.assertEqual(len(qs), 7)
        emailalias.delete()

    def test_mainpage_view_with_two_emailaliases_with_matches(self):
        emailalias = EmailAlias.objects.create(user=self.user, address='kjeld@jensen.com')
        emailalias1 = EmailAlias.objects.create(user=self.user, address='egon@olsen.com')
        qs = self.mainpage_get_queryset()
        self.assertEqual(len(qs), 12)
        emailalias.delete()
        emailalias1.delete()

    def mainpage_get_queryset(self):
        request = self.factory.get('/')
        request.user = self.user
        view = MainPageView()
        view.setup(request)
        qs = view.get_queryset()
        return qs
