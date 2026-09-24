from __future__ import annotations

from email.message import Message
import io
from pathlib import Path
import tempfile
import unittest

import oc3_cross_observer_grouping_documentary as executor
from oc3lib.cross_observer_grouping import GroupingError, file_sha256, load_canonical_json
from oc3lib.cross_observer_grouping_documentary_provenance import (
    ACQUISITION_TERMINAL, HASHED_RESPONSE_SNAPSHOT, REQUIRED_CLAIMS,
    REVISION_PINNED_RESOURCE, assert_acquisition_cannot_finalize_grouping,
    validate_capture_contract, validate_documentary_semantic_review,
    validate_local_snapshot, validate_transport_evidence,
)
from oc3lib.cross_observer_grouping_documentary_validation import CANDIDATE, MANIFEST


PROJECT = Path(__file__).resolve().parents[2]


class Response(io.BytesIO):
    def __init__(self, body: bytes, url: str, content_type: str):
        super().__init__(body)
        self.status = 200
        self._url = url
        self.headers = Message()
        self.headers["Content-Type"] = content_type

    def geturl(self):
        return self._url


class Opener:
    def __init__(self, responses):
        self.responses = iter(responses)

    def open(self, request, timeout):
        response = next(self.responses)
        if request.full_url != response.geturl():
            raise AssertionError("request identity changed")
        return response


