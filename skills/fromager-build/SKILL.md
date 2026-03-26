---
name: fromager-build
description: >
  Runs fromager builds in the workspace (locally if already on the remote, or
  over SSH otherwise): bootstrap, build, build-sequence, wheel-server; respects
  settings directories, constraints, variants, and network isolation. Interprets
  failures (missing deps, compile errors, ABI mismatches). Use when building
  wheels, reproducing CI fromager failures, or starting a local wheel server.
tools: [shell, ssh]
---

# Fromager build

## When to Use

- User asks to run **fromager** (bootstrap, single build, sequence, or wheel server).
- Debugging **wheel build** failures in an isolated/constrained environment.

## Local vs Remote

Follow the detection logic in **ssh-remote-exec** to determine whether you are
already on the remote server. If local to the remote, run commands directly
(`cd $SAGENT_WORKSPACE/fromager && ...`). Only use SSH when on a different machine.

## Skill Discovery

Before running fromager, load repo-specific guidance:

1. **Target repo** (fromager):
   - Read `${SAGENT_WORKSPACE}/fromager/AGENTS.md` for the repo's agent rules,
     contribution guidelines, and file-scoped workflows.

2. If the `AGENTS.md` is found, **follow its instructions first** for CLI usage,
   testing, and contribution patterns. Supplement with the generic steps below
   for anything not covered.

## Generic Instructions (fallback)

1. **Environment**  
   `cd` to the fromager workspace or repo root indicated by the user or profile. Confirm **Python**, **constraints**, and **variant** (CPU/CUDA/ROCm) match the intended build. Use SSH only if not already on the remote.

2. **Settings and constraints**  
   Point **settings dirs** and constraint files as fromager expects (`--settings`, env vars, or project defaults). Do not mix variant constraint files across builds.

3. **Network isolation**  
   Respect proxy, offline, or air-gapped flags documented for the job. If downloads fail, distinguish **DNS/proxy** vs **index** vs **credentials**.

4. **Commands** (typical patterns; adjust flags per repo docs)

   - **bootstrap** -- initialize toolchain / venv / fromager state before builds.  
   - **build** -- build one or selected packages with current constraints.  
   - **build-sequence** -- ordered batch build as defined by project config.  
   - **wheel-server** -- serve built wheels for downstream install/tests.

   Capture full logs for failures (compiler stderr, pip metadata errors).

5. **Interpret failures**  
   - **Missing deps** -- undeclared build deps, wrong extras, or constraint pins blocking resolution.  
   - **Compilation errors** -- missing headers, wrong compiler flags, C++/CUDA mismatch; note package and first error line.  
   - **ABI / wheel tags** -- incompatible platform tags, manylinux vs local, CUDA major mismatch.

6. **Report**  
   Command line used, high-level outcome, artifact paths (wheel dirs), and actionable next step (pin change, flag, or dep fix).

## Error Handling

- **Unknown CLI**: Run `fromager --help` or project wrapper script help.
- **Partial sequence**: Identify first failing package; later packages may be cascaded failures.
