"""Offline correction and reviewed contract for the PHOTSYS physical probe."""
from __future__ import annotations

from pathlib import Path

from .galaxy_eligibility_photsys_authority_probe import (
    ALLOWED_FIELDS, PHOTSYSProbeError, PROJECT, columns_from_header, file_sha256,
    load_canonical_json, object_seal, parse_header, projection_plan, sealed,
    validate_sealed,
)
from .galaxy_eligibility_photsys_physical_probe import LITERAL_URL, STAGE_ID


PROBE_ROOT = PROJECT / "oc3/photsys_authority_physical_probe" / STAGE_ID
PROBE_TREE_SEAL = "6a4c0d06794b86a929efd68ec58908f17c8a2289c5e59fd881271c03eb93a27c"
CORRECTION_STATE = "OFFLINE_DERIVED_CORRECTION_FROM_IMMUTABLE_PROBE_EVIDENCE"
REVIEWED_STATE = "PHOTSYS_AUTHORITY_PHYSICAL_CONTRACT_REVIEWED"
FROZEN_IMPLEMENTATION_AGGREGATE = "800f413ee53ac2fecad66386a49ecaff04989d3ffce6b232cb52916a3c9dbbe6"
CORRECTION_PATH = PROJECT / "OC3_PHOTSYS_PHYSICAL_CONTRACT_CORRECTION_001.json"
REVIEWED_CONTRACT_PATH = (
    PROJECT / "oc3/INPUTS/OC3_PHOTSYS_AUTHORITY_REVIEWED_PHYSICAL_CONTRACT_001.json"
)
ORIGINAL_CONTRACT_PATH = PROBE_ROOT / "OC3_PHOTSYS_AUTHORITY_HEADER_SCHEMA_CONTRACT.json"
HEADER_BLOCK_PATHS = tuple(
    PROBE_ROOT / f"RAW_IMMUTABLE_HEADERS/header-block-{index:03d}.bin"
    for index in range(1, 5)
)
HEADER_BLOCK_HASHES = (
    "4586d713b5ebe02a13ae9d9750127132caae738da52a99b73263a090c09cb363",
    "fb6c0767bd8f8847686261494c41dc25410dee7b1c8156c92068cb36b5ecc286",
    "d4c2af44fb675e8395dbb90f3c65f192c7d1928581ed2807f386d5356c356e95",
    "6d24357908d3e08afbf9cea100a6740bea9490d5bb27a9b3c4bfd27b57d9393f",
)
EXPECTED_FILES = {
    *(f"CHECKPOINTS/{index:04d}.json" for index in range(1, 10)),
    "CHECKPOINTS/CHECKPOINT_INDEX.json",
    "OC3_PHOTSYS_AUTHORITY_HEADER_SCHEMA_CONTRACT.json",
    "OC3_PHOTSYS_AUTHORITY_PHYSICAL_PROBE_RUN.log",
    "OC3_PHOTSYS_AUTHORITY_PROBE_TERMINAL.json",
    "OC3_PHOTSYS_AUTHORITY_RESOURCE_ACCOUNTING.json",
    "OC3_PHOTSYS_AUTHORITY_TRANSPORT_EVIDENCE.json",
    *(f"RAW_IMMUTABLE_HEADERS/header-block-{index:03d}.bin" for index in range(1, 5)),
}


def probe_tree_rows() -> list[dict[str, object]]:
    return [{"path": str(path.relative_to(PROBE_ROOT)), "size": path.stat().st_size,
             "sha256": file_sha256(path)}
            for path in sorted(PROBE_ROOT.rglob("*")) if path.is_file()]


