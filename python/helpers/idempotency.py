from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class IdempotencyInput:
    root_session_id: str
    invocation_id: str
    operation_fingerprint: dict[str, Any]
    payload: Any


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def payload_digest(payload: Any) -> str:
    """Return deterministic SHA256 digest for arbitrary JSON-serializable payload."""
    return hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest()


def derive_idempotency_key(request: IdempotencyInput) -> str:
    """Derive a deterministic key for dedupe of mutating/external operations.

    Format:
      idem:v1:<sha256(root_session_id + invocation_id + operation_fingerprint + payload_digest)>
    """
    joined = "|".join(
        [
            request.root_session_id,
            request.invocation_id,
            _stable_json(request.operation_fingerprint),
            payload_digest(request.payload),
        ]
    )
    return f"idem:v1:{hashlib.sha256(joined.encode('utf-8')).hexdigest()}"


def ttl_seconds_for_risk_tier(risk_tier: str) -> int:
    """Suggested TTL for idempotency records by tier."""
    normalized = (risk_tier or "").upper()
    if normalized == "T2":
        return 24 * 60 * 60
    if normalized == "T3":
        return 72 * 60 * 60
    return 15 * 60
