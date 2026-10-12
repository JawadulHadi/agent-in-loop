import json

from api.index import app, run_demo


def test_demo_run_exercises_recovery_and_denied_write():
    data = run_demo()
    assert data['stopped_reason'] == 'final'
    assert any('error' in t for t in data['trace'])
    denied = [t for t in data['trace'] if t.get('tool') == 'write_file']
    assert denied and 'declined' in denied[0]['observation']


def _get(path):
    seen = {}
    body = b''.join(app({'PATH_INFO': path}, lambda s, h: seen.update(status=s, headers=h)))
    return seen['status'], dict(seen['headers']), body


def test_json_and_html_routes():
    status, headers, body = _get('/api/run')
    assert status == '200 OK' and headers['Content-Type'] == 'application/json'
    assert json.loads(body)['steps'] == 6
    status, headers, body = _get('/')
    assert headers['Content-Type'].startswith('text/html') and b'scripted' in body
