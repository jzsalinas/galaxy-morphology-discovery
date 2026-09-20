"""Focused synthetic tests for durable bounded resource-contract Probe 002."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import oc3_resource_contract_probe002 as cli
from oc3lib.core import canonical
from oc3lib import resource_contract_probe002 as stage


PROJECT = Path(__file__).resolve().parents[2]
BINDING_PATH = PROJECT / "oc3/INPUTS/OC3_RESOURCE_CONTRACT_PROBE_BINDING_002.json"


def card(key, value=None):
    if value is None: text = key
    elif isinstance(value, bool): text = f"{key:<8}= {'T' if value else 'F':>20}"
    elif isinstance(value, str): text = f"{key:<8}= '{value}'"
    else: text = f"{key:<8}= {value:>20}"
    return text.ljust(80).encode("ascii")


def header(cards, blocks=1):
    capacity = blocks * 36
    if len(cards) + 1 > capacity: raise ValueError
    fillers = [card(f"K{index:07d}", index) for index in range(capacity - len(cards) - 1)]
    raw = b"".join(cards + fillers + [card("END")])
    assert len(raw) == blocks * 2880
    return raw


PRIMARY = header([card("SIMPLE", True), card("BITPIX", 8), card("NAXIS", 0), card("EXTEND", True)])
EXTENSION_CARDS = [
    card("XTENSION", "BINTABLE"), card("BITPIX", 8), card("NAXIS", 2),
    card("NAXIS1", 16), card("NAXIS2", 1), card("PCOUNT", 0), card("GCOUNT", 1),
    card("ZIMAGE", True), card("ZBITPIX", -32), card("ZNAXIS", 2),
    card("ZNAXIS1", 3600), card("ZNAXIS2", 3600), card("ZCMPTYPE", "RICE_1"),
    card("BUNIT", "count"), card("CTYPE1", "RA---TAN"), card("CTYPE2", "DEC--TAN"),
    card("CRPIX1", 1800.5), card("CRPIX2", 1800.5), card("CRVAL1", 1.0), card("CRVAL2", 2.0),
    card("CD1_1", -0.0000727778), card("CD1_2", 0.0), card("CD2_1", 0.0), card("CD2_2", 0.0000727778),
]


def payload(extension_blocks=1): return PRIMARY + header(EXTENSION_CARDS, extension_blocks)


class FakeTransport:
    def __init__(self, binding, *, first_blocks=1, fail_resource=None, fail_kind=None):
        self.rows = {r["literal_url"]: r for r in binding["resources"]}
        self.payloads = {url: payload(first_blocks if index == 0 else 1)
                         for index, url in enumerate(self.rows)}
        self.calls = []; self.fail_resource = fail_resource; self.fail_kind = fail_kind
        self.bulk_get_calls = 0
    def head(self, url):
        row = self.rows[url]; self.calls.append(("HEAD", row["resource_id"]))
        return 200, {"content-length": "1000000", "etag": '"synthetic"',
                     "last-modified": "synthetic", "content-encoding": "identity"}, b"", url
    def range(self, url, start, end):
        row = self.rows[url]; rid = row["resource_id"]
        self.calls.append(("RANGE", rid, start, end))
        body = self.payloads[url][start:end + 1]
        if len(body) < end - start + 1: body += b"D" * (end - start + 1 - len(body))
        status = 500 if self.fail_resource == rid and self.fail_kind == "status" else 206
        cr = ("bytes 0-0/1" if self.fail_resource == rid and self.fail_kind == "content-range"
              else f"bytes {start}-{end}/1000000")
        return status, {"content-range": cr, "content-encoding": "identity"}, body, url


def production_binding(): return stage.load_binding002(BINDING_PATH, PROJECT)


class Probe002Tests(unittest.TestCase):
    def test_01_binding_and_cumulative_counters(self):
        binding = production_binding()
        self.assertEqual(binding["cumulative_budget"], stage._expected_budget())
        self.assertEqual(binding["policy"], stage._expected_policy())

    def test_02_counter_reset_rejected(self):
        value = json.loads(BINDING_PATH.read_text()); value["cumulative_budget"]["used_requests"] = 8
        from oc3lib.resource_contract import _seal
        value = _seal(value)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "binding.json"; p.write_bytes(canonical(value) + b"\n")
            with self.assertRaisesRegex(stage.Probe002Error, "COUNTER_RESET_OR_MISMATCH"):
                stage.load_binding002(p, PROJECT)

    def test_03_head_checkpoints_survive_later_failure(self):
        binding = production_binding(); failed = binding["resources"][0]["resource_id"]
        before = stage.PROBE001_TERMINAL_SHA256
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "attempt"
            terminal, success = stage.run_probe002(binding, FakeTransport(binding, fail_resource=failed, fail_kind="status"), root)
            self.assertFalse(success); self.assertEqual(terminal["error"], "RANGE_STATUS_NOT_206")
            self.assertEqual(len(list((root / "HEAD_EVIDENCE").glob("*.json"))), 14)
            self.assertEqual(stage.PROBE001_TERMINAL_SHA256, before)

    def test_04_completed_checkpoint_survives_later_failure(self):
        binding = production_binding(); failed = binding["resources"][1]["resource_id"]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "attempt"
            terminal, success = stage.run_probe002(binding, FakeTransport(binding, fail_resource=failed, fail_kind="status"), root)
            first = binding["resources"][0]["resource_id"]
            self.assertFalse(success)
            checkpoint = root / "RESOURCE_CHECKPOINTS" / f"{first}.json"
            self.assertTrue(checkpoint.is_file())
            aggregate = json.loads((root / "PROBE_002_AGGREGATE.json").read_text())
            self.assertEqual(aggregate["resources"][0]["state"], "HEADER_RESOLVED")
            self.assertEqual(aggregate["resources"][1]["state"], "FAILED")

    def test_05_seven_plus_blocks_resolve(self):
        resource = production_binding()["resources"][0]; data = payload(7); calls = []
        def read(start, end): calls.append((start, end)); return data[start:end + 1]
        result = stage.inspect_header002(resource, read)
        self.assertEqual(result["header_blocks"], 8)
        self.assertEqual(result["shape"], [3600, 3600])

    def test_06_end_stops_before_next_range(self):
        resource = production_binding()["resources"][0]; data = payload(7); calls = []
        result = stage.inspect_header002(resource, lambda start, end: calls.append((start, end)) or data[start:end + 1])
        self.assertEqual(len(calls), 8)
        self.assertEqual(calls[-1][1], result["first_data_offset"] - 1)

    def test_07_first_data_block_never_requested(self):
        resource = production_binding()["resources"][0]; data = payload(1) + b"SCIENCE_CANARY" * 300
        calls = []
        result = stage.inspect_header002(resource, lambda start, end: calls.append((start, end)) or data[start:end + 1])
        self.assertTrue(all(end < result["first_data_offset"] for _, end in calls))
        self.assertEqual(result["science_pixels_decoded"], 0)

    def test_08_non_206_rejected(self):
        binding = production_binding(); rid = binding["resources"][0]["resource_id"]
        with tempfile.TemporaryDirectory() as td:
            terminal, _ = stage.run_probe002(binding, FakeTransport(binding, fail_resource=rid, fail_kind="status"), Path(td) / "a")
        self.assertEqual(terminal["error"], "RANGE_STATUS_NOT_206")

    def test_09_wrong_content_range_rejected(self):
        binding = production_binding(); rid = binding["resources"][0]["resource_id"]
        with tempfile.TemporaryDirectory() as td:
            terminal, _ = stage.run_probe002(binding, FakeTransport(binding, fail_resource=rid, fail_kind="content-range"), Path(td) / "a")
        self.assertEqual(terminal["error"], "RANGE_CONTENT_RANGE_MISMATCH")

    def test_10_local_136_request_ceiling(self):
        binding = production_binding()
        with tempfile.TemporaryDirectory() as td:
            store = stage.EvidenceStore(Path(td) / "a", binding)
            c = store.aggregate["counters"]
            c.update(local_requests=136, local_head_requests=14, local_range_requests=122,
                     local_range_body_bytes=122 * 2880,
                     local_range_body_bytes_observed=122 * 2880, cumulative_requests=200)
            with self.assertRaisesRegex(stage.Probe002Error, "PROBE002_LOCAL_REQUEST_LIMIT"):
                store.reserve_request("RANGE", binding["resources"][0]["resource_id"])

    def test_11_global_200_request_ceiling(self):
        binding = production_binding()
        with tempfile.TemporaryDirectory() as td:
            store = stage.EvidenceStore(Path(td) / "a", binding)
            store.aggregate["counters"]["cumulative_requests"] = 200
            with self.assertRaisesRegex(stage.Probe002Error, "PROBE002_GLOBAL_REQUEST_LIMIT"):
                store.reserve_request("HEAD", binding["resources"][0]["resource_id"])

    def test_12_per_resource_cap_identifies_resource(self):
        binding = production_binding(); resource = binding["resources"][0]
        with tempfile.TemporaryDirectory() as td:
            terminal, success = stage.run_probe002(binding, FakeTransport(binding, first_blocks=16), Path(td) / "a")
        self.assertFalse(success); self.assertEqual(terminal["error"], "FITS_HEADER_BLOCK_CAP")
        self.assertEqual(terminal["resource_id"], resource["resource_id"])
        self.assertEqual(terminal["observed_header_blocks"], 16)

    def test_13_partial_aggregate_checkpoint_sha_usable(self):
        binding = production_binding(); failed = binding["resources"][1]["resource_id"]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "a"; stage.run_probe002(binding, FakeTransport(binding, fail_resource=failed, fail_kind="status"), root)
            aggregate = json.loads((root / "PROBE_002_AGGREGATE.json").read_text())
            ref = aggregate["resources"][0]["resource_checkpoint"]
            data = (root / ref["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), ref["sha256"])
            self.assertEqual(json.loads(data)["science_pixels_decoded"], 0)

    def test_14_success_has_no_bulk_get_or_pixel_decode(self):
        binding = production_binding(); transport = FakeTransport(binding)
        with tempfile.TemporaryDirectory() as td:
            terminal, success = stage.run_probe002(binding, transport, Path(td) / "a")
            self.assertTrue(success); self.assertEqual(terminal["state"], stage.SUCCESS)
            self.assertEqual(terminal["science_pixels_decoded"], 0)
            self.assertEqual(terminal["bulk_get_requests"], 0)
            self.assertFalse(any(call[0] == "GET" for call in transport.calls))

    def test_15_probe001_evidence_untouched(self):
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in (PROJECT / stage.PROBE001_RELATIVE).iterdir() if p.is_file()}
        stage.verify_probe001_history(PROJECT)
        after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (PROJECT / stage.PROBE001_RELATIVE).iterdir() if p.is_file()}
        self.assertEqual(before, after)

    def test_16_dry_run_exact_zero_network(self):
        result = stage.dry_run(production_binding(), PROJECT)
        self.assertEqual(result["resources"], 14)
        self.assertEqual(result["used_global_requests"], 64)
        self.assertEqual(result["remaining_global_requests"], 136)
        self.assertEqual(result["max_new_range_requests"], 122)
        self.assertEqual(result["max_new_range_body_bytes"], 351360)
        self.assertEqual(result["network_requests"], 0)

    def test_17_cli_dry_run(self):
        with patch("builtins.print"):
            self.assertEqual(cli.main(["--dry-run", "--project", str(PROJECT),
                                       "--binding", str(BINDING_PATH)]), 0)


if __name__ == "__main__": unittest.main()
