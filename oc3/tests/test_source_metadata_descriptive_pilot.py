import inspect
import tempfile
import unittest
from pathlib import Path

from oc3lib.core import canonical
from oc3lib.cross_observer_grouping import file_sha256, load_canonical_json, sealed, sha256_bytes
from oc3lib import source_metadata_descriptive_pilot as science
from oc3lib import source_metadata_descriptive_pilot_governor as gov
from oc3lib.source_metadata_descriptive_pilot_validation import (
    CANDIDATE, EXPECTED_INPUTS, expected_command_argv, validate_candidate, validate_runtime_invocation,
)


def geom(name, ident, row, ra1, ra2):
    identity = science.GlobalBrickIdentity(name, ident)
    return identity, science.BrickGeometry(identity, row, 0.0, 0.0, ra1, ra2, -1.0, 1.0)


class SourceMetadataScienceTests(unittest.TestCase):
    def test_global_view_both_and_fixture_exclusion(self):
        root = [{"BRICKNAME": "a", "BRICKID": 1, "BRICKROW": 1, "RA": 1, "DEC": 0,
                 "RA1": 0, "RA2": 2, "DEC1": -1, "DEC2": 1},
                {"BRICKNAME": "b", "BRICKID": 2, "BRICKROW": 1, "RA": 3, "DEC": 0,
                 "RA1": 2, "RA2": 4, "DEC1": -1, "DEC2": 1}]
        north = [{"BRICKNAME": "a", "BRICKID": 1}, {"BRICKNAME": "b", "BRICKID": 2}]
        south = list(north)
        _, eligible = science.reconstruct_global_view_both(root, north, south,
            [science.GlobalBrickIdentity("b", 2)])
        self.assertEqual(eligible, (science.GlobalBrickIdentity("a", 1),))

    def test_global_identity_mismatch_fails(self):
        root = [{"BRICKNAME": "a", "BRICKID": 1, "BRICKROW": 1, "RA": 1, "DEC": 0,
                 "RA1": 0, "RA2": 2, "DEC1": -1, "DEC2": 1}]
        both = [{"BRICKNAME": "a", "BRICKID": 2}]
        with self.assertRaises(science.PilotIntegrityError):
            science.reconstruct_global_view_both(root, both, both, [])

    def test_development_fixture_file_uses_bound_bricknames(self):
        values = science.read_development_identities(gov.PROJECT / "oc3/INPUTS/OC3_DEVELOPMENT_BRICKS.csv")
        self.assertEqual(len(values), 2)
        self.assertTrue(all(isinstance(value, str) and value for value in values))

    def test_hash_literal_and_order_are_exact(self):
        identity = science.GlobalBrickIdentity("1234p567", 42)
        import hashlib
        expected = hashlib.sha256(b"OC3_SOURCE_METADATA_DESCRIPTIVE_PILOT_001|42|1234p567").hexdigest()
        self.assertEqual(science.target_digest(identity), expected)

    def test_closed_ra_wrap_and_touch(self):
        self.assertTrue(science.closed_ra_intervals_overlap(359, 1, 0.5, 2))
        self.assertTrue(science.closed_ra_intervals_overlap(10, 20, 20, 30))
        self.assertFalse(science.closed_ra_intervals_overlap(359, 1, 2, 3))

    def test_one_ring_adjacency_and_target_inclusion(self):
        items = [geom("a", 1, 5, 10, 20), geom("b", 2, 6, 15, 25),
                 geom("c", 3, 7, 15, 25), geom("d", 4, 4, 30, 40)]
        geometry = dict(items)
        self.assertEqual(science.guard_one(items[0][0], geometry), (items[0][0], items[1][0]))

    def test_selection_exact_counts_and_disjoint_guards(self):
        items = [geom(chr(97+i), i+1, i*3, i*20, i*20+5) for i in range(6)]
        geometry = dict(items)
        selected = science.select_frame([item[0] for item in items], geometry)
        self.assertEqual([x.role for x in selected], ["PILOT_TARGET"]*2+["RESERVED_HOLDOUT"]*2)
        guards = [set(x.guard) for x in selected]
        self.assertTrue(all(guards[i].isdisjoint(guards[j]) for i in range(4) for j in range(i)))

    def test_fewer_than_four_disjoint_guards_fails(self):
        items = [geom(chr(97+i), i+1, 1, 10, 20) for i in range(4)]
        with self.assertRaises(science.PilotIntegrityError):
            science.select_frame([x[0] for x in items], dict(items))

    def test_holdout_never_enters_target_guard_union(self):
        values = []
        for index, role in enumerate(["PILOT_TARGET"]*2+["RESERVED_HOLDOUT"]*2):
            ident = science.GlobalBrickIdentity(f"b{index}", index)
            guard = (ident, science.GlobalBrickIdentity(f"g{index}", 10+index))
            values.append(science.FrameSelection(ident, str(index), role, guard))
        union = science.target_guard_union(values)
        self.assertEqual(union, ("b0", "b1", "g0", "g1"))

    def test_source_projection_is_exact_and_denied_values_fail(self):
        science.validate_source_projection(science.SOURCE_PROJECTION)
        for denied in ("type", "shape_r", "flux_g", "ref_id", "photsys"):
            with self.assertRaises(science.PilotIntegrityError):
                science.validate_source_projection((*science.SOURCE_PROJECTION, denied))

    def test_combined_tractor_and_unknown_table_rejected(self):
        for table in ("ls_dr9.tractor", "other"):
            with self.assertRaises(science.PilotIntegrityError): science.validate_regional_table(table)

    def test_queries_are_literal_ordered_and_have_no_crossmatch(self):
        count = science.count_query("ls_dr9.tractor_n", ["b", "a"])
        rows = science.row_query("ls_dr9.tractor_s", ["b", "a"])
        self.assertIn("GROUP BY brickname ORDER BY brickname", count)
        self.assertIn("'a','b'", count)
        self.assertIn("SELECT TOP 150001", rows)
        self.assertIn("ORDER BY release,brickid,objid", rows)
        for query in (science.schema_query(), count, rows):
            self.assertNotIn("SELECT *", query.upper())
            self.assertNotIn("Q3C", query.upper())
            self.assertNotIn("CONE", query.upper())

    def test_count_before_row_and_both_domains_required(self):
        flow = science.AcquisitionSequence()
        with self.assertRaises(science.PilotIntegrityError): flow.accept_count("ls_dr9.tractor_n", {"a": 1})
        flow.accept_schema({table: science.SOURCE_PROJECTION for table in science.REGIONAL_TABLES})
        flow.accept_count("ls_dr9.tractor_n", {"a": 1})
        self.assertFalse(flow.rows_allowed("ls_dr9.tractor_n"))
        flow.accept_count("ls_dr9.tractor_s", {"a": 2})
        self.assertTrue(flow.rows_allowed("ls_dr9.tractor_n"))

    def test_row_cap_resource_bound_has_no_substitution(self):
        flow = science.AcquisitionSequence()
        flow.accept_schema({table: science.SOURCE_PROJECTION for table in science.REGIONAL_TABLES})
        flow.accept_count("ls_dr9.tractor_n", {"fixed": 150001})
        flow.accept_count("ls_dr9.tractor_s", {"fixed": 1})
        self.assertTrue(flow.resource_bound)
        self.assertFalse(flow.rows_allowed("ls_dr9.tractor_n"))
        self.assertEqual(flow.counts["ls_dr9.tractor_n"], 150001)

    def test_top_overflow_is_never_analyzed(self):
        science.validate_row_count(150000)
        with self.assertRaises(science.PilotIntegrityError): science.validate_row_count(150001)

    def test_row_integrity_duplicate_coordinate_and_membership(self):
        row = dict(zip(science.SOURCE_PROJECTION, (9010, 1, 2, "a", 1, 359.0, -1.0, 2.0, 3.0)))
        self.assertEqual(len(science.validate_source_rows([row], "north", {"a"})), 1)
        with self.assertRaises(science.PilotIntegrityError): science.validate_source_rows([row, row], "north", {"a"})
        bad = dict(row, ra=360.0)
        with self.assertRaises(science.PilotIntegrityError): science.validate_source_rows([bad], "north", {"a"})

    def test_spherical_distance_handles_ra_wrap(self):
        self.assertAlmostEqual(science.angular_separation_deg((359.9, 0), (0.1, 0)), 0.2, places=7)

    def test_local_k_is_two_and_terms_are_descriptive(self):
        result = science.local_two_nearest((0, 0), [("a", 1, 0), ("b", 2, 0), ("c", 3, 0)])
        self.assertEqual(len(result), 2)
        self.assertEqual(science.NEIGHBOR_RANK_COUNT, 2)
        self.assertEqual(science.LOCAL_NEAREST_TERM, "LOCAL_NEAREST_WITHIN_GUARD")
        self.assertNotIn("MATCH", science.LOCAL_RECIPROCAL_TERM)

    def test_local_reciprocity_is_boolean_topology(self):
        self.assertTrue(science.local_reciprocal("n1", "s1", {"n1": "s1"}, {"s1": "n1"}))
        self.assertFalse(science.local_reciprocal("n1", "s1", {"n1": "s1"}, {"s1": "n2"}))

    def test_quantile_grid_frozen(self):
        self.assertEqual(science.QUANTILE_GRID, (0, .05, .25, .50, .75, .95, 1))
        self.assertEqual(science.descriptive_quantiles([0, 10])["0.50"], 5)

    def test_no_matching_bound_threshold_or_group_id_algorithm(self):
        source = inspect.getsource(science)
        for forbidden in ("MATCH_RADIUS", "OBJECT_GROUP_ID", "SPLIT_GROUP_ID", "BAYES_FACTOR"):
            self.assertNotIn(forbidden, source)


