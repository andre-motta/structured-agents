---
name: gitlab-mr-takeover
description: >
  Takes over automation-opened GitLab merge requests: discovers MRs from Jira
  (or Slack when configured), fetches diffs, reviews changes, checks CI, pushes fixes to the MR branch,
  undrafts when appropriate, and confirms pipelines pass before reporting
  ready-to-merge. Encodes package-onboarding ordering (Builder, then Pipeline,
  then Probe). Use for package-automation-onboarded tickets, linked MR URLs in
  Jira, or when the user asks to continue or fix bot-created MRs.
tools: [shell, mcp]
mcps: [gitlab]
---

# GitLab MR takeover (automation MRs)

## When to Use

- **Package onboarding** workflow: labels like `package-automation-onboarded` or ticket text describes onboarding; automation may have opened MRs already.
- Jira contains **MR URLs** or references (or Slack, if `SLACK_BOT_TOKEN` is set); user wants progress without recreating MRs.
- Need to **fix CI**, address review comments, or **undraft** when work is complete.

## Prerequisites

- **jira-ticket-read** (or equivalent) to collect linked MR URLs from Jira when not pasted directly.
- Optional: **slack-channel-read** for MR links in notifications (only if `SLACK_BOT_TOKEN` is set).
- Git clone + push access to each MR source repo (e.g. the remote server); GitLab MCP or `glab` for MR/pipeline queries.
- Repo profile (`profiles/<repo>.yaml`) for branch naming, commits, and validation commands.

## Instructions

1. **Discover MRs**  
   - From Jira: issue links, development panel, description, child Stories.  
   - From Slack (only if `SLACK_BOT_TOKEN` is set): message text or thread containing `merge_requests/` or `!` IID links.  
   Deduplicate by project + IID.

2. **Order for package-onboarding**  
   Treat merge dependency as: **Builder MR → Pipeline (RHAI) MR → Probe test MR** (when all exist). Builder changes must merge before or with pipeline expectations; probe MR validates tests last. If only a subset exists (automation failure paths), process **Pipeline first** if it is the only MR, then Builder/Probe as they appear.

3. **Per MR: fetch state**  
   Via MCP or `glab mr view` / API: **title**, **description**, **source/target branch**, **draft**, **labels**, **pipeline status**, **diff** (or checkout branch and `git diff` to target).

4. **Review**  
   Skim diff for profile conventions, obvious bugs, and scope. Use **gitlab-mr-review** or **gitlab-pipeline-check** skills for depth when needed.

5. **CI**  
   If pipeline failed: identify failed jobs (see **gitlab-pipeline-check**), fix locally, commit per profile, **push to the MR source branch** (never a new MR unless the user asks).

6. **Undraft**  
   When fixes are pushed and pipeline is green (or acceptable per policy), remove draft status via MCP or `glab mr ready`.

7. **Exit criteria**  
   Before reporting **ready-to-merge**: latest pipeline **success** (or documented waiver); no unresolved blocking threads if review was requested; dependency MRs in the package-onboarding chain acknowledged in order.

8. **Report**  
   Structured summary: each MR link, branch, pipeline result, draft state, blockers, and recommended merge order.

## Error Handling

- **No MRs found**: Widen Jira search (and Slack if configured); ask user for URLs if automation did not link them.
- **Push rejected**: Check branch protection, fork workflow, and correct remote; do not force-push without explicit user approval.
- **Stale pipeline**: Trigger retry (`glab ci retry` or MCP) after push if the UI shows old SHA.
- **Permission denied on undraft**: Report; user may need to undraft manually or fix membership.
