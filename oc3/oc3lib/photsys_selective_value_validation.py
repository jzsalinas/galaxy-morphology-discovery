"""Offline selective PHOTSYS authority validation with a closed value firewall."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import gzip
import hashlib
import os
from pathlib import Path
import struct
from typing import Callable, Iterable, Iterator, Sequence

from .core import InputError, canonical, implementation_hash
from .galaxy_eligibility_photsys_authority_probe import (
    PROJECT, file_sha256, load_canonical_json, sealed, sha256_bytes,
    validate_sealed, write_json_immutable,
)
from .metadata_value_semantics import validate_brickname as validate_global_brickname
from .provider_physical_contracts import ROOT_SUMMARY


STAGE_ID = "OC3-GALAXY-ELIGIBILITY-PHOTSYS-SELECTIVE-VALUE-VALIDATION-001"
SCOPE = "PHOTSYS_THREE_FIELD_VALUE_OBSERVATION_ONLY"
SUCCESS = "PHOTSYS_THREE_FIELD_AUTHORITY_VALIDATED"
READY = "READY_AT_REAL_VALUE_OBSERVATION_BOUNDARY"

INPUT_MISMATCH = "PHOTSYS_SELECTIVE_INPUT_MISMATCH_FAILED"
PHYSICAL_MISMATCH = "PHOTSYS_SELECTIVE_PHYSICAL_CONTRACT_MISMATCH_FAILED"
ROW_COUNT_MISMATCH = "PHOTSYS_SELECTIVE_ROW_COUNT_MISMATCH_FAILED"
IDENTITY_DUPLICATE = "PHOTSYS_SELECTIVE_IDENTITY_DUPLICATE_FAILED"
GLOBAL_JOIN_CONFLICT = "PHOTSYS_SELECTIVE_GLOBAL_JOIN_CONFLICT_FAILED"
INVALID_PHOTSYS = "PHOTSYS_SELECTIVE_INVALID_PHOTSYS_FAILED"
AUTHORIZED_VALUE_INVALID = "PHOTSYS_SELECTIVE_AUTHORIZED_VALUE_INVALID_FAILED"
FIREWALL_VIOLATION = "PHOTSYS_SELECTIVE_READER_FIREWALL_VIOLATION_FAILED"
GLOBAL_ACCESS_INCONCLUSIVE = "PHOTSYS_GLOBAL_AUTHORITY_ACCESS_INCONCLUSIVE"
INCONCLUSIVE = "PHOTSYS_SELECTIVE_VALUE_VALIDATION_INCONCLUSIVE"

SPEC_PATH = PROJECT / "OC3_PHOTSYS_SELECTIVE_VALUE_VALIDATION_SPEC.md"
SPEC_SHA256 = "c04d1392e3b7bd0e974c6244201566679dae30d479b9b644c8f3abc1b1a7a119"
PHOTSYS_PATH = PROJECT / (
    "oc3/photsys_authority_full_acquisition/"
    "OC3-GALAXY-ELIGIBILITY-PHOTSYS-AUTHORITY-ACQUISITION-001/"
    "RAW_IMMUTABLE/survey-bricks-dr9-randoms-0.48.0.fits"
)
PHOTSYS_SHA256 = "804d2caf327e808bb4047cc8792a5b08d01d8875149b7b7eb019ce982f6c3f8c"
PHOTSYS_BYTES = 52_323_840
REVIEWED_CONTRACT_PATH = PROJECT / "oc3/INPUTS/OC3_PHOTSYS_AUTHORITY_REVIEWED_PHYSICAL_CONTRACT_001.json"
REVIEWED_CONTRACT_SHA256 = "30b03a47adfc5cb1cc18b8c930dee2fa1d3f04597768558f84602d6ed2aae56f"
ROOT_PATH = PROJECT / (
    "oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001/"
    "RAW_IMMUTABLE/ROOT_SUMMARY/survey-bricks.fits.gz"
)
ROOT_SHA256 = "dc943d702357f93553b9e5d15e87ace38df94eb7095f4100657407b3f9919c5f"
ROOT_BYTES = 13_147_987
ROOT_MANIFEST_PATH = PROJECT / "oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001/BOOTSTRAP_RAW_FILE_MANIFEST.json"
ROOT_MANIFEST_SHA256 = "021c31736ee19af4d137f35404a266140b2aac90349607f58bb0815df719ea2a"
ROOT_INTEGRITY_PATH = PROJECT / "oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001/BOOTSTRAP_INTEGRITY_EVIDENCE.json"
ROOT_INTEGRITY_SHA256 = "460b50eefe6ff71aa94e8c88782565fc0e487fd817e40430c11c14432810607b"
ROOT_SEMANTIC_PATH = PROJECT / "oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001/BOOTSTRAP_SEMANTIC_SUMMARY.json"
ROOT_SEMANTIC_SHA256 = "a0dd0c9bfa684a811c8033ade346d28381d6739a1991840bb23dacd00e7c9a7e"
ACQUISITION_CHECKPOINT_PATH = PHOTSYS_PATH.parents[1] / "OC3_PHOTSYS_FULL_ACQUISITION_CHECKPOINT.json"
ACQUISITION_CHECKPOINT_SHA256 = "289da27a13789682546757f74767d50dcb94c62904d668bb7c4d108758e7c51a"
ACQUISITION_TERMINAL_PATH = PHOTSYS_PATH.parents[1] / "OC3_PHOTSYS_FULL_ACQUISITION_TERMINAL.json"
ACQUISITION_TERMINAL_SHA256 = "a3d2a0cabc8387cffcf2f59efb81393d5aad5a802bfea26716ffa4b9914e830b"
PHYSICAL_CORRECTION_PATH = PROJECT / "OC3_PHOTSYS_PHYSICAL_CONTRACT_CORRECTION_001.json"
PHYSICAL_CORRECTION_SHA256 = "3a7838e89f93b309439470848bcfd932c6e758b003723dbf946de90c3c93c5dc"
PHYSICAL_REVIEW_PATH = PROJECT / "OC3_PHOTSYS_PHYSICAL_PROBE_POST_EXECUTION_REVIEW.md"
PHYSICAL_REVIEW_SHA256 = "9da0020660377e7ef9825b77e0ef465f4018a1716272727ccc578a439e3583cf"
REGION_AMENDMENT_PATH = PROJECT / "OC3_GALAXY_ELIGIBILITY_REGION_RESOLUTION_AMENDMENT_001.md"
REGION_AMENDMENT_SHA256 = "1502bd29cab97170a6fa3c4ccddf07b49966ab65b5e0db206a9b8f010ecfbe65"

CANDIDATE_PATH = PROJECT / "oc3/INPUTS/OC3_PHOTSYS_SELECTIVE_VALUE_VALIDATION_CANDIDATE_001.json"
AUTHORIZATION_PATH = PROJECT / "oc3/OC3_PHOTSYS_SELECTIVE_VALUE_VALIDATION_FINAL_AUTHORIZATION_001.json"
OUTPUT_ROOT = PROJECT / "oc3/photsys_selective_value_validation" / STAGE_ID

PROJECTED_FILENAME = "OC3_PHOTSYS_PROJECTED_AUTHORITY_001.bin"
PROJECTED_SIDECAR = "OC3_PHOTSYS_PROJECTED_AUTHORITY_001.json"


class SelectiveValidationError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class PhotsysLayout:
    data_offset: int
    row_count: int
    row_width: int
    file_size: int

    def validate(self) -> None:
        if (type(self.data_offset) is not int or type(self.row_count) is not int or
                type(self.row_width) is not int or type(self.file_size) is not int or
                min(self.data_offset, self.row_count, self.row_width, self.file_size) < 0 or
                self.row_width != 79 or self.data_offset + self.row_count * self.row_width > self.file_size):
            raise SelectiveValidationError(PHYSICAL_MISMATCH)


PRODUCTION_PHOTSYS_LAYOUT = PhotsysLayout(11520, 662174, 79, PHOTSYS_BYTES)


@dataclass
class ObservationCounters:
    authorized_rows_processed: int = 0
    authorized_BRICKNAME_values_decoded: int = 0
    authorized_BRICKID_values_decoded: int = 0
    authorized_PHOTSYS_values_decoded: int = 0
    global_rows_processed: int = 0
    global_BRICKNAME_values_decoded: int = 0
    global_BRICKID_values_decoded: int = 0
    forbidden_value_decode_count: int = 0
    forbidden_value_materialization_count: int = 0
    forbidden_value_serialization_count: int = 0
    forbidden_value_log_count: int = 0
    whole_row_materialization_count: int = 0
    forbidden_span_access_attempt_count: int = 0
    photsys_exact_span_read_count: int = 0
    global_opaque_bytes_transited: int = 0

    def object(self) -> dict[str, int]:
        return asdict(self)

    def forbidden_clean(self) -> bool:
        return not any((
            self.forbidden_value_decode_count,
            self.forbidden_value_materialization_count,
            self.forbidden_value_serialization_count,
            self.forbidden_value_log_count,
            self.whole_row_materialization_count,
            self.forbidden_span_access_attempt_count,
        ))


@dataclass(frozen=True)
class ProjectedGlobalBrickIdentity:
    brickname_raw: bytes
    brickname: str
    brickid: int

    def __post_init__(self) -> None:
        if (type(self.brickname_raw) is not bytes or len(self.brickname_raw) != 8 or
                type(self.brickname) is not str or type(self.brickid) is not int or
                not -(2**31) <= self.brickid <= 2**31 - 1):
            raise SelectiveValidationError(AUTHORIZED_VALUE_INVALID)

    @property
    def pair(self) -> tuple[bytes, int]:
        return self.brickname_raw, self.brickid


@dataclass(frozen=True)
class ProjectedPhotsysRecord:
    brickname_raw: bytes
    brickname: str
    brickid: int
    photsys_raw: bytes

    def __post_init__(self) -> None:
        if (type(self.brickname_raw) is not bytes or len(self.brickname_raw) != 8 or
                type(self.brickname) is not str or type(self.brickid) is not int or
                not -(2**31) <= self.brickid <= 2**31 - 1 or
                self.photsys_raw not in (b"N", b"S", b" ")):
            raise SelectiveValidationError(AUTHORIZED_VALUE_INVALID)

    @property
    def pair(self) -> tuple[bytes, int]:
        return self.brickname_raw, self.brickid

    def canonical_record(self) -> bytes:
        return self.brickname_raw + struct.pack(">i", self.brickid) + self.photsys_raw


@dataclass(frozen=True)
class RowObservation:
    row_index: int
    record: ProjectedPhotsysRecord | None
    error_codes: tuple[str, ...]
    brickname_valid: bool
    brickid_valid: bool
    photsys_valid: bool
    authorized_identity_sha256: str


def decode_brickname(raw: bytes) -> tuple[bytes, str]:
    if type(raw) is not bytes or len(raw) != 8 or any(value > 0x7f for value in raw):
        raise SelectiveValidationError("BRICKNAME_INVALID")
    canonical_raw = raw.rstrip(b" ")
    if (not canonical_raw or canonical_raw.startswith(b" ") or b" " in canonical_raw or
            b"\x00" in raw):
        raise SelectiveValidationError("BRICKNAME_INVALID")
    try:
        canonical = canonical_raw.decode("ascii", errors="strict")
    except UnicodeDecodeError as exc:
        raise SelectiveValidationError("BRICKNAME_INVALID") from exc
    return raw, canonical


def decode_brickid(raw: bytes) -> int:
    if type(raw) is not bytes or len(raw) != 4:
        raise SelectiveValidationError("BRICKID_INVALID")
    return struct.unpack(">i", raw)[0]


def decode_photsys(raw: bytes) -> bytes:
    if type(raw) is not bytes or len(raw) != 1 or raw not in (b"N", b"S", b" "):
        raise SelectiveValidationError(INVALID_PHOTSYS)
    return raw


def decode_photsys_projection(raw_identity: bytes, raw_photsys: bytes,
                              counters: ObservationCounters) -> ProjectedPhotsysRecord:
    if type(raw_identity) is not bytes or len(raw_identity) != 12:
        raise SelectiveValidationError(AUTHORIZED_VALUE_INVALID)
    counters.authorized_BRICKNAME_values_decoded += 1
    brickname_raw, brickname = decode_brickname(raw_identity[:8])
    counters.authorized_BRICKID_values_decoded += 1
    brickid = decode_brickid(raw_identity[8:12])
    counters.authorized_PHOTSYS_values_decoded += 1
    photsys = decode_photsys(raw_photsys)
    return ProjectedPhotsysRecord(brickname_raw, brickname, brickid, photsys)


def observe_photsys_projection(row_index: int, raw_identity: bytes, raw_photsys: bytes,
                               counters: ObservationCounters) -> RowObservation:
    if type(raw_identity) is not bytes or len(raw_identity) != 12:
        raise SelectiveValidationError(AUTHORIZED_VALUE_INVALID)
    errors: list[str] = []
    brickname_raw = b""; brickname = ""; brickid = 0; photsys = b""
    counters.authorized_BRICKNAME_values_decoded += 1
    try:
        brickname_raw, brickname = decode_brickname(raw_identity[:8])
        # Global semantics remain the authority for admissible canonical names.
        validate_global_brickname(brickname.encode("ascii"))
        brickname_valid = True
    except (SelectiveValidationError, InputError, UnicodeEncodeError):
        brickname_valid = False; errors.append("BRICKNAME_INVALID")
    counters.authorized_BRICKID_values_decoded += 1
    try:
        brickid = decode_brickid(raw_identity[8:12]); brickid_valid = True
    except SelectiveValidationError:
        brickid_valid = False; errors.append("BRICKID_INVALID")
    counters.authorized_PHOTSYS_values_decoded += 1
    try:
        photsys = decode_photsys(raw_photsys); photsys_valid = True
    except SelectiveValidationError:
        photsys_valid = False; errors.append(INVALID_PHOTSYS)
    record = None
    if brickname_valid and brickid_valid and photsys_valid:
        record = ProjectedPhotsysRecord(brickname_raw, brickname, brickid, photsys)
    return RowObservation(
        row_index, record, tuple(errors), brickname_valid, brickid_valid,
        photsys_valid, sha256_bytes(raw_identity),
    )


class ExactSpanPhotsysReader:
    """Closed semantic reader: only two frozen pread spans can reach decoding."""

    __slots__ = ("path", "counters", "layout", "_pread", "_fd", "synthetic_only")
    _ALLOWED_SPANS = frozenset(((0, 12), (70, 1)))

    def __init__(self, path: Path, counters: ObservationCounters, *,
                 layout: PhotsysLayout = PRODUCTION_PHOTSYS_LAYOUT,
                 pread: Callable[[int, int, int], bytes] = os.pread,
                 synthetic_only: bool = False):
        self.path = Path(path); self.counters = counters; self.layout = layout
        self._pread = pread; self._fd: int | None = None; self.synthetic_only = synthetic_only
        layout.validate()
        if not synthetic_only and layout != PRODUCTION_PHOTSYS_LAYOUT:
            raise SelectiveValidationError(PHYSICAL_MISMATCH)

    def boundary_ready(self) -> None:
        if not self.path.is_file():
            raise SelectiveValidationError(INPUT_MISMATCH)
        if not self.synthetic_only and self.path.resolve() != PHOTSYS_PATH.resolve():
            raise SelectiveValidationError(INPUT_MISMATCH)

    def __enter__(self):
        self.boundary_ready(); self._fd = os.open(self.path, os.O_RDONLY)
        return self

    def __exit__(self, *_):
        if self._fd is not None:
            os.close(self._fd); self._fd = None

    def _read_span(self, row_index: int, relative_offset: int, length: int) -> bytes:
        if ((relative_offset, length) not in self._ALLOWED_SPANS or
                type(row_index) is not int or row_index < 0 or row_index >= self.layout.row_count):
            self.counters.forbidden_span_access_attempt_count += 1
            raise SelectiveValidationError(FIREWALL_VIOLATION)
        base = self.layout.data_offset + row_index * self.layout.row_width
        absolute = base + relative_offset
        if (absolute < self.layout.data_offset or length <= 0 or
                absolute + length > self.layout.file_size or
                relative_offset + length > self.layout.row_width):
            self.counters.forbidden_span_access_attempt_count += 1
            raise SelectiveValidationError(FIREWALL_VIOLATION)
        if self._fd is None:
            raise SelectiveValidationError(INCONCLUSIVE)
        body = self._pread(self._fd, length, absolute)
        self.counters.photsys_exact_span_read_count += 1
        if type(body) is not bytes or len(body) != length:
            raise SelectiveValidationError(INPUT_MISMATCH)
        return body

    def read_projected(self, row_index: int) -> RowObservation:
        identity = self._read_span(row_index, 0, 12)
        photsys = self._read_span(row_index, 70, 1)
        self.counters.authorized_rows_processed += 1
        return observe_photsys_projection(row_index, identity, photsys, self.counters)

    def iter_observations(self) -> Iterator[RowObservation]:
        for row_index in range(self.layout.row_count):
            yield self.read_projected(row_index)


def _parse_card_value(raw: str):
    value = raw.split("/", 1)[0].strip()
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].strip()
    if value == "T": return True
    if value == "F": return False
    try: return int(value)
    except ValueError: return value


def _read_header(stream) -> tuple[dict[str, object], int]:
    values: dict[str, object] = {}; consumed = 0
    while True:
        block = stream.read(2880)
        if type(block) is not bytes or len(block) != 2880:
            raise SelectiveValidationError(GLOBAL_ACCESS_INCONCLUSIVE)
        consumed += 2880
        for offset in range(0, 2880, 80):
            card = block[offset:offset + 80]
            try: key = card[:8].decode("ascii", errors="strict").strip()
            except UnicodeDecodeError as exc:
                raise SelectiveValidationError(GLOBAL_ACCESS_INCONCLUSIVE) from exc
            if key == "END":
                return values, consumed
            if card[8:10] == b"= ":
                try: values[key] = _parse_card_value(card[10:80].decode("ascii", errors="strict"))
                except UnicodeDecodeError as exc:
                    raise SelectiveValidationError(GLOBAL_ACCESS_INCONCLUSIVE) from exc


@dataclass(frozen=True)
class RootProjectionLayout:
    row_count: int
    row_width: int
    column_names: tuple[str, ...]
    column_forms: tuple[str, ...]


PRODUCTION_ROOT_LAYOUT = RootProjectionLayout(
    ROOT_SUMMARY.naxis2, ROOT_SUMMARY.naxis1,
    tuple(column.ttype for column in ROOT_SUMMARY.columns),
    tuple(column.tform for column in ROOT_SUMMARY.columns),
)


class RootGzipProjectionAdapter:
    """Stream opaque gzip rows and expose only frozen root identity fields."""

    __slots__ = ("path", "counters", "layout", "synthetic_only", "_gzip_open")

    def __init__(self, path: Path, counters: ObservationCounters, *,
                 layout: RootProjectionLayout = PRODUCTION_ROOT_LAYOUT,
                 synthetic_only: bool = False, gzip_open=gzip.open):
        self.path = Path(path); self.counters = counters; self.layout = layout
        self.synthetic_only = synthetic_only; self._gzip_open = gzip_open
        if (not synthetic_only and layout != PRODUCTION_ROOT_LAYOUT) or layout.row_width != 70:
            raise SelectiveValidationError(PHYSICAL_MISMATCH)

    def boundary_ready(self) -> None:
        if not self.path.is_file():
            raise SelectiveValidationError(INPUT_MISMATCH)
        if not self.synthetic_only and self.path.resolve() != ROOT_PATH.resolve():
            raise SelectiveValidationError(INPUT_MISMATCH)

    def _validate_table_header(self, header: dict[str, object]) -> None:
        if (header.get("XTENSION") != "BINTABLE" or header.get("NAXIS") != 2 or
                header.get("NAXIS1") != self.layout.row_width or
                header.get("NAXIS2") != self.layout.row_count or
                header.get("PCOUNT") != 0 or header.get("GCOUNT") != 1 or
                header.get("TFIELDS") != len(self.layout.column_names) or
                any(key in header for key in ("EXTNAME", "CHECKSUM", "DATASUM"))):
            raise SelectiveValidationError(PHYSICAL_MISMATCH)
        for index, (name, form) in enumerate(zip(
                self.layout.column_names, self.layout.column_forms), 1):
            if (header.get(f"TTYPE{index}") != name or header.get(f"TFORM{index}") != form or
                    any(f"{prefix}{index}" in header for prefix in
                        ("TUNIT", "TNULL", "TSCAL", "TZERO"))):
                raise SelectiveValidationError(PHYSICAL_MISMATCH)

    def iter_identities(self) -> Iterator[ProjectedGlobalBrickIdentity]:
        self.boundary_ready()
        try:
            with self._gzip_open(self.path, "rb") as stream:
                primary, _ = _read_header(stream)
                if primary.get("SIMPLE") is not True or primary.get("NAXIS") != 0:
                    raise SelectiveValidationError(PHYSICAL_MISMATCH)
                table, _ = _read_header(stream); self._validate_table_header(table)
                for _row_index in range(self.layout.row_count):
                    opaque = stream.read(self.layout.row_width)
                    if type(opaque) is not bytes or len(opaque) != self.layout.row_width:
                        raise SelectiveValidationError(GLOBAL_ACCESS_INCONCLUSIVE)
                    self.counters.global_opaque_bytes_transited += len(opaque)
                    projected = opaque[:12]
                    try:
                        name = validate_global_brickname(projected[:8])
                        brickid = decode_brickid(projected[8:12])
                    except Exception as exc:
                        raise SelectiveValidationError(GLOBAL_ACCESS_INCONCLUSIVE) from exc
                    self.counters.global_rows_processed += 1
                    self.counters.global_BRICKNAME_values_decoded += 1
                    self.counters.global_BRICKID_values_decoded += 1
                    yield ProjectedGlobalBrickIdentity(name.raw, name.value, brickid)
        except SelectiveValidationError:
            raise
        except Exception as exc:
            raise SelectiveValidationError(GLOBAL_ACCESS_INCONCLUSIVE) from exc


@dataclass(frozen=True)
class ValidationAggregates:
    terminal: str
    total_rows: int
    valid_BRICKNAME: int
    invalid_BRICKNAME: int
    valid_BRICKID: int
    invalid_BRICKID: int
    valid_PHOTSYS: int
    photsys_N: int
    photsys_S: int
    photsys_space: int
    invalid_PHOTSYS: int
    invalid_authorized_values: int
    duplicate_raw_BRICKNAME: int
    duplicate_canonical_BRICKNAME: int
    duplicate_BRICKID: int
    duplicate_pair: int
    matched: int
    missing_from_PHOTSYS_authority: int
    missing_from_global_authority: int
    BRICKNAME_conflict: int
    BRICKID_conflict: int
    identity_pair_conflict: int
    diagnostic_hashes: tuple[dict[str, object], ...]

    def object(self) -> dict[str, object]:
        value = asdict(self)
        value["diagnostic_hashes"] = list(self.diagnostic_hashes)
        return value


def _diagnostic(row_index: int, reason: str, raw: bytes) -> dict[str, object]:
    return {"row_index": row_index, "reason": reason,
            "authorized_identity_sha256": sha256_bytes(raw)}


def validate_projected_records(observations: Iterable[RowObservation],
                               global_identities: Iterable[ProjectedGlobalBrickIdentity],
                               counters: ObservationCounters,
                               expected_rows: int) -> tuple[ValidationAggregates, tuple[ProjectedPhotsysRecord, ...]]:
    root_by_name: dict[str, int] = {}; root_by_id: dict[int, str] = {}; root_pairs = set()
    root_duplicate = False
    root_total = 0
    diagnostics: list[dict[str, object]] = []
    for identity in global_identities:
        root_total += 1
        canonical_pair = (identity.brickname, identity.brickid)
        if (identity.brickname in root_by_name or identity.brickid in root_by_id or
                canonical_pair in root_pairs):
            root_duplicate = True
            if len(diagnostics) < 16:
                diagnostics.append(_diagnostic(
                    root_total - 1, "GLOBAL_IDENTITY_DUPLICATE",
                    identity.brickname_raw + struct.pack(">i", identity.brickid)))
        root_by_name[identity.brickname] = identity.brickid
        root_by_id[identity.brickid] = identity.brickname
        root_pairs.add(canonical_pair)

    rows: list[ProjectedPhotsysRecord] = []; raw_names: set[bytes] = set()
    names: set[str] = set(); ids: set[int] = set(); pairs = set()
    duplicate_raw_name = duplicate_name = duplicate_id = duplicate_pair = invalid_photsys = 0
    n_count = s_count = space_count = 0
    total = valid_name = invalid_name = valid_id = invalid_id = valid_photsys = 0
    for observation in observations:
        total += 1
        valid_name += int(observation.brickname_valid)
        invalid_name += int(not observation.brickname_valid)
        valid_id += int(observation.brickid_valid)
        invalid_id += int(not observation.brickid_valid)
        valid_photsys += int(observation.photsys_valid)
        invalid_photsys += int(not observation.photsys_valid)
        if observation.record is None:
            if len(diagnostics) < 16:
                diagnostics.append(_diagnostic(observation.row_index,
                                               "+".join(observation.error_codes) or INCONCLUSIVE,
                                               bytes.fromhex(observation.authorized_identity_sha256)))
            continue
        record = observation.record; rows.append(record)
        if record.photsys_raw == b"N": n_count += 1
        elif record.photsys_raw == b"S": s_count += 1
        else: space_count += 1
        reasons = []
        if record.brickname_raw in raw_names:
            duplicate_raw_name += 1; reasons.append("DUPLICATE_RAW_BRICKNAME")
        if record.brickname in names:
            duplicate_name += 1; reasons.append("DUPLICATE_CANONICAL_BRICKNAME")
        if record.brickid in ids:
            duplicate_id += 1; reasons.append("DUPLICATE_BRICKID")
        canonical_pair = (record.brickname, record.brickid)
        if canonical_pair in pairs:
            duplicate_pair += 1; reasons.append("DUPLICATE_IDENTITY_PAIR")
        if reasons and len(diagnostics) < 16:
            diagnostics.append(_diagnostic(
                observation.row_index, "+".join(reasons),
                record.brickname_raw + struct.pack(">i", record.brickid)))
        raw_names.add(record.brickname_raw); names.add(record.brickname)
        ids.add(record.brickid); pairs.add(canonical_pair)

    matched = missing_global = name_conflict = id_conflict = pair_conflict = 0
    for row_index, record in enumerate(rows):
        canonical_pair = (record.brickname, record.brickid)
        if canonical_pair in root_pairs:
            matched += 1; continue
        name_present = record.brickname in root_by_name
        id_present = record.brickid in root_by_id
        if not name_present and not id_present:
            missing_global += 1
            reason = "MISSING_FROM_GLOBAL_AUTHORITY"
        elif name_present and id_present:
            pair_conflict += 1
            reason = "IDENTITY_PAIR_CONFLICT"
        elif name_present:
            id_conflict += 1
            reason = "BRICKID_CONFLICT"
        else:
            name_conflict += 1
            reason = "BRICKNAME_CONFLICT"
        if len(diagnostics) < 16:
            diagnostics.append(_diagnostic(
                row_index, reason,
                record.brickname_raw + struct.pack(">i", record.brickid)))
    missing_photsys = len(root_pairs - pairs)
    if missing_photsys and len(diagnostics) < 16:
        for name, brickid in sorted(root_pairs - pairs):
            diagnostics.append(_diagnostic(
                -1, "MISSING_FROM_PHOTSYS_AUTHORITY",
                name.encode("ascii") + struct.pack(">i", brickid)))
            if len(diagnostics) == 16:
                break

    if not counters.forbidden_clean(): terminal = FIREWALL_VIOLATION
    elif (total != expected_rows or root_total != expected_rows or
          counters.authorized_rows_processed != expected_rows or
          counters.authorized_BRICKNAME_values_decoded != expected_rows or
          counters.authorized_BRICKID_values_decoded != expected_rows or
          counters.authorized_PHOTSYS_values_decoded != expected_rows or
          counters.global_rows_processed != expected_rows or
          counters.global_BRICKNAME_values_decoded != expected_rows or
          counters.global_BRICKID_values_decoded != expected_rows): terminal = ROW_COUNT_MISMATCH
    elif invalid_photsys: terminal = INVALID_PHOTSYS
    elif invalid_name or invalid_id: terminal = AUTHORIZED_VALUE_INVALID
    elif (root_duplicate or duplicate_raw_name or duplicate_name or duplicate_id or
          duplicate_pair): terminal = IDENTITY_DUPLICATE
    elif any((missing_photsys, missing_global, name_conflict, id_conflict, pair_conflict)): terminal = GLOBAL_JOIN_CONFLICT
    else: terminal = SUCCESS
    aggregates = ValidationAggregates(
        terminal, total, valid_name, invalid_name, valid_id, invalid_id, valid_photsys,
        n_count, s_count, space_count, invalid_photsys, invalid_name + invalid_id,
        duplicate_raw_name, duplicate_name, duplicate_id, duplicate_pair, matched, missing_photsys,
        missing_global, name_conflict, id_conflict, pair_conflict,
        tuple(diagnostics),
    )
    return aggregates, tuple(rows)


def canonical_resolver_bytes(records: Sequence[ProjectedPhotsysRecord]) -> bytes:
    ordered = sorted(records, key=lambda row: (row.brickname_raw, row.brickid))
    return b"".join(row.canonical_record() for row in ordered)


def validate_file_binding(path: Path, expected_sha256: str, expected_bytes: int,
                          expected_mode: int | None = None) -> None:
    path = Path(path)
    if (not path.is_file() or path.stat().st_size != expected_bytes or
            file_sha256(path) != expected_sha256 or
            (expected_mode is not None and path.stat().st_mode & 0o777 != expected_mode)):
        raise SelectiveValidationError(INPUT_MISMATCH)


def publish_resolver(records: Sequence[ProjectedPhotsysRecord], output_directory: Path,
                     source_bindings: dict[str, object], implementation_aggregate: str) -> dict[str, object]:
    body = canonical_resolver_bytes(records)
    if len(body) != len(records) * 13:
        raise SelectiveValidationError(INCONCLUSIVE)
    output = Path(output_directory); binary = output / PROJECTED_FILENAME
    sidecar_path = output / PROJECTED_SIDECAR
    digest = sha256_bytes(body)
    sidecar = sealed({
        "binary_filename": PROJECTED_FILENAME,
        "binary_sha256": digest,
        "implementation_aggregate": implementation_aggregate,
        "order": "ASCENDING_RAW_BRICKNAME_THEN_SIGNED_BRICKID",
        "record_count": len(records),
        "record_schema": [
            {"field": "BRICKNAME", "offset": 0, "width": 8, "encoding": "RAW_ASCII"},
            {"field": "BRICKID", "offset": 8, "width": 4, "encoding": "SIGNED_BIG_ENDIAN_INT32"},
            {"field": "PHOTSYS", "offset": 12, "width": 1, "encoding": "RAW_ASCII_BYTE"},
        ],
        "record_width": 13,
        "source_bindings": source_bindings,
        "stage_id": STAGE_ID,
    })
    output.mkdir(parents=True, exist_ok=True)
    binary_partial = binary.with_name(binary.name + ".partial")
    sidecar_partial = sidecar_path.with_name(sidecar_path.name + ".partial")
    if any(path.exists() for path in
           (binary, sidecar_path, binary_partial, sidecar_partial)):
        raise SelectiveValidationError(INCONCLUSIVE)
    try:
        with binary_partial.open("xb") as stream:
            stream.write(body); stream.flush(); os.fsync(stream.fileno())
        with sidecar_partial.open("xb") as stream:
            stream.write(canonical(sidecar) + b"\n"); stream.flush(); os.fsync(stream.fileno())
        os.chmod(binary_partial, 0o444); os.chmod(sidecar_partial, 0o444)
        # Publish metadata first.  A crash before the second rename cannot expose
        # a row-level resolver without its sidecar.
        os.replace(sidecar_partial, sidecar_path)
        os.replace(binary_partial, binary)
    except BaseException:
        for path in (binary_partial, sidecar_partial, binary, sidecar_path):
            try: path.unlink()
            except FileNotFoundError: pass
        raise
    return sidecar


def publish_success_resolver(aggregates: ValidationAggregates,
                             records: Sequence[ProjectedPhotsysRecord],
                             output_directory: Path, source_bindings: dict[str, object],
                             implementation_aggregate: str) -> dict[str, object]:
    if aggregates.terminal != SUCCESS:
        raise SelectiveValidationError(INCONCLUSIVE)
    if (len(records) != aggregates.total_rows or
            len(records) != aggregates.matched or
            len(records) != aggregates.valid_BRICKNAME or
            len(records) != aggregates.valid_BRICKID or
            len(records) != aggregates.valid_PHOTSYS):
        raise SelectiveValidationError(INCONCLUSIVE)
    return publish_resolver(records, output_directory, source_bindings,
                            implementation_aggregate)


def validate_real_inputs() -> dict[str, object]:
    expected_files = {
        SPEC_PATH: SPEC_SHA256, PHOTSYS_PATH: PHOTSYS_SHA256,
        REVIEWED_CONTRACT_PATH: REVIEWED_CONTRACT_SHA256, ROOT_PATH: ROOT_SHA256,
        ROOT_MANIFEST_PATH: ROOT_MANIFEST_SHA256, ROOT_INTEGRITY_PATH: ROOT_INTEGRITY_SHA256,
        ROOT_SEMANTIC_PATH: ROOT_SEMANTIC_SHA256,
        ACQUISITION_CHECKPOINT_PATH: ACQUISITION_CHECKPOINT_SHA256,
        ACQUISITION_TERMINAL_PATH: ACQUISITION_TERMINAL_SHA256,
        PHYSICAL_CORRECTION_PATH: PHYSICAL_CORRECTION_SHA256,
        PHYSICAL_REVIEW_PATH: PHYSICAL_REVIEW_SHA256,
        REGION_AMENDMENT_PATH: REGION_AMENDMENT_SHA256,
    }
    for path, expected in expected_files.items():
        if not path.is_file() or file_sha256(path) != expected:
            raise SelectiveValidationError(INPUT_MISMATCH)
    validate_file_binding(PHOTSYS_PATH, PHOTSYS_SHA256, PHOTSYS_BYTES, 0o444)
    validate_file_binding(ROOT_PATH, ROOT_SHA256, ROOT_BYTES, 0o444)
    reviewed = validate_sealed(load_canonical_json(REVIEWED_CONTRACT_PATH))
    checkpoint = validate_sealed(load_canonical_json(ACQUISITION_CHECKPOINT_PATH))
    terminal = validate_sealed(load_canonical_json(ACQUISITION_TERMINAL_PATH))
    if (reviewed.get("review_state") != "PHOTSYS_AUTHORITY_PHYSICAL_CONTRACT_REVIEWED" or
            reviewed.get("file_size") != PHOTSYS_BYTES or
            reviewed.get("first_table_data_byte") != 11520 or
            reviewed.get("physical_contract", {}).get("row_count") != 662174 or
            reviewed.get("physical_contract", {}).get("row_width") != 79 or
            checkpoint.get("evidence", {}).get("sha256") != PHOTSYS_SHA256 or
            terminal.get("state") != "PHOTSYS_FULL_FILE_BYTES_ACQUIRED" or
            terminal.get("table_cell_values_decoded") != 0):
        raise SelectiveValidationError(PHYSICAL_MISMATCH)
    manifest = load_canonical_json(ROOT_MANIFEST_PATH)
    integrity = load_canonical_json(ROOT_INTEGRITY_PATH)
    semantic = load_canonical_json(ROOT_SEMANTIC_PATH)
    roots = [row for row in manifest.get("resources", []) if row.get("role") == "ROOT_SUMMARY"]
    if (len(roots) != 1 or roots[0].get("raw_sha256") != ROOT_SHA256 or
            integrity.get("input_raw_sha256", {}).get("ROOT_SUMMARY") != ROOT_SHA256 or
            semantic.get("roles", {}).get("ROOT_SUMMARY", {}).get("valid_rows") != 662174 or
            semantic.get("forbidden_values_observed") is not False):
        raise SelectiveValidationError(INPUT_MISMATCH)
    counters = ObservationCounters()
    return {
        "authorized_values_decoded": 0,
        "counters": counters.object(),
        "network_requests": 0,
        "root_authority_sha256": ROOT_SHA256,
        "stage_id": STAGE_ID,
        "state": "PHOTSYS_SELECTIVE_INPUTS_VALIDATED",
    }


def dry_run() -> dict[str, object]:
    validate_real_inputs(); counters = ObservationCounters()
    ExactSpanPhotsysReader(PHOTSYS_PATH, counters).boundary_ready()
    RootGzipProjectionAdapter(ROOT_PATH, counters).boundary_ready()
    return {
        "authorized_values_decoded": 0,
        "counters": counters.object(),
        "network_requests": 0,
        "stage_id": STAGE_ID,
        "state": READY,
    }


def exact_command(project: Path = PROJECT) -> list[str]:
    project = Path(project).resolve()
    return [
        str(project / "oc3/.venv/bin/python"),
        str(project / "oc3/oc3_photsys_selective_value_validation.py"),
        "--validate-photsys-authority", "--execute-real-value-observation",
        "--candidate", str(project / CANDIDATE_PATH.relative_to(PROJECT)),
        "--authorization", str(project / AUTHORIZATION_PATH.relative_to(PROJECT)),
        "--output-directory", str(project / OUTPUT_ROOT.relative_to(PROJECT)),
    ]


def build_candidate(implementation_aggregate: str) -> dict[str, object]:
    validate_real_inputs()
    command = exact_command()
    return sealed({
        "authorized_fields": ["BRICKNAME", "BRICKID", "PHOTSYS"],
        "candidate_state": "PENDING_HUMAN_REVIEW",
        "command_argv": command,
        "command_argv_sha256": sha256_bytes(canonical(command)),
        "execution": {"network": False, "offline_only": True,
                      "real_value_observation": "REQUIRES_SEPARATE_FINAL_AUTHORIZATION"},
        "failure_states": [INPUT_MISMATCH, PHYSICAL_MISMATCH, ROW_COUNT_MISMATCH,
                           IDENTITY_DUPLICATE, GLOBAL_JOIN_CONFLICT, INVALID_PHOTSYS,
                           AUTHORIZED_VALUE_INVALID, FIREWALL_VIOLATION,
                           GLOBAL_ACCESS_INCONCLUSIVE, INCONCLUSIVE],
        "final_authorization_path": str(AUTHORIZATION_PATH),
        "final_authorization_present": False,
        "firewall": {"forbidden_counters_required": 0,
                     "whole_row_materialization_required": 0,
                     "whole_row_fallback": False},
        "implementation_aggregate": implementation_aggregate,
        "inputs": {
            "photsys": {"path": str(PHOTSYS_PATH), "sha256": PHOTSYS_SHA256,
                        "size": PHOTSYS_BYTES},
            "acquisition_checkpoint": {"path": str(ACQUISITION_CHECKPOINT_PATH),
                                       "sha256": ACQUISITION_CHECKPOINT_SHA256},
            "acquisition_terminal": {"path": str(ACQUISITION_TERMINAL_PATH),
                                     "sha256": ACQUISITION_TERMINAL_SHA256},
            "physical_contract": {"path": str(REVIEWED_CONTRACT_PATH),
                                  "sha256": REVIEWED_CONTRACT_SHA256},
            "physical_correction": {"path": str(PHYSICAL_CORRECTION_PATH),
                                    "sha256": PHYSICAL_CORRECTION_SHA256},
            "physical_review": {"path": str(PHYSICAL_REVIEW_PATH),
                                "sha256": PHYSICAL_REVIEW_SHA256},
            "root_authority": {"path": str(ROOT_PATH), "sha256": ROOT_SHA256,
                               "physical_contract_sha256": ROOT_SUMMARY.sha256,
                               "manifest_sha256": ROOT_MANIFEST_SHA256,
                               "integrity_sha256": ROOT_INTEGRITY_SHA256,
                               "semantic_summary_sha256": ROOT_SEMANTIC_SHA256,
                               "governing_amendment_sha256": REGION_AMENDMENT_SHA256},
        },
        "output_boundary": {"projected_filename": PROJECTED_FILENAME,
                            "record_width": 13, "success_only": True},
        "photsys_spans": [{"offset": 0, "length": 12}, {"offset": 70, "length": 1}],
        "restart_boundary": {"automatic_resume": False,
                             "separate_review_and_authorization_required": True},
        "root_projection": {"fields": ["BRICKNAME", "BRICKID"],
                            "frozen_contract": ROOT_SUMMARY.object()},
        "schema_version": "OC3_PHOTSYS_SELECTIVE_VALUE_VALIDATION_CANDIDATE_001",
        "scope": SCOPE,
        "specification": {"path": str(SPEC_PATH.relative_to(PROJECT)),
                          "sha256": SPEC_SHA256},
        "stage_id": STAGE_ID,
        "success_criteria": {"row_count": 662174, "invalid_values": 0,
                             "duplicates": 0, "join_conflicts": 0,
                             "forbidden_observations": 0,
                             "terminal": SUCCESS},
    })


def validate_candidate(path: Path = CANDIDATE_PATH, *, require_authorization_absent=True) -> dict[str, object]:
    candidate = validate_sealed(load_canonical_json(path))
    if candidate != build_candidate(implementation_hash(PROJECT)):
        raise SelectiveValidationError(INPUT_MISMATCH)
    if require_authorization_absent and AUTHORIZATION_PATH.exists():
        raise SelectiveValidationError(INCONCLUSIVE)
    return candidate


def validate_authorization(path: Path, candidate_path: Path,
                           command_argv_sha256: str) -> dict[str, object]:
    value = validate_sealed(load_canonical_json(path))
    allowed = {"authorization_id", "authorization_state", "authorized",
               "candidate_sha256", "command_argv_sha256", "resume", "scope",
               "sealed", "stage_id"}
    if (set(value) != allowed or value.get("authorization_state") != "FINAL_HUMAN_AUTHORIZATION" or
            value.get("authorized") is not True or value.get("resume") is not False or
            value.get("scope") != SCOPE or value.get("stage_id") != STAGE_ID or
            value.get("candidate_sha256") != file_sha256(candidate_path) or
            value.get("command_argv_sha256") != command_argv_sha256):
        raise SelectiveValidationError(INCONCLUSIVE)
    return value


def _replace_json(path: Path, value: dict[str, object]) -> None:
    data = canonical(value) + b"\n"; path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".partial")
    with temporary.open("wb") as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)


def _append_log(path: Path, value: dict[str, object]) -> None:
    with path.open("ab") as stream:
        stream.write(canonical(value) + b"\n"); stream.flush(); os.fsync(stream.fileno())


def run_real_validation(candidate_path: Path, authorization_path: Path,
                        command_argv_sha256: str, output_directory: Path) -> dict[str, object]:
    candidate = validate_candidate(candidate_path, require_authorization_absent=False)
    validate_authorization(authorization_path, candidate_path, command_argv_sha256)
    output = Path(output_directory).resolve()
    if output != OUTPUT_ROOT.resolve() or output.exists():
        raise SelectiveValidationError(INCONCLUSIVE)
    output.mkdir(parents=True)
    counters = ObservationCounters()
    input_binding = sealed({"candidate_sha256": file_sha256(candidate_path),
                            "implementation_aggregate": implementation_hash(PROJECT),
                            "photsys_sha256": PHOTSYS_SHA256, "root_sha256": ROOT_SHA256,
                            "stage_id": STAGE_ID})
    write_json_immutable(output / "INPUT_BINDING.json", input_binding)
    terminal_state = INCONCLUSIVE; aggregates = None
    projected_authority_sha256 = None
    progress_path = output / "PROGRESS.json"
    log_path = output / "RUN.log"
    def persist_progress(phase: str) -> None:
        progress = sealed({
            "counters": counters.object(), "phase": phase, "stage_id": STAGE_ID,
        })
        _replace_json(progress_path, progress)
        _append_log(log_path, progress)
    def tracked_global(adapter: RootGzipProjectionAdapter):
        for identity in adapter.iter_identities():
            if counters.global_rows_processed % 10_000 == 0:
                persist_progress("GLOBAL_AUTHORITY_PROJECTION")
            yield identity
    def tracked_photsys(reader: ExactSpanPhotsysReader):
        for observation in reader.iter_observations():
            if counters.authorized_rows_processed % 10_000 == 0:
                persist_progress("PHOTSYS_SELECTIVE_OBSERVATION")
            yield observation
    try:
        persist_progress("INPUTS_BOUND")
        root_adapter = RootGzipProjectionAdapter(ROOT_PATH, counters)
        with ExactSpanPhotsysReader(PHOTSYS_PATH, counters) as reader:
            aggregates, records = validate_projected_records(
                tracked_photsys(reader), tracked_global(root_adapter), counters, 662174)
        terminal_state = aggregates.terminal
        persist_progress("VALIDATION_COMPLETE")
        _replace_json(output / "OBSERVABILITY.json", sealed({
            "counters": counters.object(), "stage_id": STAGE_ID}))
        _replace_json(output / "VALIDATION_AGGREGATES.json", sealed({
            "aggregates": aggregates.object(), "stage_id": STAGE_ID}))
        if terminal_state == SUCCESS:
            sidecar = publish_success_resolver(
                aggregates, records, output, candidate["inputs"],
                implementation_hash(PROJECT))
            projected_authority_sha256 = sidecar["binary_sha256"]
    except SelectiveValidationError as exc:
        terminal_state = exc.code if exc.code in candidate["failure_states"] else INCONCLUSIVE
    except BaseException:
        terminal_state = INCONCLUSIVE
        raise
    finally:
        if not (output / "OBSERVABILITY.json").exists():
            _replace_json(output / "OBSERVABILITY.json", sealed({
                "counters": counters.object(), "stage_id": STAGE_ID}))
        terminal = sealed({
            "authorized_rows_processed": counters.authorized_rows_processed,
            "counters": counters.object(),
            "forbidden_counters_zero": counters.forbidden_clean(),
            "network_requests": 0,
            "projected_authority_sha256": projected_authority_sha256,
            "projected_authority_published": (output / PROJECTED_FILENAME).exists(),
            "stage_id": STAGE_ID, "state": terminal_state,
        })
        _replace_json(output / "TERMINAL.json", terminal)
        _append_log(log_path, terminal)
    return terminal
