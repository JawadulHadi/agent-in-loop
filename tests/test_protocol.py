import pytest

from agent_loop.protocol import Final, ParseError, ToolCall, parse_action


def test_plain_tool_call():
    assert parse_action('{"tool": "calculator", "args": {"expression": "1+1"}}') == ToolCall(
        'calculator', {'expression': '1+1'})


def test_fenced_json_and_prose_are_tolerated():
    text = 'Sure! ```json\n{"final": "done"}\n``` hope that helps'
    assert parse_action(text) == Final('done')


@pytest.mark.parametrize('bad', ['no json here', '{"tool": ', '[1, 2]', '{"hello": 1}',
                                 '{"tool": "x", "args": 5}'])
def test_bad_replies_raise(bad):
    with pytest.raises(ParseError):
        parse_action(bad)
