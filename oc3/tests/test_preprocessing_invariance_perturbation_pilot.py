"""Synthetic-only tests for the closed OC-3 perturbation-pilot implementation."""
from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

import oc3_preprocessing_invariance_perturbation_pilot as cli
from oc3lib.core import canonical, file_hash
from oc3lib import preprocessing_perturbation_pilot as stage


PROJECT = Path(__file__).resolve().parents[2]


def synthetic_wcs_provenance():
    header = fits.Header()
    header["WCSAXES"] = 2
    header["CRPIX1"] = 65.0
    header["CRPIX2"] = 65.0
    header["CRVAL1"] = 180.0
    header["CRVAL2"] = 1.0
    header["CTYPE1"] = "RA---TAN"
    header["CTYPE2"] = "DEC--TAN"
    header["CD1_1"] = -7.2777777777778e-05
    header["CD1_2"] = 0.0
    header["CD2_1"] = 0.0
    header["CD2_2"] = 7.2777777777778e-05
    cards = [[card.keyword, card.value] for card in WCS(header).to_header(relax=True).cards]
    return {"translated_wcs_cards": cards,
            "translated_wcs_sha256": hashlib.sha256(canonical(cards)).hexdigest()}


def synthetic_plan(project: Path):
    crops = []
    snapshot = {}
    provenance = synthetic_wcs_provenance()
    for slot_index, slot in enumerate(stage.SLOTS):
        region = "south" if slot.startswith("S") else "north"
        for product_index, (product, band) in enumerate(stage.PRODUCT_ORDER):
            if product in ("image", "invvar", "psfsize"):
                dtype = np.dtype("<f4")
                base = np.arange(129 * 129, dtype=np.float32).reshape(129, 129)
                value = ((base + slot_index + product_index) / np.float32(1000.0)).astype(dtype)
                if product == "image":
                    value[0, 0] = np.float32(0.0)
                    value[0, 1] = np.float32(-0.0)
            else:
                dtype = np.dtype("<i2")
                value = np.full((129, 129), slot_index + product_index, dtype=dtype)
            filename = f"{product}-{band}.npy" if band else "maskbits-optical.npy"
            relative = Path("native") / slot / filename
            path = project / relative
            hashes = stage.write_canonical_npy(path, np.ascontiguousarray(value))
            os.chmod(path, 0o444)
            row = {
                "slot": slot, "region": region, "brick": f"brick-{region}",
                "product": product, "band": band, "artifact_path": str(relative),
                "artifact_sha256": hashes["artifact_sha256"],
                "array_content_sha256": hashes["array_content_sha256"],
                "output_dtype": dtype.str, "source_dtype": dtype.str,
                "output_shape": [129, 129], "source_shape": [3600, 3600],
                "slice_bounds_xy": [100, 200, 229, 329],
                "wcs_provenance": dict(provenance),
            }
            crops.append(row)
            snapshot[str(relative)] = hashes["artifact_sha256"]
    psf = []
    for slot in stage.SLOTS:
        region = "south" if slot.startswith("S") else "north"
        for point in ("P0", "P1", "P2"):
            psf.append({"slot": slot, "region": region, "brick": f"brick-{region}",
                        "point_id": point,
                        "source_response_path": f"synthetic/{slot}-{point}.fits",
                        "source_response_sha256": "d" * 64,
                        "native_provider_shapes": {band: [3, 3] for band in stage.BANDS}})
    return {"manifest": {}, "crops": crops, "psf": psf, "snapshot": snapshot,
            "authorities": {"synthetic_fixture": "offline"}}


