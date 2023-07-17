import unittest

from os2datascanner.engine2.model.core import SourceManager
from os2datascanner.engine2.rules.cpr import CPRRule

from . import model as model
from ..pipeline import worker, messages, processor


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
                        filter_rule=None,
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

    def test_pipeline_check_handling(self):
        self.maxDiff = None

        dummy = model.DummySource(0, secret=None)

        dummy_scan_spec = messages.ScanSpecMessage(
                scan_tag=messages.ScanTagFragment.make_dummy(),
                source=dummy,
                rule=CPRRule(),
                configuration={},
                filter_rule=None,
                progress=None)

        template = messages.ConversionMessage(
                scan_spec=dummy_scan_spec,
                handle=None,
                progress=messages.ProgressFragment(
                        rule=dummy_scan_spec.rule, matches=[]))

        with SourceManager() as sm:
            with self.subTest(
                    "Extant objects are processed"):
                message = template._deep_replace(
                        handle=model.DummyHandle(
                                dummy, 0, hints={"exists": True}))
                replies = list(
                        processor.message_received_raw(
                                message.to_json_object(),
                                "os2ds_conversions", sm))
                self.assertCountEqual(
                        replies,
                        processor.message_received_raw(
                                message.to_json_object(),
                                "os2ds_conversions", sm),
                        "got unexpected messages")

            with self.subTest(
                    "Deleted files are not processed"):
                message = template._deep_replace(
                        handle=model.DummyHandle(
                                dummy, 0, hints={"exists": False}))
                match list(
                        processor.message_received_raw(
                                message.to_json_object(),
                                "os2ds_conversions", sm)):
                    case [("os2ds_problems", {"missing": True}), *_]:
                        pass
                    case k:
                        self.fail(
                                'expected an "os2ds_problems" message with'
                                ' {"missing": True}, but got' f" {k}")

            with self.subTest(
                    "Transiently unavailable files are not treated"
                    " as though they had been deleted"):
                message = template._deep_replace(
                        handle=model.DummyHandle(
                                dummy, 0, hints={"exists": None}))
                match list(
                        processor.message_received_raw(
                                message.to_json_object(),
                                "os2ds_conversions", sm)):
                    case [("os2ds_problems", {"missing": False}), *_]:
                        pass
                    case k:
                        self.fail(
                                'expected an "os2ds_problems" message with'
                                ' {"missing": False}, but got' f" {k}")
