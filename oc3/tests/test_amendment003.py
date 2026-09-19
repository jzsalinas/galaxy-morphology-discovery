"""Amendment-003 provider boundary tests. Every FITS byte is generated locally."""
from __future__ import annotations

from dataclasses import fields, replace
from pathlib import Path
import re
from types import MappingProxyType
import tempfile
import unittest

import numpy as np
from astropy.io import fits

from oc3lib.bootstrap import (brick_order, resolve_bootstrap_bricks,
                              validate_literal_resource)
from oc3lib.core import InputError, IntegrityError, canonical, digest, file_hash
from oc3lib.provider_schema import *

TFORM = re.compile(r"^(\d*)([AIJEDL])$")


def _dtype(tform):
    match = TFORM.fullmatch(tform)
    repeat = int(match.group(1) or "1")
    code = match.group(2)
    dtype = {"A": "S%d" % repeat, "I": np.int16, "J": np.int32,
             "E": np.float32, "D": np.float64, "L": bool}[code]
    return repeat, code, dtype


def _default(field_id, row, name):
    stable = int(name[-3:]) - 1 if len(name) >= 3 and name[-3:].isdigit() else row
    root = {
        FieldId.ROOT_BRICKNAME: name, FieldId.ROOT_BRICKID: 100 + stable,
        FieldId.ROOT_BRICKQ: 1, FieldId.ROOT_BRICKROW: 10 + stable,
        FieldId.ROOT_BRICKCOL: 20 + stable, FieldId.ROOT_RA: 10.0 + stable,
        FieldId.ROOT_DEC: 20.0 + stable, FieldId.ROOT_RA1: 9.0 + stable,
        FieldId.ROOT_RA2: 11.0 + stable, FieldId.ROOT_DEC1: 19.0 + stable,
        FieldId.ROOT_DEC2: 21.0 + stable,
    }
    if field_id in root:
        return root[field_id]
    regional = {
        FieldId.REG_BRICKNAME: name, FieldId.REG_RA: 10.0 + stable,
        FieldId.REG_DEC: 20.0 + stable, FieldId.REG_NEXP_G: 1,
        FieldId.REG_NEXP_R: 1, FieldId.REG_NEXP_Z: 1,
        FieldId.REG_NEXPHIST_G: (0, 100 + stable, 0, 0, 0, 0),
        FieldId.REG_NEXPHIST_R: (0, 110 + stable, 0, 0, 0, 0),
        FieldId.REG_NEXPHIST_Z: (0, 120 + stable, 0, 0, 0, 0),
        FieldId.REG_BRICKID: 100 + stable, FieldId.REG_RA1: 9.0 + stable,
        FieldId.REG_RA2: 11.0 + stable, FieldId.REG_DEC1: 19.0 + stable,
        FieldId.REG_DEC2: 21.0 + stable, FieldId.REG_AREA: 4.0,
        FieldId.REG_SURVEY_PRIMARY: True,
    }
    if field_id in regional:
        return regional[field_id]
    logical = FIELD_BY_ID[field_id].logical_type
    if logical in ("int16", "int32"):
        return 30000 - row
    if logical == "float32":
        return np.float32(12345.5 + row)
    if logical == "int16[4]":
        return (30000 - row, 29999 - row, 29998 - row, 29997 - row)
    if logical == "float32[4]":
        return tuple(np.float32(12340 + row + i) for i in range(4))
    if logical == "boolean":
        return bool(row % 2)
    raise AssertionError(field_id)


