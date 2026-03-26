"""Build system and user prompts from agent definitions, skills, and profiles."""

from __future__ import annotations

import logging
import os
from io import StringIO

import yaml

from structured_agents.config import Settings
from structured_agents.loaders import Registry
from structured_agents.models.context import AgentResult, PlanStep, RunContext

log = logging.getLogger(__name__)

_ENV_KEYS_FOR_AGENTS = [
    "SAGENT_WORKSPACE",
    "SAGENT_SSH_HOST",
    "SAGENT_SSH_USER",
    "SAGENT_SSH_KEY",
    "SAGENT_SSH_PORT",
    "SAGENT_IS_REMOTE",
]


def assemble_system_prompt(
    agent_name: str,
    *,
    registry: Registry,
    settings: Settings,
    dry_run: bool = False,
) -> str:
    """Build a complete system prompt for the given agent.

    Assembles: AGENT.md + available skills + repo profiles + environment + constraints.
    """
    agent = registry.agents.get(agent_name)
    if not agent:
        raise ValueError(f"Unknown agent: {agent_name}")

    buf = StringIO()

    # --- Agent identity and instructions ---
    buf.write(agent.system_prompt)
    buf.write("\n\n")

    # --- Available skills ---
    skills = registry.get_agent_skills(agent_name)
    optional_skills = _resolve_optional_skills(agent_name, registry=registry, settings=settings)
    all_skills = skills + optional_skills

    if all_skills:
        buf.write("---\n\n## Available Skills\n\n")
        for skill in all_skills:
            buf.write(f"### {skill.name}\n\n")
            if skill.instructions:
                buf.write(skill.instructions)
                buf.write("\n\n")
            else:
                buf.write(f"{skill.description}\n\n")

    # --- Sub-agents (brief info for the orchestrator/planner) ---
    if agent.sub_agents:
        buf.write("---\n\n## Available Sub-Agents\n\n")
        for sa_name in agent.sub_agents:
            sa = registry.agents.get(sa_name)
            if sa:
                buf.write(f"- **{sa.name}**: {sa.description.strip()}\n")
                if sa.capabilities:
                    buf.write(f"  Capabilities: {', '.join(sa.capabilities)}\n")
        buf.write("\n")

    # --- Repository profiles ---
    profiles = registry.get_agent_profiles(agent_name)
    if profiles:
        buf.write("---\n\n## Repository Profiles\n\n")
        for prof in profiles:
            buf.write(f"### {prof.name}\n\n")
            buf.write(f"- **URL**: {prof.url}\n")
            buf.write(f"- **Language**: {prof.language}\n")
            buf.write(f"- **Platform**: {prof.platform}\n")
            buf.write(f"- **Local path**: {prof.local_path}\n")
            if prof.key_files:
                buf.write(f"- **Key files**: {', '.join(prof.key_files)}\n")
            if prof.conventions.testing:
                buf.write(f"- **Testing**: {prof.conventions.testing}\n")
            if prof.conventions.branch_naming:
                buf.write(f"- **Branch naming**: {prof.conventions.branch_naming}\n")
            if prof.workflows:
                buf.write("- **Workflows**:\n")
                for wf in prof.workflows:
                    buf.write(f"  - {wf.name}: {wf.description}\n")
            buf.write("\n")

    # --- MCP availability ---
    mcps = registry.get_agent_mcps(agent_name, include_optional=True)
    available_mcps = [m for m in mcps if m.available]
    if available_mcps:
        buf.write("---\n\n## Available MCP Servers\n\n")
        for mcp in available_mcps:
            buf.write(f"- **{mcp.name}** ({mcp.type}): {mcp.description.strip()}\n")
            if mcp.capabilities:
                buf.write(f"  Capabilities: {', '.join(mcp.capabilities)}\n")
        buf.write("\n")

    # --- Environment ---
    buf.write("---\n\n## Environment\n\n")
    buf.write("```\n")
    for key in _ENV_KEYS_FOR_AGENTS:
        val = os.environ.get(key, "")
        if val:
            buf.write(f"{key}={val}\n")
    buf.write("```\n\n")

    # --- Dry-run constraints ---
    if dry_run:
        buf.write("---\n\n## CONSTRAINTS (DRY RUN)\n\n")
        buf.write(
            "**This is a DRY RUN.** You MUST NOT:\n"
            "- Create, merge, or modify any merge requests / pull requests\n"
            "- Push any branches to remote repositories\n"
            "- Modify any Jira tickets (no comments, transitions, or updates)\n"
            "- Post to Slack or any external service\n"
            "- Make any changes that cannot be undone locally\n\n"
            "You MAY:\n"
            "- Read from Jira, GitLab, GitHub, and Slack\n"
            "- Explore code on the filesystem\n"
            "- Create local files in the workspace\n"
            "- Produce plans, diffs, and reports as artifacts\n\n"
            "When you would normally take an external action, describe what you WOULD do "
            "and produce the artifact (diff, comment text, etc.) without executing it.\n"
        )

    prompt = buf.getvalue()
    log.debug("Assembled system prompt for %s: %d chars", agent_name, len(prompt))
    return prompt


def assemble_user_prompt(
    *,
    task_description: str,
    step: PlanStep | None = None,
    run_context: RunContext | None = None,
    extra_context: str = "",
) -> str:
    """Build a user prompt for a specific agent invocation.

    Includes the task description, step inputs, and summaries of prior results.
    """
    buf = StringIO()

    buf.write(f"## Task\n\n{task_description}\n\n")

    if step and step.inputs:
        buf.write("## Inputs\n\n```yaml\n")
        buf.write(yaml.dump(step.inputs, default_flow_style=False))
        buf.write("```\n\n")

    if run_context and run_context.results:
        completed = {
            sid: r for sid, r in run_context.results.items() if r.success
        }
        if completed:
            buf.write("## Context from Previous Steps\n\n")
            for sid, result in completed.items():
                summary = _summarize_result(result)
                buf.write(f"### Step: {sid} ({result.agent})\n\n{summary}\n\n")

    if extra_context:
        buf.write(f"## Additional Context\n\n{extra_context}\n\n")

    if run_context and run_context.dry_run:
        buf.write(
            "\n**REMINDER: This is a DRY RUN. "
            "Read and analyze only. Do not make external changes.**\n"
        )

    prompt = buf.getvalue()
    log.debug("Assembled user prompt: %d chars", len(prompt))
    return prompt


def _resolve_optional_skills(
    agent_name: str,
    *,
    registry: Registry,
    settings: Settings,
) -> list:
    """Return optional skills whose required env vars are set."""
    agent = registry.agents.get(agent_name)
    if not agent:
        return []

    result = []
    for skill_name in agent.optional_skills:
        skill = registry.skills.get(skill_name)
        if not skill:
            continue
        for mcp_name in skill.mcps:
            mcp = registry.mcps.get(mcp_name)
            if mcp and mcp.optional and mcp.required_env:
                if not os.environ.get(mcp.required_env):
                    log.debug("Skipping optional skill %s (missing %s)", skill_name, mcp.required_env)
                    break
        else:
            result.append(skill)
    return result


def _summarize_result(result: AgentResult, max_len: int = 2000) -> str:
    """Create a concise summary of an agent result for context passing."""
    output = result.output.strip()
    if len(output) > max_len:
        output = output[:max_len] + "\n\n... (truncated)"

    if result.artifacts:
        artifacts_info = ", ".join(result.artifacts.keys())
        output += f"\n\nArtifacts produced: {artifacts_info}"

    return output
