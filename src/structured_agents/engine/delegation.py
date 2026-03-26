"""Sub-agent dispatch -- runs a single agent via the configured backend."""

from __future__ import annotations

import logging
import re
from collections.abc import Callable

from structured_agents.backends.base import AgentBackend
from structured_agents.config import Settings
from structured_agents.engine.prompt_assembler import assemble_system_prompt, assemble_user_prompt
from structured_agents.loaders import Registry
from structured_agents.log import log_agent_end, log_agent_start, log_tool_use
from structured_agents.models.context import AgentResult, PlanStep, RunContext

log = logging.getLogger(__name__)


def dispatch_agent(
    agent_name: str,
    *,
    task_description: str,
    step: PlanStep | None = None,
    run_context: RunContext,
    registry: Registry,
    settings: Settings,
    backend: AgentBackend,
    extra_context: str = "",
) -> AgentResult:
    """Run a single agent with assembled prompts and return the result.

    This is the main entry point for executing any agent in the system.
    It assembles prompts, invokes the backend, logs events, and returns results.
    """
    log_agent_start(agent_name, step_id=step.id if step else None)

    system_prompt = assemble_system_prompt(
        agent_name,
        registry=registry,
        settings=settings,
        dry_run=run_context.dry_run,
    )

    user_prompt = assemble_user_prompt(
        task_description=task_description,
        step=step,
        run_context=run_context,
        extra_context=extra_context,
    )

    event_handler = _make_event_handler(agent_name)

    # When running on the remote server itself, use the workspace as cwd so
    # that claude operates inside the repo checkout.  When running locally
    # (including Windows), cwd=None lets claude use its own default.
    # Note: sagent_workspace is a *remote* Linux path -- it must not be used
    # as a local cwd on Windows.
    from pathlib import Path

    agent_cwd: Path | None = None
    if settings.sagent_is_remote:
        agent_cwd = Path(settings.sagent_workspace)

    # Build allowed tools list -- claude -p runs headless, so MCP tools must
    # be pre-authorized via --allowedTools.  We use wildcard patterns like
    # "mcp__atlassian-jira__*" to allow all tools from each MCP server the
    # agent is configured to use.
    allowed_tools = _build_allowed_tools(agent_name, registry=registry)

    result = backend.run(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        agent_name=agent_name,
        allowed_tools=allowed_tools,
        cwd=agent_cwd,
        on_event=event_handler,
    )

    log_agent_end(
        agent_name,
        success=result.success,
        duration=result.duration_seconds,
        tokens=result.total_tokens,
    )

    result.artifacts.update(_extract_artifacts(result.output))

    # Persist prompts and raw output as artifacts so the workspace directory
    # contains a full audit trail of every agent invocation.
    result.artifacts["system_prompt.md"] = system_prompt
    result.artifacts["user_prompt.md"] = user_prompt
    result.artifacts["output.md"] = result.output

    return result


def _build_allowed_tools(agent_name: str, *, registry: Registry) -> list[str]:
    """Build the --allowedTools list for a headless claude -p invocation.

    Includes wildcard MCP tool patterns (e.g. ``mcp__atlassian-jira__*``) for
    every MCP server the agent is configured to use, so that headless mode
    does not block on permission prompts.
    """
    mcps = registry.get_agent_mcps(agent_name, include_optional=True)
    tools: list[str] = []
    for mcp in mcps:
        if mcp.available and mcp.type:
            # Claude Code names MCP tools as mcp__<server-name>__<tool>
            # The server name in .mcp.json matches mcp.type (e.g. "atlassian-jira")
            tools.append(f"mcp__{mcp.type}__*")
    if tools:
        log.debug("Allowed MCP tools for %s: %s", agent_name, tools)
    return tools


def _make_event_handler(agent_name: str) -> Callable[[dict], None]:
    """Create an event handler that logs tool use and other notable events."""

    def handler(event: dict) -> None:
        etype = event.get("type", "")

        if etype == "tool_use":
            tool_name = event.get("tool", {}).get("name", event.get("name", "unknown"))
            log_tool_use(tool_name, agent=agent_name)

        elif etype == "error":
            error = event.get("error", {})
            msg = error.get("message", str(error)) if isinstance(error, dict) else str(error)
            log.error("[%s] Backend error: %s", agent_name, msg)

    return handler


_FENCED_BLOCK_RE = re.compile(
    r"```(?:yaml|yml)\s*\n(.*?)```",
    re.DOTALL,
)

_ARTIFACT_RE = re.compile(
    r"<!-- artifact:(\S+) -->\s*\n```[^\n]*\n(.*?)```",
    re.DOTALL,
)


def _extract_artifacts(output: str) -> dict[str, str]:
    """Extract named artifacts from agent output.

    Agents can emit artifacts using:
        <!-- artifact:filename.ext -->
        ```
        content here
        ```
    """
    artifacts: dict[str, str] = {}
    for match in _ARTIFACT_RE.finditer(output):
        name = match.group(1)
        content = match.group(2).strip()
        artifacts[name] = content
        log.debug("Extracted artifact: %s (%d chars)", name, len(content))
    return artifacts


def extract_yaml_blocks(output: str) -> list[dict]:
    """Extract all YAML fenced code blocks from agent output."""
    import yaml

    blocks = []
    for match in _FENCED_BLOCK_RE.finditer(output):
        raw = match.group(1)
        try:
            parsed = yaml.safe_load(raw)
            if isinstance(parsed, dict):
                blocks.append(parsed)
        except yaml.YAMLError:
            continue
    return blocks
