---
name: gitlab-pipeline-check
description: >
  Checks GitLab CI pipeline status for a project, branch, commit, or merge request;
  retrieves failed job logs; classifies failures (tests, lint, build, timeout,
  infra); returns structured status, failed jobs, and reasons. Use when debugging
  CI, before merge, after push, or when the user asks if the pipeline is green.
tools: [mcp, shell]
mcps: [gitlab]
---

# GitLab pipeline check

## When to Use

- After push or MR update: confirm **latest pipeline** for the relevant **SHA** or **MR**.
- CI is red: need **which jobs failed** and **why** without clicking through the UI.
- Compare pipeline state across **package-onboarding** MRs (Builder / Pipeline / Probe).

## Skill Discovery

Before debugging pipelines, load the shared pipeline debugger:

1. **ai-helpers** (always available):
   - `${SAGENT_WORKSPACE}/ai-helpers/helpers/skills/gitlab-pipeline-debugger/SKILL.md`
     -- comprehensive GitLab CI debugging, monitoring, log analysis, and
     troubleshooting workflows. **Load and follow this skill first** when
     it exists; it provides richer pipeline introspection than the generic
     steps below.

2. If the ai-helpers skill is found, **follow its instructions first**.
   Supplement with the generic steps below for anything not covered.

## Prerequisites

- Project path (`namespace/project`) or resolvable MR URL.
- Commit SHA, branch name, or MR IID to identify the pipeline (default: **latest** on MR head or branch tip).
- GitLab MCP or `glab ci view` / `glab ci trace` / API access.

## Generic Instructions (fallback)

1. **Read tool schemas**  
   Use GitLab MCP descriptors for pipeline and job APIs; note pagination for many jobs.

2. **Resolve pipeline**  
   - **MR**: fetch MR’s `head_pipeline` / `sha` and associated pipelines.  
   - **Branch**: latest pipeline on branch.  
   - **SHA**: exact pipeline for that commit.  
   Prefer the pipeline that matches the **current MR diff** (not an older detached run).

3. **Record status**  
   Capture: `id`, `status` (`success`, `failed`, `running`, `pending`, `canceled`, `skipped`), `ref`, `sha`, **web URL**.

4. **Failed jobs**  
   List jobs with `failed` or `canceled` (if user cares about cancellations). For each: **name**, **stage**, **failure_message** if present, **duration**.

5. **Logs**  
   For failed jobs, fetch **trace/log** via MCP or `glab ci trace <job-id>`. Pull enough tail to capture the error (last 200–400 lines if huge).

6. **Classify failure** (heuristic)  
   - **Tests**: `FAILED`, `AssertionError`, pytest/junit summaries, nonzero test exit.  
   - **Lint/format**: `ruff`, `flake8`, `black`, `mypy`, `eslint` in log header.  
   - **Build**: compiler errors, missing headers, Docker build step failure.  
   - **Timeout**: runner killed, `no space`, job exceeded time.  
   - **Infra/registry**: 5xx, pull image errors, DNS, artifact upload failures.

7. **Structured report**  
   Return:

   ```yaml
   pipeline_status: ...
   sha: ...
   url: ...
   failed_jobs:
     - name: ...
       stage: ...
       reason_summary: ...
   ```

   Add a short human paragraph with the **primary** failure and next action.

## Error Handling

- **No pipeline**: Report “none found” for that ref/SHA; suggest verifying push or MR refresh delay.
- **Running/pending**: State status; optionally poll once after a short wait if the user asked for final result.
- **Log fetch denied**: Report job name and URL only; suggest manual log view.
- **Multiple pipelines**: Prefer **MR pipeline** over **branch** pipeline when both exist; say which was chosen.
