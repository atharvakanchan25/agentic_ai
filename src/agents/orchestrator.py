"""
Orchestrator - Coordinates all agents:
  Plan → Validate → BusinessRules → Allocate → Optimize → [HITL] → Resolve → Analyze → Explain → Reflect
  + Parallel department scheduling
  + Greedy fallback on CP-SAT failure
  + Solver outcome persistence for PlannerAgent learning
  + FeedbackAgent for HITL decision learning
  + ExplainabilityAgent for timetable transparency
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
from .feedback_agent import FeedbackAgent
from .explainability_agent import ExplainabilityAgent
from .memory import ShortTermMemory, LongTermMemory

logger = logging.getLogger(__name__)


class HumanApprovalRequired(Exception):
    def __init__(self, run_id: str, stage: str, checkpoint_data: dict):
        self.run_id = run_id
        self.stage = stage
        self.checkpoint_data = checkpoint_data
        super().__init__(f"Human approval required at stage '{stage}' for run {run_id}")


class AgentOrchestrator:

    def __init__(self, db_session_factory=None):
        self.validation_agent    = ValidationAgent()
        self.resource_agent      = ResourceAllocationAgent()
        self.optimization_agent  = OptimizationAgent()
        self.conflict_agent      = ConflictResolutionAgent()
        self.analytics_agent     = AnalyticsAgent()
        self.planner_agent       = PlannerAgent()
        self.feedback_agent      = FeedbackAgent()
        self.explainability_agent = ExplainabilityAgent()

        self._initialized = False
        self.pipeline_log: list = []

        self._run_memory = ShortTermMemory()
        self._long_term  = LongTermMemory(db_session_factory) if db_session_factory else None

        self._all_agents = [
            self.validation_agent, self.resource_agent,
            self.optimization_agent, self.conflict_agent,
            self.analytics_agent, self.planner_agent,
            self.feedback_agent, self.explainability_agent,
        ]

    async def _initialize(self):
        if self._initialized:
            return
        for agent in self._all_agents:
            agent.mcp_enabled = False
            await agent._initialize_agent()
            agent.long_term_memory = self._long_term
        self._initialized = True
        logger.info("[Orchestrator] All agents initialized")

    def _share_memory(self, key: str, value: Any):
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
            run.stage  = stage
            run.input_data = json.dumps(input_data)
            if checkpoint_data is not None:
                run.checkpoint_data = json.dumps(checkpoint_data)
            if result is not None:
                run.result = json.dumps(result)
            db.commit()
        finally:
            db.close()

    # ── Parallel department scheduling ────────────────────────────────────────

    async def _schedule_department(self, dept_input: dict, plan: dict) -> dict:
        """Run optimize → conflict-resolve for a single department's data."""
        optimization = await self._call(
            self.optimization_agent, "optimize_timetable",
            {**dept_input, "solver_mode": plan.get("solver_mode", "cp_sat")}
        )
        if optimization.get("status") != "success":
            return optimization

        timetable = optimization["timetable"]
        conflict_result = await self._call(self.conflict_agent, "detect_conflicts", {"timetable": timetable})
        conflicts = conflict_result.get("conflicts", [])
        if conflicts:
            resolution = await self._call(self.conflict_agent, "resolve_conflicts", {
                "timetable": timetable,
                "conflicts": conflicts,
                "timeslots": dept_input.get("timeslots", []),
                "rooms":     dept_input.get("rooms", []),
                "divisions": dept_input.get("divisions", []),
            })
            timetable = resolution.get("resolved_timetable", timetable)
        optimization["timetable"] = timetable
        return optimization

    # ── Main pipeline ─────────────────────────────────────────────────────────

    async def run(self, input_data: dict[str, Any], run_id: str = None,
                  hitl_enabled: bool = True) -> dict[str, Any]:
        await self._initialize()
        self.pipeline_log = []
        self._run_memory.clear()
        for agent in self._all_agents:
            agent.memory.clear()

        run_id = run_id or str(uuid.uuid4())
        start  = time.time()

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

        # ── Step 1: Validate ──────────────────────────────────────────────────
        logger.info("[Orchestrator] Step 1: Validating input data")
        validation = await self._call(self.validation_agent, "validate_input_data", input_data)
        if validation.get("status") == "invalid":
            return {"status": "failed", "stage": "validation", "errors": validation.get("errors", []), "pipeline_log": self.pipeline_log}

        completeness = await self._call(self.validation_agent, "check_data_completeness", input_data)
        if completeness.get("status") == "incomplete":
            return {"status": "failed", "stage": "completeness", "missing": completeness.get("missing_entities", []), "pipeline_log": self.pipeline_log}

        constraints = await self._call(self.validation_agent, "verify_constraints", input_data)
        if constraints.get("status") == "unsatisfiable":
            return {"status": "failed", "stage": "constraints", "issues": constraints.get("constraint_issues", []), "pipeline_log": self.pipeline_log}

        # ── Step 2: Business rules ────────────────────────────────────────────
        logger.info("[Orchestrator] Step 2: Checking business rules")
        biz_rules = await self._call(self.validation_agent, "check_business_rules", input_data)
        # Violations are warnings — don't block, but surface them
        biz_warnings = biz_rules.get("rule_violations", []) + biz_rules.get("warnings", [])

        # ── HITL checkpoint after validation ─────────────────────────────────
        if hitl_enabled and "validation" in plan.get("hitl_after", []):
            self._save_run(run_id, "awaiting_approval", "post_validation", input_data,
                           checkpoint_data={"validation": validation, "completeness": completeness})
            raise HumanApprovalRequired(run_id, "post_validation", {
                "message": "Validation passed. Approve to continue with resource allocation.",
                "validation_summary": {
                    "warnings": validation.get("warnings", []),
                    "completeness_score": completeness.get("completeness_score"),
                    "business_rule_warnings": biz_warnings,
                }
            })

        # ── Step 3: Allocate resources ────────────────────────────────────────
        logger.info("[Orchestrator] Step 3: Allocating resources (load-balanced)")
        allocation = await self._call(self.resource_agent, "allocate_resources", input_data)
        self._share_memory("allocation", allocation)

        # ── Step 4: Optimize (parallel or sequential) ─────────────────────────
        logger.info(f"[Orchestrator] Step 4: Optimizing ({plan.get('solver_mode', 'cp_sat')} mode, parallel={plan.get('parallel_depts')})")

        if plan.get("parallel_depts") and len(input_data.get("divisions", [])) > 4:
            # Group divisions by department and schedule in parallel
            dept_groups: dict[int, list] = {}
            for div in input_data.get("divisions", []):
                dept_groups.setdefault(div["department_id"], []).append(div)

            tasks = []
            for dept_id, divs in dept_groups.items():
                dept_subjects = [s for s in input_data.get("subjects", []) if s.get("department_id") == dept_id]
                dept_input = {**input_data, "divisions": divs, "subjects": dept_subjects}
                tasks.append(self._schedule_department(dept_input, plan))

            dept_results = await asyncio.gather(*tasks, return_exceptions=True)

            timetable = []
            conflicts_found = 0
            optimization_status = "success"
            solve_time = 0.0
            quality_metrics: dict = {}

            for res in dept_results:
                if isinstance(res, Exception) or res.get("status") != "success":
                    optimization_status = "partial"
                    continue
                timetable.extend(res.get("timetable", []))
                solve_time = max(solve_time, res.get("solve_time", 0))
                quality_metrics = res.get("quality_metrics", quality_metrics)

            optimization = {
                "status": optimization_status,
                "solver_status": "parallel_complete",
                "solver_mode": plan.get("solver_mode"),
                "timetable": timetable,
                "solve_time": solve_time,
                "quality_metrics": quality_metrics,
            }
        else:
            optimization = await self._call(
                self.optimization_agent, "optimize_timetable",
                {**input_data, "solver_mode": plan.get("solver_mode", "cp_sat")}
            )

        if optimization.get("status") != "success":
            # Persist failure so PlannerAgent learns
            if self._long_term:
                self._long_term.remember_solver_outcome(
                    run_id, plan.get("cp_vars", 0),
                    plan.get("solver_mode", "cp_sat"), "failed",
                    optimization.get("solve_time", 0)
                )
            return {
                "status": "failed", "stage": "optimization",
                "message": optimization.get("message", "Optimization failed"),
                "suggestions": optimization.get("suggestions", []),
                "pipeline_log": self.pipeline_log,
            }

        timetable = optimization["timetable"]
        self._share_memory("timetable_v1", timetable)

        # Persist solver outcome for PlannerAgent learning
        if self._long_term:
            self._long_term.remember_solver_outcome(
                run_id, plan.get("cp_vars", 0),
                optimization.get("solver_mode", plan.get("solver_mode", "cp_sat")),
                "success", optimization.get("solve_time", 0)
            )

        # ── HITL checkpoint after optimization ───────────────────────────────
        if hitl_enabled and "optimization" in plan.get("hitl_after", []):
            self._save_run(run_id, "awaiting_approval", "post_optimization", input_data,
                           checkpoint_data={"timetable": timetable, "solver_status": optimization.get("solver_status")})
            raise HumanApprovalRequired(run_id, "post_optimization", {
                "message": f"Optimization complete ({optimization.get('solver_status')}). Preview timetable and approve to continue.",
                "total_assignments": len(timetable),
                "solve_time": optimization.get("solve_time"),
                "quality_metrics": optimization.get("quality_metrics", {}),
                "fallback_used": optimization.get("fallback_used", False),
            })

        # ── Step 5: Conflict resolution (ReAct) ──────────────────────────────
        logger.info("[Orchestrator] Step 5: Detecting & resolving conflicts (ReAct)")
        conflict_result = await self._call(self.conflict_agent, "detect_conflicts", {"timetable": timetable})
        conflicts = conflict_result.get("conflicts", [])

        if conflicts:
            resolution = await self._call(self.conflict_agent, "resolve_conflicts", {
                "timetable": timetable,
                "conflicts": conflicts,
                "timeslots": input_data.get("timeslots", []),
                "rooms":     input_data.get("rooms", []),
                "divisions": input_data.get("divisions", []),
            })
            timetable = resolution.get("resolved_timetable", timetable)
            self._share_memory("react_log", resolution.get("react_log", []))

        # ── Step 6: Utilization ───────────────────────────────────────────────
        logger.info("[Orchestrator] Step 6: Calculating utilization")
        utilization = await self._call(self.optimization_agent, "calculate_utilization", {"timetable": timetable})

        # ── Step 7: Analytics + anomaly detection + self-reflection ──────────
        logger.info("[Orchestrator] Step 7: Generating analytics, anomalies & self-reflection")
        report = await self._call(self.analytics_agent, "generate_report", {
            "timetable": timetable,
            "subjects": input_data.get("subjects", []),
        })

        # ── Step 8: Explainability ────────────────────────────────────────────
        logger.info("[Orchestrator] Step 8: Generating timetable explanation")
        explanation = await self._call(self.explainability_agent, "explain_timetable", {
            "timetable": timetable,
            "plan": {**plan, "fallback_used": optimization.get("fallback_used", False),
                     "cp_sat_failure_reason": optimization.get("cp_sat_failure_reason", "")},
        })

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
            "explanation": explanation.get("explanation", []),
            "solver_status": optimization.get("solver_status"),
            "solver_mode": optimization.get("solver_mode"),
            "fallback_used": optimization.get("fallback_used", False),
            "solve_time": optimization.get("solve_time"),
            "generation_time": elapsed,
            "plan": plan,
            "business_rule_warnings": biz_warnings,
            "pipeline_log": self.pipeline_log,
            "react_log": self._run_memory.get("react_log", []),
        }

        self._save_run(run_id, "completed", "done", input_data, result=result)
        return result

    # ── Resume after HITL approval ────────────────────────────────────────────

    async def resume(self, run_id: str, approved: bool,
                     notes: str = "", db_session_factory=None) -> dict[str, Any]:
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

            stage = run.stage or ""

            if not approved:
                run.status = "rejected"
                db.commit()
                # Record rejection in FeedbackAgent
                if self._long_term:
                    await self._initialize()
                    await self._call(self.feedback_agent, "record_feedback", {
                        "run_id": run_id, "stage": stage, "approved": False, "notes": notes,
                    })
                return {"status": "rejected", "run_id": run_id, "message": "Pipeline rejected by user"}

            input_data = json.loads(run.input_data)
            run.status = "running"
            db.commit()
        finally:
            db.close()

        # Record approval
        if self._long_term:
            await self._initialize()
            await self._call(self.feedback_agent, "record_feedback", {
                "run_id": run_id, "stage": stage, "approved": True, "notes": notes,
            })

        return await self.run(input_data, run_id=run_id, hitl_enabled=False)

    # ── Sync wrapper ──────────────────────────────────────────────────────────

    def generate_timetable(self, input_data: dict[str, Any],
                           hitl_enabled: bool = False) -> dict[str, Any]:
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
