# Structured Agents -- Cursor Workflow Guide

This file documents how to replicate the structured-agents orchestration flow
manually inside Cursor (or any chat-based IDE), without the Python CLI.

The Python CLI (`structured-agents run TICKET-123`) automates this entire flow
via Claude Code. This guide lets you achieve the same results interactively.

## Prerequisites

1. MCP servers configured: `make mcp-config WORKSPACE=/path/to/workspace`
2. Environment variables set in `.env` (see `.env.example`)
3. Familiarity with the agent/skill/profile definitions in this repo

## The Four Phases

### Phase 1: Intake

1. Open `agents/orchestrator/AGENT.md` -- this is your system context
2. Include `skills/jira-ticket-read/SKILL.md` as additional context
3. Ask the orchestrator to read your ticket:

   > Read Jira ticket AIPCC-12095. Classify the workflow type and list all
   > linked MRs and child tickets.

4. The orchestrator will use the Jira MCP to fetch ticket details and classify
   the work as one of: package-onboarding, dependency-update, feature, bugfix,
   probe-test, adr, container, investigation, infra.

### Phase 2: Planning

1. Open `agents/planner/AGENT.md` as system context
2. Include all skills listed in `agents/planner/agent.yaml` -> `skills:`
3. Paste the intake results and ask for a plan:

   > Based on this ticket (paste intake output), create an execution plan.
   > List the steps, which agent handles each, and the dependencies.

4. The planner produces a structured plan with ordered steps.

### Phase 3: Execution

For each step in the plan:

1. Open the agent's `AGENT.md` (e.g., `agents/coder/AGENT.md`)
2. Include the skills listed in that agent's `agent.yaml`
3. Include relevant repo profiles from `profiles/`
4. Pass the task description and any context from prior steps
5. Let the agent execute (it will use MCP tools, SSH, etc.)
6. Capture the result for the next step

### Phase 4: Report

1. Return to the orchestrator (`agents/orchestrator/AGENT.md`)
2. Pass all step results
3. Ask for a final report and Jira update

## Quick Reference: Agent -> Skills Mapping

Open `agents/<name>/agent.yaml` to see which skills each agent needs.
The `skills:` field lists required skills; `optional_skills:` lists those
that depend on environment variables (e.g., Slack).

## Dry Run

Add this constraint to every prompt:

> This is a DRY RUN. Do not create, merge, or modify any MRs/PRs.
> Do not modify Jira tickets. Do not post to Slack.
> Read and analyze only. Describe what you WOULD do.

## Tips

- Use `structured-agents show <agent>` to see the full assembled prompt
  (useful for copying into Cursor chat)
- Use `structured-agents list` to see all available agents, skills, and profiles
- Use `structured-agents validate` to check definitions for errors
- The `profiles/` directory contains repo-specific knowledge (conventions,
  key files, workflows) -- include relevant profiles when working with
  specific repositories
