"""Offline regression for the prospective OC-3 stage-local request budget."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import oc3_resource_contract as cli
import oc3lib.resource_contract as stage
from oc3lib.core import canonical


PROJECT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (PROJECT /
    "oc3/resource_contract/OC3-RESOURCE-CONTRACT-PROBE-002/RESOURCE_CONTRACT_RESOLVED.json")
CANDIDATE_PATH = PROJECT / stage.AUXILIARY_CANDIDATE_RELATIVE


def contract():
    return stage.load_canonical_json(CONTRACT_PATH)


def candidate(value=None):
    return stage.build_acquisition_candidate(value or contract(), PROJECT)


def authorization(value, *, resume=False):
    return stage._seal({
        "schema_version": stage.ACQUISITION_AUTHORIZATION_SCHEMA,
        "authorization_type": "AUXILIARY_14_ACQUISITION_FINAL_HUMAN_AUTHORIZATION",
        "authorization_state": "FINAL_HUMAN_AUTHORIZATION", "authorized": True,
        "authorized_by": "synthetic test", "authorized_at_utc": "2026-09-21T00:00:00Z",
        "stage_id": stage.STAGE_ID, "scope": "AUXILIARY_14_ONLY",
        "candidate_path": str(CANDIDATE_PATH.resolve()),
        "candidate_sha256": hashlib.sha256(canonical(value) + b"\n").hexdigest(),
        "resume": resume,
    })


class DriftTransport:
    def __init__(self, value):
        self.rows = {row["literal_url"]: row for row in value["resources"]}
        self.calls = []

    def head(self, url):
        self.calls.append(("HEAD", url)); row = self.rows[url]
        return 200, {"content-length": str(row["expected_content_length"]),
                     "etag": '"drift"'}, b"", url

    def get(self, url, max_bytes):
        self.calls.append(("GET", url)); raise AssertionError("GET must not start")


def descriptors(paths, value):
    return []


class NetworkRequestBudgetTests(unittest.TestCase):
    def test_01_imports_exact_cumulative_counters(self):
        value = candidate()
        self.assertEqual(value["starting_cumulative"],
                         {"requests": 166, "body_bytes": 89_836_046})

    def test_02_historical_counter_reset_rejected(self):
        value = candidate(); value["starting_cumulative"]["requests"] = 0
        value = stage._seal(value)
        with self.assertRaisesRegex(stage.ResourceContractError, "ACQUISITION_CANDIDATE_INVALID"):
            stage.validate_acquisition_candidate(value, contract(), PROJECT)

    def test_03_global_body_cap_unchanged(self):
        self.assertEqual(stage.GLOBAL_MAX_BYTES, 1_610_612_736)
        self.assertEqual(candidate()["global_caps"]["body_bytes"], 1_610_612_736)

    def test_04_historical_200_not_future_stage_gate(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "ledger.json"; state = stage._load_state(path)
            state["used_requests"] = 200
            attempt = stage._reserve_stage_request(path, state, "fresh", "HEAD")
            self.assertEqual(state["used_requests"], 201)
            self.assertFalse(attempt["retry"])

    def test_05_stage_cap_is_mandatory_in_candidate(self):
        value = candidate(); del value["retry_policy"]["stage_request_cap"]
        value = stage._seal(value)
        with self.assertRaisesRegex(stage.ResourceContractError, "ACQUISITION_CANDIDATE_INVALID"):
            stage.validate_acquisition_candidate(value, contract(), PROJECT)

    def test_06_primary_plan_retry_pool_and_cap(self):
        value = candidate()
        self.assertEqual(value["primary_requests"], {"head": 14, "get": 14, "total": 28})
        self.assertEqual(value["retry_policy"]["stage_retry_request_pool"], 6)
        self.assertEqual(value["retry_policy"]["stage_request_cap"], 34)

    def test_07_request_35_fails_before_transport(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "ledger.json"; state = stage._load_state(path)
            state["attempts"] = [{"resource_id": f"r{i}", "method": "HEAD"} for i in range(34)]
            state["stage_requests"] = 34; state["used_requests"] += 34
            with self.assertRaisesRegex(stage.ResourceContractError, "STAGE_REQUEST_CAP_EXCEEDED"):
                stage._reserve_stage_request(path, state, "new", "HEAD")
            self.assertEqual(state["stage_requests"], 34)

    def test_08_per_identity_retry_limit_still_applies(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "ledger.json"; state = stage._load_state(path)
            for _ in range(3): stage._reserve_stage_request(path, state, "r", "GET")
            with self.assertRaisesRegex(stage.ResourceContractError, "RETRY_LIMIT"):
                stage._reserve_stage_request(path, state, "r", "GET")

    def test_09_retry_consumes_stage_and_cumulative_count(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "ledger.json"; state = stage._load_state(path)
            stage._reserve_stage_request(path, state, "r", "GET")
            stage._reserve_stage_request(path, state, "r", "GET")
            self.assertEqual(state["stage_requests"], 2)
            self.assertEqual(state["stage_retry_requests"], 1)
            self.assertEqual(state["used_requests"], 168)

    def test_10_exact_14_lengths_and_total(self):
        value = candidate()
        self.assertEqual(len(value["resources"]), 14)
        self.assertEqual(sum(row["expected_content_length"] for row in value["resources"]),
                         3_827_520)

    def test_11_unresolved_contract_rejected(self):
        value = contract(); value["resources"][0]["max_bytes"] = stage._prop("UNRESOLVED", None)
        value = stage._seal(value)
        with self.assertRaises(stage.ResourceContractError):
            stage.build_acquisition_candidate(value, PROJECT)

    def test_12_representation_drift_stops_before_get(self):
        resolved = contract(); proposal = candidate(resolved); transport = DriftTransport(proposal)
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(stage.ResourceContractError, "AUXILIARY_REPRESENTATION_DRIFT"):
                stage.acquire_auxiliary(
                    resolved, proposal, authorization(proposal), transport, Path(td), descriptors,
                    project=PROJECT, candidate_path=CANDIDATE_PATH)
        self.assertEqual([call[0] for call in transport.calls], ["HEAD"])

    def test_13_resolved_contract_reused_without_probe(self):
        with patch.object(stage, "probe_contract", side_effect=AssertionError("reprobe forbidden")):
            stage.validate_acquisition_candidate(candidate(), contract(), PROJECT)

    def test_14_candidate_never_authorizes_transport(self):
        value = candidate()
        self.assertNotIn("authorized", value)
        self.assertEqual(value["candidate_state"], "PENDING_HUMAN_REVIEW")
        self.assertFalse(value["negative_capabilities"]["location_selection"])
        self.assertFalse(value["negative_capabilities"]["image_invvar_acquisition"])

    def test_15_retry_pool_cannot_be_widened(self):
        value = candidate(); value["retry_policy"]["stage_retry_request_pool"] = 7
        value = stage._seal(value)
        with self.assertRaisesRegex(stage.ResourceContractError, "ACQUISITION_CANDIDATE_INVALID"):
            stage.validate_acquisition_candidate(value, contract(), PROJECT)

    def test_16_candidate_validation_is_offline(self):
        with patch.object(stage.LiteralHTTPTransport, "__init__", side_effect=AssertionError("network")):
            stage.validate_acquisition_candidate(candidate(), contract(), PROJECT)

    def test_17_candidate_schema_is_closed(self):
        schema = json.loads((PROJECT /
            "oc3/schemas/oc3_auxiliary_14_acquisition_candidate_001.schema.json").read_text())
        self.assertFalse(schema["additionalProperties"])
        self.assertFalse(schema["$defs"]["resource"]["additionalProperties"])

    def test_18_production_candidate_is_canonical_and_valid(self):
        raw = CANDIDATE_PATH.read_bytes(); value = json.loads(raw)
        self.assertEqual(raw, canonical(value) + b"\n")
        stage.validate_acquisition_candidate(value, contract(), PROJECT)

    def test_19_cli_candidate_validation_constructs_no_transport(self):
        argv = ["--validate-auxiliary-candidate", "--project", str(PROJECT),
                "--contract-manifest", str(CONTRACT_PATH), "--candidate", str(CANDIDATE_PATH)]
        with patch.object(stage.LiteralHTTPTransport, "__init__", side_effect=AssertionError("network")), \
                patch("builtins.print"):
            self.assertEqual(cli.main(argv), 0)

    def test_20_candidate_cannot_serve_as_final_authorization(self):
        value = candidate()
        with self.assertRaisesRegex(stage.ResourceContractError, "ACQUISITION_AUTHORIZATION_INVALID"):
            stage.validate_acquisition_authorization(
                value, value, candidate_path=CANDIDATE_PATH, resume=False)

    def test_21_candidate_binds_distinct_final_authorization_path(self):
        value = candidate()
        self.assertEqual(value["final_authorization_path"],
                         str((PROJECT / stage.AUXILIARY_AUTHORIZATION_RELATIVE).resolve()))
        self.assertNotEqual(Path(value["final_authorization_path"]), CANDIDATE_PATH)


if __name__ == "__main__":
    unittest.main()
