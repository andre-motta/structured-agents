---
name: gitlab-mr-review
description: >
  Reviews a GitLab merge request: loads the diff, checks conventions against repo
  profile, inspects CI pipeline status, posts review comments via GitLab MCP, and
  returns a structured verdict (LGTM or needs-fixes with specifics). Use when the
  user asks for an MR review, before merge approval, or when automation must
  comment on a specific !IID or MR URL.
tools: [mcp, shell]
mcps: [gitlab]
---

# GitLab merge request review

## When to Use

- User provides MR URL, project + IID, or branch pair and asks for code review.
- Pre-merge gate: reviewer agent or human wants a concise, actionable assessment.
- Need **inline or general** feedback recorded **on the MR** (not only chat).

## Prerequisites

- GitLab MCP enabled **or** `glab` + local checkout for diff if MCP is read-only.
- Target **project path** and **MR IID** (or parse from URL).
- Optional: `profiles/<repo>.yaml` for lint/test/commit conventions to check against.

## Instructions

1. **Read MCP tool schemas**  
   Confirm how to fetch MR details, diffs, discussions, and create notes/comments.

2. **Fetch MR metadata**  
   Title, description, author, labels, target branch, draft state, **pipeline status**, and **commit count / SHA**.

3. **Fetch and analyze diff**  
   Prefer unified diff from API/MCP. Categorize changes: logic, tests, config, CI, docs. Flag risky patterns (secrets, broad `except`, API breaks, missing tests for new behavior).

4. **Convention check**  
   Against repo profile and obvious project norms: file layout, naming, typing, error handling, changelog fragments if required.

5. **CI**  
   If pipeline failed or pending, state job names and link to logs; do not claim LGTM on red pipelines unless the user scoped “code-only” review.

6. **Post review on GitLab**  
   Use MCP to add a **summary comment** (and inline comments on specific lines if the API supports line-level notes). Keep comments factual and respectful. Include:
   - Verdict line: **LGTM** or **Needs fixes**
   - Bullet list of **must-fix** vs **nits**
   - **Pipeline** one-liner
   - Optional **suggested follow-ups** (non-blocking)

7. **Structured output (for agents)**  
   Emit a short machine-friendly block, for example:

   ```yaml
   verdict: lgtm | needs-fixes
   pipeline: passed | failed | pending | skipped
   must_fix: []
   nits: []
   ```

## Error Handling

- **Cannot post comments** (read-only token): Still return structured review in chat; state that GitLab comments were skipped.
- **Large MR**: Summarize by file/module; focus on changed hunks; mention if review is sample-based due to size.
- **Diff unavailable**: Fall back to `git fetch` + `git diff` on a workspace clone if allowed; otherwise report the blocker.
