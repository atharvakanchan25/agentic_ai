"""
Orchestrator - Coordinates all agents to generate the timetable
"""
import asyncio
import time
import logging
from typing import Dict, Any

from .validation_agent import ValidationAgent
from .optimization_agent import OptimizationAgent
from .conflict_resolution_agent import ConflictResolutionAgent
from .resource_allocation_agent import ResourceAllocationAgent
from .analytics_agent import AnalyticsAgent

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Coordinates the multi-agent pipeline:
    Validate → Allocate → Optimize → Resolve → Analyze
    """

    def __init__(self):
        self.validation_agent = ValidationAgent()
        self.resource_agent = ResourceAllocationAgent()
        self.optimization_agent = OptimizationAgent()
        self.conflict_agent = ConflictResolutionAgent()
        self.analytics_agent = AnalyticsAgent()
        self._initialized = False
        self.pipeline_log: list = []

    async def _initialize(self):
        if self._initialized:
            return
        for agent in [
            self.validation_agent,
            self.resource_agent,
            self.optimization_agent,
            self.conflict_agent,
            self.analytics_agent
        ]:
            # Run in standalone mode (no MCP server required for direct use)
            agent.mcp_enabled = False
            await agent._initialize_agent()
        self._initialized = True
        logger.info("[Orchestrator] All agents initialized")

    def _log(self, step: str, agent: str, status: str, detail: str = ""):
        entry = {"step": step, "agent": agent, "status": status, "detail": detail}
        self.pipeline_log.append(entry)
        logger.info(f"[{agent}] {step}: {status} {detail}")

    async def _call(self, agent, method: str, params: Dict) -> Dict:
        result = await agent.process_request({"method": method, "params": params})
        self._log(method, agent.agent_name, result.get("status", "unknown"))
        return result

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Full async pipeline"""
        await self._initialize()
        self.pipeline_log = []
        start = time.time()

        # Step 1 — Validate input
        logger.info("[Orchestrator] Step 1: Validating input data")
        validation = await self._call(self.validation_agent, "validate_input_data", input_data)
        if validation.get("status") == "invalid":
            return {
                "status": "failed",
                "stage": "validation",
                "errors": validation.get("errors", []),
                "pipeline_log": self.pipeline_log
            }

        # Step 2 — Check completeness
        logger.info("[Orchestrator] Step 2: Checking completeness")
        completeness = await self._call(self.validation_agent, "check_data_completeness", input_data)
        if completeness.get("status") == "incomplete":
            return {
                "status": "failed",
                "stage": "completeness",
                "missing": completeness.get("missing_entities", []),
                "pipeline_log": self.pipeline_log
            }

        # Step 3 — Verify constraints
        logger.info("[Orchestrator] Step 3: Verifying constraints")
        constraints = await self._call(self.validation_agent, "verify_constraints", input_data)
        if constraints.get("status") == "unsatisfiable":
            return {
                "status": "failed",
                "stage": "constraints",
                "issues": constraints.get("constraint_issues", []),
                "pipeline_log": self.pipeline_log
            }

        # Step 4 — Allocate resources
        logger.info("[Orchestrator] Step 4: Allocating resources")
        allocation = await self._call(self.resource_agent, "allocate_resources", input_data)

        # Step 5 — Optimize timetable
        logger.info("[Orchestrator] Step 5: Optimizing timetable")
        optimization = await self._call(self.optimization_agent, "optimize_timetable", input_data)
        if optimization.get("status") != "success":
            return {
                "status": "failed",
                "stage": "optimization",
                "message": optimization.get("message", "Optimization failed"),
                "suggestions": optimization.get("suggestions", []),
                "pipeline_log": self.pipeline_log
            }

        timetable = optimization["timetable"]

        # Step 6 — Detect and resolve conflicts
        logger.info("[Orchestrator] Step 6: Detecting conflicts")
        conflict_result = await self._call(self.conflict_agent, "detect_conflicts", {"timetable": timetable})
        conflicts = conflict_result.get("conflicts", [])

        if conflicts:
            logger.info(f"[Orchestrator] Resolving {len(conflicts)} conflicts")
            resolution = await self._call(self.conflict_agent, "resolve_conflicts", {
                "timetable": timetable,
                "conflicts": conflicts
            })
            timetable = resolution.get("resolved_timetable", timetable)

        # Step 7 — Calculate utilization
        logger.info("[Orchestrator] Step 7: Calculating utilization")
        utilization = await self._call(self.optimization_agent, "calculate_utilization", {"timetable": timetable})

        # Step 8 — Generate analytics and report
        logger.info("[Orchestrator] Step 8: Generating analytics")
        report = await self._call(self.analytics_agent, "generate_report", {"timetable": timetable})

        elapsed = round(time.time() - start, 2)
        logger.info(f"[Orchestrator] Pipeline completed in {elapsed}s")

        return {
            "status": "success",
            "timetable": timetable,
            "total_assignments": len(timetable),
            "conflicts_found": len(conflicts),
            "utilization": utilization.get("overall_metrics", {}),
            "report": report.get("report", {}),
            "solver_status": optimization.get("solver_status"),
            "solve_time": optimization.get("solve_time"),
            "generation_time": elapsed,
            "pipeline_log": self.pipeline_log
        }

    def generate_timetable(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync wrapper for use in FastAPI endpoints"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.run(input_data))
        finally:
            loop.close()
