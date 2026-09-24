from __future__ import annotations

from dataclasses import FrozenInstanceError
import inspect
import unittest

from oc3lib import cross_observer_grouping as cog


class CrossObserverGroupingSemanticsTests(unittest.TestCase):
    def source(self, domain="north", objid=1):
        return cog.CatalogSourceObservation(9011 if domain == "north" else 9012, 42, objid, domain)

    def code(self, expected, function, *args, **kwargs):
        with self.assertRaises(cog.GroupingError) as caught:
            function(*args, **kwargs)
        self.assertEqual(caught.exception.code, expected)

    def test_catalog_observation_is_not_object_group(self):
        source = self.source()
        self.assertEqual(source.identity, (9011, 42, 1))
        self.code("OBJECT_GROUP_EVIDENCE_REQUIRED", cog.AstrophysicalObjectGroup,
                  "object-1", (source,), "")

    def test_split_group_is_distinct_and_may_be_coarse(self):
        rows = (self.source("north", 1), self.source("north", 2), self.source("south", 9))
        group = cog.SplitSafetyGroup("coarse-cell-1", rows)
        self.assertEqual(len(group.observations), 3)
        self.assertFalse(hasattr(group, "object_group_id"))

    def test_unknown_grouping_blocks_replication_and_confirmatory_split(self):
        self.code("UNKNOWN_GROUPING_BLOCKS_REPLICATION_CLAIM", cog.validate_replication_claim, None)
        self.code("UNKNOWN_GROUPING_BLOCKS_CONFIRMATORY_SPLIT", cog.validate_split_assignments,
                  [(None, "test")], confirmatory=True)

    def test_one_to_many_many_to_one_and_many_to_many_preserved(self):
        self.assertEqual(cog.classify_candidate_cardinality(1, 2), cog.AssociationState.ONE_TO_MANY)
        self.assertEqual(cog.classify_candidate_cardinality(2, 1), cog.AssociationState.MANY_TO_ONE)
        self.assertEqual(cog.classify_candidate_cardinality(2, 2), cog.AssociationState.MANY_TO_MANY)
        cog.CrossObserverAssociation((self.source("north", 1),),
            (self.source("south", 2), self.source("south", 3)), cog.AssociationState.ONE_TO_MANY)

    def test_nearest_is_never_selected_implicitly(self):
        candidates = [self.source("south", 9), self.source("south", 2)]
        self.assertEqual([x.objid for x in cog.preserve_candidate_set(candidates)], [2, 9])
        self.assertNotIn("nearest", inspect.getsource(cog.preserve_candidate_set).lower().replace("never choose a nearest", ""))

    def test_region_cannot_enter_morphology_role(self):
        cog.validate_observer_domain_role("PROVENANCE")
        self.code("OBSERVER_DOMAIN_ROLE_FORBIDDEN", cog.validate_observer_domain_role, "MORPHOLOGY_LABEL")

    def test_exact_allowlist_and_denied_fields(self):
        self.assertEqual(cog.validate_source_projection(cog.ALLOWED_SOURCE_FIELDS), cog.ALLOWED_SOURCE_FIELDS)
        self.code("SOURCE_PROJECTION_NOT_EXACT", cog.validate_source_projection,
                  (*cog.ALLOWED_SOURCE_FIELDS, "TYPE"))
        self.code("SOURCE_PROJECTION_NOT_EXACT", cog.validate_source_projection,
                  cog.ALLOWED_SOURCE_FIELDS[:-1])

    def test_ivar_is_not_complete_covariance(self):
        self.code("STATISTICAL_IVAR_NOT_COMPLETE_COVARIANCE",
                  cog.validate_positional_uncertainty_contract, uses_ra_dec_ivar=True,
                  calibration_covariance_bound=False, extended_centroid_model_bound=True)
        self.code("EXTENDED_SOURCE_CENTROID_MODEL_UNRESOLVED",
                  cog.validate_positional_uncertainty_contract, uses_ra_dec_ivar=False,
                  calibration_covariance_bound=True, extended_centroid_model_bound=False)

    def test_resolved_catalog_rejected_and_regional_tables_require_contract(self):
        self.code("RESOLVED_TRACTOR_NOT_INDEPENDENT_POPULATION",
                  cog.validate_regional_source_table, cog.RESOLVED_TABLE, exact_schema_contract=True)
        self.code("EXACT_SOURCE_SCHEMA_CONTRACT_REQUIRED",
                  cog.validate_regional_source_table, "ls_dr9.tractor_n", exact_schema_contract=False)
        self.assertEqual(cog.validate_regional_source_table("ls_dr9.tractor_s", exact_schema_contract=True),
                         "ls_dr9.tractor_s")

    def test_holdout_contract_is_frozen_and_separated(self):
        contract = cog.FrozenHoldoutContract("GLOBAL_BRICK_IDENTITY_HASH_V1", "a" * 64, "b" * 64)
        with self.assertRaises(FrozenInstanceError):
            contract.holdout_digest = "c" * 64
        self.code("HOLDOUT_SEPARATION_INVALID", cog.FrozenHoldoutContract,
                  "GLOBAL_BRICK_IDENTITY_HASH_V1", "a" * 64, "a" * 64)

    def test_no_production_match_radius_constant(self):
        source = inspect.getsource(cog)
        self.assertNotIn("MATCH_RADIUS", source)
        self.assertNotIn("1.5 arcsec", source)
