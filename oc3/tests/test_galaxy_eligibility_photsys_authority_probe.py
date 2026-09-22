"""Synthetic-only tests for the bounded PHOTSYS authority probe."""
from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from astropy.io import fits

import oc3_galaxy_eligibility_photsys_authority_probe as cli
import oc3lib.galaxy_eligibility_photsys_authority_probe as stage


def official_html(link: str | None = None, *, brick_level: bool = True) -> bytes:
    href = f'<a href="{link}">{stage.TARGET_FILENAME}</a>' if link else stage.TARGET_FILENAME
    row = "One row per brick." if brick_level else "Random point rows."
    return (f"<html>{href} survey-bricks fields plus PHOTSYS AREA_PER_BRICK. {row} "
            "PHOTSYS values: <code>N</code> <code>S</code> and blank space. "
            "The north and south imaging footprints overlap.</html>").encode()


def manifest_value():
    return stage.sealed({
        "broad_web_crawling": False,
        "resources": [
            {"document_id": "DR9_FILES", "literal_url": stage.DOCUMENTARY_ALLOWLIST[0],
             "max_body_bytes": stage.DOCUMENTARY_BODY_PER_RESOURCE,
             "provider": "Legacy Surveys DR9",
             "required_evidence": ["exact product identity", "literal official data link"],
             "resolution_state": "PENDING_AUTHORIZED_DOCUMENTARY_RETRIEVAL"},
            {"document_id": "DR9_CATALOGS", "literal_url": stage.DOCUMENTARY_ALLOWLIST[1],
             "max_body_bytes": stage.DOCUMENTARY_BODY_PER_RESOURCE,
             "provider": "Legacy Surveys DR9",
             "required_evidence": ["brick-level role", "PHOTSYS values", "overlap semantics"],
             "resolution_state": "PENDING_AUTHORIZED_DOCUMENTARY_RETRIEVAL"},
        ],
        "schema_version": "OC3_PHOTSYS_AUTHORITY_DOCUMENTARY_MANIFEST_001",
        "scope": stage.SCOPE,
        "stage_id": stage.STAGE_ID,
    })


def documents(link: str | None = None, *, brick_level: bool = True):
    body = official_html(link, brick_level=brick_level)
    return ({"source_url": stage.DOCUMENTARY_ALLOWLIST[0], "body": body},
            {"source_url": stage.DOCUMENTARY_ALLOWLIST[1], "body": body})


def header_inventory(*, row_count=stage.EXPECTED_ROOT_ROWS, extra=False, brick_level=True):
    primary = {"SIMPLE": True, "BITPIX": 8, "NAXIS": 0}
    table = {"XTENSION": "BINTABLE", "BITPIX": 8, "NAXIS": 2, "NAXIS1": 25,
             "NAXIS2": row_count, "PCOUNT": 0, "GCOUNT": 1, "TFIELDS": 5,
             "TTYPE1": "BRICKNAME", "TFORM1": "8A", "TTYPE2": "NOISE", "TFORM2": "D",
             "TTYPE3": "BRICKID", "TFORM3": "J", "TTYPE4": "PHOTSYS", "TFORM4": "A",
             "TTYPE5": "AREA_PER_BRICK", "TFORM5": "E"}
    result = [{"hdu_index": 0, "header": primary, "data_offset": 2880},
              {"hdu_index": 1, "header": table, "data_offset": 5760}]
    if extra:
        result.append({"hdu_index": 2, "header": primary, "data_offset": 8640})
    return result, stage.documentary_facts(documents(
        "https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/randoms/" + stage.TARGET_FILENAME,
        brick_level=brick_level))


