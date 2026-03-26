"""Claude Code CLI backend -- runs agents via `claude -p` with stream-json output."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

from structured_agents.backends.base import AgentBackend
from structured_agents.models.context import AgentResult

log = logging.getLogger(__name__)

_CLAUDE_BIN = "claude"


class ClaudeCodeBackend(AgentBackend):
    """Execute agents via the Claude Code CLI in headless (print) mode.

    Each agent invocation runs:
        claude -p "<user_prompt>"
            --append-system-prompt-file <tmpfile>
            --output-format stream-json
            [--allowedTools ...]
    """

    def __init__(self, *, claude_bin: str = _CLAUDE_BIN, extra_flags: list[str] | None = None) -> None:
        self._claude_bin = claude_bin
        self._extra_flags = extra_flags or []

    def check_available(self) -> bool:
        """Check that the `claude` CLI is on $PATH."""
        return shutil.which(self._claude_bin) is not None

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
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", prefix=f"sagent-{agent_name}-", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(system_prompt)
            system_prompt_path = tmp.name

        cmd = self._build_command(
            user_prompt=user_prompt,
            system_prompt_path=system_prompt_path,
            allowed_tools=allowed_tools,
        )

        log.debug("Running claude: %s", " ".join(cmd[:6]) + " ...")
        log.debug("System prompt file: %s (%d chars)", system_prompt_path, len(system_prompt))
        log.debug("User prompt: %.200s...", user_prompt)

        start = time.monotonic()
        output_parts: list[str] = []
        input_tokens = 0
        output_tokens = 0
        error_msg: str | None = None

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd,
                text=True,
                encoding="utf-8",
            )
            assert proc.stdout is not None

            for line in proc.stdout:
                line = line.rstrip("\n")
                if not line:
                    continue

                event = _try_parse_json(line)
                if event is None:
                    output_parts.append(line)
                    continue

                in_tok, out_tok = _extract_tokens(event)
                input_tokens += in_tok
                output_tokens += out_tok

                text = _extract_text(event)
                if text:
                    output_parts.append(text)

                if on_event:
                    on_event(event)

            proc.wait(timeout=timeout)

            if proc.returncode != 0:
                stderr_text = proc.stderr.read() if proc.stderr else ""
                error_msg = f"claude exited with code {proc.returncode}: {stderr_text[:500]}"
                log.error("[%s] %s", agent_name, error_msg)

        except subprocess.TimeoutExpired:
            proc.kill()
            error_msg = f"Agent {agent_name} timed out after {timeout}s"
            log.error(error_msg)
        except FileNotFoundError:
            error_msg = f"Claude CLI not found at '{self._claude_bin}'. Is Claude Code installed?"
            log.error(error_msg)
        finally:
            Path(system_prompt_path).unlink(missing_ok=True)

        duration = time.monotonic() - start
        full_output = "\n".join(output_parts)

        return AgentResult(
            agent=agent_name,
            success=error_msg is None,
            output=full_output,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_seconds=duration,
            error=error_msg,
        )

    def _build_command(
        self,
        *,
        user_prompt: str,
        system_prompt_path: str,
        allowed_tools: list[str] | None = None,
    ) -> list[str]:
        cmd = [
            self._claude_bin,
            "-p", user_prompt,
            "--output-format", "stream-json",
            "--append-system-prompt-file", system_prompt_path,
            "--verbose",
        ]

        if allowed_tools:
            for tool in allowed_tools:
                cmd.extend(["--allowedTools", tool])

        cmd.extend(self._extra_flags)
        return cmd


def _try_parse_json(line: str) -> dict | None:
    """Attempt to parse a line as JSON; return None on failure."""
    try:
        return json.loads(line)
    except (json.JSONDecodeError, ValueError):
        return None


def _extract_tokens(event: dict) -> tuple[int, int]:
    """Extract (input_tokens, output_tokens) from a stream-json event."""
    usage = event.get("usage") or event.get("result", {}).get("usage") or {}
    return usage.get("input_tokens", 0), usage.get("output_tokens", 0)


def _extract_text(event: dict) -> str:
    """Extract displayable text from a stream-json event."""
    etype = event.get("type", "")

    if etype == "assistant":
        content = event.get("message", {}).get("content", [])
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block["text"])
        return "\n".join(parts)

    if etype == "result":
        return event.get("result", {}).get("text", "")

    return ""
