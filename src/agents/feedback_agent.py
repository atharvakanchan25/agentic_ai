"""
Feedback Agent - Learns from HITL approve/reject decisions.
Stores user preferences in LongTermMemory to influence future pipeline runs.
"""
from typing import Any
from .base_agent import BaseAgent


class FeedbackAgent(BaseAgent):

    def __init__(self):
        super().__init__("FeedbackAgent", ["record_feedback", "get_preferences"])

    async def _initialize_agent(self):
        self.log_action("FeedbackAgent initialized")

    def _register_custom_handlers(self): pass
    async def _cleanup_agent(self): pass

    async def process_request(self, request: dict[str, Any]) -> dict[str, Any]:
        method = request.get("method")
        params = request.get("params", {})
        if method == "record_feedback":
            return await self.record_feedback(params)
        elif method == "get_preferences":
            return await self.get_preferences(params)
        return {"status": "error", "message": f"Unknown method: {method}"}

    async def record_feedback(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Called after a HITL decision. Persists the decision and any notes
        so future PlannerAgent runs can factor in user preferences.
        """
        run_id   = data.get("run_id", "")
        stage    = data.get("stage", "")
        approved = data.get("approved", False)
        notes    = data.get("notes", "")

        if not self.long_term_memory:
            return {"status": "skipped", "message": "No long-term memory available"}

        self.long_term_memory.remember_feedback(run_id, stage, approved, notes)

        # If rejected, store the quality metrics as a "bad pattern" signal
        if not approved:
            quality = data.get("quality_metrics", {})
            if quality:
                self.long_term_memory.remember(
                    self.agent_name, "rejected_quality_profile",
                    {"stage": stage, "quality_metrics": quality, "notes": notes},
                    run_id=run_id,
                )

        self.log_action(f"Recorded {'approval' if approved else 'rejection'} for run {run_id} at stage '{stage}'")
        return {"status": "success", "recorded": True}

    async def get_preferences(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Returns a summary of past HITL decisions to guide the planner.
        """
        if not self.long_term_memory:
            return {"status": "success", "preferences": {}, "approval_rate": None}

        history = self.long_term_memory.recall_feedback(limit=50)
        if not history:
            return {"status": "success", "preferences": {}, "approval_rate": None}

        total    = len(history)
        approved = sum(1 for h in history if h.get("approved"))
        approval_rate = round(approved / total * 100, 1)

        # Summarise which stages get rejected most
        stage_rejections: dict[str, int] = {}
        for h in history:
            if not h.get("approved"):
                s = h.get("stage", "unknown")
                stage_rejections[s] = stage_rejections.get(s, 0) + 1

        preferences = {
            "most_rejected_stage": max(stage_rejections, key=stage_rejections.get) if stage_rejections else None,
            "stage_rejection_counts": stage_rejections,
        }

        return {
            "status": "success",
            "approval_rate": approval_rate,
            "total_decisions": total,
            "preferences": preferences,
        }
