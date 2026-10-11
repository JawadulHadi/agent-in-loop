import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from .llm import LLM
from .protocol import Final, ParseError, parse_action
from .tools import Tool, ToolError


@dataclass
class RunResult:
    final: str | None
    stopped_reason: str  # 'final' | 'max_steps' | 'budget' | 'too_many_errors'
    steps: int
    tokens_estimate: int
    trace: list = field(default_factory=list)


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)  # rough, good enough for a budget guard


class Agent:
    def __init__(
        self,
        llm: LLM,
        tools: dict[str, Tool],
        max_steps: int = 8,
        max_tokens: int = 20_000,
        max_errors: int = 3,
        confirm: Callable[[str, dict], bool] | None = None,
        log_path: str | Path | None = None,
    ):
        self.llm, self.tools = llm, tools
        self.max_steps, self.max_tokens, self.max_errors = max_steps, max_tokens, max_errors
        self.confirm = confirm or (lambda name, args: False)  # deny by default
        self.log_path = Path(log_path) if log_path else None

    def system_prompt(self) -> str:
        lines = ['You solve tasks by calling tools. Reply with ONE JSON object and nothing else.',
                 'To call a tool: {"tool": "<name>", "args": {...}}',
                 'To finish: {"final": "<answer>"}', '', 'Tools:']
        for t in self.tools.values():
            args = ', '.join(f'{k}: {v["type"]}' for k, v in t.params.items())
            lines.append(f'- {t.name}({args}): {t.description}')
        return '\n'.join(lines)

    def _log(self, record: dict) -> None:
        if self.log_path:
            with self.log_path.open('a') as fh:
                fh.write(json.dumps({'ts': time.time(), **record}) + '\n')

    def _execute(self, name: str, args: dict) -> str:
        tool = self.tools.get(name)
        if tool is None:
            return f'error: unknown tool {name!r}. Available: {sorted(self.tools)}'
        try:
            tool.validate(args)
            if tool.needs_confirm and not self.confirm(name, args):
                return 'error: the human declined this action'
            return tool.fn(**args)
        except ToolError as exc:
            return f'error: {exc}'

    def run(self, task: str) -> RunResult:
        messages = [{'role': 'system', 'content': self.system_prompt()},
                    {'role': 'user', 'content': task}]
        tokens, errors, trace = 0, 0, []

        for step in range(1, self.max_steps + 1):
            if tokens >= self.max_tokens:
                return RunResult(None, 'budget', step - 1, tokens, trace)
            reply = self.llm.complete(messages)
            tokens += sum(estimate_tokens(m['content']) for m in messages) + estimate_tokens(reply)
            messages.append({'role': 'assistant', 'content': reply})
            try:
                action = parse_action(reply)
            except ParseError as exc:
                errors += 1
                obs = f'error: invalid reply ({exc}). Reply with one JSON object.'
                self._log({'step': step, 'reply': reply, 'observation': obs})
                trace.append({'step': step, 'error': str(exc)})
                if errors >= self.max_errors:
                    return RunResult(None, 'too_many_errors', step, tokens, trace)
                messages.append({'role': 'user', 'content': obs})
                continue

            if isinstance(action, Final):
                self._log({'step': step, 'reply': reply, 'final': action.text})
                trace.append({'step': step, 'final': action.text})
                return RunResult(action.text, 'final', step, tokens, trace)

            obs = self._execute(action.tool, action.args)
            if obs.startswith('error:'):
                errors += 1
            entry = {'step': step, 'tool': action.tool, 'args': action.args, 'observation': obs}
            self._log(entry)
            trace.append(entry)
            if errors >= self.max_errors:
                return RunResult(None, 'too_many_errors', step, tokens, trace)
            messages.append({'role': 'user', 'content': f'observation: {obs}'})

        return RunResult(None, 'max_steps', self.max_steps, tokens, trace)