def validate_probe_tree() -> dict[str, object]:
    if not PROBE_ROOT.is_dir():
        raise PHOTSYSProbeError("PHYSICAL_PROBE_EVIDENCE_MISSING")
    rows = probe_tree_rows()
    if ({row["path"] for row in rows} != EXPECTED_FILES or
            object_seal(rows) != PROBE_TREE_SEAL):
        raise PHOTSYSProbeError("PHYSICAL_PROBE_EVIDENCE_MUTATED")
    for path, expected in zip(HEADER_BLOCK_PATHS, HEADER_BLOCK_HASHES):
        if file_sha256(path) != expected or path.stat().st_size != 2880:
            raise PHOTSYSProbeError("PHYSICAL_HEADER_BLOCK_MUTATED")
    terminal = validate_sealed(load_canonical_json(
        PROBE_ROOT / "OC3_PHOTSYS_AUTHORITY_PROBE_TERMINAL.json"))
    accounting = validate_sealed(load_canonical_json(
        PROBE_ROOT / "OC3_PHOTSYS_AUTHORITY_RESOURCE_ACCOUNTING.json"))
    if (terminal.get("state") != "PHOTSYS_AUTHORITY_RESOURCE_CONTRACT_RESOLVED" or
            terminal.get("table_cell_values_decoded") != 0 or
            accounting.get("network_requests_started") != 5 or
            accounting.get("header_blocks") != 4 or
            accounting.get("network_body_bytes") != 11520 or
            accounting.get("full_fits_gets") != 0 or
            any(accounting.get("forbidden_counters", {}).values())):
        raise PHOTSYSProbeError("PHYSICAL_PROBE_EVIDENCE_INVALID")
    return {"accounting": accounting, "rows": rows, "terminal": terminal}


def classify_hdu_type(hdu_index: int, header: dict[str, object]) -> str:
    if hdu_index == 0 and header.get("SIMPLE") is True and "XTENSION" not in header:
        return "PRIMARY"
    extension = header.get("XTENSION")
    if hdu_index > 0 and isinstance(extension, str) and extension:
        return extension
    raise PHOTSYSProbeError("OFFLINE_HDU_TYPE_CLASSIFICATION_FAILED")


def reconstruct_from_immutable_headers() -> dict[str, object]:
    validate_probe_tree()
    primary, primary_used = parse_header(HEADER_BLOCK_PATHS[0].read_bytes())
    table_bytes = b"".join(path.read_bytes() for path in HEADER_BLOCK_PATHS[1:])
    table, table_used = parse_header(table_bytes)
    if primary_used != 2880 or table_used != 8640:
        raise PHOTSYSProbeError("OFFLINE_HEADER_EXTENT_MISMATCH")
    columns = columns_from_header(table)
    plan = projection_plan(columns)
    return {
        "corrected_hdu_types": [classify_hdu_type(0, primary), classify_hdu_type(1, table)],
        "headers": [primary, table],
        "primary_header_bytes": primary_used,
        "projection": plan,
        "schema": [{"dtype": column.dtype, "name": column.name, "offset": column.offset,
                    "shape": list(column.shape), "tform": column.tform,
                    "tnull": column.tnull, "tscal": column.tscal,
                    "tzero": column.tzero, "unit": column.unit, "width": column.width}
                   for column in columns],
        "table_header_bytes": table_used,
    }


def _unchanged_findings() -> dict[str, bool]:
    return {key: True for key in (
        "area_per_brick_structural_presence", "brickid_offset_and_type",
        "brickname_offset_and_type", "column_count_13", "firewall_counters",
        "first_table_data_byte", "hdu_count", "header_only_boundary",
        "http_identity_and_representation", "photsys_offset_and_type",
        "row_count_662174", "row_width_79", "three_field_projection",
    )}


