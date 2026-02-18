import json
import os
import tempfile
import unittest

from python.helpers import superframe_events


class SuperframeEventsTests(unittest.TestCase):
    def setUp(self):
        superframe_events.reset_superframe_event_emitter_for_tests()
        self._prev_enabled = os.environ.get("SUPERFRAME_EVENTS_ENABLED")
        self._prev_file = os.environ.get("SUPERFRAME_EVENTS_FILE")

    def tearDown(self):
        if self._prev_enabled is None:
            os.environ.pop("SUPERFRAME_EVENTS_ENABLED", None)
        else:
            os.environ["SUPERFRAME_EVENTS_ENABLED"] = self._prev_enabled

        if self._prev_file is None:
            os.environ.pop("SUPERFRAME_EVENTS_FILE", None)
        else:
            os.environ["SUPERFRAME_EVENTS_FILE"] = self._prev_file

        superframe_events.reset_superframe_event_emitter_for_tests()

    def test_disabled_emitter_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "events.jsonl")
            os.environ["SUPERFRAME_EVENTS_ENABLED"] = "0"
            os.environ["SUPERFRAME_EVENTS_FILE"] = out

            emitter = superframe_events.get_superframe_event_emitter()
            written = emitter.emit("run.started", {"x": 1})

            self.assertFalse(written)
            self.assertFalse(os.path.exists(out))

    def test_enabled_emitter_writes_jsonl_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "events.jsonl")
            os.environ["SUPERFRAME_EVENTS_ENABLED"] = "true"
            os.environ["SUPERFRAME_EVENTS_FILE"] = out

            emitter = superframe_events.get_superframe_event_emitter()
            written = emitter.emit("tool.call.requested", {"tool_name": "response"})

            self.assertTrue(written)
            with open(out, "r", encoding="utf-8") as f:
                line = f.readline().strip()
            record = json.loads(line)
            self.assertEqual(record["event"], "tool.call.requested")
            self.assertEqual(record["payload"]["tool_name"], "response")
            self.assertIn("ts", record)

    def test_emit_failure_is_isolated(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["SUPERFRAME_EVENTS_ENABLED"] = "1"
            os.environ["SUPERFRAME_EVENTS_FILE"] = tmp  # directory path; append should fail

            emitter = superframe_events.get_superframe_event_emitter()
            written = emitter.emit("run.completed", {"status": "succeeded"})

            self.assertFalse(written)


if __name__ == "__main__":
    unittest.main()
