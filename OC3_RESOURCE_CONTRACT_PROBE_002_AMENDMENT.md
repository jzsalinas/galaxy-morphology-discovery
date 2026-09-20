# OC-3 Resource Contract Probe 002 — narrow amendment

**Stage:** `OC3-RESOURCE-CONTRACT-PROBE-002`

**Status:** prospective correction after the immutable partial result of Probe 001.

## Historical trigger

`OC3-RESOURCE-CONTRACT-PROBE-001` ended as `RESOURCE_CONTRACT_PROBE_PARTIALLY_RESOLVED` after 56 requests and 120,960 response-body bytes. Fourteen HEAD requests and 42 exact 2880-byte Range responses succeeded, with zero retries and zero science pixels decoded. The terminal error was `FITS_HEADER_BLOCK_CAP`: the former six-block ceiling was insufficient. Probe 001 did not persist Content-Length, HDU or resource-level completion evidence with enough granularity for reuse. Its terminal, log, binding and counters remain immutable and are not promoted into missing per-resource facts.

The cumulative project state before Probe 002 is exactly 89,582,606 used body bytes and 64 used requests, leaving 1,521,030,130 body bytes and 136 requests under the unchanged global maxima. These counters never reset.

## Sole corrections

Probe 002 preserves the 14 literal auxiliary identities and underlying resource contract. It changes only the probe evidence and bounded header-scanning mechanism:

1. every successful HEAD is published immediately as an immutable sealed checkpoint;
2. every completely resolved resource header is published immediately as an immutable sealed checkpoint before advancing;
3. an atomically published aggregate and immutable aggregate history reference every checkpoint and SHA-256;
4. FITS header scanning may use up to 16 aligned 2880-byte blocks per resource;
5. scanning stops in the block containing the exact FITS `END` card and never requests the following data block;
6. a nonempty primary-data span is skipped arithmetically rather than read when a later image extension is required;
7. every Range response still requires status 206, the exact requested byte interval, exact total Content-Length, identity representation and exact body length;
8. failure records the exact resource, error and observed block count while preserving all earlier checkpoints;
9. Probe 002 has no retry or resume path. A later attempt requires a new prospective decision.

No auxiliary-array GET, image/invvar request, PSF request, location selection, pixel decode, resampling, preprocessing or morphology operation is authorized.

## Request and byte limits

Probe 002 imports 64 used requests before transport construction. Its local maxima are:

| Dimension | Maximum |
|---|---:|
| HEAD | 14 requests |
| Range | 122 requests |
| All new requests | 136 requests |
| Range response bodies | 351,360 bytes |
| Header blocks per resource | 16 |
| Block size | 2880 bytes |
| Retries | 0 |
| Concurrency | 1 |

Both local and cumulative global counters are reserved before a request starts. No request may raise the cumulative total above 200. A complete 2880-byte Range block is charged before transport and that conservative charge is retained after a crash, short response or validation failure; separately recorded observed bytes never reduce it.

## Durable evidence model

The distinct Probe-002 audit directory contains:

- a sealed copy of Binding 002;
- one immutable HEAD checkpoint per successful resource;
- one immutable structural checkpoint per fully resolved resource;
- immutable event and aggregate-history records;
- an atomically updated aggregate manifest with resource states `NOT_STARTED`, `HEAD_VALIDATED`, `HEADER_RESOLVED` or `FAILED`;
- a resolved resource contract only after all 14 resources reach `HEADER_RESOLVED`;
- an immutable terminal and compact log.

HEAD evidence contains only technical response identity and accounting. Structural checkpoints contain selected FITS header semantics, HDU mapping, shape, BITPIX/dtype, units when present and relevant WCS cards. Neither artifact contains science pixel values.

## Decisions

Success is `RESOURCE_CONTRACT_PROBE_RESOLVED`. A partial stop is `RESOURCE_CONTRACT_PROBE_PARTIALLY_RESOLVED`; all completed checkpoints remain evidence, but execution must not be repeated without a new prospective decision. Bulk auxiliary acquisition remains unauthorized after either terminal until separately reviewed.

**OC-3 MORPHOLOGICAL SCIENTIFIC PHASE REMAINS NOT STARTED.**
