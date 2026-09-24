# OC3 Source-Metadata Descriptive Pilot Stop Report 001

## Governed stop

Blocker: `CONSUMED_FRAME_PERMIT_NO_TERMINAL`.

The standing authorization was materialized and the governor activated the mission. The exact state-bound `PILOT_FRAME_DERIVATION` candidate was registered and permit `OC3-AUTONOMOUS-PERMIT-000003-27b9f0393867` was issued. The exact sealed argv was invoked.

The executor recorded permit consumption before local FITS access, as required. After the invocation ended, no executor process remained and neither the bound output directory nor `PILOT_FRAME.json` nor `TERMINAL.json` existed. The process result after permit issuance was not preserved as a compact executor artifact, so this report does not assign a technical cause.

## Immutable evidence

- Permit: `oc3/SOURCE_METADATA_DESCRIPTIVE_PILOT_AUTONOMY_PERMITS/OC3_SOURCE_METADATA_PILOT_FRAME_PERMIT_001.json`, SHA-256 `8e96a042d50e436b9fbd8ee65ccd53be5d9e2ae9a6152968511d7faa001a0f4d`.
- Consumption marker: `oc3/SOURCE_METADATA_DESCRIPTIVE_PILOT_AUTONOMY_LEDGER/PERMIT_CONSUMPTION/8e96a042d50e436b9fbd8ee65ccd53be5d9e2ae9a6152968511d7faa001a0f4d.json`, SHA-256 `70a22ada30ca459c939440750a562eec657dd7b72a6cb83b417d8fb1b2b433ef`.
- Active state at detection: SHA-256 `e104d54ced1f5ae63e9dc8cf591fdc0a7fb9ee71c681699ff993a5ada418b374`, sequence 2, with the frame action still registered.

## Accounting and scientific boundary

No network action was prepared or executed. Mission budgets remain five requests and 67,108,864 response-body bytes. No source row, count, Data Lab response, PHOTSYS value, morphology, target/holdout source information, matching operation, radius, scientific threshold, object-group ID, split-group ID, Panel V3 or P1 output was observed or produced.

No `PILOT_FRAME.json` exists, so no target or reserved-holdout identity is claimed from this attempt. The permit is consumed and cannot be replayed. A future recovery requires prospective human review and authorization before any renewed material access.
