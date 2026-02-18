from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from python.helpers.p2_flags import P2Flags


_MUTATING_TOOLS = {
    "browser",
    "browser_agent",
    "code_execution_tool",
    "openclaw_tool",
    "memory_save",
    "memory_delete",
    "memory_forget",
    "behaviour_adjustment",
    "call_subordinate",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class PolicyGateDecision:
    schema: str
    event_type: str
    run_id: str
    root_session_id: str
    invocation_id: str
    gate_name: str
    decision: str
    reason_code: str
    policy_version: str
    risk_tier: str
    timestamp: str
    action: dict[str, Any]
    meta: dict[str, Any]

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "event_type": self.event_type,
            "run_id": self.run_id,
            "root_session_id": self.root_session_id,
            "invocation_id": self.invocation_id,
            "gate_name": self.gate_name,
            "decision": self.decision,
            "reason_code": self.reason_code,
            "policy_version": self.policy_version,
            "risk_tier": self.risk_tier,
            "timestamp": self.timestamp,
            "action": self.action,
            "meta": self.meta,
        }


def is_mutating_tool(tool_name: str, tool_args: dict[str, Any] | None = None) -> bool:
    name = (tool_name or "").strip().lower()
    if name in _MUTATING_TOOLS:
        return True

    args = tool_args or {}
    # lightweight heuristic for URL/navigation and file writes
    if name.startswith("browser_"):
        return True
    if any(k in args for k in ("path", "file", "file_path", "url", "target")) and name not in {
        "knowledge_tool",
        "webpage_content_tool",
        "memory_load",
        "input",
        "response",
    }:
        return True
    return False


def infer_risk_tier(tool_name: str, tool_args: dict[str, Any] | None = None) -> str:
    name = (tool_name or "").strip().lower()
    if name in {"openclaw_tool", "code_execution_tool", "browser_agent", "call_subordinate"}:
        return "T3"
    if is_mutating_tool(name, tool_args):
        return "T2"
    if name in {"knowledge_tool", "webpage_content_tool", "memory_load", "input", "response"}:
        return "T0"
    return "T1"


def evaluate_execution_gate(
    *,
    flags: P2Flags,
    tool_name: str,
    tool_args: dict[str, Any],
    run_id: str,
    root_session_id: str,
    invocation_id: str,
) -> PolicyGateDecision:
    risk_tier = infer_risk_tier(tool_name, tool_args)
    action = {
        "tool": tool_name,
        "operation": "execute",
        "target": tool_args.get("target") or tool_args.get("url") or tool_args.get("path"),
    }

    decision = "allow"
    reason_code = "policy_disabled"
    meta: dict[str, Any] = {
        "mode": flags.policy_gates_mode,
        "shadow_emit_only": flags.p2_shadow_emit_only,
    }

    if flags.policy_gates_v1 and flags.policy_gates_mode == "shadow":
        decision = "allow"
        reason_code = "shadow_allow"
        meta["would_decision"] = "challenge" if risk_tier in {"T2", "T3"} else "allow"

    elif flags.policy_gates_v1 and flags.policy_gates_mode == "enforce":
        if flags.p2_shadow_emit_only:
            decision = "allow"
            reason_code = "enforce_shadow_emit_only"
            meta["would_decision"] = "challenge" if risk_tier in {"T2", "T3"} else "allow"
        else:
            if risk_tier == "T3":
                decision = "challenge"
                reason_code = "high_risk_challenge"
            else:
                decision = "allow"
                reason_code = "enforce_allow"

    return PolicyGateDecision(
        schema="policy-gate-decision/v0",
        event_type="policy.gate.evaluated",
        run_id=run_id,
        root_session_id=root_session_id,
        invocation_id=invocation_id,
        gate_name="execution",
        decision=decision,
        reason_code=reason_code,
        policy_version="p2-min-slice-v1",
        risk_tier=risk_tier,
        timestamp=_utc_now_iso(),
        action=action,
        meta=meta,
    )
