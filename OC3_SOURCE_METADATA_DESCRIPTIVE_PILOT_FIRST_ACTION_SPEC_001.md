# OC3 Source-Metadata Pilot Frame Derivation 001

This frozen first action is `PILOT_FRAME_DERIVATION`, stage `OC3-SOURCE-METADATA-PILOT-FRAME-DERIVATION-001`, scope `OFFLINE_PILOT_FRAME_DERIVATION_ONLY`.

It verifies and reads only:

- `oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001/RAW_IMMUTABLE/ROOT_SUMMARY/survey-bricks.fits.gz` (`dc943d702357f93553b9e5d15e87ace38df94eb7095f4100657407b3f9919c5f`): `BRICKNAME, BRICKID, BRICKROW, RA, DEC, RA1, RA2, DEC1, DEC2`.
- `oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001/RAW_IMMUTABLE/NORTH_SUMMARY/survey-bricks-dr9-north.fits.gz` (`2edd5c295fdad26852c6f224a3ff023cff43dd0e03a53acd35b767e726ee72fb`): `BRICKNAME, BRICKID`.
- `oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001/RAW_IMMUTABLE/SOUTH_SUMMARY/survey-bricks-dr9-south.fits.gz` (`7360414f5d53571ca70fa0cb483eb8c80cfcbe80df0856a117246f442a0b9a3f`): `BRICKNAME, BRICKID`.
- `oc3/INPUTS/OC3_DEVELOPMENT_BRICKS.csv` (`147c0942a5340ed18eec23a610f8afd5721390fad09c1da7ed01593deb40fab6`): identity columns only.

The implementation reconstructs `GLOBAL_VIEW_BOTH`, applies `SHA256_ASCII_GLOBAL_BRICK_IDENTITY_V1`, constructs `WRAP_AWARE_CLOSED_RA_BRICKROW_GUARD_1_V1`, and selects exactly two targets followed by two holdouts with pairwise disjoint guards. It writes one compact canonical `PILOT_FRAME.json` atomically to the candidate-bound local output directory. The file includes selected identities and hashes, each selected guard's root geometry identities, input hashes, and algorithm IDs. It never writes the complete eligible list.

Network, source rows, PHOTSYS, morphology, matching, radius, threshold, group IDs, Panel V3 and P1 all remain zero. The action is not executed by bootstrap. A later authorization and single-use permit are required.
