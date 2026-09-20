"""Focused offline orchestration regression for Metadata Bootstrap Attempt 001."""
from __future__ import annotations

from dataclasses import replace
import gzip
import hashlib
import io
import json
from pathlib import Path
import tempfile
from types import MappingProxyType
import unittest
from unittest.mock import patch

import numpy as np
from astropy.io import fits

import oc3_metadata_bootstrap as cli
import oc3lib.metadata_bootstrap as bootstrap
from oc3lib.core import file_hash
from oc3lib.metadata_bootstrap import (
    ATTEMPT_ID, ATTEMPT_RELATIVE_DIRECTORY, FINAL_EVIDENCE_ARTIFACTS,
    RESOURCE_ORDER, RESOURCES, BootstrapError, MetadataResource,
    SyntheticTransport, TransportResponse,
)
from oc3lib.provider_physical_contracts import (
    PRODUCTION_PHYSICAL_CONTRACTS, FrozenPhysicalContract, PhysicalRole,
)


def make_fits(path: Path, contract: FrozenPhysicalContract, rows: int,
              *, gzip_output: bool) -> tuple[Path, FrozenPhysicalContract]:
    columns = []
    for column_index, column in enumerate(contract.columns):
        form = column.tform
        names = [f"{row % 10000:04d}{'p' if row % 2 else 'm'}{row % 1000:03d}".encode()
                 for row in range(1, rows + 1)]
        if form == "8A": values = np.asarray(names, dtype="S8")
        elif form == "I": values = np.asarray([1 + row for row in range(rows)], dtype=np.int16)
        elif form == "J":
            base = 101 if column.ttype.lower() == "brickid" else 2_000_000_001 + column_index
            values = np.asarray([base + row for row in range(rows)], dtype=np.int32)
        elif form == "6J": values = np.asarray([[0, 1, 0, 0, 0, 0]] * rows, dtype=np.int32)
        elif form == "4I": values = np.asarray([[30001, 30002, 30003, 30004]] * rows, dtype=np.int16)
        elif form == "4E": values = np.asarray([[1.0, 2.0, 3.0, 4.0]] * rows, dtype=np.float32)
        elif form == "E": values = np.asarray([1.5 + row for row in range(rows)], dtype=np.float32)
        elif form == "D": values = np.asarray([10.25 + row for row in range(rows)], dtype=np.float64)
        elif form == "L": values = np.asarray([True] * rows, dtype=bool)
        else: raise AssertionError(form)
        columns.append(fits.Column(name=column.ttype, format=form, array=values))
    plain = path.with_suffix(".fits") if gzip_output else path
    fits.HDUList([fits.PrimaryHDU(), fits.BinTableHDU.from_columns(columns)]).writeto(
        plain, checksum=False)
    if gzip_output:
        path.write_bytes(gzip.compress(plain.read_bytes(), mtime=0)); plain.unlink()
    return path, replace(contract, naxis2=rows)


def response(item: MetadataResource, body: bytes | None = None, **changes) -> TransportResponse:
    headers = {"content-length": str(item.expected_length)}
    if item.role is PhysicalRole.SOUTH_PATCH_LIST:
        headers.update(etag=item.expected_etag,
                       **{"last-modified": item.expected_last_modified})
    values = dict(status=200, requested_url=item.url, final_url=item.url,
                  redirect_history=(), headers=headers,
                  body_chunks=() if body is None else (body,))
    values.update(changes)
    return TransportResponse(**values)


