"""Synthetic-only tests for the distinct PHOTSYS FITS physical-header probe."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from astropy.io import fits

import oc3_galaxy_eligibility_photsys_physical_probe as cli
from oc3lib.core import implementation_hash
import oc3lib.galaxy_eligibility_photsys_authority_probe as shared
import oc3lib.galaxy_eligibility_photsys_physical_probe as stage


def synthetic_headers(*, row_count=shared.EXPECTED_ROOT_ROWS, extra_hdu=False):
    primary = fits.Header()
    primary["SIMPLE"] = True; primary["BITPIX"] = 8; primary["NAXIS"] = 0
    primary["EXTEND"] = True
    table = fits.Header()
    table["XTENSION"] = "BINTABLE"; table["BITPIX"] = 8; table["NAXIS"] = 2
    table["NAXIS1"] = 25; table["NAXIS2"] = row_count; table["PCOUNT"] = 0
    table["GCOUNT"] = 1; table["TFIELDS"] = 5
    table["TTYPE1"] = "BRICKNAME"; table["TFORM1"] = "8A"
    table["TTYPE2"] = "NOISE"; table["TFORM2"] = "D"
    table["TTYPE3"] = "BRICKID"; table["TFORM3"] = "J"
    table["TTYPE4"] = "PHOTSYS"; table["TFORM4"] = "A"
    table["TTYPE5"] = "AREA_PER_BRICK"; table["TFORM5"] = "E"
    blocks = [primary.tostring(sep="", endcard=True, padding=True).encode("ascii"),
              table.tostring(sep="", endcard=True, padding=True).encode("ascii")]
    if extra_hdu:
        blocks.append(primary.tostring(sep="", endcard=True, padding=True).encode("ascii"))
    table_raw = 25 * row_count
    table_padded = ((table_raw + shared.HEADER_BLOCK - 1) // shared.HEADER_BLOCK) * shared.HEADER_BLOCK
    file_size = len(blocks[0]) + len(blocks[1]) + table_padded
    if extra_hdu:
        file_size += len(blocks[2])
    return blocks, file_size


class SyntheticTransport:
    blocks, file_size = synthetic_headers()
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs; self.head_requests = 0; self.range_requests = 0
        self.ranges = []; self.max_requested_byte = -1
        type(self).instances.append(self)

    def request(self, method, url, *, byte_range, max_body_bytes):
        if method == "HEAD":
            self.head_requests += 1
            return {"body": b"", "final_url": url,
                    "headers": {"accept-ranges": "bytes", "content-encoding": "identity",
                                "content-length": str(self.file_size), "etag": '"synthetic"',
                                "last-modified": "Mon, 01 Jan 2024 00:00:00 GMT"},
                    "requests_started": 1, "status": 200}
        start, end = byte_range; self.range_requests += 1; self.ranges.append(byte_range)
        self.max_requested_byte = max(self.max_requested_byte, end)
        if start == 0:
            body = self.blocks[0][:shared.HEADER_BLOCK]
        elif start == len(self.blocks[0]):
            body = self.blocks[1][:shared.HEADER_BLOCK]
        else:
            raise AssertionError("table data or unexpected byte range requested")
        return {"body": body, "final_url": url,
                "headers": {"content-encoding": "identity", "content-length": "2880",
                            "content-range": f"bytes {start}-{end}/{self.file_size}",
                            "etag": '"synthetic"'},
                "requests_started": 1, "status": 206}


def candidate_and_authorization(base: Path):
    command = ["synthetic"]
    candidate = stage.build_candidate(implementation_hash(stage.PROJECT), command)
    candidate_path = base / "candidate.json"
    authorization_path = base / "authorization.json"
    shared.write_json_immutable(candidate_path, candidate)
    argv_hash = shared.sha256_bytes(shared.canonical(command))
    shared.write_json_immutable(authorization_path, {
        "authorization_id": "synthetic", "authorization_state": "FINAL_HUMAN_AUTHORIZATION",
        "authorized": True, "candidate_sha256": shared.file_sha256(candidate_path),
        "command_argv_sha256": argv_hash, "scope": stage.SCOPE, "stage_id": stage.STAGE_ID})
    return candidate_path, authorization_path, argv_hash


class EvidenceAndCandidateTests(unittest.TestCase):
    def test_01_attempt_002_literal_binding_and_tree_are_immutable(self):
        value = stage.validate_documentary_attempt()
        self.assertEqual(value["literal_url"], stage.LITERAL_URL)
        self.assertEqual(value["directory_html_sha256"], stage.DIRECTORY_HTML_SHA256)
        self.assertEqual(value["documentary_tree_seal"], stage.DOCUMENTARY_TREE_SEAL)

    def test_02_distinct_stage_scope_and_caps(self):
        self.assertEqual(stage.STAGE_ID,
                         "OC3-GALAXY-ELIGIBILITY-PHOTSYS-AUTHORITY-PHYSICAL-PROBE-001")
        self.assertEqual(stage.SCOPE, "PHOTSYS_FITS_HEADER_CONTRACT_ONLY")
        self.assertEqual((stage.PRIMARY_LOGICAL_REQUESTS, stage.MAX_TRANSPORT_REQUESTS,
                          stage.HEADER_BODY_CAP), (29, 58, 80640))

    def test_03_candidate_binds_exact_resource_and_blocks_wider_stages(self):
        value = stage.build_candidate(implementation_hash(stage.PROJECT), ["synthetic"])
        self.assertEqual(value["resource"]["literal_url"], stage.LITERAL_URL)
        self.assertEqual(value["resource"]["resource_count"], 1)
        self.assertFalse(any(value["negative_capabilities"].values()))
        self.assertEqual(value["projection"]["status_before_real_probe"],
                         "UNOBSERVED_REAL_LAYOUT")

    def test_04_completed_probe_authorization_is_preserved(self):
        self.assertTrue(stage.AUTHORIZATION_PATH.exists())
        authorization = shared.load_canonical_json(stage.AUTHORIZATION_PATH)
        self.assertEqual(authorization["authorization_state"], "FINAL_HUMAN_AUTHORIZATION")
        self.assertEqual(authorization["candidate_sha256"],
                         shared.file_sha256(stage.CANDIDATE_PATH))

    def test_05_offline_modes_and_cli_are_network_free(self):
        with patch.object(stage, "PhysicalTransport", side_effect=AssertionError("transport")):
            self.assertEqual(stage.validate_inputs()["network_requests"], 0)
            self.assertEqual(stage.dry_run()["state"], "READY_AT_REAL_TRANSPORT_BOUNDARY")
        options = {option for action in cli.parser()._actions for option in action.option_strings}
        self.assertTrue({"--validate-inputs", "--dry-run", "--probe-physical-contract"}
                        .issubset(options))


class TransportBoundaryTests(unittest.TestCase):
    def make_transport(self):
        return object.__new__(stage.PhysicalTransport)

    def test_10_full_get_and_alternate_resource_are_rejected_before_network(self):
        transport = stage.PhysicalTransport(redirect_cap=1)
        with patch.object(stage.http.client, "HTTPSConnection",
                          side_effect=AssertionError("network")):
            with self.assertRaises(shared.PHOTSYSProbeError):
                transport.request("GET", stage.LITERAL_URL, byte_range=None,
                                  max_body_bytes=shared.HEADER_BLOCK)
            with self.assertRaises(shared.PHOTSYSProbeError):
                transport.request("HEAD", "https://example.org/x", byte_range=None,
                                  max_body_bytes=0)

    def test_11_only_one_head_is_permitted(self):
        transport = stage.PhysicalTransport(redirect_cap=1)
        transport.head_requests = 1
        with self.assertRaises(shared.PHOTSYSProbeError):
            transport.request("HEAD", stage.LITERAL_URL, byte_range=None, max_body_bytes=0)

    def test_12_ranges_are_exact_aligned_header_blocks(self):
        transport = stage.PhysicalTransport(redirect_cap=1); transport.head_requests = 1
        for byte_range in ((1, 2880), (0, 100), (0, 2879)):
            maximum = 1 if byte_range == (0, 2879) else shared.HEADER_BLOCK
            with self.assertRaises(shared.PHOTSYSProbeError):
                transport.request("GET", stage.LITERAL_URL, byte_range=byte_range,
                                  max_body_bytes=maximum)

    def test_13_redirect_to_other_destination_stops_before_second_connection(self):
        transport = stage.PhysicalTransport(redirect_cap=1)
        class Response:
            status = 302
            def getheaders(self): return [("Location", "https://example.org/x")]
        class Connection:
            def request(self, *args, **kwargs): pass
            def getresponse(self): return Response()
            def close(self): pass
        calls = []
        with patch.object(stage.http.client, "HTTPSConnection",
                          side_effect=lambda *a, **k: (calls.append(a), Connection())[1]), \
                self.assertRaises(shared.PHOTSYSProbeError):
            transport.request("HEAD", stage.LITERAL_URL, byte_range=None, max_body_bytes=0)
        self.assertEqual(len(calls), 1)


class SyntheticPhysicalProbeTests(unittest.TestCase):
    def setUp(self):
        SyntheticTransport.instances.clear()

    def run_probe(self):
        temporary = tempfile.TemporaryDirectory(); base = Path(temporary.name)
        candidate, authorization, argv_hash = candidate_and_authorization(base)
        result = stage.execute(candidate, authorization, argv_hash, base / "out",
                               transport_factory=SyntheticTransport)
        return temporary, base, result, SyntheticTransport.instances[-1]

    def test_20_full_synthetic_probe_resolves_with_no_data_byte(self):
        temporary, base, result, transport = self.run_probe()
        try:
            self.assertEqual(result["state"], stage.SUCCESS)
            self.assertEqual((transport.head_requests, transport.range_requests), (1, 2))
            self.assertEqual(transport.ranges, [(0, 2879), (2880, 5759)])
            self.assertLess(result["maximum_requested_byte"], result["first_table_data_byte"])
        finally: temporary.cleanup()

    def test_21_actual_schema_is_exhaustive_and_row_cardinality_is_frozen(self):
        temporary, base, result, transport = self.run_probe()
        try:
            contract = shared.load_canonical_json(
                base / "out/OC3_PHOTSYS_AUTHORITY_HEADER_SCHEMA_CONTRACT.json")
            structural = contract["structural_contract"]
            self.assertEqual([row["hdu_type"] for row in contract["hdu_inventory"]],
                             ["PRIMARY", "BINTABLE"])
            self.assertEqual(structural["row_count"], 662174)
            self.assertEqual([row["name"] for row in structural["column_schema"]],
                             ["BRICKNAME", "NOISE", "BRICKID", "PHOTSYS", "AREA_PER_BRICK"])
            self.assertEqual(structural["area_per_brick_cell_values_observed"], 0)
        finally: temporary.cleanup()

    def test_22_three_field_interleaved_projection_has_no_whole_row_fallback(self):
        temporary, base, result, transport = self.run_probe()
        try:
            contract = shared.load_canonical_json(
                base / "out/OC3_PHOTSYS_AUTHORITY_HEADER_SCHEMA_CONTRACT.json")
            projection = contract["structural_contract"]["selective_projection"]
            self.assertEqual(projection["row_relative_spans"],
                             [{"fields": ["BRICKNAME"], "length": 8, "offset": 0},
                              {"fields": ["BRICKID", "PHOTSYS"], "length": 5, "offset": 16}])
            self.assertFalse(projection["whole_row_fallback"])
            self.assertEqual(projection["forbidden_cell_bytes_fetched_per_row"], 0)
        finally: temporary.cleanup()

    def test_23_zero_value_firewall_and_stage_b_remain_blocked(self):
        temporary, base, result, transport = self.run_probe()
        try:
            accounting = shared.load_canonical_json(
                base / "out/OC3_PHOTSYS_AUTHORITY_RESOURCE_ACCOUNTING.json")
            terminal = shared.load_canonical_json(
                base / "out/OC3_PHOTSYS_AUTHORITY_PROBE_TERMINAL.json")
            self.assertFalse(any(accounting["forbidden_counters"].values()))
            self.assertEqual(accounting["table_cell_values_decoded"], 0)
            self.assertEqual(accounting["full_fits_gets"], 0)
            self.assertFalse(terminal["full_acquisition_authorized"])
        finally: temporary.cleanup()

    def test_24_head_blocks_hdu_schema_and_projection_are_checkpointed(self):
        temporary, base, result, transport = self.run_probe()
        try:
            values = [shared.load_canonical_json(path) for path in sorted(
                (base / "out/CHECKPOINTS").glob("[0-9][0-9][0-9][0-9].json"))]
            kinds = [value["kind"] for value in values]
            self.assertEqual(kinds[0], "FITS_HEAD_EVIDENCE")
            self.assertEqual(kinds.count("FITS_HEADER_BLOCK"), 2)
            self.assertEqual(kinds.count("HDU_STRUCTURAL_CHECKPOINT"), 2)
            self.assertIn("SCHEMA_CHECKPOINT", kinds)
            self.assertIn("PROJECTION_PLAN_CHECKPOINT", kinds)
        finally: temporary.cleanup()

    def test_25_wrong_row_count_stops_as_not_brick_level(self):
        blocks, file_size = synthetic_headers(row_count=1000)
        previous = SyntheticTransport.blocks, SyntheticTransport.file_size
        SyntheticTransport.blocks, SyntheticTransport.file_size = blocks, file_size
        try:
            with tempfile.TemporaryDirectory() as temp:
                base = Path(temp); candidate, authorization, argv_hash = candidate_and_authorization(base)
                with self.assertRaises(shared.PHOTSYSProbeError) as caught:
                    stage.execute(candidate, authorization, argv_hash, base / "out",
                                  transport_factory=SyntheticTransport)
            self.assertEqual(caught.exception.code, stage.NOT_BRICK_LEVEL)
        finally:
            SyntheticTransport.blocks, SyntheticTransport.file_size = previous

    def test_26_unexpected_hdu_structure_stops(self):
        inventory = [{"header": {"SIMPLE": True}}, {"header": {"XTENSION": "BINTABLE"}},
                     {"header": {"XTENSION": "IMAGE"}}]
        with self.assertRaises(shared.PHOTSYSProbeError) as caught:
            shared.structural_contract(inventory, {"brick_level_row_model_documented": True,
                                                   "product_identity_documented": True})
        self.assertEqual(caught.exception.code, "FITS_UNEXPECTED_HDU")

    def test_27_projection_unavailable_has_no_decode_fallback(self):
        columns = (shared.Column("BRICKNAME", "8A", 0, 8, "ascii", (8,), None, None, None, None),)
        with self.assertRaises(shared.PHOTSYSProbeError) as caught:
            shared.projection_plan(columns)
        self.assertEqual(caught.exception.code, shared.PROJECTION_UNAVAILABLE)

    def test_28_partial_failure_remains_durably_reviewable(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp); checkpoints = stage.PhysicalCheckpoints(base / "CHECKPOINTS")
            checkpoints.record(1, {"kind": "FITS_HEAD_EVIDENCE",
                                   "network_body_bytes": 0, "network_requests_started": 1})
            checkpoints.record(2, {"kind": "FITS_HEADER_BLOCK",
                                   "network_body_bytes": 2880, "network_requests_started": 2})
            stage.persist_failure_terminal(base, "SYNTHETIC_STOP")
            terminal = shared.load_canonical_json(
                base / "OC3_PHOTSYS_AUTHORITY_PROBE_TERMINAL.json")
            accounting = shared.load_canonical_json(
                base / "OC3_PHOTSYS_AUTHORITY_RESOURCE_ACCOUNTING.json")
        self.assertEqual(terminal["first_error"], "SYNTHETIC_STOP")
        self.assertEqual((accounting["header_blocks"], accounting["network_body_bytes"]),
                         (1, 2880))
        self.assertEqual(accounting["table_cell_values_decoded"], 0)

    def test_29_panel_v2_p1_and_acquisition_are_absent(self):
        value = stage.build_candidate(implementation_hash(stage.PROJECT), ["synthetic"])
        for key in ("panel_v2", "p1", "stage_b_acquisition"):
            self.assertFalse(value["negative_capabilities"][key])


if __name__ == "__main__":
    unittest.main()
