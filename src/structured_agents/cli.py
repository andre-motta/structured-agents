"""CLI entry point for structured-agents."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import click
from rich.table import Table

from structured_agents.config import Settings, load_settings
from structured_agents.log import console, get_logger, log_phase, print_run_summary, setup_logging

log = get_logger("cli")


@click.group()
@click.version_option()
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
@click.option("--repo-root", type=click.Path(exists=True, path_type=Path), default=None, help="Path to structured-agents repo root")
@click.pass_context
def main(ctx: click.Context, verbose: bool, repo_root: Path | None) -> None:
    """Structured Agents - hierarchical multi-agent orchestration."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["repo_root"] = repo_root


@main.command()
@click.argument("ticket_id")
@click.option("--context", "-c", default=None, help="Additional context for the agent")
@click.option("--dry-run", "-n", is_flag=True, help="Read and plan only, don't make external changes")
@click.option("--agent", "-a", default=None, help="Run a single agent instead of full orchestration")
@click.option("--timeout", "-t", default=600, type=int, help="Per-agent timeout in seconds")
@click.option("--log-dir", type=click.Path(path_type=Path), default=None, help="Override log output directory")
@click.pass_context
def run(
    ctx: click.Context,
    ticket_id: str,
    context: str | None,
    dry_run: bool,
    agent: str | None,
    timeout: int,
    log_dir: Path | None,
) -> None:
    """Run the agent system against a Jira ticket."""
    from structured_agents.backends.claude_code import ClaudeCodeBackend
    from structured_agents.engine.orchestrator import execute_run
    from structured_agents.engine.workspace import RunWorkspace
    from structured_agents.loaders import load_registry

    verbose = ctx.obj.get("verbose", False)
    repo_root = ctx.obj.get("repo_root")

    try:
        settings = load_settings(repo_root=repo_root)
    except Exception as exc:
        console.print(f"[failure]Failed to load settings: {exc}[/failure]")
        console.print("Make sure .env exists with required variables. See .env.example.")
        sys.exit(1)

    base_dir = log_dir or settings.repo_root

    workspace = RunWorkspace.create(
        base_dir=base_dir,
        ticket_id=ticket_id,
        dry_run=dry_run,
        additional_context=context or "",
    )

    root_logger = setup_logging(verbose=verbose, log_file=workspace.log_file)

    log.info("Run ID: %s", workspace.context.run_id)
    log.info("Ticket: %s", ticket_id)
    log.info("Dry run: %s", dry_run)
    log.info("Workspace: %s", workspace.run_dir)

    registry = load_registry(settings.repo_root)

    backend = ClaudeCodeBackend()
    if not backend.check_available():
        console.print(
            "[failure]Claude Code CLI not found.[/failure]\n"
            "Install it from https://docs.anthropic.com/en/docs/claude-code\n"
            "or ensure 'claude' is on your PATH."
        )
        sys.exit(1)

    if agent:
        _run_single_agent(
            agent_name=agent,
            ticket_id=ticket_id,
            context=context,
            dry_run=dry_run,
            settings=settings,
            registry=registry,
            backend=backend,
            workspace=workspace,
        )
    else:
        _run_full_orchestration(
            ticket_id=ticket_id,
            context=context,
            dry_run=dry_run,
            settings=settings,
            registry=registry,
            backend=backend,
            workspace=workspace,
        )


def _run_full_orchestration(
    *,
    ticket_id: str,
    context: str | None,
    dry_run: bool,
    settings: Settings,
    registry: "Registry",
    backend: "AgentBackend",
    workspace: "RunWorkspace",
) -> None:
    """Execute the full 4-phase orchestration loop."""
    from structured_agents.engine.orchestrator import execute_run

    start = time.monotonic()

    run_ctx = execute_run(
        ticket_id,
        dry_run=dry_run,
        additional_context=context or "",
        settings=settings,
        registry=registry,
        backend=backend,
        workspace=workspace,
    )

    total_duration = time.monotonic() - start

    steps_summary = []
    for sid, res in run_ctx.results.items():
        steps_summary.append({
            "id": sid,
            "agent": res.agent,
            "status": "OK" if res.success else "FAILED",
            "success": res.success,
            "duration": res.duration_seconds,
            "tokens": res.total_tokens,
        })

    print_run_summary(
        ticket_id=ticket_id,
        workflow_type=run_ctx.workflow_type or "unknown",
        dry_run=dry_run,
        steps=steps_summary,
        total_duration=total_duration,
        total_tokens=run_ctx.total_tokens,
    )

    console.print(f"  Workspace: [bold]{workspace.run_dir}[/bold]\n")

    if any(not r.success for r in run_ctx.results.values()):
        sys.exit(1)


