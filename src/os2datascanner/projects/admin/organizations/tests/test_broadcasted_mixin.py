from django.db import connection
from django.db.models import Model, BooleanField
from django.db.utils import DatabaseError
from django.test import TestCase

from ..models.broadcasted_mixin import Broadcasted


class DummyBroadcastedModel(Broadcasted, Model):
    test_field = BooleanField(
        default=False
    )

    class Meta:
        managed = False
        db_table = 'dummy_table'


class BroadcastedTest(TestCase):

    def setUp(self) -> None:
        super().setUp()
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(DummyBroadcastedModel)

            table_name = DummyBroadcastedModel._meta.db_table
            if table_name not in connection.introspection.table_names():
                msg = "Table '{table_name}' is missing in test database"
                raise DatabaseError(msg.format(table_name=table_name))

    def tearDown(self) -> None:
        super().tearDown()
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(DummyBroadcastedModel)

    # used to test signal error output
    def testBroadcastingCreate(self):
        self.assertEqual(DummyBroadcastedModel.objects.count(), 0)
        DummyBroadcastedModel.objects.create()
        self.assertEqual(DummyBroadcastedModel.objects.count(), 1)