class DocumentaryProvenanceTests(unittest.TestCase):
    def code(self, expected, callback, *args, **kwargs):
        with self.assertRaises(GroupingError) as caught:
            callback(*args, **kwargs)
        self.assertEqual(caught.exception.code, expected)

    def test_historical_pre_authorization_artifacts_are_unchanged(self):
        expected = {
            "oc3/INPUTS/OC3_CROSS_OBSERVER_GROUPING_POLICY_CORE_MANIFEST_001.json":
                "2a380d5895e2763e2cead586a09c3b7d94ea3a812e5009917870c7de7b20ddb1",
            "oc3/INPUTS/OC3_CROSS_OBSERVER_GROUPING_DOCUMENTARY_FEASIBILITY_CANDIDATE_001.json":
                "181e254c98a89bea56c30842d76991ad6b042e58a5ffedc4975eca9506a3168f",
            "oc3/INPUTS/OC3_CROSS_OBSERVER_GROUPING_DOCUMENTARY_RESOURCE_MANIFEST_001.json":
                "81256914f5c12f97b9c81fd62c9c36a1d1c96672517804a65acbf75631e1ce51",
        }
        self.assertEqual({name: file_sha256(PROJECT / name) for name in expected}, expected)

    def test_live_resources_use_snapshot_capture_without_boolean_claim(self):
        manifest = load_canonical_json(MANIFEST)
        self.assertEqual(len(manifest["resources"]), 6)
        for resource in manifest["resources"]:
            self.assertNotIn("immutable_revision_required", resource)
            self.assertEqual(validate_capture_contract(resource), HASHED_RESPONSE_SNAPSHOT)
            self.assertIsNone(resource["revision_identity"])

    def test_boolean_upstream_immutability_is_rejected(self):
        self.code("BOOLEAN_UPSTREAM_IMMUTABILITY_FORBIDDEN", validate_capture_contract,
                  {"evidence_capture_mode": HASHED_RESPONSE_SNAPSHOT,
                   "immutable_revision_required": True, "revision_identity": None})

    def test_revision_pinned_mode_requires_actual_identity(self):
        self.code("PINNED_REVISION_IDENTITY_REQUIRED", validate_capture_contract,
                  {"evidence_capture_mode": REVISION_PINNED_RESOURCE,
                   "revision_identity": None})
        resource = {"evidence_capture_mode": REVISION_PINNED_RESOURCE,
                    "revision_identity": {"authority": "provider-tag",
                        "identifier": "v1.2.3", "verification_method": "signed tag object"}}
        self.assertEqual(validate_capture_contract(resource), REVISION_PINNED_RESOURCE)

    def test_transport_evidence_requires_null_optional_metadata(self):
        record = {"application_body_bytes": 3, "capture_mode": HASHED_RESPONSE_SNAPSHOT,
            "content_length": None, "content_type": "text/plain", "etag": None,
            "final_url": "https://example.invalid/a", "last_modified": None,
            "requested_url": "https://example.invalid/a", "resource_id": "A",
            "retrieved_at_utc": "2026-09-24T00:00:00Z", "sha256": "a" * 64,
            "status": 200}
        validate_transport_evidence(record)
        missing = dict(record); missing.pop("etag")
        self.code("TRANSPORT_EVIDENCE_SCHEMA_INVALID", validate_transport_evidence, missing)

    def test_raw_snapshot_is_read_only_and_hash_bound(self):
        with tempfile.TemporaryDirectory(dir=PROJECT / "oc3") as tmp:
            path = Path(tmp) / "snapshot.body"
            executor._write_raw_snapshot(path, b"exact-body")
            validate_local_snapshot(path, file_sha256(path))
            self.assertEqual(path.stat().st_mode & 0o222, 0)
            with self.assertRaises(FileExistsError):
                executor._write_raw_snapshot(path, b"replacement")

    def test_synthetic_acquisition_records_full_snapshot_provenance(self):
        manifest = load_canonical_json(MANIFEST)
        responses = [Response(f"body-{index}".encode(), resource["url"],
                     resource["accepted_content_types"][0])
                     for index, resource in enumerate(manifest["resources"])]
        original = executor.urllib.request.build_opener
        executor.urllib.request.build_opener = lambda handler: Opener(responses)
        try:
            with tempfile.TemporaryDirectory(dir=PROJECT / "oc3") as tmp:
                output = Path(tmp) / "attempt"
                counters = {"application_body_bytes": 0, "network_requests_started": 0}
                terminal = executor._acquire(load_canonical_json(CANDIDATE), output, counters)
                evidence = load_canonical_json(output / "TRANSPORT_EVIDENCE.json")
                self.assertEqual(terminal["state"], ACQUISITION_TERMINAL)
                self.assertEqual(counters["network_requests_started"], 6)
                self.assertEqual(len(evidence["resources"]), 6)
                for record in evidence["resources"]:
                    validate_transport_evidence(record)
                    self.assertIsNone(record["content_length"])
                    self.assertIsNone(record["etag"])
                    self.assertIsNone(record["last_modified"])
                    raw = output / "RAW_IMMUTABLE" / f"{record['resource_id']}.body"
                    validate_local_snapshot(raw, record["sha256"])
        finally:
            executor.urllib.request.build_opener = original

    def test_semantic_review_cannot_read_source_rows_or_photsys_values(self):
        claims = {claim: "SUPPORTED" for claim in REQUIRED_CLAIMS}
        self.code("DOCUMENTARY_REVIEW_SOURCE_ROWS_FORBIDDEN",
                  validate_documentary_semantic_review, claims=claims,
                  outcome="DOCUMENTARY_SOURCE_METADATA_PILOT_SPECIFIABLE",
                  source_rows_read=1, photsys_scientific_values_read=0,
                  acquisition_terminal=ACQUISITION_TERMINAL)
        self.code("DOCUMENTARY_REVIEW_PHOTSYS_VALUES_FORBIDDEN",
                  validate_documentary_semantic_review, claims=claims,
                  outcome="DOCUMENTARY_SOURCE_METADATA_PILOT_SPECIFIABLE",
                  source_rows_read=0, photsys_scientific_values_read=1,
                  acquisition_terminal=ACQUISITION_TERMINAL)

    def test_documentary_pass_requires_all_claims_and_no_threshold(self):
        claims = {claim: "SUPPORTED" for claim in REQUIRED_CLAIMS}
        self.assertEqual(validate_documentary_semantic_review(claims=claims,
            outcome="DOCUMENTARY_SOURCE_METADATA_PILOT_SPECIFIABLE",
            source_rows_read=0, photsys_scientific_values_read=0,
            acquisition_terminal=ACQUISITION_TERMINAL),
            "DOCUMENTARY_SOURCE_METADATA_PILOT_SPECIFIABLE")
        claims[REQUIRED_CLAIMS[-1]] = "INCONCLUSIVE"
        self.code("DOCUMENTARY_PASS_REQUIRES_ALL_CLAIMS_SUPPORTED",
                  validate_documentary_semantic_review, claims=claims,
                  outcome="DOCUMENTARY_SOURCE_METADATA_PILOT_SPECIFIABLE",
                  source_rows_read=0, photsys_scientific_values_read=0,
                  acquisition_terminal=ACQUISITION_TERMINAL)

    def test_acquisition_cannot_emit_grouping_terminal(self):
        assert_acquisition_cannot_finalize_grouping(ACQUISITION_TERMINAL)
        self.code("DOCUMENTARY_ACQUISITION_MISSION_TERMINAL_FORBIDDEN",
                  assert_acquisition_cannot_finalize_grouping,
                  "CROSS_OBSERVER_GROUPING_SUPPORTED_FOR_SPLITS_AND_REPLICATION")
