# OC-3 fixed native products and PSF final authorization review

**Authorization state:** `FINAL_HUMAN_AUTHORIZATION`

**Decision:** `AUTHORIZED`

**Authorized by:** José Salinas

**Authorized at (UTC):** `2026-09-21T16:18:58Z`

**Network performed by authorization and preflight:** zero requests, zero bytes

## Frozen bindings

| Binding | Value |
|---|---|
| Authorization path | `oc3/INPUTS/OC3_FIXED_NATIVE_PSF_ACQUISITION_AUTHORIZATION_001.json` |
| Authorization SHA-256 | `e493fa0acdeb0f70ebce2a51f04d1d41f18c5a5a81a6e745d0d1b8cc5afc3d0d` |
| Candidate SHA-256 | `961a763e5732b38c5193764a785a3799b0a74e9e42de111fa1de08c8d4cc2951` |
| Candidate internal seal | `59ccb5ed3dedfa0ac9ea1b52a48a83fadda2240108d9a8bbbdf2966a44bda662` |
| Implementation aggregate | `18d72c7843d376f7cc70b74a5906df5ec6d2dd046859e30b9fda735c9ba91661` |
| Location selection SHA-256 | `2e6f2cb070a363e9e3dbdb1f25670590c33500a293bb926d8ff94657a2ff8860` |
| Fixed-native contract SHA-256 | `8e8ac029aa61e82b2a089205aff4781123700a30ce24353dd95e5eaedd55befc` |
| Coadd-PSF contract SHA-256 | `8f7ba5c0f50f26f240ff08ece3a8e0afef62559cb35f4947423136a05904bf30` |
| Fixed-native resources/body | 12 / 144,766,080 bytes |
| PSF transport responses/identities | 18 / 54 |
| PSF total reservation | 56,623,104 bytes |
| Primary body reservation | 201,389,184 bytes |
| Primary requests | 42 |
| Stage retry pool / request cap | 6 / 48 |
| Cumulative start | 280 requests / 93,968,846 body bytes |
| Global body cap | 1,610,612,736 bytes |
| Concurrency | 1 |
| Expected success terminal | `BOUNDED_NATIVE_PRODUCTS_ACQUIRED` |

The production authorization validator accepted the canonical authorization,
its exact candidate binding and the closed resource and capability scope. The
focused result was `FINAL_HUMAN_AUTHORIZATION_VALIDATED`; its local evidence
SHA-256 was
`a2b438dfb9aef0a4719341e87e0a21287d3431d29f2ff8fa9a7dc9247610b6e0`.

The offline preflight validated paths, command vector, runtime caps, candidate,
authorization, resolved contracts, location manifest, inventories and budgets,
then stopped before construction of `ClosedAcquisitionTransport`. Its result was
`READY_AT_REAL_TRANSPORT_BOUNDARY`; its local evidence SHA-256 was
`aa62c6de672d3e14b0a3bd6d93aa35592e8ee830f05718b9d335fcebf49b91de`.

This authorization covers only the twelve fixed-native resources and eighteen
bundled PSF responses sealed in the candidate. It does not authorize location
changes, shape homogenization, response rewriting, cutout extraction,
preprocessing, morphology inspection, automatic retry or automatic resume.

## Authorized human-executable command

Run from `/home/jzsalinas/Documents/galaxy-morphology-discovery`:

```bash
/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/.venv/bin/python \
  /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/oc3_fixed_native_psf_acquisition.py \
  --acquire \
  --execute-network \
  --project /home/jzsalinas/Documents/galaxy-morphology-discovery \
  --candidate /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/INPUTS/OC3_FIXED_NATIVE_PSF_ACQUISITION_CANDIDATE_001.json \
  --authorization /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/INPUTS/OC3_FIXED_NATIVE_PSF_ACQUISITION_AUTHORIZATION_001.json \
  --audit-directory /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/fixed_native_psf_acquisition/OC3-FIXED-NATIVE-PSF-ACQUISITION-001 \
  --log /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/fixed_native_psf_acquisition/OC3-FIXED-NATIVE-PSF-ACQUISITION-001/ACQUISITION_RUN.log \
  --primary-request-count 42 \
  --retry-pool 6 \
  --stage-request-cap 48 \
  --fixed-body-bytes 144766080 \
  --psf-body-cap 56623104
```

**FIXED NATIVE + PSF FINAL AUTHORIZATION READY.**

**NEXT ACTION: HUMAN EXECUTES THE AUTHORIZED ACQUISITION.**

**OC-3 MORPHOLOGICAL SCIENTIFIC PHASE REMAINS NOT STARTED.**
