"""C0 safety and provenance primitives; standard library only."""
import csv
import hashlib
import json
import os
import sqlite3
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

GIB = 1024**3
MIB = 1024**2
LIMIT_BYTES = 2 * GIB
LIMIT_REQUESTS = 1000


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(MIB), b''):
            h.update(block)
    return h.hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    os.replace(tmp, path)


class Stop(RuntimeError):
    pass


class Budget:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.root / 'resource_ledger.sqlite')
        self.db.executescript('''CREATE TABLE IF NOT EXISTS counters(k TEXT PRIMARY KEY, n INTEGER);
        INSERT OR IGNORE INTO counters VALUES('bytes',0),('data_requests',0),('all_requests',0);
        CREATE TABLE IF NOT EXISTS attempts(url TEXT PRIMARY KEY, n INTEGER);
        CREATE TABLE IF NOT EXISTS objects(id TEXT PRIMARY KEY);
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, payload TEXT);''')
        self.db.commit()

    def count(self, k):
        return self.db.execute('SELECT n FROM counters WHERE k=?', (k,)).fetchone()[0]

    def request(self, url, metadata):
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            a = self.db.execute('SELECT n FROM attempts WHERE url=?', (url,)).fetchone()
            if a and a[0] >= 4:
                raise Stop('RESOURCE_RETRIES_EXHAUSTED')
            if not metadata and self.count('data_requests') >= LIMIT_REQUESTS:
                raise Stop('DATA_REQUEST_LIMIT')
            self.db.execute('INSERT INTO attempts VALUES(?,1) ON CONFLICT(url) DO UPDATE SET n=n+1', (url,))
            self.db.execute("UPDATE counters SET n=n+1 WHERE k='all_requests'")
            if not metadata:
                self.db.execute("UPDATE counters SET n=n+1 WHERE k='data_requests'")

    def charge(self, n):
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            if n < 0 or self.count('bytes') + n > LIMIT_BYTES:
                raise Stop('BYTE_LIMIT')
            self.db.execute("UPDATE counters SET n=n+? WHERE k='bytes'", (n,))

    def object(self, identifier):
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            if self.db.execute('SELECT 1 FROM objects WHERE id=?', (identifier,)).fetchone():
                return
            if self.db.execute('SELECT COUNT(*) FROM objects').fetchone()[0] >= 96:
                raise Stop('OBJECT_LIMIT')
            self.db.execute('INSERT INTO objects VALUES(?)', (identifier,))

    def event(self, value):
        with self.db:
            self.db.execute('INSERT INTO events(payload) VALUES(?)', (json.dumps(value),))

    def events(self):
        return [json.loads(r[0]) for r in self.db.execute('SELECT payload FROM events ORDER BY id')]


# Positive allowlist: unknown columns fail closed without disclosing their names.
PROBE_FIELDS = frozenset(('galaxy_id', 'ra_deg', 'dec_deg', 'petro_radius',
                         'active_learning_on', 'source_row'))


def check_probe_fields(fields):
    if not set(fields) <= PROBE_FIELDS:
        raise Stop('PROBE_SCHEMA_NOT_ALLOWED')


def validate_product(kind, physical, image_shape=None, product_shape=None):
    if kind == 'pixel_mask' and physical.upper().startswith(('ANYMASK', 'ALLMASK')):
        raise Stop('CATALOG_FLAG_IS_NOT_PIXEL_MASK')
    if kind == 'pixel_ivar' and physical.upper().startswith('FLUX_IVAR'):
        raise Stop('CATALOG_IVAR_IS_NOT_PIXEL_IVAR')
    if kind in ('pixel_mask', 'pixel_ivar', 'pixel_nexp') and image_shape != product_shape:
        raise Stop('INCOMPATIBLE_PRODUCT_SHAPE')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch(budget, url, destination, source_id, metadata=True, max_bytes=8*MIB, force=False, timeout_seconds=25):
    """Sequential HTTP, no automatic retries; all redirects separately metered.

    Account response payload including failed attempts. Crash between read and charge
    is prevented by reserving each block first; charged bytes may conservatively
    exceed observed bytes after interruption. No compressed HTTP transport requested.
    """
    if not 1 <= timeout_seconds <= 120:
        raise Stop("INVALID_HTTP_TIMEOUT")
    dest = Path(destination)
    for e in reversed(budget.events()):
        if not force and e.get('url') == url and e.get('access_result') == 'VERIFIED' and dest.exists() and sha(dest) == e.get('sha256'):
            return e
    if max_bytes > 250*MIB:
        raise Stop('MANUAL_EXECUTION_REQUIRED')
    if budget.count('bytes') + max_bytes > LIMIT_BYTES:
        raise Stop('INSUFFICIENT_RESERVED_BUDGET')
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + '.part')
    current = url
    opener = urllib.request.build_opener(NoRedirect)
    event = dict(source_id=source_id, url=url, retrieved_at_utc=utc(),
                 local_logical_path=str(dest), observed_bytes=0,
                 access_result='INCONCLUSIVE', metadata=metadata)
    try:
        for redirect in range(6):
            budget.request(current, metadata)
            request = urllib.request.Request(current, headers={'User-Agent':'GalaxyMorphology-C0/0.1 (bounded research inventory)', 'Accept-Encoding':'identity'})
            try:
                event['transfer_stage'] = 'awaiting_response_headers'
                response = opener.open(request, timeout=timeout_seconds)
            except urllib.error.HTTPError as err:
                response = err
            event['transfer_stage'] = 'response_headers_received'
            event.update(final_url=current, http_status=response.code,
                         etag=response.headers.get('ETag'), last_modified=response.headers.get('Last-Modified'),
                         declared_bytes=response.headers.get('Content-Length'))
            if response.code in (301,302,303,307,308):
                from urllib.parse import urljoin
                current = urljoin(current, response.headers['Location'])
                response.close()
                if not current.startswith('https://'):
                    raise Stop('UNSAFE_REDIRECT')
                continue
            if response.code != 200:
                response.close()
                raise Stop('HTTP_ACCESS_UNRESOLVED')
            length = response.headers.get('Content-Length')
            if length and int(length) > max_bytes:
                response.close()
                raise Stop('RESOURCE_EXCEEDS_APPROVED_CAP')
            with response, open(part, 'wb') as output:
                while event['observed_bytes'] < max_bytes:
                    size = min(65536, max_bytes-event['observed_bytes'])
                    budget.charge(size)
                    event['transfer_stage'] = 'reading_body'
                    block = response.read(size)
                    # Refund unconsumed reservation after a successful read only.
                    with budget.db:
                        budget.db.execute("UPDATE counters SET n=n-? WHERE k='bytes'", (size-len(block),))
                    output.write(block)
                    event['observed_bytes'] += len(block)
                    if not block:
                        break
                else:
                    if not length or int(length) != max_bytes:
                        raise Stop('RESOURCE_CAP_REACHED')
            if length and event['observed_bytes'] != int(length):
                raise Stop('TRUNCATED_RESPONSE')
            os.replace(part, dest)
            dest.chmod(0o400)
            event.update(sha256=sha(dest), access_result='VERIFIED')
            break
        else:
            raise Stop('REDIRECT_LIMIT')
    except Exception as exc:
        # Never log exception strings: they can contain content from sensitive input.
        event['error_type'] = type(exc).__name__
        if isinstance(exc, Stop):
            event['reason'] = str(exc)
    finally:
        budget.event(event)
    return event
