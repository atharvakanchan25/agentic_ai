"""
Planner Agent - Decomposes the scheduling task dynamically.
Learns from past solver outcomes stored in LongTermMemory.
"""
from typing import Any
from .base_agent import BaseAgent


class PlannerAgent(BaseAgent):

    def __init__(self):
        super().__init__("PlannerAgent", ["plan_pipeline"])

    async def _initialize_agent(self): pass
    def _register_custom_handlers(self): pass
    async def _cleanup_agent(self): pass

    async def _handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        method = request.get("method")
        if method == "plan_pipeline":
            return await self.plan_pipeline(request.get("params", {}))
        return {"status": "error", "message": f"Unknown method: {method}"}

    async def plan_pipeline(self, data: dict[str, Any]) -> dict[str, Any]:
        divisions  = data.get("divisions", [])
        subjects   = data.get("subjects", [])
        rooms      = data.get("rooms", [])
        timeslots  = data.get("timeslots", [])

        n_divisions = len(divisions)
        n_subjects  = len(subjects)
        n_timeslots = len(timeslots)

        cp_vars = n_divisions * n_subjects * len(rooms) * n_timeslots
        is_large = cp_vars > 5_000

        # ── Learn from past runs ──────────────────────────────────────────────
        solver_mode = "greedy" if is_large else "cp_sat"
        reason_suffix = ""

        if self.long_term_memory:
            past = self.long_term_memory.recall_solver_outcomes(limit=10)
            if past:
                # Find outcomes for similar problem sizes (within 50% of current)
                similar = [
                    p for p in past
                    if abs(p.get("cp_vars", 0) - cp_vars) / max(cp_vars, 1) < 0.5
                ]
                if similar:
                    cp_sat_failures = sum(
                        1 for p in similar
                        if p.get("solver_mode") == "cp_sat" and p.get("status") != "success"
                    )
                    cp_sat_successes = sum(
                        1 for p in similar
                        if p.get("solver_mode") == "cp_sat" and p.get("status") == "success"
                    )
                    # If CP-SAT failed more than it succeeded on similar problems, use greedy
                    if cp_sat_failures > cp_sat_successes and not is_large:
                        solver_mode = "greedy"
                        reason_suffix = f" (switched to greedy: CP-SAT failed {cp_sat_failures}/{len(similar)} similar runs)"
                    elif cp_sat_successes > 0 and is_large:
                        # CP-SAT worked on similar large problems before — try it
                        solver_mode = "cp_sat"
                        reason_suffix = f" (CP-SAT succeeded {cp_sat_successes}/{len(similar)} similar runs despite size)"

        plan: dict[str, Any] = {
            "solver_mode":    solver_mode,
            "cp_vars":        cp_vars,
            "skip_steps":     [],
            "parallel_depts": is_large and n_divisions > 4,
            "hitl_after":     ["validation", "optimization"],
            "reason":         "",
        }

        if is_large:
            plan["reason"] = (
                f"Large problem ({cp_vars:,} CP variables). "
                f"Using {solver_mode} solver."
            )
        else:
            plan["reason"] = (
                f"Small problem ({cp_vars:,} CP variables). "
                f"Using {solver_mode} solver."
            )

        plan["reason"] += reason_suffix

        if not data.get("faculty"):
            plan["skip_steps"].append("faculty_constraints")
            plan["reason"] += " No faculty data — skipping faculty constraints."

        self.log_action(f"Plan created: {plan['solver_mode']} mode, skip={plan['skip_steps']}")
        return {"status": "success", "plan": plan}
