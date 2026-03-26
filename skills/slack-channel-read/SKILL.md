---
name: slack-channel-read
description: >
  Reads Slack channel history via Slack MCP to find merge request links, package
  onboarding messages, build/pipeline outcomes, and mentions of ticket IDs or
  package names. Use when the user points to a Slack channel, asks what was posted
  about a package or Jira key, or needs MR URLs and CI status from team chatter.
tools: [mcp]
mcps: [slack]
---

# Slack channel read

## When to Use

**This skill is optional.** Only use it when `SLACK_BOT_TOKEN` is set in the environment. If the variable is not configured, skip this skill entirely and rely on Jira links for MR discovery instead.

When available:
- Discover **MR links**, **onboarding notifications**, or **pipeline/build status** from a channel thread or timeline.
- Search channel history for a **package name**, **repository**, or **Jira key** (e.g. `PROJ-123`).
- Summarize recent relevant messages without asking humans to paste logs manually.

## Prerequisites

- `SLACK_BOT_TOKEN` environment variable must be set (if unset, do not attempt to use this skill)
- Slack MCP enabled; the agent's workspace must have access to the **channel ID or name** the user specifies.
- Optional: time window, package string, or ticket ID to narrow the read.

## Instructions

1. **Read Slack MCP tool schemas**  
   Identify tools for listing channels, reading history, searching messages, and fetching threads. Note limits (pagination, oldest/latest, result caps).

2. **Resolve the channel**  
   If the user gives a name (e.g. `#eng-releases`), resolve to channel ID via MCP list/search. Confirm the channel is the intended one (similar names exist).

3. **Define scope**  
   Prefer a bounded window (e.g. last 7 days or since a given date) unless the user needs full history. For threads, fetch the full thread when a hit is inside a reply chain.

4. **Search strategy**  
   - For **package names**: match case-insensitively; include common variants (hyphen vs underscore, scoped npm names if mentioned).
   - For **ticket IDs**: match `\b[A-Z][A-Z0-9]+-\d+\b`.
   - For **MRs**: match URLs containing merge requests paths (GitLab/GitHub patterns) and bare `!123` / `#123` references if your org uses them—disambiguate with surrounding text.

5. **Extract structured data**  
   From matching messages, produce:

   | Field | Notes |
   |--------|--------|
   | MR URLs | Full `https://…` links |
   | Build / pipeline | Pass/fail, job name, link if present |
   | Package / service | Name as stated in message |
   | Jira keys | Keys found in same message or thread |
   | Timestamp / author | For traceability |

   Deduplicate identical links across messages; keep the most recent status if contradictory—note the conflict briefly.

6. **Report**  
   Output a short markdown summary: what was searched, how many messages matched, then bullet list of extracted MRs and statuses. Quote sparingly (one line per finding unless the user asked for full quotes).

## Error Handling

- **Channel not found / not in workspace**: Say so clearly; ask for channel ID or invite/access clarification.
- **MCP rate limits or empty history**: Widen the time window slightly once, or ask the user for a narrower keyword.
- **Ambiguous MR references**: List candidates and ask which repo/MR if multiple projects share numbering.
- **Sensitive content**: Do not exfiltrate secrets; summarize presence of tokens/passwords as "[redacted]" if accidentally visible in API output.
