"""Skill definition model -- mirrors skills/_schema.yaml."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SkillDefinition(BaseModel):
    """A loaded skill: YAML frontmatter metadata + markdown instructions."""

    name: str
    description: str
    tools: list[str] = Field(default_factory=list)
    mcps: list[str] = Field(default_factory=list)
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)

    instructions: str = ""
    source_path: str = ""
