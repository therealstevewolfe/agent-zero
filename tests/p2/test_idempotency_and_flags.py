import os
import unittest

from python.helpers.idempotency import (
    IdempotencyInput,
    derive_idempotency_key,
    payload_digest,
    ttl_seconds_for_risk_tier,
)
from python.helpers.p2_flags import load_p2_flags


class IdempotencyUtilityTests(unittest.TestCase):
    def test_payload_digest_stable(self):
        left = {"b": 2, "a": 1}
        right = {"a": 1, "b": 2}
        self.assertEqual(payload_digest(left), payload_digest(right))

    def test_idempotency_key_deterministic(self):
        request = IdempotencyInput(
            root_session_id="root-1",
            invocation_id="inv-1",
            operation_fingerprint={"tool": "message.send", "target": "chat-42", "action": "send"},
            payload={"text": "hello"},
        )
        self.assertEqual(derive_idempotency_key(request), derive_idempotency_key(request))

    def test_idempotency_key_changes_with_payload(self):
        common = dict(
            root_session_id="root-1",
            invocation_id="inv-1",
            operation_fingerprint={"tool": "message.send", "target": "chat-42", "action": "send"},
        )
        k1 = derive_idempotency_key(IdempotencyInput(**common, payload={"text": "hello"}))
        k2 = derive_idempotency_key(IdempotencyInput(**common, payload={"text": "hello again"}))
        self.assertNotEqual(k1, k2)

    def test_ttl_by_risk_tier(self):
        self.assertEqual(ttl_seconds_for_risk_tier("T0"), 900)
        self.assertEqual(ttl_seconds_for_risk_tier("T1"), 900)
        self.assertEqual(ttl_seconds_for_risk_tier("T2"), 86400)
        self.assertEqual(ttl_seconds_for_risk_tier("T3"), 259200)


class P2FlagsTests(unittest.TestCase):
    def test_defaults_safe_and_off(self):
        for key in [
            "POLICY_GATES_V1",
            "POLICY_GATES_MODE",
            "IDEMPOTENCY_V1",
            "RETRY_ORCHESTRATOR_V1",
            "P2_SHADOW_EMIT_ONLY",
        ]:
            os.environ.pop(key, None)

        flags = load_p2_flags()
        self.assertFalse(flags.policy_gates_v1)
        self.assertEqual(flags.policy_gates_mode, "off")
        self.assertFalse(flags.idempotency_v1)
        self.assertFalse(flags.retry_orchestrator_v1)
        self.assertTrue(flags.p2_shadow_emit_only)

    def test_reads_env_overrides(self):
        os.environ["POLICY_GATES_V1"] = "true"
        os.environ["POLICY_GATES_MODE"] = "enforce"
        os.environ["IDEMPOTENCY_V1"] = "1"
        os.environ["RETRY_ORCHESTRATOR_V1"] = "yes"
        os.environ["P2_SHADOW_EMIT_ONLY"] = "false"

        flags = load_p2_flags()
        self.assertTrue(flags.policy_gates_v1)
        self.assertEqual(flags.policy_gates_mode, "enforce")
        self.assertTrue(flags.idempotency_v1)
        self.assertTrue(flags.retry_orchestrator_v1)
        self.assertFalse(flags.p2_shadow_emit_only)


if __name__ == "__main__":
    unittest.main()
