import unittest

from python.helpers.p2_flags import P2Flags
from python.helpers.policy_gates import (
    evaluate_execution_gate,
    infer_risk_tier,
    is_mutating_tool,
)


class PolicyGatesTests(unittest.TestCase):
    def test_mutating_tool_detection(self):
        self.assertTrue(is_mutating_tool("openclaw_tool", {"command": "message send"}))
        self.assertTrue(is_mutating_tool("browser", {"url": "https://example.com"}))
        self.assertFalse(is_mutating_tool("response", {"text": "ok"}))

    def test_risk_tier_inference(self):
        self.assertEqual(infer_risk_tier("openclaw_tool", {}), "T3")
        self.assertEqual(infer_risk_tier("memory_save", {"fact": "x"}), "T2")
        self.assertEqual(infer_risk_tier("response", {"text": "ok"}), "T0")

    def test_shadow_mode_emits_would_decision(self):
        flags = P2Flags(
            policy_gates_v1=True,
            policy_gates_mode="shadow",
            idempotency_v1=False,
            retry_orchestrator_v1=False,
            p2_shadow_emit_only=True,
        )
        decision = evaluate_execution_gate(
            flags=flags,
            tool_name="openclaw_tool",
            tool_args={"command": "message send --target x --message y"},
            run_id="run-1",
            root_session_id="ctx-1",
            invocation_id="run-1:1",
        )
        self.assertEqual(decision.decision, "allow")
        self.assertEqual(decision.reason_code, "shadow_allow")
        self.assertEqual(decision.meta.get("would_decision"), "challenge")

    def test_enforce_shadow_emit_only_keeps_allow(self):
        flags = P2Flags(
            policy_gates_v1=True,
            policy_gates_mode="enforce",
            idempotency_v1=False,
            retry_orchestrator_v1=False,
            p2_shadow_emit_only=True,
        )
        decision = evaluate_execution_gate(
            flags=flags,
            tool_name="openclaw_tool",
            tool_args={"command": "message send --target x --message y"},
            run_id="run-1",
            root_session_id="ctx-1",
            invocation_id="run-1:1",
        )
        self.assertEqual(decision.decision, "allow")
        self.assertEqual(decision.reason_code, "enforce_shadow_emit_only")


if __name__ == "__main__":
    unittest.main()
