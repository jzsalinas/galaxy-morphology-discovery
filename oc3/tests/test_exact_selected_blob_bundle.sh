#!/usr/bin/env python3
"""Focused offline tests for the selected exact Git blob bundle."""
from importlib.machinery import SourceFileLoader
from pathlib import Path
import base64
import hashlib
import json
import unittest

PROJECT = Path(__file__).resolve().parents[2]
module = SourceFileLoader("selected_blob_bundle", str(PROJECT / "oc3/oc3_exact_github_selected_blob_bundle.sh")).load_module()


class Tests(unittest.TestCase):
    def test_target_set_is_closed(self):
        self.assertEqual(module.TARGET_PATHS, (
            "py/desitarget/targets.py", "bin/split_randoms", "bin/alt_split_randoms"))

    def test_git_blob_identity(self):
        content = b"example\n"
        identity = hashlib.sha1(b"blob 8\0" + content).hexdigest()
        body = json.dumps({"sha": identity, "encoding": "base64", "size": 8,
                           "content": base64.b64encode(content).decode()}).encode()
        self.assertEqual(module.validate_blob_body(body, identity, 8), content)

    def test_bad_identity_fails(self):
        body = json.dumps({"sha": "0" * 40, "encoding": "base64", "size": 1,
                           "content": "eA=="}).encode()
        with self.assertRaises(module.ProbeError):
            module.validate_blob_body(body, "0" * 40, 1)


if __name__ == "__main__":
    unittest.main()
