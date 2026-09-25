# OC3 Source-Metadata Autonomous Recovery Stop Report 001

## Mission terminal

`STOP_REQUIRES_HUMAN`

Stop reason:
`FIRST_CANDIDATE_EXECUTION_PATH_BINDING_CONTRADICTION`.

The reviewed standing authorization was materialized and validated, and the
production Mission Runner activated the recovery envelope. Generation 1
registered the frozen `TECHNICAL_RESPONSE_DIAGNOSTIC` candidate for trigger
`DATALAB_TRANSPORT_FAILURE` and issued its single-use technical permit.

Execution then failed closed before permit consumption. The registered and
permit-bound candidate is:

`oc3/INPUTS/OC3_SOURCE_METADATA_RECOVERY_FIRST_CANDIDATE_001.json`

Both the candidate's sealed supervisor argv and its sealed worker argv instead
bind the candidate argument to:

`oc3/SOURCE_METADATA_AUTONOMOUS_RECOVERY_LEDGER/CANDIDATES/OC3-SOURCE-METADATA-RECOVERY-G01-TECHNICAL_RESPONSE_DIAGNOSTIC.json`

The production runner reported `RECOVERY_SUPERVISOR_RUNTIME_FAILURE`. A direct
validation attempt using the registered candidate path reported
`RECOVERY_SUPERVISOR_ARGV_MISMATCH`. Using the argv-bound path cannot satisfy
the existing permit, which binds the registered `INPUTS` path. No path can
therefore satisfy both closed validations.

Correcting this contradiction requires changing or regenerating a frozen first
candidate, or changing the candidate factory, Mission Runner, supervisor, or
governor. Those are control-plane authorities outside the authorized Mutable
Technical Surface. The standing mandate lists a required control-plane change
as a `STOP_REQUIRES_HUMAN` condition, so the mission was stopped without a
silent repair or replay.

## Complete mission trace

1. The standing authorization was sealed at
   `oc3/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_STANDING_AUTHORIZATION_001.json`,
   SHA-256
   `dbda2947b11fecc7ea2849343d94a9231ddc5169280160a70931158dcce7bae8`.
2. The Mission Runner activated the exact waiting state. Activation evidence is
   `000_ACTIVATION.json`.
3. Recovery generation 1 registered action
   `TECHNICAL_RESPONSE_DIAGNOSTIC`, using first-candidate SHA-256
   `85768ae364773c67ae1ff458ead767db5f6ff4b789afcc28a61a185ef348dfd7`.
4. One single-use permit artifact was issued, SHA-256
   `badd14e4d398ff444a361bd929cfaed32f8bb3603bcf4a28b10d73bd2eaba314`.
   It was not consumed. The state counter remains zero because no action
   transition occurred.
5. No worker capability, request intent, output directory, action terminal, or
   Recovery Graph action transition was produced. The runner crash record and
   sealed contradiction evidence preserve the pre-network failure.
6. The mandate's explicit control-plane-change rule selected
   `STOP_REQUIRES_HUMAN`. The final state is sequence 3, SHA-256
   `364905c88a55e65d6429caadea3614b4de34b2990eea1b2cc23cde435ae784ea`.

There was no agentic handoff, documentary acquisition, technical patch,
transport contract, test receipt, adapter activation, or active-adapter runtime
SHA. Both registered adapters remain unvalidated.

## Resource accounting

- Technical network requests started: 0.
- Technical response-body bytes read or charged: 0.
- Technical requests remaining: 8.
- Technical body bytes remaining: 2,097,152.
- Material network requests started: 0.
- Material response-body bytes read or charged: 0.
- Material requests remaining: 5.
- Material body bytes remaining: 67,108,864.
- Retries: 0.
- Worker capabilities created or consumed: 0.
- Source rows observed: 0.

The issued permit is durable evidence, but it remains unconsumed and cannot be
reinterpreted as a network request or completed action.

## Frozen scientific identity

- Scientific Invariants SHA-256:
  `0d2b304e815a949cf7f69d44cd43148eb663fadb68afb47a7e9f767635a329f3`.
- Recovery Graph SHA-256:
  `19e7d6226d6550efbd32c62a4268d682e448f15fb3c490550471286943587fb7`.
- Technical Authorities Registry V2 SHA-256:
  `187ba6da5a85caf38a72988e1b95f2184903913ff923ba6611dacf60ebbcda36`.
- Schema query semantic SHA-256:
  `d5be2b494f737e047fea77f4002d387fed15c5dbe3ad019f4a0cafe83faf4a0b`.
- North-count query semantic SHA-256:
  `971078fbd961f2c9ae2f94f13a9ec9d4bb49e7421096cd90fb29c307e597c8f8`.
- South-count query semantic SHA-256:
  `7080fb7977071438871c5371255672e5da59e0d2ae0196adbb9c23f4c6c1f685`.
- North-rows query semantic SHA-256:
  `ee4b97daf1f7b3d23ccb5b9227200b40c9adb4cc40c6a6c33cff98fe6db0449a`.
- South-rows query semantic SHA-256:
  `30f5d1fdc0239c4302a6d6388e0bc25a0cb98b5bff2a8d851c97a9e1b89e7918`.

No scientific query reached a service. The scientific invariants, query
semantics, target/holdout firewalls, and Recovery Graph were not modified.

## Compact evidence

- Sealed contradiction evidence SHA-256:
  `6f3831aa4a0e8f7ea6a5a64d08f66af0addba66996440fa693a7d0af22dcaf96`.
- Mission final report SHA-256:
  `3d0c521aead3f1a977723161287b9366bb411136597153c904dfafac35833e16`.
- Ledger aggregate SHA-256:
  `af2db3858b15f23a4fdf5ef2365a8ebc2da7528455eaf9a28c178528b7d1178b`.

The ledger aggregate is SHA-256 over the canonical JSON mapping from each
sorted ledger-relative file path to that file's SHA-256, covering the seven
JSON files present at closure.

No source row was observed. This mission establishes no cross-observer
identity and makes no morphology claim.
