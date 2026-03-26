---
name: gitlab-mr-create
description: >
  Creates GitLab merge requests with title, description, labels, reviewers, target
  branch, draft state, and optional MR dependencies (blocking MRs). Uses glab CLI
  or GitLab MCP. Aligns branch names and commit messages with repo profiles under
  profiles/. Use when pushing a feature branch and opening an MR, automating MR
  creation after commits, or when the user asks to open a draft or ready MR on GitLab.
tools: [shell, mcp]
mcps: [gitlab]
---

# GitLab merge request create

## When to Use

- Local branch is pushed and an MR must be opened (draft or ready).
- User specifies GitLab project, source branch, target branch, labels, or reviewers.
- Automation must link MRs as **blocking** dependencies (merge order / dependency graph).
- Need consistency with **repo profile** conventions (`profiles/<repo>.yaml`: default target branch, branch naming, commit format).

## Prerequisites

- Authenticated **glab** on the host that runs git (`glab auth status`) **or** GitLab MCP configured for the same instance.
- Remote URL or project path resolvable to the correct GitLab namespace/project.
- Source branch exists on the remote; commits follow the active repo profile if one applies.

## Instructions

1. **Load repo profile**  
   Before naming the branch or writing the MR title/description, read `profiles/<repo>.yaml` (or the closest match) for: default **target branch**, **branch prefix** patterns, **MR title** conventions, and **label** hints.

2. **Choose API path**  
   - Prefer **GitLab MCP** when the environment already uses it for MRs (read tool schemas first).  
   - Use **glab** when scripting on a shell host: `glab mr create` with explicit flags.

3. **Draft vs ready**  
   Open as **draft** while CI or review is pending; remove draft (`glab mr ready` or MCP update) only when the user or workflow says the MR is ready for merge.

4. **Create the MR**  
   Set explicitly:
   - **Title** — concise; match profile or team convention (e.g. ticket key prefix).
   - **Description** — summary, test plan, links to Jira/issue, breaking changes if any.
   - **Target branch** — from profile or user (often `main` / `master` / release branch).
   - **Labels** — space- or comma-separated per CLI/MCP API.
   - **Reviewers** — usernames or IDs as required by the API.

5. **MR dependencies (blocking)**  
   If GitLab version and API support **merge request dependencies** / related MRs as blockers:
   - Attach the **blocking** MR(s) so this MR cannot merge until they merge.
   - Document the dependency chain in the description (e.g. “Blocked by !123”).

6. **Verify**  
   Print or return the MR URL, IID, and state. Confirm target branch and draft flag match intent.

## Error Handling

- **403 / unauthorized**: Re-auth `glab` or MCP; never guess tokens.
- **Branch not found**: Confirm push completed and remote branch name matches (case-sensitive on some setups).
- **Duplicate MR**: If “already exists”, fetch existing MR via MCP/`glab mr view` and report URL instead of failing silently.
- **Dependencies API unavailable**: Put blocking relationships in the description and labels; note that formal dependency links could not be set.