def write_fixture(path: Path, contract: PhysicalContract, names=("SYN001",),
                  overrides=None, omit=None, format_overrides=None,
                  unknown=False, table_hdu=1, header_edits=None):
    overrides = overrides or {}
    omit = set(omit or ())
    format_overrides = format_overrides or {}
    columns = []
    for physical in contract.fields:
        if physical.field_id in omit:
            continue
        logical = FIELD_BY_ID[physical.field_id]
        tform = format_overrides.get(physical.field_id, physical.tform)
        values = overrides.get(physical.field_id)
        if values is None:
            values = [_default(physical.field_id, index, name)
                      for index, name in enumerate(names)]
        repeat, code, dtype = _dtype(tform)
        array = np.asarray(values, dtype=dtype)
        columns.append(fits.Column(name=logical.provider_name, format=tform, array=array))
    if unknown:
        columns.append(fits.Column(name="UNREVIEWED_SENTINEL_COLUMN", format="J",
                                   array=np.asarray([987654] * len(names), dtype=np.int32)))
    table = fits.BinTableHDU.from_columns(columns)
    if header_edits:
        for key, value in header_edits.items():
            table.header[key] = value
    hdus = [fits.PrimaryHDU()]
    while len(hdus) < table_hdu:
        hdus.append(fits.ImageHDU(data=np.zeros((1, 1), dtype=np.int16)))
    hdus.append(table)
    fits.HDUList(hdus).writeto(path, overwrite=False, checksum=False)
    return path


