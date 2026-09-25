# OC3 Source-Metadata Autonomous Recovery Envelope Specification 001

Status: **PROSPECTIVE; INACTIVE; BOOTSTRAP ONLY**.

Mission `OC3-SOURCE-METADATA-AUTONOMOUS-RECOVERY-ENVELOPE-001` has scope `SOURCE_METADATA_ACQUISITION_WITH_BOUNDED_TECHNICAL_RECOVERY`. It begins from closed predecessor commit `b356b448f170d49a03727722324ed0d6e6913c34`, outcome `SOURCE_METADATA_ACQUISITION_INCONCLUSIVE`, error `DATALAB_TRANSPORT_FAILURE`. The predecessor observed one request, HTTP 200, `text/html`, zero application-body bytes, zero schema rows, zero counts, zero source rows, zero holdout access and zero positional topology operations. Its report, final state, ledger aggregate, runtime terminal and query-manifest identities are immutable.

## Architectural finding

`PREMATURE_MISSION_FINALIZATION_ON_RECOVERABLE_TECHNICAL_FAILURE` is frozen as an architectural defect. An action terminal is not a mission terminal: `ACTION_TERMINAL != MISSION_TERMINAL`. Every action terminates, then the immutable Recovery Graph selects exactly `RECOVER_AUTONOMOUSLY`, `FINALIZE_SCIENTIFIC` or `STOP_REQUIRES_HUMAN`.

## Immutable science

The Scientific Invariants Manifest is the complete non-mutable scientific contract. It freezes the pilot frame, targets, holdouts, support bricks, tables, projection, five ADQL semantics and hashes, `brick_primary`, schema and row gates, count cap 150,000, `TOP 150001`, identity/coordinate/order/count integrity, ivar states and all scientific firewalls. While active, mutation is `STOP_REQUIRES_HUMAN`.

Transport representation is not science. A governed recovery may change only a documented endpoint/path for the same query, standards-compliant TAP GET/POST serialization, representation handling, CSV wrapper/parser, capability discovery, diagnostic capture, local network implementation or dependency-free adapter. It may never change predicates, brick support, projection, tables, caps, sentinel or scientific criteria. Reusing the byte-identical ADQL is preferred; semantic identity must be mechanically proven before material use.

## Finite governed recovery

Allowed action families are exactly `TECHNICAL_RESPONSE_DIAGNOSTIC`, `OFFICIAL_SERVICE_DOCUMENTARY_PROBE`, `OFFLINE_TECHNICAL_REPAIR`, `MATERIAL_SOURCE_METADATA_ACQUISITION` and `TECHNICAL_INTEGRITY_TRIAGE`. The graph explicitly classifies every allowed continuation; unmapped conditions stop for human review. Credentials, new authority, invariant or graph mutation, target/holdout/projection/table/column/query/cap change, budget increase, matching/radius/threshold introduction, holdout access or Policy Core mutation stop for human review.

Technical recovery is bounded to four generations, three code-repair generations, eight technical requests, 2,097,152 technical body bytes, 262,144 bytes per technical request, concurrency one, zero retries and at most two occurrences of one technical failure class after distinct remediation. Material acquisition retains five requests, 67,108,864 body bytes, its existing per-response caps, concurrency one, zero retries and no resume. Technical accounting never consumes material slots; every request is classified.

Every network action follows standing authorization → action registration → single-use permit → supervisor permit consumption → single-use worker capability → worker capability consumption → durable request intent → network. Crash restores neither gate. Documentary requests have the same governance. Runtime bodies remain local.

## First action

The first state-bound action is an unexecuted `TECHNICAL_RESPONSE_DIAGNOSTIC`. It may reissue only the exact frozen schema ADQL, once, with a 65,536-byte body cap. Content type is evidence. It may hash and locally preserve the body and classify only its technical representation. It cannot parse HTML as schema, query counts or rows, inspect holdouts, or make a scientific claim.

The first prospective path may continue diagnostic → official documentary probe → offline technical repair → synthetic validation → material acquisition. This is a permitted graph, not a guaranteed result. Autonomous repair begins only after an action terminal routes to it, changes only frozen technical paths, and produces a patch manifest proving all scientific, graph, query and firewall identities unchanged.

Scientific terminals remain `SOURCE_METADATA_ACQUISITION_COMPLETED`, `SOURCE_METADATA_ACQUISITION_RESOURCE_BOUND`, `SOURCE_METADATA_ACQUISITION_INCONCLUSIVE` and `SOURCE_METADATA_ACQUISITION_INTEGRITY_FAILED`. A technical action failure alone cannot finalize the mission.
