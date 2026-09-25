# OC3 Source-Metadata Autonomous Recovery Policy Core Contract 002

The Run-002 policy core consists only of the files bound by Policy Core
Manifest 002. While a Run-002 standing authorization is active, mutation of
that core requires `STOP_REQUIRES_HUMAN`.

Candidate paths are factory-derived. The first path is the fixed reviewed
INPUTS path; subsequent paths are derived from immutable generation and action
identity. Callers cannot supply a candidate path. Every operational gate binds
the Run-002 identifier, canonical candidate path, and candidate SHA.

Run-001 evidence is immutable predecessor evidence. No Run-001 authorization,
permit, consumption marker, capability, or runtime namespace grants authority
to Run-002.
