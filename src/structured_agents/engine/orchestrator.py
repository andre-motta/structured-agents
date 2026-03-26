"""Main orchestration loop -- drives the full run lifecycle."""

from __future__ import annotations

import logging

from structured_agents.backends.base import AgentBackend
from structured_agents.config import Settings
from structured_agents.engine.delegation import dispatch_agent, extract_yaml_blocks
from structured_agents.engine.workspace import RunWorkspace
from structured_agents.loaders import Registry
from structured_agents.log import log_phase
from structured_agents.models.context import AgentResult, ExecutionPlan, PlanStep, RunContext

log = logging.getLogger(__name__)


def execute_run(
    ticket_id: str,
    *,
    dry_run: bool = False,
    additional_context: str = "",
    settings: Settings,
    registry: Registry,
    backend: AgentBackend,
    workspace: RunWorkspace,
) -> RunContext:
    """Execute the full orchestration loop for a ticket.

    Phases:
        1. Intake   -- read ticket, classify workflow type
        2. Planning -- produce structured execution plan
        3. Execute  -- run each plan step via specialist agents
        4. Report   -- compile final summary
    """
    ctx = workspace.context

    # --- Phase 1: Intake ---
    log_phase("Phase 1: Intake", dry_run=dry_run)
    intake_result = _phase_intake(
        ticket_id,
        additional_context=additional_context,
        run_context=ctx,
        registry=registry,
        settings=settings,
        backend=backend,
    )
    workspace.record_result("intake", intake_result)

    if not intake_result.success:
        log.error("Intake phase failed: %s", intake_result.error)
        return ctx

    _update_context_from_intake(ctx, intake_result)

    # --- Phase 2: Planning ---
    log_phase("Phase 2: Planning", dry_run=dry_run)
    plan_result = _phase_plan(
        run_context=ctx,
        registry=registry,
        settings=settings,
        backend=backend,
    )
    workspace.record_result("planning", plan_result)

    if not plan_result.success or ctx.plan is None:
        log.error("Planning phase failed: %s", plan_result.error or "No plan produced")
        return ctx

    workspace.write_plan(ctx.plan)
    log.info(
        "Execution plan: %s workflow, %d steps",
        ctx.workflow_type,
        len(ctx.plan.steps),
    )

    # --- Phase 3: Execute plan steps ---
    log_phase("Phase 3: Execution", dry_run=dry_run)
    _phase_execute(
        run_context=ctx,
        registry=registry,
        settings=settings,
        backend=backend,
        workspace=workspace,
    )

    # --- Phase 4: Report ---
    log_phase("Phase 4: Report", dry_run=dry_run)
    report_result = _phase_report(
        run_context=ctx,
        registry=registry,
        settings=settings,
        backend=backend,
    )
    workspace.record_result("report", report_result)

    if report_result.success:
        workspace.write_report(report_result.output)

    return ctx


def _phase_intake(
    ticket_id: str,
    *,
    additional_context: str,
    run_context: RunContext,
    registry: Registry,
    settings: Settings,
    backend: AgentBackend,
) -> AgentResult:
    """Phase 1: Read the Jira ticket and classify the workflow type."""
    task = (
        f"Read Jira ticket {ticket_id} and perform the intake workflow:\n"
        f"1. Fetch the full ticket details (summary, description, type, labels, "
        f"linked MRs, child tickets)\n"
        f"2. If it's an Epic, also fetch all child Stories\n"
        f"3. Classify the workflow type based on the Classification Rules\n"
        f"4. List all linked MR URLs found\n\n"
        f"Respond with a YAML block containing:\n"
        f"```yaml\n"
        f"ticket_id: {ticket_id}\n"
        f"summary: <ticket summary>\n"
        f"workflow_type: <one of: package-onboarding, dependency-update, feature, "
        f"bugfix, probe-test, adr, container, investigation, infra>\n"
        f"linked_mrs:\n"
        f"  - <url1>\n"
        f"  - <url2>\n"
        f"child_tickets:\n"
        f"  - key: <key>\n"
        f"    summary: <summary>\n"
        f"    status: <status>\n"
        f"classification_reasoning: <why you chose this workflow type>\n"
        f"```\n"
    )

    return dispatch_agent(
        "orchestrator",
        task_description=task,
        run_context=run_context,
        registry=registry,
        settings=settings,
        backend=backend,
        extra_context=additional_context,
    )


