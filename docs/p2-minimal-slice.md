# P2 Minimal Slice (Scaffold-Only)

Date: 2026-02-18 UTC  
Status: additive and reversible

## Scope delivered
1. Idempotency key utility proposal implemented as helper module + tests.
2. Feature-flag wiring helper added with concrete env flags and safe defaults.
3. Execution gate shadow wiring added to runtime path (decision telemetry + enforce hooks).
4. Rollback wiring plan documented for staged enablement.

## Files
- `python/helpers/idempotency.py`
- `python/helpers/p2_flags.py`
- `python/helpers/policy_gates.py`
- `tests/p2/test_idempotency_and_flags.py`
- `tests/p2/test_policy_gates.py`
- `example.env` (flag examples)
- `agent.py` (shadow gate + idempotency insertion hooks)

## Idempotency utility proposal
Implemented deterministic key derivation:
- `derive_idempotency_key(IdempotencyInput)`
- `payload_digest(payload)`
- `ttl_seconds_for_risk_tier(risk_tier)`

Key format:
- `idem:v1:<sha256(...)>`

This module is now minimally wired into runtime tool execution for mutating-tool calls (local-run dedupe), while remaining flag-gated and defaults-off.

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

## Runtime wiring added (shadow-first)
- `agent.py` now evaluates an execution policy gate per tool call when `POLICY_GATES_V1=true`.
- In `POLICY_GATES_MODE=shadow`, decisions are emitted as telemetry only (`policy.gate.evaluated`) and execution continues.
- In `POLICY_GATES_MODE=enforce` with `P2_SHADOW_EMIT_ONLY=false`, challenge/deny decisions can block execution.
- Mutating tool calls derive an idempotency key when `IDEMPOTENCY_V1=true` and emit `idempotency.key.derived` telemetry.
- Duplicate mutating calls are only blocked in enforce mode with shadow-emit disabled.

## Runtime safety notes
- All flags default to non-enforcing/off behavior.
- Changes are reversible by setting flags off.
- Emission and gate checks are additive; default behavior remains unchanged.
