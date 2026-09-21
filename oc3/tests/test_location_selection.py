"""Focused synthetic tests for the frozen offline location selector."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

import oc3_location_selection as cli
import oc3lib.location_selection as stage
from oc3lib.core import canonical


def simple_wcs(crval=(10.0, 0.0), shape=(384, 384)) -> WCS:
    value = WCS(naxis=2)
    value.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    value.wcs.crval = list(crval)
    value.wcs.crpix = [shape[1] / 2 + .5, shape[0] / 2 + .5]
    value.wcs.cd = [[-1 / 3600, 0], [0, 1 / 3600]]
    return value


def bundle(region="south", *, permuted=False, weak_n3=False) -> stage.RegionBundle:
    shape = (384, 384)
    primary = np.zeros(shape, dtype=bool)
    primary[80:305, 80:305] = True
    nexp = {band: np.full(shape, 2, dtype=np.int16) for band in stage.BANDS}
    # N2 class 0 around (64,64); class 1 remains available elsewhere.
    nexp["g"][0:129, 0:65] = 0
    nexp["r"][128:257, 128:257] = 1
    mask = np.zeros(shape, dtype=np.int16)
    mask[300:321, 300:321] = 1 << 3
    psf = {}
    yy, xx = np.indices(shape)
    for index, band in enumerate(stage.BANDS):
        if weak_n3:
            values = np.full(shape, 1.0 + index * .01, dtype=np.float32)
        else:
            values = (1.0 + index * .05 + xx / 2000 + yy / 4000).astype(np.float32)
        psf[band] = values
    items = [*(("nexp", band, nexp[band]) for band in stage.BANDS),
             *(("psfsize", band, psf[band]) for band in stage.BANDS),
             ("maskbits", None, mask)]
    if permuted:
        items = list(reversed(items))
    arrays = {(product, band): array for product, band, array in items}
    wcs = simple_wcs(shape=shape)
    return stage.RegionBundle(region, "synthetic", arrays, {}, wcs,
                              (9.9, 10.1, -.1, .1), primary, {}, 0.0)


def location(slot, region, brick, x, y, *, value=None, status="SELECTED"):
    return {"slot": slot, "region": region, "brick": brick, "x": x, "y": y,
            "ra_dec": [10.0, 0.0], "window": stage._window(x, y),
            "selection_hash": stage.selection_hash(slot, region, brick, x, y),
            "status": status, "V": value}


class LocationSelectionTests(unittest.TestCase):
    def test_001_exact_reticle(self):
        self.assertEqual(stage.reticle(130), (0, 64, 128, 129))
        self.assertEqual(stage.reticle(128), (0, 64, 127))

    def test_002_full_129_geometry(self):
        centers = stage.complete_centers((256, 256))
        self.assertEqual(centers, ((64, 64), (128, 64), (64, 128), (128, 128)))
        self.assertEqual(stage._window(64, 64)["requested"], [0, 0, 129, 129])

    def test_003_edge_rejection(self):
        self.assertNotIn((0, 0), stage.complete_centers((3600, 3600)))
        self.assertNotIn((3584, 3584), stage.complete_centers((3600, 3600)))
        self.assertIn((3520, 3520), stage.complete_centers((3600, 3600)))

    def test_004_ra_wrap(self):
        values = np.asarray([359.9, .1, 180.0])
        np.testing.assert_array_equal(stage.ra_in_bounds(values, 359.5, .5), [True, True, False])

    def test_005_primary_wcs_logic(self):
        wcs = simple_wcs(crval=(359.9, 0.0), shape=(32, 32))
        mask = stage.primary_mask(wcs, (32, 32), (359.898, 359.902, -.002, .002), chunk_rows=7)
        self.assertTrue(mask[16, 16])
        self.assertFalse(mask[0, 0])

    def test_006_boundary_distance(self):
        values = np.zeros((129, 129), dtype=bool)
        values[:, 65:] = True
        self.assertEqual(stage.boundary_distance(values), .5)

    def test_007_south_slots(self):
        selected, flow, _ = stage.select_region(bundle("south"))
        self.assertEqual([row[0] for row in selected], ["S1", "S2", "S3"])
        self.assertEqual(len({(row[1]["x"], row[1]["y"]) for row in selected}), 3)
        self.assertEqual([row["selected"] for row in flow], [1, 1, 1])

    def test_008_s1_interior(self):
        selected, _, _ = stage.select_region(bundle("south"))
        self.assertTrue(selected[0][1]["inside"])

    def test_009_s2_boundary_crossing(self):
        selected, _, _ = stage.select_region(bundle("south"))
        self.assertTrue(selected[1][1]["mixed"])
        self.assertIsNotNone(selected[1][1]["boundary_distance"])

    def test_010_s3_allowed_maskbits(self):
        selected, _, _ = stage.select_region(bundle("south"))
        self.assertTrue(selected[2][1]["allowed_mask"])

    def test_011_s3_excludes_wise_only(self):
        value = bundle("south")
        value.arrays[("maskbits", None)].fill((1 << 8) | (1 << 9))
        with self.assertRaisesRegex(stage.LocationSelectionError, "MISSING_SLOT_S3"):
            stage.select_region(value)

    def test_012_north_slot_order(self):
        selected, _, _ = stage.select_region(bundle("north"))
        self.assertEqual([row[0] for row in selected], ["N1", "N2", "N3"])

    def test_013_n1_interior(self):
        selected, _, _ = stage.select_region(bundle("north"))
        self.assertTrue(selected[0][1]["inside"])

    def test_014_n2_class_zero(self):
        arrays = [np.asarray([[0, 2]]), np.asarray([[2, 2]]), np.asarray([[2, 2]])]
        self.assertEqual(stage.n2_class(arrays), 0)

    def test_015_n2_class_one_fallback(self):
        arrays = [np.asarray([[1, 2]]), np.asarray([[2, 2]]), np.asarray([[2, 2]])]
        self.assertEqual(stage.n2_class(arrays), 1)

    def test_016_n3_calculation(self):
        base = np.ones((129, 129), dtype=np.float64)
        base[:, 65:] = 2.0
        arrays = [base.copy() for _ in range(3)]
        self.assertAlmostEqual(stage.n3_variation(arrays), 1.0)

    def test_017_n3_invalid_window(self):
        arrays = [np.ones((129, 129)) for _ in range(3)]
        arrays[1][0, 0] = 0
        self.assertIsNone(stage.n3_variation(arrays))

    def test_018_n3_not_exercised(self):
        selected, _, _ = stage.select_region(bundle("north", weak_n3=True))
        self.assertEqual(selected[2][2], "STRATUM_NOT_EXERCISED")
        self.assertLess(selected[2][1]["V"], .10)

    def test_019_without_replacement(self):
        selected, flow, _ = stage.select_region(bundle("south"))
        self.assertEqual(len({(row[1]["x"], row[1]["y"]) for row in selected}), 3)
        self.assertGreaterEqual(sum(row["already_used_exclusions"] for row in flow), 0)

    def test_020_hash_exact(self):
        expected = hashlib.sha256(b"OC3-v1|S1|south|3443m052|64|128").hexdigest()
        self.assertEqual(stage.selection_hash("S1", "south", "3443m052", 64, 128), expected)

    def test_021_provider_order_invariance(self):
        left = stage.select_region(bundle("north", permuted=False))[0]
        right = stage.select_region(bundle("north", permuted=True))[0]
        self.assertEqual([(s, r["x"], r["y"], st) for s, r, st in left],
                         [(s, r["x"], r["y"], st) for s, r, st in right])

    def test_022_tie_break(self):
        brick = "x"
        rows = [{"x": 128, "y": 64}, {"x": 64, "y": 64}]
        used = set()
        chosen, _ = stage._choose("S1", "south", brick, rows, used,
                                  lambda row: ("same", row["y"], row["x"]))
        self.assertEqual((chosen["x"], chosen["y"]), (64, 64))

    def test_023_missing_slot_failure(self):
        value = bundle("south")
        value.arrays[("maskbits", None)].fill(0)
        with self.assertRaises(stage.LocationSelectionError):
            stage.select_region(value)

    def test_024_unauthorized_observation_tripwire_before_open(self):
        guard = object.__new__(stage.AuxiliaryObservationGuard)
        guard._resources = {}
        guard._root = Path("/nonexistent")
        guard.observed = []
        with patch.object(stage.fits, "open") as opened:
            with self.assertRaisesRegex(stage.LocationSelectionError, "UNAUTHORIZED_PRODUCT_OBSERVATION"):
                guard.observe("south", "image", "r")
            opened.assert_not_called()

    def test_025_native_array_validation(self):
        header = fits.Header({"BRICK": "b", "LSDR": "DR9", "DRVERSIO": 9012,
                              "IMTYPE": "nexp", "CTYPE1": "RA---TAN", "CTYPE2": "DEC--TAN",
                              "CRVAL1": 10., "CRVAL2": 0., "CRPIX1": 1800.5, "CRPIX2": 1800.5,
                              "CD1_1": -1/3600, "CD1_2": 0., "CD2_1": 0., "CD2_2": 1/3600})
        wcs = stage._validate_array("south", "b", "nexp", "g",
                                    np.zeros((3600, 3600), dtype=np.int16), header, "int16")
        self.assertEqual(wcs.pixel_n_dim, 2)

    def test_026_negative_integer_rejected(self):
        header = fits.Header({"BRICK": "b", "LSDR": "DR9", "DRVERSIO": 9012,
                              "IMTYPE": "maskbits", "CTYPE1": "RA---TAN", "CTYPE2": "DEC--TAN",
                              "CRVAL1": 10., "CRVAL2": 0., "CRPIX1": 1800.5, "CRPIX2": 1800.5,
                              "CD1_1": -1/3600, "CD1_2": 0., "CD2_1": 0., "CD2_2": 1/3600})
        array = np.zeros((3600, 3600), dtype=np.int16); array[0, 0] = -1
        with self.assertRaises(stage.LocationSelectionError):
            stage._validate_array("south", "b", "maskbits", None, array, header, "int16")

    def test_027_manifest_schema_and_canonical_hash(self):
        bricks = {"south": "s", "north": "n"}
        rows = [location("S1", "south", "s", 64, 64),
                location("S2", "south", "s", 128, 64),
                location("S3", "south", "s", 192, 64),
                location("N1", "north", "n", 64, 64),
                location("N2", "north", "n", 128, 64),
                location("N3", "north", "n", 192, 64, value=.2)]
        manifest = {"binding": {}, "locations": rows,
                    "selection_sha256": hashlib.sha256(canonical(rows)).hexdigest()}
        stage.validate_locations_manifest(manifest, bricks)
        self.assertEqual(set(manifest), stage.MANIFEST_KEYS)

    def test_028_manifest_rejects_extra_field(self):
        bricks = {"south": "s", "north": "n"}
        rows = [location("S1", "south", "s", 64, 64)] * 6
        rows[0] = dict(rows[0], diagnostic="forbidden")
        manifest = {"binding": {}, "locations": rows,
                    "selection_sha256": hashlib.sha256(canonical(rows)).hexdigest()}
        with self.assertRaises(stage.LocationSelectionError):
            stage.validate_locations_manifest(manifest, bricks)

    def test_029_flow_has_no_candidate_coordinates(self):
        _, flow, _ = stage.select_region(bundle("south"))
        text = stage._flow_csv(flow).decode()
        self.assertNotIn(",x,", text)
        self.assertNotIn(",y,", text)
        self.assertEqual(text.count("\n"), 4)

    def test_030_cli_success_and_failure_terminals(self):
        with patch.object(cli, "dry_run", return_value={"state": "READY", "network_requests": 0}):
            self.assertEqual(cli.main(["--dry-run", "--offline"]), 0)
        with patch.object(cli, "dry_run", side_effect=stage.LocationSelectionError("TEST")):
            self.assertEqual(cli.main(["--dry-run", "--offline"]), 1)

    def test_031_cli_source_has_no_network_stack(self):
        source = Path(stage.__file__).read_text() + Path(cli.__file__).read_text()
        for forbidden in ("import socket", "import http", "import urllib", "from urllib",
                          "import requests", "from requests", "LiteralHTTPTransport"):
            self.assertNotIn(forbidden, source)

    def test_032_n3_status_threshold_is_frozen(self):
        selected, _, _ = stage.select_region(bundle("north", weak_n3=True))
        slot, row, status = selected[-1]
        self.assertEqual(slot, "N3")
        self.assertEqual(status, "STRATUM_NOT_EXERCISED")
        self.assertGreaterEqual(row["V"], 0)


if __name__ == "__main__":
    unittest.main()
