"""Agent definition model -- mirrors agents/_schema.yaml."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AgentInput(BaseModel):
    type: str = "string"
    required: bool = False
    description: str = ""


class AgentRemote(BaseModel):
    host: str = ""
    workspace: str = ""


class AgentDefinition(BaseModel):
    """A loaded agent: YAML metadata + AGENT.md system prompt."""

    name: str
    description: str
    version: str = "0.1.0"
    capabilities: list[str] = Field(default_factory=list)
    sub_agents: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    optional_skills: list[str] = Field(default_factory=list)
    mcps: list[str] = Field(default_factory=list)
    optional_mcps: list[str] = Field(default_factory=list)
    inputs: dict[str, AgentInput] = Field(default_factory=dict)
    outputs: dict[str, str] = Field(default_factory=dict)
    remote: AgentRemote | None = None
    profiles: list[str] = Field(default_factory=list)

    system_prompt: str = ""
    source_dir: str = ""