class WorkflowFixture:
    def __init__(self, project: Path):
        self.project = project
        fixture = project / "fixtures"; fixture.mkdir(parents=True)
        self.resources = {}
        self.contracts = {}
        self.bodies = {}
        for role in RESOURCE_ORDER:
            contract = PRODUCTION_PHYSICAL_CONTRACTS[role]
            rows = 1691 if role is PhysicalRole.SOUTH_PATCH_LIST else 1
            path = fixture / (f"{role.value}.fits" if role is PhysicalRole.SOUTH_PATCH_LIST
                              else f"{role.value}.fits.gz")
            path, adjusted = make_fits(
                path, contract, rows, gzip_output=contract.compression == "gzip")
            body = path.read_bytes(); self.bodies[role] = body
            if role is PhysicalRole.SOUTH_PATCH_LIST:
                item = RESOURCES[role]
                assert len(body) == item.expected_length
            else:
                item = MetadataResource(
                    role, f"https://synthetic.invalid/{role.value}/summary.fits.gz",
                    len(body), f"RAW_IMMUTABLE/{role.value}/summary.fits.gz", "gzip")
            self.resources[role] = item; self.contracts[role] = adjusted
        self.resources = MappingProxyType(self.resources)
        self.contracts = MappingProxyType(self.contracts)
        replies = [response(self.resources[role]) for role in RESOURCE_ORDER]
        replies += [response(self.resources[role], self.bodies[role]) for role in RESOURCE_ORDER]
        self.transport = SyntheticTransport(replies)
        self.integrity_calls = []

    def integrity(self, digest):
        self.integrity_calls.append(digest.role)
        return True

    def run(self, **changes):
        values = dict(
            project=self.project, transport=self.transport,
            authorization_sha256="a" * 64, rights_sha256="c" * 64,
            command_sha256_value="d" * 64, implementation_aggregate="b" * 64,
            synthetic_only=True, resources=self.resources, contracts=self.contracts,
            integrity_validator=self.integrity,
            retry_wait=lambda seconds: None,
            timestamp="2026-09-19T00:00:00+00:00",
        )
        values.update(changes)
        return bootstrap._execute_metadata_bootstrap_workflow(**values)


class MetadataBootstrapOrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="oc3_orchestrator_")
        self.project = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_cli_invokes_orchestrator_after_authorization_path(self):
        result = {"counters": {"requests": 8},
                  "outcome": "METADATA_BOOTSTRAP_PARTIALLY_RESOLVED",
                  "successful": True}
        with patch.object(cli, "execute_authorized_metadata_bootstrap", return_value=result) as run:
            output = io.StringIO()
            with patch("sys.stdout", output):
                code = cli.main(["--execute-network", "--authorization", "/a",
                                 "--rights-binding", "/r"])
        self.assertEqual(code, 0); self.assertEqual(run.call_count, 1)
        self.assertEqual(json.loads(output.getvalue())["state"],
                         "METADATA_BOOTSTRAP_PARTIALLY_RESOLVED")

    def test_authorized_wrapper_invokes_workflow(self):
        authorization = self.project / "authorization.json"; authorization.write_text("{}\n")
        rights = self.project / "rights.json"; rights.write_text("{}\n")
        expected = {"outcome": "METADATA_BOOTSTRAP_PARTIALLY_RESOLVED"}
        with patch.object(bootstrap, "activate_network_transport", return_value="transport") as gate, \
                patch.object(bootstrap, "_execute_metadata_bootstrap_workflow",
                             return_value=expected) as workflow:
            observed = bootstrap.execute_authorized_metadata_bootstrap(
                project=self.project, command=("tool",), authorization_path=authorization,
                rights_path=rights, resume=False)
        self.assertEqual(observed, expected); self.assertEqual(gate.call_count, 1)
        self.assertEqual(workflow.call_args.kwargs["transport"], "transport")

    def test_four_heads_precede_ordered_gets(self):
        fixture = WorkflowFixture(self.project); result = fixture.run()
        expected = ([('HEAD', role) for role in RESOURCE_ORDER] +
                    [('GET', role) for role in RESOURCE_ORDER])
        self.assertEqual(fixture.transport.calls, expected)
        self.assertEqual(result["outcome"], "METADATA_BOOTSTRAP_PARTIALLY_RESOLVED")

    def test_head_failure_prevents_every_get(self):
        fixture = WorkflowFixture(self.project)
        replies = [response(fixture.resources[role]) for role in RESOURCE_ORDER]
        replies[-1] = response(fixture.resources[RESOURCE_ORDER[-1]], status=503)
        fixture.transport = SyntheticTransport(replies)
        result = fixture.run()
        self.assertEqual([method for method, _ in fixture.transport.calls], ["HEAD"] * 4)
        self.assertEqual(result["outcome"], "PATCH_LIST_REPRESENTATION_DRIFT_STOP")

    def test_exact_request_and_cap_accounting(self):
        fixture = WorkflowFixture(self.project); result = fixture.run()
        total = sum(item.expected_length for item in fixture.resources.values())
        counters = result["counters"]
        self.assertEqual(counters["requests"], 8)
        self.assertEqual(counters["body_bytes"], total)
        self.assertEqual(counters["disk_bytes"], total)
        summaries = sum(fixture.resources[role].expected_length for role in RESOURCE_ORDER[:3])
        self.assertEqual(counters["io_bytes"], total * 4 + summaries)

    def test_raw_publication_and_integrity_gates(self):
        fixture = WorkflowFixture(self.project); fixture.run()
        attempt = self.project / ATTEMPT_RELATIVE_DIRECTORY
        self.assertEqual(fixture.integrity_calls, list(RESOURCE_ORDER[:3]))
        for role, item in fixture.resources.items():
            raw = attempt / item.raw_relative_path
            self.assertEqual(file_hash(raw), hashlib.sha256(fixture.bodies[role]).hexdigest())
            self.assertEqual(raw.stat().st_mode & 0o777, 0o444)
        self.assertEqual(list((attempt / "STAGING").iterdir()), [])

    def test_decode_waits_for_all_acquisition_and_physical_gates(self):
        fixture = WorkflowFixture(self.project); decoded = []
        class SpyDecoder(bootstrap.SelectiveFitsDecoder):
            def decode(inner, path, contract):
                self.assertEqual(len(fixture.transport.calls), 8)
                self.assertEqual(fixture.integrity_calls, list(RESOURCE_ORDER[:3]))
                decoded.append(contract.role)
                return super().decode(path, contract)
        fixture.run(decoder_factory=SpyDecoder)
        self.assertEqual(decoded, list(RESOURCE_ORDER[:3]))

    def test_patch_header_only_and_no_patch_decoder(self):
        fixture = WorkflowFixture(self.project); decoded = []
        class SpyDecoder(bootstrap.SelectiveFitsDecoder):
            def decode(inner, path, contract):
                decoded.append(contract.role); return super().decode(path, contract)
        fixture.run(decoder_factory=SpyDecoder)
        attempt = self.project / ATTEMPT_RELATIVE_DIRECTORY
        evidence = json.loads((attempt / "PATCH_ACQUISITION_BOUND_EVIDENCE.json").read_text())
        physical = json.loads((attempt / "BOOTSTRAP_PHYSICAL_CONTRACT_EVIDENCE.json").read_text())
        self.assertNotIn(PhysicalRole.SOUTH_PATCH_LIST, decoded)
        self.assertEqual((evidence["payload_bytes_observed"], evidence["row_decoder_calls"]), (0, 0))
        self.assertEqual(physical["roles"]["SOUTH_PATCH_LIST"]["payload_bytes_observed"], 0)

    def test_semantic_failure_selects_frozen_terminal(self):
        fixture = WorkflowFixture(self.project)
        with patch.object(bootstrap, "validate_regional_semantics",
                          side_effect=BootstrapError("METADATA_VALUE_SEMANTICS_FAILURE")):
            result = fixture.run()
        self.assertEqual(result["outcome"], "METADATA_VALUE_SEMANTICS_FAILURE")
        self.assertFalse(result["successful"])

    def test_success_creates_complete_expected_evidence(self):
        fixture = WorkflowFixture(self.project); result = fixture.run()
        attempt = self.project / ATTEMPT_RELATIVE_DIRECTORY
        self.assertEqual({path.name for path in attempt.iterdir() if path.is_file()},
                         set(FINAL_EVIDENCE_ARTIFACTS))
        self.assertEqual(result["patch_state"],
                         "PATCH_ACQUISITION_BOUND_PENDING_HUMAN_REVIEW")

    def test_resolved_is_unreachable_under_model_b(self):
        self.assertEqual(bootstrap.terminal_outcome(("METADATA_BOOTSTRAP_RESOLVED",
            "METADATA_BOOTSTRAP_PARTIALLY_RESOLVED")),
            "METADATA_BOOTSTRAP_PARTIALLY_RESOLVED")
        with self.assertRaises(BootstrapError):
            bootstrap.terminal_outcome(("METADATA_BOOTSTRAP_RESOLVED",))

    def test_transport_error_stops_after_single_frozen_retry(self):
        fixture = WorkflowFixture(self.project)
        base = fixture.transport
        class FailingTransport:
            def __init__(inner): inner.calls = []
            def head(inner, item):
                inner.calls.append(("HEAD", item.role)); return base.head(item)
            def get(inner, item):
                inner.calls.append(("GET", item.role))
                if item.role is PhysicalRole.NORTH_SUMMARY:
                    raise OSError("synthetic transport failure")
                return base.get(item)
        fixture.transport = FailingTransport(); result = fixture.run()
        self.assertEqual(fixture.transport.calls,
            [('HEAD', role) for role in RESOURCE_ORDER] +
            [('GET', PhysicalRole.ROOT_SUMMARY), ('GET', PhysicalRole.NORTH_SUMMARY),
             ('GET', PhysicalRole.NORTH_SUMMARY)])
        self.assertEqual(result["outcome"], "METADATA_TRANSPORT_INTEGRITY_FAILURE")
        self.assertEqual(result["counters"]["requests"], 7)

    def test_single_exact_identity_retry_can_recover(self):
        fixture = WorkflowFixture(self.project); base = fixture.transport
        class OnceFailingTransport:
            def __init__(inner): inner.calls = []; inner.failed = False
            def head(inner, item):
                inner.calls.append(("HEAD", item.role)); return base.head(item)
            def get(inner, item):
                inner.calls.append(("GET", item.role))
                if item.role is PhysicalRole.NORTH_SUMMARY and not inner.failed:
                    inner.failed = True; raise OSError("one synthetic failure")
                return base.get(item)
        fixture.transport = OnceFailingTransport(); result = fixture.run()
        self.assertEqual(result["outcome"], "METADATA_BOOTSTRAP_PARTIALLY_RESOLVED")
        self.assertEqual(result["counters"]["requests"], 9)
        north_gets = [call for call in fixture.transport.calls
                      if call == ("GET", PhysicalRole.NORTH_SUMMARY)]
        self.assertEqual(len(north_gets), 2)

    def test_fresh_attempt_only_no_automatic_resume(self):
        fixture = WorkflowFixture(self.project); fixture.run()
        with self.assertRaises(BootstrapError) as caught:
            bootstrap._execute_metadata_bootstrap_workflow(
                project=self.project, transport=fixture.transport,
                authorization_sha256="a" * 64, rights_sha256="c" * 64,
                command_sha256_value="d" * 64, implementation_aggregate="b" * 64,
                synthetic_only=True, resources=fixture.resources,
                contracts=fixture.contracts, integrity_validator=fixture.integrity,
                retry_wait=lambda seconds: None)
        self.assertEqual(caught.exception.code, "METADATA_LOCAL_STATE_CONFLICT")

    def test_failure_writes_terminal_and_preserves_staging_rules(self):
        fixture = WorkflowFixture(self.project)
        replies = [response(fixture.resources[role]) for role in RESOURCE_ORDER]
        replies.append(response(fixture.resources[PhysicalRole.ROOT_SUMMARY], b"short"))
        fixture.transport = SyntheticTransport(replies)
        result = fixture.run(); attempt = self.project / ATTEMPT_RELATIVE_DIRECTORY
        self.assertEqual(result["outcome"], "METADATA_TRANSPORT_INTEGRITY_FAILURE")
        self.assertTrue((attempt / "BOOTSTRAP_TERMINAL.json").is_file())
        self.assertEqual(list((attempt / "STAGING").iterdir()), [])


if __name__ == "__main__":
    unittest.main()
