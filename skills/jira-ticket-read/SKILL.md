---
name: jira-ticket-read
description: >
  Retrieves full Jira issue context for a given key or URL: summary, description,
  type, status, labels, components, links, merge requests, and child work items.
  For Epics, loads child Stories with statuses and links. Use when the user names
  a ticket (e.g. PROJ-123), pastes a Jira link, asks what an Epic contains, or needs
  linked MRs and subtasks before coding or updating Jira.
tools: [mcp]
mcps: [jira]
---

# Jira ticket read

## When to Use

- User provides a Jira issue key, URL, or asks to "look up" / "read" / "summarize" a ticket.
- Planning or implementation requires linked issues, MRs, children, or Epic scope.
- Need authoritative status, labels, components, and description from Jira (not guesses).

## Skill Discovery

Before reading Jira tickets, load the shared activity summarizer:

1. **ai-helpers** (always available):
   - `${SAGENT_WORKSPACE}/ai-helpers/helpers/skills/jira-activity/SKILL.md`
     -- summarizes Jira ticket activity including children, spotting stale work
     and providing a broader activity picture. Useful when the user asks for
     Epic-level summaries or backlog triage.

2. If the ai-helpers skill is found and the task involves summarizing activity
   or triaging, **follow its instructions first**. Supplement with the generic
   steps below for anything not covered.

## Prerequisites

- Jira MCP server enabled and authenticated for the target site/project.
- Issue key or URL (or enough context to resolve the key, e.g. project + summary search via MCP if allowed).

## Generic Instructions (fallback)

1. **Resolve the issue key**  
   If the user gave a URL, extract the issue key (e.g. `PROJ-123`). If only a title is given, use Jira MCP search tools (if available) to find the key; confirm with the user if multiple matches.

2. **Read the MCP tool schema**  
   Before calling tools, read the Jira MCP tool descriptors (parameters and return shapes) so you use the correct operation names and fields.

3. **Fetch core issue fields**  
   Request at minimum: **summary**, **description**, **issuetype**, **status**, **labels**, **components**.  
   Also capture **priority**, **assignee**, **reporter**, and **created/updated** if exposed.

4. **Linked issues**  
   Retrieve outward/inward issue links (e.g. "blocks", "is blocked by", "relates to", duplicates). Normalize into a short list: link type, direction, linked key, linked summary/status if returned.

5. **Linked merge requests**  
   If the MCP or Jira integration exposes dev/MR links (e.g. GitLab/GitHub), fetch and list MR URLs, titles, and states. If only a generic "development" panel exists, pull whatever structured MR metadata the API returns.

6. **Child tickets**  
   Fetch sub-tasks and any child issues returned by the API. Include key, type, summary, status.

7. **Epics: child Stories**  
   If **issuetype** is Epic (or equivalent):

   - Use Jira MCP search or hierarchy tools to list **all Stories (and Tasks if relevant)** under that Epic.
   - For each child: key, summary, status, and links to MRs or parent if available.
   - Note ordering if the API provides rank or Epic relationship order.

8. **Present results**  
   Summarize in markdown: header with key + summary + status; then sections for Description (trimmed if huge), Labels, Components, Links, MRs, Children/Epic children. Flag missing data ("not returned by API") instead of inventing it.

## Error Handling

- **Permission or 404**: Report clearly; do not fabricate ticket content. Suggest checking project access or key spelling.
- **Partial MCP responses**: Return what you got; list fields that were unavailable.
- **Rate limits / timeouts**: Retry once with backoff if appropriate; otherwise summarize partial data and state the failure.
- **Ambiguous key**: Ask the user to confirm the issue key before treating search hits as definitive.