class Amendment003Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="oc3_A003_SYNTHETIC_")
        self.root = Path(self.tmp.name)
        self.adapter = ProviderSchemaAdapter()
        self.root_identity = ProviderIdentity(ProviderRole.ROOT_GEOMETRY, "SYNTHETIC",
                                              "DR9", None, None, "DR9",
                                              ("SYNTHETIC_ROOT_IDENTITY",))
        self.north_identity = ProviderIdentity(ProviderRole.REGIONAL_NORTH, "SYNTHETIC",
                                               "DR9", "north", "BASS_MzLS", "9011",
                                               ("SYNTHETIC_NORTH_IDENTITY",))
        self.south_identity = ProviderIdentity(ProviderRole.REGIONAL_SOUTH, "SYNTHETIC",
                                               "DR9", "south", "DECaLS", None,
                                               ("SYNTHETIC_SOUTH_IDENTITY",))
        self.south_contract = replace(SYNTHETIC_REGIONAL_FITS_V2,
                                      contract_id="SYNTHETIC_REGIONAL_SOUTH_FITS_V1",
                                      role=ProviderRole.REGIONAL_SOUTH)

    def tearDown(self):
        self.tmp.cleanup()

    def decode_root(self, names=("SYN001",), **kwargs):
        path = write_fixture(self.root / ("root_%d.fits" % len(list(self.root.glob("root_*.fits")))),
                             SYNTHETIC_ROOT_FITS_V1, names, **kwargs)
        return self.adapter.decode(path, self.root_identity, file_hash(path),
                                   SYNTHETIC_ROOT_FITS_V1)

    def decode_regional(self, region="north", names=("SYN001",), probe=None, **kwargs):
        contract = SYNTHETIC_REGIONAL_FITS_V2 if region == "north" else self.south_contract
        identity = self.north_identity if region == "north" else self.south_identity
        path = write_fixture(self.root / ("reg_%d.fits" % len(list(self.root.glob("reg_*.fits")))),
                             contract, names, **kwargs)
        return self.adapter.decode(path, identity, file_hash(path), contract, probe), path

    def pair(self, region="north", names=("SYN001",), root_kwargs=None,
             regional_kwargs=None, membership=None):
        root = self.decode_root(names, **(root_kwargs or {}))
        regional, _ = self.decode_regional(region, names, **(regional_kwargs or {}))
        identity = self.north_identity if region == "north" else self.south_identity
        return build_technical_candidates(root, regional, identity, membership)

    def selection_with_north(self, north_candidates):
        south, _ = self.pair("south", names=("SYN900",),
                             membership=SyntheticPatchMembership(["SYN900"]))
        return resolve_bootstrap_bricks(tuple(south) + tuple(north_candidates))

    # 1. Complete schema and exact selective projection.
    def test_01_complete_valid_regional_schema(self):
        probe = CellAccessProbe()
        table, _ = self.decode_regional(probe=probe)
        self.assertEqual(len(table.rows), 1)
        self.assertEqual(set(table.rows[0]), {f.field_id for f in REGIONAL_ALLOWED_FIELDS})
        self.assertEqual(probe.forbidden_accesses, [])

    # 2 and 35. Forbidden columns exist, contain sentinels, and are never accessed.
    def test_02_forbidden_fields_present_but_inaccessible(self):
        probe = CellAccessProbe()
        table, _ = self.decode_regional(probe=probe)
        self.assertFalse(any(f.field_id in table.rows[0] for f in REGIONAL_FORBIDDEN_FIELDS))
        self.assertEqual(probe.forbidden_accesses, [])
        self.assertEqual(len(probe.allowed_accesses), len(REGIONAL_ALLOWED_FIELDS))

    def test_03_forbidden_source_cannot_map_to_allowed_target(self):
        bad = PhysicalContract("BAD_FREEFORM", 1, ProviderRole.REGIONAL_NORTH, 1,
                              (PhysicalField(FieldId.REG_NOBJS, "I"),), True)
        path = self.root / "bad_source.fits"
        write_fixture(path, bad)
        with self.assertRaisesRegex(InputError, SCHEMA_CONFLICT):
            self.adapter.decode(path, self.north_identity, file_hash(path), bad)

    # 4 and 34. Unknown schema stops before rows and does not leak the name.
    def test_04_unknown_column_rejected_before_row_iteration(self):
        path = write_fixture(self.root / "unknown.fits", SYNTHETIC_REGIONAL_FITS_V2,
                             unknown=True)
        probe = CellAccessProbe()
        with self.assertRaises(InputError) as caught:
            self.adapter.decode(path, self.north_identity, file_hash(path),
                                SYNTHETIC_REGIONAL_FITS_V2, probe)
        self.assertEqual(str(caught.exception), SCHEMA_CONFLICT)
        self.assertNotIn("UNREVIEWED_SENTINEL_COLUMN", str(caught.exception))
        self.assertEqual(probe.rows_started, 0)

    def test_05_missing_allowed_column_fails(self):
        path = write_fixture(self.root / "missing.fits", SYNTHETIC_REGIONAL_FITS_V2,
                             omit={FieldId.REG_NEXP_G})
        with self.assertRaisesRegex(InputError, SCHEMA_CONFLICT):
            self.adapter.decode(path, self.north_identity, file_hash(path),
                                SYNTHETIC_REGIONAL_FITS_V2)

    def test_06_dtype_mismatch_fails(self):
        path = write_fixture(self.root / "dtype.fits", SYNTHETIC_REGIONAL_FITS_V2,
                             format_overrides={FieldId.REG_NEXP_G: "J"})
        with self.assertRaisesRegex(InputError, SCHEMA_CONFLICT):
            self.adapter.decode(path, self.north_identity, file_hash(path),
                                SYNTHETIC_REGIONAL_FITS_V2)

    def test_07_vector_shape_mismatch_fails(self):
        path = write_fixture(self.root / "shape.fits", SYNTHETIC_REGIONAL_FITS_V2,
                             format_overrides={FieldId.REG_NEXPHIST_G: "5J"},
                             overrides={FieldId.REG_NEXPHIST_G: [(0, 1, 2, 3, 4)]})
        with self.assertRaisesRegex(InputError, SCHEMA_CONFLICT):
            self.adapter.decode(path, self.north_identity, file_hash(path),
                                SYNTHETIC_REGIONAL_FITS_V2)

    def test_08_hdu_mismatch_fails(self):
        path = write_fixture(self.root / "hdu.fits", SYNTHETIC_REGIONAL_FITS_V2,
                             table_hdu=2)
        with self.assertRaisesRegex(InputError, SCHEMA_CONFLICT):
            self.adapter.decode(path, self.north_identity, file_hash(path),
                                SYNTHETIC_REGIONAL_FITS_V2)

    def test_09_unexpected_scaling_fails(self):
        path = write_fixture(self.root / "scaling.fits", SYNTHETIC_REGIONAL_FITS_V2,
                             header_edits={"TSCAL4": 2})
        with self.assertRaisesRegex(InputError, SCHEMA_CONFLICT):
            self.adapter.decode(path, self.north_identity, file_hash(path),
                                SYNTHETIC_REGIONAL_FITS_V2)

    def test_10_unexpected_null_semantics_fails(self):
        path = write_fixture(self.root / "null.fits", SYNTHETIC_REGIONAL_FITS_V2,
                             header_edits={"TNULL4": -32768})
        with self.assertRaisesRegex(InputError, SCHEMA_CONFLICT):
            self.adapter.decode(path, self.north_identity, file_hash(path),
                                SYNTHETIC_REGIONAL_FITS_V2)

    def test_11_no_forbidden_values_in_dto_or_errors(self):
        candidates, audits = self.pair()
        encoded = candidate_bytes(candidates[0]) + canonical(audit_object(audits[0]))
        self.assertNotIn(b"12345.5", encoded)
        self.assertNotIn(b"30000", encoded)
        self.assertFalse(any(f.field_id.value.encode() in encoded for f in REGIONAL_FORBIDDEN_FIELDS))

    def test_12_grz_true_at_one_one_one(self):
        self.assertTrue(grz_median_present_v1(1, 1, 1))

    def test_13_grz_zero_g_false(self):
        self.assertFalse(grz_median_present_v1(0, 1, 1))

    def test_14_grz_zero_r_false(self):
        self.assertFalse(grz_median_present_v1(1, 0, 1))

    def test_15_grz_zero_z_false(self):
        self.assertFalse(grz_median_present_v1(1, 1, 0))

    def test_16_invalid_null_noninteger_nexp_fails(self):
        for value in (None, 1.0, np.int16(1), True, (1,)):
            with self.subTest(value=repr(value)), self.assertRaises(InputError):
                grz_median_present_v1(value, 1, 1)

    def test_17_nexp_magnitude_does_not_affect_candidate_or_order(self):
        first, _ = self.pair(regional_kwargs={"overrides": {
            FieldId.REG_NEXP_G: [1], FieldId.REG_NEXP_R: [1], FieldId.REG_NEXP_Z: [1]}})
        second, _ = self.pair(regional_kwargs={"overrides": {
            FieldId.REG_NEXP_G: [9], FieldId.REG_NEXP_R: [8], FieldId.REG_NEXP_Z: [7]}})
        self.assertEqual(candidate_bytes(first[0]), candidate_bytes(second[0]))
        self.assertEqual(self.selection_with_north(first), self.selection_with_north(second))

    def test_18_nexphist_does_not_affect_candidate_or_order(self):
        first, _ = self.pair()
        altered = {FieldId.REG_NEXPHIST_G: [(9, 8, 7, 6, 5, 4)],
                   FieldId.REG_NEXPHIST_R: [(1, 2, 3, 4, 5, 6)],
                   FieldId.REG_NEXPHIST_Z: [(6, 5, 4, 3, 2, 1)]}
        second, audits = self.pair(regional_kwargs={"overrides": altered})
        self.assertEqual(candidate_bytes(first[0]), candidate_bytes(second[0]))
        self.assertEqual(self.selection_with_north(first), self.selection_with_north(second))
        self.assertNotEqual(audits[0].nexphist_g, (0, 100, 0, 0, 0, 0))

    def test_19_north_generation_exactly_9011(self):
        candidates, _ = self.pair()
        self.assertEqual((candidates[0].generation, candidates[0].corrected_9012),
                         ("9011", False))

    def test_20_north_never_calls_patch_list(self):
        class Explodes:
            def contains(self, name):
                raise AssertionError("NORTH_PATCH_LIST_FORBIDDEN")
        candidates, _ = self.pair(membership=Explodes())
        self.assertEqual(len(candidates), 1)

    def test_21_south_exact_membership_required(self):
        candidates, _ = self.pair("south", membership=SyntheticPatchMembership(["SYN001"]))
        self.assertEqual((len(candidates), candidates[0].generation,
                          candidates[0].corrected_9012), (1, "9012", True))

    def test_22_south_nonmember_has_no_replacement(self):
        candidates, _ = self.pair("south", names=("SYN001", "SYN002"),
                                  membership=SyntheticPatchMembership(["SYN002"]))
        self.assertEqual([candidate.brickname for candidate in candidates], ["SYN002"])

    def test_23_duplicate_join_rejected(self):
        root = self.decode_root(("SYN001", "SYN001"))
        regional, _ = self.decode_regional(names=("SYN001",))
        with self.assertRaisesRegex(InputError, "PROVIDER_JOIN_DUPLICATE"):
            build_technical_candidates(root, regional, self.north_identity)

    def test_24_missing_join_rejected(self):
        root = self.decode_root(("SYN002",))
        regional, _ = self.decode_regional(names=("SYN001",))
        with self.assertRaisesRegex(InputError, "PROVIDER_JOIN_MISSING_ROOT"):
            build_technical_candidates(root, regional, self.north_identity)

    def test_25_conflicting_join_rejected_without_coercion(self):
        root = self.decode_root()
        regional, _ = self.decode_regional(overrides={FieldId.REG_BRICKID: [101]})
        with self.assertRaisesRegex(InputError, "PROVIDER_JOIN_IDENTITY_CONFLICT"):
            build_technical_candidates(root, regional, self.north_identity)

    def test_26_case_alias_not_normalized(self):
        root = self.decode_root(("SYN001",))
        regional, _ = self.decode_regional(names=("syn001",))
        with self.assertRaisesRegex(InputError, "PROVIDER_JOIN_MISSING_ROOT"):
            build_technical_candidates(root, regional, self.north_identity)

    def test_27_provider_row_permutation_invariant(self):
        first, _ = self.pair(names=("SYN001", "SYN002"))
        second, _ = self.pair(names=("SYN002", "SYN001"))
        self.assertEqual([candidate_bytes(x) for x in first],
                         [candidate_bytes(x) for x in second])
        self.assertEqual(self.selection_with_north(first), self.selection_with_north(second))

    def test_28_forbidden_values_arbitrary_no_effect(self):
        first, _ = self.pair()
        changed = {field.field_id: [_default(field.field_id, 0, "SYN001")]
                   for field in REGIONAL_FORBIDDEN_FIELDS}
        for field in REGIONAL_FORBIDDEN_FIELDS:
            logical = field.logical_type
            if logical in ("int16", "int32"): changed[field.field_id] = [-30000]
            elif logical == "float32": changed[field.field_id] = [np.float32(-23456.5)]
            elif logical == "int16[4]": changed[field.field_id] = [(-1, -2, -3, -4)]
            elif logical == "float32[4]": changed[field.field_id] = [(-1., -2., -3., -4.)]
            elif logical == "boolean": changed[field.field_id] = [True]
        second, _ = self.pair(regional_kwargs={"overrides": changed})
        self.assertEqual(candidate_bytes(first[0]), candidate_bytes(second[0]))
        self.assertEqual(self.selection_with_north(first), self.selection_with_north(second))

    def test_29_brickid_amendment004_correction_and_history(self):
        path = write_fixture(self.root / "brickid_conflict.fits",
                             SYNTHETIC_REGIONAL_FITS_V2,
                             format_overrides={FieldId.REG_BRICKID: "I"})
        with self.assertRaisesRegex(InputError, SCHEMA_CONFLICT):
            self.adapter.decode(path, self.north_identity, file_hash(path),
                                SYNTHETIC_REGIONAL_FITS_V2)
        self.assertEqual(BRICKID_STATUS, "BRICKID_PHYSICAL_LAYOUT_CORRECTED_AMENDMENT_004")
        self.assertEqual(HISTORICAL_BRICKID_STATUS, "DOCUMENTED_PROVIDER_TYPE_INCONSISTENCY")
        self.assertEqual(HISTORICAL_LOGICAL_CONTRACT_VERSION, "OC3_DR9_PROVIDER_LOGICAL_V1")
        self.assertEqual(HISTORICAL_LOGICAL_CONTRACT_SHA256,
                         digest(canonical(historical_logical_contract_object())))

    def test_30_production_patch_adapter_disabled(self):
        with self.assertRaisesRegex(InputError, PATCH_LIST_STATUS):
            PatchListSchemaAdapter().decode_production(self.root / "never-read.fits")

    def test_31_stable_field_ids_reject_free_form_source(self):
        resource = {"id": "x", "url": "https://synthetic.invalid/x", "method": "GET",
                    "role": "brick_geometry", "host": "synthetic.invalid",
                    "release": "DR9", "generation": "DR9", "max_bytes": 10,
                    "sha256": "0" * 64, "evidence_ref": "synthetic",
                    "decoder": "JSON_ROWS_V1", "projection": {"grz": "nobjs"}}
        with self.assertRaisesRegex(InputError, "LEGACY_PROVIDER_PROJECTION_FORBIDDEN"):
            validate_literal_resource(resource, ["synthetic.invalid"], "PRODUCTION")

    def test_32_raw_provider_table_cannot_reach_selector(self):
        with self.assertRaisesRegex(InputError, "RAW_PROVIDER_TABLE_FORBIDDEN"):
            resolve_bootstrap_bricks([{"region": "north"}])

    def test_33_candidate_canonicalization_deterministic(self):
        candidates, _ = self.pair()
        self.assertEqual(candidate_bytes(candidates[0]), candidate_bytes(candidates[0]))
        self.assertEqual(candidate_sha256(candidates[0]), digest(candidate_bytes(candidates[0])))
        self.assertTrue(candidate_bytes(candidates[0]).endswith(b"\n"))

    def test_34_candidate_exact_fields_no_audit_or_forbidden(self):
        candidates, _ = self.pair()
        self.assertEqual([field.name for field in fields(candidates[0])],
                         ["region", "survey", "release_family", "generation", "brickname",
                          "brickid", "ra", "dec", "primary_bounds", "grz",
                          "corrected_9012", "survey_primary", "evidence_refs"])
        payload = candidate_object(candidates[0])["candidate"]
        self.assertNotIn("nexp_g", payload)
        self.assertNotIn("nexphist_g", payload)
        self.assertNotIn("nobjs", payload)

    def test_35_grz_audit_does_not_influence_ordering(self):
        candidates, audits = self.pair(names=("SYN001", "SYN002"))
        before = self.selection_with_north(candidates)
        altered = tuple(replace(audit, nexp_g=30000,
                                nexphist_g=(9, 9, 9, 9, 9, 9)) for audit in audits)
        self.assertNotEqual(audits, altered)
        self.assertEqual(before, self.selection_with_north(candidates))

    def test_36_synthetic_physical_contract_mismatch_stops(self):
        path = write_fixture(self.root / "physical_mismatch.fits",
                             SYNTHETIC_REGIONAL_FITS_V2)
        mismatched = replace(SYNTHETIC_REGIONAL_FITS_V2, hdu_index=2)
        with self.assertRaisesRegex(InputError, SCHEMA_CONFLICT):
            self.adapter.decode(path, self.north_identity, file_hash(path), mismatched)

    def test_37_missing_production_physical_contract_blocks(self):
        identity = ProviderIdentity(ProviderRole.REGIONAL_NORTH, "PRODUCTION", "DR9",
                                    "north", "BASS_MzLS", "9011", ("PRODUCTION",))
        with self.assertRaisesRegex(InputError, "PRODUCTION_PROVIDER_DECODE_NOT_ENABLED"):
            self.adapter.decode(self.root / "not-opened.fits", identity, "0" * 64)

    def test_38_checksum_verified_before_fits(self):
        path = write_fixture(self.root / "checksum.fits", SYNTHETIC_REGIONAL_FITS_V2)
        with self.assertRaisesRegex(IntegrityError, "PROVIDER_CHECKSUM_MISMATCH"):
            self.adapter.decode(path, self.north_identity, "0" * 64,
                                SYNTHETIC_REGIONAL_FITS_V2)

    def test_39_provider_manifest_binding_versions(self):
        binding = provider_manifest_binding()
        self.assertEqual(binding["adapter_version"], ADAPTER_VERSION)
        self.assertEqual(binding["candidate_dto_version"], CANDIDATE_DTO_VERSION)
        self.assertEqual(binding["logical_contract_sha256"], LOGICAL_CONTRACT_SHA256)
        self.assertEqual(validate_provider_manifest_binding(binding, production=False), binding)

    def test_40_production_binding_without_physical_contract_blocks(self):
        with self.assertRaisesRegex(InputError, "PRODUCTION_PROVIDER_PHYSICAL_CONTRACT_UNAVAILABLE"):
            validate_provider_manifest_binding(provider_manifest_binding(), production=True)


if __name__ == "__main__":
    unittest.main()
