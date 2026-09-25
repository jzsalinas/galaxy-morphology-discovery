# OC3 Source-Metadata Autonomous Recovery Production Specification 003

This prospective revision governs only
`OC3-SOURCE-METADATA-AUTONOMOUS-RECOVERY-RUN-002` within scientific mission
`OC3-SOURCE-METADATA-AUTONOMOUS-RECOVERY-ENVELOPE-001`. Run-001 remains a
closed governed STOP and none of its authorization, permits, state, ledger, or
runtime evidence is reusable.

Every Run-002 candidate carries `run_id` and `candidate_path`. The candidate
file, supervisor `--candidate`, worker `--candidate`, permit, and worker
capability must bind the same canonical project-relative path and file SHA.
Aliases, copies, path overrides, and symlink indirection fail closed with
`RECOVERY_CANDIDATE_SELF_PATH_MISMATCH` or a narrower permit/capability
validation error.

First Candidate 002 is the sole reviewed INPUT candidate at
`oc3/INPUTS/OC3_SOURCE_METADATA_RECOVERY_FIRST_CANDIDATE_002.json`.
Children G02+ are generated only at deterministic paths under
`oc3/SOURCE_METADATA_AUTONOMOUS_RECOVERY_RUN_002_LEDGER/CANDIDATES/`.
Permits, consumption markers, capabilities, mission ledger, and runtime output
use distinct Run-002 namespaces.

`RUN_ID` is operational provenance and does not modify the scientific mission.
Scientific Invariants, Recovery Graph, Recovery Budget, query semantics,
holdout firewall, action families, and Technical Authorities V2 remain
unchanged. Both adapters begin `AVAILABLE_UNVALIDATED`.

Run-002 begins inactive and cannot emit a permit or perform network access
without a new Run-002 standing human authorization. This bootstrap performs no
network request and observes no schema response, count, row, or source value.