def _run_single_agent(
    *,
    agent_name: str,
    ticket_id: str,
    context: str | None,
    dry_run: bool,
    settings: Settings,
    registry: "Registry",
    backend: "AgentBackend",
    workspace: "RunWorkspace",
) -> None:
    """Run a single named agent with the ticket as input."""
    from structured_agents.engine.delegation import dispatch_agent
    from structured_agents.models.context import RunContext

    if agent_name not in registry.agents:
        console.print(f"[failure]Unknown agent: {agent_name}[/failure]")
        console.print(f"Available: {', '.join(sorted(registry.agents))}")
        sys.exit(1)

    log_phase(f"Single Agent: {agent_name}", dry_run=dry_run)

    run_ctx = workspace.context
    task = f"Process Jira ticket {ticket_id}."
    if context:
        task += f"\n\nAdditional context: {context}"

    result = dispatch_agent(
        agent_name,
        task_description=task,
        run_context=run_ctx,
        registry=registry,
        settings=settings,
        backend=backend,
        extra_context=context or "",
    )

    workspace.record_result("single-agent", result)

    if result.success:
        console.print(f"\n[success]Agent {agent_name} completed successfully.[/success]")
    else:
        console.print(f"\n[failure]Agent {agent_name} failed: {result.error}[/failure]")

    console.print(f"  Duration: {result.duration_seconds:.1f}s | Tokens: {result.total_tokens:,}")
    console.print(f"  Workspace: [bold]{workspace.run_dir}[/bold]\n")

    if not result.success:
        sys.exit(1)


@main.command("validate")
@click.pass_context
def validate_cmd(ctx: click.Context) -> None:
    """Validate all agent, skill, and profile definitions."""
    from structured_agents.loaders import load_registry

    verbose = ctx.obj.get("verbose", False)
    repo_root = ctx.obj.get("repo_root")
    setup_logging(verbose=verbose)

    try:
        settings = load_settings(repo_root=repo_root)
    except Exception as exc:
        console.print(f"[failure]Settings error: {exc}[/failure]")
        sys.exit(1)

    registry = load_registry(settings.repo_root)

    errors: list[str] = []

    for name, agent in registry.agents.items():
        for skill_name in agent.skills:
            if skill_name not in registry.skills:
                errors.append(f"Agent '{name}' references missing skill: {skill_name}")
        for sa_name in agent.sub_agents:
            if sa_name not in registry.agents:
                errors.append(f"Agent '{name}' references missing sub-agent: {sa_name}")
        for prof_name in agent.profiles:
            if prof_name not in registry.profiles:
                errors.append(f"Agent '{name}' references missing profile: {prof_name}")
        for mcp_name in agent.mcps:
            if mcp_name not in registry.mcps:
                errors.append(f"Agent '{name}' references missing MCP: {mcp_name}")
        if not agent.system_prompt:
            errors.append(f"Agent '{name}' has no AGENT.md system prompt")

    for name, skill in registry.skills.items():
        if not skill.instructions:
            errors.append(f"Skill '{name}' has no instructions (empty SKILL.md body)")

    if errors:
        console.print(f"\n[failure]Found {len(errors)} validation errors:[/failure]\n")
        for err in errors:
            console.print(f"  - {err}")
        sys.exit(1)
    else:
        console.print(
            f"\n[success]All definitions valid.[/success]\n"
            f"  {len(registry.agents)} agents, {len(registry.skills)} skills, "
            f"{len(registry.profiles)} profiles, {len(registry.mcps)} MCPs\n"
        )


