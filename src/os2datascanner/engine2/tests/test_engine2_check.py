import unittest

from os2datascanner.engine2.model.core import SourceManager
from os2datascanner.engine2.rules.cpr import CPRRule

from . import model as model
from ..pipeline import worker, messages


class CheckTests(unittest.TestCase):
    def test_subobject_omission(self):
        """The Resource.check method should not be called for nested
        sub-objects."""

        dummy = model.DummySource(20, secret="do not tell the spies!")
        dummy_handle = model.DummyHandle(dummy, 9)

        msg = messages.ConversionMessage(
                scan_spec=messages.ScanSpecMessage(
                    scan_tag=messages.ScanTagFragment.make_dummy(),
                    source=dummy,
                    rule=CPRRule(),
                    configuration={},
                    progress=None),
                handle=dummy_handle,
                progress=messages.ProgressFragment(
                        rule=CPRRule(),
                        matches=[]))

        # Simulate pipeline execution of this object
        sm = SourceManager()
        for _ in worker.message_received_raw(
                msg.to_json_object(), "os2ds_conversions", sm):
            pass

        self.assertEqual(
                sm.open(msg.scan_spec.source),
                {dummy_handle: 1},
                "Resource.check() called too frequently")
