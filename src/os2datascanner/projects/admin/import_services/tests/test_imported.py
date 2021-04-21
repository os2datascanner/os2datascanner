from datetime import timedelta
from parameterized import parameterized

from django.db import connection
from django.test import TestCase
from django.db.utils import DatabaseError
from django.utils.timezone import now

from ..models import Imported


class DummyImportedModel(Imported):
    class Meta:
        managed = False
        db_table = 'dummy_table'


NOW = now()
ONE_DAY = timedelta(days=1)


class ExportedTest(TestCase):

    def setUp(self) -> None:
        super().setUp()
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(DummyImportedModel)

            table_name = DummyImportedModel._meta.db_table
            if table_name not in connection.introspection.table_names():
                msg = "Table '{table_name}' is missing in test database"
                raise DatabaseError(msg.format(table_name=table_name))

        self.test_model = DummyImportedModel

    def tearDown(self) -> None:
        super().tearDown()
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(DummyImportedModel)

    def get_awaiting_cases():
        no_req_no_imp = (None, None)
        no_req = (None, NOW)
        req_no_imp = (NOW, None)
        req_before_imp = (NOW-ONE_DAY, NOW)
        req_same_as_imp = (NOW, NOW)
        req_after_imp = (NOW, NOW-ONE_DAY)
        future_req_no_imp = (NOW+ONE_DAY, None)
        future_req_before_imp = (NOW+ONE_DAY, NOW+timedelta(days=2))
        future_req_same_as_imp = (NOW+ONE_DAY, NOW+ONE_DAY)
        future_req_after_imp = (NOW+ONE_DAY, NOW)
        cases = [
            ("Empty queryset", [], 0),
            ("No request and no import", [no_req_no_imp], 0),
            ("No request", [no_req], 0),
            ("Request but no import", [req_no_imp], 1),
            ("Request before import", [req_before_imp], 0),
            ("Request same as import", [req_same_as_imp], 1),
            ("Request after import", [req_after_imp], 1),
            ("Future request but no import", [future_req_no_imp], 0),
            ("Future request before import", [future_req_before_imp], 0),
            ("Future request same as import", [future_req_same_as_imp], 0),
            ("Future request after import", [future_req_after_imp], 0),
            ("All without request", [no_req, no_req_no_imp], 0),
            (
                "All with non-future request",
                [req_no_imp, req_before_imp, req_same_as_imp, req_after_imp],
                3
            ),
            (
                "All with future request",
                [future_req_no_imp, future_req_before_imp,
                 future_req_same_as_imp, future_req_after_imp],
                0
            )
        ]
        return cases

    @parameterized.expand(get_awaiting_cases)
    def test_get_all_awaiting(self, _, imported_date_list, expected_count):
        for requested, imported in imported_date_list:
            self.test_model.objects.create(
                last_import_requested=requested,
                last_import=imported,
            )
        count = self.test_model.get_all_awaiting().count()
        self.assertEqual(count, expected_count)