@main.command("list")
@click.argument("resource", type=click.Choice(["agents", "skills", "profiles", "mcps", "all"]), default="all")
@click.pass_context
def list_cmd(ctx: click.Context, resource: str) -> None:
    """List available agents, skills, profiles, or MCP servers."""
    from structured_agents.loaders import load_registry

    verbose = ctx.obj.get("verbose", False)
    repo_root = ctx.obj.get("repo_root")
    setup_logging(verbose=verbose)

    try:
        settings = load_settings(repo_root=repo_root)
    except Exception as exc:
        console.print(f"[failure]Settings error: {exc}[/failure]")
        sys.exit(1)

    registry = load_registry(settings.repo_root)

    if resource in ("agents", "all"):
        table = Table(title="Agents", show_lines=True)
        table.add_column("Name", style="agent")
        table.add_column("Description")
        table.add_column("Sub-agents")
        table.add_column("Skills")
        for a in sorted(registry.agents.values(), key=lambda x: x.name):
            table.add_row(
                a.name,
                a.description.strip()[:80],
                ", ".join(a.sub_agents) or "—",
                ", ".join(a.skills[:3]) + ("..." if len(a.skills) > 3 else "") or "—",
            )
        console.print(table)
        console.print()

    if resource in ("skills", "all"):
        table = Table(title="Skills", show_lines=True)
        table.add_column("Name", style="skill")
        table.add_column("Description")
        table.add_column("Tools")
        table.add_column("MCPs")
        for s in sorted(registry.skills.values(), key=lambda x: x.name):
            table.add_row(
                s.name,
                s.description.strip()[:80],
                ", ".join(s.tools) or "—",
                ", ".join(s.mcps) or "—",
            )
        console.print(table)
        console.print()

    if resource in ("profiles", "all"):
        table = Table(title="Profiles", show_lines=True)
        table.add_column("Name")
        table.add_column("Language")
        table.add_column("Platform")
        table.add_column("URL")
        for p in sorted(registry.profiles.values(), key=lambda x: x.name):
            table.add_row(p.name, p.language, p.platform, p.url[:60])
        console.print(table)
        console.print()

    if resource in ("mcps", "all"):
        table = Table(title="MCP Servers", show_lines=True)
        table.add_column("Name")
        table.add_column("Type")
        table.add_column("Available")
        table.add_column("Optional")
        for m in sorted(registry.mcps.values(), key=lambda x: x.name):
            avail = "[success]yes[/success]" if m.available else "[failure]no[/failure]"
            table.add_row(m.name, m.type, avail, "yes" if m.optional else "no")
        console.print(table)
        console.print()


@main.command("show")
@click.argument("agent_name")
@click.option("--dry-run", "-n", is_flag=True, help="Include dry-run constraints in prompt")
@click.pass_context
def show_cmd(ctx: click.Context, agent_name: str, dry_run: bool) -> None:
    """Show the fully assembled system prompt for an agent (useful for debugging)."""
    from structured_agents.engine.prompt_assembler import assemble_system_prompt
    from structured_agents.loaders import load_registry

    verbose = ctx.obj.get("verbose", False)
    repo_root = ctx.obj.get("repo_root")
    setup_logging(verbose=verbose)

    try:
        settings = load_settings(repo_root=repo_root)
    except Exception as exc:
        console.print(f"[failure]Settings error: {exc}[/failure]")
        sys.exit(1)

    registry = load_registry(settings.repo_root)

    if agent_name not in registry.agents:
        console.print(f"[failure]Unknown agent: {agent_name}[/failure]")
        console.print(f"Available: {', '.join(sorted(registry.agents))}")
        sys.exit(1)

    prompt = assemble_system_prompt(
        agent_name,
        registry=registry,
        settings=settings,
        dry_run=dry_run,
    )

    console.print(f"\n[agent]System prompt for: {agent_name}[/agent]")
    console.print(f"[dim]({len(prompt):,} characters)[/dim]\n")
    console.print(prompt)


@main.command()
@click.option("--host", default="localhost", help="MCP server host")
@click.option("--port", default=8400, help="MCP server port")
def serve(host: str, port: int) -> None:
    """Start the MCP server for Cursor integration (not yet implemented)."""
    console.print(f"[dim]MCP server not yet implemented. Would start on {host}:{port}[/dim]")