def build_correction() -> dict[str, object]:
    reconstruction = reconstruct_from_immutable_headers()
    original = validate_sealed(load_canonical_json(ORIGINAL_CONTRACT_PATH))
    structural = original["structural_contract"]
    if (original.get("first_table_data_byte") != 11520 or
            original.get("maximum_requested_byte") != 11519 or
            structural.get("row_count") != 662174 or structural.get("row_width") != 79 or
            len(structural.get("column_schema", [])) != 13 or
            reconstruction["schema"] != structural.get("column_schema") or
            reconstruction["projection"] != structural.get("selective_projection")):
        raise PHOTSYSProbeError("OFFLINE_CORRECTION_IMPACT_MISMATCH")
    return sealed({
        "correction_state": CORRECTION_STATE,
        "corrected_derived_hdu_type": reconstruction["corrected_hdu_types"],
        "immutable_header_evidence": [
            {"path": str(path.relative_to(PROJECT)), "sha256": expected, "size": 2880}
            for path, expected in zip(HEADER_BLOCK_PATHS, HEADER_BLOCK_HASHES)
        ],
        "impact_assessment": _unchanged_findings(),
        "network_requests": 0,
        "original_contract_path": str(ORIGINAL_CONTRACT_PATH.relative_to(PROJECT)),
        "original_contract_sha256": file_sha256(ORIGINAL_CONTRACT_PATH),
        "original_derived_hdu_type": [None, "PRIMARY"],
        "physical_conclusions_unchanged": True,
        "probe_tree_seal": PROBE_TREE_SEAL,
        "root_cause": {
            "code_path": "oc3/oc3lib/galaxy_eligibility_photsys_authority_probe.py:probe_hdu_inventory",
            "corrected_logic": "hdu_index = len(inventory); PRIMARY iff hdu_index == 0",
            "defect": "len(inventory) == 1 was evaluated before appending the current HDU",
            "scope": "DERIVED_LABEL_ONLY",
        },
        "stage_id": STAGE_ID,
        "table_cell_values_decoded": 0,
    })


def validate_correction(path: Path = CORRECTION_PATH) -> dict[str, object]:
    value = validate_sealed(load_canonical_json(path))
    if value != build_correction():
        raise PHOTSYSProbeError("PHYSICAL_CONTRACT_CORRECTION_INVALID")
    return value


def build_reviewed_contract(correction_sha256: str,
                            implementation_aggregate: str) -> dict[str, object]:
    correction = build_correction()
    if correction_sha256 != file_sha256(CORRECTION_PATH):
        raise PHOTSYSProbeError("CORRECTION_HASH_MISMATCH")
    original = validate_sealed(load_canonical_json(ORIGINAL_CONTRACT_PATH))
    accounting = validate_sealed(load_canonical_json(
        PROBE_ROOT / "OC3_PHOTSYS_AUTHORITY_RESOURCE_ACCOUNTING.json"))
    transport = validate_sealed(load_canonical_json(
        PROBE_ROOT / "OC3_PHOTSYS_AUTHORITY_TRANSPORT_EVIDENCE.json"))
    inventory = []
    for index, item in enumerate(original["hdu_inventory"]):
        corrected = dict(item); corrected["hdu_type"] = correction["corrected_derived_hdu_type"][index]
        inventory.append(corrected)
    return sealed({
        "correction_artifact": {"path": str(CORRECTION_PATH.relative_to(PROJECT)),
                                "sha256": correction_sha256},
        "file_size": transport["content_length"],
        "firewall": accounting["forbidden_counters"],
        "hdu_inventory": inventory,
        "http": {key: transport[key] for key in (
            "accept_ranges", "content_encoding", "content_length", "etag", "final_url",
            "last_modified", "representation_stability", "status")},
        "implementation_aggregate": implementation_aggregate,
        "literal_url": LITERAL_URL,
        "first_table_data_byte": original["first_table_data_byte"],
        "full_fits_gets": accounting["full_fits_gets"],
        "maximum_probe_byte": original["maximum_requested_byte"],
        "original_probe_tree_seal": PROBE_TREE_SEAL,
        "physical_contract": original["structural_contract"],
        "proof_maximum_requested_byte_before_table_data":
            original["proof_maximum_requested_byte_before_table_data"],
        "review_state": REVIEWED_STATE,
        "source_observation": "IMMUTABLE_PHYSICAL_PROBE_001",
        "stage_id": STAGE_ID,
        "table_cell_values_decoded": 0,
    })


def validate_reviewed_contract(path: Path = REVIEWED_CONTRACT_PATH) -> dict[str, object]:
    value = validate_sealed(load_canonical_json(path))
    # This is immutable historical evidence.  Later source additions must not
    # reinterpret its recorded implementation binding as the current tree.
    expected = build_reviewed_contract(file_sha256(CORRECTION_PATH),
                                       FROZEN_IMPLEMENTATION_AGGREGATE)
    if value != expected:
        raise PHOTSYSProbeError("REVIEWED_PHYSICAL_CONTRACT_INVALID")
    return value
