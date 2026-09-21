"""Synthetic/offline tests for the bounded galaxy-eligibility probe."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from astropy.io import fits

import oc3_galaxy_eligibility_resource_schema_probe as cli
import oc3lib.galaxy_eligibility_resource_schema_probe as stage


def geometry(seed: int) -> tuple[float, float, float, float, float, float]:
    ra = float(seed % 300) + 0.5
    dec = float(seed % 100) / 10 - 5
    return (ra, dec, ra - .1, ra + .1, dec - .1, dec + .1)


def name_for(region: str, index: int) -> str:
    prefix = 1000 + index if region == "north" else 2000 + index
    return f"{prefix:04d}{'p' if region == 'north' else 'm'}{index:03d}"


def rows(count: int = 10):
    roots = []
    regional = {"north": [], "south": []}
    for region_index, region in enumerate(("north", "south")):
        for index in range(count):
            name = name_for(region, index).encode("ascii")
            brickid = 10_000 * (region_index + 1) + index
            geom = geometry(brickid)
            roots.append(stage.RootRow(name, brickid, geom))
            regional[region].append(stage.RegionalRow(
                region, name, brickid, geom, 0.25, True, (1, 1, 1)))
    return tuple(roots), tuple(regional["north"]), tuple(regional["south"])


def documentary_manifest():
    return stage.sealed_object({
        "broad_web_crawling": False,
        "resources": [
            {"content_sha256": None, "expected_semantics": ["a"], "max_body_bytes": 524288,
             "provider": "Legacy Surveys DR9", "resolution_state": "UNRESOLVED_PENDING_AUTHORIZED_P1",
             "retrieval_role": "TRACTOR_CATALOG_AND_C1_SCHEMA", "retrieval_timestamp_utc": None,
             "url": "https://www.legacysurvey.org/dr9/catalogs/"},
            {"content_sha256": None, "expected_semantics": ["b"], "max_body_bytes": 524288,
             "provider": "Legacy Surveys DR9", "resolution_state": "UNRESOLVED_PENDING_AUTHORIZED_P1",
             "retrieval_role": "B1_EXTERNAL_MATCH_FILES_AND_SEMANTICS", "retrieval_timestamp_utc": None,
             "url": "https://www.legacysurvey.org/dr9/files/"},
        ],
        "schema_version": "OC3_GALAXY_ELIGIBILITY_DOCUMENTARY_MANIFEST_001",
        "stage_id": stage.STAGE_ID,
    })


def authority_binding():
    return {"authorities": [{"path": "x", "role": "ROOT_SUMMARY", "sha256": "a" * 64}],
            "specification_sha256": stage.SPEC_SHA256}


class GalaxyEligibilityPanelTests(unittest.TestCase):
    def setUp(self):
        self.roots, self.north, self.south = rows()
        self.fixtures = frozenset()

    def test_01_frozen_authority_hashes(self):
        self.assertEqual(stage.SPEC_SHA256,
                         "db80f8fefda0aad4a7e1cea4fb3e32bca0f238d33d2a52cbaf72af5da9ec5f17")
        self.assertEqual(len(stage.EXPECTED_AUTHORITIES), 4)

    def test_02_exact_allowed_summary_fields(self):
        self.assertEqual(stage.ROOT_ALLOWED_FIELDS,
                         ("BRICKNAME", "BRICKID", "RA", "DEC", "RA1", "RA2", "DEC1", "DEC2"))
        self.assertEqual(stage.REGIONAL_ALLOWED_FIELDS,
                         ("brickname", "brickid", "ra", "dec", "ra1", "ra2", "dec1", "dec2",
                          "area", "survey_primary", "nexp_g", "nexp_r", "nexp_z"))
        forbidden = {"nobjs", "npsf", "psfsize_g", "galdepth_r", "ebv", "trans_g"}
        self.assertTrue(forbidden.isdisjoint(stage.REGIONAL_ALLOWED_FIELDS))

    def test_03_fixture_exclusion_derived_from_file(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "fixtures.csv"
            path.write_text("region,brickname,development,holdout_disjoint,evidence_ref\n"
                            "north,1000p000,true,true,fixture\n", encoding="ascii")
            self.assertEqual(stage.load_fixture_exclusions(path), frozenset({("north", "1000p000")}))

    def test_04_exact_eight_plus_eight(self):
        panel, evidence = stage.select_panel(self.roots, self.north, self.south, self.fixtures)
        self.assertEqual((len(panel), sum(x.region == "north" for x in panel),
                          sum(x.region == "south" for x in panel)), (16, 8, 8))
        self.assertEqual(evidence["tie_count"], 0)

    def test_05_low_cardinality_fails(self):
        with self.assertRaises(stage.EligibilityProbeError) as caught:
            stage.select_panel(self.roots, self.north[:7], self.south, self.fixtures)
        self.assertEqual(caught.exception.code, "P0_LOW_CARDINALITY")

    def test_06_duplicate_brickname_and_brickid_fail(self):
        for duplicate in (replace(self.north[-1], brickname=self.north[0].brickname),
                          replace(self.north[-1], brickid=self.north[0].brickid)):
            modified = self.north[:-1] + (duplicate,)
            with self.assertRaises(stage.EligibilityProbeError) as caught:
                stage.select_panel(self.roots, modified, self.south, self.fixtures)
            self.assertEqual(caught.exception.code, "P0_DUPLICATE_REGIONAL_IDENTITY")

    def test_07_root_join_mismatch_fails(self):
        modified = (replace(self.north[0], geometry=geometry(999)),) + self.north[1:]
        with self.assertRaises(stage.EligibilityProbeError) as caught:
            stage.select_panel(self.roots, modified, self.south, self.fixtures)
        self.assertEqual(caught.exception.code, "P0_ROOT_REGIONAL_JOIN_FAILURE")

    def test_08_row_order_invariance(self):
        first, _ = stage.select_panel(self.roots, self.north, self.south, self.fixtures)
        second, _ = stage.select_panel(tuple(reversed(self.roots)), tuple(reversed(self.north)),
                                       tuple(reversed(self.south)), self.fixtures)
        self.assertEqual(first, second)

    def test_09_exact_hash_bytes_and_final_lf(self):
        raw = stage.selection_hash_bytes("north", "1000p000", 10000)
        self.assertEqual(raw, b"OC3-GALAXY-ELIGIBILITY-PANEL-V1\nregion=north\n"
                              b"brickname=1000p000\nbrickid=10000\n")
        self.assertEqual(raw[-1:], b"\n")

    def test_10_deterministic_hash_order(self):
        panel, _ = stage.select_panel(self.roots, self.north, self.south, self.fixtures)
        north = tuple(item for item in panel if item.region == "north")
        self.assertEqual(north, tuple(sorted(north, key=lambda x: (
            x.selection_sha256, x.brickname.encode("ascii"), x.brickid))))

    def test_11_fixture_is_excluded(self):
        excluded = frozenset({("north", self.north[0].brickname.decode("ascii"))})
        panel, evidence = stage.select_panel(self.roots, self.north, self.south, excluded)
        self.assertNotIn(excluded.pop() if False else self.north[0].brickname.decode("ascii"),
                         {item.brickname for item in panel})
        self.assertEqual(evidence["regions"]["north"]["fixture_excluded"], 1)

    def test_12_canonical_panel_seal(self):
        panel, evidence = stage.select_panel(self.roots, self.north, self.south, self.fixtures)
        manifest = stage.build_panel_manifest(panel, authority_binding(), evidence,
                                              stage.P0Observation(), stage.P0Accounting())
        self.assertEqual(stage.validate_sealed(manifest), manifest)
        changed = dict(manifest); changed["panel_size"] = 15
        with self.assertRaises(stage.EligibilityProbeError): stage.validate_sealed(changed)


class GalaxyEligibilityFirewallTests(unittest.TestCase):
    def test_20_exact_tractor_urls_and_directory_component(self):
        self.assertEqual(stage.tractor_url("north", "1000p000"),
                         "https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/"
                         "north/tractor/100/tractor-1000p000.fits")
        self.assertEqual(stage.tractor_url("south", "2000m000").split("/")[-2], "200")

    def test_21_exact_projection_sets(self):
        self.assertEqual(len(stage.A_CORE), 9)
        self.assertEqual(len(stage.C1_EXTENSION), 10)
        self.assertEqual(len(stage.TRACTOR_ALLOWLIST), 19)
        self.assertEqual(stage.TRACTOR_DENYLIST,
                         {"TYPE", "DCHISQ", "SERSIC", "SHAPE_R", "SHAPE_E1", "SHAPE_E2"})

    def test_22_denied_name_recognition_without_value_access(self):
        columns = stage.bintable_layout(("RELEASE", "TYPE"), ("I", "4A"), 6)
        classified = stage.schema_classification(columns)
        self.assertEqual(classified["TYPE"], "EXPLICITLY_DENIED")
        self.assertEqual(stage.Tripwires().object(), {key: 0 for key in stage.Tripwires().object()})

    def test_23_unknown_provider_column_rejected_by_exhaustive_binding(self):
        columns = stage.bintable_layout(("RELEASE", "NEWCOL"), ("I", "J"), 6)
        with self.assertRaises(stage.EligibilityProbeError) as caught:
            stage.validate_exhaustive_schema(columns, (("RELEASE", "I"), ("OTHER", "J")))
        self.assertEqual(caught.exception.code, "PROVIDER_EXHAUSTIVE_SCHEMA_MISMATCH")

    def test_24_bintable_offsets_and_tform_widths(self):
        columns = stage.bintable_layout(("RELEASE", "DCHISQ", "RA"), ("I", "5D", "D"), 50)
        self.assertEqual([(x.offset, x.width) for x in columns], [(0, 2), (2, 40), (42, 8)])
        self.assertEqual(stage.tform_width("17X"), 3)

    def test_25_contiguous_allowed_span(self):
        columns = stage.bintable_layout(("RELEASE", "BRICKID", "TYPE"), ("I", "J", "4A"), 10)
        plan = stage.selective_projection_plan(columns, ("RELEASE", "BRICKID"), exact_byte_ranges=True)
        self.assertEqual(plan["row_relative_spans"], [{"length": 6, "offset": 0}])
        self.assertEqual(plan["forbidden_cell_bytes_per_row"], 0)

    def test_26_interleaved_denied_requires_disjoint_spans(self):
        columns = stage.bintable_layout(("RELEASE", "TYPE", "BRICKID"), ("I", "4A", "J"), 10)
        plan = stage.selective_projection_plan(columns, ("RELEASE", "BRICKID"), exact_byte_ranges=True)
        self.assertEqual(plan["row_relative_spans"],
                         [{"length": 2, "offset": 0}, {"length": 4, "offset": 6}])
        self.assertTrue(plan["feasible"])

    def test_27_firewall_unavailable_without_projection_or_exact_ranges(self):
        columns = stage.bintable_layout(("RELEASE", "TYPE"), ("I", "4A"), 6)
        plan = stage.selective_projection_plan(columns, ("RELEASE",), exact_byte_ranges=False)
        self.assertEqual(plan["state"], stage.FIREWALL_UNAVAILABLE)
        self.assertFalse(plan["feasible"])

    def test_28_post_decode_drop_shortcut_forbidden(self):
        columns = stage.bintable_layout(("RELEASE", "TYPE"), ("I", "4A"), 6)
        with self.assertRaises(stage.EligibilityProbeError) as caught:
            stage.selective_projection_plan(columns, ("RELEASE",), exact_byte_ranges=True,
                                            whole_row_fetch=True)
        self.assertEqual(caught.exception.code, "POST_DECODE_DROP_FORBIDDEN")

    def test_29_zero_real_cell_decode_in_projection(self):
        columns = stage.bintable_layout(("RELEASE",), ("I",), 2)
        plan = stage.selective_projection_plan(columns, ("RELEASE",), exact_byte_ranges=True)
        self.assertEqual(plan["cell_values_decoded"], 0)

    def test_30_panel_candidate_has_sixteen_tractor_and_zero_b1_urls(self):
        roots, north, south = rows()
        panel, evidence = stage.select_panel(roots, north, south, frozenset())
        manifest = stage.build_panel_manifest(panel, authority_binding(), evidence,
                                              stage.P0Observation(), stage.P0Accounting())
        candidate = stage.build_p1_candidate(manifest, "b" * 64, documentary_manifest(), "c" * 64)
        self.assertEqual(len(candidate["tractor_resources_after_documentary_resolution"]), 16)
        self.assertEqual(len(candidate["b1_candidate_filenames"]), 2)
        self.assertEqual(candidate["b1_literal_urls"], [])
        self.assertEqual(candidate["candidate_scope"], "MINIMUM_DOCUMENTARY_BINDING_ONLY")


class GalaxyEligibilityNetworkControlTests(unittest.TestCase):
    def test_40_transport_unavailable_without_final_authorization(self):
        constructed = []
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp); candidate = base / "candidate.json"; authorization = base / "missing.json"
            stage.write_json_immutable(candidate, stage.sealed_object({"stage_id": stage.STAGE_ID}))
            def factory(**kwargs): constructed.append(True); return object()
            with self.assertRaises(stage.EligibilityProbeError):
                stage.probe_resource_schema(candidate, authorization, "a" * 64, base / "out",
                                             transport_factory=factory)
        self.assertEqual(constructed, [])

    def test_41_first_attempt_policy_is_stricter(self):
        self.assertEqual(stage.FIRST_P1_POLICY["concurrency"], 1)
        self.assertEqual(stage.FIRST_P1_POLICY["automatic_retries_per_resource"], 0)
        self.assertLessEqual(stage.FIRST_P1_POLICY["redirects_per_request"],
                             stage.P1_SPEC_MAXIMA["redirects_per_request"])

    def test_42_request_and_body_caps(self):
        budget = stage.NetworkBudget(1, 100, 50)
        budget.reserve("x", 50, is_range=True)
        with self.assertRaises(stage.EligibilityProbeError): budget.reserve("x", 1, is_range=True)
        budget.settle("x", 50, 20, is_range=True)
        self.assertEqual((budget.requests, budget.body_bytes, budget.ranges["x"]), (1, 20, 20))

    def test_43_per_resource_range_cap(self):
        budget = stage.NetworkBudget(4, 1000, 10)
        with self.assertRaises(stage.EligibilityProbeError): budget.reserve("x", 11, is_range=True)

    def test_44_exact_full_candidate_order(self):
        candidate = {
            "documentary_resources": [{"retrieval_role": "DOC", "url": "https://example.org/doc"}],
            "candidate_scope": "FULL_RESOURCE_SCHEMA_PROBE",
            "tractor_resources": [{"brickname": f"b{i}", "literal_url": f"https://example.org/t{i}"}
                                  for i in range(16)],
            "b1_resources": [{"region": "north", "literal_url": "https://example.org/n"},
                             {"region": "south", "literal_url": "https://example.org/s"}],
        }
        plan = stage.p1_logical_order(candidate)
        self.assertEqual([x[0] for x in plan],
                         ["DOCUMENT"] + ["HEAD_TRACTOR"] * 16 + ["HEAD_B1"] * 2 +
                         ["HEADER_TRACTOR"] * 16 + ["HEADER_B1"] * 2)

    def test_45_durable_checkpoint_preserves_completed_receipts(self):
        with tempfile.TemporaryDirectory() as temp:
            checkpoint = stage.DurableCheckpoint(Path(temp))
            first = checkpoint.record(1, {"resource": "a"})
            second = checkpoint.record(2, {"resource": "b"})
            value = stage.load_canonical_json(Path(temp) / "CHECKPOINT.json")
            self.assertNotEqual(first, second)
            self.assertEqual(value["completed_count"], 2)
            self.assertTrue((Path(temp) / "0001.json").is_file())

    def test_46_plan_contains_no_full_fits_get_or_gaia_desi(self):
        roots, north, south = rows()
        panel, evidence = stage.select_panel(roots, north, south, frozenset())
        manifest = stage.build_panel_manifest(panel, authority_binding(), evidence,
                                              stage.P0Observation(), stage.P0Accounting())
        candidate = stage.build_p1_candidate(manifest, "a" * 64, documentary_manifest(), "b" * 64)
        plan = stage.p1_logical_order(candidate)
        self.assertTrue(all(kind == "DOCUMENT" for kind, _, _ in plan))
        body = json.dumps(candidate).lower()
        self.assertNotIn("gaia_query", body); self.assertNotIn("desi_query", body)

    def test_47_cli_has_all_closed_modes(self):
        actions = {option for action in cli.parser()._actions for option in action.option_strings}
        self.assertTrue({"--validate-inputs", "--dry-run", "--bind-panel",
                         "--probe-resource-schema"}.issubset(actions))

    def test_48_synthetic_p0_publication_and_no_replay(self):
        roots, north, south = rows()
        def decoder(observation):
            observation.allowed_cell_values_decoded = len(roots) * 8 + (len(north) + len(south)) * 13
            return roots, north, south
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp); panel = base / "panel.json"; run = base / "run"; candidate = base / "candidate.json"
            with patch.object(stage, "validate_authorities", return_value=authority_binding()), \
                    patch.object(stage, "load_fixture_exclusions", return_value=frozenset()), \
                    patch.object(stage, "validate_documentary_manifest", return_value=documentary_manifest()), \
                    patch.object(stage, "DOCUMENTARY_MANIFEST_PATH", stage.DOCUMENTARY_MANIFEST_PATH):
                first = stage.execute_p0(panel_path=panel, run_directory=run, candidate_path=candidate,
                                         decoder=decoder, current_implementation="c" * 64)
                second = stage.execute_p0(panel_path=panel, run_directory=run, candidate_path=candidate,
                                          decoder=lambda unused: (_ for _ in ()).throw(AssertionError("replay")),
                                          current_implementation="c" * 64)
            self.assertFalse(first["reused_existing"]); self.assertTrue(second["reused_existing"])
            self.assertEqual(first["terminal"]["terminal"], stage.P0_SUCCESS_TERMINAL)
            self.assertEqual(first["terminal"]["network_requests"], 0)

    def test_49_partial_p0_output_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp); panel = base / "panel.json"; panel.write_text("partial")
            with self.assertRaises(stage.EligibilityProbeError) as caught:
                stage.execute_p0(panel_path=panel, run_directory=base / "run",
                                 candidate_path=base / "candidate.json", decoder=lambda unused: ())
            self.assertEqual(caught.exception.code, "P0_PARTIAL_OR_CONFLICTING_OUTPUT")

    def test_50_authorized_document_probe_persists_body_and_checkpoint(self):
        candidate_value = stage.sealed_object({
            "candidate_scope": "MINIMUM_DOCUMENTARY_BINDING_ONLY",
            "documentary_resources": [
                {"max_body_bytes": 32, "retrieval_role": "DOC",
                 "url": "https://example.org/doc"},
            ],
            "policy": {"automatic_retries_per_resource": 0, "body_bytes_cap": 64,
                       "concurrency": 1, "per_resource_range_body_bytes": 32,
                       "redirects_per_request": 0, "request_cap": 1},
            "scope": stage.SCOPE, "stage_id": stage.STAGE_ID,
        })
        class FakeTransport:
            def __init__(self, **kwargs): self.kwargs = kwargs
            def request(self, method, url, *, byte_range, max_body_bytes):
                self.assertions = (method, url, byte_range, max_body_bytes)
                return {"body": b"official-document", "final_url": url,
                        "headers": {"content-length": "17"}, "redirects": 0,
                        "requests_started": 1, "status": 200}
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp); candidate = base / "candidate.json"
            stage.write_json_immutable(candidate, candidate_value)
            argv_hash = "d" * 64
            authorization = base / "authorization.json"
            stage.write_json_immutable(authorization, {
                "authorization_id": "synthetic", "authorized": True,
                "candidate_sha256": stage.file_sha256(candidate),
                "command_argv_sha256": argv_hash, "scope": stage.SCOPE,
                "stage_id": stage.STAGE_ID,
            })
            result = stage.probe_resource_schema(candidate, authorization, argv_hash, base / "out",
                                                 transport_factory=FakeTransport)
            self.assertEqual((result["network_requests"], result["completed_resources"]), (1, 1))
            self.assertEqual(result["state"], stage.P1_INCONCLUSIVE_TERMINAL)
            self.assertEqual((base / "out/RAW_IMMUTABLE/document-00.body").read_bytes(),
                             b"official-document")
            self.assertTrue((base / "out/checkpoints/CHECKPOINT.json").is_file())

    def test_51_header_probe_reads_only_complete_header_blocks(self):
        primary = fits.PrimaryHDU()
        table = fits.BinTableHDU.from_columns([
            fits.Column(name="RELEASE", format="I", array=np.array([9011], dtype=np.int16)),
            fits.Column(name="TYPE", format="4A", array=np.array([b"PSF"], dtype="S4")),
            fits.Column(name="BRICKID", format="J", array=np.array([1], dtype=np.int32)),
        ])
        stream = io.BytesIO(); fits.HDUList([primary, table]).writeto(stream)
        payload = stream.getvalue(); requested = []
        class FakeTransport:
            def request(self, method, url, *, byte_range, max_body_bytes):
                requested.append(byte_range)
                start, end = byte_range; body = payload[start:end + 1]
                return {"body": body, "final_url": url,
                        "headers": {"content-length": str(len(body)), "accept-ranges": "bytes"},
                        "redirects": 0, "requests_started": 1, "status": 206}
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp); budget = stage.NetworkBudget(10, 20000, 20000)
            checkpoints = stage.DurableCheckpoint(base / "checkpoints")
            evidence, columns = stage._probe_bintable_headers(
                FakeTransport(), budget, checkpoints, [0], base / "raw",
                url="https://example.org/table.fits", resource_id="table",
                redirect_cap=0)
            self.assertEqual(tuple(column.name for column in columns),
                             ("RELEASE", "TYPE", "BRICKID"))
            self.assertEqual(requested, [(0, 2879), (2880, 5759)])
            self.assertEqual(evidence["extension_header_start"], 2880)
            self.assertLessEqual(max(end for _, end in requested), 5759)


if __name__ == "__main__":
    unittest.main()
