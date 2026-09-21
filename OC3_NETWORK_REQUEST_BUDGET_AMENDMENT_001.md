# OC-3 Network Request Budget Amendment 001

**Status:** prospective operational-governance correction before auxiliary acquisition

**Scope:** `AUXILIARY_14_ONLY` and later separately authorized network stages

**Trigger:** measured header-probe request overhead, observed before any auxiliary array, location, image/invvar or morphology operation

## Frozen historical state

The original OC-3 plan used 200 requests as its global request cap. That value remains immutable in the historical specifications, bindings, resolved resource contract and Probe-001/002 evidence. Probe 002 closed with cumulative counters of 166 requests and 89,836,046 HTTP body bytes. No counter is reset, erased or reinterpreted.

The resolved resource contract remains byte-identical at SHA-256 `5afff8fddbcb8a9e86ea3f55cf89288840a21ca705bca121ed1b9204c349616d`. It contains 14 resolved `AUXILIARY_FIRST` resources and 12 deferred `FUTURE_IMAGE_INVVAR` resources.

## Narrow accounting correction

The global HTTP body cap remains 1,610,612,736 bytes. Disk, I/O, RAM, CPU, wall-time and concurrency caps remain unchanged. Every request and every observed or conservatively reserved body remains cumulative and auditable across stages.

The value 200 is retained as the original planning estimate and the historical hard cap applied through Probe 002. For every future stage, request safety is enforced by a prospectively sealed stage-local request cap. A network stage cannot construct transport without an exact stage ID, exact resource inventory and order, primary request count, per-identity retry ceiling, closed stage retry pool, exact stage request cap, imported cumulative counters and separate human authorization.

This amendment changes no brick, resource, URL, product, observer-variation strategy, location-selection rule, image content, byte cap or scientific Gate. Request count is a transport safeguard; it is not a morphology criterion, observational-equivalence definition, sample-selection criterion, success metric, holdout criterion or physical hypothesis.

## `AUXILIARY_14_ONLY` stage

The first-run primary plan is exactly:

| Request class | Count |
|---|---:|
| HEAD | 14 |
| GET | 14 |
| Primary total | 28 |
| Closed retry pool | 6 |
| Stage request cap | 34 |

Concurrency is one. Each identity retains a maximum of two additional attempts beyond its primary requests. No automatic retry or automatic resume is permitted. Every additional request consumes the retry pool, the stage cap and the cumulative request counter. Request 35 fails before transport. A partial attempt requires a separately sealed resume authorization; validated HEAD evidence and completely staged resources from that same attempt may be reused only after their immutable binding and checksums pass.

The stage starts from 166 cumulative requests and 89,836,046 cumulative body bytes. Cumulative requests may exceed the historical planning value 200 only inside this and later separately authorized stage-local envelopes. They never reset.

## Exact byte plan and representation drift

The 14 resolved body lengths sum to exactly 3,827,520 bytes. Before the first GET, the implementation must validate all 14 HEAD representations, publish an immutable complete-body plan and demonstrate that the primary body reservation fits the unchanged global body, disk, I/O and RAM caps. Each HEAD Content-Length must equal the resolved contract; URL, identity representation and observed ETag when present must also agree.

A discrepancy is representation drift and stops before GET. It does not trigger another probe, alternate URL, release substitution or automatic correction. Probe 002 is never resumed or modified.

## Authorization boundary

An offline candidate may bind the technical proposal for human review but cannot authorize transport. Final authorization must be a separate canonical sealed artifact with explicit human identity and time, bound to the exact candidate bytes. Location selection, image/invvar acquisition, bulk work outside the 14 resources and science-pixel interpretation remain unauthorized.

**OC-3 MORPHOLOGICAL SCIENTIFIC PHASE REMAINS NOT STARTED.**
