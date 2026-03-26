"""MCP server configuration model -- mirrors mcps/*.yaml."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MCPConnection(BaseModel):
    server_url: str = ""
    auth: dict[str, str] = Field(default_factory=dict)


class MCPServerConfig(BaseModel):
    """A loaded MCP server definition."""

    name: str
    description: str = ""
    type: str = ""
    connection: MCPConnection = Field(default_factory=MCPConnection)
    capabilities: list[str] = Field(default_factory=list)
    used_by_agents: list[str] = Field(default_factory=list)
    used_by_skills: list[str] = Field(default_factory=list)
    environment_variables: dict[str, str] = Field(default_factory=dict)
    optional: bool = False
    required_env: str = ""

    available: bool = False
    source_path: str = ""
