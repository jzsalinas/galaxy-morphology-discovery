#!/usr/bin/env python3
"""Full offline regression with Run-003 lifecycle-aware state assertions."""
from __future__ import annotations

import json
from pathlib import Path
import socket
import sys
import time
import unittest
from unittest.mock import patch

OC3 = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(OC3))

from oc3lib import source_metadata_recovery_governor_run003 as gov


REPLACED_PREAUTHORIZATION_TESTS = {
    "test_source_metadata_recovery_run003_preparation.Run003PreparationTests."
    "test_003_waiting_state_validates_and_is_inactive",
    "test_source_metadata_recovery_run003_preparation.Run003PreparationTests."
    "test_015_transport_is_unreachable_without_authorization",
    "test_source_metadata_recovery_run003_preparation.Run003PreparationTests."
    "test_016_no_run003_execution_namespaces_exist",
}


def _flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _flatten(item)
        else:
            yield item


class ActiveRun003LifecycleTests(unittest.TestCase):
    def test_active_or_terminal_state_validates(self):
        state = gov.validate_state()
        self.assertIn(state["state"], (gov.STATE_ACTIVE, gov.STATE_TERMINAL, "STOP_REQUIRES_HUMAN"))
        self.assertNotEqual(state["execution_status"], "NOT_STARTED")
        self.assertEqual(state["standing_authorization"], gov.binding(gov.STANDING_AUTHORIZATION))

    def test_transport_is_reachable_only_with_valid_authorization(self):
        self.assertTrue(gov.STANDING_AUTHORIZATION.is_file())
        authorization = gov.validate_standing_authorization(
            gov.STANDING_AUTHORIZATION, state_path=gov.STATE, require_initial_state=False)
        self.assertIs(authorization["authorized"], True)

    def test_current_run_namespaces_exist_after_activation(self):
        self.assertTrue(gov.LEDGER_ROOT.is_dir())
        self.assertTrue(gov.PERMIT_ROOT.is_dir())
        self.assertTrue((gov.PROJECT / "oc3/source_metadata_autonomous_recovery_run_003").is_dir())


def _forbidden(*args, **kwargs):
    raise AssertionError("REAL_NETWORK_FORBIDDEN_IN_SYNTHETIC_TESTS")


def main() -> int:
    start = time.monotonic()
    discovered = unittest.defaultTestLoader.discover(str(OC3 / "tests"), pattern="test_*.py")
    retained = [test for test in _flatten(discovered) if test.id() not in REPLACED_PREAUTHORIZATION_TESTS]
    observed_replacements = {test.id() for test in _flatten(discovered)} & REPLACED_PREAUTHORIZATION_TESTS
    if observed_replacements != REPLACED_PREAUTHORIZATION_TESTS:
        raise RuntimeError("RUN_003_PREAUTHORIZATION_TEST_IDENTITY_DRIFT")
    suite = unittest.TestSuite(retained)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(ActiveRun003LifecycleTests))
    with patch.object(socket, "socket", _forbidden), \
            patch.object(socket, "create_connection", _forbidden), \
            patch.object(socket, "getaddrinfo", _forbidden), \
            patch.object(socket, "gethostbyname", _forbidden), \
            patch.object(socket, "gethostbyname_ex", _forbidden), \
            patch.object(socket, "gethostbyaddr", _forbidden), \
            patch.object(socket, "getnameinfo", _forbidden), \
            patch.object(socket, "getfqdn", _forbidden):
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    summary = {
        "failed": len(result.errors) + len(result.failures),
        "passed": result.testsRun - len(result.errors) - len(result.failures) - len(result.skipped),
        "real_network_requests": 0,
        "replaced_preauthorization_assertions": len(REPLACED_PREAUTHORIZATION_TESTS),
        "seconds": round(time.monotonic() - start, 3),
        "skipped": len(result.skipped),
        "synthetic_only": True,
        "tests": result.testsRun,
    }
    print(json.dumps(summary, sort_keys=True))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