def frozen_nexp_rows():
    values = {
        "S1": ([], ["g", "r", "z"], [0, 0, 0], [388, 100, 113], "Z0_TALL"),
        "S2": ([], ["g", "r", "z"], [0, 0, 0], [95, 129, 40], "Z0_TALL"),
        "S3": ([], ["g", "z"], [0, 0, 0], [144, 0, 644], "Z0_TSOME"),
        "N1": (["g", "r", "z"], ["g", "r", "z"], [588, 534, 227],
               [503, 326, 579], "ZANY_TALL"),
        "N2": (["z"], ["g", "r", "z"], [0, 0, 88], [174, 207, 138], "ZANY_TALL"),
        "N3": ([], ["z"], [0, 0, 0], [0, 0, 247], "Z0_TSOME"),
    }
    return [{"slot": slot, "zero_support_bands": zero_bands,
             "transition_bands": transition_bands,
             **{f"zero_count_{band}": zero[index] for index, band in enumerate(stage.BANDS)},
             **{f"transition_count_{band}": transitions[index]
                for index, band in enumerate(stage.BANDS)},
             "technical_stratum": label, "source_sha256": stage.AUDIT_METRICS_SHA256}
            for slot, (zero_bands, transition_bands, zero, transitions, label)
            in values.items()]


