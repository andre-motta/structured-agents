---
name: package-onboard
description: >
  Guides the AIPCC package onboarding workflow: onboarding-cli triggers pipelines
  that open MRs (Builder failure path, RHAI Pipeline always, Probe Test failure
  path), merge order Builder then Pipeline then Probe, and Jira Epic/Stories with
  labels and transitions. Use when onboarding a new package, tracking onboarding
  MRs, or reconciling Jira with GitLab onboarding automation.
tools: [shell, ssh, mcp]
mcps: [gitlab, jira]
---

# Package onboard (AIPCC)

## When to Use

- Starting or continuing **AIPCC package onboarding**.
- User mentions **onboarding-cli**, onboarding **pipelines**, or MR types (**Builder**, **RHAI Pipeline**, **Probe Test**).
- Need **Jira** structure (Epic, Stories, labels) aligned with **GitLab** MRs.

## Skill Discovery

Before onboarding a package, load repo-specific and shared skills:

1. **ai-helpers** (always available):
   - `${SAGENT_WORKSPACE}/ai-helpers/helpers/skills/python-packaging-complexity/SKILL.md`
     -- assess build complexity from PyPI metadata and suggest strategies.
   - `${SAGENT_WORKSPACE}/ai-helpers/helpers/skills/python-packaging-source-finder/SKILL.md`
     -- locate source repos for Python packages.
   - `${SAGENT_WORKSPACE}/ai-helpers/helpers/skills/python-packaging-license-checker/SKILL.md`
     -- check license compatibility with redistribution.
   - `${SAGENT_WORKSPACE}/ai-helpers/helpers/skills/python-packaging-env-finder/SKILL.md`
     -- discover build-time environment variables from setup/CMake configs.
   - `${SAGENT_WORKSPACE}/ai-helpers/helpers/skills/python-packaging-bug-finder/SKILL.md`
     -- find known packaging bugs, fixes, and workarounds via GitHub issues.

2. **Repo-specific skills**:
   - `${SAGENT_WORKSPACE}/builder/.claude/skills/package-settings/SKILL.md`
     -- generate package settings for the AIPCC wheels builder.
   - `${SAGENT_WORKSPACE}/builder/.claude/skills/prebuilt-package/SKILL.md`
     -- configure pre-built wheels that cannot be built from source.
   - `${SAGENT_WORKSPACE}/builder/AGENTS.md`
     -- builder repo conventions and plugin system.
   - `${SAGENT_WORKSPACE}/wheels-test/.claude/skills/probe-test-creator/SKILL.md`
     -- create probe tests for new packages in wheels-test.
   - `${SAGENT_WORKSPACE}/selfservice/.claude/skills/testing-builds/SKILL.md`
     -- test builds via self-service CLI and GitLab pipelines.

3. Load all available skills from the lists above, then **follow their
   instructions for the relevant phase** of onboarding. Supplement with the
   generic steps below for workflow orchestration and anything not covered.

## Generic Instructions (fallback)

1. **Automation flow**  
   **onboarding-cli** kicks off the pipeline that creates or updates **merge requests**. Do not assume manual MR creation is the source of truth unless the user says so.

2. **MR types**  
   - **Builder** — opened on **failure** path when builder integration needs fixes.  
   - **RHAI Pipeline** — **always** part of the flow (pipeline definition/integration).  
   - **Probe Test** — opened on **failure** path when probe validation fails.

3. **Merge ordering (blocking)**  
   Merge in this order:
   1. **Builder** first — **blocking**; downstream work assumes builder state is correct.  
   2. **RHAI Pipeline** second — after Builder is merged.  
   3. **Probe Test** third — after Pipeline is in good shape.

   When using GitLab MCP or UI, respect **MR dependencies** / description notes so reviewers see the chain.

4. **Jira structure**  
   - **Epic** for the onboarding initiative; **child Stories** for concrete deliverables (builder, pipeline, probe, docs).  
   - Apply team **labels** and keep **lifecycle transitions** accurate (e.g. In Progress → Done) as work lands on default branch.

5. **Operational steps**  
   Use **shell/ssh** for CLI (`onboarding-cli`, git status on the remote server). Use **GitLab MCP** to list MR state, pipelines, and links. Use **Jira MCP** to create/update Epic/Stories, set labels, and transition issues.

6. **Status reporting**  
   Summarize: which MRs exist, merge order satisfied or not, open blockers, and Jira keys with current state.

## Error Handling

- **MCP auth**: Complete auth per server instructions before mutating GitLab/Jira.
- **Partial pipeline**: Identify which MR type failed and whether Builder must be fixed before rerunning later stages.