class DocumentaryTests(unittest.TestCase):
    def test_01_closed_allowlist(self):
        self.assertEqual(stage.DOCUMENTARY_ALLOWLIST,
                         ("https://www.legacysurvey.org/dr9/files/",
                          "https://www.legacysurvey.org/dr9/catalogs/"))

    def test_02_exact_target_filename(self):
        self.assertEqual(stage.TARGET_FILENAME, "survey-bricks-dr9-randoms-0.48.0.fits")
        for wrong in ("randoms-1-0.fits", "randoms-allsky-1.fits",
                      "randoms-outside-1.fits", "survey-bricks-dr9-randoms-0.49.0.fits"):
            self.assertFalse(stage.is_official_literal_url(
                "https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/" + wrong))

    def test_03_literal_url_requires_explicit_href(self):
        url = "https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/randoms/" + stage.TARGET_FILENAME
        self.assertEqual(stage.resolve_literal_url_from_documents(documents(url)), url)
        with self.assertRaises(stage.PHOTSYSProbeError) as caught:
            stage.resolve_literal_url_from_documents(documents(None))
        self.assertEqual(caught.exception.code, "LITERAL_URL_NOT_DOCUMENTED")

    def test_04_mirror_and_unrelated_catalog_rejected(self):
        for url in ("https://example.org/" + stage.TARGET_FILENAME,
                    "https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/randoms/randoms-1-0.fits"):
            with self.assertRaises(stage.PHOTSYSProbeError):
                stage.resolve_literal_url_from_documents(documents(url))

    def test_05_exact_document_semantics(self):
        facts = stage.documentary_facts(documents())
        self.assertTrue(facts["product_identity_documented"])
        self.assertTrue(facts["brick_level_row_model_documented"])
        self.assertTrue(facts["photsys_exact_values_documented"])
        self.assertTrue(facts["north_south_overlap_documented"])

    def test_06_canonical_manifest_validation_and_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            stage.write_json_immutable(path, manifest_value())
            with patch.object(stage, "DOCUMENTARY_MANIFEST", path):
                value = stage.validate_documentary_manifest(path)
            self.assertEqual(value["sealed"], manifest_value()["sealed"])
            self.assertEqual(stage.file_sha256(path), stage.sha256_bytes(path.read_bytes()))

    def test_07_wrong_document_allowlist_rejected(self):
        value = manifest_value(); value = {k: v for k, v in value.items() if k != "sealed"}
        value["resources"][0]["literal_url"] = "https://www.legacysurvey.org/dr8/files/"
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "x.json"; stage.write_json_immutable(path, stage.sealed(value))
            with self.assertRaises(stage.PHOTSYSProbeError): stage.validate_documentary_manifest(path)


