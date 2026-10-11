# Notes: mistakes and fixes

## 2026-10-11: CI "failed" in 3 seconds with no logs

**What happened:** The first CI runs went red in 2 to 3 seconds. `gh run view --log-failed` returned "log not found", which made it look like a broken workflow file.
**Root cause:** Not the code or the workflow. The run annotation said the job was not started because the GitHub account was locked over a billing issue, so no step ever ran.
**Fix:** Once the account lock was cleared, re-ran the checks. CI then passed on the same workflow with no changes to it.
**What I would do differently:** Read the run annotations (`gh run view <id>`) before touching the workflow. A red check that finishes in seconds with no logs is an account or runner problem, not a test failure.

## 2026-10-11: README overstated how small the agent is

**What I expected:** The README to describe the code accurately: "a tool-calling agent in about 250 lines".
**What happened:** Counting `agent_loop/` showed about 330 lines. The headline number was 30% off.
**Root cause:** The README was written before the confirmation gate and logging were finished, and the number was never re-checked.
**Fix:** Corrected the README to about 330 lines (commit e7a0e19).
**What I'd do differently:** Re-measure any number in a README right before publishing, because a reviewer will check the one claim that is easy to check.

---

## Template

## YYYY-MM-DD: <one-line title of what broke>

**What I expected:** <what the agent should have done>
**What happened:** <the actual behaviour; quote the relevant run.jsonl line>
**Root cause:** <why: model, parser, prompt, tool, cap>
**Fix:** <what I changed, with the commit link>
**Test that now guards it:** <tests/test_xxx.py::test_name>
**What I'd do differently:** <one sentence>
