import ast
import operator
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

TYPES = {'string': str, 'number': (int, float), 'integer': int, 'boolean': bool}
_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg,
    ast.Mod: operator.mod,
}


class ToolError(Exception):
    """Raised for problems the model can fix by retrying with better arguments."""


@dataclass
class Tool:
    name: str
    description: str
    params: dict  # {'arg': {'type': 'string', 'required': True}}
    fn: Callable[..., str]
    needs_confirm: bool = False
    examples: list = field(default_factory=list)

    def validate(self, args: dict) -> None:
        for key, spec in self.params.items():
            if key not in args:
                if spec.get('required', True):
                    raise ToolError(f'missing argument: {key}')
                continue
            expected = TYPES[spec['type']]
            value = args[key]
            if isinstance(value, bool) and spec['type'] != 'boolean':
                raise ToolError(f'argument {key} must be {spec["type"]}')
            if not isinstance(value, expected):
                raise ToolError(f'argument {key} must be {spec["type"]}')
        extra = set(args) - set(self.params)
        if extra:
            raise ToolError(f'unexpected arguments: {sorted(extra)}')


def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        if isinstance(node.op, ast.Pow) and abs(_eval(node.right)) > 10:
            raise ToolError('exponent too large')
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    raise ToolError('only numbers and + - * / % ** are allowed')


def calculator(expression: str) -> str:
    try:
        return str(_eval(ast.parse(expression, mode='eval')))
    except ZeroDivisionError as exc:
        raise ToolError('division by zero') from exc
    except SyntaxError as exc:
        raise ToolError('could not parse expression') from exc


def _safe_path(root: Path, rel: str) -> Path:
    path = (root / rel).resolve()
    if root.resolve() not in path.parents and path != root.resolve():
        raise ToolError('path is outside the allowed folder')
    return path


def default_tools(root: str | Path = '.') -> dict[str, Tool]:
    root = Path(root)

    def read_file(path: str) -> str:
        p = _safe_path(root, path)
        if not p.is_file():
            raise ToolError(f'no such file: {path}')
        return p.read_text()[:4000]

    def write_file(path: str, content: str) -> str:
        p = _safe_path(root, path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return f'wrote {len(content)} characters to {path}'

    def search_notes(query: str) -> str:
        hits = []
        for p in sorted(root.rglob('*.md')):
            for n, line in enumerate(p.read_text().splitlines(), 1):
                if query.lower() in line.lower():
                    hits.append(f'{p.relative_to(root)}:{n}: {line.strip()}')
        return '\n'.join(hits[:10]) or 'no matches'

    tools = [
        Tool('calculator', 'Evaluate an arithmetic expression.',
             {'expression': {'type': 'string'}}, calculator),
        Tool('read_file', 'Read a text file inside the notes folder.',
             {'path': {'type': 'string'}}, read_file),
        Tool('search_notes', 'Search markdown notes for a keyword.',
             {'query': {'type': 'string'}}, search_notes),
        Tool('write_file', 'Write a file inside the notes folder. Needs human approval.',
             {'path': {'type': 'string'}, 'content': {'type': 'string'}}, write_file,
             needs_confirm=True),
    ]
    return {t.name: t for t in tools}
