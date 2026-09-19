#!/usr/bin/env python3
"""Synthetic-only unittest runner; physical network disabled before test imports."""
import sys,os
sys.dont_write_bytecode=True
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
 os.environ[key]='1'
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import socket
from unittest.mock import patch

def forbidden(*args,**kwargs): raise AssertionError('REAL_NETWORK_FORBIDDEN_IN_SYNTHETIC_TESTS')

if __name__=='__main__':
 import unittest,json,time
 start=time.monotonic()
 with patch.object(socket,'socket',forbidden),patch.object(socket,'create_connection',forbidden),patch.object(socket,'getaddrinfo',forbidden),patch.object(socket,'gethostbyname',forbidden),patch.object(socket,'gethostbyname_ex',forbidden),patch.object(socket,'gethostbyaddr',forbidden),patch.object(socket,'getnameinfo',forbidden),patch.object(socket,'getfqdn',forbidden):
  suite=unittest.defaultTestLoader.discover(str(Path(__file__).parent),pattern='test_*.py')
  result=unittest.TextTestRunner(verbosity=2).run(suite)
 print(json.dumps(dict(synthetic_only=True,real_network_requests=0,tests=result.testsRun,passed=result.testsRun-len(result.errors)-len(result.failures)-len(result.skipped),failed=len(result.errors)+len(result.failures),skipped=len(result.skipped),seconds=round(time.monotonic()-start,3))))
 raise SystemExit(0 if result.wasSuccessful() else 1)
