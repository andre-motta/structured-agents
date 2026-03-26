---
name: dependency-update
description: >
  Updates dependency pins in constraints.txt and requirements.txt across
  multiple repositories, following the builder to pipeline repos to testcollections
  constraint flow and variant-specific files (CPU, CUDA, ROCm). Validates
  cross-file consistency. Use when bumping packages, aligning pins after a
  release, or fixing version skew across the wheel build stack.
tools: [shell, ssh]
---

# Dependency update

## When to Use

- Bumping or aligning **package versions** in **constraints.txt** / **requirements.txt**.
- Work spans **builder**, **pipeline** repos, and **testcollections** with possible **variant** splits (CPU, CUDA, ROCm).

## Skill Discovery

Before updating dependencies, load relevant shared skills:

1. **ai-helpers** (always available):
   - `${SAGENT_WORKSPACE}/ai-helpers/helpers/skills/python-full-deps/SKILL.md`
     -- resolve full install-time dependency trees including markers and versions.
   - `${SAGENT_WORKSPACE}/ai-helpers/helpers/skills/vllm-compare-reqs/SKILL.md`
     -- compare requirements files between vLLM versions (useful for vLLM-related bumps).

2. **Target repo**: Check `${SAGENT_WORKSPACE}/<repo>/AGENTS.md` for
   repo-specific constraint workflows and `.claude/skills/*/SKILL.md` for
   dependency-related skills.

3. If relevant skills are found, **follow their instructions first**.
   Supplement with the generic steps below for anything not covered.

## Generic Instructions (fallback)

1. **Map the flow**  
   Understand **multi-repo constraint propagation**:
   - **Builder** repos are often the **source of truth** for pins used in builds.  
   - **Pipeline** repos consume or mirror those constraints for CI and assembly.  
   - **testcollections** (or test harness repos) must stay **consistent** with what ships or is probed.

   Apply changes in dependency order: update upstream (builder) first when the workflow requires it, then downstream, unless the user specifies a hotfix path.

2. **Variant-specific files**  
   Locate **CPU** vs **CUDA** vs **ROCm** (and any other variant) constraint files. Edit only the files that apply to the target platform or build matrix; duplicate pins must remain **identical** where the same package is shared across variants unless intentionally divergent (document why).

3. **Edit consistently**  
   - Keep **sorting** and **comment** style (`# reason`, ticket links) matching each file.  
   - Update **both** `requirements.txt` and `constraints.txt` when the repo uses both for install vs lock semantics.  
   - Search for **duplicate** package entries across the repo and reconcile.

4. **Validate**  
   - `diff` across related repos or branches for the same package line.  
   - Run **lint** or **compile** checks if the repo provides them (`pip-compile`, `tox -e deps`, etc.).  
   - Note any **transitive** pins that must move in lockstep (e.g. `numpy` / `torch` stacks).

5. **Report**  
   Table of package → old → new version, files touched, and repos. Flag files that still need downstream propagation.

## Error Handling

- **Conflicting pins**: Prefer the builder or the file documented as canonical; escalate in summary if two sources disagree.
- **Missing profile**: Use in-repo README or `tox.ini` to find which constraint file feeds which job.