class FITSStructureTests(unittest.TestCase):
    def test_10_exact_tform_offsets_and_shapes(self):
        inventory, facts = header_inventory()
        result = stage.structural_contract(inventory, facts)
        schema = result["column_schema"]
        self.assertEqual([(x["name"], x["offset"], x["width"]) for x in schema],
                         [("BRICKNAME", 0, 8), ("NOISE", 8, 8), ("BRICKID", 16, 4),
                          ("PHOTSYS", 20, 1), ("AREA_PER_BRICK", 21, 4)])
        self.assertEqual(schema[0]["shape"], [8])

    def test_11_selective_projection_minimal_interleaved_spans(self):
        inventory, facts = header_inventory()
        projection = stage.structural_contract(inventory, facts)["selective_projection"]
        self.assertEqual(projection["row_relative_spans"],
                         [{"fields": ["BRICKNAME"], "length": 8, "offset": 0},
                          {"fields": ["BRICKID", "PHOTSYS"], "length": 5, "offset": 16}])
        self.assertEqual(projection["forbidden_cell_bytes_fetched_per_row"], 0)
        self.assertFalse(projection["whole_row_fallback"])

    def test_12_area_structural_only(self):
        result = stage.structural_contract(*header_inventory())
        self.assertEqual(result["area_per_brick_cell_values_observed"], 0)
        self.assertNotIn(stage.STRUCTURAL_ONLY_FIELD,
                         result["selective_projection"]["allowed_fields"])

    def test_13_missing_allowed_field_fails_closed(self):
        inventory, facts = header_inventory()
        inventory[1]["header"]["TTYPE4"] = "OTHER"
        with self.assertRaises(stage.PHOTSYSProbeError) as caught:
            stage.structural_contract(inventory, facts)
        self.assertEqual(caught.exception.code, stage.NOT_BRICK_LEVEL)

    def test_14_random_point_row_count_rejected(self):
        with self.assertRaises(stage.PHOTSYSProbeError) as caught:
            stage.structural_contract(*header_inventory(row_count=1000))
        self.assertEqual(caught.exception.code, stage.NOT_BRICK_LEVEL)

    def test_15_documented_row_model_required(self):
        with self.assertRaises(stage.PHOTSYSProbeError) as caught:
            stage.structural_contract(*header_inventory(brick_level=False))
        self.assertEqual(caught.exception.code, stage.NOT_BRICK_LEVEL)

    def test_16_unexpected_hdu_rejected(self):
        with self.assertRaises(stage.PHOTSYSProbeError) as caught:
            stage.structural_contract(*header_inventory(extra=True))
        self.assertEqual(caught.exception.code, "FITS_UNEXPECTED_HDU")

    def test_17_malformed_schema_rejected(self):
        inventory, facts = header_inventory(); inventory[1]["header"]["NAXIS1"] = 26
        with self.assertRaises(stage.PHOTSYSProbeError) as caught:
            stage.structural_contract(inventory, facts)
        self.assertEqual(caught.exception.code, "FITS_ROW_WIDTH_MISMATCH")

    def test_18_null_scaling_units_retained(self):
        inventory, facts = header_inventory(); header = inventory[1]["header"]
        header.update({"TNULL3": -1, "TSCAL3": 2, "TZERO3": 4, "TUNIT3": "id"})
        brickid = stage.structural_contract(inventory, facts)["column_schema"][2]
        self.assertEqual((brickid["tnull"], brickid["tscal"], brickid["tzero"], brickid["unit"]),
                         (-1, 2, 4, "id"))

    def test_19_probe_stops_at_headers_and_skips_table_data(self):
        primary = fits.PrimaryHDU()
        table = fits.BinTableHDU.from_columns([
            fits.Column(name="BRICKNAME", format="8A", array=np.array([b"0001p000"])),
            fits.Column(name="BRICKID", format="J", array=np.array([1], dtype=np.int32)),
            fits.Column(name="PHOTSYS", format="A", array=np.array([b"N"])),
            fits.Column(name="AREA_PER_BRICK", format="E", array=np.array([1.0], dtype=np.float32)),
        ])
        buffer = io.BytesIO(); fits.HDUList([primary, table]).writeto(buffer)
        payload = buffer.getvalue(); ranges = []
        class Transport:
            def request(self, method, url, *, byte_range, max_body_bytes):
                start, end = byte_range; ranges.append(byte_range); body = payload[start:end + 1]
                return {"body": body, "final_url": url,
                        "headers": {"content-range": f"bytes {start}-{end}/{len(payload)}"},
                        "requests_started": 1, "status": 206}
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            inventory, used = stage.probe_hdu_inventory(
                Transport(), stage.Budget(4, 4 * 2880, 4 * 2880),
                stage.Checkpoints(base / "checkpoints"), base / "raw",
                url="https://portal.nersc.gov/x.fits", file_size=len(payload), header_block_cap=4)
        self.assertEqual((len(inventory), used), (2, 2))
        self.assertEqual(ranges, [(0, 2879), (2880, 5759)])
        self.assertNotIn((5760, 8639), ranges)

    def test_20_range_mismatch_rejected(self):
        class Transport:
            def request(self, *args, **kwargs):
                return {"body": b" " * 2880, "final_url": "x",
                        "headers": {"content-range": "bytes 1-2880/5760"},
                        "requests_started": 1, "status": 206}
        with tempfile.TemporaryDirectory() as temp, self.assertRaises(stage.PHOTSYSProbeError) as caught:
            base = Path(temp); stage.probe_hdu_inventory(
                Transport(), stage.Budget(2, 5760, 5760), stage.Checkpoints(base / "c"), base / "r",
                url="https://portal.nersc.gov/x", file_size=5760, header_block_cap=2)
        self.assertEqual(caught.exception.code, "RANGE_MISMATCH")

    def test_21_header_block_cap(self):
        class Transport:
            def request(self, *args, **kwargs):
                return {"body": b" " * 2880, "final_url": "x",
                        "headers": {"content-range": "bytes 0-2879/5760"},
                        "requests_started": 1, "status": 206}
        with tempfile.TemporaryDirectory() as temp, self.assertRaises(stage.PHOTSYSProbeError):
            base = Path(temp); stage.probe_hdu_inventory(
                Transport(), stage.Budget(1, 2880, 2880), stage.Checkpoints(base / "c"), base / "r",
                url="https://portal.nersc.gov/x", file_size=5760, header_block_cap=1)


