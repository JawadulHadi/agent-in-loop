"""The wire protocol between model and loop.

The model must answer with exactly one JSON object:
  {"tool": "<name>", "args": {...}}   to call a tool
  {"final": "<answer>"}               to finish
Small local models often wrap JSON in prose or code fences, so parsing is tolerant.
"""
import json
from dataclasses import dataclass, field


class ParseError(ValueError):
    pass


@dataclass
class ToolCall:
    tool: str
    args: dict = field(default_factory=dict)


@dataclass
class Final:
    text: str


def parse_action(text: str) -> ToolCall | Final:
    start, end = text.find('{'), text.rfind('}')
    if start == -1 or end <= start:
        raise ParseError('no JSON object found')
    try:
        data = json.loads(text[start:end + 1])
    except json.JSONDecodeError as exc:
        raise ParseError(f'invalid JSON: {exc.msg}') from exc
    if not isinstance(data, dict):
        raise ParseError('JSON must be an object')
    if 'final' in data:
        return Final(str(data['final']))
    if 'tool' in data:
        args = data.get('args', {})
        if not isinstance(args, dict):
            raise ParseError('args must be an object')
        return ToolCall(str(data['tool']), args)
    raise ParseError('object needs a tool or a final key')