class PerturbationPilotTests(unittest.TestCase):
    def test_001_frozen_authority_hashes_and_terminology_binding(self):
        self.assertEqual(file_hash(PROJECT / stage.SPEC_RELATIVE), stage.SPEC_SHA256)
        self.assertEqual(file_hash(PROJECT / stage.CLARIFICATION_RELATIVE),
                         stage.CLARIFICATION_SHA256)
        text = (PROJECT / stage.CLARIFICATION_RELATIVE).read_text()
        self.assertIn("2 frozen technical development bricks", text)
        self.assertIn("6 frozen observational windows", text)
        self.assertIn("0 defined astronomical objects for morphology learning", text)

    def test_002_exact_branch_classification(self):
        rows = stage._branch_classes()
        counts = {}
        for row in rows:
            counts[row["execution_class"]] = counts.get(row["execution_class"], 0) + 1
        self.assertEqual(len(rows), 18)
        self.assertEqual(counts, {"EXECUTE_TRANSFORMATION_NOW": 9,
                                  "METADATA_ONLY_NOW": 1,
                                  "RESERVED_FOR_REPRESENTATION_STAGE": 4,
                                  "BLOCKED_BY_FROZEN_DEFERRAL_OR_GATE": 4})
        families = stage._branch_family_classes()
        self.assertEqual(len(families), 16)
        self.assertEqual(sum(row["execution_class"] == "EXECUTE_TRANSFORMATION_NOW"
                             for row in families), 7)

    def test_003_exact_float32_constants_and_bits(self):
        stage._verify_frozen_constants()
        self.assertEqual(stage.FLOAT32_BITS["factor_0p5"], "3f000000")
        self.assertEqual(stage.FLOAT32_BITS["factor_2p0"], "40000000")
        self.assertEqual({key: stage.FLOAT32_BITS[key] for key in stage.BANDS},
                         {"g": "3b4ff253", "r": "3bcb54da", "z": "3c8087b7"})

    def test_004_b01_inverse_behavior_and_float32_dtype(self):
        source = np.linspace(-2, 2, 129 * 129, dtype="<f4").reshape(129, 129)
        for key in ("factor_0p5", "factor_2p0"):
            output, round_trip = stage.scalar_transform(
                source, "multiply", stage._float32_from_bits(stage.FLOAT32_BITS[key]))
            self.assertEqual((output.dtype.str, round_trip.dtype.str), ("<f4", "<f4"))
            self.assertEqual(stage.bitwise_equal_count(source, round_trip), source.size)

    def test_005_b02_exact_offsets_change_zero_and_round_trip_is_measured(self):
        source = np.zeros((129, 129), dtype="<f4")
        for band in stage.BANDS:
            scalar = stage._float32_from_bits(stage.FLOAT32_BITS[band])
            output, round_trip = stage.scalar_transform(source, "add", scalar)
            self.assertEqual(np.count_nonzero(output == 0), 0)
            self.assertEqual(stage.bitwise_equal_count(source, round_trip), source.size)
            negative = stage._float32_from_bits(stage.FLOAT32_BITS[f"negative_{band}"])
            self.assertEqual(negative, -scalar)

    def test_006_b03_scale_is_band_global_and_not_slot_dependent(self):
        scales = stage.development_scales()
        self.assertEqual(set(scales), set(stage.BANDS))
        for band in stage.BANDS:
            observed = {float(stage._scalar_for(
                "B03_DIVIDE_BY_DEVELOPMENT_REFERENCE_SCALE_001", band))
                        for _slot in stage.SLOTS}
            self.assertEqual(len(observed), 1)

    def test_007_scalar_transform_preserves_non_native_byte_order(self):
        source = np.arange(129 * 129, dtype=">f4").reshape(129, 129)
        output, round_trip = stage.scalar_transform(
            source, "multiply", stage._float32_from_bits(stage.FLOAT32_BITS["factor_0p5"]))
        self.assertEqual(output.dtype.str, ">f4")
        self.assertEqual(round_trip.dtype.str, ">f4")

    def test_008_finite_overflow_fails_closed_without_clipping(self):
        source = np.full((129, 129), np.finfo(np.float32).max, dtype="<f4")
        with np.errstate(over="ignore"), self.assertRaisesRegex(
                stage.PilotError, "FINITE_INPUT_BECAME_NONFINITE"):
            stage.scalar_transform(source, "multiply", np.float32(2.0))

    def test_009_exact_rotation_affines(self):
        self.assertEqual(stage.AFFINES["B12_ROT90_CCW"]["A"], [[0, 1], [-1, 0]])
        self.assertEqual(stage.AFFINES["B12_ROT90_CCW"]["t"], [0, 128])
        self.assertEqual(stage.AFFINES["B12_ROT180"]["t"], [128, 128])
        self.assertEqual(stage.AFFINES["B12_ROT270_CCW"]["t"], [128, 0])

    def test_010_exact_reflection_affines(self):
        self.assertEqual(stage.AFFINES["B13_REFLECT_HORIZONTAL"]["A"],
                         [[-1, 0], [0, 1]])
        self.assertEqual(stage.AFFINES["B13_REFLECT_VERTICAL"]["A"],
                         [[1, 0], [0, -1]])

    def test_011_rotation_and_reflection_inverse_is_bitwise(self):
        source = np.arange(129 * 129, dtype="<i2").reshape(129, 129)
        for variant in stage.AFFINES:
            output, inverse = stage.affine_transform(source, variant)
            self.assertTrue(output.flags.c_contiguous)
            self.assertTrue(stage.multiset_bytes_equal(source, output))
            self.assertEqual(stage.bitwise_equal_count(source, inverse), source.size)

    def test_012_synchronized_thirteen_map_permutation(self):
        maps = [np.full((129, 129), index, dtype="<i2") for index in range(13)]
        for variant in stage.AFFINES:
            outputs = [stage.affine_transform(value, variant)[0] for value in maps]
            self.assertEqual(len(outputs), 13)
            self.assertTrue(all(np.all(output == index)
                                for index, output in enumerate(outputs)))

    def test_013_nan_payload_is_preserved_by_permutation(self):
        bits = np.zeros((129, 129), dtype=">u4")
        bits.flat[:3] = [0x7FC12345, 0x7FC54321, 0xFFC11111]
        source = bits.view(">f4")
        for variant in stage.AFFINES:
            output, inverse = stage.affine_transform(source, variant)
            self.assertTrue(stage.multiset_bytes_equal(source, output))
            self.assertEqual(source.tobytes(), inverse.tobytes())

    def test_014_signed_zero_is_preserved_by_permutation(self):
        bits = np.zeros((129, 129), dtype=">u4")
        bits.flat[0] = 0x80000000
        source = bits.view(">f4")
        output, inverse = stage.affine_transform(source, "B13_REFLECT_HORIZONTAL")
        self.assertEqual(output.dtype.str, ">f4")
        self.assertEqual(source.tobytes(), inverse.tobytes())

    def test_015_wcs_affine_adapter_uses_nine_points_and_frozen_tolerance(self):
        row = {"slot": "S1", "wcs_provenance": synthetic_wcs_provenance()}
        for variant in stage.AFFINES:
            result = stage.validate_wcs_affine(row, variant)
            self.assertEqual(len(result["test_points_xy"]), 9)
            self.assertLessEqual(result["max_residual_native_pixels"], 1e-6)
            self.assertEqual((result["padding_count"], result["interpolation_count"]), (0, 0))

    def test_016_psf_limitation_is_exact(self):
        row = {"slot": "N1", "wcs_provenance": synthetic_wcs_provenance()}
        result = stage.validate_wcs_affine(row, "B12_ROT180")
        self.assertEqual(result["provider_psf_response_transform"], "NOT_EXECUTED")
        self.assertTrue(result["psf_provenance_retained"])
        self.assertEqual(result["known_semantic_limitation"],
                         "TRANSFORMED_WINDOW_HAS_NO_TRANSFORMED_PROVIDER_PSF_RESPONSE")

    def test_017_canonical_npy_and_independent_hash_verification(self):
        value = np.arange(129 * 129, dtype=">i2").reshape(129, 129)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "value.npy"
            hashes = stage.write_canonical_npy(path, value)
            self.assertEqual(path.read_bytes()[:8], b"\x93NUMPY\x01\x00")
            self.assertEqual(file_hash(path), hashes["artifact_sha256"])
            with path.open("rb") as handle:
                restored = np.lib.format.read_array(handle, allow_pickle=False)
            self.assertEqual(stage.array_content_hash(restored), hashes["array_content_sha256"])
            self.assertEqual(restored.dtype.str, ">i2")

    def test_018_nexp_mapping_is_regenerated_from_frozen_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            fields = ["slot", "tier", "family", "band", "metric_id", "value_int"]
            rows = []
            expected = frozen_nexp_rows()
            for item in expected:
                for band in stage.BANDS:
                    rows.extend([
                        {"slot": item["slot"], "tier": "A", "family": "NEXP",
                         "band": band, "metric_id": "zero_count",
                         "value_int": item[f"zero_count_{band}"]},
                        {"slot": item["slot"], "tier": "A", "family": "NEXP",
                         "band": band, "metric_id": "total_transition_count",
                         "value_int": item[f"transition_count_{band}"]},
                    ])
            path = project / "audit.csv"
            with path.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
                writer.writeheader(); writer.writerows(rows)
            with patch.object(stage, "AUDIT_METRICS_RELATIVE", Path("audit.csv")), \
                    patch.object(stage, "AUDIT_METRICS_SHA256", file_hash(path)):
                observed = stage.build_nexp_strata(project)
            self.assertEqual([row["technical_stratum"] for row in observed],
                             [row["technical_stratum"] for row in expected])

    def test_019_information_loss_register_is_complete_and_neutral(self):
        rows = stage.build_information_loss_register()
        self.assertEqual(len(rows), 23)
        self.assertTrue(all(set(row) == set(stage.LOSS_FIELDS) for row in rows))
        text = json.dumps(rows).lower()
        for token in ('"best"', '"better"', '"worse"', '"preferred"', '"recommended"'):
            self.assertNotIn(token, text)

    def test_020_reserved_and_blocked_branches_create_no_executable_variant(self):
        variants = {row[0] for row in stage.SCALAR_VARIANTS} | \
                   {config["branch"] for config in stage.AFFINES.values()} | \
                   {"B00_NATIVE_IMAGE_ONLY", "B14_BAND_ABLATION"}
        self.assertTrue(set(stage.RESERVED_BRANCHES).isdisjoint(variants))
        self.assertTrue(set(stage.BLOCKED_BRANCHES).isdisjoint(variants))

    def test_021_metric_schema_is_closed_and_has_no_scientific_convenience_metrics(self):
        self.assertEqual(len(stage.METRIC_FIELDS), 37)
        for field in ("mean", "median", "quantile", "snr", "centroid", "texture",
                      "segmentation", "morphology", "similarity", "ranking"):
            self.assertFalse(any(field in item.lower() for item in stage.METRIC_FIELDS))

    def test_022_validate_inputs_decodes_no_array(self):
        with patch.object(stage, "_authority_plan",
                          return_value={"crops": [{}] * 78, "psf": [{}] * 18}):
            observed = stage.validate_inputs(PROJECT)
        self.assertEqual(observed["array_values_decoded"], 0)
        self.assertEqual(observed["transformations_executed"], 0)
        self.assertEqual(observed["network_requests"], 0)

    def test_023_complete_synthetic_publication_has_exact_inventory_and_is_immutable(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            plan = synthetic_plan(project)
            before = {relative: (project / relative).read_bytes()
                      for relative in plan["snapshot"]}
            with patch.object(stage, "build_nexp_strata", return_value=frozen_nexp_rows()):
                terminal = stage.execute(project, plan=plan)
            self.assertEqual(terminal["state"], stage.SUCCESS)
            self.assertEqual(terminal["transformed_arrays"], 480)
            self.assertEqual((terminal["network_requests"], terminal["model_operations"],
                              terminal["morphology_operations"]), (0, 0, 0))
            root = project / stage.STAGE_ROOT_RELATIVE
            self.assertEqual(len(list((root / "TRANSFORMED").glob("*/*/*.npy"))), 480)
            self.assertFalse((root / "TRANSFORMED/B00_NATIVE_IMAGE_ONLY").exists())
            self.assertFalse(any("B14" in str(path)
                                 for path in (root / "TRANSFORMED").rglob("*.npy")))
            manifest = stage._load_canonical(root / "OC3_PERTURBATION_BRANCH_MANIFEST.json")
            stage._verify_seal(manifest)
            self.assertEqual(len(manifest["b00_references"]), 18)
            self.assertEqual(len(manifest["band_selections"]), 18)
            self.assertEqual(len(manifest["transformed_arrays"]), 480)
            self.assertEqual(len(manifest["wcs_adapters"]), 30)
            self.assertEqual(manifest["terminology"], {
                "technical_development_bricks": 2, "observational_windows": 6,
                "astronomical_objects_defined": 0})
            for relative, content in before.items():
                self.assertEqual((project / relative).read_bytes(), content)
                self.assertEqual(stat.S_IMODE((project / relative).stat().st_mode) & 0o222, 0)
            self.assertTrue(all(path.stat().st_mode & 0o222 == 0
                                for path in root.rglob("*") if path.is_file()))

    def test_024_complete_synthetic_metrics_and_register_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            plan = synthetic_plan(project)
            with patch.object(stage, "build_nexp_strata", return_value=frozen_nexp_rows()):
                stage.execute(project, plan=plan)
            root = project / stage.STAGE_ROOT_RELATIVE
            with (root / "OC3_PERTURBATION_TECHNICAL_EFFECT_METRICS.csv").open() as handle:
                metrics = list(csv.DictReader(handle))
            with (root / "OC3_PERTURBATION_INFORMATION_LOSS_REGISTER.csv").open() as handle:
                losses = list(csv.DictReader(handle))
            with (root / "OC3_NEXP_TECHNICAL_STRATA.csv").open() as handle:
                nexp = list(csv.DictReader(handle))
            self.assertEqual((len(metrics), len(losses), len(nexp)), (480, 23, 6))
            self.assertTrue(all(row["padding_count"] == "0" and
                                row["interpolation_count"] == "0" and
                                row["clipping_count"] == "0" for row in metrics))

    def test_025_second_or_partial_execution_is_refused_before_input_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            root = project / stage.STAGE_ROOT_RELATIVE
            root.mkdir(parents=True)
            with patch.object(stage, "_authority_plan") as forbidden:
                with self.assertRaisesRegex(stage.PilotError,
                                            "SECOND_OR_PARTIAL_EXECUTION_REFUSED"):
                    stage.execute(project)
                forbidden.assert_not_called()

    def test_026_failure_does_not_publish_successful_subset(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            plan = synthetic_plan(project)
            with patch.object(stage, "build_nexp_strata", return_value=frozen_nexp_rows()), \
                    patch.object(stage, "write_canonical_npy",
                                 side_effect=stage.PilotError("SYNTHETIC_WRITE_FAILURE")):
                with self.assertRaisesRegex(stage.PilotError, "SYNTHETIC_WRITE_FAILURE"):
                    stage.execute(project, plan=plan)
            root = project / stage.STAGE_ROOT_RELATIVE
            terminal = stage._load_canonical(root / "OC3_PERTURBATION_PILOT_TERMINAL.json")
            self.assertEqual(terminal["state"], stage.FAILURE)
            self.assertFalse(terminal["successful_subset_published"])

    def test_027_cli_exposes_only_offline_validation_and_explicit_execution(self):
        help_text = cli.parser().format_help().lower()
        self.assertIn("--validate-inputs", help_text)
        self.assertIn("--execute-pilot", help_text)
        self.assertNotIn("resume", help_text)
        self.assertNotIn("network", help_text)

    def test_028_cli_validation_is_compact_and_offline(self):
        value = {"stage_id": stage.STAGE_ID, "state": "ok", "network_requests": 0}
        with patch.object(cli, "validate_inputs", return_value=value) as validate:
            self.assertEqual(cli.main(["--validate-inputs", "--project", str(PROJECT)]), 0)
            validate.assert_called_once()

    def test_029_source_has_no_network_visualization_or_model_stack(self):
        source = (PROJECT / "oc3/oc3lib/preprocessing_perturbation_pilot.py").read_text().lower()
        for token in ("import requests", "import urllib", "import socket", "urlopen(",
                      "matplotlib", "seaborn", "pillow", "skimage", "imshow(", "plt.",
                      "torch", "tensorflow", "keras", "sklearn"):
            self.assertNotIn(token, source)

    def test_030_source_has_no_location_change_or_parent_coadd_access(self):
        source = (PROJECT / "oc3/oc3lib/preprocessing_perturbation_pilot.py").read_text()
        self.assertNotIn("CompImageHDU", source)
        self.assertNotIn("hdu.section", source)
        self.assertNotIn("all_pix2world" + "(" + "locations", source)

    def test_031_production_plan_validates_exact_inventory_without_array_decode(self):
        plan = stage._authority_plan(PROJECT, verify_payload_hashes=False)
        self.assertEqual((len(plan["crops"]), len(plan["psf"])), (78, 18))
        self.assertEqual([(row["slot"], row["product"], row["band"])
                          for row in plan["crops"]],
                         [(slot, product, band) for slot in stage.SLOTS
                          for product, band in stage.PRODUCT_ORDER])

    def test_032_production_wcs_is_synchronized_within_every_slot(self):
        plan = stage._authority_plan(PROJECT, verify_payload_hashes=False)
        for slot in stage.SLOTS:
            hashes = {row["wcs_provenance"]["translated_wcs_sha256"]
                      for row in plan["crops"] if row["slot"] == slot}
            self.assertEqual(len(hashes), 1)

    def test_033_expected_array_arithmetic_is_exactly_480(self):
        observed = 2 * 6 * 3 + 2 * 6 * 3 + 1 * 6 * 3 + 3 * 6 * 13 + 2 * 6 * 13
        self.assertEqual(observed, 480)


if __name__ == "__main__":
    unittest.main()
