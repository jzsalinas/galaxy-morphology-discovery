"""Synthetic-only tests for the OC-3 observational/confound audit."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

import oc3_observational_confound_audit as cli
from oc3lib.core import canonical, file_hash
from oc3lib import observational_confound_audit as stage


PROJECT = Path(__file__).resolve().parents[2]


def wcs_cards(crval=(10.0, 0.0)):
    header = fits.Header()
    header["WCSAXES"] = 2
    header["CRPIX1"] = 65.0
    header["CRPIX2"] = 65.0
    header["CRVAL1"] = crval[0]
    header["CRVAL2"] = crval[1]
    header["CTYPE1"] = "RA---TAN"
    header["CTYPE2"] = "DEC--TAN"
    header["CD1_1"] = -7.2777777777778e-05
    header["CD1_2"] = 0.0
    header["CD2_1"] = 0.0
    header["CD2_2"] = 7.2777777777778e-05
    return [[card.keyword, card.value] for card in WCS(header).to_header(relax=True).cards]


def synthetic_inputs(project: Path):
    arrays = {}
    crops = []
    cards = wcs_cards()
    for slot in stage.SLOTS:
        region = "south" if slot.startswith("S") else "north"
        for product, band in stage.PRODUCT_ORDER:
            relative = f"synthetic/{slot}/{product}-{band}.npy"
            if product in ("image", "invvar", "psfsize"):
                dtype = np.dtype("<f4")
            else:
                dtype = np.dtype("<i2")
            value = np.ones((129, 129), dtype=dtype)
            if product == "nexp" and slot == "N2" and band == "g":
                value[:, :64] = 0
            if product == "maskbits" and slot == "S3":
                value[0, 0] = 1 << 3
            if product == "psfsize" and slot == "N3":
                value = np.ones((129, 129), dtype=np.float64)
                value[0, 0] = 1.0 + stage.N3_FROZEN_V
                dtype = value.dtype
            arrays[str(project / relative)] = value
            crops.append({
                "slot": slot, "region": region, "brick": f"brick-{region}",
                "product": product, "band": band, "artifact_path": relative,
                "artifact_sha256": "a" * 64, "array_content_sha256": "b" * 64,
                "output_dtype": dtype.str, "source_dtype": dtype.str,
                "output_shape": [129, 129], "source_shape": [3600, 3600],
                "slice_bounds_xy": [100, 200, 229, 329],
                "source_path": f"synthetic/{region}-source.fits.fz",
                "source_body_sha256": "c" * 64, "source_hdu": 1,
                "wcs_provenance": {
                    "integer_origin_xy": [100, 200],
                    "parent_wcs_cards": cards, "translated_wcs_cards": cards,
                    "residual_upper_bound_pixels": 1e-10,
                },
            })
    psf = []
    for slot in stage.SLOTS:
        region = "south" if slot.startswith("S") else "north"
        for point in ("P0", "P1", "P2"):
            psf.append({
                "slot": slot, "region": region, "brick": f"brick-{region}",
                "point_id": point, "transport_id": f"psf-{slot}-{point}",
                "source_response_path": f"synthetic/psf-{slot}-{point}.fits",
                "source_response_sha256": "d" * 64,
                "plane_mapping": {"g": 0, "r": 1, "z": 2},
                "observational_identity_ids": [f"id-{slot}-{point}-{b}" for b in stage.BANDS],
                "native_provider_shapes": {band: [3, 3] for band in stage.BANDS},
            })
    locations = {"locations": [{"slot": slot,
                                  "region": "south" if slot.startswith("S") else "north",
                                  "brick": "brick-south" if slot.startswith("S") else "brick-north"}
                                 for slot in stage.SLOTS]}
    plan = {"crops": crops, "psf": psf, "locations": locations,
            "header_rows": {"south": crops[6], "north": crops[45]}, "snapshot": {}}
    return plan, arrays


class FakeHDU:
    def __init__(self, data):
        self.data = data


class FakeHDUs(list):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class AuditTests(unittest.TestCase):
    def test_001_production_manifest_plan_has_exact_inventory_without_array_open(self):
        plan = stage._manifest_plan(PROJECT, verify_payload_hashes=False)
        self.assertEqual((len(plan["crops"]), len(plan["psf"])), (78, 18))
        self.assertEqual(len({identity for row in plan["psf"]
                              for identity in row["observational_identity_ids"]}), 54)

    def test_002_image_before_tier_a_is_rejected_and_counted(self):
        row = {"product": "image", "slot": "S1", "artifact_path": "x",
               "output_dtype": "<f4"}
        gate = stage.ArrayAccessGate(Path("/tmp"), loader=lambda path: np.zeros((129, 129), "<f4"))
        with self.assertRaisesRegex(stage.AuditError, "IMAGE_BEFORE_TIER_A_COMPLETE"):
            gate.read(row)
        self.assertEqual(gate.image_reads_before_tier_a_complete, 1)

    def test_003_tier_gate_requires_exact_sixty_then_allows_eighteen(self):
        arrays = {"invvar": np.ones((129, 129), "<f4"),
                  "image": np.ones((129, 129), "<f4")}
        gate = stage.ArrayAccessGate(Path("/tmp"), loader=lambda path: arrays[path.name])
        tier_a = {"product": "invvar", "slot": "S1", "artifact_path": "invvar",
                  "output_dtype": "<f4"}
        image = {"product": "image", "slot": "S1", "artifact_path": "image",
                 "output_dtype": "<f4"}
        for _ in range(60):
            gate.read(tier_a)
        gate.complete_tier_a()
        for _ in range(18):
            gate.read(image)
        self.assertEqual((gate.tier_a_crop_reads, gate.image_reads,
                          gate.image_reads_before_tier_a_complete), (60, 18, 0))

    def test_004_nexp_transition_denominator_and_four_neighbours(self):
        value = (np.indices((129, 129)).sum(axis=0) % 2).astype(np.int16)
        horizontal, vertical, total = stage.transition_counts(value)
        self.assertEqual((horizontal, vertical, total), (16512, 16512, 33024))
        self.assertEqual(total / 33024, 1.0)

    def test_005_dynamic_integer_levels_are_sorted(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = stage.AuditEngine(Path(tmp), {"crops": []})
            row = {"slot": "S1", "region": "south", "brick": "b", "band": "g"}
            value = np.resize(np.array([7, 1, 4], dtype=np.int16), (129, 129))
            engine._nexp(row, value)
            levels = [r["level"] for r in engine.rows if r["metric_id"] == "level_count"]
            self.assertEqual(levels, [1, 4, 7])

    def test_006_quantiles_use_frozen_linear_method(self):
        value = np.array([0.0, 1.0, 4.0, 10.0])
        observed = stage.fixed_quantiles(value)
        expected = np.quantile(value, stage.QUANTILES, method="linear")
        self.assertEqual(list(observed.values()), list(expected))

    def test_007_zero_median_invvar_is_explicitly_undefined(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = stage.AuditEngine(Path(tmp), {"crops": []})
            row = {"slot": "S1", "region": "south", "brick": "b", "band": "g"}
            value = np.zeros((129, 129), dtype=np.float32)
            engine._invvar(row, value)
            relative = next(r for r in engine.rows if r["metric_id"] == "relative_iqr")
            self.assertIsNone(relative["value_float"])
            self.assertEqual(relative["validity_state"], "UNDEFINED_ZERO_MEDIAN")

    def test_008_diagnostic_sigma_uses_positive_values_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = stage.AuditEngine(Path(tmp), {"crops": []})
            row = {"slot": "S1", "region": "south", "brick": "b", "band": "g"}
            value = np.zeros((129, 129), dtype=np.float32)
            value[0, :3] = [-1.0, 1.0, 4.0]
            engine._invvar(row, value)
            count = next(r for r in engine.rows if r["metric_id"] == "diagnostic_sigma_count")
            median = next(r for r in engine.rows if r["metric_id"] == "diagnostic_sigma_median")
            self.assertEqual(count["value_int"], 2)
            self.assertEqual(median["value_float"], 0.75)

    def test_009_maskbits_overlap_and_unknown_position_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = stage.AuditEngine(Path(tmp), {"crops": []})
            row = {"slot": "S3", "region": "south", "brick": "b", "band": None}
            value = np.zeros((129, 129), dtype=np.int32)
            value[0, 0] = (1 << 1) | (1 << 3) | (1 << 14)
            engine._maskbits(row, value)
            bit_counts = {r["level"]: r["value_int"] for r in engine.rows
                          if r["metric_id"] == "bit_count"}
            unknown = next(r for r in engine.rows if r["metric_id"] == "unknown_bit_positions")
            expressed = next(r for r in engine.rows
                             if r["metric_id"] == "s3_optical_condition_expressed")
            self.assertEqual((bit_counts[1], bit_counts[3]), (1, 1))
            self.assertEqual(unknown["value_text"], "[14]")
            self.assertEqual(expressed["value_text"], "true")

    def test_010_n2_class_zero_rule(self):
        arrays = [np.ones((129, 129), dtype=np.int16) for _ in stage.BANDS]
        arrays[1][0, 0] = 0
        bands = [band for band, value in zip(stage.BANDS, arrays)
                 if np.any(value == 0) and np.any(value > 0)]
        self.assertEqual(bands, ["r"])

    def test_011_n3_exact_value_and_tolerance(self):
        values = [np.ones((129, 129), dtype=np.float64) for _ in stage.BANDS]
        values[0][0, 0] = 1.0 + stage.N3_FROZEN_V
        observed = stage.n3_variation(values)
        self.assertLessEqual(abs(observed - stage.N3_FROZEN_V), stage.N3_TOLERANCE)

    def test_012_psf_raw_sum_uses_math_fsum_and_nonfinite_defers(self):
        value = np.array([1e16, 1.0, -1e16], dtype=np.float64)
        self.assertEqual(stage.psf_raw_sum(value), 1.0)
        self.assertIsNone(stage.psf_raw_sum(np.array([1.0, np.nan])))

    def test_013_psf_peak_tie_break_is_row_major(self):
        value = np.zeros((4, 4), dtype=np.float32)
        value[2, 0] = value[0, 3] = 9.0
        self.assertEqual(stage.raw_peak(value), (0, 3))

    def test_014_psf_plane_hash_is_exact(self):
        value = np.arange(9, dtype=">f4").reshape(3, 3)
        metadata = {"dtype": ">f4", "order": "C", "shape": [3, 3]}
        expected = hashlib.sha256(stage.PSF_HASH_PREFIX + canonical(metadata) + b"\n" +
                                  value.tobytes(order="C")).hexdigest()
        self.assertEqual(stage.psf_plane_hash(value), expected)

    def test_015_ra_wrap_is_half_open(self):
        values = np.array([359.5, 0.0, 0.9, 1.0, 180.0])
        self.assertEqual(stage.ra_in_bounds(values, 359.0, 1.0).tolist(),
                         [True, True, True, False, False])

    def test_016_primary_geometry_all_and_mixed(self):
        class Constant:
            def all_pix2world(self, x, y, origin):
                return np.full_like(x, 10.0, dtype=float), np.zeros_like(y, dtype=float)
        all_primary = stage.primary_geometry(Constant(), (9.0, 11.0, -1.0, 1.0))
        self.assertEqual(all_primary["state"], "ALL_PRIMARY")

        class Split:
            def all_pix2world(self, x, y, origin):
                return 9.0 + np.asarray(x) / 64.0, np.zeros_like(y, dtype=float)
        mixed = stage.primary_geometry(Split(), (9.0, 10.0, -1.0, 1.0))
        self.assertEqual(mixed["state"], "MIXED_PRIMARY")
        self.assertGreater(mixed["total"], 0)
        self.assertIsNotNone(mixed["center_boundary_distance"])

    def test_017_wcs_jacobian_convention(self):
        cards = wcs_cards()
        header = fits.Header()
        for key, value in cards:
            header[key] = value
        observed = stage.wcs_jacobian(WCS(header), 64.0, 64.0)
        self.assertAlmostEqual(np.sqrt(observed["area"]), 0.262, places=6)
        self.assertGreaterEqual(observed["axis_ratio"], 1.0)

    def test_018_feature_schema_has_no_image_family(self):
        columns = stage.feature_columns()
        self.assertFalse(any("image" in name.lower() for name in columns))
        self.assertEqual(len(columns), len(set(columns)))

    def test_019_exact_five_contrasts_and_signed_difference(self):
        columns = ["slot", "region", "x"]
        matrix = [{"slot": slot, "region": "s" if slot.startswith("S") else "n", "x": i}
                  for i, slot in enumerate(stage.SLOTS)]
        rows = stage.build_contrasts(columns, matrix, {"x": "u"})
        self.assertEqual({r["contrast_id"] for r in rows}, {"C01", "C02", "C03", "C04", "C05"})
        c01 = next(r for r in rows if r["contrast_id"] == "C01" and r["feature_id"] == "x")
        self.assertEqual(c01["signed_difference"], -1.0)

    def test_020_interpretation_precedence(self):
        gate = SimpleNamespace(tier_a_complete=False, image_reads=0)
        engine = SimpleNamespace(gate=gate, psf_body_reads=0, psf_plane_decodes=0,
                                 stratum_not_expressed=True, witnesses=["x"])
        self.assertEqual(stage.interpretation_state(engine), stage.FAILURE)
        gate.tier_a_complete, gate.image_reads = True, 18
        engine.psf_body_reads, engine.psf_plane_decodes = 18, 54
        self.assertEqual(stage.interpretation_state(engine), "STRATUM_NOT_EXPRESSED")
        engine.stratum_not_expressed = False
        self.assertEqual(stage.interpretation_state(engine), "CONFOUND_VARIATION_OBSERVED")
        engine.witnesses = []
        self.assertEqual(stage.interpretation_state(engine), "LIMITED_VARIATION_OBSERVED")

    def test_021_complete_synthetic_execution_has_exact_counts_and_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            plan, arrays = synthetic_inputs(project)
            gate = stage.ArrayAccessGate(project, loader=lambda path: arrays[str(path)])
            open_counter = {"value": 0}

            def opener(path):
                open_counter["value"] += 1
                base = float(open_counter["value"])
                return FakeHDUs([FakeHDU(np.full((3, 3), base + band, dtype=np.float32))
                                 for band in range(3)])

            geometry = [
                {"primary_count": 16641, "nonprimary_count": 0, "primary_fraction": 1.0,
                 "horizontal": 0, "vertical": 0, "total": 0, "state": "ALL_PRIMARY",
                 "center_boundary_distance": None},
                {"primary_count": 8000, "nonprimary_count": 8641,
                 "primary_fraction": 8000 / 16641, "horizontal": 129, "vertical": 0,
                 "total": 129, "state": "MIXED_PRIMARY", "center_boundary_distance": .5},
                {"primary_count": 16641, "nonprimary_count": 0, "primary_fraction": 1.0,
                 "horizontal": 0, "vertical": 0, "total": 0, "state": "ALL_PRIMARY",
                 "center_boundary_distance": None},
                {"primary_count": 16641, "nonprimary_count": 0, "primary_fraction": 1.0,
                 "horizontal": 0, "vertical": 0, "total": 0, "state": "ALL_PRIMARY",
                 "center_boundary_distance": None},
                {"primary_count": 16000, "nonprimary_count": 641,
                 "primary_fraction": 16000 / 16641, "horizontal": 129, "vertical": 0,
                 "total": 129, "state": "MIXED_PRIMARY", "center_boundary_distance": 20.5},
                {"primary_count": 16641, "nonprimary_count": 0, "primary_fraction": 1.0,
                 "horizontal": 0, "vertical": 0, "total": 0, "state": "ALL_PRIMARY",
                 "center_boundary_distance": None},
            ]
            jacobian = {"singular_max": .262, "singular_min": .262,
                        "area": .262 ** 2, "axis_ratio": 1.0}
            with patch.object(stage, "_manifest_plan", return_value=plan), \
                    patch.object(stage, "_header_bounds", return_value=((9, 11, -1, 1), 1)), \
                    patch.object(stage, "primary_geometry", side_effect=geometry), \
                    patch.object(stage, "wcs_jacobian", return_value=jacobian), \
                    patch.object(stage, "_recheck_snapshot", return_value=0):
                terminal = stage.execute(project, gate=gate, psf_opener=opener)
            self.assertEqual(terminal["state"], stage.SUCCESS)
            self.assertEqual((terminal["tier_a_crop_reads"], terminal["image_reads"]), (60, 18))
            self.assertEqual((terminal["psf_response_reads"], terminal["psf_plane_decodes"]),
                             (18, 54))
            self.assertEqual(terminal["image_reads_before_tier_a_complete"], 0)
            root = project / stage.STAGE_ROOT_RELATIVE
            self.assertEqual({p.name for p in root.iterdir()}, {
                "OC3_OBSERVER_AUDIT_SLOT_METRICS.csv", "OC3_OBSERVER_FEATURE_MATRIX.csv",
                "OC3_OBSERVER_AUDIT_CONTRASTS.csv", "OC3_OBSERVER_AUDIT_SUMMARY.json",
                "OC3_OBSERVER_AUDIT_TERMINAL.json", "OC3_OBSERVER_AUDIT_RUN.log"})
            self.assertFalse(any(p.suffix in (".png", ".jpg", ".npy") for p in root.iterdir()))
            with (root / "OC3_OBSERVER_FEATURE_MATRIX.csv").open() as handle:
                reader = csv.DictReader(handle)
                matrix = list(reader)
            self.assertEqual(len(matrix), 6)
            self.assertFalse(any("image" in key.lower() for key in reader.fieldnames))
            with (root / "OC3_OBSERVER_AUDIT_SLOT_METRICS.csv").open() as handle:
                rows = list(csv.DictReader(handle))
            deferred = [r for r in rows if r["metric_id"] == "physical_psf_shape_metrics"]
            self.assertEqual(len(deferred), 54)
            self.assertTrue(all(r["value_text"] == "PHYSICAL_PSF_SHAPE_METRICS_DEFERRED"
                                for r in deferred))
            self.assertTrue(all(p.stat().st_mode & 0o222 == 0 for p in root.iterdir()))

    def test_022_input_modification_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            path = project / "x"
            path.write_bytes(b"a")
            snapshot = {"x": file_hash(path)}
            path.write_bytes(b"b")
            with self.assertRaisesRegex(stage.AuditError, "INPUT_MODIFICATION_DETECTED"):
                stage._recheck_snapshot(project, snapshot)

    def test_023_source_has_no_network_or_visual_stack(self):
        source = (PROJECT / "oc3/oc3lib/observational_confound_audit.py").read_text().lower()
        for token in ("import requests", "import urllib", "import socket", "matplotlib",
                      "skimage", "pillow", "seaborn", "plt.", "imshow("):
            self.assertNotIn(token, source)
        for token in ("source_detection", '"centroid"', '"segmentation"', '"sersic"',
                      '"concentration"', '"asymmetry"', '"texture"', '"embedding"',
                      '"cluster"', '"thumbnail"', '"rgb"'):
            self.assertEqual(source.count(token), 1 if token in source[source.find("prohibited ="):]
                             else 0)

    def test_024_cli_has_only_offline_modes(self):
        help_text = cli.parser().format_help().lower()
        self.assertIn("--validate-inputs", help_text)
        self.assertIn("--audit", help_text)
        self.assertNotIn("network", help_text)


if __name__ == "__main__":
    unittest.main()