class SourceMetadataBootstrapTests(unittest.TestCase):
    def test_bound_input_hashes(self):
        for path, digest in EXPECTED_INPUTS:
            self.assertEqual(file_sha256(gov.PROJECT / path), digest)

    def test_candidate_exact_argv_and_zero_bootstrap_access(self):
        candidate = validate_candidate()
        argv = expected_command_argv()
        validate_runtime_invocation(candidate, executable=argv[0], script_path=argv[1], argument_vector=argv[2:])
        self.assertEqual((candidate["network_requests"], candidate["source_rows_read"], candidate["matching_operations"]), (0, 0, 0))
        self.assertFalse(candidate["frame_materialized"])

    def test_governor_mandate_and_state_inactive(self):
        gov.validate_static_authorities(); mandate = gov.validate_mandate(); state = gov.validate_state()
        self.assertEqual(mandate["budgets"]["network_requests_parent"], 5)
        self.assertEqual(mandate["budgets"]["application_body_bytes_parent"], 67108864)
        self.assertEqual((state["state"], state["active"], state["permits_issued"]),
                         (gov.STATE_WAITING, False, 0))
        self.assertFalse(gov.STANDING_AUTHORIZATION_PATH.exists())
        self.assertFalse((gov.PROJECT / validate_candidate()["autonomy_policy"]["permit_output_path"]).exists())
        self.assertEqual(gov.evaluate_candidate(CANDIDATE),
                         {"decision": gov.MANDATE_NOT_ACTIVE, "permit_state": gov.NO_PERMIT_ISSUED})

    def test_terminal_vocabulary_exact(self):
        self.assertEqual(gov.TERMINAL_OUTCOMES, (
            "SOURCE_METADATA_DESCRIPTIVE_PILOT_COMPLETED", "SOURCE_METADATA_DESCRIPTIVE_PILOT_RESOURCE_BOUND",
            "SOURCE_METADATA_DESCRIPTIVE_PILOT_INCONCLUSIVE", "SOURCE_METADATA_DESCRIPTIVE_PILOT_INTEGRITY_FAILED"))

    def test_firewall_blocks_scientific_identity_operations(self):
        for key in ("matching_operations", "search_bound_selections", "scientific_threshold_selections",
                    "object_group_ids_created", "split_group_ids_created", "morphology_accesses"):
            self.assertIn(key, gov.FIREWALL_KEYS)

    def test_policy_core_is_generic_and_single_use_capable(self):
        source = inspect.getsource(gov)
        self.assertIn("AUTONOMOUS_PERMIT_ALREADY_CONSUMED", source)
        self.assertIn("UNRESOLVED_REGISTERED_ACTION", source)
        self.assertNotIn("MAX_SOURCE_ROWS_PER_DOMAIN", source)


class SourceMetadataGovernorLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=gov.PROJECT / "oc3")
        self.root = Path(self.tmp.name)
        self.original_consumption = gov.CONSUMPTION_ROOT
        gov.CONSUMPTION_ROOT = self.root / "ledger/PERMIT_CONSUMPTION"
        self.index = 0

    def tearDown(self):
        gov.CONSUMPTION_ROOT = self.original_consumption
        self.tmp.cleanup()

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical(value) + b"\n")
        return path

    def binding(self, path):
        return {"path": str(Path(path).resolve().relative_to(gov.PROJECT)), "sha256": file_sha256(path)}

    def candidate(self, label):
        self.index += 1
        stage, scope = f"SYNTHETIC-{label}-{self.index}", f"SYNTHETIC_{label}_ONLY"
        argv = ["synthetic", stage]
        payload = {"command_argv": argv, "command_argv_sha256": sha256_bytes(canonical(argv)),
            "implementation_aggregate": "a"*64, "schema_version": "SYNTHETIC_SOURCE_METADATA_001",
            "scope": scope, "stage_id": stage}
        payload_sha = sha256_bytes(canonical(payload))
        implementation = {"algorithm": "OC3_IMPLEMENTATION_AGGREGATE_V1", "sha256": "a"*64}
        receipt = self.write(f"receipt-{self.index}.json", sealed({
            "action_kind": label, "candidate_payload_sha256": payload_sha,
            "frozen_specification": self.binding(gov.SCIENTIFIC_SPEC_PATH),
            "implementation_binding": implementation, "network_requests": 0,
            "schema_version": "OC3_SOURCE_METADATA_DESCRIPTIVE_PILOT_ACTION_VALIDATION_RECEIPT_001",
            "scope": scope, "stage_id": stage, "validated": True,
            "validator": self.binding(gov.PROJECT / "oc3/oc3lib/source_metadata_descriptive_pilot.py")}))
        contract = {"action_kind": label, "action_validation_receipt": self.binding(receipt),
            "application_body_reservation": 0, "authority_classes_used": [gov.AUTHORITY_CLASSES[0]],
            "candidate_hash_mode": "CANONICAL_ROOT_EXCLUDING_AUTONOMY_POLICY_AND_SEALED",
            "candidate_payload_sha256": payload_sha, "command_argv_sha256": payload["command_argv_sha256"],
            "concurrency": 1, "frozen_specification": self.binding(gov.SCIENTIFIC_SPEC_PATH),
            "full_candidate_identity": "FULL_FILE_SHA256_BOUND_BY_STATE_AUTHORIZATION_PERMIT_AND_LEDGER",
            "git_assertions": {"branch": gov.AUTONOMY_BRANCH, "force_push": False, "merge_main": False},
            "implementation_binding": implementation, "network_request_reservation": 0,
            "permit_output_path": str((self.root/f"permit-{self.index}.json").relative_to(gov.PROJECT)),
            "requested_prohibited_scopes": [], "resource_manifest": None,
            "resume_policy": {"allowed": False, "prospectively_frozen": True},
            "retry_policy": {"exact_same_resource": True, "prospectively_frozen": True},
            "retry_reservation": 0, "schema_version": "OC3_SOURCE_METADATA_DESCRIPTIVE_PILOT_ACTION_CONTRACT_001",
            "scientific_firewall": {key: 0 for key in gov.FIREWALL_KEYS}, "scope": scope,
            "stage_id": stage, "standing_mandate_sha256": file_sha256(gov.MANDATE_PATH)}
        return self.write(f"candidate-{self.index}.json", sealed({**payload, "autonomy_policy": contract}))

    def activate(self, first):
        production = load_canonical_json(gov.STATE_PATH)
        body = {k:v for k,v in production.items() if k != "sealed"}
        body.update({"active": False, "first_candidate": self.binding(first), "current_stage": "FIRST_ACTION_PREPARED",
            "last_completed_stage": None, "last_terminal": None, "permits_issued": 0,
            "registered_pending_action": None, "scientific_outcome": None, "sequence": 0,
            "standing_authorization": None, "standing_authorization_initial_state_sha256": None,
            "state": gov.STATE_WAITING, "stop_reason": None})
        state = self.write("state.json", sealed(body))
        auth = self.write("authorization.json", sealed({
            "authorization_state":"STANDING_HUMAN_AUTONOMY_AUTHORIZATION", "authorized":True,
            "authorized_at_utc":"2026-09-24T20:00:00Z", "authorized_by":"Synthetic Reviewer",
            "continuation_policy":"CONTINUE_UNTIL_SCIENTIFIC_TERMINAL_OR_STOP_REQUIRES_HUMAN",
            "first_candidate_path":str(first.relative_to(gov.PROJECT)), "first_candidate_sha256":file_sha256(first),
            "initial_state_path":str(state.relative_to(gov.PROJECT)), "initial_state_sha256":file_sha256(state),
            "mandate_path":str(gov.MANDATE_PATH.relative_to(gov.PROJECT)), "mandate_sha256":file_sha256(gov.MANDATE_PATH),
            "mission_id":gov.MISSION_ID, "mission_scope":gov.MISSION_SCOPE,
            "policy_core_manifest_path":str(gov.POLICY_CORE_MANIFEST_PATH.relative_to(gov.PROJECT)),
            "policy_core_manifest_sha256":file_sha256(gov.POLICY_CORE_MANIFEST_PATH),
            "schema_version":"OC3_SOURCE_METADATA_DESCRIPTIVE_PILOT_STANDING_AUTHORIZATION_001"}))
        ledger = self.root / "ledger"
        gov.activate_standing_autonomy(state_path=state, standing_authorization_path=auth,
            ledger_directory=ledger, activated_at_utc="2026-09-24T20:01:00Z", current_branch=gov.AUTONOMY_BRANCH)
        return state, auth, ledger

    def run_action(self, candidate, state, auth, ledger, minute):
        gov.register_pending_action(state_path=state, candidate_path=candidate, standing_authorization_path=auth,
            ledger_directory=ledger, registered_at_utc=f"2026-09-24T20:{minute:02d}:00Z", current_branch=gov.AUTONOMY_BRANCH)
        permit = gov.PROJECT / gov.validate_candidate(candidate)[1]["permit_output_path"]
        gov.issue_permit(candidate_path=candidate, state_path=state, standing_authorization_path=auth,
            output_path=permit, ledger_directory=ledger, issued_at_utc=f"2026-09-24T20:{minute+1:02d}:00Z")
        gov.consume_permit(permit, candidate_path=candidate, state_path=state, standing_authorization_path=auth,
            consumed_at_utc=f"2026-09-24T20:{minute+2:02d}:00Z")
        parsed = gov.validate_candidate(candidate)[0]
        terminal = self.write(f"terminal-{minute}.json", sealed({"application_body_bytes_read":0,
            "counters":{**{key:0 for key in gov.FIREWALL_KEYS}, "network_requests_started":0, "retry_requests":0},
            "scope":parsed["scope"], "stage_id":parsed["stage_id"], "state":"SYNTHETIC_COMPLETE"}))
        gov.transition_completed_action(state_path=state, candidate_path=candidate, permit_path=permit,
            standing_authorization_path=auth, terminal_path=terminal, terminal_sha256=file_sha256(terminal),
            request_delta=0, body_delta=0, retry_delta=0, ledger_directory=ledger,
            transitioned_at_utc=f"2026-09-24T20:{minute+3:02d}:00Z", reason="SYNTHETIC_COMPLETE")
        return permit

    def test_single_use_multi_action_and_scientific_terminal(self):
        first = self.candidate("FIRST")
        state, auth, ledger = self.activate(first)
        permit = self.run_action(first, state, auth, ledger, 2)
        with self.assertRaises(gov.GovernorError) as caught:
            gov.consume_permit(permit, candidate_path=first, state_path=state,
                standing_authorization_path=auth, consumed_at_utc="2026-09-24T20:06:00Z")
        self.assertEqual(caught.exception.code, "AUTONOMOUS_PERMIT_ALREADY_CONSUMED")
        second = self.candidate("SECOND")
        self.run_action(second, state, auth, ledger, 7)
        report = self.root / "final.md"; report.write_text("synthetic final\n")
        final = gov.finalize_scientific_terminal(state_path=state, standing_authorization_path=auth,
            outcome="SOURCE_METADATA_DESCRIPTIVE_PILOT_INCONCLUSIVE", final_report_path=report,
            claim_matrix_path=None, ledger_directory=ledger, finalized_at_utc="2026-09-24T20:12:00Z",
            current_branch=gov.AUTONOMY_BRANCH)
        self.assertEqual((final["state"], final["active"], final["permits_issued"]),
                         (gov.STATE_TERMINAL, False, 2))


if __name__ == "__main__":
    unittest.main()
