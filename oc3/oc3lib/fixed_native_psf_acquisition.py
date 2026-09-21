"""Closed acquisition plan for twelve native products and eighteen PSF responses.

Candidate construction and validation are offline.  Network capability exists only
behind the acquisition entry point and a separately created final authorization.
No extraction, resampling, homogenization, preprocessing, or morphology path exists.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil

from .core import canonical, file_hash, implementation_hash
from .fixed_native_contract import inspect_header
from .coadd_psf_contract import LiteralPSFTransport, inspect_response
from .resource_contract import LiteralHTTPTransport


STAGE_ID = "OC3-FIXED-NATIVE-PSF-ACQUISITION-001"
SUCCESS = "BOUNDED_NATIVE_PRODUCTS_ACQUIRED"
PARTIAL = "BOUNDED_NATIVE_PRODUCTS_ACQUISITION_PARTIAL"
CANDIDATE_READY = "FIXED_NATIVE_PSF_ACQUISITION_CANDIDATE_VALID_FOR_HUMAN_REVIEW"

SELECTION_SHA256 = "2e6f2cb070a363e9e3dbdb1f25670590c33500a293bb926d8ff94657a2ff8860"
LOCATIONS_RELATIVE = Path("oc3/TECHNICAL_INDEX/OC3_LOCATIONS.json")
LOCATIONS_SHA256 = "33d593638c074a3ff59d32d3e4c38558e8912377ea15818ca5072087007c97d1"
LOCATION_TERMINAL_RELATIVE = Path(
    "oc3/location_selection/OC3-OFFLINE-LOCATION-SELECTION-001/LOCATION_SELECTION_TERMINAL.json")
FIXED_CONTRACT_RELATIVE = Path(
    "oc3/fixed_native_resource_contract/OC3-FIXED-NATIVE-RESOURCE-PROBE-001/"
    "FIXED_NATIVE_RESOURCE_CONTRACT_RESOLVED.json")
FIXED_CONTRACT_SHA256 = "8e8ac029aa61e82b2a089205aff4781123700a30ce24353dd95e5eaedd55befc"
FIXED_CHECKPOINTS_RELATIVE = Path(
    "oc3/fixed_native_resource_contract/OC3-FIXED-NATIVE-RESOURCE-PROBE-001/RESOURCE_CHECKPOINTS")
PSF_CONTRACT_RELATIVE = Path(
    "oc3/coadd_psf_contract_probe/OC3-COADD-PSF-CONTRACT-PROBE-001/"
    "COADD_PSF_RESOURCE_CONTRACT_RESOLVED.json")
PSF_CONTRACT_SHA256 = "8f7ba5c0f50f26f240ff08ece3a8e0afef62559cb35f4947423136a05904bf30"
PSF_BASE_RELATIVE = Path("oc3/INPUTS/OC3_PSF_RESOURCE_CONTRACT_001.json")
PSF_BASE_SHA256 = "1720e8ae9b77f4d5b7de9b7d28a2dbf3d1785c7005e2507e9a9ba21467dbc9f7"
PSF_IDENTITIES_RELATIVE = Path("oc3/TECHNICAL_INDEX/OC3_PSF_IDENTITIES.json")
PSF_IDENTITIES_SHA256 = "8c8ec5a14169154fce82f6b7a6de147d08e749ba5b410974fd920411b8fe9036"
CANDIDATE_RELATIVE = Path("oc3/INPUTS/OC3_FIXED_NATIVE_PSF_ACQUISITION_CANDIDATE_001.json")
AUTHORIZATION_RELATIVE = Path("oc3/INPUTS/OC3_FIXED_NATIVE_PSF_ACQUISITION_AUTHORIZATION_001.json")
AUDIT_RELATIVE = Path("oc3/fixed_native_psf_acquisition/OC3-FIXED-NATIVE-PSF-ACQUISITION-001")

START_REQUESTS = 280
START_BODY_BYTES = 93_968_846
GLOBAL_BODY_CAP = 1_610_612_736
FIXED_RESOURCE_COUNT = 12
FIXED_BODY_BYTES = 144_766_080
PSF_TRANSPORT_COUNT = 18
PSF_IDENTITY_COUNT = 54
PSF_PER_RESPONSE_CAP = 3 * 2**20
PSF_TOTAL_RESERVATION = 54 * 2**20
TOTAL_BODY_RESERVATION = FIXED_BODY_BYTES + PSF_TOTAL_RESERVATION
FIXED_HEAD_REQUESTS = 12
FIXED_GET_REQUESTS = 12
PSF_HEAD_REQUESTS = 0
PSF_GET_REQUESTS = 18
PRIMARY_REQUESTS = 42
RETRY_POOL = 6
STAGE_REQUEST_CAP = PRIMARY_REQUESTS + RETRY_POOL
CONCURRENCY = 1
RETRIES_AUTOMATIC = 0
BANDS = ("g", "r", "z")
SLOTS = ("S1", "S2", "S3", "N1", "N2", "N3")
PSF_POINTS = ("P0", "P1", "P2")
EXPECTED_PSF_SHAPES = {
    "south": {"g": [63, 63], "r": [63, 63], "z": [63, 63]},
    "north": {"g": [31, 31], "r": [31, 31], "z": [63, 63]},
}


class NativePSFAcquisitionError(Exception):
    def __init__(self, code: str, resource_id: str | None = None):
        self.code = code
        self.resource_id = resource_id
        super().__init__(code)


class ClosedAcquisitionTransport:
    """Route static native files and query-bearing PSF URLs without rewriting either."""

    def __init__(self, fixed_urls: list[str], psf_urls: list[str]):
        self.fixed_urls = frozenset(fixed_urls)
        self.psf_urls = frozenset(psf_urls)
        if (not self.fixed_urls or not self.psf_urls or
                self.fixed_urls & self.psf_urls):
            raise NativePSFAcquisitionError("TRANSPORT_URL_PARTITION_INVALID")
        self._fixed = LiteralHTTPTransport(self.fixed_urls)
        self._psf = LiteralPSFTransport(list(self.psf_urls))

    @property
    def requests_started(self) -> int:
        return self._fixed.requests_started + self._psf.requests_started

    @property
    def body_bytes_observed(self) -> int:
        return self._fixed.body_bytes_observed + self._psf.body_bytes_observed

    def head(self, url: str):
        if url not in self.fixed_urls:
            raise NativePSFAcquisitionError("HEAD_URL_NOT_IN_FIXED_INVENTORY")
        return self._fixed.head(url)

    def get(self, url: str, max_bytes: int):
        if url in self.fixed_urls:
            return self._fixed.get(url, max_bytes)
        if url in self.psf_urls:
            response = self._psf.get(url, max_bytes)
            if len(response[2]) > max_bytes:
                raise NativePSFAcquisitionError("HTTP_BODY_EXCEEDS_BOUND")
            return response
        raise NativePSFAcquisitionError("GET_URL_NOT_IN_REVIEWED_INVENTORY")


def _seal(value: dict) -> dict:
    body = dict(value)
    body.pop("sealed", None)
    body["sealed"] = hashlib.sha256(canonical(body)).hexdigest()
    return body


def _verify_seal(value: dict) -> None:
    if not isinstance(value, dict) or _seal(value).get("sealed") != value.get("sealed"):
        raise NativePSFAcquisitionError("SEAL_INVALID")


def _canonical_load(path: Path) -> dict:
    try:
        raw = Path(path).read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise NativePSFAcquisitionError("CANONICAL_INPUT_INVALID") from exc
    if not isinstance(value, dict) or raw != canonical(value) + b"\n":
        raise NativePSFAcquisitionError("CANONICAL_INPUT_INVALID")
    return value


def _immutable_json(path: Path, value: dict) -> str:
    data = canonical(value) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise NativePSFAcquisitionError("IMMUTABLE_ARTIFACT_CONFLICT")
    else:
        with path.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    return hashlib.sha256(data).hexdigest()


def _atomic_json(path: Path, value: dict) -> None:
    data = canonical(value) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _required_inputs(project: Path) -> dict[str, dict]:
    project = Path(project).resolve()
    exact = {
        "locations": (LOCATIONS_RELATIVE, LOCATIONS_SHA256),
        "fixed": (FIXED_CONTRACT_RELATIVE, FIXED_CONTRACT_SHA256),
        "psf": (PSF_CONTRACT_RELATIVE, PSF_CONTRACT_SHA256),
        "psf_base": (PSF_BASE_RELATIVE, PSF_BASE_SHA256),
        "identities": (PSF_IDENTITIES_RELATIVE, PSF_IDENTITIES_SHA256),
    }
    result = {}
    for name, (relative, digest) in exact.items():
        path = project / relative
        if not path.is_file() or file_hash(path) != digest:
            raise NativePSFAcquisitionError("FROZEN_INPUT_HASH_MISMATCH")
        result[name] = _canonical_load(path)
    terminal = _canonical_load(project / LOCATION_TERMINAL_RELATIVE)
    if (result["locations"].get("selection_sha256") != SELECTION_SHA256 or
            terminal.get("state") != "LOCATION_SELECTION_VALIDATED" or
            terminal.get("selection_sha256") != SELECTION_SHA256):
        raise NativePSFAcquisitionError("LOCATION_SELECTION_AUTHORITY_INVALID")
    psf = result["psf"]
    mapping = psf.get("provider_contract", {}).get("band_mapping", {}).get("value", {})
    if (mapping.get("decision") != "A_ONE_RESPONSE_BUNDLES_G_R_Z" or
            mapping.get("future_http_response_count") != 18 or
            mapping.get("same_schema_north_south") is not False or
            psf.get("counts") != {"future_http_responses": 18,
                                  "observational_identities": 54,
                                  "representative_probe_requests": 2,
                                  "spatial_points": 18}):
        raise NativePSFAcquisitionError("PSF_RESOLVED_CONTRACT_INVALID")
    return result


def _fixed_rows(project: Path, inputs: dict[str, dict]) -> list[dict]:
    rows = []
    for resource in inputs["fixed"]["resources"]:
        fields = resource["fields"]
        rid = resource["resource_id"]
        checkpoint_path = project / FIXED_CHECKPOINTS_RELATIVE / f"{rid}.json"
        checkpoint = _canonical_load(checkpoint_path)
        expected = {
            "logical_hdu": fields["logical_hdu"]["value"],
            "physical_image_hdu": fields["physical_image_hdu"]["value"],
            "compression_mapping": fields["compression_mapping"]["value"],
            "shape": fields["expected_shape"]["value"],
            "dtype": fields["dtype"]["value"],
            "observed_bunit": checkpoint["observed_bunit"],
            "observed_imtype": checkpoint["observed_imtype"],
            "wcs": checkpoint["wcs"],
        }
        rows.append({
            "resource_id": rid, "kind": "fixed_native",
            "region": fields["region"]["value"], "brick": fields["brick"]["value"],
            "product": fields["product"]["value"], "band": fields["band"]["value"],
            "literal_url": fields["literal_url"]["value"],
            "filename": fields["filename"]["value"],
            "expected_content_length": fields["content_length"]["value"],
            "expected_etag": fields["etag"]["value"],
            "expected_structure": expected,
            "documented_units": fields["documented_units"]["value"],
            "expected_logical_role": fields["expected_logical_role"]["value"],
            "contract_evidence": {"resolved_contract_sha256": FIXED_CONTRACT_SHA256,
                                  "checkpoint_sha256": file_hash(checkpoint_path)},
        })
    expected_order = [(region, product, band) for region in ("south", "north")
                      for product in ("image", "invvar") for band in BANDS]
    if (len(rows) != 12 or
            [(r["region"], r["product"], r["band"]) for r in rows] != expected_order or
            sum(r["expected_content_length"] for r in rows) != FIXED_BODY_BYTES):
        raise NativePSFAcquisitionError("FIXED_RESOURCE_INVENTORY_INVALID")
    return rows


def _psf_rows(inputs: dict[str, dict]) -> list[dict]:
    points = {(row["slot"], row["point_id"]): row
              for row in inputs["psf_base"]["spatial_points"]}
    identities = inputs["identities"]["identities"]
    identities_by_transport = {}
    for identity in identities:
        identities_by_transport.setdefault(identity["transport_id"], []).append(identity)
    rows = []
    for transport in inputs["psf_base"]["transport_requests"]:
        point = points[(transport["slot"], transport["point_id"])]
        mapped = identities_by_transport.get(transport["transport_id"], [])
        mapped = sorted(mapped, key=lambda row: BANDS.index(row["band"]))
        rows.append({
            "resource_id": transport["transport_id"], "kind": "coadd_psf",
            "slot": transport["slot"], "region": point["region"],
            "brick": point["brick"], "point_id": transport["point_id"],
            "native_xy": point["native_xy"], "ra_dec": point["ra_dec"],
            "layer": point["layer"], "literal_url": transport["literal_url"],
            "observational_identity_ids": [row["identity_id"] for row in mapped],
            "observational_bands": [row["band"] for row in mapped],
            "expected_shapes": EXPECTED_PSF_SHAPES[point["region"]],
            "expected_dtype": "float32", "max_response_bytes": PSF_PER_RESPONSE_CAP,
            "semantic_limitations": {"units": "UNRESOLVED",
                                     "normalization": "SOURCE_VERIFIED_NOT_DIRECTLY_OBSERVED",
                                     "deployed_service_version": "UNRESOLVED",
                                     "etag_may_be_absent": True,
                                     "last_modified_may_be_available": True},
            "contract_evidence": {"resolved_contract_sha256": PSF_CONTRACT_SHA256,
                                  "identity_manifest_sha256": PSF_IDENTITIES_SHA256},
        })
    expected_order = [(slot, point) for slot in SLOTS for point in PSF_POINTS]
    if (len(rows) != 18 or [(r["slot"], r["point_id"]) for r in rows] != expected_order or
            any(r["observational_bands"] != list(BANDS) or
                len(r["observational_identity_ids"]) != 3 for r in rows) or
            len({item for row in rows for item in row["observational_identity_ids"]}) != 54):
        raise NativePSFAcquisitionError("PSF_RESOURCE_INVENTORY_INVALID")
    return rows


def exact_command(project: Path) -> list[str]:
    project = Path(project).resolve()
    audit = project / AUDIT_RELATIVE
    return [str(project / "oc3/.venv/bin/python"),
            str(project / "oc3/oc3_fixed_native_psf_acquisition.py"),
            "--acquire", "--execute-network", "--project", str(project),
            "--candidate", str(project / CANDIDATE_RELATIVE),
            "--authorization", str(project / AUTHORIZATION_RELATIVE),
            "--audit-directory", str(audit), "--log", str(audit / "ACQUISITION_RUN.log"),
            "--primary-request-count", str(PRIMARY_REQUESTS),
            "--retry-pool", str(RETRY_POOL),
            "--stage-request-cap", str(STAGE_REQUEST_CAP),
            "--fixed-body-bytes", str(FIXED_BODY_BYTES),
            "--psf-body-cap", str(PSF_TOTAL_RESERVATION)]


def build_candidate(project: Path) -> dict:
    project = Path(project).resolve()
    inputs = _required_inputs(project)
    fixed = _fixed_rows(project, inputs)
    psf = _psf_rows(inputs)
    value = _seal({
        "schema_version": "OC3_FIXED_NATIVE_PSF_ACQUISITION_CANDIDATE_001",
        "candidate_type": "FIXED_NATIVE_PRODUCTS_AND_PSF_ACQUISITION",
        "candidate_state": "PENDING_HUMAN_REVIEW", "stage_id": STAGE_ID,
        "selection_sha256": SELECTION_SHA256,
        "fixed_native_resolved_contract_sha256": FIXED_CONTRACT_SHA256,
        "psf_resolved_contract_sha256": PSF_CONTRACT_SHA256,
        "implementation_aggregate": implementation_hash(project),
        "inventories": {"fixed_native_resources": 12, "psf_transport_resources": 18,
                        "psf_observational_identities": 54,
                        "psf_spatial_points": 18},
        "body_budget": {"fixed_native_exact_bytes": FIXED_BODY_BYTES,
                        "psf_total_cap_bytes": PSF_TOTAL_RESERVATION,
                        "psf_per_response_cap_bytes": PSF_PER_RESPONSE_CAP,
                        "stage_primary_body_reservation": TOTAL_BODY_RESERVATION,
                        "global_body_cap": GLOBAL_BODY_CAP,
                        "disk_reservation_bytes": 2 * TOTAL_BODY_RESERVATION,
                        "io_reservation_bytes": 4 * TOTAL_BODY_RESERVATION},
        "request_plan": {"fixed_head": FIXED_HEAD_REQUESTS,
                         "fixed_get": FIXED_GET_REQUESTS,
                         "psf_head": PSF_HEAD_REQUESTS,
                         "psf_get": PSF_GET_REQUESTS,
                         "primary_request_count": PRIMARY_REQUESTS,
                         "retry_pool": RETRY_POOL,
                         "stage_request_cap": STAGE_REQUEST_CAP,
                         "automatic_retry": False, "automatic_resume": False,
                         "separate_resume_authorization_required": True,
                         "concurrency": CONCURRENCY},
        "starting_cumulative": {"requests": START_REQUESTS,
                                "body_bytes": START_BODY_BYTES},
        "acquisition_order": [r["resource_id"] for r in fixed + psf],
        "fixed_native_resources": fixed, "psf_transport_resources": psf,
        "psf_contract": {"band_mapping_decision": "A_ONE_RESPONSE_BUNDLES_G_R_Z",
                         "same_schema_north_south": False,
                         "region_specific_shapes": EXPECTED_PSF_SHAPES,
                         "preserve_exact_provider_response": True,
                         "split_per_band": False, "homogenize_shapes": False},
        "publication": {"staging_first": True, "immutable_publication": True,
                        "overwrite": False, "sha256_every_body": True},
        "negative_capabilities": {"alternate_url": False, "automatic_reprobe": False,
                                  "location_change": False, "cutout_extraction": False,
                                  "preprocessing": False, "morphology_inspection": False,
                                  "psf_normalization": False},
        "success_terminal": SUCCESS,
        "final_authorization_path": str(project / AUTHORIZATION_RELATIVE),
        "final_authorization_present": False,
        "command_argv": exact_command(project),
    })
    validate_candidate(value, project, compare_expected=False)
    return value


def validate_candidate(candidate: dict, project: Path, *, compare_expected: bool = True) -> dict:
    _verify_seal(candidate)
    if compare_expected and candidate != build_candidate(project):
        raise NativePSFAcquisitionError("ACQUISITION_CANDIDATE_MISMATCH")
    if (candidate.get("stage_id") != STAGE_ID or
            candidate.get("candidate_state") != "PENDING_HUMAN_REVIEW" or
            candidate.get("selection_sha256") != SELECTION_SHA256 or
            candidate.get("fixed_native_resolved_contract_sha256") != FIXED_CONTRACT_SHA256 or
            candidate.get("psf_resolved_contract_sha256") != PSF_CONTRACT_SHA256 or
            candidate.get("final_authorization_present") is not False or
            candidate.get("success_terminal") != SUCCESS or
            len(candidate.get("fixed_native_resources", [])) != 12 or
            len(candidate.get("psf_transport_resources", [])) != 18 or
            candidate.get("request_plan", {}).get("primary_request_count") != PRIMARY_REQUESTS or
            candidate.get("request_plan", {}).get("stage_request_cap") != STAGE_REQUEST_CAP or
            candidate.get("body_budget", {}).get("fixed_native_exact_bytes") != FIXED_BODY_BYTES or
            candidate.get("body_budget", {}).get("psf_total_cap_bytes") != PSF_TOTAL_RESERVATION or
            candidate.get("body_budget", {}).get("stage_primary_body_reservation") != TOTAL_BODY_RESERVATION or
            START_BODY_BYTES + TOTAL_BODY_RESERVATION > GLOBAL_BODY_CAP):
        raise NativePSFAcquisitionError("ACQUISITION_CANDIDATE_INVALID")
    if candidate["acquisition_order"] != [r["resource_id"] for r in
                                           candidate["fixed_native_resources"] +
                                           candidate["psf_transport_resources"]]:
        raise NativePSFAcquisitionError("ACQUISITION_ORDER_INVALID")
    return candidate


def validate_authorization(authorization: dict, candidate: dict, candidate_path: Path) -> dict:
    _verify_seal(authorization)
    expected_hash = hashlib.sha256(canonical(candidate) + b"\n").hexdigest()
    if (authorization.get("schema_version") !=
            "OC3_FIXED_NATIVE_PSF_ACQUISITION_FINAL_HUMAN_AUTHORIZATION_001" or
            authorization.get("stage_id") != STAGE_ID or
            authorization.get("scope") != "FIXED_NATIVE_PRODUCTS_AND_PSF_ACQUISITION" or
            authorization.get("authorization_state") != "FINAL_HUMAN_AUTHORIZATION" or
            authorization.get("authorized") is not True or
            authorization.get("resume") is not False or
            authorization.get("candidate_path") != str(Path(candidate_path).resolve()) or
            authorization.get("candidate_sha256") != expected_hash):
        raise NativePSFAcquisitionError("FINAL_AUTHORIZATION_INVALID")
    return authorization


def _assert_fixed_structure(expected: dict, observed: dict, rid: str) -> None:
    keys = ("logical_hdu", "physical_image_hdu", "compression_mapping", "shape", "dtype",
            "observed_bunit", "observed_imtype", "wcs")
    if any(observed.get(key) != expected.get(key) for key in keys):
        raise NativePSFAcquisitionError("FIXED_NATIVE_REPRESENTATION_DRIFT", rid)
    if observed.get("science_pixel_values_observed") != 0:
        raise NativePSFAcquisitionError("FIXED_NATIVE_PIXEL_DECODE_FORBIDDEN", rid)


def validate_fixed_body(row: dict, body: bytes) -> dict:
    if len(body) != row["expected_content_length"]:
        raise NativePSFAcquisitionError("FIXED_NATIVE_BODY_LENGTH_MISMATCH", row["resource_id"])
    def read_block(start: int, end: int) -> bytes:
        if start < 0 or end >= len(body):
            raise NativePSFAcquisitionError("FIXED_NATIVE_HEADER_OUT_OF_RANGE", row["resource_id"])
        return body[start:end + 1]
    try:
        observed = inspect_header(row, read_block)
    except Exception as exc:
        raise NativePSFAcquisitionError("FIXED_NATIVE_FITS_INVALID", row["resource_id"]) from exc
    _assert_fixed_structure(row["expected_structure"], observed, row["resource_id"])
    return observed


def _assert_psf_structure(row: dict, observed: dict) -> None:
    rid = row["resource_id"]
    if (observed.get("representation_format") != "FITS" or
            observed.get("image_hdu_count") != 3 or
            observed.get("bands") != list(BANDS) or
            observed.get("array_values_decoded") != 0):
        raise NativePSFAcquisitionError("PSF_REPRESENTATION_DRIFT", rid)
    images = [h for h in observed["hdus"] if h["is_image"]]
    if len(images) != 3:
        raise NativePSFAcquisitionError("PSF_ADDITIONAL_OR_MISSING_SCIENCE_PLANE", rid)
    for image, band in zip(images, BANDS):
        if (image["band"] != band or image["dtype"] != row["expected_dtype"] or
                image["shape"] != row["expected_shapes"][band]):
            raise NativePSFAcquisitionError("PSF_REGION_SHAPE_OR_DTYPE_DRIFT", rid)


def validate_psf_body(row: dict, body: bytes) -> dict:
    if not body or len(body) > row["max_response_bytes"]:
        raise NativePSFAcquisitionError("PSF_BODY_CAP_EXCEEDED", row["resource_id"])
    try:
        observed = inspect_response(body)
    except Exception as exc:
        raise NativePSFAcquisitionError("PSF_FITS_INVALID", row["resource_id"]) from exc
    _assert_psf_structure(row, observed)
    return observed


def _stage(path: Path, body: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise NativePSFAcquisitionError("STAGING_IDENTITY_CONFLICT")
    with path.open("xb") as handle:
        handle.write(body)
        handle.flush()
        os.fsync(handle.fileno())
    return file_hash(path)


def _publish(source: Path, destination: Path, expected_sha256: str) -> None:
    if destination.exists():
        raise NativePSFAcquisitionError("IMMUTABLE_PUBLICATION_CONFLICT")
    if file_hash(source) != expected_sha256:
        raise NativePSFAcquisitionError("STAGING_CHECKSUM_DRIFT")
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.replace(source, destination)
    os.chmod(destination, 0o444)
    if file_hash(destination) != expected_sha256:
        raise NativePSFAcquisitionError("IMMUTABLE_PUBLICATION_CHECKSUM_DRIFT")


class AcquisitionState:
    def __init__(self, root: Path, candidate: dict):
        self.root = Path(root)
        if self.root.exists():
            raise NativePSFAcquisitionError("SEPARATE_RESUME_AUTHORIZATION_REQUIRED")
        self.root.mkdir(parents=True)
        self.path = self.root / "ACQUISITION_LEDGER.json"
        self.value = {
            "schema_version": "OC3_FIXED_NATIVE_PSF_ACQUISITION_LEDGER_001",
            "stage_id": STAGE_ID, "candidate_seal": candidate["sealed"], "state": "ACTIVE",
            "starting_cumulative_requests": START_REQUESTS,
            "starting_cumulative_body_bytes": START_BODY_BYTES,
            "stage_requests": 0, "stage_retry_requests": 0,
            "stage_body_bytes": 0, "cumulative_requests": START_REQUESTS,
            "cumulative_body_bytes": START_BODY_BYTES,
            "heads": {}, "completed": [], "published": [], "attempts": [],
            "checksums": {}, "psf_identity_mappings": {},
            "cutouts_extracted": 0, "morphology_inspections": 0,
            "preprocessing_operations": 0,
        }
        _immutable_json(self.root / "ACQUISITION_CANDIDATE_COPY.json", candidate)
        self.flush()

    def flush(self) -> None:
        _atomic_json(self.path, self.value)

    def reserve(self, rid: str, method: str, body_cap: int) -> None:
        if (method not in ("HEAD", "GET") or body_cap < 0 or
                self.value["stage_requests"] + 1 > PRIMARY_REQUESTS or
                self.value["cumulative_body_bytes"] + body_cap > GLOBAL_BODY_CAP):
            raise NativePSFAcquisitionError("ACQUISITION_BUDGET_EXCEEDED", rid)
        self.value["stage_requests"] += 1
        self.value["cumulative_requests"] += 1
        self.value["attempts"].append({"resource_id": rid, "method": method,
                                       "body_cap": body_cap, "state": "STARTED"})
        self.flush()

    def complete_request(self, status: int, observed_bytes: int) -> None:
        if observed_bytes < 0 or self.value["stage_body_bytes"] + observed_bytes > TOTAL_BODY_RESERVATION:
            raise NativePSFAcquisitionError("ACQUISITION_BODY_ACCOUNTING_INVALID")
        attempt = self.value["attempts"][-1]
        if attempt["state"] != "STARTED" or observed_bytes > attempt["body_cap"]:
            raise NativePSFAcquisitionError("ACQUISITION_RESPONSE_CAP_EXCEEDED")
        attempt["state"] = "COMPLETE"
        attempt["status"] = status
        attempt["observed_bytes"] = observed_bytes
        self.value["stage_body_bytes"] += observed_bytes
        self.value["cumulative_body_bytes"] += observed_bytes
        self.flush()

    def fail_request(self, observed_bytes: int) -> None:
        attempt = self.value["attempts"][-1]
        if (attempt["state"] != "STARTED" or observed_bytes < 0 or
                self.value["cumulative_body_bytes"] + observed_bytes > GLOBAL_BODY_CAP):
            raise NativePSFAcquisitionError("ACQUISITION_FAILURE_ACCOUNTING_INVALID")
        attempt["state"] = "FAILED"
        attempt["observed_bytes"] = observed_bytes
        attempt["response_cap_exceeded"] = observed_bytes > attempt["body_cap"]
        self.value["stage_body_bytes"] += observed_bytes
        self.value["cumulative_body_bytes"] += observed_bytes
        self.flush()


def _check_head(row: dict, response) -> dict:
    status, headers, body, final_url = response
    if (status != 200 or body or final_url != row["literal_url"] or
            headers.get("content-encoding", "identity") != "identity" or
            headers.get("content-length") != str(row["expected_content_length"]) or
            headers.get("etag") != row["expected_etag"]):
        raise NativePSFAcquisitionError("FIXED_NATIVE_HEAD_DRIFT", row["resource_id"])
    return {"status": status, "content_length": row["expected_content_length"],
            "etag": headers.get("etag"), "last_modified": headers.get("last-modified")}


def run_acquisition(candidate: dict, authorization: dict, transport, root: Path,
                    *, candidate_path: Path,
                    fixed_validator=validate_fixed_body,
                    psf_validator=validate_psf_body) -> dict:
    validate_authorization(authorization, candidate, candidate_path)
    root = Path(root)
    disk_anchor = root.parent
    while not disk_anchor.exists() and disk_anchor != disk_anchor.parent:
        disk_anchor = disk_anchor.parent
    if shutil.disk_usage(disk_anchor).free < 2 * TOTAL_BODY_RESERVATION:
        raise NativePSFAcquisitionError("INSUFFICIENT_DISK_BEFORE_ACQUISITION")
    state = AcquisitionState(root, candidate)
    fixed = candidate["fixed_native_resources"]
    psf = candidate["psf_transport_resources"]
    current = None
    try:
        for row in fixed:
            current = row["resource_id"]
            state.reserve(current, "HEAD", 0)
            before = getattr(transport, "body_bytes_observed", 0)
            try:
                response = transport.head(row["literal_url"])
            except Exception:
                state.fail_request(getattr(transport, "body_bytes_observed", before) - before)
                raise
            state.complete_request(response[0], len(response[2]))
            evidence = _check_head(row, response)
            state.value["heads"][current] = evidence
            state.flush()
        if len(state.value["heads"]) != 12:
            raise NativePSFAcquisitionError("FIXED_NATIVE_HEAD_PLAN_INCOMPLETE")
        for row in fixed:
            current = row["resource_id"]
            expected = row["expected_content_length"]
            state.reserve(current, "GET", expected)
            before = getattr(transport, "body_bytes_observed", 0)
            try:
                status, headers, body, final_url = transport.get(row["literal_url"], expected)
            except Exception:
                state.fail_request(getattr(transport, "body_bytes_observed", before) - before)
                raise
            state.complete_request(status, len(body))
            if (status != 200 or final_url != row["literal_url"] or
                    headers.get("content-encoding", "identity") != "identity" or
                    headers.get("content-length") != str(expected) or len(body) != expected):
                raise NativePSFAcquisitionError("FIXED_NATIVE_GET_DRIFT", current)
            suffix = ".fits.fz"
            staged = state.root / "STAGING" / "fixed_native" / f"{current}{suffix}"
            digest = _stage(staged, body)
            descriptor = fixed_validator(row, body)
            destination = state.root / "RAW_IMMUTABLE" / "fixed_native" / f"{current}{suffix}"
            _publish(staged, destination, digest)
            state.value["completed"].append(current)
            state.value["published"].append(current)
            state.value["checksums"][current] = digest
            _immutable_json(state.root / "CHECKPOINTS" / f"{current}.json",
                            _seal({"stage_id": STAGE_ID, "resource_id": current,
                                   "kind": "fixed_native", "sha256": digest,
                                   "body_bytes": len(body), "descriptor": descriptor,
                                   "response_metadata": {"status": status,
                                                         "content_length": expected,
                                                         "etag": headers.get("etag"),
                                                         "last_modified": headers.get("last-modified")},
                                   "published_path": str(destination.relative_to(state.root))}))
            state.flush()
        for row in psf:
            current = row["resource_id"]
            cap = row["max_response_bytes"]
            state.reserve(current, "GET", cap)
            before = getattr(transport, "body_bytes_observed", 0)
            try:
                status, headers, body, final_url = transport.get(row["literal_url"], cap)
            except Exception:
                state.fail_request(getattr(transport, "body_bytes_observed", before) - before)
                raise
            state.complete_request(status, len(body))
            content_type = headers.get("content-type", "").split(";", 1)[0].strip().lower()
            content_length = headers.get("content-length")
            if content_length is not None:
                try:
                    content_length_value = int(content_length)
                except ValueError as exc:
                    raise NativePSFAcquisitionError("PSF_CONTENT_LENGTH_INVALID", current) from exc
            else:
                content_length_value = None
            if (status != 200 or final_url != row["literal_url"] or
                    headers.get("content-encoding", "identity") != "identity" or
                    content_type != "image/fits" or not body or len(body) > cap or
                    (content_length_value is not None and content_length_value != len(body))):
                raise NativePSFAcquisitionError("PSF_GET_DRIFT", current)
            staged = state.root / "STAGING" / "psf" / f"{current}.fits"
            digest = _stage(staged, body)
            descriptor = psf_validator(row, body)
            destination = state.root / "RAW_IMMUTABLE" / "psf" / f"{current}.fits"
            _publish(staged, destination, digest)
            state.value["completed"].append(current)
            state.value["published"].append(current)
            state.value["checksums"][current] = digest
            state.value["psf_identity_mappings"][current] = row["observational_identity_ids"]
            _immutable_json(state.root / "CHECKPOINTS" / f"{current}.json",
                            _seal({"stage_id": STAGE_ID, "resource_id": current,
                                   "kind": "coadd_psf", "sha256": digest,
                                   "body_bytes": len(body), "descriptor": descriptor,
                                   "response_metadata": {"status": status,
                                                         "content_type": content_type,
                                                         "content_length": content_length_value,
                                                         "etag": headers.get("etag"),
                                                         "last_modified": headers.get("last-modified")},
                                   "observational_identity_ids": row["observational_identity_ids"],
                                   "published_path": str(destination.relative_to(state.root))}))
            state.flush()
        if (len(state.value["published"]) != 30 or
                len({identity for values in state.value["psf_identity_mappings"].values()
                     for identity in values}) != 54 or
                state.value["stage_requests"] != PRIMARY_REQUESTS):
            raise NativePSFAcquisitionError("ACQUISITION_COMPLETENESS_FAILURE")
        state.value["state"] = "COMPLETE"
        state.flush()
        terminal = {"stage_id": STAGE_ID, "state": SUCCESS,
                    "fixed_native_published": 12, "psf_responses_published": 18,
                    "psf_observational_identities_mapped": 54,
                    "stage_requests": state.value["stage_requests"],
                    "stage_retry_requests": 0,
                    "cumulative_requests": state.value["cumulative_requests"],
                    "cumulative_body_bytes": state.value["cumulative_body_bytes"],
                    "locations_unchanged": True, "cutouts_extracted": 0,
                    "preprocessing_operations": 0, "morphology_inspections": 0}
        _immutable_json(state.root / "ACQUISITION_TERMINAL.json", terminal)
        return terminal
    except Exception as exc:
        state.value["state"] = "PARTIAL"
        if state.value["attempts"] and state.value["attempts"][-1]["state"] == "STARTED":
            state.value["attempts"][-1]["state"] = "FAILED"
        state.value["error"] = getattr(exc, "code", "ACQUISITION_FAILURE")
        state.value["failed_resource_id"] = current
        state.flush()
        terminal = {"stage_id": STAGE_ID, "state": PARTIAL,
                    "error": state.value["error"], "resource_id": current,
                    "stage_requests": state.value["stage_requests"],
                    "cumulative_requests": state.value["cumulative_requests"],
                    "cumulative_body_bytes": state.value["cumulative_body_bytes"],
                    "automatic_resume": False,
                    "separate_resume_authorization_required": True}
        _immutable_json(state.root / "ACQUISITION_TERMINAL.json", terminal)
        if isinstance(exc, NativePSFAcquisitionError):
            raise
        raise NativePSFAcquisitionError("ACQUISITION_FAILURE", current) from exc


def validate_candidate_offline(path: Path, project: Path) -> dict:
    candidate = _canonical_load(path)
    validate_candidate(candidate, project)
    return {"stage_id": STAGE_ID, "state": CANDIDATE_READY,
            "fixed_native_resources": 12, "fixed_native_body_bytes": FIXED_BODY_BYTES,
            "psf_transport_resources": 18, "psf_observational_identities": 54,
            "psf_total_cap_bytes": PSF_TOTAL_RESERVATION,
            "primary_request_count": PRIMARY_REQUESTS, "retry_pool": RETRY_POOL,
            "stage_request_cap": STAGE_REQUEST_CAP,
            "starting_cumulative_requests": START_REQUESTS,
            "starting_cumulative_body_bytes": START_BODY_BYTES,
            "final_authorization_present": False, "network_requests": 0,
            "implementation_aggregate": candidate["implementation_aggregate"]}
