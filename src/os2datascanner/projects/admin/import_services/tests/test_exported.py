from datetime import timedelta
from parameterized import parameterized

from django.db import connection
from django.test import TestCase
from django.db.utils import DatabaseError
from django.utils.timezone import now

from ..models import Exported


class DummyExportedModel(Exported):
    class Meta:
        managed = False
        db_table = 'dummy_table'


NOW = now()
ONE_DAY = timedelta(days=1)


class ExportedTest(TestCase):

    def setUp(self) -> None:
        super().setUp()
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(DummyExportedModel)

            table_name = DummyExportedModel._meta.db_table
            if table_name not in connection.introspection.table_names():
                msg = "Table '{table_name}' is missing in test database"
                raise DatabaseError(msg.format(table_name=table_name))

        self.test_model = DummyExportedModel

    def tearDown(self) -> None:
        super().tearDown()
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(DummyExportedModel)

    def test_model_is_valid(self):
        instance = self.test_model.objects.create(
            last_modified=NOW,
        )
        self.assertIsInstance(instance, Exported)
        self.assertEqual(self.test_model.objects.count(), 1)

    @parameterized.expand([
        ("Empty queryset", [], 0),
        ("No successful export", [None], 1),
        ("Exported before modified", [NOW - ONE_DAY], 1),
        ("Exported same as modified", [NOW], 1),
        ("Exported after modified", [NOW + ONE_DAY], 0),
        ("All four cases", [None, NOW - ONE_DAY, NOW, NOW + ONE_DAY], 3),
    ])
    def test_get_all_awaiting(self, _, exported_date_list, expected_count):
        for exported in exported_date_list:
            self.test_model.objects.create(
                last_modified=NOW,
                last_exported=exported,
            )
        count = self.test_model.get_all_awaiting().count()
        self.assertEqual(count, expected_count)

    @parameterized.expand([
        ("No deleted time", [None], 0),
        ("Deleted in the future", [NOW+ONE_DAY], 0),
        ("Deleted in the past", [NOW-ONE_DAY], 1),
        ("All three cases", [None, NOW+ONE_DAY, NOW-ONE_DAY], 1),
    ])
    def test_get_all_deleted(self, _, deleted_date_list, expected_count):
        for deleted in deleted_date_list:
            self.test_model.objects.create(
                last_modified=NOW,
                deleted_at=deleted,
            )
        count = self.test_model.get_all_deleted().count()
        self.assertEqual(count, expected_count)
