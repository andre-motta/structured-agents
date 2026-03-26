---
name: test-run
description: >
  Executes test suites in the workspace (locally if already on the remote, or
  over SSH otherwise), parses output, and reports failures. For wheels-test uses
  tox probe with markers; for other repos uses tox, make test, or pytest per
  profile. Use when verifying CI locally, debugging failing tests, or running
  probe markers after dependency changes.
tools: [shell, ssh]
---

# Test run

## When to Use

- Tests must run in the **workspace** environment (directly or via SSH).
- User asks to run **probe** tests, full suite, or a **specific marker/test name**.

## Local vs Remote

Follow the detection logic in **ssh-remote-exec** to determine whether you are
already on the remote server. If local to the remote, run commands directly
(`cd $SAGENT_WORKSPACE/<repo> && ...`). Only use SSH when on a different machine.

## Skill Discovery

Before running tests, load repo-specific guidance:

1. **Repo-specific skills**:
   - For **selfservice**: read `${SAGENT_WORKSPACE}/selfservice/.claude/skills/testing-builds/SKILL.md`
     -- test Python package builds via self-service CLI and GitLab pipelines
     across collections, variants, and architectures.
   - For other repos: check `${SAGENT_WORKSPACE}/<repo>/.claude/skills/*/SKILL.md`
     for test-execution skills, and `${SAGENT_WORKSPACE}/<repo>/AGENTS.md`
     for testing commands and conventions.

2. If repo-specific skills are found, **follow their instructions first**.
   Supplement with the generic steps below for anything not covered.

## Generic Instructions (fallback)

1. **Resolve command from profile**  
   Read `profiles/<repo>.yaml` and repo docs for default test commands, env vars, and working directory.

2. **wheels-test**  
   Run probe tests via tox, narrowing with marker and keyword when given:

   ```bash
   tox -e probe -- -m <marker> -k <test_name>
   ```

   Omit `-m` / `-k` only when the user requests the full probe env. Capture **stdout/stderr** in full for parsing.

3. **Other repositories**  
   Prefer, in order: **`tox`** (named env if specified), **`make test`**, **`pytest`** at repo root or `tests/`. Use the same Python/version as the profile or `tox` env.

4. **Execute**  
   `cd` to the canonical clone under `$SAGENT_WORKSPACE`, activate env if required (e.g. `source`, `conda`), then run the command. Use SSH only if not already on the remote (see **Local vs Remote** above). Use non-interactive flags (`pytest -q`, `tox -q` if appropriate) but keep enough output to diagnose failures.

5. **Parse and report**  
   Extract: passed/failed/skipped counts, **failed test names**, tracebacks (last few lines per failure), and **exit code**. Group failures by root cause when obvious (collection error vs assertion vs timeout).

6. **Follow-up**  
   If failures are environmental (missing GPU, network), note skip vs hard fail and suggest marker or env fix.

## Error Handling

- **tox env unknown**: List `tox -l` or read `tox.ini`.
- **SSH timeout** (remote mode only): Retry once; report partial log if any.
- **Flaky tests**: Mention rerun policy if user asked for stability check.
