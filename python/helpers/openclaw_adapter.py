from __future__ import annotations

import json

try:
    from python.helpers import extract_tools
except Exception:  # pragma: no cover - optional dependency fallback for lightweight validation
    extract_tools = None


def _json_parse_best_effort(message: str):
    if extract_tools is not None:
        return extract_tools.json_parse_dirty(message)
    try:
        return json.loads(message)
    except Exception:
        return None


def classify_model_output_shape(message: str) -> str:
    """Classify model output shape for adapter hardening decisions.

    Returns one of:
      - empty
      - plain_response
      - json_like
      - malformed_json_like
    """
    msg = normalize_model_output(message)
    if not msg:
        return "empty"

    has_open = "{" in msg
    has_close = "}" in msg
    if has_open and has_close:
        parsed = _json_parse_best_effort(msg)
        return "json_like" if parsed is not None else "malformed_json_like"

    if has_open or has_close:
        return "malformed_json_like"

    return "plain_response"


def normalize_model_output(message: str) -> str:
    """Normalize model output to improve extraction reliability.

    Handles common OpenAI-compatible output styles (e.g. fenced JSON).
    """
    msg = (message or "").strip()
    if msg.startswith("```") and msg.endswith("```"):
        lines = msg.splitlines()
        if len(lines) >= 3:
            # Remove opening and closing fences
            msg = "\n".join(lines[1:-1]).strip()
    return msg


def extract_tool_request(message: str):
    """Best-effort tool JSON extraction from model output."""
    return _json_parse_best_effort(normalize_model_output(message))


def should_fallback_plain_response(message: str) -> bool:
    """Return True if the assistant message should be treated as final plain response.

    We only fallback for plain text responses. JSON-like or malformed JSON-like outputs stay
    on strict tool-call flow so warning/repair logic can trigger.
    """
    return classify_model_output_shape(message) == "plain_response"
