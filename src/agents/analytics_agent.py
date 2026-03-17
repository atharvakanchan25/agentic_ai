"""
Analytics Agent - Generates insights, metrics, and reports from timetable data
"""
from typing import Dict, Any, List
from collections import defaultdict
from .base_agent import BaseAgent
from .state_machine import AgentState
from .tools import score_timetable


class AnalyticsAgent(BaseAgent):

    def __init__(self):
        super().__init__("AnalyticsAgent", [
            "analyze_timetable",
            "generate_insights",
            "calculate_metrics",
            "generate_report"
        ])

    async def _initialize_agent(self):
        self.register_tool("score_timetable", score_timetable)
        self.log_action("AnalyticsAgent initialized with self-reflection")

    def _register_custom_handlers(self):
        pass

    async def _cleanup_agent(self):
        pass

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        method = request.get("method")
        params = request.get("params", {})

        if method == "analyze_timetable":
            return await self.analyze_timetable(params)
        elif method == "generate_insights":
            return await self.generate_insights(params)
        elif method == "calculate_metrics":
            return await self.calculate_metrics(params)
        elif method == "generate_report":
            return await self.generate_report(params)
        elif method == "self_reflect":
            return await self.self_reflect(params)
        return {"status": "error", "message": f"Unknown method: {method}"}

    async def analyze_timetable(self, data: Dict[str, Any]) -> Dict[str, Any]:
        timetable: List[Dict] = data.get("timetable", [])

        if not timetable:
            return {"status": "error", "message": "No timetable data provided"}

        # Day distribution
        day_dist: Dict[str, int] = defaultdict(int)
        # Subject distribution
        subject_dist: Dict[str, int] = defaultdict(int)
        # Division load
        division_load: Dict[str, int] = defaultdict(int)
        # Room usage
        room_usage: Dict[str, int] = defaultdict(int)

        for entry in timetable:
            day_dist[entry.get("day", "Unknown")] += 1
            subject_dist[entry.get("subject_name", "Unknown")] += 1
            division_load[entry.get("division_name", "Unknown")] += 1
            room_usage[str(entry.get("room_number", "Unknown"))] += 1

        return {
            "status": "success",
            "analytics": {
                "total_assignments": len(timetable),
                "unique_divisions": len(division_load),
                "unique_subjects": len(subject_dist),
                "unique_rooms": len(room_usage),
                "unique_days": len(day_dist),
                "day_distribution": dict(day_dist),
                "subject_distribution": dict(subject_dist),
                "division_load": dict(division_load),
                "room_usage": dict(room_usage)
            }
        }

    async def generate_insights(self, data: Dict[str, Any]) -> Dict[str, Any]:
        timetable: List[Dict] = data.get("timetable", [])
        insights = []

        if not timetable:
            return {"status": "success", "insights": ["No timetable data to analyze"]}

        # Day balance check
        day_dist: Dict[str, int] = defaultdict(int)
        for entry in timetable:
            day_dist[entry.get("day", "Unknown")] += 1

        if day_dist:
            max_day = max(day_dist, key=day_dist.get)
            min_day = min(day_dist, key=day_dist.get)
            if day_dist[max_day] > day_dist[min_day] * 1.5:
                insights.append(
                    f"Uneven workload: {max_day} has {day_dist[max_day]} classes vs "
                    f"{min_day} with {day_dist[min_day]}. Consider rebalancing."
                )
            else:
                insights.append("Daily workload is well balanced across the week.")

        # Room utilization check
        room_usage: Dict[str, int] = defaultdict(int)
        for entry in timetable:
            room_usage[str(entry.get("room_id"))] += 1

        if room_usage:
            avg = sum(room_usage.values()) / len(room_usage)
            underused = [r for r, c in room_usage.items() if c < avg * 0.5]
            if underused:
                insights.append(f"{len(underused)} room(s) are significantly underutilized.")

        # Lab scheduling check
        lab_entries = [e for e in timetable if e.get("is_lab", False)]
        if lab_entries:
            insights.append(f"{len(lab_entries)} lab sessions scheduled successfully.")

        if not insights:
            insights.append("Timetable looks good with no major issues detected.")

        return {"status": "success", "insights": insights}

    async def calculate_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        timetable: List[Dict] = data.get("timetable", [])

        if not timetable:
            return {"status": "success", "metrics": {
                "efficiency_score": 0, "balance_score": 0,
                "utilization_score": 0, "overall_score": 0
            }}

        total = len(timetable)
        unique_slots = len(set(f"{e['day']}_{e['slot_number']}" for e in timetable))
        unique_rooms = len(set(e["room_id"] for e in timetable))

        # Efficiency: how densely slots are used
        efficiency = min(100.0, (total / max(unique_slots, 1)) * 100)

        # Balance: variance in day distribution
        day_dist: Dict[str, int] = defaultdict(int)
        for e in timetable:
            day_dist[e.get("day", "Unknown")] += 1

        values = list(day_dist.values())
        if len(values) > 1:
            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            balance = max(0.0, 100.0 - variance)
        else:
            balance = 100.0

        # Utilization: room usage density
        utilization = min(100.0, (total / max(unique_rooms * unique_slots, 1)) * 100)

        overall = round((efficiency * 0.3 + balance * 0.4 + utilization * 0.3), 2)

        return {
            "status": "success",
            "metrics": {
                "efficiency_score": round(efficiency, 2),
                "balance_score": round(balance, 2),
                "utilization_score": round(utilization, 2),
                "overall_score": overall
            }
        }

    async def self_reflect(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Critique the timetable and return actionable improvement suggestions.
        Uses the score_timetable tool then reasons about the issues found.
        """
        self._set_state(AgentState.REFLECTING)
        timetable: List[Dict] = data.get("timetable", [])

        score_result = self.use_tool("score_timetable", timetable=timetable)
        score = score_result["score"]
        issues = score_result["issues"]
        gaps   = score_result["total_gaps"]

        critique: List[str] = []
        suggestions: List[str] = []

        for issue in issues:
            if issue["type"] == "consecutive_overload":
                critique.append(
                    f"Division {issue['division_id']} has {issue['consecutive_count']} consecutive lectures on {issue['day']}."
                )
                suggestions.append(
                    f"Insert a break for division {issue['division_id']} on {issue['day']} — split lectures across the day."
                )

        if gaps > 0:
            critique.append(f"Total of {gaps} free-slot gaps detected across all divisions.")
            suggestions.append("Compact schedules to reduce gaps — students prefer back-to-back classes.")

        if score >= 80:
            critique.append("Overall timetable quality is good.")
        elif score >= 50:
            critique.append("Timetable quality is acceptable but has room for improvement.")
        else:
            critique.append("Timetable quality is poor — consider re-running optimization with tighter constraints.")

        self._set_state(AgentState.COMPLETED)
        self.log_action(f"Self-reflection complete. Score: {score}")
        return {
            "status": "success",
            "quality_score": score,
            "critique": critique,
            "suggestions": suggestions,
        }

    async def generate_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        timetable = data.get("timetable", [])
        analytics   = (await self.analyze_timetable({"timetable": timetable})).get("analytics", {})
        insights    = (await self.generate_insights({"timetable": timetable})).get("insights", [])
        metrics     = (await self.calculate_metrics({"timetable": timetable})).get("metrics", {})
        reflection  = (await self.self_reflect({"timetable": timetable}))

        return {
            "status": "success",
            "report": {
                "summary": analytics,
                "insights": insights,
                "performance_metrics": metrics,
                "quality_score": reflection.get("quality_score"),
                "critique": reflection.get("critique", []),
                "improvement_suggestions": reflection.get("suggestions", []),
                "total_entries": len(timetable)
            }
        }
