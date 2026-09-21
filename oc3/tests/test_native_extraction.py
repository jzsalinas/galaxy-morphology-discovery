"""Synthetic/offline tests for exact bounded native extraction."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from astropy.io import fits

import oc3_offline_native_extraction as cli
from oc3lib.core import canonical, file_hash
from oc3lib import native_extraction as stage


PROJECT = Path(__file__).resolve().parents[2]


def tan_header(shape=(300, 300)):
    header = fits.Header()
    header["NAXIS"] = 2
    header["NAXIS1"] = shape[1]
    header["NAXIS2"] = shape[0]
    header["CTYPE1"] = "RA---TAN"
    header["CTYPE2"] = "DEC--TAN"
    header["CRPIX1"] = 151.0
    header["CRPIX2"] = 151.0
    header["CRVAL1"] = 180.0
    header["CRVAL2"] = 1.0
    header["CD1_1"] = -7.27777777777778e-05
    header["CD1_2"] = 0.0
    header["CD2_1"] = 0.0
    header["CD2_2"] = 7.27777777777778e-05
    return header


def synthetic_plan():
    crops = []
    for slot_index, slot in enumerate(stage.SLOTS):
        region = "south" if slot.startswith("S") else "north"
        for product, band in stage.PRODUCT_ORDER:
            dtype = stage.EXPECTED_DTYPES[product]
            filename = f"{product}-{band}.npy" if band else "maskbits-optical.npy"
            crops.append({
                "slot": slot, "region": region, "brick": f"brick-{region}",
                "product": product, "band": band,
                "slice_bounds_xy": [64, 64, 193, 193], "filename": filename,
                "resource_id": f"resource-{region}-{product}-{band}",
                "source_path": f"synthetic/{region}-{product}-{band}.fits.fz",
                "source_body_sha256": "a" * 64, "source_shape": [300, 300],
                "expected_dtype_name": dtype, "source_hdu": 1,
            })
    mappings = []
    for slot in stage.SLOTS:
        region = "south" if slot.startswith("S") else "north"
        shapes = ({band: [63, 63] for band in stage.BANDS} if region == "south"
                  else {"g": [31, 31], "r": [31, 31], "z": [63, 63]})
        for point in ("P0", "P1", "P2"):
            mappings.append({
                "slot": slot, "region": region, "brick": f"brick-{region}",
                "point_id": point, "transport_id": f"psf-{slot}-{point}",
                "source_response_path": f"synthetic/psf-{slot}-{point}.fits",
                "source_response_sha256": "b" * 64,
                "plane_mapping": {"g": 0, "r": 1, "z": 2},
                "observational_identity_ids":
                    [f"{slot}-{point}-{band}" for band in stage.BANDS],
                "native_provider_shapes": shapes,
            })
    return {"authority_bindings": {"synthetic": True}, "crops": crops,
            "psf_mappings": mappings}


class FakeAccessor:
    def __init__(self):
        self.section_calls = 0
        self.authorized_elements_returned = 0
        self.full_plane_materializations = 0
        self.unauthorized_pixels_exposed = 0
        self.header = tan_header()

    def read(self, path, hdu_index, bounds, expected_shape):
        product = Path(path).stem.split("-")[1]
        dtype = np.dtype(stage.EXPECTED_DTYPES[product])
        array = np.zeros(stage.ARRAY_SHAPE, dtype=dtype)
        if product == "image":
            array.view(np.uint8).reshape(-1)[:4] = [0, 0, 128, 127]
        self.section_calls += 1
        self.authorized_elements_returned += array.size
        return array, self.header.copy()


class NativeExtractionTests(unittest.TestCase):
    def test_001_production_plan_has_exact_frozen_inventory_without_body_scan(self):
        plan = stage.build_plan(PROJECT, verify_body_hashes=False)
        self.assertEqual(len(plan["crops"]), 78)
        self.assertEqual(len(plan["psf_mappings"]), 18)
        self.assertEqual(len({identity for row in plan["psf_mappings"]
                              for identity in row["observational_identity_ids"]}), 54)
        self.assertEqual([(row["slot"], row["product"], row["band"])
                          for row in plan["crops"]],
                         [(slot, product, band) for slot in stage.SLOTS
                          for product, band in stage.PRODUCT_ORDER])

    def test_002_all_six_frozen_windows_follow_half_open_center_convention(self):
        plan = stage.build_plan(PROJECT, verify_body_hashes=False)
        first_by_slot = {row["slot"]: row for row in plan["crops"]
                         if row["product"] == "image" and row["band"] == "g"}
        locations = stage._canonical_load(PROJECT / stage.LOCATIONS_RELATIVE)["locations"]
        for row in locations:
            bounds = first_by_slot[row["slot"]]["slice_bounds_xy"]
            self.assertEqual(bounds, [row["x"] - 64, row["y"] - 64,
                                      row["x"] + 65, row["y"] + 65])
            self.assertEqual((bounds[2] - bounds[0], bounds[3] - bounds[1]), (129, 129))

    def test_003_real_compressed_section_is_exact_and_does_not_load_plane(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "synthetic.fits.fz"
            parent = np.arange(300 * 300, dtype=np.int16).reshape(300, 300)
            compressed = fits.CompImageHDU(parent, header=tan_header(), tile_shape=(50, 50))
            fits.HDUList([fits.PrimaryHDU(), compressed]).writeto(path)
            accessor = stage.BoundedSectionAccessor()
            actual, _ = accessor.read(path, 1, [70, 80, 199, 209], [300, 300])
            self.assertEqual(actual.dtype.str, parent.dtype.str)
            self.assertEqual(actual.tobytes(), parent[80:209, 70:199].tobytes())
            self.assertEqual((accessor.section_calls, accessor.full_plane_materializations), (1, 0))

    def test_004_section_bounds_and_wrong_hdu_fail_closed(self):
        accessor = stage.BoundedSectionAccessor()
        with self.assertRaisesRegex(stage.NativeExtractionError, "SECTION_BOUNDS_INVALID"):
            accessor.read(Path("unused"), 1, [-1, 0, 128, 129], [300, 300])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plain.fits"
            fits.HDUList([fits.PrimaryHDU(np.zeros((300, 300), dtype=np.int16))]).writeto(path)
            with self.assertRaisesRegex(stage.NativeExtractionError,
                                        "SOURCE_NOT_TILED_COMPRESSED_IMAGE"):
                accessor.read(path, 0, [0, 0, 129, 129], [300, 300])

    def test_005_writer_preserves_byte_order_nan_payload_inf_and_signed_zero(self):
        bits = np.zeros(stage.ARRAY_SHAPE, dtype=">u4")
        bits.flat[:5] = [0x7FC12345, 0x7F800000, 0xFF800000, 0x80000000, 0]
        source = bits.view(">f4")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "value.npy"
            observed = stage.write_canonical_npy(path, source)
            with path.open("rb") as handle:
                restored = np.lib.format.read_array(handle, allow_pickle=False)
            self.assertEqual(restored.dtype.str, ">f4")
            self.assertEqual(restored.tobytes(), source.tobytes())
            self.assertEqual(observed["array_content_sha256"], stage.array_content_hash(source))
            self.assertEqual(path.read_bytes()[:6], b"\x93NUMPY")
            self.assertEqual(path.read_bytes()[6:8], b"\x01\x00")

    def test_006_array_content_hash_uses_frozen_domain_and_metadata(self):
        value = np.arange(129 * 129, dtype="<i2").reshape(129, 129)
        metadata = {"dtype": value.dtype.str, "order": "C", "shape": [129, 129]}
        expected = hashlib.sha256(stage.ARRAY_HASH_PREFIX + canonical(metadata) + b"\n" +
                                  value.tobytes(order="C")).hexdigest()
        self.assertEqual(stage.array_content_hash(value), expected)

    def test_007_wcs_translation_is_mechanical_and_reproducible(self):
        result = stage.wcs_provenance(tan_header((3600, 3600)), [123, 456, 252, 585])
        cards = dict(result["translated_wcs_cards"])
        self.assertEqual(cards["CRPIX1"], 151.0 - 123)
        self.assertEqual(cards["CRPIX2"], 151.0 - 456)
        self.assertLessEqual(result["residual_upper_bound_pixels"], 1e-6)
        self.assertEqual(result, stage.wcs_provenance(
            tan_header((3600, 3600)), [123, 456, 252, 585]))

    def test_008_distorted_or_non_tan_wcs_is_rejected(self):
        header = tan_header()
        header["CTYPE1"] = "RA---SIN"
        header["CTYPE2"] = "DEC--SIN"
        with self.assertRaisesRegex(stage.NativeExtractionError, "PARENT_WCS_UNSUPPORTED"):
            stage.wcs_provenance(header, [64, 64, 193, 193])

    def test_009_science_summary_fields_are_rejected_recursively(self):
        for key in ("mean", "histogram", "morphology", "flux"):
            with self.subTest(key=key), self.assertRaisesRegex(
                    stage.NativeExtractionError, "SCIENCE_STATISTIC_FIELD_FORBIDDEN"):
                stage._assert_no_science_fields({"nested": [{key: 0}]})

    def test_010_source_tree_has_no_network_client_or_full_plane_access(self):
        source = (PROJECT / "oc3/oc3lib/native_extraction.py").read_text()
        for forbidden in ("import requests", "import urllib", "import socket",
                          "urlopen(", "hdu.data", ".getdata("):
            self.assertNotIn(forbidden, source)
        self.assertIn("hdu.section[y0:y1, x0:x1]", source)

    def test_011_atomic_promotion_and_second_target_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            staging = Path(tmp) / "STAGING"
            raw = Path(tmp) / "RAW_IMMUTABLE"
            staging.mkdir()
            (staging / "x").write_bytes(b"x")
            stage._promote(staging, raw)
            self.assertFalse(staging.exists())
            self.assertEqual((raw / "x").read_bytes(), b"x")
            again = Path(tmp) / "STAGING2"
            again.mkdir()
            with self.assertRaisesRegex(stage.NativeExtractionError,
                                        "ATOMIC_PROMOTION_PRECONDITION_FAILED"):
                stage._promote(again, raw)

    def test_012_complete_synthetic_publication_is_exact_and_immutable(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "oc3/TECHNICAL_INDEX").mkdir(parents=True)
            accessor = FakeAccessor()
            with patch.object(stage, "build_plan", return_value=synthetic_plan()):
                terminal = stage.execute(project, accessor=accessor)
            self.assertEqual(terminal["state"], stage.SUCCESS)
            self.assertEqual(terminal["crop_arrays"], 78)
            self.assertEqual(terminal["network_requests"], 0)
            manifest_path = project / stage.MANIFEST_RELATIVE
            manifest = stage._canonical_load(manifest_path)
            stage._verify_seal(manifest)
            self.assertEqual(set(manifest), {
                "schema_version", "stage_id", "state", "authority_bindings",
                "format_contract", "crops", "psf_mappings", "aggregate", "sealed"})
            self.assertEqual(len(list((project / stage.STAGE_ROOT_RELATIVE /
                                       "RAW_IMMUTABLE").glob("*/*.npy"))), 78)
            self.assertEqual(manifest_path.stat().st_mode & 0o222, 0)
            for row in manifest["crops"]:
                artifact = project / row["artifact_path"]
                self.assertEqual(file_hash(artifact), row["artifact_sha256"])
                self.assertEqual(artifact.stat().st_mode & 0o222, 0)
            with patch.object(stage, "build_plan") as forbidden_plan:
                with self.assertRaisesRegex(stage.NativeExtractionError,
                                            "SECOND_PUBLICATION_REFUSED"):
                    stage.execute(project)
                forbidden_plan.assert_not_called()

    def test_013_failure_never_publishes_manifest(self):
        class Broken(FakeAccessor):
            def read(self, *args, **kwargs):
                raise stage.NativeExtractionError("SYNTHETIC_DECODE_FAILURE")
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "oc3/TECHNICAL_INDEX").mkdir(parents=True)
            with patch.object(stage, "build_plan", return_value=synthetic_plan()):
                with self.assertRaisesRegex(stage.NativeExtractionError,
                                            "SYNTHETIC_DECODE_FAILURE"):
                    stage.execute(project, accessor=Broken())
            self.assertFalse((project / stage.MANIFEST_RELATIVE).exists())
            terminal = stage._canonical_load(project / stage.STAGE_ROOT_RELATIVE /
                                             "OC3_NATIVE_EXTRACTION_TERMINAL.json")
            self.assertEqual(terminal["state"], stage.FAILURE)
            self.assertFalse(terminal["published_manifest"])

    def test_014_cli_exposes_only_offline_validation_and_extraction_modes(self):
        help_text = cli.parser().format_help()
        self.assertIn("--validate-inputs", help_text)
        self.assertIn("--extract", help_text)
        self.assertNotIn("network", help_text.lower())
        with patch.object(cli, "validate_inputs", return_value={"state": "ok"}) as validate:
            self.assertEqual(cli.main(["--validate-inputs", "--project", str(PROJECT)]), 0)
            validate.assert_called_once()

    def test_015_wrong_frozen_hash_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            relative = Path("input.bin")
            (project / relative).write_bytes(b"wrong")
            with self.assertRaisesRegex(stage.NativeExtractionError,
                                        "FROZEN_INPUT_HASH_MISMATCH"):
                stage._exact_file(project, relative, "0" * 64)

    def test_016_accessor_never_touches_full_data_and_exposes_only_requested_pixels(self):
        parent = np.arange(300 * 300, dtype=np.int16).reshape(300, 300)

        class Section:
            def __getitem__(self, key):
                self.key = key
                return parent[key]

        class Compressed:
            def __init__(self):
                self._data_loaded = False
                self.header = tan_header()
                self.section = Section()

            @property
            def data(self):
                raise AssertionError("FULL_PLANE_DATA_ACCESSED")

        hdu = Compressed()

        class Context(list):
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        class FitsModule:
            CompImageHDU = Compressed

            @staticmethod
            def open(*args, **kwargs):
                return Context([None, hdu])

        accessor = stage.BoundedSectionAccessor(FitsModule)
        result, _ = accessor.read(Path("synthetic"), 1, [71, 83, 200, 212], [300, 300])
        self.assertEqual(hdu.section.key, (slice(83, 212), slice(71, 200)))
        self.assertEqual(result.tobytes(), parent[83:212, 71:200].tobytes())
        self.assertEqual(result.size, 129 * 129)
        self.assertEqual(accessor.unauthorized_pixels_exposed, 0)

    def test_017_companion_serialization_never_mutates_image(self):
        image = np.arange(129 * 129, dtype=np.float32).reshape(129, 129)
        image_before = image.tobytes()
        invvar = np.ones((129, 129), dtype=np.float32)
        maskbits = np.ones((129, 129), dtype=np.int16)
        with tempfile.TemporaryDirectory() as tmp:
            stage.write_canonical_npy(Path(tmp) / "invvar.npy", invvar)
            stage.write_canonical_npy(Path(tmp) / "maskbits.npy", maskbits)
        self.assertEqual(image.tobytes(), image_before)


if __name__ == "__main__":
    unittest.main()
