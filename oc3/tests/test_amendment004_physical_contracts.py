"""Amendment-004 contracts and POST_PROBE_001 synthetic/offline tests."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

import numpy as np
from astropy.io import fits

from oc3lib.core import InputError, IntegrityError, canonical, file_hash
from oc3lib.provider_physical_contracts import *
from oc3lib.provider_schema import *


PROJECT = Path(__file__).resolve().parents[2]
EXPECTED_CONTRACT_HASHES = {
    PhysicalRole.ROOT_SUMMARY: "6e50b8b0c258f10752bf2d7d7d2d88c64ec16899fbb02711fd0621e4d642ea53",
    PhysicalRole.NORTH_SUMMARY: "59fb8668165d14f201df1f269009ca0b47b41fa431b0bb0d55212c19c77f2677",
    PhysicalRole.SOUTH_SUMMARY: "2faad729eac8e1912f63e4da8373acdc7cd5e9101601ea51e8ec9fb145dc25fa",
    PhysicalRole.SOUTH_PATCH_LIST: "5be4df46180c0ec4964b53e3ad095bf75bf80a4c142dc7a8d22ba60efafbbd14",
}
FORBIDDEN_J_IDS = (
    FieldId.REG_NOBJS, FieldId.REG_NPSF, FieldId.REG_NSIM,
    FieldId.REG_NREX, FieldId.REG_NEXP, FieldId.REG_NDEV,
    FieldId.REG_NCOMP, FieldId.REG_NSER, FieldId.REG_NDUP,
)
GEOMETRY_D_IDS = (FieldId.REG_RA1, FieldId.REG_RA2, FieldId.REG_DEC1,
                  FieldId.REG_DEC2, FieldId.REG_AREA)


def _card(key, value=None):
    if value is None:
        text = key
    elif isinstance(value, bool):
        text = f"{key:<8}= {'T' if value else 'F':>20}"
    elif isinstance(value, str):
        text = f"{key:<8}= '{value}'"
    else:
        text = f"{key:<8}= {value:>20}"
    return text[:80].ljust(80).encode("ascii")


def _header(cards):
    raw = b"".join(cards) + _card("END")
    return raw + b" " * ((-len(raw)) % 2880)


def write_sparse_fixture(path: Path, contract: FrozenPhysicalContract, *,
                         columns=None, naxis1=None, naxis2=None,
                         metadata=None, extension_metadata=None,
                         preceding_hdu=False):
    columns = list(columns if columns is not None else
                   [(column.ttype, column.tform) for column in contract.columns])
    primary = _header((_card("SIMPLE", True), _card("BITPIX", 8),
                       _card("NAXIS", 0), _card("EXTEND", True)))
    intermediate = b""
    if preceding_hdu:
        intermediate = _header((_card("XTENSION", "IMAGE"), _card("BITPIX", 8),
                                _card("NAXIS", 0), _card("PCOUNT", 0),
                                _card("GCOUNT", 1)))
    row_bytes = contract.naxis1 if naxis1 is None else naxis1
    rows = contract.naxis2 if naxis2 is None else naxis2
    cards = [_card("XTENSION", contract.xtension), _card("BITPIX", contract.bitpix),
             _card("NAXIS", contract.naxis), _card("NAXIS1", row_bytes),
             _card("NAXIS2", rows), _card("PCOUNT", contract.pcount),
             _card("GCOUNT", contract.gcount), _card("TFIELDS", len(columns))]
    for key, value in (extension_metadata or {}).items():
        cards.append(_card(key, value))
    metadata = metadata or {}
    for index, (name, tform) in enumerate(columns, 1):
        cards.extend((_card(f"TTYPE{index}", name), _card(f"TFORM{index}", tform)))
        for prefix, value in metadata.get(index, {}).items():
            cards.append(_card(f"{prefix}{index}", value))
    table_header = _header(cards)
    header_bytes = primary + intermediate + table_header
    padded_data = ((row_bytes * rows + 2879) // 2880) * 2880
    with path.open("xb") as stream:
        stream.write(header_bytes)
        stream.truncate(len(header_bytes) + padded_data)
    return path


def write_adapter_fixture(path: Path):
    columns = []
    for physical in SYNTHETIC_REGIONAL_FITS_V2.fields:
        logical = FIELD_BY_ID[physical.field_id]
        if physical.tform == "8A": value = np.asarray([b"SYN001"], dtype="S8")
        elif physical.tform == "I": value = np.asarray([1], dtype=np.int16)
        elif physical.tform == "J":
            number = 2_000_000_001 if physical.field_id in FORBIDDEN_J_IDS else 100
            value = np.asarray([number], dtype=np.int32)
        elif physical.tform == "6J": value = np.asarray([(0, 1, 0, 0, 0, 0)], dtype=np.int32)
        elif physical.tform == "4I": value = np.asarray([(1, 2, 3, 4)], dtype=np.int16)
        elif physical.tform == "4E": value = np.asarray([(1., 2., 3., 4.)], dtype=np.float32)
        elif physical.tform == "E": value = np.asarray([12345.5], dtype=np.float32)
        elif physical.tform == "D": value = np.asarray([10.0], dtype=np.float64)
        elif physical.tform == "L": value = np.asarray([True], dtype=bool)
        else: raise AssertionError(physical.tform)
        columns.append(fits.Column(name=logical.provider_name, format=physical.tform,
                                   array=value))
    fits.HDUList([fits.PrimaryHDU(), fits.BinTableHDU.from_columns(columns)]).writeto(
        path, checksum=False)
    return path


class Amendment004AuthorityLogicalTests(unittest.TestCase):
    def test_001_authority_bindings(self):
        expected = {
            "OC3_DR9_PROVIDER_SCHEMA_ADAPTER_AMENDMENT_003.md": AMENDMENT_003_SHA256,
            "OC3_DR9_PROVIDER_SCHEMA_CORRECTION_AMENDMENT_004.md": AMENDMENT_004_SHA256,
            "OC3_DR9_PROVIDER_PHYSICAL_CONTRACTS.md": PHYSICAL_CONTRACT_DOCUMENT_SHA256,
            "OC3_POST_PROBE_001_REGRESSION_STATE_CLARIFICATION_001.md": POST_PROBE_001_CLARIFICATION_SHA256,
        }
        self.assertEqual({name: file_hash(PROJECT / name) for name in expected}, expected)

    def test_002_post_probe_state_binding(self):
        self.assertEqual((REGRESSION_STATE, REGRESSION_INVARIANT),
                         ("POST_PROBE_001", "ONE_AUDITED_REAL_PROBE_ATTEMPT_EXPECTED"))

    def test_003_logical_contract_version_and_history(self):
        self.assertEqual(LOGICAL_CONTRACT_VERSION, "OC3_DR9_PROVIDER_LOGICAL_V2_AMENDMENT_004")
        self.assertNotEqual(LOGICAL_CONTRACT_SHA256, HISTORICAL_LOGICAL_CONTRACT_SHA256)
        self.assertEqual(HISTORICAL_LOGICAL_CONTRACT_SHA256,
                         hash_object(historical_logical_contract_object()))

    def test_004_exact_fifteen_corrected_types(self):
        self.assertEqual(len(AMENDMENT_004_CORRECTED_TYPES), 15)
        self.assertEqual({key: FIELD_BY_ID[key].logical_type
                          for key in AMENDMENT_004_CORRECTED_TYPES},
                         dict(AMENDMENT_004_CORRECTED_TYPES))

    def test_005_classifications_unchanged(self):
        self.assertIs(FIELD_BY_ID[FieldId.REG_BRICKID].classification,
                      FieldClass.TECHNICAL_ALLOWED)
        self.assertTrue(all(FIELD_BY_ID[key].classification is FieldClass.KNOWN_BUT_FORBIDDEN
                            for key in FORBIDDEN_J_IDS))
        self.assertTrue(all(FIELD_BY_ID[key].classification is FieldClass.TECHNICAL_ALLOWED
                            for key in GEOMETRY_D_IDS))

    def test_006_corrected_synthetic_tforms_and_unchanged_types(self):
        forms = {field.field_id: field.tform for field in SYNTHETIC_REGIONAL_FITS_V2.fields}
        self.assertEqual(forms[FieldId.REG_BRICKID], "J")
        self.assertTrue(all(forms[key] == "J" for key in FORBIDDEN_J_IDS))
        self.assertTrue(all(forms[key] == "D" for key in GEOMETRY_D_IDS))
        self.assertEqual((forms[FieldId.REG_NEXP_G], forms[FieldId.REG_NEXPHIST_G],
                          forms[FieldId.REG_PSFSIZE_G], forms[FieldId.REG_WISE_NOBS],
                          forms[FieldId.REG_SURVEY_PRIMARY]), ("I", "6J", "E", "4I", "L"))


class FrozenPhysicalContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="oc3_A004_PHYSICAL_SYNTHETIC_")
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def fixture(self, contract, **kwargs):
        return write_sparse_fixture(self.root / f"{contract.role.value}-{len(list(self.root.iterdir()))}.fits",
                                    contract, **kwargs)

    def assert_conflict(self, contract, **kwargs):
        path = self.fixture(contract, **kwargs)
        with self.assertRaisesRegex(InputError, PHYSICAL_SCHEMA_CONFLICT):
            validate_fits_structure(path, contract)

    def test_010_exact_contract_roles_and_hashes(self):
        self.assertEqual(set(PRODUCTION_PHYSICAL_CONTRACTS), set(PhysicalRole))
        self.assertEqual(dict(PHYSICAL_CONTRACT_HASHES), EXPECTED_CONTRACT_HASHES)
        self.assertEqual({role: contract.sha256 for role, contract in
                          PRODUCTION_PHYSICAL_CONTRACTS.items()}, EXPECTED_CONTRACT_HASHES)

    def test_011_root_contract_exact(self):
        contract = ROOT_SUMMARY
        self.assertEqual((contract.target_hdu_index, contract.xtension, contract.bitpix,
                          contract.naxis, contract.naxis1, contract.naxis2,
                          contract.pcount, contract.gcount, contract.tfields),
                         (1, "BINTABLE", 8, 2, 70, 662174, 0, 1, 11))
        self.assertEqual([(x.ttype, x.tform) for x in contract.columns],
                         [("BRICKNAME", "8A"), ("BRICKID", "J"), ("BRICKQ", "I"),
                          ("BRICKROW", "J"), ("BRICKCOL", "J"), ("RA", "D"),
                          ("DEC", "D"), ("RA1", "D"), ("RA2", "D"),
                          ("DEC1", "D"), ("DEC2", "D")])

    def test_012_regional_contracts_exact(self):
        for contract, rows in ((NORTH_SUMMARY, 93548), (SOUTH_SUMMARY, 253658)):
            self.assertEqual((contract.naxis1, contract.naxis2, contract.tfields),
                             (300, rows, 51))
            self.assertEqual(contract.columns, REGIONAL_COLUMNS)
        self.assertEqual(REGIONAL_COLUMNS[43].tform, "J")
        self.assertTrue(all(REGIONAL_COLUMNS[index].tform == "J" for index in range(9, 18)))
        self.assertTrue(all(REGIONAL_COLUMNS[index].tform == "D" for index in range(44, 49)))

    def test_013_patch_contract_exact_and_membership_disabled(self):
        self.assertEqual((SOUTH_PATCH_LIST.naxis1, SOUTH_PATCH_LIST.naxis2,
                          SOUTH_PATCH_LIST.tfields), (14, 1691, 3))
        self.assertEqual([(x.ttype, x.tform) for x in SOUTH_PATCH_LIST.columns],
                         [("RELEASE", "I"), ("BRICKID", "J"), ("BRICKNAME", "8A")])
        self.assertEqual(PATCH_MEMBERSHIP_FIELD_STATUS, "STRUCTURAL_MEMBERSHIP_KEY_CANDIDATE")
        self.assertNotEqual(PATCH_MEMBERSHIP_FIELD_STATUS, "MEMBERSHIP_KEY_ENABLED")
        with self.assertRaisesRegex(InputError, PATCH_LIST_STATUS):
            PatchListSchemaAdapter().decode_production(self.root / "not-opened.fits")

    def test_014_all_four_exact_synthetic_structures_validate(self):
        for contract in PRODUCTION_PHYSICAL_CONTRACTS.values():
            self.assertEqual(validate_fits_structure(self.fixture(contract), contract),
                             EXPECTED_CONTRACT_HASHES[contract.role])

    def test_015_wrong_hdu_fails(self):
        self.assert_conflict(ROOT_SUMMARY, preceding_hdu=True)

    def test_016_extra_missing_reordered_case_and_tform_fail(self):
        base = [(c.ttype, c.tform) for c in NORTH_SUMMARY.columns]
        variants = [
            base + [("EXTRA", "J")], base[:-1],
            [base[1], base[0], *base[2:]],
            [(base[0][0].upper(), base[0][1]), *base[1:]],
            [(base[0][0], "9A"), *base[1:]],
        ]
        for columns in variants:
            with self.subTest(columns=len(columns), first=columns[0]):
                self.assert_conflict(NORTH_SUMMARY, columns=columns)

    def test_017_unexpected_column_metadata_fail(self):
        for prefix, value in (("TUNIT", "deg"), ("TNULL", -1),
                              ("TSCAL", 2), ("TZERO", 1)):
            with self.subTest(prefix=prefix):
                self.assert_conflict(ROOT_SUMMARY, metadata={1: {prefix: value}})

    def test_018_unexpected_extension_metadata_fail(self):
        for key, value in (("EXTNAME", "BRICKS"), ("CHECKSUM", "0000000000000000"),
                           ("DATASUM", "0")):
            with self.subTest(key=key):
                self.assert_conflict(ROOT_SUMMARY, extension_metadata={key: value})

    def test_019_naxis1_and_naxis2_drift_fail(self):
        self.assert_conflict(ROOT_SUMMARY, naxis1=71)
        self.assert_conflict(ROOT_SUMMARY, naxis2=662173)
        self.assert_conflict(NORTH_SUMMARY, naxis2=93549)
        self.assert_conflict(SOUTH_SUMMARY, naxis2=253657)

    def test_020_checksum_identities_and_patch_unresolved(self):
        self.assertEqual(ROOT_SUMMARY.expected_provider_full_file_sha256,
                         "dc943d702357f93553b9e5d15e87ace38df94eb7095f4100657407b3f9919c5f")
        self.assertEqual(NORTH_SUMMARY.expected_provider_full_file_sha256,
                         "2edd5c295fdad26852c6f224a3ff023cff43dd0e03a53acd35b767e726ee72fb")
        self.assertEqual(SOUTH_SUMMARY.expected_provider_full_file_sha256,
                         "7360414f5d53571ca70fa0cb483eb8c80cfcbe80df0856a117246f442a0b9a3f")
        self.assertIsNone(SOUTH_PATCH_LIST.expected_provider_full_file_sha256)
        self.assertEqual(SOUTH_PATCH_LIST.checksum_status, PATCH_CHECKSUM_STATUS)

    def test_021_synthetic_digest_comparison_cannot_activate(self):
        before = ACTIVATION_STATES[PhysicalRole.ROOT_SUMMARY]
        self.assertTrue(compare_complete_file_sha256(
            PhysicalRole.ROOT_SUMMARY, ROOT_SUMMARY.expected_provider_full_file_sha256))
        self.assertEqual(ACTIVATION_STATES[PhysicalRole.ROOT_SUMMARY], before)
        self.assertFalse(before.full_file_integrity_bound)
        with self.assertRaisesRegex(IntegrityError, "FULL_FILE_SHA256_MISMATCH"):
            compare_complete_file_sha256(PhysicalRole.ROOT_SUMMARY, "0" * 64)
        with self.assertRaisesRegex(InputError, PATCH_INTEGRITY_UNRESOLVED):
            compare_complete_file_sha256(PhysicalRole.SOUTH_PATCH_LIST, "0" * 64)

    def test_022_activation_matrix_exact_and_independent(self):
        expected = {
            PhysicalRole.ROOT_SUMMARY: ActivationState(True, True, False, False, False),
            PhysicalRole.NORTH_SUMMARY: ActivationState(True, True, False, False, False),
            PhysicalRole.SOUTH_SUMMARY: ActivationState(True, True, False, False, False),
            PhysicalRole.SOUTH_PATCH_LIST: ActivationState(True, False, False, False, False),
        }
        self.assertEqual(dict(ACTIVATION_STATES), expected)
        self.assertTrue(all(not state.production_decode_enabled for state in ACTIVATION_STATES.values()))
        self.assertTrue(all(state.physical_schema_frozen for state in ACTIVATION_STATES.values()))

    def test_023_production_decode_and_row_semantics_blocked(self):
        for role in PhysicalRole:
            with self.subTest(role=role), self.assertRaisesRegex(InputError, PRODUCTION_DECODE_BLOCKER):
                require_production_decode(role)
            with self.subTest(role=role), self.assertRaisesRegex(InputError, ROW_SEMANTICS_BLOCKER):
                require_row_semantics(role)
        identity = ProviderIdentity(ProviderRole.REGIONAL_NORTH, "PRODUCTION", "DR9",
                                    "north", "BASS_MzLS", "9011", ("SYNTHETIC_TEST",))
        with self.assertRaisesRegex(InputError, PRODUCTION_DECODE_BLOCKER):
            ProviderSchemaAdapter().decode(self.root / "must-not-open.fits", identity, "0" * 64)

    def test_024_brickname_production_semantics_unresolved(self):
        self.assertFalse(hasattr(ROOT_COLUMNS[0], "string_policy"))
        self.assertFalse(ACTIVATION_STATES[PhysicalRole.SOUTH_PATCH_LIST].row_semantics_validated)
        with self.assertRaisesRegex(InputError, ROW_SEMANTICS_BLOCKER):
            require_row_semantics(PhysicalRole.SOUTH_PATCH_LIST)

    def test_025_forbidden_j_canaries_never_cross_adapter(self):
        path = write_adapter_fixture(self.root / "regional-canaries.fits")
        identity = ProviderIdentity(ProviderRole.REGIONAL_NORTH, "SYNTHETIC", "DR9",
                                    "north", "BASS_MzLS", "9011", ("SYNTHETIC",))
        probe = CellAccessProbe()
        table = ProviderSchemaAdapter().decode(path, identity, file_hash(path),
                                               SYNTHETIC_REGIONAL_FITS_V2, probe)
        self.assertEqual(probe.forbidden_accesses, [])
        self.assertFalse(any(key in table.rows[0] for key in FORBIDDEN_J_IDS))
        self.assertNotIn(b"2000000001", canonical([dict(table.rows[0])]))

    def test_026_manifest_binding_accepts_contract_identity_but_not_decode(self):
        contract = production_physical_contract(ProviderRole.REGIONAL_NORTH)
        binding = provider_manifest_binding(contract.contract_id)
        self.assertEqual(validate_provider_manifest_binding(binding, production=True), binding)
        self.assertFalse(ACTIVATION_STATES[PhysicalRole.NORTH_SUMMARY].production_decode_enabled)


if __name__ == "__main__":
    unittest.main()
