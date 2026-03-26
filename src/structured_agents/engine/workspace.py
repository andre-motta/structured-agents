"""Run workspace management -- creates and manages per-run artifact directories."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import yaml

from structured_agents.models.context import AgentResult, ExecutionPlan, RunContext

log = logging.getLogger(__name__)


class RunWorkspace:
    """Manages the filesystem workspace for a single orchestration run.

    Layout:
        workspace/runs/<run-id>/
        ├── run.log          # log file for this run
        ├── context.yaml     # serialized RunContext
        ├── plan.yaml        # execution plan (after planning phase)
        ├── report.md        # final report
        └── artifacts/       # per-step outputs
            └── <step-id>/
                └── <artifact files>
    """

    def __init__(self, run_dir: Path, run_context: RunContext) -> None:
        self.run_dir = run_dir
        self.context = run_context
        self.artifacts_dir = run_dir / "artifacts"
        self.log_file = run_dir / "run.log"

    @classmethod
    def create(cls, *, base_dir: Path, ticket_id: str, dry_run: bool = False, additional_context: str = "") -> RunWorkspace:
        """Create a new run workspace directory and initialize the RunContext."""
        now = datetime.now(timezone.utc)
        run_id = f"{ticket_id}-{now.strftime('%Y%m%d-%H%M%S')}"

        run_dir = base_dir / "workspace" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "artifacts").mkdir(exist_ok=True)

        ctx = RunContext(
            run_id=run_id,
            ticket_id=ticket_id,
            dry_run=dry_run,
            additional_context=additional_context,
            started_at=now,
        )

        ws = cls(run_dir, ctx)
        ws._save_context()

        log.info("Created run workspace: %s", run_dir)
        return ws

    def record_result(self, step_id: str, result: AgentResult) -> None:
        """Record an agent result for a plan step."""
        result.step_id = step_id
        self.context.results[step_id] = result

        if result.artifacts:
            step_dir = self.artifacts_dir / step_id
            step_dir.mkdir(exist_ok=True)
            for name, content in result.artifacts.items():
                (step_dir / name).write_text(content, encoding="utf-8")
                log.debug("Wrote artifact %s/%s", step_id, name)

        self._save_context()

    def write_plan(self, plan: ExecutionPlan) -> None:
        """Write the execution plan to plan.yaml."""
        self.context.plan = plan
        plan_path = self.run_dir / "plan.yaml"
        plan_path.write_text(
            yaml.dump(plan.model_dump(), default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )
        self._save_context()
        log.info("Wrote execution plan: %s (%d steps)", plan_path, len(plan.steps))

    def write_report(self, report_text: str) -> None:
        """Write the final report markdown."""
        self.context.completed_at = datetime.now(timezone.utc)
        report_path = self.run_dir / "report.md"
        report_path.write_text(report_text, encoding="utf-8")
        self._save_context()
        log.info("Wrote final report: %s", report_path)

    def _save_context(self) -> None:
        """Persist the current RunContext to context.json."""
        ctx_path = self.run_dir / "context.json"
        ctx_path.write_text(
            json.dumps(self.context.model_dump(mode="json"), indent=2, default=str),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, run_dir: Path) -> RunWorkspace:
        """Load an existing run workspace from disk."""
        ctx_path = run_dir / "context.json"
        if not ctx_path.exists():
            raise FileNotFoundError(f"No context.json found in {run_dir}")

        data = json.loads(ctx_path.read_text(encoding="utf-8"))
        ctx = RunContext(**data)
        return cls(run_dir, ctx)
