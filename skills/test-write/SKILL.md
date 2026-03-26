---
name: test-write
description: >
  Authors automated tests following project conventions: for wheels-test, pytest
  probe tests with markers (torch, vllm, etc.), hardware-adaptive skips, and
  conftest patterns; for other repos, unit tests mirroring existing layout. Use
  when adding coverage for new code, fixing flaky gaps, or implementing probe
  tests in repos under $SAGENT_WORKSPACE.
tools: [shell, ssh, write]
---

# Test write

## When to Use

- New or changed code needs **tests** before merge.
- Target is **wheels-test** (probe/pytest markers, hardware skips) or another repo with an established test layout.

## Local vs Remote

Follow the detection logic in **ssh-remote-exec** to determine whether you are
already on the remote server. If local to the remote, run commands and access
files directly. Only use SSH when on a different machine.

## Skill Discovery

Before writing tests, load repo-specific and shared skills:

1. **ai-helpers** (always available):
   - `${SAGENT_WORKSPACE}/ai-helpers/helpers/skills/unit-test-project-conformant/SKILL.md`
     -- write unit tests that match the project's existing test structure and
     style. **Load and follow this skill first** for any repo to ensure tests
     conform to the project's conventions.

2. **Repo-specific skills**:
   - For **wheels-test**: read `${SAGENT_WORKSPACE}/wheels-test/.claude/skills/probe-test-creator/SKILL.md`
     -- create probe tests for new packages with the correct markers, fixtures,
     and hardware-adaptive skips.
   - For other repos: check `${SAGENT_WORKSPACE}/<repo>/.claude/skills/*/SKILL.md`
     for test-related skills, and `${SAGENT_WORKSPACE}/<repo>/AGENTS.md`
     for testing conventions.

3. If repo-specific skills are found, **follow their instructions first**.
   Supplement with the generic steps below for anything not covered.

## Generic Instructions (fallback)

1. **Inspect existing tests**  
   List `tests/`, `conftest.py`, `pytest.ini`/`pyproject.toml` markers, and `tox` envs. Copy **file naming**, **fixture** style, and **assertion** patterns from the closest similar test.

2. **wheels-test (probe)**  
   - Use **pytest** with project **markers** (`torch`, `vllm`, etc.) as documented in the repo.
   - Apply **hardware-adaptive skipping** (`pytest.importorskip`, custom skips in `conftest.py`, or markers) so tests skip cleanly when GPU/libs are absent.
   - Reuse or extend **`conftest.py`** fixtures; do not duplicate session-scoped setup.
   - Keep probes **fast** and **deterministic** where possible; isolate temp dirs and env.

3. **Other repositories**  
   - Add **unit** (or integration) tests in the same tree as siblings (e.g. `tests/unit/`, mirror package path).
   - Use the project's runner: `pytest`, `unittest`, or framework-specific harness.
   - Match **async** vs sync, **parametrize** style, and **mock** libraries already in use.

4. **Implement**  
   Write minimal tests that prove behavior and regressions. Name tests after behavior (`test_rejects_empty_input`). Prefer one logical assertion cluster per test.

5. **Verify**  
   Run the narrowest command first (single file or `-k` expression), then the profile's full test target if required. Run directly if local to the remote, via SSH otherwise. Fix failures before handing off.

## Error Handling

- **Unclear marker policy**: Read `pyproject.toml` / `tox.ini` and existing `@pytest.mark` usage; align with maintainers' patterns.
- **Cannot run tests**: Document intended command from profile; still deliver consistent test code.
