# OC-3 Resource Contract Probe 002 — implementation report

**Stage:** `OC3-RESOURCE-CONTRACT-PROBE-002`

**State:** implemented and validated offline; real Probe 002 not executed.

**Implementation aggregate:** `51fd720da24b3a718916dc907b2ee7688a9d8eedd3db29fe9b17e16a95c12380`

## Historical state preserved

Probe 001 remains `RESOURCE_CONTRACT_PROBE_PARTIALLY_RESOLVED` with immutable terminal/log SHA-256 `a91ef41dea95928b5d76e7e9a3eff595753a64686b1d069202406e8400a56741`. It consumed 56 requests and 120,960 body bytes after 14 successful HEAD and 42 exact Range responses, with no retry and no pixel decode. Binding 001 remains SHA-256 `fd8ebd4057ddbc32b4a0f87d65cf61772c637a08b3a7ffbd76dc76f9de80c333`. No Probe-001 file was modified.

Probe 002 imports cumulative totals of 64 requests and 89,582,606 body bytes, leaving 136 requests and 1,521,030,130 bytes under the unchanged global caps.

## Files changed

- `OC3_RESOURCE_CONTRACT_PROBE_002_AMENDMENT.md`: narrow prospective correction and limits.
- `oc3/oc3lib/resource_contract_probe002.py`: closed binding validation, historical tripwire, cumulative accounting, durable evidence, 16-block FITS scanner and resolved-contract publication.
- `oc3/oc3_resource_contract_probe002.py`: `--help`, offline `--dry-run` and explicit Probe-002 network entry point.
- `oc3/schemas/oc3_dr9_coadd_resource_probe_binding_002.schema.json`: closed Binding-002 schema.
- `oc3/INPUTS/OC3_RESOURCE_CONTRACT_PROBE_BINDING_002.json`: canonical sealed binding of the unchanged 14 URLs.
- `oc3/tests/test_resource_contract_probe002.py`: 17 focused synthetic tests.
- `oc3/tests/test_physical_contract_probe.py`: the production-input tripwire now enumerates the CSV plus the two committed probe bindings and still rejects every other entry.
- `oc3/README.md`: Probe-002 entry-point summary.

## Durable checkpoint model

Before each request, the implementation atomically publishes its request and worst-case byte reservation. Every valid HEAD produces an immutable sealed file under `HEAD_EVIDENCE/`. Every fully resolved resource produces an immutable sealed file under `RESOURCE_CHECKPOINTS/` before the next resource begins. Each transition publishes an immutable aggregate-history snapshot and atomically replaces `PROBE_002_AGGREGATE.json`; the aggregate references checkpoint paths, file SHA-256 and content seals.

Resource checkpoints retain only technical structure: HEAD binding, physical/logical HDU mapping, compressed representation, selected FITS cards, shape, BITPIX/dtype, BUNIT when observed, WCS cards, requested header intervals and exact first-data offset. Science pixels are never requested or decoded. Failure records the exact resource and observed block count while keeping all completed checkpoints usable.

The execution first performs 14 HEAD requests, then scans headers in frozen inventory order. Range requests are single aligned 2880-byte blocks, require exact 206 and `Content-Range`, and stop in the block containing `END`. A primary data span is skipped arithmetically. Per-resource header ceiling is 16; global Probe-002 ceilings are 122 Range requests, 351,360 charged Range bytes and 136 total new requests. Retries are zero and concurrency is one.

## Binding 002

- File SHA-256: `d449324f4794120095b2bf039b37b8bcee6679bf8ce857e926bcbdce44e2de15`
- Canonical content seal: `ff71883fe3f049674174551889c8701a84edacb83ec03b77cb3914957689d3f1`
- Resources: 14, byte-for-byte resource list inherited from Binding 001.
- Bound implementation: entry point, module and amendment paths plus SHA-256.
- Acquisition authorization: absent.

## Offline validation

- Focused Probe-002 suite: **17/17 PASS**, 0 failures, 0 skips. Log `/tmp/oc3_probe002_focused.log`, SHA-256 `eb07a4542a70a561976af679904a357bb044fa6ca81a2a9c1e615de666b381f1`.
- Full regression: **711/711 PASS**, 0 failures, 0 skips, `real_network_requests=0`. Log `/tmp/oc3_probe002_full_regression.log`, SHA-256 `dbe0dc958b350710540c5afc476367ac8961b69b587f55e38a106757f88e30c7`.
- Production dry-run: PASS, 14 resources, 64 used requests, 136 remaining, 14 HEAD maximum, 122 Range maximum, 351,360 Range bytes, 16 blocks/resource, zero retries, zero bulk GET and `network_requests=0`. `/tmp/oc3_probe002_dry_run.json`, SHA-256 `1669d0bb372a06a2f09664b2b3cbcb0e64337cdf2365de2385deab59fa4598de`.

No network transport was constructed or invoked by implementation, focused tests, regression or dry-run. No array, location, image/invvar product or morphology operation was materialized.

## Exact human command

Run from `/home/jzsalinas/Documents/galaxy-morphology-discovery`:

```bash
/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/.venv/bin/python /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/oc3_resource_contract_probe002.py --execute-probe-002 --execute-network --project /home/jzsalinas/Documents/galaxy-morphology-discovery --binding /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/INPUTS/OC3_RESOURCE_CONTRACT_PROBE_BINDING_002.json --audit-directory /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/resource_contract/OC3-RESOURCE-CONTRACT-PROBE-002 --log /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/resource_contract/OC3-RESOURCE-CONTRACT-PROBE-002/PROBE_002_RUN.log --max-new-requests 136 --max-range-requests 122 --max-range-bytes 351360 --max-header-blocks 16
```

Expected transfer is at most 351,360 bytes and audit output is a few MiB. Runtime depends on up to 136 sequential provider requests and possible throttling. There is no resume command. Success prints and writes `RESOURCE_CONTRACT_PROBE_RESOLVED`; partial failure writes `RESOURCE_CONTRACT_PROBE_PARTIALLY_RESOLVED` and preserves all checkpoints. Do not rerun a partial Probe 002 without a new prospective decision.

Bulk auxiliary acquisition and location selection remain unauthorized.

**OC-3 MORPHOLOGICAL SCIENTIFIC PHASE REMAINS NOT STARTED.**
