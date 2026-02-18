from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class P2Flags:
    policy_gates_v1: bool
    policy_gates_mode: str
    idempotency_v1: bool
    retry_orchestrator_v1: bool
    p2_shadow_emit_only: bool


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def load_p2_flags() -> P2Flags:
    """Load additive P2 feature flags with safe defaults (all off)."""
    mode = (os.getenv("POLICY_GATES_MODE", "off").strip().lower())
    if mode not in {"off", "shadow", "enforce"}:
        mode = "off"
    return P2Flags(
        policy_gates_v1=_env_bool("POLICY_GATES_V1", default=False),
        policy_gates_mode=mode,
        idempotency_v1=_env_bool("IDEMPOTENCY_V1", default=False),
        retry_orchestrator_v1=_env_bool("RETRY_ORCHESTRATOR_V1", default=False),
        p2_shadow_emit_only=_env_bool("P2_SHADOW_EMIT_ONLY", default=True),
    )
