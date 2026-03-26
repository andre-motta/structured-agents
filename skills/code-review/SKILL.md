---
name: code-review
description: >
  Reviews code changes for correctness, security, maintainability, and convention
  adherence from local diffs or merge-request diffs. Produces structured findings
  with severity (critical, suggestion, nitpick). Use when reviewing a PR/MR,
  auditing a patch, or when the user asks for a code review before merge.
tools: [shell, read]
---

# Code review

## When to Use

- User provides a **local diff** (`git diff`, patch file) or points to an **MR/MR branch**.
- Need a structured review before merge, release, or handoff.
- Focus on quality, security, edge cases, and **test coverage** gaps.

## Skill Discovery

Before reviewing, load repo-specific guidance:

1. **ai-helpers** (always available):
   - `${SAGENT_WORKSPACE}/ai-helpers/helpers/skills/coderabbit-review/SKILL.md`
     -- for evaluating automated review comments on the change.

2. **Target repo**: Check `${SAGENT_WORKSPACE}/<repo>/` for:
   - `.claude/skills/*/SKILL.md` matching "review" (known examples:
     `builder-reviewer`, `infrastructure-reviewer`, `ansible-setup-reviewer`,
     `review-pipeline` in rhai/pipeline and rhaiis/pipeline).
   - `AGENTS.md` for repo conventions and review expectations.

3. If repo-specific review skills are found, **follow their instructions first**.
   Supplement with the generic checklist below for anything not covered.

## Generic Instructions (fallback)

1. **Gather the change set**  
   Use `read` (and `shell` for `git diff`, `git show`, `git log -1`) to obtain the full diff and surrounding context. For MRs, include base..head or the provided patch; ensure new files are included.

2. **Check conventions**  
   If a **profile** exists (`profiles/<repo>.yaml`), verify style, import order, naming, and testing expectations. Otherwise infer from nearby files and existing tests.

3. **Systematic pass**  
   Evaluate:
   - **Correctness** — logic, types, API usage, race conditions, resource cleanup.
   - **Errors** — handling of failures, timeouts, invalid input; no silent swallowing without justification.
   - **Security** — injection, authz, secrets, unsafe deserialization, path traversal.
   - **Edge cases** — empty collections, nulls, boundary values, concurrency.
   - **Tests** — new behavior covered; negative and regression cases where appropriate.

4. **Structured output**  
   For each finding use a clear **severity**:
   - **critical** — merge blockers: bugs, security issues, data loss, broken contracts.
   - **suggestion** — meaningful improvements: design, performance, clearer APIs, missing tests.
   - **nitpick** — optional polish: naming, comments, minor style (only if valuable).

   Per item: location (file:line or symbol), issue, and concrete fix or alternative.

5. **Summary**  
   Short verdict: approve, approve with nits, or request changes. List top risks and what to verify manually (e.g. integration environment).

## Output template

```text
## Summary
<verdict and one-line rationale>

## Critical
- ...

## Suggestions
- ...

## Nitpicks
- ...
```
