import json

import httpx

from agent_loop import Agent, OllamaLLM, ScriptedLLM, default_tools


def call(tool, **args):
    return json.dumps({'tool': tool, 'args': args})


def final(text):
    return json.dumps({'final': text})


def test_tool_then_final(tmp_path):
    llm = ScriptedLLM([call('calculator', expression='6*7'), final('42')])
    result = Agent(llm, default_tools(tmp_path)).run('what is 6*7?')
    assert (result.final, result.stopped_reason, result.steps) == ('42', 'final', 2)
    assert result.trace[0]['observation'] == '42'


def test_recovers_from_invalid_json(tmp_path):
    llm = ScriptedLLM(['not json', final('ok')])
    result = Agent(llm, default_tools(tmp_path)).run('hi')
    assert result.final == 'ok' and result.steps == 2


def test_unknown_tool_is_reported_to_model(tmp_path):
    llm = ScriptedLLM([call('rm_rf'), final('gave up')])
    result = Agent(llm, default_tools(tmp_path)).run('x')
    assert 'unknown tool' in result.trace[0]['observation']


def test_step_cap(tmp_path):
    llm = ScriptedLLM([call('calculator', expression='1+1')] * 10)
    result = Agent(llm, default_tools(tmp_path), max_steps=3).run('loop')
    assert (result.final, result.stopped_reason, result.steps) == (None, 'max_steps', 3)


def test_error_cap(tmp_path):
    llm = ScriptedLLM(['bad'] * 5)
    result = Agent(llm, default_tools(tmp_path), max_errors=2).run('x')
    assert result.stopped_reason == 'too_many_errors' and result.steps == 2


def test_token_budget(tmp_path):
    llm = ScriptedLLM([call('calculator', expression='1+1')] * 10)
    result = Agent(llm, default_tools(tmp_path), max_tokens=50).run('x' * 400)
    assert result.stopped_reason == 'budget'


def test_write_denied_by_default(tmp_path):
    llm = ScriptedLLM([call('write_file', path='a.md', content='x'), final('done')])
    result = Agent(llm, default_tools(tmp_path)).run('write')
    assert not (tmp_path / 'a.md').exists()
    assert 'declined' in result.trace[0]['observation']


def test_write_allowed_when_human_confirms(tmp_path):
    seen = []
    llm = ScriptedLLM([call('write_file', path='a.md', content='x'), final('done')])
    agent = Agent(llm, default_tools(tmp_path), confirm=lambda n, a: seen.append(n) or True)
    agent.run('write')
    assert (tmp_path / 'a.md').read_text() == 'x' and seen == ['write_file']


def test_jsonl_log_written(tmp_path):
    log = tmp_path / 'run.jsonl'
    llm = ScriptedLLM([call('calculator', expression='2+2'), final('4')])
    Agent(llm, default_tools(tmp_path), log_path=log).run('x')
    rows = [json.loads(line) for line in log.read_text().splitlines()]
    assert rows[0]['tool'] == 'calculator' and rows[1]['final'] == '4'


def test_ollama_client_uses_chat_api():
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert request.url.path == '/api/chat' and body['stream'] is False
        return httpx.Response(200, json={'message': {'content': final('hi')}})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    assert OllamaLLM(client=client).complete([{'role': 'user', 'content': 'x'}]) == final('hi')
