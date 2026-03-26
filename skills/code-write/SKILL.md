---
name: code-write
description: >
  Writes or modifies source code in the workspace (locally if already on the
  remote, or over SSH otherwise). Applies repo profiles for style, imports, and
  layout; validates with lint and tests before declaring work complete. Use when
  implementing features, fixing bugs, or refactoring in repos under $SAGENT_WORKSPACE.
tools: [shell, ssh]
---

# Code write

## When to Use

- Implementation or edits must happen in repos under `$SAGENT_WORKSPACE`.
- Changes must align with **profiles** (`profiles/<repo>.yaml`) and pass repo **lint/test** gates.

## Local vs Remote

Follow the detection logic in **ssh-remote-exec** to determine whether you are
already on the remote server. If local to the remote, run commands directly
(`cd $SAGENT_WORKSPACE/<repo> && ...`). Only use SSH when on a different machine.

## Skill Discovery

Before writing code, load repo-specific guidance:

1. **Target repo**: Check `${SAGENT_WORKSPACE}/<repo>/` for:
   - `AGENTS.md` for repo-level coding conventions, file-scoped workflows, and
     contribution rules (known repos with AGENTS.md: fromager, builder,
     architecture-decision-records, containers, rhaiis/containers,
     rhai/pipeline, rhel-ansible-setup).
   - `.claude/skills/*/SKILL.md` for any repo-specific coding skills.

2. If an `AGENTS.md` or repo-specific skills are found, **follow their
   instructions first** for style, structure, and workflow. Supplement with the
   generic steps below for anything not covered.

## Generic Instructions (fallback)

1. **Discover context**  
   Read existing files (directly if local, or via SSH) to match naming, imports, module layout, and error-handling patterns. Load `profiles/<repo>.yaml` for language version, formatters, test commands, and branch conventions.

2. **Plan minimal diffs**  
   Prefer the smallest change that satisfies the request. Reuse existing helpers and types; do not introduce new patterns unless the profile or codebase already uses them.

3. **Apply edits**  
   Edit in the canonical repo path under `$SAGENT_WORKSPACE`. Use the same tools the environment expects (`vim`, `patch`, `git apply`, or scripted writes). Keep file permissions and line endings consistent with the repo. Use SSH only if not already on the remote (see **Local vs Remote** above).

4. **Validate before "done"**  
   Run the repo's **lint** and **test** entrypoints from the profile or project docs (e.g. `tox -e lint`, `ruff`, `mypy`, `pytest`, `make test`). Fix failures caused by your edits; if failures are pre-existing, say so with evidence from the command output.

5. **Report**  
   Summarize files touched, commands run, and pass/fail of validation. Include relevant diff snippets or paths for review.

## Error Handling

- **SSH failures** (remote mode only): Verify host, key, and path; do not commit secrets in commands.
- **Lint/test missing**: Infer from `tox.ini`, `Makefile`, or CI config on the repo; document what was run.
- **Profile missing**: Fall back to in-repo config files only; note assumptions.
