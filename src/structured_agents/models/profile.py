"""Repository profile model -- mirrors profiles/_schema.yaml."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RepoConventions(BaseModel):
    commit_format: str = ""
    branch_naming: str = ""
    review_requirements: str = ""
    testing: str = ""


class RepoRelationship(BaseModel):
    repo: str
    type: str = ""
    description: str = ""


class RepoWorkflow(BaseModel):
    name: str
    description: str = ""
    steps: list[str] = Field(default_factory=list)


class RepoProfile(BaseModel):
    """A loaded repository profile."""

    name: str
    url: str = ""
    description: str = ""
    language: str = "mixed"
    platform: str = "gitlab"
    default_branch: str = "main"
    local_path: str = ""
    ci_system: str = "none"
    key_files: list[str] = Field(default_factory=list)
    conventions: RepoConventions = Field(default_factory=RepoConventions)
    relationships: list[RepoRelationship] = Field(default_factory=list)
    workflows: list[RepoWorkflow] = Field(default_factory=list)

    source_path: str = ""
