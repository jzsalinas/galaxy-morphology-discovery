"""Frozen Amendment-004 DR9 physical schemas; no production row permission.

The contracts are constants derived from the prospectively frozen documentary
specification.  Header validation is read-only and never accesses ``hdu.data``.
Activation states are immutable and deliberately independent.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from types import MappingProxyType

from .core import InputError, IntegrityError, hash_object


AMENDMENT_003_SHA256 = "ca8d2884995a2f3411bc24bb7a2003752153e99ca06cca7c5ba9f2163b47aa8c"
AMENDMENT_004_SHA256 = "842d7b62e3a5408c88d534b3e531a6e2d85a4eb66593f2b0c9bf91bb7fe3fe48"
PHYSICAL_CONTRACT_DOCUMENT_SHA256 = "bdf38d98866de8a7a9ee1c4e495dafea9492e8fc2980edf307b5fb6951040e6b"
POST_PROBE_001_CLARIFICATION_SHA256 = "930909ebdfffff58bc0c88cbbab9c619128cb4ab7adb8df9ec6a88e82324e155"
PHYSICAL_CONTRACT_VERSION = "OC3_DR9_PROVIDER_PHYSICAL_CONTRACT_V1"
REGRESSION_STATE = "POST_PROBE_001"
REGRESSION_INVARIANT = "ONE_AUDITED_REAL_PROBE_ATTEMPT_EXPECTED"
PATCH_CHECKSUM_STATUS = "PATCH_LIST_PROVIDER_CHECKSUM_NOT_FOUND"
PATCH_MEMBERSHIP_FIELD_STATUS = "STRUCTURAL_MEMBERSHIP_KEY_CANDIDATE"
PRODUCTION_DECODE_BLOCKER = "PRODUCTION_PROVIDER_DECODE_NOT_ENABLED"
ROW_SEMANTICS_BLOCKER = "PROVIDER_ROW_SEMANTICS_NOT_VALIDATED"
PHYSICAL_SCHEMA_CONFLICT = "PROVIDER_PHYSICAL_SCHEMA_CONFLICT"
PATCH_INTEGRITY_UNRESOLVED = "PATCH_LIST_FULL_FILE_INTEGRITY_UNRESOLVED"


class PhysicalRole(str, Enum):
    ROOT_SUMMARY = "ROOT_SUMMARY"
    NORTH_SUMMARY = "NORTH_SUMMARY"
    SOUTH_SUMMARY = "SOUTH_SUMMARY"
    SOUTH_PATCH_LIST = "SOUTH_PATCH_LIST"


@dataclass(frozen=True)
class FrozenColumn:
    ttype: str
    tform: str
    tunit_absent: bool = True
    tnull_absent: bool = True
    tscal_absent: bool = True
    tzero_absent: bool = True

    def object(self) -> dict:
        return {
            "tform": self.tform,
            "tnull": "ABSENT" if self.tnull_absent else "PRESENT",
            "tscal": "ABSENT" if self.tscal_absent else "PRESENT",
            "ttype": self.ttype,
            "tunit": "ABSENT" if self.tunit_absent else "PRESENT",
            "tzero": "ABSENT" if self.tzero_absent else "PRESENT",
        }


@dataclass(frozen=True)
class ActivationState:
    physical_schema_frozen: bool
    expected_provider_checksum_known: bool
    full_file_integrity_bound: bool
    row_semantics_validated: bool
    production_decode_enabled: bool

    def object(self) -> dict:
        return {
            "expected_provider_checksum_known": self.expected_provider_checksum_known,
            "full_file_integrity_bound": self.full_file_integrity_bound,
            "physical_schema_frozen": self.physical_schema_frozen,
            "production_decode_enabled": self.production_decode_enabled,
            "row_semantics_validated": self.row_semantics_validated,
        }


@dataclass(frozen=True)
class FrozenPhysicalContract:
    role: PhysicalRole
    resource_url: str
    compression: str
    target_hdu_index: int
    xtension: str
    bitpix: int
    naxis: int
    naxis1: int
    naxis2: int
    pcount: int
    gcount: int
    columns: tuple[FrozenColumn, ...]
    expected_provider_full_file_sha256: str | None
    checksum_status: str
    extname_absent: bool = True
    checksum_absent: bool = True
    datasum_absent: bool = True
    version: str = PHYSICAL_CONTRACT_VERSION

    @property
    def tfields(self) -> int:
        return len(self.columns)

    @property
    def contract_id(self) -> str:
        return f"{self.version}:{self.role.value}"

    def object(self) -> dict:
        return {
            "BITPIX": self.bitpix,
            "CHECKSUM": "ABSENT" if self.checksum_absent else "PRESENT",
            "DATASUM": "ABSENT" if self.datasum_absent else "PRESENT",
            "EXTNAME": "ABSENT" if self.extname_absent else "PRESENT",
            "GCOUNT": self.gcount,
            "NAXIS": self.naxis,
            "NAXIS1": self.naxis1,
            "NAXIS2": self.naxis2,
            "PCOUNT": self.pcount,
            "TFIELDS": self.tfields,
            "XTENSION": self.xtension,
            "checksum_status": self.checksum_status,
            "columns": [column.object() for column in self.columns],
            "compression": self.compression,
            "contract_id": self.contract_id,
            "expected_provider_full_file_sha256": self.expected_provider_full_file_sha256,
            "resource_url": self.resource_url,
            "role": self.role.value,
            "target_hdu_index": self.target_hdu_index,
            "version": self.version,
        }

    @property
    def sha256(self) -> str:
        return hash_object(self.object())


def _columns(items: tuple[tuple[str, str], ...]) -> tuple[FrozenColumn, ...]:
    return tuple(FrozenColumn(name, tform) for name, tform in items)


ROOT_COLUMNS = _columns((
    ("BRICKNAME", "8A"), ("BRICKID", "J"), ("BRICKQ", "I"),
    ("BRICKROW", "J"), ("BRICKCOL", "J"), ("RA", "D"),
    ("DEC", "D"), ("RA1", "D"), ("RA2", "D"),
    ("DEC1", "D"), ("DEC2", "D"),
))

REGIONAL_COLUMNS = _columns((
    ("brickname", "8A"), ("ra", "D"), ("dec", "D"),
    ("nexp_g", "I"), ("nexp_r", "I"), ("nexp_z", "I"),
    ("nexphist_g", "6J"), ("nexphist_r", "6J"), ("nexphist_z", "6J"),
    ("nobjs", "J"), ("npsf", "J"), ("nsimp", "J"),
    ("nrex", "J"), ("nexp", "J"), ("ndev", "J"),
    ("ncomp", "J"), ("nser", "J"), ("ndup", "J"),
    ("psfsize_g", "E"), ("psfsize_r", "E"), ("psfsize_z", "E"),
    ("psfdepth_g", "E"), ("psfdepth_r", "E"), ("psfdepth_z", "E"),
    ("galdepth_g", "E"), ("galdepth_r", "E"), ("galdepth_z", "E"),
    ("ebv", "E"), ("trans_g", "E"), ("trans_r", "E"),
    ("trans_z", "E"), ("cosky_g", "E"), ("cosky_r", "E"),
    ("cosky_z", "E"), ("ext_g", "E"), ("ext_r", "E"),
    ("ext_z", "E"), ("wise_nobs", "4I"), ("trans_wise", "4E"),
    ("ext_w1", "E"), ("ext_w2", "E"), ("ext_w3", "E"),
    ("ext_w4", "E"), ("brickid", "J"), ("ra1", "D"),
    ("ra2", "D"), ("dec1", "D"), ("dec2", "D"),
    ("area", "D"), ("survey_primary", "L"), ("in_desi", "L"),
))

PATCH_COLUMNS = _columns((("RELEASE", "I"), ("BRICKID", "J"), ("BRICKNAME", "8A")))


ROOT_SUMMARY = FrozenPhysicalContract(
    PhysicalRole.ROOT_SUMMARY,
    "https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/survey-bricks.fits.gz",
    "gzip", 1, "BINTABLE", 8, 2, 70, 662174, 0, 1, ROOT_COLUMNS,
    "dc943d702357f93553b9e5d15e87ace38df94eb7095f4100657407b3f9919c5f",
    "EXPECTED_PROVIDER_CHECKSUM_KNOWN",
)
NORTH_SUMMARY = FrozenPhysicalContract(
    PhysicalRole.NORTH_SUMMARY,
    "https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/north/survey-bricks-dr9-north.fits.gz",
    "gzip", 1, "BINTABLE", 8, 2, 300, 93548, 0, 1, REGIONAL_COLUMNS,
    "2edd5c295fdad26852c6f224a3ff023cff43dd0e03a53acd35b767e726ee72fb",
    "EXPECTED_PROVIDER_CHECKSUM_KNOWN",
)
SOUTH_SUMMARY = FrozenPhysicalContract(
    PhysicalRole.SOUTH_SUMMARY,
    "https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/south/survey-bricks-dr9-south.fits.gz",
    "gzip", 1, "BINTABLE", 8, 2, 300, 253658, 0, 1, REGIONAL_COLUMNS,
    "7360414f5d53571ca70fa0cb483eb8c80cfcbe80df0856a117246f442a0b9a3f",
    "EXPECTED_PROVIDER_CHECKSUM_KNOWN",
)
SOUTH_PATCH_LIST = FrozenPhysicalContract(
    PhysicalRole.SOUTH_PATCH_LIST,
    "https://www.legacysurvey.org/files/dr9-south-patched-bricks.fits",
    "identity", 1, "BINTABLE", 8, 2, 14, 1691, 0, 1, PATCH_COLUMNS,
    None, PATCH_CHECKSUM_STATUS,
)

PRODUCTION_PHYSICAL_CONTRACTS = MappingProxyType({
    contract.role: contract for contract in
    (ROOT_SUMMARY, NORTH_SUMMARY, SOUTH_SUMMARY, SOUTH_PATCH_LIST)
})
PHYSICAL_CONTRACT_HASHES = MappingProxyType({
    role: contract.sha256 for role, contract in PRODUCTION_PHYSICAL_CONTRACTS.items()
})

ACTIVATION_STATES = MappingProxyType({
    PhysicalRole.ROOT_SUMMARY: ActivationState(True, True, False, False, False),
    PhysicalRole.NORTH_SUMMARY: ActivationState(True, True, False, False, False),
    PhysicalRole.SOUTH_SUMMARY: ActivationState(True, True, False, False, False),
    PhysicalRole.SOUTH_PATCH_LIST: ActivationState(True, False, False, False, False),
})


def require_production_decode(role: PhysicalRole) -> None:
    state = ACTIVATION_STATES[role]
    if not (state.physical_schema_frozen and
            state.expected_provider_checksum_known and
            state.full_file_integrity_bound and
            state.row_semantics_validated and
            state.production_decode_enabled):
        raise InputError(PRODUCTION_DECODE_BLOCKER)


def require_row_semantics(role: PhysicalRole) -> None:
    if not ACTIVATION_STATES[role].row_semantics_validated:
        raise InputError(ROW_SEMANTICS_BLOCKER)


def compare_complete_file_sha256(role: PhysicalRole, locally_computed_sha256: str) -> bool:
    contract = PRODUCTION_PHYSICAL_CONTRACTS[role]
    expected = contract.expected_provider_full_file_sha256
    if expected is None:
        raise InputError(PATCH_INTEGRITY_UNRESOLVED)
    if not re.fullmatch(r"[0-9a-f]{64}", locally_computed_sha256 or ""):
        raise InputError("FULL_FILE_SHA256_INVALID")
    if locally_computed_sha256 != expected:
        raise IntegrityError("FULL_FILE_SHA256_MISMATCH")
    return True


def validate_fits_structure(path, contract: FrozenPhysicalContract) -> str:
    """Validate only frozen FITS header structure; never return or access rows."""
    try:
        from astropy.io import fits
        with fits.open(path, mode="readonly", memmap=True, lazy_load_hdus=True,
                       do_not_scale_image_data=True, uint=False) as hdus:
            if contract.target_hdu_index >= len(hdus):
                raise InputError(PHYSICAL_SCHEMA_CONFLICT)
            hdu = hdus[contract.target_hdu_index]
            if not isinstance(hdu, fits.BinTableHDU):
                raise InputError(PHYSICAL_SCHEMA_CONFLICT)
            header = hdu.header
            expected = {
                "XTENSION": contract.xtension, "BITPIX": contract.bitpix,
                "NAXIS": contract.naxis, "NAXIS1": contract.naxis1,
                "NAXIS2": contract.naxis2, "PCOUNT": contract.pcount,
                "GCOUNT": contract.gcount, "TFIELDS": contract.tfields,
            }
            if any(header.get(key) != value for key, value in expected.items()):
                raise InputError(PHYSICAL_SCHEMA_CONFLICT)
            for key, absent in (("EXTNAME", contract.extname_absent),
                                ("CHECKSUM", contract.checksum_absent),
                                ("DATASUM", contract.datasum_absent)):
                if absent and key in header:
                    raise InputError(PHYSICAL_SCHEMA_CONFLICT)
            for index, column in enumerate(contract.columns, 1):
                if header.get(f"TTYPE{index}") != column.ttype:
                    raise InputError(PHYSICAL_SCHEMA_CONFLICT)
                if header.get(f"TFORM{index}") != column.tform:
                    raise InputError(PHYSICAL_SCHEMA_CONFLICT)
                for prefix, absent in (("TUNIT", column.tunit_absent),
                                       ("TNULL", column.tnull_absent),
                                       ("TSCAL", column.tscal_absent),
                                       ("TZERO", column.tzero_absent)):
                    if absent and f"{prefix}{index}" in header:
                        raise InputError(PHYSICAL_SCHEMA_CONFLICT)
    except (InputError, IntegrityError):
        raise
    except Exception as exc:
        raise InputError(PHYSICAL_SCHEMA_CONFLICT) from exc
    return contract.sha256
