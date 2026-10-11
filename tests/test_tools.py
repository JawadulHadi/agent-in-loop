import pytest

from agent_loop.tools import ToolError, calculator, default_tools


def test_calculator_math_and_limits():
    assert calculator('2 + 3 * 4') == '14'
    for bad in ['__import__("os")', '2 ** 999', '1/0', 'open("x")']:
        with pytest.raises(ToolError):
            calculator(bad)


def test_read_file_is_sandboxed(tmp_path):
    (tmp_path / 'a.md').write_text('hello')
    (tmp_path.parent / 'secret.txt').write_text('nope')
    tools = default_tools(tmp_path)
    assert tools['read_file'].fn('a.md') == 'hello'
    with pytest.raises(ToolError):
        tools['read_file'].fn('../secret.txt')


def test_validation_rejects_wrong_types_and_extras():
    tool = default_tools('.')['calculator']
    with pytest.raises(ToolError):
        tool.validate({})
    with pytest.raises(ToolError):
        tool.validate({'expression': 5})
    with pytest.raises(ToolError):
        tool.validate({'expression': '1', 'x': 1})


def test_search_notes_finds_lines(tmp_path):
    (tmp_path / 'n.md').write_text('alpha\nBeta line\n')
    assert 'n.md:2' in default_tools(tmp_path)['search_notes'].fn('beta')
