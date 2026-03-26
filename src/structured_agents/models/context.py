"""Runtime context models for orchestration runs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class PlanStep(BaseModel):
    """A single step in an execution plan."""

    id: str
    agent: str
    action: str
    inputs: dict = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)
    status: Literal["pending", "running", "completed", "failed", "skipped"] = "pending"


class ExecutionPlan(BaseModel):
    """Structured execution plan produced by the planner agent."""

    ticket_id: str
    workflow_type: str
    summary: str = ""
    steps: list[PlanStep] = Field(default_factory=list)


class AgentResult(BaseModel):
    """Result from a single agent invocation."""

    agent: str
    step_id: str | None = None
    success: bool = True
    output: str = ""
    artifacts: dict[str, str] = Field(default_factory=dict)
    input_tokens: int = 0
    output_tokens: int = 0
    duration_seconds: float = 0.0
    error: str | None = None

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class RunContext(BaseModel):
    """Full context for an orchestration run, persisted to the workspace."""

    run_id: str
    ticket_id: str
    dry_run: bool = False
    additional_context: str = ""
    workflow_type: str | None = None
    ticket_summary: str = ""
    ticket_data: dict = Field(default_factory=dict)
    plan: ExecutionPlan | None = None
    results: dict[str, AgentResult] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None

    @property
    def total_tokens(self) -> int:
        return sum(r.total_tokens for r in self.results.values())

    @property
    def total_duration(self) -> float:
        return sum(r.duration_seconds for r in self.results.values())
