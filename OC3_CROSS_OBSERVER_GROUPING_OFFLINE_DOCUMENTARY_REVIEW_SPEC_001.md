# OC3 Cross-Observer Grouping Offline Documentary Review Specification 001

Scope: `OFFLINE_DOCUMENTARY_SEMANTIC_REVIEW_ONLY`.

This Stage B action is fully offline.  It reads only exact, SHA-bound local
snapshots and closed failure terminals from the governed documentary actions.
It reads no source rows, astronomical values, pixels, labels, morphology, or
network resource and selects no radius or score threshold.

Every frozen documentary claim is classified as `SUPPORTED`, `INCONCLUSIVE`,
or `CONFLICT`.  `SUPPORTED` requires the following predeclared observations:

1. `CATALOG_SOURCE_IDENTITY`: the DR9 catalog page defines the unique
   `(RELEASE, BRICKID, OBJID)` hash and the corrected provider schema exposes
   all three fields in each regional table.
2. `BRICK_PRIMARY_SEMANTICS`: the catalog page defines membership inside the
   brick boundary and the corrected schema exposes `brick_primary`.
3. `NORTH_SOUTH_PROCESSING_DOMAINS`: the release page separately identifies
   northern BASS/MzLS and southern DECam sources.
4. `RESOLVED_CATALOG_NOT_EQUIVALENCE_MAP`: the release page defines resolved
   sources by a north/south region-retention rule and Data Lab describes the
   combined table as a catalog; this supports only the project inference that
   it is not an independent-observation equivalence map.
5. `ASTROMETRIC_FIELD_SEMANTICS`: the provider documentation and corrected
   schema define RA/DEC at J2000 and expose RA/DEC inverse variances.
6. `CALIBRATION_ERROR_OMITTED_FROM_IVARS`: both inverse-variance descriptions
   explicitly exclude astrometric calibration errors.
7. `GAIA_DR2_ASTROMETRIC_PROVENANCE`: the release page explicitly states that
   DR9 image astrometry and extracted positions are tied to Gaia Data Release
   2.
8. `REGIONAL_DATALAB_TABLE_AVAILABILITY`: corrected `TAP_SCHEMA` responses
   contain exactly the combined, north, and south table identities and every
   allowlisted field in all three.
9. `CROSS_IDENTIFICATION_FORMALISM_ASSUMPTIONS`: an acquired primary paper is
   required.  HTTP failure terminals alone cannot support it.
10. `BOUNDED_PILOT_SPECIFIABLE_WITHOUT_THRESHOLD`: every preceding claim must
    be supported; no missing formalism may be replaced by a familiar radius.

No observed predicate may be weakened after execution.  Any contradictory
provider statement produces `CONFLICT`; a missing predicate produces
`INCONCLUSIVE`.  The documentary outcome is
`DOCUMENTARY_SOURCE_METADATA_CONFLICT` if any claim conflicts,
`DOCUMENTARY_SOURCE_METADATA_PILOT_SPECIFIABLE` only if all ten are supported,
and otherwise `DOCUMENTARY_SOURCE_METADATA_PILOT_INCONCLUSIVE`.

