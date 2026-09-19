"""Synthetic/offline tests for frozen OC-3 metadata value semantics."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import inspect
import socket
from pathlib import Path
import unittest

from oc3lib.core import InputError, IntegrityError, file_hash
import oc3lib.metadata_value_semantics as semantics
from oc3lib.metadata_value_semantics import *
from oc3lib.provider_physical_contracts import (
    ACTIVATION_STATES, PATCH_CHECKSUM_STATUS, PHYSICAL_CONTRACT_HASHES,
    PhysicalRole,
)
from oc3lib.provider_schema import (
    FIELD_BY_ID, GRZ_PREDICATE_VERSION, LOGICAL_CONTRACT_SHA256,
    LOGICAL_CONTRACT_VERSION, FieldClass, FieldId,
)


PROJECT = Path(__file__).resolve().parents[2]
PHYSICAL_HASHES = {
    PhysicalRole.ROOT_SUMMARY: "6e50b8b0c258f10752bf2d7d7d2d88c64ec16899fbb02711fd0621e4d642ea53",
    PhysicalRole.NORTH_SUMMARY: "59fb8668165d14f201df1f269009ca0b47b41fa431b0bb0d55212c19c77f2677",
    PhysicalRole.SOUTH_SUMMARY: "2faad729eac8e1912f63e4da8373acdc7cd5e9101601ea51e8ec9fb145dc25fa",
    PhysicalRole.SOUTH_PATCH_LIST: "5be4df46180c0ec4964b53e3ad095bf75bf80a4c142dc7a8d22ba60efafbbd14",
}
EXPECTED_DIGESTS = {
    PhysicalRole.ROOT_SUMMARY: "dc943d702357f93553b9e5d15e87ace38df94eb7095f4100657407b3f9919c5f",
    PhysicalRole.NORTH_SUMMARY: "2edd5c295fdad26852c6f224a3ff023cff43dd0e03a53acd35b767e726ee72fb",
    PhysicalRole.SOUTH_SUMMARY: "7360414f5d53571ca70fa0cb483eb8c80cfcbe80df0856a117246f442a0b9a3f",
}


def synthetic_name(index: int, marker: str = "p") -> bytes:
    return f"{index:04d}{marker}{(index * 7) % 1000:03d}".encode("ascii")


def synthetic_patch_inputs() -> list[PatchRowInput]:
    return [PatchRowInput(9012, index - 845, synthetic_name(index))
            for index in range(PATCH_CARDINALITY)]


def complete_patch() -> ValidatedPatchList:
    return validate_complete_patch_rows(synthetic_patch_inputs())


def exact_join_inputs(rows=None) -> list[JoinRowInput]:
    values = synthetic_patch_inputs() if rows is None else rows
    return [JoinRowInput(row.brickname, row.brickid) for row in values]


def synthetic_acquisition(**changes) -> AcquisitionBoundLocalSha256:
    values = dict(
        role=PhysicalRole.SOUTH_PATCH_LIST,
        resource_url=PATCH_RESOURCE_URL,
        physical_contract_sha256=PHYSICAL_HASHES[PhysicalRole.SOUTH_PATCH_LIST],
        authorization_sha256="a" * 64,
        implementation_aggregate="b" * 64,
        environment_fingerprint="c" * 64,
        representation_identity=EXPECTED_PATCH_REPRESENTATION,
        acquired_byte_count=PATCH_CONTENT_LENGTH,
        local_sha256="d" * 64,
        synthetic_only=True,
    )
    values.update(changes)
    return AcquisitionBoundLocalSha256(**values)


class BricknameSemanticsTests(unittest.TestCase):
    def invalid(self, raw):
        with self.assertRaisesRegex(InputError, BRICKNAME_INVALID):
            validate_brickname(raw)

    def test_001_valid_p_form(self):
        value = validate_brickname(b"1126p222")
        self.assertEqual((value.raw, value.value), (b"1126p222", "1126p222"))

    def test_002_valid_m_form(self):
        self.assertEqual(validate_brickname(b"0000m999").value, "0000m999")

    def test_003_uppercase_p_rejected(self): self.invalid(b"1126P222")
    def test_004_uppercase_m_rejected(self): self.invalid(b"1126M222")
    def test_005_leading_space_rejected(self): self.invalid(b" 126p222")
    def test_006_trailing_space_rejected(self): self.invalid(b"1126p22 ")
    def test_007_internal_space_rejected(self): self.invalid(b"1126p2 2")
    def test_008_leading_nul_rejected(self): self.invalid(b"\x00126p222")
    def test_009_internal_nul_rejected(self): self.invalid(b"1126\x00222")
    def test_010_trailing_nul_rejected(self): self.invalid(b"1126p22\x00")
    def test_011_non_ascii_rejected(self): self.invalid(b"1126p22\xff")
    def test_012_seven_bytes_rejected(self): self.invalid(b"126p222")
    def test_013_nine_bytes_rejected(self): self.invalid(b"01126p222")

    def test_014_no_trimming_demonstrated(self):
        self.invalid(b"1126p22 ")
        source = inspect.getsource(semantics._validate_brickname_bytes)
        self.assertNotIn("strip(", source)

    def test_015_no_case_folding_demonstrated(self):
        self.invalid(b"1126P222")
        source = inspect.getsource(semantics._validate_brickname_bytes)
        for token in ("lower(", "upper(", "casefold("):
            self.assertNotIn(token, source)

    def test_016_canonical_strict_ascii_decode(self):
        source = inspect.getsource(semantics._validate_brickname_bytes)
        self.assertIn('decode("ascii", errors="strict")', source)
        self.assertEqual(validate_brickname(b"9999m000").semantics_version,
                         "OC3_BRICKNAME_SEMANTICS_V1")

    def test_017_exact_byte_equality_accepted(self):
        self.assertTrue(exact_brickname_equal(validate_brickname(b"1126p222"),
                                              validate_brickname(b"1126p222")))

    def test_018_unequal_byte_identity_rejected(self):
        self.assertFalse(exact_brickname_equal(validate_brickname(b"1126p222"),
                                               validate_brickname(b"1126p223")))

    def test_019_unvalidated_comparison_rejected(self):
        with self.assertRaisesRegex(InputError, BRICKNAME_VALIDATION_REQUIRED):
            exact_brickname_equal(b"1126p222", validate_brickname(b"1126p222"))


class PatchSemanticsTests(unittest.TestCase):
    def test_020_release_9012_accepted(self):
        self.assertEqual(validate_patch_row(PatchRowInput(9012, 1, b"1126p222")).release, 9012)

    def test_021_release_9010_rejected(self):
        with self.assertRaisesRegex(InputError, PATCH_ROW_INVALID):
            validate_patch_row(PatchRowInput(9010, 1, b"1126p222"))

    def test_022_other_release_rejected(self):
        for value in (9011, 9013, "9012", True):
            with self.subTest(value=value), self.assertRaisesRegex(InputError, PATCH_ROW_INVALID):
                validate_patch_row(PatchRowInput(value, 1, b"1126p222"))

    def test_023_int32_minimum_accepted(self):
        self.assertEqual(validate_patch_row(PatchRowInput(9012, SIGNED_INT32_MIN,
                                                         b"1126p222")).brickid,
                         SIGNED_INT32_MIN)

    def test_024_int32_maximum_accepted(self):
        self.assertEqual(validate_patch_row(PatchRowInput(9012, SIGNED_INT32_MAX,
                                                         b"1126p222")).brickid,
                         SIGNED_INT32_MAX)

    def test_025_below_int32_rejected(self):
        with self.assertRaisesRegex(InputError, PATCH_ROW_INVALID):
            validate_patch_row(PatchRowInput(9012, SIGNED_INT32_MIN - 1, b"1126p222"))

    def test_026_above_int32_rejected(self):
        with self.assertRaisesRegex(InputError, PATCH_ROW_INVALID):
            validate_patch_row(PatchRowInput(9012, SIGNED_INT32_MAX + 1, b"1126p222"))

    def test_027_one_malformed_row_invalidates_all(self):
        rows = synthetic_patch_inputs()
        rows[1000] = PatchRowInput(9012, rows[1000].brickid, b"BAD")
        with self.assertRaisesRegex(InputError, BRICKNAME_INVALID):
            validate_complete_patch_rows(rows)

    def test_028_exactly_1691_accepted(self):
        result = complete_patch()
        self.assertEqual((len(result.rows), len(result.bricknames), len(result.brickids)),
                         (1691, 1691, 1691))

    def test_029_1690_rejected(self):
        with self.assertRaisesRegex(InputError, PATCH_CARDINALITY_INVALID):
            validate_complete_patch_rows(synthetic_patch_inputs()[:-1])

    def test_030_1692_rejected(self):
        rows = synthetic_patch_inputs() + [PatchRowInput(9012, 9999, b"9999m999")]
        with self.assertRaisesRegex(InputError, PATCH_CARDINALITY_INVALID):
            validate_complete_patch_rows(rows)

    def test_031_duplicate_brickname_rejected(self):
        rows = synthetic_patch_inputs()
        rows[-1] = replace(rows[-1], brickname=rows[0].brickname)
        with self.assertRaisesRegex(IntegrityError, PATCH_BRICKNAME_DUPLICATE):
            validate_complete_patch_rows(rows)

    def test_032_duplicate_brickid_rejected(self):
        rows = synthetic_patch_inputs()
        rows[-1] = replace(rows[-1], brickid=rows[0].brickid)
        with self.assertRaisesRegex(IntegrityError, PATCH_BRICKID_DUPLICATE):
            validate_complete_patch_rows(rows)

    def test_033_duplicate_pair_rejected(self):
        rows = synthetic_patch_inputs()
        rows[-1] = replace(rows[-1], brickid=rows[0].brickid, brickname=rows[0].brickname)
        with self.assertRaises((IntegrityError, InputError)):
            validate_complete_patch_rows(rows)


class ExactJoinTests(unittest.TestCase):
    def setUp(self):
        self.inputs = synthetic_patch_inputs()
        self.patch = validate_complete_patch_rows(self.inputs)
        self.root = exact_join_inputs(self.inputs)
        self.south = exact_join_inputs(reversed(self.inputs))

    def fail(self, root=None, south=None):
        with self.assertRaisesRegex(IntegrityError, PATCH_JOIN_INVALID):
            validate_patch_joins(self.patch, self.root if root is None else root,
                                 self.south if south is None else south)

    def test_034_root_exact_single_match_accepted(self):
        result = validate_patch_joins(self.patch, self.root, self.south)
        self.assertEqual(result.joined_rows, 1691)

    def test_035_root_zero_match_rejected(self): self.fail(root=self.root[1:])
    def test_036_root_duplicate_match_rejected(self): self.fail(root=self.root + [self.root[0]])

    def test_037_patch_root_brickid_mismatch_rejected(self):
        root = list(self.root); root[0] = replace(root[0], brickid=999999)
        self.fail(root=root)

    def test_038_south_exact_single_match_accepted(self):
        result = validate_patch_joins(self.patch, list(reversed(self.root)), self.south)
        self.assertTrue(result.exact_brickname_matches and result.brickids_equal)

    def test_039_south_zero_match_rejected(self): self.fail(south=self.south[1:])
    def test_040_south_duplicate_match_rejected(self): self.fail(south=self.south + [self.south[0]])

    def test_041_south_brickid_mismatch_rejected(self):
        south = list(self.south); south[0] = replace(south[0], brickid=999999)
        self.fail(south=south)

    def test_042_no_brickid_only_join_fallback(self):
        root = list(self.root)
        root[0] = JoinRowInput(b"9999m999", root[0].brickid)
        self.fail(root=root)


class IntegrityTests(unittest.TestCase):
    def validate(self, role):
        local = LocallyComputedFullFileSha256(EXPECTED_DIGESTS[role])
        return validate_provider_full_file_integrity(role, local)

    def test_043_expected_root_digest_equality_accepted(self):
        result = self.validate(PhysicalRole.ROOT_SUMMARY)
        self.assertTrue(result.complete_file_equal)

    def test_044_root_digest_mismatch_rejected(self):
        with self.assertRaisesRegex(IntegrityError, FULL_FILE_SHA256_MISMATCH):
            validate_provider_full_file_integrity(
                PhysicalRole.ROOT_SUMMARY, LocallyComputedFullFileSha256("0" * 64))

    def test_045_north_digest_equality_accepted(self):
        self.assertTrue(self.validate(PhysicalRole.NORTH_SUMMARY).complete_file_equal)

    def test_046_south_digest_equality_accepted(self):
        self.assertTrue(self.validate(PhysicalRole.SOUTH_SUMMARY).complete_file_equal)

    def test_047_malformed_sha_string_rejected(self):
        for value in ("x" * 64, "a" * 63, "A" * 64, None):
            with self.subTest(value=value), self.assertRaises(InputError):
                LocallyComputedFullFileSha256(value)

    def test_048_partial_digest_cannot_bind_integrity(self):
        partial = PartialFileSha256(EXPECTED_DIGESTS[PhysicalRole.ROOT_SUMMARY])
        with self.assertRaisesRegex(InputError, COMPLETE_FILE_DIGEST_REQUIRED):
            validate_provider_full_file_integrity(PhysicalRole.ROOT_SUMMARY, partial)

    def test_049_checksum_equality_does_not_mutate_production_state(self):
        before = ACTIVATION_STATES[PhysicalRole.ROOT_SUMMARY]
        result = self.validate(PhysicalRole.ROOT_SUMMARY)
        self.assertFalse(result.production_state_mutated)
        self.assertIs(ACTIVATION_STATES[PhysicalRole.ROOT_SUMMARY], before)
        self.assertFalse(before.full_file_integrity_bound)

    def test_050_patch_provider_checksum_remains_absent(self):
        self.assertIsNone(PATCH_PROVIDER_PUBLISHED_SHA256.value)
        self.assertEqual(PATCH_PROVIDER_PUBLISHED_SHA256.status,
                         "PATCH_LIST_PROVIDER_CHECKSUM_NOT_FOUND")

    def test_051_local_patch_digest_remains_distinct_type(self):
        local = synthetic_acquisition()
        self.assertIsInstance(local, AcquisitionBoundLocalSha256)
        self.assertNotIsInstance(local, ProviderPublishedSha256)


class PatchRepresentationAndGateTests(unittest.TestCase):
    def drift(self, **changes):
        with self.assertRaisesRegex(IntegrityError, PATCH_LIST_REPRESENTATION_DRIFT_STOP):
            validate_patch_representation(replace(EXPECTED_PATCH_REPRESENTATION, **changes))

    def test_052_etag_drift_rejected(self): self.drift(etag='"changed"')
    def test_053_last_modified_drift_rejected(self): self.drift(last_modified="Wed, 13 Jan 2021 18:53:59 GMT")
    def test_054_content_length_drift_rejected(self): self.drift(content_length=31681)
    def test_055_final_url_drift_rejected(self): self.drift(final_url=PATCH_RESOURCE_URL + "?mirror=1")
    def test_056_redirect_rejected(self): self.drift(redirected=True)

    def test_057_exact_probe_identity_accepted_synthetically(self):
        self.assertIs(validate_patch_representation(EXPECTED_PATCH_REPRESENTATION),
                      EXPECTED_PATCH_REPRESENTATION)

    def test_058_synthetic_acquisition_bound_digest_object(self):
        value = synthetic_acquisition()
        self.assertEqual((value.role, value.acquired_byte_count, value.local_sha256,
                          value.synthetic_only),
                         (PhysicalRole.SOUTH_PATCH_LIST, 31680, "d" * 64, True))

    def test_059_synthetic_digest_cannot_become_provider_digest(self):
        local = synthetic_acquisition()
        with self.assertRaises(InputError):
            ProviderPublishedSha256(local.role, local.local_sha256, PATCH_CHECKSUM_STATUS)

    def test_060_no_automatic_full_file_integrity_promotion(self):
        before = PATCH_INTEGRITY_STATE
        synthetic_acquisition()
        self.assertIs(PATCH_INTEGRITY_STATE, before)
        self.assertEqual(before, PatchIntegrityState(False, False, False))

    def test_061_production_decode_false_all_four_roles(self):
        self.assertFalse(PRODUCTION_VALUE_DECODE_ENABLED)
        self.assertEqual(set(ACTIVATION_STATES), set(PhysicalRole))
        self.assertTrue(all(not state.production_decode_enabled
                            for state in ACTIVATION_STATES.values()))

    def test_062_semantics_does_not_enable_selector(self):
        exported_callables = {name for name, value in vars(semantics).items()
                              if callable(value) and name.startswith("select")}
        self.assertEqual(exported_callables, set())

    def test_063_ordering_requires_integrity_before_semantics(self):
        order = FUTURE_VALIDATION_ORDER
        self.assertLess(order.index("full_file_integrity"),
                        order.index("physical_contract_validation"))
        self.assertLess(order.index("physical_contract_validation"), order.index("value_decode"))
        self.assertLess(order.index("value_decode"), order.index("semantic_validation"))
        self.assertLess(order.index("semantic_validation"), order.index("selection"))

    def test_064_redistribution_remains_false(self): self.assertIs(REDISTRIBUTION_ALLOWED, False)


class FrozenRegressionTests(unittest.TestCase):
    def test_065_grz_median_present_v1_unchanged(self):
        self.assertEqual(GRZ_PREDICATE_VERSION, "GRZ_MEDIAN_PRESENT_V1")

    def test_066_physical_contracts_unchanged(self):
        self.assertEqual(dict(PHYSICAL_CONTRACT_HASHES), PHYSICAL_HASHES)

    def test_067_logical_v2_unchanged(self):
        self.assertEqual(LOGICAL_CONTRACT_VERSION, "OC3_DR9_PROVIDER_LOGICAL_V2_AMENDMENT_004")
        self.assertEqual(LOGICAL_CONTRACT_SHA256,
                         "f396ba8dfb933043cf75a3a15a60f6019e77adeeaf2dd8c721d132bc41090a40")

    def test_068_forbidden_field_firewall_unchanged(self):
        ids = (FieldId.REG_NOBJS, FieldId.REG_NPSF, FieldId.REG_NSIM,
               FieldId.REG_NREX, FieldId.REG_NEXP, FieldId.REG_NDEV,
               FieldId.REG_NCOMP, FieldId.REG_NSER, FieldId.REG_NDUP)
        self.assertTrue(all(FIELD_BY_ID[key].classification is FieldClass.KNOWN_BUT_FORBIDDEN
                            for key in ids))

    def test_069_post_probe_001_immutable_evidence_13_of_13(self):
        attempt = PROJECT / "oc3/provider_contract_probe/OC3-PHYSICAL-CONTRACT-PROBE-001"
        expected = {
            "PROBE_CHECKSUM_EVIDENCE.json": (1109, "f464983d87ef4ab2776b699a54490874667c7f4a7ca138269180d8467defee3f"),
            "PROBE_EVENTS.json": (145, "d130134b7bb46a612c8213aba80b0d5d613303d04d1870063b5d0a5677e75fd0"),
            "PROBE_LEDGER.sqlite": (40960, "8bd834e3a1fa28d820d7ac81f8fe049749761f518b569cc2d915beb32191b441"),
            "PROBE_PHYSICAL_CONTRACT_CANDIDATES.json": (15421, "eaa8287fab7c4de44dc265239dcf3b9e9e56f5c2adce4334711634cb9e9b7eb1"),
            "PROBE_TERMINAL.json": (257, "27b944d654045c314505e548242eee85416cf9391ffc337d5f4a834fbb3c84e3"),
            "PROBE_TRANSPORT_EVIDENCE.json": (2462, "cd0248193669bb2d303ca55fb24e3ab46f9b0ac2aefc59086c3df2dd49f4975a"),
            "compressed_prefix/NORTH_SUMMARY/0.part": (65536, "7b0cb006d16f193cdcef2120169d039300aa56d9aca863decc3d654c20be4cd6"),
            "compressed_prefix/ROOT_SUMMARY/0.part": (65536, "28c7b004fbbcf9cd02999c6345b6b5f428c901bf8b76fc10d6612aa29d5ded5e"),
            "compressed_prefix/SOUTH_SUMMARY/0.part": (65536, "383aa7a812405560e418efff4109268979c3ad45118e9d00ffbb0ad3c666748b"),
            "transport/NORTH_SUMMARY.head.json": (508, "833b31cdccb786069e07c2bbf0e286ca8a84c410399ab3b9ad1fa28e321e0a9c"),
            "transport/ROOT_SUMMARY.head.json": (490, "bf79a2189fd3ae09863059f4c5bcd5ae6531a4d242d75cd813603f3b8ddc972a"),
            "transport/SOUTH_PATCH_LIST.head.json": (410, "9d8ce43f7bc76529045a80c495d47787c1d7d539cbbd142d2d0889919edc6c3c"),
            "transport/SOUTH_SUMMARY.head.json": (508, "71636341463e738a601cf8aa8c24131e900762bb802ac5d17b12751bf24cb166"),
        }
        observed = {str(path.relative_to(attempt)): path
                    for path in attempt.rglob("*") if path.is_file()}
        self.assertEqual(set(observed), set(expected))
        for relative, (size, sha256) in expected.items():
            self.assertEqual(observed[relative].stat().st_size, size)
            self.assertEqual(file_hash(observed[relative]), sha256)

    def test_070_real_network_requests_are_firewalled(self):
        with self.assertRaisesRegex(AssertionError, "REAL_NETWORK_FORBIDDEN"):
            socket.getaddrinfo("example.invalid", 443)


class AdditionalClosedWorldTests(unittest.TestCase):
    def test_071_brickname_requires_bytes_not_string(self):
        with self.assertRaisesRegex(InputError, BRICKNAME_INVALID):
            validate_brickname("1126p222")

    def test_072_bool_is_not_int32(self):
        with self.assertRaisesRegex(InputError, PATCH_ROW_INVALID):
            validate_patch_row(PatchRowInput(9012, True, b"1126p222"))

    def test_073_join_is_independent_of_row_order(self):
        patch = complete_patch()
        rows = exact_join_inputs()
        result = validate_patch_joins(patch, reversed(rows), rows[700:] + rows[:700])
        self.assertEqual(result.joined_rows, 1691)

    def test_074_patch_role_has_no_provider_digest_validator(self):
        with self.assertRaisesRegex(InputError, PATCH_LIST_PROVIDER_CHECKSUM_NOT_FOUND):
            validate_provider_full_file_integrity(
                PhysicalRole.SOUTH_PATCH_LIST, LocallyComputedFullFileSha256("a" * 64))

    def test_075_acquisition_binding_requires_exact_physical_contract(self):
        with self.assertRaisesRegex(InputError, "PATCH_ACQUISITION_BINDING_INVALID"):
            synthetic_acquisition(physical_contract_sha256="0" * 64)

    def test_076_acquisition_binding_requires_complete_byte_count(self):
        with self.assertRaisesRegex(InputError, "PATCH_ACQUISITION_BINDING_INVALID"):
            synthetic_acquisition(acquired_byte_count=PATCH_CONTENT_LENGTH - 1)

    def test_077_patch_state_is_frozen(self):
        with self.assertRaises((AttributeError, TypeError)):
            PATCH_INTEGRITY_STATE.full_file_integrity_bound = True

    def test_078_production_activation_snapshot_is_immutable(self):
        snapshot = production_activation_snapshot()
        with self.assertRaises(TypeError):
            snapshot[PhysicalRole.ROOT_SUMMARY] = snapshot[PhysicalRole.ROOT_SUMMARY]

    def test_079_authorities_unchanged(self):
        expected = {
            "OC3_METADATA_VALUE_SEMANTICS_AND_INTEGRITY_SPEC.md": VALUE_SEMANTICS_SPEC_SHA256,
            "OC3_DR9_PROVIDER_SCHEMA_CORRECTION_AMENDMENT_004.md": "842d7b62e3a5408c88d534b3e531a6e2d85a4eb66593f2b0c9bf91bb7fe3fe48",
            "OC3_DR9_PROVIDER_PHYSICAL_CONTRACTS.md": "bdf38d98866de8a7a9ee1c4e495dafea9492e8fc2980edf307b5fb6951040e6b",
            "OC3_POST_PROBE_001_REGRESSION_STATE_CLARIFICATION_001.md": "930909ebdfffff58bc0c88cbbab9c619128cb4ab7adb8df9ec6a88e82324e155",
        }
        self.assertEqual({name: file_hash(PROJECT / name) for name in expected}, expected)

    def test_080_no_provider_file_or_table_dependency(self):
        source = inspect.getsource(semantics)
        for token in ("astropy", "fits.open", "Table.read", "urllib", "requests"):
            self.assertNotIn(token, source)

    def test_081_representation_rejects_numeric_type_coercion(self):
        for changes in ({"content_length": 31680.0}, {"redirected": 0}):
            with self.subTest(changes=changes), self.assertRaisesRegex(
                    IntegrityError, PATCH_LIST_REPRESENTATION_DRIFT_STOP):
                validate_patch_representation(replace(EXPECTED_PATCH_REPRESENTATION, **changes))

    def test_082_acquisition_byte_count_rejects_float(self):
        with self.assertRaisesRegex(InputError, "PATCH_ACQUISITION_BINDING_INVALID"):
            synthetic_acquisition(acquired_byte_count=31680.0)

    def test_083_validated_patch_types_cannot_be_forged(self):
        with self.assertRaisesRegex(InputError, PATCH_ROW_INVALID):
            ValidatedPatchRow(9010, 1, validate_brickname(b"1126p222"))
