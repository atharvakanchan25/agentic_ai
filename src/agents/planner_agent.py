"""
Planner Agent - Decomposes the scheduling task dynamically based on input size/complexity.
Decides which pipeline steps to run and in what mode (greedy vs CP-SAT).
"""
from typing import Any
from .base_agent import BaseAgent


class PlannerAgent(BaseAgent):

    def __init__(self):
        super().__init__("PlannerAgent", ["plan_pipeline"])

    async def _initialize_agent(self): pass
    def _register_custom_handlers(self): pass
    async def _cleanup_agent(self): pass

    async def process_request(self, request: dict[str, Any]) -> dict[str, Any]:
        method = request.get("method")
        if method == "plan_pipeline":
            return await self.plan_pipeline(request.get("params", {}))
        return {"status": "error", "message": f"Unknown method: {method}"}

    async def plan_pipeline(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Analyse input and return a plan dict that the orchestrator follows.

        Plan fields:
          solver_mode   : "greedy" | "cp_sat"
          skip_steps    : list of step names to skip
          parallel_depts: bool — schedule each dept independently in parallel
          hitl_after    : list of step names where human approval is required
          reason        : human-readable explanation
        """
        divisions  = data.get("divisions", [])
        subjects   = data.get("subjects", [])
        rooms      = data.get("rooms", [])
        timeslots  = data.get("timeslots", [])

        n_divisions = len(divisions)
        n_subjects  = len(subjects)
        n_timeslots = len(timeslots)

        # Complexity heuristic: variable count for CP-SAT
        cp_vars = n_divisions * n_subjects * len(rooms) * n_timeslots
        is_large = cp_vars > 5_000

        plan: dict[str, Any] = {
            "solver_mode":    "greedy" if is_large else "cp_sat",
            "skip_steps":     [],
            "parallel_depts": is_large and n_divisions > 4,
            "hitl_after":     ["validation", "optimization"],  # always ask after these
            "reason":         "",
        }

        if is_large:
            plan["reason"] = (
                f"Large problem ({cp_vars:,} CP variables). "
                "Using greedy solver and parallel department scheduling."
            )
        else:
            plan["reason"] = (
                f"Small problem ({cp_vars:,} CP variables). "
                "Using full CP-SAT solver."
            )

        # If no faculty data, skip faculty-constraint step
        if not data.get("faculty"):
            plan["skip_steps"].append("faculty_constraints")
            plan["reason"] += " No faculty data — skipping faculty constraints."

        self.log_action(f"Plan created: {plan['solver_mode']} mode, skip={plan['skip_steps']}")
        return {"status": "success", "plan": plan}
