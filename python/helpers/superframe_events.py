import json
import os
import threading
import time
from typing import Any

from python.helpers import files


_TRUTHY = {"1", "true", "yes", "on", "enabled"}


class SuperframeEventEmitter:
    """Best-effort JSONL event writer.

    Failure isolation is intentional: emit() never raises.
    """

    def __init__(self):
        enabled_raw = os.getenv("SUPERFRAME_EVENTS_ENABLED", "")
        self.enabled = enabled_raw.strip().lower() in _TRUTHY
        output_path = os.getenv(
            "SUPERFRAME_EVENTS_FILE", files.get_abs_path("logs", "superframe-events.jsonl")
        )
        self.output_path = output_path
        self._lock = threading.Lock()

    def emit(self, event: str, payload: dict[str, Any] | None = None) -> bool:
        if not self.enabled:
            return False

        record = {
            "ts": time.time(),
            "event": event,
            "payload": payload or {},
        }

        try:
            with self._lock:
                parent = os.path.dirname(self.output_path)
                if parent:
                    os.makedirs(parent, exist_ok=True)
                with open(self.output_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
            return True
        except Exception:
            # Never crash the main flow due to observability plumbing.
            return False


_emitter_singleton: SuperframeEventEmitter | None = None


def get_superframe_event_emitter() -> SuperframeEventEmitter:
    global _emitter_singleton
    if _emitter_singleton is None:
        _emitter_singleton = SuperframeEventEmitter()
    return _emitter_singleton


def reset_superframe_event_emitter_for_tests() -> None:
    global _emitter_singleton
    _emitter_singleton = None
