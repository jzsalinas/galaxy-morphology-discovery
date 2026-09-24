from __future__ import annotations

import json
from pathlib import Path
import unittest

from oc3lib import observational_multiplicity as om
from oc3lib import observational_multiplicity_governor as gov


GEOMETRY = (1.0, 2.0, 0.9, 1.1, 1.9, 2.1)


def identity(index: int) -> om.GlobalBrickIdentity:
    return om.GlobalBrickIdentity(f"{index:04d}p001".encode("ascii"), index)


def root(index: int, geometry=GEOMETRY) -> om.RootBrick:
    return om.RootBrick(identity(index), geometry)


def view(index: int, domain: str, geometry=GEOMETRY, valid=True) -> om.RegionalBrickView:
    return om.RegionalBrickView(domain, identity(index), geometry, valid)


class ObservationalMultiplicityTests(unittest.TestCase):
    def code(self, expected, function, *args, **kwargs):
        with self.assertRaises(om.MultiplicityError) as caught:
            function(*args, **kwargs)
        self.assertEqual(caught.exception.code, expected)

    def test_same_global_brick_north_south_is_both_not_duplicate(self):
        entries, counts = om.build_global_view_relation([root(1)], [view(1, "north")], [view(1, "south")])
        self.assertEqual(entries[0].category, om.VIEW_BOTH)
        self.assertEqual(counts["both"], 1)
        self.assertEqual(len(entries), 1)

    def test_north_only_south_only_and_both(self):
        entries, counts = om.build_global_view_relation(
            [root(1), root(2), root(3)],
            [view(1, "north"), view(3, "north")],
            [view(2, "south"), view(3, "south")],
        )
        self.assertEqual([entry.category for entry in entries],
                         [om.VIEW_NORTH_ONLY, om.VIEW_SOUTH_ONLY, om.VIEW_BOTH])
        self.assertEqual((counts["north_only"], counts["south_only"], counts["both"]), (1, 1, 1))

    def test_duplicate_inside_one_regional_summary_fails(self):
        self.code("REGIONAL_IDENTITY_DUPLICATE", om.build_global_view_relation,
                  [root(1)], [view(1, "north"), view(1, "north")], [])

    def test_root_identity_mismatch_fails(self):
        self.code("REGIONAL_ROOT_IDENTITY_MISMATCH", om.build_global_view_relation,
                  [root(1)], [view(2, "north")], [])

    def test_geometry_mismatch_fails(self):
        altered = (1.0, 2.0, 0.8, 1.1, 1.9, 2.1)
        self.code("REGIONAL_ROOT_GEOMETRY_MISMATCH", om.build_global_view_relation,
                  [root(1)], [view(1, "north", altered)], [])

    def test_row_order_invariance(self):
        rows = [root(1), root(2), root(3)]
        a, counts_a = om.build_global_view_relation(rows, [view(3, "north"), view(1, "north")],
                                                   [view(3, "south"), view(2, "south")])
        b, counts_b = om.build_global_view_relation(reversed(rows), [view(1, "north"), view(3, "north")],
                                                   [view(2, "south"), view(3, "south")])
        self.assertEqual(a, b)
        self.assertEqual(counts_a, counts_b)

    def test_selection_identity_excludes_region_and_selects_once(self):
        entry = om.build_global_view_relation([root(1)], [view(1, "north")], [view(1, "south")])[0][0]
        self.assertNotIn(b"north", om.global_selection_hash_bytes(entry.identity))
        self.assertNotIn(b"south", om.global_selection_hash_bytes(entry.identity))
        self.assertEqual(len(om.select_global_identities([entry], 1)), 1)

    def test_all_and_only_valid_views_are_retained(self):
        entry = om.RelationEntry(identity(1), om.VIEW_BOTH,
                                 (view(1, "north", valid=True), view(1, "south", valid=False)), False)
        retained = om.retain_all_valid_views([entry])
        self.assertEqual(tuple(item.observer_domain for item in retained), ("north",))

    def test_fixture_exclusion_is_global(self):
        entries, counts = om.build_global_view_relation([root(1)], [view(1, "north")],
                                                        [view(1, "south")], [identity(1)])
        self.assertTrue(entries[0].fixture_excluded)
        self.assertEqual(counts["fixture_exclusions"], 1)
        self.code("SELECTION_CARDINALITY_INSUFFICIENT", om.select_global_identities, entries, 1)

    def test_photsys_tractor_network_morphology_firewall_stays_zero(self):
        counters = om.AccessCounters()
        counters.require_clean()
        self.assertEqual(counters.PHOTSYS_reads, 0)
        self.assertEqual(counters.Tractor_cells_read, 0)
        self.assertEqual(counters.network_requests, 0)
        self.assertEqual(counters.morphology_accesses, 0)
        counters.PHOTSYS_reads = 1
        self.code("FIELD_FIREWALL_VIOLATION", counters.require_clean)

    def test_observer_domain_cannot_be_morphology_label(self):
        for allowed in ("PROVENANCE", "CONFOUND_AUDIT", "REPLICATION_AUDIT"):
            om.validate_observer_domain_role(allowed)
        self.code("OBSERVER_DOMAIN_ROLE_FORBIDDEN", om.validate_observer_domain_role, "MORPHOLOGY_LABEL")

    def test_balancing_or_region_cannot_enter_selection_contract(self):
        om.validate_selection_contract(("brickname", "brickid"))
        for fields in (("region", "brickname", "brickid"),
                       ("brickname", "brickid", "balance"),
                       ("observer_domain", "brickname", "brickid")):
            self.code("OBSERVER_DOMAIN_SELECTION_FORBIDDEN", om.validate_selection_contract, fields)

    def test_same_group_cannot_cross_split(self):
        self.code("SPLIT_GROUP_LEAKAGE", om.validate_split_assignments,
                  [("object-1", "train"), ("object-1", "test")], confirmatory=True)

    def test_unresolved_grouping_blocks_confirmatory_split(self):
        self.code("UNRESOLVED_GROUPING_BLOCKS_CONFIRMATORY_SPLIT", om.validate_split_assignments,
                  [(None, "test")], confirmatory=True)
        om.validate_split_assignments([(None, "exploratory")], confirmatory=False)

    def test_bootstrap_candidate_is_offline_inactive_and_photsys_independent(self):
        result = gov.validate_all()
        self.assertFalse(result["active"])
        self.assertEqual(result["state"], gov.STATE_WAITING)
        self.assertEqual(result["permits_issued"], 0)
        candidate, contract = gov.validate_candidate()
        self.assertEqual(contract["network_request_reservation"], 0)
        self.assertEqual(contract["application_body_reservation"], 0)
        self.assertEqual(contract["schema_version"], "OC3_OBSERVATIONAL_MULTIPLICITY_ACTION_CONTRACT_002")
        self.assertEqual(contract["requested_prohibited_scopes"], [])
        fields = sum(candidate["decoded_fields"].values(), [])
        self.assertNotIn("PHOTSYS", fields)
        self.assertFalse(gov.AUTHORIZATION_PATH.exists())
        self.assertFalse((om.PROJECT / contract["permit_output_path"]).exists())
        self.assertEqual(gov.evaluate_candidate()["decision"], gov.MANDATE_NOT_ACTIVE)

    def test_closed_photsys_terminal_is_exact_immutable_input(self):
        candidate, _ = gov.validate_candidate()
        self.assertEqual(candidate["closed_photsys_terminal"], {
            "claim_matrix_sha256": "72d9b26c5be5e03acb9bc41f88421ce087705fabfb1ee0421eb533f971c635c5",
            "commit": "9a492bd43f804d3b17af7a21875a9e82314375e4",
            "final_report_sha256": "e80d7caeb57f3c05dd66986e801c46a78d6a8abb454aea678332a6e29639dc24",
            "outcome": "PHOTSYS_0x00_SEMANTICS_INCONCLUSIVE",
        })


if __name__ == "__main__":
    unittest.main()
