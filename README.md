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

## Live demo

<https://agent-in-loop.vercel.app> replays a scripted run on Vercel: the parser, tools, caps and
human-approval gate are the real code, but `ScriptedLLM` supplies the model replies, so no model
is called and the page costs nothing to host. `/api/run` returns the same run as JSON. The entry
point is `api/index.py`; run it locally with `python -c "from api.index import run_demo; print(run_demo())"`.

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

## Changelog and contributing

Every change adds an entry under **Unreleased** in [`CHANGELOG.md`](CHANGELOG.md) and updates this
README when behaviour, setup or limits change. A CI job fails any pull request that skips the
changelog (label it `skip-changelog` for changes that truly need none). Before opening a PR:

```bash
ruff check .
pytest -q
```

See `NOTES.md` for mistakes made and fixed.
