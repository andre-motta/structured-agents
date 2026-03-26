"""Rich-based logging for structured-agents runs."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

THEME = Theme(
    {
        "agent": "bold cyan",
        "skill": "bold green",
        "step": "bold yellow",
        "success": "bold green",
        "failure": "bold red",
        "dry_run": "bold magenta",
        "token": "dim",
    }
)

console = Console(theme=THEME, stderr=True)

_LOG_FORMAT = "%(message)s"
_DATE_FORMAT = "%H:%M:%S"


def setup_logging(*, verbose: bool = False, log_file: Path | None = None) -> logging.Logger:
    """Configure the root structured-agents logger with Rich console + optional file handler."""
    root = logging.getLogger("structured_agents")
    root.setLevel(logging.DEBUG if verbose else logging.INFO)
    root.handlers.clear()

    rich_handler = RichHandler(
        console=console,
        show_path=False,
        markup=True,
        rich_tracebacks=True,
        tracebacks_show_locals=verbose,
        log_time_format=_DATE_FORMAT,
    )
    rich_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    rich_handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    root.addHandler(rich_handler)

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter("%(asctime)s %(name)-25s %(levelname)-8s %(message)s"))
        root.addHandler(fh)

    return root


def get_logger(name: str) -> logging.Logger:
    """Return a child logger scoped to an agent or component."""
    return logging.getLogger(f"structured_agents.{name}")


def log_phase(title: str, *, dry_run: bool = False) -> None:
    """Print a prominent phase header."""
    style = "dry_run" if dry_run else "step"
    suffix = " [DRY RUN]" if dry_run else ""
    console.print()
    console.print(Panel(f"[{style}]{title}{suffix}[/{style}]", expand=False, border_style=style))


def log_agent_start(agent_name: str, step_id: str | None = None) -> None:
    """Log the start of an agent invocation."""
    label = f"[agent]{agent_name}[/agent]"
    if step_id:
        label += f" (step [step]{step_id}[/step])"
    console.print(f"  -> Running {label} ...")


def log_agent_end(agent_name: str, *, success: bool, duration: float, tokens: int = 0) -> None:
    """Log the end of an agent invocation."""
    status = "[success]OK[/success]" if success else "[failure]FAILED[/failure]"
    parts = [f"  <- [agent]{agent_name}[/agent] {status} ({duration:.1f}s)"]
    if tokens:
        parts.append(f"[token]{tokens:,} tokens[/token]")
    console.print(" ".join(parts))


def log_tool_use(tool_name: str, *, agent: str = "") -> None:
    """Log a tool invocation from an agent."""
    prefix = f"[agent]{agent}[/agent] " if agent else ""
    console.print(f"     {prefix}[skill]tool:[/skill] {tool_name}", highlight=False)


def log_stream_text(text: str) -> None:
    """Print streamed text from an agent (partial output)."""
    sys.stderr.write(text)
    sys.stderr.flush()


def print_run_summary(
    *,
    ticket_id: str,
    workflow_type: str,
    dry_run: bool,
    steps: list[dict],
    total_duration: float,
    total_tokens: int,
) -> None:
    """Print a summary table at the end of a run."""
    table = Table(title="Run Summary", show_lines=True)
    table.add_column("Step", style="step")
    table.add_column("Agent", style="agent")
    table.add_column("Status")
    table.add_column("Duration", justify="right")
    table.add_column("Tokens", justify="right", style="token")

    for s in steps:
        status_style = "success" if s["success"] else "failure"
        table.add_row(
            s.get("id", "—"),
            s["agent"],
            Text(s["status"], style=status_style),
            f"{s['duration']:.1f}s",
            f"{s.get('tokens', 0):,}",
        )

    console.print()
    console.print(table)

    suffix = " [DRY RUN]" if dry_run else ""
    console.print(
        f"\n  Ticket: [bold]{ticket_id}[/bold]  |  Workflow: [bold]{workflow_type}[/bold]{suffix}"
        f"\n  Total: [bold]{total_duration:.1f}s[/bold]  |  Tokens: [token]{total_tokens:,}[/token]\n"
    )
