import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from c0_pipeline.core import Budget, fetch

class Response(io.BytesIO):
    def __init__(self,data,status=200,headers=None):
        super().__init__(data);self.code=status;self.headers=headers or {'Content-Length':str(len(data))}

class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.b=Budget(self.root)
    def tearDown(self):self.b.db.close();self.tmp.cleanup()
    def test_cache_avoids_request(self):
        with patch('urllib.request.OpenerDirector.open',return_value=Response(b'abc')) as op:
            a=fetch(self.b,'https://fixture.test/a',self.root/'data','TEST',False,10)
            z=fetch(self.b,'https://fixture.test/a',self.root/'data','TEST',False,10)
            self.assertEqual(a['sha256'],z['sha256']);self.assertEqual(op.call_count,1)
            self.assertEqual(self.b.count('bytes'),3);self.assertEqual(self.b.count('data_requests'),1)
    def test_redirect_count(self):
        with patch('urllib.request.OpenerDirector.open',side_effect=[Response(b'',302,{'Location':'https://fixture.test/b'}),Response(b'abc')]):
            a=fetch(self.b,'https://fixture.test/a',self.root/'data','TEST',False,10)
            self.assertEqual(a['final_url'],'https://fixture.test/b');self.assertEqual(self.b.count('data_requests'),2)
    def test_oversized_rejected_before_read(self):
        with patch('urllib.request.OpenerDirector.open',return_value=Response(b'abc')):
            a=fetch(self.b,'https://fixture.test/a',self.root/'data','TEST',False,2)
            self.assertEqual(a['reason'],'RESOURCE_EXCEEDS_APPROVED_CAP');self.assertFalse((self.root/'data').exists())
            self.assertEqual(self.b.count('bytes'),0)
    def test_truncation_is_not_cached(self):
        with patch('urllib.request.OpenerDirector.open',return_value=Response(b'abc',headers={'Content-Length':'5'})):
            a=fetch(self.b,'https://fixture.test/a',self.root/'data','TEST',False,10)
            self.assertEqual(a['reason'],'TRUNCATED_RESPONSE');self.assertFalse((self.root/'data').exists())
            self.assertEqual(self.b.count('bytes'),3)
    def test_stream_cap(self):
        with patch('urllib.request.OpenerDirector.open',return_value=Response(b'abcdef',headers={'Unknown':'length'})):
            a=fetch(self.b,'https://fixture.test/a',self.root/'data','TEST',False,3)
            self.assertEqual(a['reason'],'RESOURCE_CAP_REACHED');self.assertEqual(self.b.count('bytes'),3)

    def test_timeout_keeps_budget_and_records_stage(self):
        with patch('urllib.request.OpenerDirector.open',side_effect=TimeoutError) as op:
            a=fetch(self.b,'https://fixture.test/a',self.root/'data','TEST',False,10,timeout_seconds=120)
            self.assertEqual(op.call_args.kwargs['timeout'],120)
            self.assertEqual(a['error_type'],'TimeoutError')
            self.assertEqual(a['transfer_stage'],'awaiting_response_headers')
            self.assertEqual(self.b.count('data_requests'),1)
            self.assertEqual(self.b.count('bytes'),0)
            self.assertFalse((self.root/'data').exists())
