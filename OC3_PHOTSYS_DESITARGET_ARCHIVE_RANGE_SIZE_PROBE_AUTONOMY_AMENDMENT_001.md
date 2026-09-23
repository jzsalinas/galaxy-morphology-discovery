# OC3 Range-size probe autonomy amendment 001

## Historical binding

The frozen Range-size specification is `OC3_PHOTSYS_DESITARGET_ARCHIVE_RANGE_SIZE_PROBE_SPEC.md`, SHA-256 `f4751e6d5aab144b637c313fb6f100df234f8ab78ad2a4186a2036b4e44f5604`.

The historical human-review candidate is `oc3/INPUTS/OC3_PHOTSYS_DESITARGET_ARCHIVE_RANGE_SIZE_PROBE_CANDIDATE_001.json`, SHA-256 `a277a5e5b4d710650df5e89713dfd23a97c0f79ff273076273eb84835f55fc19`. It remains `PENDING_HUMAN_REVIEW`, is not modified, and cannot be executed under autonomous governance.

## Prospective candidate 002

Candidate 002 preserves the exact scientific and transport behavior of candidate 001: one GET to the exact commit archive, `Range: bytes=0-0`, zero application body bytes, request cap one, zero redirects, zero retries, concurrency one, HTTP 206 plus exact `bytes 0-0/TOTAL` success grammar, the same historical bindings, budget threshold, identity checks, and terminal mapping.

Only execution governance changes prospectively. Candidate 002 requires an active standing human autonomy authorization and a deterministic, action-specific `AUTONOMOUS_EXECUTION_PERMIT` bound to the exact candidate, command, state, sequence, and budgets. It does not accept a per-stage `FINAL_HUMAN_AUTHORIZATION`. No permit exists at bootstrap and no real Range operation is authorized.
