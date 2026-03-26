"""Abstract backend interface for agent execution."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path

from structured_agents.models.context import AgentResult


class AgentBackend(ABC):
    """Interface for invoking an LLM with a system prompt and user prompt."""

    @abstractmethod
    def run(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        agent_name: str = "agent",
        allowed_tools: list[str] | None = None,
        cwd: Path | None = None,
        timeout: int = 600,
        on_event: Callable[[dict], None] | None = None,
    ) -> AgentResult:
        """Execute an agent with the given prompts and return structured results.

        Args:
            system_prompt: The assembled system prompt (AGENT.md + skills + profiles).
            user_prompt: The task-specific user prompt.
            agent_name: Name for logging purposes.
            allowed_tools: Restrict available tools (backend-specific).
            cwd: Working directory for the agent process.
            timeout: Maximum seconds before killing the process.
            on_event: Callback for streaming events (tool use, text, etc.).

        Returns:
            AgentResult with output text, artifacts, token usage, and duration.
        """

    @abstractmethod
    def check_available(self) -> bool:
        """Return True if this backend is usable (e.g. CLI is installed)."""
