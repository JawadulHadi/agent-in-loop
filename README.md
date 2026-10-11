# agent-in-loop

A tool-calling agent in about 330 lines of plain Python. No LangChain, no framework: just the loop,
so you can see exactly what an agent is.

```
task -> [system prompt + tools] -> model -> parse JSON -> tool call -> observation -> model ... -> final
```

## What it demonstrates

| Concept | Where |
| --- | --- |
| Tool calling over a plain JSON protocol (works with small local models) | `protocol.py` |
| Argument validation and sandboxed tools | `tools.py` |
| Step cap, error cap, approximate token budget | `agent.py` |
| Human confirmation for risky tools (denied by default) | `Agent(confirm=...)` |
| JSONL trace of every step for debugging and evals | `log_path` |
| Testing an LLM app with a scripted model, no network | `ScriptedLLM` |

## Run

```bash
pip install -e '.[dev]'
pytest -q
ollama pull llama3.2            # free, local
python -m agent_loop 'search my notes for the failure story and summarise it'
```

## Design decisions

- **Plain JSON, not native function calling.** It works with any model, including small local ones.
  The tolerant parser strips code fences and prose around the JSON.
- **Errors go back to the model as observations.** A bad argument or unknown tool is a chance to
  retry, not a crash. A cap stops infinite retry loops.
- **Risky tools need a human.** `write_file` is denied unless the `confirm` callback approves.
- **Token budget is an estimate** (characters divided by four). Good enough as a guard, not billing.

## Known limits

- Single agent, sequential tool calls, no memory between runs.
- Small models sometimes ignore the protocol. Check `run.jsonl` to see where.
- The calculator allows only arithmetic and caps exponents.

See `NOTES.md` for mistakes made and fixed.
