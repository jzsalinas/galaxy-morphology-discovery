"""Pure OC-3 metadata value semantics and integrity primitives.

This module accepts only caller-supplied values.  It has no filesystem,
network, FITS-row, bootstrap, DTO, membership-selection, or selector entry
point.  Successful synthetic validation never changes production activation
state.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from types import MappingProxyType
from typing import Iterable

from .core import InputError, IntegrityError
from .provider_physical_contracts import (
    ACTIVATION_STATES,
    PATCH_CHECKSUM_STATUS,
    PHYSICAL_CONTRACT_HASHES,
    PRODUCTION_PHYSICAL_CONTRACTS,
    PhysicalRole,
)


VALUE_SEMANTICS_SPEC_SHA256 = "c72f2ff7d3032b1ed38a22cc7f002781e3e1266c8b9aa45c2af08822164d6348"
BRICKNAME_SEMANTICS_VERSION = "OC3_BRICKNAME_SEMANTICS_V1"
PATCH_RELEASE = 9012
PATCH_CARDINALITY = 1691
SIGNED_INT32_MIN = -(2**31)
SIGNED_INT32_MAX = 2**31 - 1

BRICKNAME_INVALID = "OC3_BRICKNAME_SEMANTICS_INVALID"
BRICKNAME_VALIDATION_REQUIRED = "OC3_BRICKNAME_VALIDATION_REQUIRED"
PATCH_ROW_INVALID = "PATCH_LIST_ROW_SEMANTICS_INVALID"
PATCH_CARDINALITY_INVALID = "PATCH_LIST_CARDINALITY_INVALID"
PATCH_BRICKNAME_DUPLICATE = "PATCH_LIST_BRICKNAME_DUPLICATE"
PATCH_BRICKID_DUPLICATE = "PATCH_LIST_BRICKID_DUPLICATE"
PATCH_PAIR_DUPLICATE = "PATCH_LIST_IDENTITY_PAIR_DUPLICATE"
PATCH_JOIN_INVALID = "PATCH_LIST_EXACT_JOIN_INVALID"
FULL_FILE_SHA256_INVALID = "FULL_FILE_SHA256_INVALID"
FULL_FILE_SHA256_MISMATCH = "FULL_FILE_SHA256_MISMATCH"
COMPLETE_FILE_DIGEST_REQUIRED = "COMPLETE_FILE_DIGEST_REQUIRED"
PATCH_LIST_REPRESENTATION_DRIFT_STOP = "PATCH_LIST_REPRESENTATION_DRIFT_STOP"
PATCH_LIST_PROVIDER_CHECKSUM_NOT_FOUND = PATCH_CHECKSUM_STATUS

PATCH_RESOURCE_URL = "https://www.legacysurvey.org/files/dr9-south-patched-bricks.fits"
PATCH_CONTENT_LENGTH = 31680
PATCH_ETAG = '"5ffdf047-7bc0"'
PATCH_LAST_MODIFIED = "Tue, 12 Jan 2021 18:53:59 GMT"

REDISTRIBUTION_ALLOWED = False
PRODUCTION_VALUE_DECODE_ENABLED = False

FUTURE_VALIDATION_ORDER = (
    "authorization",
    "complete_acquisition",
    "full_file_integrity",
    "physical_contract_validation",
    "value_decode",
    "semantic_validation",
    "joins",
    "membership",
    "dtos",
    "selection",
)


def _valid_sha256(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


@dataclass(frozen=True)
class ValidatedBrickname:
    """An exact canonical identifier validated from eight raw bytes."""

    raw: bytes
    value: str
    semantics_version: str = BRICKNAME_SEMANTICS_VERSION

    def __post_init__(self) -> None:
        if self.semantics_version != BRICKNAME_SEMANTICS_VERSION:
            raise InputError(BRICKNAME_INVALID)
        canonical = _validate_brickname_bytes(self.raw)
        if self.value != canonical:
            raise InputError(BRICKNAME_INVALID)


def _validate_brickname_bytes(raw: object) -> str:
    if type(raw) is not bytes or len(raw) != 8:
        raise InputError(BRICKNAME_INVALID)
    if not all(0x30 <= raw[index] <= 0x39 for index in (0, 1, 2, 3, 5, 6, 7)):
        raise InputError(BRICKNAME_INVALID)
    if raw[4] not in (0x70, 0x6D):
        raise InputError(BRICKNAME_INVALID)
    # Every accepted byte is already restricted to ASCII by the checks above.
    try:
        return raw.decode("ascii", errors="strict")
    except UnicodeDecodeError as exc:  # defensive; the byte predicate is decisive
        raise InputError(BRICKNAME_INVALID) from exc


def validate_brickname(raw: bytes) -> ValidatedBrickname:
    value = _validate_brickname_bytes(raw)
    return ValidatedBrickname(raw=raw, value=value)


def exact_brickname_equal(left: object, right: object) -> bool:
    if not isinstance(left, ValidatedBrickname) or not isinstance(right, ValidatedBrickname):
        raise InputError(BRICKNAME_VALIDATION_REQUIRED)
    return left.raw == right.raw


@dataclass(frozen=True)
class PatchRowInput:
    release: object
    brickid: object
    brickname: object


@dataclass(frozen=True)
class ValidatedPatchRow:
    release: int
    brickid: int
    brickname: ValidatedBrickname

    def __post_init__(self) -> None:
        if (type(self.release) is not int or self.release != PATCH_RELEASE or
                type(self.brickid) is not int or
                not SIGNED_INT32_MIN <= self.brickid <= SIGNED_INT32_MAX or
                not isinstance(self.brickname, ValidatedBrickname)):
            raise InputError(PATCH_ROW_INVALID)


def _signed_int32(value: object) -> int:
    if type(value) is not int or not SIGNED_INT32_MIN <= value <= SIGNED_INT32_MAX:
        raise InputError(PATCH_ROW_INVALID)
    return value


def validate_patch_row(row: PatchRowInput) -> ValidatedPatchRow:
    if not isinstance(row, PatchRowInput) or type(row.release) is not int or row.release != PATCH_RELEASE:
        raise InputError(PATCH_ROW_INVALID)
    return ValidatedPatchRow(
        release=PATCH_RELEASE,
        brickid=_signed_int32(row.brickid),
        brickname=validate_brickname(row.brickname),
    )


@dataclass(frozen=True)
class ValidatedPatchList:
    rows: tuple[ValidatedPatchRow, ...]
    bricknames: frozenset[bytes]
    brickids: frozenset[int]
    identity_pairs: frozenset[tuple[int, bytes]]

    def __post_init__(self) -> None:
        if (type(self.rows) is not tuple or len(self.rows) != PATCH_CARDINALITY or
                not all(isinstance(row, ValidatedPatchRow) for row in self.rows)):
            raise InputError(PATCH_CARDINALITY_INVALID)
        names = tuple(row.brickname.raw for row in self.rows)
        ids = tuple(row.brickid for row in self.rows)
        pairs = tuple((row.brickid, row.brickname.raw) for row in self.rows)
        if (self.bricknames != frozenset(names) or self.brickids != frozenset(ids) or
                self.identity_pairs != frozenset(pairs) or
                len(self.bricknames) != PATCH_CARDINALITY or
                len(self.brickids) != PATCH_CARDINALITY or
                len(self.identity_pairs) != PATCH_CARDINALITY):
            raise IntegrityError("PATCH_LIST_VALIDATED_REPRESENTATION_INVALID")


def validate_complete_patch_rows(rows: Iterable[PatchRowInput]) -> ValidatedPatchList:
    supplied = tuple(rows)
    if len(supplied) != PATCH_CARDINALITY:
        raise InputError(PATCH_CARDINALITY_INVALID)
    validated = tuple(validate_patch_row(row) for row in supplied)
    names = [row.brickname.raw for row in validated]
    ids = [row.brickid for row in validated]
    pairs = [(row.brickid, row.brickname.raw) for row in validated]
    if len(set(names)) != len(names):
        raise IntegrityError(PATCH_BRICKNAME_DUPLICATE)
    if len(set(ids)) != len(ids):
        raise IntegrityError(PATCH_BRICKID_DUPLICATE)
    if len(set(pairs)) != len(pairs):
        raise IntegrityError(PATCH_PAIR_DUPLICATE)
    return ValidatedPatchList(validated, frozenset(names), frozenset(ids), frozenset(pairs))


@dataclass(frozen=True)
class JoinRowInput:
    brickname: object
    brickid: object


@dataclass(frozen=True)
class ValidatedJoinRow:
    brickname: ValidatedBrickname
    brickid: int

    def __post_init__(self) -> None:
        if (not isinstance(self.brickname, ValidatedBrickname) or
                type(self.brickid) is not int or
                not SIGNED_INT32_MIN <= self.brickid <= SIGNED_INT32_MAX):
            raise InputError(PATCH_JOIN_INVALID)


def validate_join_row(row: JoinRowInput) -> ValidatedJoinRow:
    if not isinstance(row, JoinRowInput):
        raise InputError(PATCH_JOIN_INVALID)
    return ValidatedJoinRow(validate_brickname(row.brickname), _signed_int32(row.brickid))


@dataclass(frozen=True)
class PatchJoinValidation:
    joined_rows: int
    exact_brickname_matches: bool
    brickids_equal: bool


def _join_index(rows: Iterable[JoinRowInput]) -> dict[bytes, list[ValidatedJoinRow]]:
    index: dict[bytes, list[ValidatedJoinRow]] = {}
    for supplied in rows:
        row = validate_join_row(supplied)
        index.setdefault(row.brickname.raw, []).append(row)
    return index


def validate_patch_joins(
    patch: ValidatedPatchList,
    root_rows: Iterable[JoinRowInput],
    south_rows: Iterable[JoinRowInput],
) -> PatchJoinValidation:
    if not isinstance(patch, ValidatedPatchList):
        raise InputError(PATCH_JOIN_INVALID)
    root = _join_index(root_rows)
    south = _join_index(south_rows)
    for member in patch.rows:
        root_matches = root.get(member.brickname.raw, ())
        if len(root_matches) != 1 or root_matches[0].brickid != member.brickid:
            raise IntegrityError(PATCH_JOIN_INVALID)
        south_matches = south.get(member.brickname.raw, ())
        if len(south_matches) != 1 or south_matches[0].brickid != member.brickid:
            raise IntegrityError(PATCH_JOIN_INVALID)
    return PatchJoinValidation(PATCH_CARDINALITY, True, True)


@dataclass(frozen=True)
class ExpectedProviderFullFileSha256:
    role: PhysicalRole
    value: str

    def __post_init__(self) -> None:
        contract = PRODUCTION_PHYSICAL_CONTRACTS.get(self.role)
        expected = contract.expected_provider_full_file_sha256 if contract else None
        if expected is None or self.value != expected or not _valid_sha256(self.value):
            raise InputError(FULL_FILE_SHA256_INVALID)


@dataclass(frozen=True)
class LocallyComputedFullFileSha256:
    value: str
    byte_scope: str = "COMPLETE_FILE"

    def __post_init__(self) -> None:
        if self.byte_scope != "COMPLETE_FILE" or not _valid_sha256(self.value):
            raise InputError(COMPLETE_FILE_DIGEST_REQUIRED)


@dataclass(frozen=True)
class PartialFileSha256:
    value: str
    byte_scope: str = "PARTIAL_FILE"

    def __post_init__(self) -> None:
        if self.byte_scope != "PARTIAL_FILE" or not _valid_sha256(self.value):
            raise InputError(FULL_FILE_SHA256_INVALID)


@dataclass(frozen=True)
class ProviderIntegrityValidation:
    role: PhysicalRole
    expected: ExpectedProviderFullFileSha256
    locally_computed: LocallyComputedFullFileSha256
    complete_file_equal: bool
    production_state_mutated: bool = False


_EXPECTED_PROVIDER_DIGESTS = {
    role: ExpectedProviderFullFileSha256(role, contract.expected_provider_full_file_sha256)
    for role, contract in PRODUCTION_PHYSICAL_CONTRACTS.items()
    if contract.expected_provider_full_file_sha256 is not None
}
EXPECTED_PROVIDER_FULL_FILE_SHA256 = MappingProxyType(_EXPECTED_PROVIDER_DIGESTS)


def validate_provider_full_file_integrity(
    role: PhysicalRole,
    locally_computed: LocallyComputedFullFileSha256,
) -> ProviderIntegrityValidation:
    if role not in EXPECTED_PROVIDER_FULL_FILE_SHA256:
        raise InputError(PATCH_LIST_PROVIDER_CHECKSUM_NOT_FOUND)
    if not isinstance(locally_computed, LocallyComputedFullFileSha256):
        raise InputError(COMPLETE_FILE_DIGEST_REQUIRED)
    expected = EXPECTED_PROVIDER_FULL_FILE_SHA256[role]
    if locally_computed.value != expected.value:
        raise IntegrityError(FULL_FILE_SHA256_MISMATCH)
    return ProviderIntegrityValidation(role, expected, locally_computed, True, False)


@dataclass(frozen=True)
class ProviderPublishedSha256:
    role: PhysicalRole
    value: None
    status: str

    def __post_init__(self) -> None:
        if (self.role is not PhysicalRole.SOUTH_PATCH_LIST or self.value is not None or
                self.status != PATCH_LIST_PROVIDER_CHECKSUM_NOT_FOUND):
            raise InputError(PATCH_LIST_PROVIDER_CHECKSUM_NOT_FOUND)


PATCH_PROVIDER_PUBLISHED_SHA256 = ProviderPublishedSha256(
    PhysicalRole.SOUTH_PATCH_LIST, None, PATCH_LIST_PROVIDER_CHECKSUM_NOT_FOUND
)


@dataclass(frozen=True)
class PatchRepresentationIdentity:
    content_length: int
    etag: str
    last_modified: str
    final_url: str
    redirected: bool


EXPECTED_PATCH_REPRESENTATION = PatchRepresentationIdentity(
    PATCH_CONTENT_LENGTH, PATCH_ETAG, PATCH_LAST_MODIFIED, PATCH_RESOURCE_URL, False
)


def validate_patch_representation(identity: PatchRepresentationIdentity) -> PatchRepresentationIdentity:
    if (not isinstance(identity, PatchRepresentationIdentity) or
            type(identity.content_length) is not int or
            type(identity.etag) is not str or
            type(identity.last_modified) is not str or
            type(identity.final_url) is not str or
            type(identity.redirected) is not bool or
            identity != EXPECTED_PATCH_REPRESENTATION):
        raise IntegrityError(PATCH_LIST_REPRESENTATION_DRIFT_STOP)
    return identity


@dataclass(frozen=True)
class AcquisitionBoundLocalSha256:
    role: PhysicalRole
    resource_url: str
    physical_contract_sha256: str
    authorization_sha256: str
    implementation_aggregate: str
    environment_fingerprint: str
    representation_identity: PatchRepresentationIdentity
    acquired_byte_count: int
    local_sha256: str
    synthetic_only: bool

    def __post_init__(self) -> None:
        values = (self.authorization_sha256, self.implementation_aggregate,
                  self.environment_fingerprint, self.local_sha256)
        if (self.role is not PhysicalRole.SOUTH_PATCH_LIST or
                self.resource_url != PATCH_RESOURCE_URL or
                self.physical_contract_sha256 != PHYSICAL_CONTRACT_HASHES[PhysicalRole.SOUTH_PATCH_LIST] or
                not all(_valid_sha256(value) for value in values) or
                type(self.acquired_byte_count) is not int or
                self.acquired_byte_count != PATCH_CONTENT_LENGTH or
                type(self.synthetic_only) is not bool):
            raise InputError("PATCH_ACQUISITION_BINDING_INVALID")
        validate_patch_representation(self.representation_identity)


@dataclass(frozen=True)
class PatchIntegrityState:
    provider_published_checksum_known: bool
    acquisition_bound_local_sha256_known: bool
    full_file_integrity_bound: bool


PATCH_INTEGRITY_STATE = PatchIntegrityState(False, False, False)


def production_activation_snapshot():
    """Return the unchanged immutable production states for audit assertions."""
    return ACTIVATION_STATES
