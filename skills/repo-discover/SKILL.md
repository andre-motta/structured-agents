---
name: repo-discover
description: >
  Analyzes a repository’s layout, conventions, and technology stack at runtime
  when no structured-agents profile exists or to enrich profile data. Reads
  README and common config files, infers language, CI, tests, lint, and branch
  habits, and emits a repo-profile-style summary. Use for unknown repos,
  onboarding, “what stack is this?”, or validating assumptions before edits.
tools: [shell, ssh, read]
mcps: []
---

# Repo discover

## When to Use

- No matching entry in `profiles/<repo>.yaml` (or profile is stale or thin).
- Before large refactors, CI changes, or container work when stack and gates are unclear.
- User asks what language, test runner, linter, or pipeline a tree uses.
- You need a **structured summary** comparable to a repo profile for planners or orchestrators.

## Instructions

1. **Pick the root**  
   Use the canonical path (often on the remote server under `$SAGENT_WORKSPACE/<repo>/` per **ssh-remote-exec**). If both local and remote exist, prefer the path you will actually edit.

2. **Read high-signal files first** (use **read** locally or `ssh … cat`/equivalent remotely):  
   `README.md`, `README.rst`, `CONTRIBUTING*`, then configs as present: `pyproject.toml`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `go.mod`, `package.json`, `Cargo.toml`, `Makefile`, `justfile`, `tox.ini`, `noxfile.py`, `.pre-commit-config.yaml`, `ruff.toml`, `.flake8`, `mypy.ini`, `pytest.ini`, `setup.py`, `Dockerfile`, `Containerfile*`, `.gitlab-ci.yml`, `.github/workflows/*`, `Jenkinsfile`, `.circleci/*`.

3. **Infer stack** (cite file paths in output):  
   - **Language(s)** and package manager from manifests and extensions.  
   - **CI** from GitLab/GitHub/Jenkins configs (job names, stages, images).  
   - **Tests** from `tox` envs, `pytest` markers, `make test`, `npm test`, Go test flags, etc.  
   - **Lint/format** from `ruff`, `black`, `eslint`, `golangci-lint`, pre-commit hooks.  
   - **Branch conventions** from `CONTRIBUTING`, MR templates, default branch in CI, or `git` docs—only state what is documented or obvious from automation.

4. **Optional deep pass**  
   List top-level dirs, spot `src/` layouts, `tests/` vs `test/`, and any `docs/` or `ansible/` hints. Skim one representative module only if needed for import style.

5. **Produce structured output**  
   Emit a short YAML or bullet block the orchestrator can treat like a profile fragment, for example:

   ```yaml
   repo: <name>
   root: <path>
   languages: [...]
   package_manager: ...
   ci: { system: gitlab|github|..., key_files: [...] }
   test_commands: [...]
   lint_commands: [...]
   formatters: [...]
   container: { present: bool, files: [...] }
   branch_conventions: ...
   notes: [assumptions, gaps]
   ```

6. **Honesty**  
   Mark unknowns as `unknown` or `not_found`; do not invent tools not evidenced in the tree.

## Error Handling

- Missing files: continue with what exists; widen search (`rg` for `pytest`, `tox`, workflow filenames) only when necessary.  
- SSH unreadable tree: confirm path and permissions; retry with a narrower `ls`/`find` depth.
