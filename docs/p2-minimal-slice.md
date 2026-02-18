# P2 Minimal Slice (Scaffold-Only)

Date: 2026-02-18 UTC  
Status: additive and reversible

## Scope delivered
1. Idempotency key utility proposal implemented as helper module + tests.
2. Feature-flag wiring helper added with concrete env flags and safe defaults.
3. Rollback wiring plan documented for staged enablement.

## Files
- `python/helpers/idempotency.py`
- `python/helpers/p2_flags.py`
- `tests/p2/test_idempotency_and_flags.py`
- `example.env` (flag examples)

## Idempotency utility proposal
Implemented deterministic key derivation:
- `derive_idempotency_key(IdempotencyInput)`
- `payload_digest(payload)`
- `ttl_seconds_for_risk_tier(risk_tier)`

Key format:
- `idem:v1:<sha256(...)>`

This module is not yet wired into runtime tool execution; it is a safe drop-in scaffold for broker integration.

## Feature flags (concrete)
- `POLICY_GATES_V1` (`false` default)
- `POLICY_GATES_MODE` (`off|shadow|enforce`, default `off`)
- `IDEMPOTENCY_V1` (`false` default)
- `RETRY_ORCHESTRATOR_V1` (`false` default)
- `P2_SHADOW_EMIT_ONLY` (`true` default)

## Rollback / rollout wiring plan
1. **Shadow-only start**
   - `POLICY_GATES_V1=true`
   - `POLICY_GATES_MODE=shadow`
   - `P2_SHADOW_EMIT_ONLY=true`
   - Keep `IDEMPOTENCY_V1=false`, `RETRY_ORCHESTRATOR_V1=false`
2. **Enable dedupe before retries**
   - `IDEMPOTENCY_V1=true`
   - observe dedupe-hit metrics and absence of duplicate side effects
3. **Enable retries last**
   - `RETRY_ORCHESTRATOR_V1=true`
   - watch retry amplification / external error rate
4. **Rollback order**
   - Disable retries first: `RETRY_ORCHESTRATOR_V1=false`
   - Keep idempotency on if safe: `IDEMPOTENCY_V1=true`
   - Set policy to shadow/off: `POLICY_GATES_MODE=shadow` then `off`
   - Final hard rollback: all `*_V1=false`

## Runtime safety notes
- All flags default to non-enforcing/off behavior.
- No existing execution path modified in this minimal slice.
- Changes are reversible by removing helper module usage or setting flags off.