class ControlBoundaryTests(unittest.TestCase):
    def test_30_zeroed_firewall_counters(self):
        counters = stage.Counters().object()
        self.assertEqual(counters, {name: 0 for name in counters})
        self.assertEqual(len(counters), 7)

    def test_31_tightened_envelopes(self):
        self.assertEqual(stage.DOCUMENTARY_REQUEST_CAP, 4)
        self.assertEqual(stage.DOCUMENTARY_BODY_CAP, 1024 * 1024)
        self.assertLessEqual(stage.FULL_REQUEST_CAP, 72)
        self.assertLessEqual(stage.FULL_BODY_CAP, 2 * 1024 * 1024)
        self.assertEqual(stage.MAX_REDIRECTS, 1)

    def test_32_budget_request_and_byte_caps(self):
        budget = stage.Budget(1, 10, 5)
        with self.assertRaises(stage.PHOTSYSProbeError):
            budget.preflight(maximum=1, is_range=False, request_envelope=2)
        with self.assertRaises(stage.PHOTSYSProbeError):
            budget.charge({"body": b"123456", "requests_started": 1}, maximum=6, is_range=True)
        with self.assertRaises(stage.PHOTSYSProbeError):
            budget.charge({"body": b"", "requests_started": 2}, maximum=0, is_range=False)

    def test_33_atomic_checkpoint_index(self):
        with tempfile.TemporaryDirectory() as temp:
            checkpoint = stage.Checkpoints(Path(temp))
            checkpoint.record(1, {"kind": "DOC"}); checkpoint.record(2, {"kind": "HEAD"})
            value = stage.load_canonical_json(Path(temp) / "CHECKPOINT_INDEX.json")
            self.assertEqual(value["completed_count"], 2)
            self.assertFalse((Path(temp) / ".CHECKPOINT_INDEX.tmp").exists())

    def test_34_authorization_precedes_transport(self):
        constructed = []
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp); candidate = base / "candidate.json"
            stage.write_json_immutable(candidate, stage.sealed({"stage_id": stage.STAGE_ID}))
            with self.assertRaises(stage.PHOTSYSProbeError):
                stage.probe_resource_contract(candidate, base / "missing.json", "a" * 64, base / "out",
                                              transport_factory=lambda **kwargs: constructed.append(True))
        self.assertEqual(constructed, [])

    def test_35_documentary_execution_retains_hash_and_decodes_zero_cells(self):
        class Transport:
            def __init__(self, **kwargs): pass
            def request(self, method, url, *, byte_range, max_body_bytes):
                body = official_html(None)
                return {"body": body, "final_url": url,
                        "headers": {"content-length": str(len(body))},
                        "requests_started": 1, "status": 200}
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp); manifest = base / "manifest.json"
            stage.write_json_immutable(manifest, manifest_value())
            candidate_path = base / "candidate.json"; authorization = base / "auth.json"
            command = ["--probe-resource-contract", "--candidate", str(candidate_path),
                       "--authorization", str(authorization), "--output-directory", str(base / "out")]
            with patch.object(stage, "DOCUMENTARY_MANIFEST", manifest):
                candidate = stage.build_documentary_candidate(
                    manifest_value(), "a" * 64, command)
            stage.write_json_immutable(candidate_path, candidate)
            argv_hash = stage.sha256_bytes(stage.canonical(command))
            stage.write_json_immutable(authorization, {
                "authorization_id": "synthetic", "authorization_state": "FINAL_HUMAN_AUTHORIZATION",
                "authorized": True, "candidate_sha256": stage.file_sha256(candidate_path),
                "command_argv_sha256": argv_hash, "scope": stage.SCOPE, "stage_id": stage.STAGE_ID})
            result = stage.probe_resource_contract(candidate_path, authorization, argv_hash, base / "out",
                                                   transport_factory=Transport)
            documentary = stage.load_canonical_json(
                base / "out/OC3_PHOTSYS_AUTHORITY_DOCUMENTARY_MANIFEST.json")
        self.assertEqual(result["state"], stage.INCONCLUSIVE)
        self.assertEqual(result["table_cell_values_decoded"], 0)
        self.assertEqual(documentary["documents"][0]["content_sha256"],
                         stage.sha256_bytes(official_html(None)))

    def test_36_no_rerun_or_automatic_resume(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp); manifest = base / "manifest.json"
            stage.write_json_immutable(manifest, manifest_value())
            candidate_path = base / "candidate.json"; authorization = base / "auth.json"
            command = ["x"]
            with patch.object(stage, "DOCUMENTARY_MANIFEST", manifest):
                candidate = stage.build_documentary_candidate(manifest_value(), "a" * 64, command)
            stage.write_json_immutable(candidate_path, candidate)
            argv_hash = stage.sha256_bytes(stage.canonical(command))
            stage.write_json_immutable(authorization, {
                "authorization_id": "synthetic", "authorization_state": "FINAL_HUMAN_AUTHORIZATION",
                "authorized": True, "candidate_sha256": stage.file_sha256(candidate_path),
                "command_argv_sha256": argv_hash, "scope": stage.SCOPE, "stage_id": stage.STAGE_ID})
            (base / "out").mkdir(); constructed = []
            with self.assertRaises(stage.PHOTSYSProbeError) as caught:
                stage.probe_resource_contract(candidate_path, authorization, argv_hash, base / "out",
                                              transport_factory=lambda **kwargs: constructed.append(True))
            self.assertEqual(caught.exception.code, "AUTOMATIC_RERUN_OR_RESUME_FORBIDDEN")
            self.assertEqual(constructed, [])

    def test_36b_partial_failure_terminal_is_durable(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp); checkpoints = stage.Checkpoints(base / "CHECKPOINTS")
            checkpoints.record(1, {"kind": "DOCUMENT", "network_body_bytes": 17,
                                   "network_requests_started": 1})
            stage.persist_failure_terminal(base, "SYNTHETIC_STOP")
            terminal = stage.load_canonical_json(base / "OC3_PHOTSYS_AUTHORITY_PROBE_TERMINAL.json")
            accounting = stage.load_canonical_json(
                base / "OC3_PHOTSYS_AUTHORITY_RESOURCE_ACCOUNTING.json")
            self.assertEqual(terminal["first_error"], "SYNTHETIC_STOP")
            self.assertEqual(accounting["body_bytes"], 17)

    def test_37_cli_modes(self):
        options = {option for action in cli.parser()._actions for option in action.option_strings}
        self.assertTrue({"--help", "--validate-inputs", "--dry-run",
                         "--probe-resource-contract"}.issubset(options))

    def test_38_historical_v1_evidence_immutable(self):
        self.assertEqual(stage.file_sha256(stage.HISTORICAL_REPORT), stage.HISTORICAL_REPORT_SHA256)
        text = stage.HISTORICAL_REPORT.read_text()
        self.assertIn("P0_DUPLICATE_REGIONAL_IDENTITY", text)
        self.assertIn("GALAXY_ELIGIBILITY_PANEL_BINDING_FAILED", text)

    def test_39_stage_boundary_blocks_panel_and_other_transports(self):
        candidate = stage.sealed({
            "authorization_state": "FINAL_HUMAN_AUTHORIZATION_ABSENT",
            "candidate_scope": "MINIMUM_DOCUMENTARY_BINDING_ONLY",
            "command_argv": [], "command_argv_sha256": stage.sha256_bytes(stage.canonical([])),
            "documentary_manifest_sha256": "a" * 64,
            "documentary_resources": manifest_value()["resources"],
            "expected_terminals": [stage.INCONCLUSIVE, stage.FAILED],
            "implementation_aggregate": "b" * 64, "literal_official_url": None,
            "negative_capabilities": {"acquire_photsys_file": False, "decode_table_cells": False,
                                      "full_fits_get": False, "panel_v1": False, "panel_v2": False,
                                      "tractor_sdss_gaia_desi": False},
            "policy": {"automatic_retries": 0, "body_bytes_cap": stage.DOCUMENTARY_BODY_CAP,
                       "concurrency": 1, "data_head_requests": 0, "header_block_cap": 0,
                       "per_document_body_bytes": stage.DOCUMENTARY_BODY_PER_RESOURCE,
                       "per_resource_range_body_bytes": 0,
                       "redirects_per_request": stage.MAX_REDIRECTS,
                       "request_cap": stage.DOCUMENTARY_REQUEST_CAP},
            "scope": stage.SCOPE, "stage_id": stage.STAGE_ID,
            "target_filename": stage.TARGET_FILENAME})
        stage.validate_candidate(candidate)
        self.assertFalse(any(candidate["negative_capabilities"].values()))


if __name__ == "__main__":
    unittest.main()
