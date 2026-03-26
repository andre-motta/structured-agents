"""Load agent definitions from agents/*/agent.yaml + AGENT.md."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from structured_agents.models.agent import AgentDefinition, AgentInput, AgentRemote

log = logging.getLogger(__name__)


def load_agents(agents_dir: Path) -> dict[str, AgentDefinition]:
    """Walk agents/ and return a mapping of agent name -> AgentDefinition."""
    agents: dict[str, AgentDefinition] = {}

    if not agents_dir.is_dir():
        log.warning("Agents directory not found: %s", agents_dir)
        return agents

    for entry in sorted(agents_dir.iterdir()):
        if not entry.is_dir() or entry.name.startswith("_"):
            continue

        yaml_path = entry / "agent.yaml"
        md_path = entry / "AGENT.md"

        if not yaml_path.exists():
            log.warning("Skipping %s -- no agent.yaml found", entry.name)
            continue

        try:
            raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            log.error("Failed to parse %s: %s", yaml_path, exc)
            continue

        inputs = {}
        for k, v in raw.pop("inputs", {}).items():
            inputs[k] = AgentInput(**v) if isinstance(v, dict) else AgentInput(type=str(v))

        remote = None
        if raw_remote := raw.pop("remote", None):
            remote = AgentRemote(**raw_remote)

        system_prompt = ""
        if md_path.exists():
            system_prompt = md_path.read_text(encoding="utf-8")

        agent = AgentDefinition(
            **{k: v for k, v in raw.items() if k in AgentDefinition.model_fields},
            inputs=inputs,
            remote=remote,
            system_prompt=system_prompt,
            source_dir=str(entry),
        )
        agents[agent.name] = agent
        log.debug("Loaded agent: %s (%s)", agent.name, agent.version)

    log.info("Loaded %d agents", len(agents))
    return agents
