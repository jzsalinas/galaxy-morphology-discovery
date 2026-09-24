# OC3 exact desitarget mandatory-blob bundle specification 001

## Prospective selection

The complete, non-truncated tree for desitarget commit `dd30297f9d50fcb7bbba57d79d4b8fc86cb35701` has been frozen locally. Before reading any source blob, this stage selects exactly the five paths already declared mandatory by the frozen zero-byte provenance implementation:

1. `py/desitarget/randoms.py`
2. `bin/select_randoms`
3. `bin/supplement_randoms`
4. `py/desitarget/io.py`
5. `doc/changes.rst`

Their path, blob SHA, and unencoded size must match the immutable tree inventory. No other blob is authorized by this action.

## Transport

Each blob is retrieved once, sequentially, through its exact official GitHub Git Data API URL. Responses must be HTTP 200 JSON Git blob objects with the frozen SHA, `encoding=base64`, exact decoded size, and exact Git blob SHA recomputed as SHA-1 of `blob <size>\0<content>`. Redirects, retries, mirrors, credentials, generic URLs, and concurrency above one are prohibited.

Per-resource accepted/read caps are frozen by the candidate. One extra byte per resource is reserved only to detect an over-cap response. A failure stops the remaining sequence, records actual requests and bytes, produces a terminal, and consumes the permit.

## Offline analysis

After all five blobs validate, the exact decoded bytes are preserved locally under their source-tree paths. The implementation then runs the already frozen eight search terms:

`survey-bricks`, `survey-bricks-dr9-randoms`, `AREA_PER_BRICK`, `PHOTSYS`, `supplement_randoms`, `zeros=True`, `write_randoms`, `resolve`.

It also runs the existing producer trace over the three required implementation files. Search hits record only path, line number, and line hash. Source content remains local runtime evidence.

This mandatory subset can establish implementation facts that the existing producer analyzer recognizes. A negative named-product search over five files does not prove absence from the complete tree and cannot close the named-product provenance gap.

## Boundary

The stage uses only `EXACT_DESITARGET_0_48_0_METADATA_AND_SOURCE`. It reads no astronomical product, PHOTSYS byte, BRICKNAME, BRICKID, or ROOT value. It cannot select a scientific outcome, create a resolver, or start Panel V2, P1, or morphological discovery.