def _phase_plan(
    *,
    run_context: RunContext,
    registry: Registry,
    settings: Settings,
    backend: AgentBackend,
) -> AgentResult:
    """Phase 2: Produce a structured execution plan."""
    task = (
        f"Create a structured execution plan for ticket {run_context.ticket_id}.\n\n"
        f"Workflow type: {run_context.workflow_type}\n"
        f"Ticket summary: {run_context.ticket_summary}\n\n"
        f"Produce a plan as a YAML block with this structure:\n"
        f"```yaml\n"
        f"ticket_id: {run_context.ticket_id}\n"
        f"workflow_type: {run_context.workflow_type}\n"
        f"summary: <brief plan summary>\n"
        f"steps:\n"
        f"  - id: step-1\n"
        f"    agent: <agent name from available sub-agents>\n"
        f"    action: <what this step does>\n"
        f"    inputs:\n"
        f"      <key>: <value>\n"
        f"    depends_on: []  # list of step IDs this depends on\n"
        f"  - id: step-2\n"
        f"    agent: <agent name>\n"
        f"    action: <what this step does>\n"
        f"    depends_on: [step-1]\n"
        f"```\n\n"
        f"Use the delegation patterns from your instructions to determine the right "
        f"sequence of agents. Each step should map to exactly one agent."
    )

    result = dispatch_agent(
        "planner",
        task_description=task,
        run_context=run_context,
        registry=registry,
        settings=settings,
        backend=backend,
    )

    if result.success:
        plan = _parse_plan(result.output, run_context)
        if plan:
            run_context.plan = plan
        else:
            result.success = False
            result.error = "Failed to parse execution plan from planner output"
            log.error("Could not parse plan. Raw output:\n%.500s", result.output)

    return result


def _phase_execute(
    *,
    run_context: RunContext,
    registry: Registry,
    settings: Settings,
    backend: AgentBackend,
    workspace: RunWorkspace,
) -> None:
    """Phase 3: Execute each plan step in dependency order."""
    if not run_context.plan:
        return

    plan = run_context.plan
    executed: set[str] = set()

    for step in plan.steps:
        unmet = [d for d in step.depends_on if d not in executed]
        if unmet:
            failed_deps = [d for d in unmet if d in run_context.results and not run_context.results[d].success]
            if failed_deps:
                log.warning(
                    "Skipping step %s -- dependency %s failed",
                    step.id,
                    failed_deps,
                )
                step.status = "skipped"
                workspace.record_result(
                    step.id,
                    AgentResult(agent=step.agent, step_id=step.id, success=False, error=f"Skipped: dependency {failed_deps} failed"),
                )
                continue

        if step.agent not in registry.agents:
            log.error("Unknown agent '%s' in step %s -- skipping", step.agent, step.id)
            step.status = "skipped"
            workspace.record_result(
                step.id,
                AgentResult(agent=step.agent, step_id=step.id, success=False, error=f"Unknown agent: {step.agent}"),
            )
            continue

        step.status = "running"
        log.info("Executing step %s: %s (agent: %s)", step.id, step.action, step.agent)

        result = dispatch_agent(
            step.agent,
            task_description=step.action,
            step=step,
            run_context=run_context,
            registry=registry,
            settings=settings,
            backend=backend,
        )

        step.status = "completed" if result.success else "failed"
        workspace.record_result(step.id, result)

        if result.success:
            executed.add(step.id)
        else:
            log.error("Step %s failed: %s", step.id, result.error or "unknown error")


def _phase_report(
    *,
    run_context: RunContext,
    registry: Registry,
    settings: Settings,
    backend: AgentBackend,
) -> AgentResult:
    """Phase 4: Compile a final report from all results."""
    step_summaries = []
    for sid, res in run_context.results.items():
        status = "OK" if res.success else "FAILED"
        step_summaries.append(f"- **{sid}** ({res.agent}): {status}")
        if res.error:
            step_summaries.append(f"  Error: {res.error}")

    task = (
        f"Compile a final report for ticket {run_context.ticket_id}.\n\n"
        f"Workflow: {run_context.workflow_type}\n"
        f"Summary: {run_context.ticket_summary}\n\n"
        f"Step results:\n" + "\n".join(step_summaries) + "\n\n"
        f"Write a markdown report suitable for posting as a Jira comment or "
        f"saving as documentation. Include:\n"
        f"- What was done (or planned, if dry run)\n"
        f"- Key decisions and reasoning\n"
        f"- Any issues encountered\n"
        f"- Next steps or open items\n"
    )

    return dispatch_agent(
        "orchestrator",
        task_description=task,
        run_context=run_context,
        registry=registry,
        settings=settings,
        backend=backend,
    )


def _update_context_from_intake(ctx: RunContext, result: AgentResult) -> None:
    """Parse the intake result and update the RunContext."""
    blocks = extract_yaml_blocks(result.output)
    for block in blocks:
        if "workflow_type" in block:
            ctx.workflow_type = block["workflow_type"]
            ctx.ticket_summary = block.get("summary", "")
            ctx.ticket_data = block
            log.info(
                "Classified as: %s -- %s",
                ctx.workflow_type,
                ctx.ticket_summary,
            )
            return

    log.warning("Could not extract structured intake data; using raw output as context")
    ctx.workflow_type = "unknown"
    ctx.ticket_summary = result.output[:200]


def _parse_plan(output: str, ctx: RunContext) -> ExecutionPlan | None:
    """Parse an ExecutionPlan from the planner agent's output."""
    blocks = extract_yaml_blocks(output)
    for block in blocks:
        if "steps" in block:
            try:
                steps = [PlanStep(**s) for s in block["steps"]]
                return ExecutionPlan(
                    ticket_id=ctx.ticket_id,
                    workflow_type=block.get("workflow_type", ctx.workflow_type or "unknown"),
                    summary=block.get("summary", ""),
                    steps=steps,
                )
            except Exception as exc:
                log.warning("Failed to parse plan block: %s", exc)
                continue
    return None
