"""Vercel entrypoint: replays a scripted agent run so the loop can be seen without a model.

No LLM is called here. ScriptedLLM plays fixed replies; the tools, parser, caps and the
confirmation gate are the real code. GET / renders the trace as HTML, GET /api/run returns JSON.
"""
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent_loop import Agent, ScriptedLLM, default_tools  # noqa: E402

TASK = 'Find the failure story in my notes, check the latency gain, and save a summary.'


def _call(tool: str, **args) -> str:
    return json.dumps({'tool': tool, 'args': args})


SCRIPT = [
    _call('search_notes', query='failure'),
    'Sure! Here is the file: read_file interview-prep.md',  # protocol violation, recovered
    _call('read_file', path='interview-prep.md'),
    _call('calculator', expression='(12 - 2) / 12 * 100'),
    _call('write_file', path='summary.md', content='Retry storm fixed with backoff.'),
    json.dumps({'final': 'Failure story: a gateway retry storm, fixed with exponential backoff '
                         'and jitter. Caching cut latency from 12s to 2s (about 83%). The '
                         'summary was not saved because the human declined the write.'}),
]


def run_demo() -> dict:
    agent = Agent(ScriptedLLM(SCRIPT), default_tools(ROOT / 'notes_demo'))  # confirm denies
    result = agent.run(TASK)
    return {'task': TASK, 'final': result.final, 'stopped_reason': result.stopped_reason,
            'steps': result.steps, 'tokens_estimate': result.tokens_estimate,
            'trace': result.trace, 'note': 'Scripted replay: no model was called.'}


def _render(data: dict) -> str:
    rows = []
    for t in data['trace']:
        if 'error' in t:
            what, out = 'invalid reply', t['error']
        elif 'final' in t:
            what, out = 'final', t['final']
        else:
            what, out = f"{t['tool']}({json.dumps(t['args'])})", t['observation']
        rows.append(f"<tr><td>{t['step']}</td><td><code>{html.escape(what)}</code></td>"
                    f"<td><pre>{html.escape(out)}</pre></td></tr>")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>agent-in-loop demo</title>
<style>body{{font:15px/1.5 system-ui,sans-serif;max-width:900px;margin:2rem auto;padding:0 16px}}
table{{border-collapse:collapse;width:100%}}
td{{border-top:1px solid #ddd;padding:6px;vertical-align:top}}
pre{{white-space:pre-wrap;margin:0}}</style></head><body>
<h1>agent-in-loop</h1>
<p>A tool-calling agent loop in plain Python. This page replays a <strong>scripted</strong> run:
no model is called, but the parser, tools, caps and human-approval gate are the real code.
Source: <a href="https://github.com/JawadulHadi/agent-in-loop">GitHub</a> ·
JSON: <a href="/api/run">/api/run</a></p>
<p><strong>Task:</strong> {html.escape(data['task'])}</p>
<table><tr><th>Step</th><th>Action</th><th>Observation</th></tr>{''.join(rows)}</table>
<p>Stopped: <code>{data['stopped_reason']}</code> after {data['steps']} steps,
about {data['tokens_estimate']} tokens (estimate).</p></body></html>"""


def app(environ, start_response):
    data = run_demo()
    if environ.get('PATH_INFO', '/').rstrip('/').endswith('/run'):
        body, ctype = json.dumps(data, indent=2), 'application/json'
    else:
        body, ctype = _render(data), 'text/html; charset=utf-8'
    payload = body.encode()
    start_response('200 OK', [('Content-Type', ctype), ('Content-Length', str(len(payload)))])
    return [payload]
