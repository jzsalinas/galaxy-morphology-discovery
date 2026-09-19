"""Amendment-003 provider-schema boundary.

Production physical contracts and the production 9012 patch-list decoder are
deliberately unavailable.  Synthetic tests may provide exact local FITS
contracts; the adapter validates all schema metadata before reading only the
byte ranges belonging to TECHNICAL_ALLOWED columns.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import math
from pathlib import Path
import re
import struct
from types import MappingProxyType
from typing import ClassVar, Iterable

from .core import InputError, IntegrityError, canonical, digest, file_hash, hash_object
from .provider_physical_contracts import (
    PhysicalRole, PRODUCTION_PHYSICAL_CONTRACTS as FROZEN_PHYSICAL_CONTRACTS,
    require_production_decode,
)


ADAPTER_VERSION = "PROVIDER_SCHEMA_ADAPTER_V1"
HISTORICAL_LOGICAL_CONTRACT_VERSION = "OC3_DR9_PROVIDER_LOGICAL_V1"
HISTORICAL_LOGICAL_CONTRACT_SHA256 = "301ef8bf8d30da2f9bc0410146a7faa6537e4badb5100ae57128d3f4ff5b4373"
LOGICAL_CONTRACT_VERSION = "OC3_DR9_PROVIDER_LOGICAL_V2_AMENDMENT_004"
FIELD_ID_NAMESPACE = "OC3_PROVIDER_FIELD_ID_V1"
CANDIDATE_DTO_VERSION = "OC3_TECHNICAL_CANDIDATE_V1"
GRZ_AUDIT_VERSION = "OC3_GRZ_TECHNICAL_AUDIT_V1"
GRZ_PREDICATE_VERSION = "GRZ_MEDIAN_PRESENT_V1"
PATCH_LIST_STATUS = "PATCH_LIST_ADAPTER_DISABLED"
HISTORICAL_BRICKID_STATUS = "DOCUMENTED_PROVIDER_TYPE_INCONSISTENCY"
BRICKID_STATUS = "BRICKID_PHYSICAL_LAYOUT_CORRECTED_AMENDMENT_004"
SCHEMA_CONFLICT = "PROVIDER_SCHEMA_DOCUMENTATION_CONFLICT_STOP"


class FieldClass(str, Enum):
    TECHNICAL_ALLOWED = "TECHNICAL_ALLOWED"
    KNOWN_BUT_FORBIDDEN = "KNOWN_BUT_FORBIDDEN"


class ProviderRole(str, Enum):
    ROOT_GEOMETRY = "ROOT_GEOMETRY"
    REGIONAL_NORTH = "REGIONAL_NORTH"
    REGIONAL_SOUTH = "REGIONAL_SOUTH"


class FieldId(str, Enum):
    ROOT_BRICKNAME = "root.brickname"
    ROOT_BRICKID = "root.brickid"
    ROOT_BRICKQ = "root.brickq"
    ROOT_BRICKROW = "root.brickrow"
    ROOT_BRICKCOL = "root.brickcol"
    ROOT_RA = "root.ra"
    ROOT_DEC = "root.dec"
    ROOT_RA1 = "root.ra1"
    ROOT_RA2 = "root.ra2"
    ROOT_DEC1 = "root.dec1"
    ROOT_DEC2 = "root.dec2"

    REG_BRICKNAME = "regional.brickname"
    REG_RA = "regional.ra"
    REG_DEC = "regional.dec"
    REG_NEXP_G = "regional.nexp_g"
    REG_NEXP_R = "regional.nexp_r"
    REG_NEXP_Z = "regional.nexp_z"
    REG_NEXPHIST_G = "regional.nexphist_g"
    REG_NEXPHIST_R = "regional.nexphist_r"
    REG_NEXPHIST_Z = "regional.nexphist_z"
    REG_BRICKID = "regional.brickid"
    REG_RA1 = "regional.ra1"
    REG_RA2 = "regional.ra2"
    REG_DEC1 = "regional.dec1"
    REG_DEC2 = "regional.dec2"
    REG_AREA = "regional.area"
    REG_SURVEY_PRIMARY = "regional.survey_primary"

    REG_NOBJS = "regional.nobjs"
    REG_NPSF = "regional.npsf"
    REG_NSIM = "regional.nsimp"
    REG_NREX = "regional.nrex"
    REG_NEXP = "regional.nexp"
    REG_NDEV = "regional.ndev"
    REG_NCOMP = "regional.ncomp"
    REG_NSER = "regional.nser"
    REG_NDUP = "regional.ndup"
    REG_PSFSIZE_G = "regional.psfsize_g"
    REG_PSFSIZE_R = "regional.psfsize_r"
    REG_PSFSIZE_Z = "regional.psfsize_z"
    REG_PSFDEPTH_G = "regional.psfdepth_g"
    REG_PSFDEPTH_R = "regional.psfdepth_r"
    REG_PSFDEPTH_Z = "regional.psfdepth_z"
    REG_GALDEPTH_G = "regional.galdepth_g"
    REG_GALDEPTH_R = "regional.galdepth_r"
    REG_GALDEPTH_Z = "regional.galdepth_z"
    REG_EBV = "regional.ebv"
    REG_TRANS_G = "regional.trans_g"
    REG_TRANS_R = "regional.trans_r"
    REG_TRANS_Z = "regional.trans_z"
    REG_COSKY_G = "regional.cosky_g"
    REG_COSKY_R = "regional.cosky_r"
    REG_COSKY_Z = "regional.cosky_z"
    REG_EXT_G = "regional.ext_g"
    REG_EXT_R = "regional.ext_r"
    REG_EXT_Z = "regional.ext_z"
    REG_WISE_NOBS = "regional.wise_nobs"
    REG_TRANS_WISE = "regional.trans_wise"
    REG_EXT_W1 = "regional.ext_w1"
    REG_EXT_W2 = "regional.ext_w2"
    REG_EXT_W3 = "regional.ext_w3"
    REG_EXT_W4 = "regional.ext_w4"
    REG_IN_DESI = "regional.in_desi"


@dataclass(frozen=True)
class LogicalField:
    field_id: FieldId
    role_family: str
    provider_name: str
    classification: FieldClass
    logical_type: str
    transform: str


def _allowed(field_id: FieldId, role: str, name: str, logical: str, transform: str) -> LogicalField:
    return LogicalField(field_id, role, name, FieldClass.TECHNICAL_ALLOWED, logical, transform)


def _forbidden(field_id: FieldId, name: str, logical: str) -> LogicalField:
    return LogicalField(field_id, "regional", name, FieldClass.KNOWN_BUT_FORBIDDEN,
                        logical, "SCHEMA_METADATA_ONLY")


ROOT_LOGICAL_FIELDS = (
    _allowed(FieldId.ROOT_BRICKNAME, "root", "BRICKNAME", "char[8]", "IDENTITY"),
    _allowed(FieldId.ROOT_BRICKID, "root", "BRICKID", "int32", "IDENTITY"),
    _allowed(FieldId.ROOT_BRICKQ, "root", "BRICKQ", "int16", "GEOMETRY_AUDIT"),
    _allowed(FieldId.ROOT_BRICKROW, "root", "BRICKROW", "int32", "GEOMETRY_AUDIT"),
    _allowed(FieldId.ROOT_BRICKCOL, "root", "BRICKCOL", "int32", "GEOMETRY_AUDIT"),
    _allowed(FieldId.ROOT_RA, "root", "RA", "float64", "CANDIDATE_RA"),
    _allowed(FieldId.ROOT_DEC, "root", "DEC", "float64", "CANDIDATE_DEC"),
    _allowed(FieldId.ROOT_RA1, "root", "RA1", "float64", "PRIMARY_BOUNDS"),
    _allowed(FieldId.ROOT_RA2, "root", "RA2", "float64", "PRIMARY_BOUNDS"),
    _allowed(FieldId.ROOT_DEC1, "root", "DEC1", "float64", "PRIMARY_BOUNDS"),
    _allowed(FieldId.ROOT_DEC2, "root", "DEC2", "float64", "PRIMARY_BOUNDS"),
)

REGIONAL_ALLOWED_FIELDS = (
    _allowed(FieldId.REG_BRICKNAME, "regional", "brickname", "char[8]", "IDENTITY"),
    _allowed(FieldId.REG_RA, "regional", "ra", "float64", "GEOMETRY_AUDIT"),
    _allowed(FieldId.REG_DEC, "regional", "dec", "float64", "GEOMETRY_AUDIT"),
    _allowed(FieldId.REG_NEXP_G, "regional", "nexp_g", "int16", GRZ_PREDICATE_VERSION),
    _allowed(FieldId.REG_NEXP_R, "regional", "nexp_r", "int16", GRZ_PREDICATE_VERSION),
    _allowed(FieldId.REG_NEXP_Z, "regional", "nexp_z", "int16", GRZ_PREDICATE_VERSION),
    _allowed(FieldId.REG_NEXPHIST_G, "regional", "nexphist_g", "int32[6]", "AUDIT_ONLY"),
    _allowed(FieldId.REG_NEXPHIST_R, "regional", "nexphist_r", "int32[6]", "AUDIT_ONLY"),
    _allowed(FieldId.REG_NEXPHIST_Z, "regional", "nexphist_z", "int32[6]", "AUDIT_ONLY"),
    _allowed(FieldId.REG_BRICKID, "regional", "brickid", "int32", "IDENTITY_CONFLICT_GATED"),
    _allowed(FieldId.REG_RA1, "regional", "ra1", "float64", "GEOMETRY_AUDIT"),
    _allowed(FieldId.REG_RA2, "regional", "ra2", "float64", "GEOMETRY_AUDIT"),
    _allowed(FieldId.REG_DEC1, "regional", "dec1", "float64", "GEOMETRY_AUDIT"),
    _allowed(FieldId.REG_DEC2, "regional", "dec2", "float64", "GEOMETRY_AUDIT"),
    _allowed(FieldId.REG_AREA, "regional", "area", "float64", "AUDIT_ONLY"),
    _allowed(FieldId.REG_SURVEY_PRIMARY, "regional", "survey_primary", "boolean", "CANDIDATE_AUDIT"),
)

REGIONAL_FORBIDDEN_FIELDS = (
    _forbidden(FieldId.REG_NOBJS, "nobjs", "int32"),
    _forbidden(FieldId.REG_NPSF, "npsf", "int32"),
    _forbidden(FieldId.REG_NSIM, "nsimp", "int32"),
    _forbidden(FieldId.REG_NREX, "nrex", "int32"),
    _forbidden(FieldId.REG_NEXP, "nexp", "int32"),
    _forbidden(FieldId.REG_NDEV, "ndev", "int32"),
    _forbidden(FieldId.REG_NCOMP, "ncomp", "int32"),
    _forbidden(FieldId.REG_NSER, "nser", "int32"),
    _forbidden(FieldId.REG_NDUP, "ndup", "int32"),
    _forbidden(FieldId.REG_PSFSIZE_G, "psfsize_g", "float32"),
    _forbidden(FieldId.REG_PSFSIZE_R, "psfsize_r", "float32"),
    _forbidden(FieldId.REG_PSFSIZE_Z, "psfsize_z", "float32"),
    _forbidden(FieldId.REG_PSFDEPTH_G, "psfdepth_g", "float32"),
    _forbidden(FieldId.REG_PSFDEPTH_R, "psfdepth_r", "float32"),
    _forbidden(FieldId.REG_PSFDEPTH_Z, "psfdepth_z", "float32"),
    _forbidden(FieldId.REG_GALDEPTH_G, "galdepth_g", "float32"),
    _forbidden(FieldId.REG_GALDEPTH_R, "galdepth_r", "float32"),
    _forbidden(FieldId.REG_GALDEPTH_Z, "galdepth_z", "float32"),
    _forbidden(FieldId.REG_EBV, "ebv", "float32"),
    _forbidden(FieldId.REG_TRANS_G, "trans_g", "float32"),
    _forbidden(FieldId.REG_TRANS_R, "trans_r", "float32"),
    _forbidden(FieldId.REG_TRANS_Z, "trans_z", "float32"),
    _forbidden(FieldId.REG_COSKY_G, "cosky_g", "float32"),
    _forbidden(FieldId.REG_COSKY_R, "cosky_r", "float32"),
    _forbidden(FieldId.REG_COSKY_Z, "cosky_z", "float32"),
    _forbidden(FieldId.REG_EXT_G, "ext_g", "float32"),
    _forbidden(FieldId.REG_EXT_R, "ext_r", "float32"),
    _forbidden(FieldId.REG_EXT_Z, "ext_z", "float32"),
    _forbidden(FieldId.REG_WISE_NOBS, "wise_nobs", "int16[4]"),
    _forbidden(FieldId.REG_TRANS_WISE, "trans_wise", "float32[4]"),
    _forbidden(FieldId.REG_EXT_W1, "ext_w1", "float32"),
    _forbidden(FieldId.REG_EXT_W2, "ext_w2", "float32"),
    _forbidden(FieldId.REG_EXT_W3, "ext_w3", "float32"),
    _forbidden(FieldId.REG_EXT_W4, "ext_w4", "float32"),
    _forbidden(FieldId.REG_IN_DESI, "in_desi", "boolean"),
)

REGIONAL_LOGICAL_FIELDS = REGIONAL_ALLOWED_FIELDS + REGIONAL_FORBIDDEN_FIELDS
ALL_LOGICAL_FIELDS = ROOT_LOGICAL_FIELDS + REGIONAL_LOGICAL_FIELDS
FIELD_BY_ID = MappingProxyType({field.field_id: field for field in ALL_LOGICAL_FIELDS})

AMENDMENT_004_CORRECTED_TYPES = MappingProxyType({
    FieldId.REG_BRICKID: "int32",
    FieldId.REG_NOBJS: "int32", FieldId.REG_NPSF: "int32",
    FieldId.REG_NSIM: "int32", FieldId.REG_NREX: "int32",
    FieldId.REG_NEXP: "int32", FieldId.REG_NDEV: "int32",
    FieldId.REG_NCOMP: "int32", FieldId.REG_NSER: "int32",
    FieldId.REG_NDUP: "int32",
    FieldId.REG_RA1: "float64", FieldId.REG_RA2: "float64",
    FieldId.REG_DEC1: "float64", FieldId.REG_DEC2: "float64",
    FieldId.REG_AREA: "float64",
})
_HISTORICAL_TYPES = MappingProxyType({
    FieldId.REG_BRICKID: "int16_DOCUMENTED_TYPE",
    FieldId.REG_NOBJS: "int16", FieldId.REG_NPSF: "int16",
    FieldId.REG_NSIM: "int16", FieldId.REG_NREX: "int16",
    FieldId.REG_NEXP: "int16", FieldId.REG_NDEV: "int16",
    FieldId.REG_NCOMP: "int16", FieldId.REG_NSER: "int16",
    FieldId.REG_NDUP: "int16",
    FieldId.REG_RA1: "float32", FieldId.REG_RA2: "float32",
    FieldId.REG_DEC1: "float32", FieldId.REG_DEC2: "float32",
    FieldId.REG_AREA: "float32",
})


def _logical_contract_object() -> dict:
    def item(field: LogicalField) -> dict:
        return {"classification": field.classification.value, "field_id": field.field_id.value,
                "logical_type": field.logical_type, "provider_name": field.provider_name,
                "role_family": field.role_family, "transform": field.transform}
    return {"version": LOGICAL_CONTRACT_VERSION,
            "root": [item(field) for field in ROOT_LOGICAL_FIELDS],
            "regional": [item(field) for field in REGIONAL_LOGICAL_FIELDS],
            "brickid_status": BRICKID_STATUS}


LOGICAL_CONTRACT_SHA256 = hash_object(_logical_contract_object())


def historical_logical_contract_object() -> dict:
    """Exact V1 logical identity retained for audit, never used for decode."""
    current = _logical_contract_object()
    regional = []
    for item in current["regional"]:
        copy = dict(item)
        field_id = FieldId(copy["field_id"])
        if field_id in _HISTORICAL_TYPES:
            copy["logical_type"] = _HISTORICAL_TYPES[field_id]
        regional.append(copy)
    return {"version": HISTORICAL_LOGICAL_CONTRACT_VERSION,
            "root": current["root"], "regional": regional,
            "brickid_status": HISTORICAL_BRICKID_STATUS}


@dataclass(frozen=True)
class PhysicalField:
    field_id: FieldId
    tform: str
    unit: str | None = None
    null: int | str | None = None
    bscale: int | float | None = None
    bzero: int | float | None = None
    string_policy: str | None = None


@dataclass(frozen=True)
class PhysicalContract:
    contract_id: str
    version: int
    role: ProviderRole
    hdu_index: int
    fields: tuple[PhysicalField, ...]
    synthetic_only: bool

    def object(self) -> dict:
        return {"contract_id": self.contract_id, "version": self.version,
                "role": self.role.value, "hdu_index": self.hdu_index,
                "synthetic_only": self.synthetic_only,
                "fields": [{"field_id": f.field_id.value, "tform": f.tform,
                            "unit": f.unit, "null": f.null, "bscale": f.bscale,
                            "bzero": f.bzero, "string_policy": f.string_policy}
                           for f in self.fields]}

    @property
    def sha256(self) -> str:
        return hash_object(self.object())


def _physical(field_id: FieldId, tform: str, *, string_policy: str | None = None) -> PhysicalField:
    return PhysicalField(field_id, tform, string_policy=string_policy)


SYNTHETIC_ROOT_FITS_V1 = PhysicalContract(
    "SYNTHETIC_ROOT_FITS_V1", 1, ProviderRole.ROOT_GEOMETRY, 1,
    (_physical(FieldId.ROOT_BRICKNAME, "8A", string_policy="ASCII_RSTRIP_SPACE_NUL_V1"),
     _physical(FieldId.ROOT_BRICKID, "J"), _physical(FieldId.ROOT_BRICKQ, "I"),
     _physical(FieldId.ROOT_BRICKROW, "J"), _physical(FieldId.ROOT_BRICKCOL, "J"),
     _physical(FieldId.ROOT_RA, "D"), _physical(FieldId.ROOT_DEC, "D"),
     _physical(FieldId.ROOT_RA1, "D"), _physical(FieldId.ROOT_RA2, "D"),
     _physical(FieldId.ROOT_DEC1, "D"), _physical(FieldId.ROOT_DEC2, "D")), True)

_LOGICAL_TFORM = MappingProxyType({
    "char[8]": "8A", "float64": "D", "int16": "I", "int32": "J",
    "int32[6]": "6J", "int16_DOCUMENTED_TYPE": "I", "float32": "E",
    "boolean": "L", "int16[4]": "4I", "float32[4]": "4E",
})

SYNTHETIC_REGIONAL_FITS_V1 = PhysicalContract(
    "SYNTHETIC_REGIONAL_FITS_V1", 1, ProviderRole.REGIONAL_NORTH, 1,
    tuple(_physical(field.field_id,
                    _LOGICAL_TFORM[_HISTORICAL_TYPES.get(field.field_id, field.logical_type)],
                    string_policy="ASCII_RSTRIP_SPACE_NUL_V1" if field.logical_type == "char[8]" else None)
          for field in REGIONAL_LOGICAL_FIELDS), True)

SYNTHETIC_REGIONAL_FITS_V2 = PhysicalContract(
    "SYNTHETIC_REGIONAL_FITS_V2_AMENDMENT_004", 2, ProviderRole.REGIONAL_NORTH, 1,
    tuple(_physical(field.field_id, _LOGICAL_TFORM[field.logical_type],
                    string_policy="ASCII_RSTRIP_SPACE_NUL_V1" if field.logical_type == "char[8]" else None)
          for field in REGIONAL_LOGICAL_FIELDS), True)


_PROVIDER_TO_PHYSICAL_ROLE = MappingProxyType({
    ProviderRole.ROOT_GEOMETRY: PhysicalRole.ROOT_SUMMARY,
    ProviderRole.REGIONAL_NORTH: PhysicalRole.NORTH_SUMMARY,
    ProviderRole.REGIONAL_SOUTH: PhysicalRole.SOUTH_SUMMARY,
})
PRODUCTION_PHYSICAL_CONTRACTS = FROZEN_PHYSICAL_CONTRACTS


def production_physical_contract(role: ProviderRole):
    physical_role = _PROVIDER_TO_PHYSICAL_ROLE.get(role)
    if physical_role is None:
        raise InputError("PRODUCTION_PROVIDER_PHYSICAL_CONTRACT_UNAVAILABLE")
    return PRODUCTION_PHYSICAL_CONTRACTS[physical_role]


def provider_manifest_binding(physical_contract_id: str | None = None) -> dict:
    return {"adapter_version": ADAPTER_VERSION,
            "candidate_dto_version": CANDIDATE_DTO_VERSION,
            "field_id_namespace": FIELD_ID_NAMESPACE,
            "logical_contract_version": LOGICAL_CONTRACT_VERSION,
            "logical_contract_sha256": LOGICAL_CONTRACT_SHA256,
            "physical_contract_id": physical_contract_id}


PROVIDER_BINDING_FIELDS = frozenset(provider_manifest_binding())


def validate_provider_manifest_binding(value: object, *, production: bool) -> dict:
    if not isinstance(value, dict) or set(value) != PROVIDER_BINDING_FIELDS:
        raise InputError("PROVIDER_SCHEMA_BINDING")
    expected = provider_manifest_binding(value.get("physical_contract_id"))
    if value != expected:
        raise IntegrityError("PROVIDER_SCHEMA_BINDING_MISMATCH")
    if production:
        if value["physical_contract_id"] is None:
            raise InputError("PRODUCTION_PROVIDER_PHYSICAL_CONTRACT_UNAVAILABLE")
        if value["physical_contract_id"] not in {c.contract_id for c in PRODUCTION_PHYSICAL_CONTRACTS.values()}:
            raise InputError("PRODUCTION_PROVIDER_PHYSICAL_CONTRACT_UNAVAILABLE")
    return value


@dataclass(frozen=True)
class ProviderIdentity:
    role: ProviderRole
    execution_kind: str
    release_family: str
    region: str | None
    survey: str | None
    generation: str | None
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.execution_kind not in ("SYNTHETIC", "PRODUCTION"):
            raise InputError("PROVIDER_IDENTITY_KIND")
        if self.release_family != "DR9" or not self.evidence_refs:
            raise InputError("PROVIDER_IDENTITY_SCOPE")
        expected = {
            ProviderRole.ROOT_GEOMETRY: (None, None, "DR9"),
            ProviderRole.REGIONAL_NORTH: ("north", "BASS_MzLS", "9011"),
            ProviderRole.REGIONAL_SOUTH: ("south", "DECaLS", None),
        }[self.role]
        if (self.region, self.survey, self.generation) != expected:
            raise InputError("PROVIDER_IDENTITY_ROLE_CONFLICT")


class CellAccessProbe:
    """Synthetic instrumentation; production behavior does not depend on it."""
    def __init__(self) -> None:
        self.allowed_accesses: list[FieldId] = []
        self.forbidden_accesses: list[FieldId] = []
        self.rows_started = 0

    def row_started(self) -> None:
        self.rows_started += 1

    def accessed(self, field_id: FieldId) -> None:
        spec = FIELD_BY_ID[field_id]
        if spec.classification is FieldClass.KNOWN_BUT_FORBIDDEN:
            self.forbidden_accesses.append(field_id)
            raise IntegrityError("FORBIDDEN_PROVIDER_CELL_ACCESS")
        self.allowed_accesses.append(field_id)


@dataclass(frozen=True)
class AllowedProviderTable:
    role: ProviderRole
    contract_id: str
    contract_sha256: str
    resource_sha256: str
    rows: tuple[MappingProxyType, ...]

    def __post_init__(self) -> None:
        for row in self.rows:
            if not isinstance(row, MappingProxyType):
                raise InputError("RAW_PROVIDER_TABLE_FORBIDDEN")
            for key in row:
                if not isinstance(key, FieldId) or FIELD_BY_ID[key].classification is not FieldClass.TECHNICAL_ALLOWED:
                    raise IntegrityError("FORBIDDEN_PROVIDER_CELL_EXPOSED")


_TFORM = re.compile(r"^(\d*)([AIJEDL])$")
_WIDTH = {"A": 1, "L": 1, "I": 2, "J": 4, "E": 4, "D": 8}


def _tform_parts(tform: str) -> tuple[int, str, int]:
    match = _TFORM.fullmatch(tform)
    if not match:
        raise InputError(SCHEMA_CONFLICT)
    repeat = int(match.group(1) or "1")
    code = match.group(2)
    return repeat, code, repeat * _WIDTH[code]


def _decode_cell(raw: bytes, field: PhysicalField):
    repeat, code, width = _tform_parts(field.tform)
    if len(raw) != width:
        raise IntegrityError("PROVIDER_SELECTIVE_READ_TRUNCATED")
    if code == "A":
        try:
            value = raw.decode("ascii")
        except UnicodeDecodeError as exc:
            raise InputError("PROVIDER_ASCII_DECODE") from exc
        if field.string_policy == "ASCII_RSTRIP_SPACE_NUL_V1":
            return value.rstrip(" \x00")
        if field.string_policy is None:
            return value
        raise InputError(SCHEMA_CONFLICT)
    if code == "L":
        values = []
        for value in raw:
            if value == ord("T"):
                values.append(True)
            elif value == ord("F"):
                values.append(False)
            else:
                raise InputError("PROVIDER_LOGICAL_VALUE_INVALID")
    else:
        fmt = {"I": "h", "J": "i", "E": "f", "D": "d"}[code]
        values = list(struct.unpack(">" + fmt * repeat, raw))
    return values[0] if repeat == 1 else tuple(values)


def _contract_fields(contract: PhysicalContract) -> tuple[LogicalField, ...]:
    if not contract.synthetic_only:
        raise InputError("UNREVIEWED_PRODUCTION_PHYSICAL_CONTRACT")
    expected = ROOT_LOGICAL_FIELDS if contract.role is ProviderRole.ROOT_GEOMETRY else REGIONAL_LOGICAL_FIELDS
    ids = tuple(field.field_id for field in contract.fields)
    if ids != tuple(field.field_id for field in expected):
        raise InputError(SCHEMA_CONFLICT)
    if len(set(ids)) != len(ids):
        raise InputError(SCHEMA_CONFLICT)
    for physical, logical in zip(contract.fields, expected):
        if physical.field_id is not logical.field_id:
            raise InputError(SCHEMA_CONFLICT)
        _tform_parts(physical.tform)
    return expected


class ProviderSchemaAdapter:
    version = ADAPTER_VERSION

    def decode(self, path: str | Path, identity: ProviderIdentity, expected_sha256: str,
               physical_contract: PhysicalContract | None = None,
               probe: CellAccessProbe | None = None) -> AllowedProviderTable:
        source = Path(path)
        if identity.execution_kind == "PRODUCTION":
            physical_role = _PROVIDER_TO_PHYSICAL_ROLE[identity.role]
            require_production_decode(physical_role)
            raise InputError("PRODUCTION_PROVIDER_DECODE_NOT_ENABLED")
        else:
            if physical_contract is None or not physical_contract.synthetic_only:
                raise InputError("SYNTHETIC_PHYSICAL_CONTRACT_REQUIRED")
            contract = physical_contract
        if contract.role is not identity.role:
            raise InputError("PROVIDER_ROLE_CONTRACT_MISMATCH")
        if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256 or ""):
            raise InputError("PROVIDER_CHECKSUM_REQUIRED")
        observed_sha256 = file_hash(source)
        if observed_sha256 != expected_sha256:
            raise IntegrityError("PROVIDER_CHECKSUM_MISMATCH")
        logical_fields = _contract_fields(contract)
        return self._inspect_then_select(source, identity.role, contract, logical_fields,
                                         observed_sha256, probe or CellAccessProbe())

    def _inspect_then_select(self, source: Path, role: ProviderRole,
                             contract: PhysicalContract,
                             logical_fields: tuple[LogicalField, ...],
                             resource_sha256: str,
                             probe: CellAccessProbe) -> AllowedProviderTable:
        try:
            from astropy.io import fits
            with fits.open(source, mode="readonly", memmap=True, lazy_load_hdus=True,
                           do_not_scale_image_data=True, uint=False) as hdus:
                if contract.hdu_index >= len(hdus):
                    raise InputError(SCHEMA_CONFLICT)
                hdu = hdus[contract.hdu_index]
                if not isinstance(hdu, fits.BinTableHDU):
                    raise InputError(SCHEMA_CONFLICT)
                header = hdu.header
                if header.get("XTENSION") != "BINTABLE" or header.get("PCOUNT") != 0 or header.get("GCOUNT") != 1:
                    raise InputError(SCHEMA_CONFLICT)
                if header.get("TFIELDS") != len(contract.fields):
                    raise InputError(SCHEMA_CONFLICT)
                offsets = []
                offset = 0
                for index, (physical, logical) in enumerate(zip(contract.fields, logical_fields), 1):
                    # Header inspection only: hdu.data is deliberately never accessed.
                    if header.get(f"TTYPE{index}") != logical.provider_name:
                        raise InputError(SCHEMA_CONFLICT)
                    if header.get(f"TFORM{index}") != physical.tform:
                        raise InputError(SCHEMA_CONFLICT)
                    for prefix, expected in (("TUNIT", physical.unit), ("TNULL", physical.null),
                                             ("TSCAL", physical.bscale), ("TZERO", physical.bzero)):
                        key = f"{prefix}{index}"
                        if (header[key] if key in header else None) != expected:
                            raise InputError(SCHEMA_CONFLICT)
                    _, _, width = _tform_parts(physical.tform)
                    offsets.append((offset, width, physical, logical))
                    offset += width
                if header.get("NAXIS1") != offset:
                    raise InputError(SCHEMA_CONFLICT)
                nrows = header.get("NAXIS2")
                if isinstance(nrows, bool) or not isinstance(nrows, int) or nrows < 0:
                    raise InputError(SCHEMA_CONFLICT)
                info = hdu.fileinfo()
                if not info or not isinstance(info.get("datLoc"), int):
                    raise InputError(SCHEMA_CONFLICT)
                data_start = info["datLoc"]
                row_length = offset
        except (InputError, IntegrityError):
            raise
        except Exception as exc:
            raise InputError(SCHEMA_CONFLICT) from exc

        selected = [(offset, width, physical, logical)
                    for offset, width, physical, logical in offsets
                    if logical.classification is FieldClass.TECHNICAL_ALLOWED]
        rows = []
        with source.open("rb") as stream:
            for row_index in range(nrows):
                probe.row_started()
                row = {}
                for offset, width, physical, logical in selected:
                    probe.accessed(logical.field_id)
                    stream.seek(data_start + row_index * row_length + offset)
                    row[logical.field_id] = _decode_cell(stream.read(width), physical)
                rows.append(MappingProxyType(row))
        return AllowedProviderTable(role, contract.contract_id, contract.sha256,
                                    resource_sha256, tuple(rows))


@dataclass(frozen=True)
class PrimaryBounds:
    ra1: float
    ra2: float
    dec1: float
    dec2: float


@dataclass(frozen=True)
class TechnicalCandidate:
    VERSION: ClassVar[str] = CANDIDATE_DTO_VERSION
    region: str
    survey: str
    release_family: str
    generation: str
    brickname: str
    brickid: int
    ra: float
    dec: float
    primary_bounds: PrimaryBounds
    grz: bool
    corrected_9012: bool
    survey_primary: bool
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.region not in ("north", "south") or self.release_family != "DR9":
            raise InputError("CANDIDATE_SCOPE")
        expected = ("BASS_MzLS", "9011", False) if self.region == "north" else ("DECaLS", "9012", True)
        if (self.survey, self.generation, self.corrected_9012) != expected:
            raise InputError("CANDIDATE_PROVENANCE")
        if not isinstance(self.brickname, str) or not self.brickname or not self.brickname.isascii():
            raise InputError("BRICKNAME_NOT_ASCII")
        if isinstance(self.brickid, bool) or not isinstance(self.brickid, int):
            raise InputError("CANDIDATE_BRICKID")
        if not 1 <= self.brickid <= 662174:
            raise InputError("CANDIDATE_BRICKID")
        coordinates = (self.ra, self.dec, self.primary_bounds.ra1, self.primary_bounds.ra2,
                       self.primary_bounds.dec1, self.primary_bounds.dec2)
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or
               not math.isfinite(value) for value in coordinates):
            raise InputError("CANDIDATE_GEOMETRY")
        if type(self.grz) is not bool or type(self.survey_primary) is not bool:
            raise InputError("CANDIDATE_BOOLEAN")
        if not self.evidence_refs or any(not isinstance(x, str) or not x for x in self.evidence_refs):
            raise InputError("CANDIDATE_EVIDENCE")
        if self.evidence_refs != tuple(sorted(set(self.evidence_refs))):
            raise InputError("CANDIDATE_EVIDENCE")


@dataclass(frozen=True)
class GrzTechnicalAudit:
    VERSION: ClassVar[str] = GRZ_AUDIT_VERSION
    brickname: str
    nexp_g: int
    nexp_r: int
    nexp_z: int
    nexphist_g: tuple[int, ...]
    nexphist_r: tuple[int, ...]
    nexphist_z: tuple[int, ...]
    grz: bool
    evidence_refs: tuple[str, ...]


def _payload(candidate: TechnicalCandidate) -> dict:
    return {"region": candidate.region, "survey": candidate.survey,
            "release_family": candidate.release_family, "generation": candidate.generation,
            "brickname": candidate.brickname, "brickid": candidate.brickid,
            "ra": candidate.ra, "dec": candidate.dec,
            "primary_bounds": {"ra1": candidate.primary_bounds.ra1,
                               "ra2": candidate.primary_bounds.ra2,
                               "dec1": candidate.primary_bounds.dec1,
                               "dec2": candidate.primary_bounds.dec2},
            "grz": candidate.grz, "corrected_9012": candidate.corrected_9012,
            "survey_primary": candidate.survey_primary,
            "evidence_refs": list(candidate.evidence_refs)}


def candidate_object(candidate: TechnicalCandidate) -> dict:
    if not isinstance(candidate, TechnicalCandidate):
        raise InputError("RAW_PROVIDER_TABLE_FORBIDDEN")
    return {"dto_version": CANDIDATE_DTO_VERSION, "candidate": _payload(candidate)}


def candidate_bytes(candidate: TechnicalCandidate) -> bytes:
    return canonical(candidate_object(candidate)) + b"\n"


def candidate_sha256(candidate: TechnicalCandidate) -> str:
    return digest(candidate_bytes(candidate))


def audit_object(audit: GrzTechnicalAudit) -> dict:
    if not isinstance(audit, GrzTechnicalAudit):
        raise InputError("GRZ_AUDIT_TYPE")
    return {"audit_version": GRZ_AUDIT_VERSION,
            "brickname": audit.brickname, "nexp_g": audit.nexp_g,
            "nexp_r": audit.nexp_r, "nexp_z": audit.nexp_z,
            "nexphist_g": list(audit.nexphist_g), "nexphist_r": list(audit.nexphist_r),
            "nexphist_z": list(audit.nexphist_z), "grz": audit.grz,
            "evidence_refs": list(audit.evidence_refs)}


def _finite_integer(value) -> bool:
    return type(value) is int


def grz_median_present_v1(nexp_g, nexp_r, nexp_z) -> bool:
    values = (nexp_g, nexp_r, nexp_z)
    if not all(_finite_integer(value) for value in values):
        raise InputError("GRZ_NEXP_INVALID")
    return all(value >= 1 for value in values)


class SyntheticPatchMembership:
    """Explicitly synthetic membership provider; cannot represent production evidence."""
    synthetic_only = True

    def __init__(self, names: Iterable[str]):
        values = tuple(names)
        if any(not isinstance(name, str) or not name or not name.isascii() for name in values):
            raise InputError("SYNTHETIC_PATCH_MEMBERSHIP")
        if len(values) != len(set(values)):
            raise InputError("SYNTHETIC_PATCH_DUPLICATE")
        self._names = frozenset(values)

    def contains(self, brickname: str) -> bool:
        return brickname in self._names


class PatchListSchemaAdapter:
    def decode_production(self, *args, **kwargs):
        raise InputError(PATCH_LIST_STATUS)


def _unique_rows(table: AllowedProviderTable, key: FieldId) -> dict:
    out = {}
    for row in table.rows:
        value = row[key]
        if value in out:
            raise InputError("PROVIDER_JOIN_DUPLICATE")
        out[value] = row
    return out


def _tuple6(value) -> tuple[int, ...]:
    if not isinstance(value, tuple) or len(value) != 6 or any(type(x) is not int for x in value):
        raise InputError("GRZ_HIST_INVALID")
    return value


def build_technical_candidates(root: AllowedProviderTable,
                               regional: AllowedProviderTable,
                               identity: ProviderIdentity,
                               patch_membership: SyntheticPatchMembership | None = None
                               ) -> tuple[tuple[TechnicalCandidate, ...], tuple[GrzTechnicalAudit, ...]]:
    if root.role is not ProviderRole.ROOT_GEOMETRY or regional.role is not identity.role:
        raise InputError("PROVIDER_JOIN_ROLE")
    if identity.execution_kind != "SYNTHETIC":
        # Production is additionally blocked by absent physical contracts and patch schema.
        raise InputError("PRODUCTION_PROVIDER_PHYSICAL_CONTRACT_UNAVAILABLE")
    root_rows = _unique_rows(root, FieldId.ROOT_BRICKNAME)
    regional_rows = _unique_rows(regional, FieldId.REG_BRICKNAME)
    candidates = []
    audits = []
    # Resource byte hashes remain in the acquisition receipt.  Candidate/selection
    # evidence binds stable resource identities plus schema contracts so changes
    # confined to forbidden cells cannot perturb any selection artifact.
    evidence = tuple(sorted(set(identity.evidence_refs +
                                (root.contract_sha256, regional.contract_sha256))))
    for brickname in sorted(regional_rows):
        if brickname not in root_rows:
            raise InputError("PROVIDER_JOIN_MISSING_ROOT")
        root_row = root_rows[brickname]
        reg_row = regional_rows[brickname]
        if root_row[FieldId.ROOT_BRICKNAME] != reg_row[FieldId.REG_BRICKNAME]:
            raise InputError("PROVIDER_JOIN_BRICKNAME_CONFLICT")
        if root_row[FieldId.ROOT_BRICKID] != reg_row[FieldId.REG_BRICKID]:
            raise InputError("PROVIDER_JOIN_IDENTITY_CONFLICT")
        geometry = ((FieldId.ROOT_RA, FieldId.REG_RA), (FieldId.ROOT_DEC, FieldId.REG_DEC),
                    (FieldId.ROOT_RA1, FieldId.REG_RA1), (FieldId.ROOT_RA2, FieldId.REG_RA2),
                    (FieldId.ROOT_DEC1, FieldId.REG_DEC1), (FieldId.ROOT_DEC2, FieldId.REG_DEC2))
        if any(root_row[left] != reg_row[right] for left, right in geometry):
            raise InputError("PROVIDER_JOIN_GEOMETRY_CONFLICT")
        grz = grz_median_present_v1(reg_row[FieldId.REG_NEXP_G],
                                    reg_row[FieldId.REG_NEXP_R],
                                    reg_row[FieldId.REG_NEXP_Z])
        audit = GrzTechnicalAudit(
            brickname, reg_row[FieldId.REG_NEXP_G], reg_row[FieldId.REG_NEXP_R],
            reg_row[FieldId.REG_NEXP_Z], _tuple6(reg_row[FieldId.REG_NEXPHIST_G]),
            _tuple6(reg_row[FieldId.REG_NEXPHIST_R]),
            _tuple6(reg_row[FieldId.REG_NEXPHIST_Z]), grz, evidence)
        audits.append(audit)
        if identity.role is ProviderRole.REGIONAL_NORTH:
            generation = "9011"
            corrected = False
        else:
            if patch_membership is None or not isinstance(patch_membership, SyntheticPatchMembership):
                raise InputError(PATCH_LIST_STATUS)
            if not patch_membership.contains(brickname):
                continue
            generation = "9012"
            corrected = True
        candidates.append(TechnicalCandidate(
            identity.region, identity.survey, identity.release_family, generation,
            brickname, root_row[FieldId.ROOT_BRICKID], root_row[FieldId.ROOT_RA],
            root_row[FieldId.ROOT_DEC],
            PrimaryBounds(root_row[FieldId.ROOT_RA1], root_row[FieldId.ROOT_RA2],
                          root_row[FieldId.ROOT_DEC1], root_row[FieldId.ROOT_DEC2]),
            grz, corrected, reg_row[FieldId.REG_SURVEY_PRIMARY], evidence))
    return tuple(candidates), tuple(audits)


def synthetic_candidate_from_legacy(row: dict) -> TechnicalCandidate:
    """Narrow Amendment-002 regression bridge; never used for production provider input."""
    expected = {"region", "brickname", "survey", "release", "generation", "grz",
                "corrected_9012", "primary_bounds", "evidence_refs"}
    if not isinstance(row, dict) or set(row) != expected:
        raise InputError("SYNTHETIC_LEGACY_CANDIDATE_SCHEMA")
    bounds = row["primary_bounds"]
    if not isinstance(bounds, (list, tuple)) or len(bounds) != 4:
        raise InputError("SYNTHETIC_LEGACY_BOUNDS")
    raw_id = hashlib.sha256(row["brickname"].encode("ascii")).digest()[:4]
    brickid = struct.unpack(">I", raw_id)[0] % 662174 + 1
    ra = (bounds[0] + bounds[1]) / 2
    dec = (bounds[2] + bounds[3]) / 2
    return TechnicalCandidate(row["region"], row["survey"], row["release"],
                              row["generation"], row["brickname"], brickid, ra, dec,
                              PrimaryBounds(*bounds), row["grz"], row["corrected_9012"],
                              True, tuple(sorted(set(row["evidence_refs"]))))


def selection_payload(candidate: TechnicalCandidate) -> dict:
    return _payload(candidate)
