---
name: jira-ticket-update
description: >
  Updates existing Jira issues via MCP: comments, workflow transitions, labels,
  and arbitrary fields. Uses a structured markdown comment template (progress, MRs,
  next steps). Handles common transitions (To Do → In Progress → In Review → Done)
  and package-lifecycle labels. Use when the user asks to comment on, transition,
  or relabel a Jira ticket, or to record MR/pipeline progress on an issue.
tools: [mcp]
mcps: [jira]
---

# Jira ticket update

## When to Use

- Add a comment, change status, or edit labels/fields on a known issue key.
- Record progress after an MR, review, or pipeline outcome.
- Apply package onboarding lifecycle labels consistently.

## Prerequisites

- Jira MCP enabled; credentials must allow transitions and edits on the issue.
- Target **issue key** and intended **outcome** (comment only vs transition vs field change).

## Instructions

1. **Read MCP schemas**  
   Inspect Jira MCP tools for: add/update comment, transition issue, edit issue fields, and available transitions for the issue.

2. **Load current state**  
   Fetch current status, labels, and (if needed) allowed transitions so you do not repeat invalid operations.

3. **Comments: structured markdown**  
   When adding a comment, use this shape (adjust headings if the tool strips markdown—keep the same sections in plain text if needed):

   ```markdown
   ## Progress
   - …

   ## MR links
   - …

   ## Next steps
   - …
   ```

   Keep bullets factual; paste full MR URLs. Omit empty sections.

4. **Transitions**  
   Prefer this path when it matches the project's workflow names (map to actual transition **names** or **IDs** from the API):

   - **To Do** → **In Progress** → **In Review** → **Done**

   If names differ slightly (e.g. "In Development"), use the transition list returned by Jira for that issue. Never assume a transition exists without checking.

5. **Labels**  
   To add or remove labels, use the MCP edit-labels or update-issue operation as documented.

   **Package lifecycle** (add when applicable; remove only if the user explicitly asks):

   - `package-automation-onboarded`
   - `package-pipeline-onboarded`
   - `package-probe-tests-created`
   - `package-autoqa-passed`

6. **Other fields**  
   Set custom or standard fields only when the user requests them and the MCP exposes writable field IDs. Confirm destructive changes (e.g. clearing assignee) with the user if ambiguous.

7. **Verify**  
   After updates, re-read the issue (or rely on MCP success payload) and confirm status, labels, and latest comment match intent.

## Error Handling

- **Transition not available**: Report current status and list valid transitions from the API; ask the user which one to use or fix workflow config.
- **Permission denied**: State that edits failed; do not claim the ticket was updated.
- **Concurrent edits**: If a field conflict occurs, re-fetch the issue and retry only the failed field with the user's direction.
- **Label typos**: Use exact strings listed above for package lifecycle labels.
