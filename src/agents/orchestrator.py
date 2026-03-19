"""
Orchestrator - Coordinates all agents with:
  - PlannerAgent for dynamic task decomposition
  - Shared short-term memory across agents
  - Long-term memory injection
  - Human-in-the-loop (HITL) checkpoints
  - Inter-agent messaging via shared memory
"""
import asyncio
import time
import uuid
import json
import logging
from typing import Any, Optional

from .validation_agent import ValidationAgent
from .optimization_agent import OptimizationAgent
from .conflict_resolution_agent import ConflictResolutionAgent
from .resource_allocation_agent import ResourceAllocationAgent
from .analytics_agent import AnalyticsAgent
from .planner_agent import PlannerAgent
from .memory import ShortTermMemory, LongTermMemory

logger = logging.getLogger(__name__)


class HumanApprovalRequired(Exception):
    """Raised when the pipeline pauses for human input."""
    def __init__(self, run_id: str, stage: str, checkpoint_data: dict):
        self.run_id = run_id
        self.stage = stage
        self.checkpoint_data = checkpoint_data
        super().__init__(f"Human approval required at stage '{stage}' for run {run_id}")


class AgentOrchestrator:
    """
    Coordinates the multi-agent pipeline:
    Plan → Validate → Allocate → Optimize → [HITL] → Resolve → Analyze → Reflect
    """

    def __init__(self, db_session_factory=None):
        self.validation_agent  = ValidationAgent()
        self.resource_agent    = ResourceAllocationAgent()
        self.optimization_agent = OptimizationAgent()
        self.conflict_agent    = ConflictResolutionAgent()
        self.analytics_agent   = AnalyticsAgent()
        self.planner_agent     = PlannerAgent()

        self._initialized = False
        self.pipeline_log: list = []

        # Shared short-term memory for this run
        self._run_memory = ShortTermMemory()

        # Long-term memory (only available when DB session factory is provided)
        self._long_term = LongTermMemory(db_session_factory) if db_session_factory else None

        self._all_agents = [
            self.validation_agent, self.resource_agent,
            self.optimization_agent, self.conflict_agent,
            self.analytics_agent, self.planner_agent,
        ]

    async def _initialize(self):
        if self._initialized:
            return
        for agent in self._all_agents:
            agent.mcp_enabled = False
            await agent._initialize_agent()
            # Inject long-term memory into every agent
            agent.long_term_memory = self._long_term
        self._initialized = True
        logger.info("[Orchestrator] All agents initialized")

    def _share_memory(self, key: str, value: Any):
        """Write to shared short-term memory so all agents can read it."""
        self._run_memory.set(key, value)
        for agent in self._all_agents:
            agent.memory.set(key, value)

    def _log(self, step: str, agent: str, status: str, detail: str = ""):
        entry = {"step": step, "agent": agent, "status": status, "detail": detail}
        self.pipeline_log.append(entry)
        logger.info(f"[{agent}] {step}: {status} {detail}")

    async def _call(self, agent, method: str, params: dict) -> dict:
        result = await agent.process_request({"method": method, "params": params})
        self._log(method, agent.agent_name, result.get("status", "unknown"))
        return result

    def _save_run(self, run_id: str, status: str, stage: str,
                  input_data: dict, checkpoint_data: dict = None, result: dict = None):
        """Persist run state to DB if available."""
        if not self._long_term:
            return
        from src.database.models import PipelineRun
        db = self._long_term._factory()
        try:
            run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
            if not run:
                run = PipelineRun(id=run_id)
                db.add(run)
            run.status = status
            run.stage = stage
            run.input_data = json.dumps(input_data)
            if checkpoint_data is not None:
                run.checkpoint_data = json.dumps(checkpoint_data)
            if result is not None:
                run.result = json.dumps(result)
            db.commit()
        finally:
            db.close()

    # ── Main pipeline ─────────────────────────────────────────────────────────

    async def run(self, input_data: dict[str, Any], run_id: str = None,
                  hitl_enabled: bool = True) -> dict[str, Any]:
        await self._initialize()
        self.pipeline_log = []
        self._run_memory.clear()
        for agent in self._all_agents:
            agent.memory.clear()

        run_id = run_id or str(uuid.uuid4())
        start = time.time()

        # Share input context with all agents via memory
        self._share_memory("run_id", run_id)
        self._share_memory("input_summary", {
            "divisions": len(input_data.get("divisions", [])),
            "subjects":  len(input_data.get("subjects", [])),
            "rooms":     len(input_data.get("rooms", [])),
            "timeslots": len(input_data.get("timeslots", [])),
        })

        # ── Step 0: Plan ──────────────────────────────────────────────────────
        logger.info("[Orchestrator] Step 0: Planning pipeline")
        plan_result = await self._call(self.planner_agent, "plan_pipeline", input_data)
        plan = plan_result.get("plan", {})
        self._share_memory("plan", plan)
        logger.info(f"[Orchestrator] Plan: {plan.get('reason')}")

        # ── Step 1-3: Validate ────────────────────────────────────────────────
        logger.info("[Orchestrator] Step 1: Validating input data")
        validation = await self._call(self.validation_agent, "validate_input_data", input_data)
        if validation.get("status") == "invalid":
            return {"status": "failed", "stage": "validation", "errors": validation.get("errors", []), "pipeline_log": self.pipeline_log}

        completeness = await self._call(self.validation_agent, "check_data_completeness", input_data)
        if completeness.get("status") in ("incomplete", "insufficient"):
            return {
                "status": "failed",
                "stage": "completeness",
                "missing": completeness.get("missing_entities", []),
                "insufficient_data": completeness.get("insufficient_data", []),
                "pipeline_log": self.pipeline_log
            }

        constraints = await self._call(self.validation_agent, "verify_constraints", input_data)
        if constraints.get("status") == "unsatisfiable":
            return {"status": "failed", "stage": "constraints", "issues": constraints.get("constraint_issues", []), "pipeline_log": self.pipeline_log}

        # ── HITL checkpoint after validation ─────────────────────────────────
        if hitl_enabled and "validation" in plan.get("hitl_after", []):
            self._save_run(run_id, "awaiting_approval", "post_validation", input_data,
                           checkpoint_data={"validation": validation, "completeness": completeness})
            raise HumanApprovalRequired(run_id, "post_validation", {
                "message": "Validation passed. Approve to continue with resource allocation.",
                "validation_summary": {
                    "warnings": validation.get("warnings", []),
                    "completeness_score": completeness.get("completeness_score"),
                }
            })

        # ── Step 4: Allocate resources ────────────────────────────────────────
        logger.info("[Orchestrator] Step 4: Allocating resources")
        allocation = await self._call(self.resource_agent, "allocate_resources", input_data)
        self._share_memory("allocation", allocation)

        # ── Step 5: Optimize ──────────────────────────────────────────────────
        logger.info(f"[Orchestrator] Step 5: Optimizing ({plan.get('solver_mode', 'cp_sat')} mode)")
        optimization = await self._call(self.optimization_agent, "optimize_timetable", input_data)
        if optimization.get("status") != "success":
            return {
                "status": "failed", "stage": "optimization",
                "message": optimization.get("message", "Optimization failed"),
                "suggestions": optimization.get("suggestions", []),
                "pipeline_log": self.pipeline_log
            }

        timetable = optimization["timetable"]
        self._share_memory("timetable_v1", timetable)

        # ── HITL checkpoint after optimization ───────────────────────────────
        if hitl_enabled and "optimization" in plan.get("hitl_after", []):
            self._save_run(run_id, "awaiting_approval", "post_optimization", input_data,
                           checkpoint_data={"timetable": timetable, "solver_status": optimization.get("solver_status")})
            raise HumanApprovalRequired(run_id, "post_optimization", {
                "message": f"Optimization complete ({optimization.get('solver_status')}). Preview timetable and approve to continue.",
                "total_assignments": len(timetable),
                "solve_time": optimization.get("solve_time"),
                "quality_metrics": optimization.get("quality_metrics", {}),
            })

        # ── Step 6: Conflict resolution (ReAct) ──────────────────────────────
        logger.info("[Orchestrator] Step 6: Detecting & resolving conflicts (ReAct)")
        conflict_result = await self._call(self.conflict_agent, "detect_conflicts", {"timetable": timetable})
        conflicts = conflict_result.get("conflicts", [])

        if conflicts:
            resolution = await self._call(self.conflict_agent, "resolve_conflicts", {
                "timetable": timetable,
                "conflicts": conflicts,
                "timeslots": input_data.get("timeslots", []),
                "rooms": input_data.get("rooms", []),
                "divisions": input_data.get("divisions", []),
            })
            timetable = resolution.get("resolved_timetable", timetable)
            self._share_memory("react_log", resolution.get("react_log", []))

        # ── Step 7: Utilization ───────────────────────────────────────────────
        logger.info("[Orchestrator] Step 7: Calculating utilization")
        utilization = await self._call(self.optimization_agent, "calculate_utilization", {"timetable": timetable})

        # ── Step 8: Analytics + self-reflection ──────────────────────────────
        logger.info("[Orchestrator] Step 8: Generating analytics & self-reflection")
        report = await self._call(self.analytics_agent, "generate_report", {"timetable": timetable})

        elapsed = round(time.time() - start, 2)
        logger.info(f"[Orchestrator] Pipeline completed in {elapsed}s")

        result = {
            "status": "success",
            "run_id": run_id,
            "timetable": timetable,
            "total_assignments": len(timetable),
            "conflicts_found": len(conflicts),
            "utilization": utilization.get("overall_metrics", {}),
            "report": report.get("report", {}),
            "solver_status": optimization.get("solver_status"),
            "solve_time": optimization.get("solve_time"),
            "generation_time": elapsed,
            "plan": plan,
            "pipeline_log": self.pipeline_log,
            "react_log": self._run_memory.get("react_log", []),
        }

        self._save_run(run_id, "completed", "done", input_data, result=result)
        return result

    # ── Resume after HITL approval ────────────────────────────────────────────

    async def resume(self, run_id: str, approved: bool, db_session_factory=None) -> dict[str, Any]:
        """
        Called after human approves/rejects a checkpoint.
        Loads checkpoint data from DB and continues (or aborts) the pipeline.
        """
        if not (self._long_term or db_session_factory):
            return {"status": "error", "message": "No DB session factory available for HITL resume"}

        factory = db_session_factory or self._long_term._factory
        from src.database.models import PipelineRun
        db = factory()
        try:
            run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
            if not run:
                return {"status": "error", "message": f"Run {run_id} not found"}
            if run.status != "awaiting_approval":
                return {"status": "error", "message": f"Run {run_id} is not awaiting approval (status: {run.status})"}

            if not approved:
                run.status = "rejected"
                db.commit()
                return {"status": "rejected", "run_id": run_id, "message": "Pipeline rejected by user"}

            input_data = json.loads(run.input_data)
            run.status = "running"
            db.commit()
        finally:
            db.close()

        # Re-run without HITL (already approved)
        return await self.run(input_data, run_id=run_id, hitl_enabled=False)

    # ── Sync wrapper ──────────────────────────────────────────────────────────

    def generate_timetable(self, input_data: dict[str, Any],
                           hitl_enabled: bool = False) -> dict[str, Any]:
        """Sync wrapper for FastAPI endpoints. HITL disabled by default for direct calls."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.run(input_data, hitl_enabled=hitl_enabled))
        except HumanApprovalRequired as e:
            return {
                "status": "awaiting_approval",
                "run_id": e.run_id,
                "stage": e.stage,
                "checkpoint": e.checkpoint_data,
            }
        finally:
            loop.close()
