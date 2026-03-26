"""Loaders for agent definitions, skills, profiles, and MCP configs."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from structured_agents.loaders.agents import load_agents
from structured_agents.loaders.mcps import load_mcps
from structured_agents.loaders.profiles import load_profiles
from structured_agents.loaders.skills import load_skills
from structured_agents.models.agent import AgentDefinition
from structured_agents.models.mcp import MCPServerConfig
from structured_agents.models.profile import RepoProfile
from structured_agents.models.skill import SkillDefinition

log = logging.getLogger(__name__)


@dataclass
class Registry:
    """Holds all loaded definitions for a structured-agents repo."""

    agents: dict[str, AgentDefinition] = field(default_factory=dict)
    skills: dict[str, SkillDefinition] = field(default_factory=dict)
    profiles: dict[str, RepoProfile] = field(default_factory=dict)
    mcps: dict[str, MCPServerConfig] = field(default_factory=dict)

    def get_agent_skills(self, agent_name: str, *, include_optional: bool = False) -> list[SkillDefinition]:
        """Return the skill definitions available to an agent."""
        agent = self.agents.get(agent_name)
        if not agent:
            return []
        names = list(agent.skills)
        if include_optional:
            names.extend(agent.optional_skills)
        return [self.skills[n] for n in names if n in self.skills]

    def get_agent_profiles(self, agent_name: str) -> list[RepoProfile]:
        """Return the repo profiles referenced by an agent."""
        agent = self.agents.get(agent_name)
        if not agent:
            return []
        return [self.profiles[n] for n in agent.profiles if n in self.profiles]

    def get_agent_mcps(self, agent_name: str, *, include_optional: bool = False) -> list[MCPServerConfig]:
        """Return the MCP configs referenced by an agent."""
        agent = self.agents.get(agent_name)
        if not agent:
            return []
        names = list(agent.mcps)
        if include_optional:
            names.extend(agent.optional_mcps)
        return [self.mcps[n] for n in names if n in self.mcps]


def load_registry(repo_root: Path) -> Registry:
    """Load all definitions from a structured-agents repository."""
    log.info("Loading registry from %s", repo_root)

    return Registry(
        agents=load_agents(repo_root / "agents"),
        skills=load_skills(repo_root / "skills"),
        profiles=load_profiles(repo_root / "profiles"),
        mcps=load_mcps(repo_root / "mcps"),
    )


__all__ = [
    "Registry",
    "load_agents",
    "load_mcps",
    "load_profiles",
    "load_registry",
    "load_skills",
]
