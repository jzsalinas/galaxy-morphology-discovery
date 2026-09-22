# OC3 PHOTSYS selective-value validation — post-execution review

## Status

This document closes the completed historical stage `OC3-GALAXY-ELIGIBILITY-PHOTSYS-SELECTIVE-VALUE-VALIDATION-001`. It is an offline review of existing sealed evidence. It does not rerun the stage, read another table byte, alter the failed attempt, or amend PHOTSYS semantics.

The historical terminal is:

`PHOTSYS_SELECTIVE_INVALID_PHOTSYS_FAILED`

The term `invalid` is retained only as the exact frozen V1 terminal. In this review, the affected observations are described as `PHOTSYS_OUTSIDE_FROZEN_V1_DOMAIN`: their bytes were outside the precommitted domain `{0x4e, 0x53, 0x20}`. No intrinsic or provider meaning is assigned to them.

## Frozen bindings

| Evidence | SHA-256 |
|---|---|
| `OC3_PHOTSYS_SELECTIVE_VALUE_VALIDATION_SPEC.md` | `c04d1392e3b7bd0e974c6244201566679dae30d479b9b644c8f3abc1b1a7a119` |
| `oc3/INPUTS/OC3_PHOTSYS_SELECTIVE_VALUE_VALIDATION_CANDIDATE_001.json` | `11496a57ab65d44f2c743c72b0c6ea88f4942cb2fa4fab716936357357c5770d` |
| `oc3/OC3_PHOTSYS_SELECTIVE_VALUE_VALIDATION_FINAL_AUTHORIZATION_001.json` | `5bd46901a4dc3c522e5c4feceab869023c8e8598b6530239526f18a283fc87f3` |
| `TERMINAL.json` | `ad817611054ace2daf395cebaa3a3bf70bfc90dac7f05a0f040366fdd1b241d8` |
| `VALIDATION_AGGREGATES.json` | `c0a7a0322a9f626e1d215717458b401ed260946211743bcea6f40abc065143af` |
| `OBSERVABILITY.json` | `977be060d5439908c0a47884ea2fe7c6211e4d1f7195f73ca4a060ef90bd420b` |

The three runtime artifacts are under `oc3/photsys_selective_value_validation/OC3-GALAXY-ELIGIBILITY-PHOTSYS-SELECTIVE-VALUE-VALIDATION-001/`. Their canonical seals validate.

## Observed V1 result

- Rows processed: `662174`.
- Valid `BRICKNAME`: `662174`.
- Valid `BRICKID`: `662174`.
- PHOTSYS inside the frozen V1 domain: `331966`.
- `0x4e` (`N`): `82897`.
- `0x53` (`S`): `249069`.
- `0x20` (ASCII space): `0`.
- `PHOTSYS_OUTSIDE_FROZEN_V1_DOMAIN`: `330208`.
- Matched among V1-domain rows: `331966`.
- `missing_from_PHOTSYS_authority`: `330208`.
- Identity duplicates and identity conflicts: `0`.
- Forbidden-span, forbidden-value, and whole-row counters: `0`.
- Network requests: `0`.
- Exact-span reads: `1324348`.
- Projected resolver published: `false`.

The equality between `missing_from_PHOTSYS_authority` and `PHOTSYS_OUTSIDE_FROZEN_V1_DOMAIN` is a consequence of the frozen V1 join boundary: rows without an accepted V1 PHOTSYS byte did not enter the projected resolver set. It is not evidence that physical rows were absent.

## Review conclusion

The V1 implementation behaved as specified and stopped closed. The evidence establishes only that `330208` observed bytes were outside the frozen V1 domain. It does not establish their raw byte identities or whether they mean blank, missing, footprint exclusion, NUL padding, provider sentinel, corruption, or anything else.

No resolver exists. PHOTSYS V1 semantics remain unchanged. Panel V2 remains `NOT_STARTED`; P1 remains `BLOCKED`; OC-3 morphological discovery remains not started.
