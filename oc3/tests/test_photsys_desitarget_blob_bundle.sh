#!/usr/bin/env python3
"""Synthetic tests for exact Git blob validation."""
import base64
from importlib.machinery import SourceFileLoader
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
stage = SourceFileLoader("blob_bundle", str(ROOT / "oc3/oc3_exact_github_blob_bundle.sh")).load_module()


class BlobBundleTests(unittest.TestCase):
    def body(self, data=b"exact source\n"):
        sha = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
        value = {"content": base64.b64encode(data).decode(), "encoding": "base64",
                 "sha": sha, "size": len(data)}
        return json.dumps(value).encode(), sha, data

    def test_exact_blob(self):
        body, sha, data = self.body()
        self.assertEqual(stage.validate_blob_body(body, sha, len(data)), data)

    def test_sha_and_size_mismatch_refused(self):
        body, sha, data = self.body()
        for wrong_sha, wrong_size in (("0" * 40, len(data)), (sha, len(data) + 1)):
            with self.assertRaises(stage.ProbeError):
                stage.validate_blob_body(body, wrong_sha, wrong_size)

    def test_frozen_terms_and_paths(self):
        self.assertEqual(tuple(stage.MANDATORY_SOURCE_PATHS), (
            "py/desitarget/randoms.py", "bin/select_randoms", "bin/supplement_randoms",
            "py/desitarget/io.py", "doc/changes.rst"))
        self.assertEqual(tuple(stage.SEARCH_TERMS), (
            "survey-bricks", "survey-bricks-dr9-randoms", "AREA_PER_BRICK", "PHOTSYS",
            "supplement_randoms", "zeros=True", "write_randoms", "resolve"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
