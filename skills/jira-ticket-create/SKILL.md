---
name: jira-ticket-create
description: >
  Creates new Jira Stories or sub-tasks under an existing Epic using Jira MCP,
  setting summary, description, type, labels, Epic/parent link, issue links
  (e.g. blocked-by), and story sizing (S/L/XL). Use when the user asks to open
  a ticket under an Epic, split work into sub-tasks, or file a Story with
  explicit dependencies and sizing.
tools: [mcp]
mcps: [jira]
---

# Jira ticket create

## When to Use

- User names an Epic (or parent) and wants new Stories or sub-tasks underneath.
- Need a ticket with labels, **blocked-by** / **blocks** links, and size metadata.
- Bulk or single create is acceptable as long as each issue has a clear parent Epic when required by process.

## Skill Discovery

Before creating Jira tickets, load the shared AIPCC Jira skill:

1. **ai-helpers** (always available):
   - `${SAGENT_WORKSPACE}/ai-helpers/helpers/skills/jira-aipcc-create/SKILL.md`
     -- AIPCC-specific Jira issue creation with project conventions, user
     confirmation workflow, and field defaults. **Load and follow this skill
     first** when creating AIPCC project issues.

2. If the ai-helpers skill is found and the target project is AIPCC,
   **follow its instructions first**. Supplement with the generic steps below
   for non-AIPCC projects or anything not covered.

## Prerequisites

- Jira MCP authenticated; **project key** or default create context known.
- **Parent Epic key** (or Story for sub-tasks) and required **issue type** names as configured in Jira (e.g. "Story", "Sub-task").
- Optional: list of labels, blocked-by keys, and size (S, L, XL).

## Generic Instructions (fallback)

1. **Read MCP create schema**  
   Open Jira MCP descriptors for create-issue (and link-issue if separate). Note required fields for the target project (e.g. Epic Link custom field id, parent for sub-tasks).

2. **Resolve Epic/parent**  
   Confirm the Epic (or parent Story) key exists and is the correct container. If the user gave a name only, search via MCP and confirm the key.

3. **Build the payload**  
   Set:

   - **summary**: Short, imperative or outcome-focused.
   - **description**: Markdown or ADF as required by the API/MCP; include acceptance criteria if the user provided them.
   - **issuetype**: `Story` or `Sub-task` (use exact names from the project).
   - **Parent/Epic link**: Use the field your Jira instance uses (`Epic Link`, `parent`, etc.) per MCP docs.

4. **Issue links**  
   If the user specifies **blocked-by** (or blocks):

   - Create the issue first, then add links with the MCP link tool, **or** use a single create payload if the MCP supports `issuelinks` on create.
   - Use the correct link type name from Jira (e.g. "Blocks" / "is blocked by").

5. **Labels**  
   Apply any user-requested labels. For package work, align with existing team conventions (see `jira-ticket-update` for standard package lifecycle label names if relevant).

6. **Sizing (S / L / XL)**  
   Map to the project's story-point or size field:

   - If a numeric story-points field exists, map S/L/XL only when the user or team doc defines the mapping; otherwise set a **labels** or **custom field** if that is how sizing is stored.
   - Never invent numeric points without user or team rules.

7. **Create and return**  
   Call create; return the new **issue key** and URL if available. If multiple issues were created, list all keys.

## Error Handling

- **Missing required field**: Read the project's create metadata from MCP/API; ask the user for mandatory fields (e.g. Component, Fix Version).
- **Invalid Epic/parent**: Do not create orphan issues if process requires an Epic—stop and clarify.
- **Duplicate summary**: If search shows a likely duplicate, warn the user and ask before creating.
- **Link type errors**: Fetch allowed link types; retry with the exact type name Jira expects.
