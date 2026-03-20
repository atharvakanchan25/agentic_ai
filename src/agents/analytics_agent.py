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

    async def _handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
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
        elif method == "detect_anomalies":
            return await self.detect_anomalies(params)
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

    async def detect_anomalies(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flags unusual patterns in the timetable:
        - Divisions with 0 classes on a scheduled day
        - Subjects scheduled far more than their hours_per_week
        - Rooms used in every single slot (overloaded)
        """
        timetable: List[Dict] = data.get("timetable", [])
        subjects_meta: List[Dict] = data.get("subjects", [])
        anomalies: List[str] = []

        if not timetable:
            return {"status": "success", "anomalies": []}

        # Division × day class count
        div_day: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        all_days: set = set()
        for e in timetable:
            div_day[str(e.get("division_id"))][e.get("day", "")] += 1
            all_days.add(e.get("day", ""))

        for div_id, day_counts in div_day.items():
            for day in all_days:
                if day_counts.get(day, 0) == 0:
                    anomalies.append(
                        f"Division {div_id} has 0 classes on {day} — possible scheduling gap."
                    )

        # Subject over-scheduling
        subject_hours_meta = {s["name"]: s.get("hours_per_week", 0) for s in subjects_meta}
        subject_scheduled: Dict[str, int] = defaultdict(int)
        for e in timetable:
            subject_scheduled[e.get("subject_name", "")] += 1

        for subj, count in subject_scheduled.items():
            expected = subject_hours_meta.get(subj, 0)
            if expected and count > expected * len({e["division_id"] for e in timetable if e.get("subject_name") == subj}) * 1.5:
                anomalies.append(
                    f"Subject '{subj}' is scheduled {count} times — significantly above expected."
                )

        # Overloaded rooms
        room_slot_count: Dict[str, int] = defaultdict(int)
        total_slots = len(all_days) * max((e.get("slot_number", 0) for e in timetable), default=1)
        for e in timetable:
            room_slot_count[str(e.get("room_id"))] += 1

        for room_id, count in room_slot_count.items():
            if total_slots > 0 and count >= total_slots:
                anomalies.append(
                    f"Room {room_id} is used in every available slot — may be a bottleneck."
                )

        return {"status": "success", "anomalies": anomalies, "anomaly_count": len(anomalies)}

    async def generate_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        timetable = data.get("timetable", [])
        analytics  = (await self.analyze_timetable({"timetable": timetable})).get("analytics", {})
        insights   = (await self.generate_insights({"timetable": timetable})).get("insights", [])
        metrics    = (await self.calculate_metrics({"timetable": timetable})).get("metrics", {})
        reflection = (await self.self_reflect({"timetable": timetable}))
        anomalies  = (await self.detect_anomalies(data)).get("anomalies", [])

        return {
            "status": "success",
            "report": {
                "summary": analytics,
                "insights": insights,
                "performance_metrics": metrics,
                "quality_score": reflection.get("quality_score"),
                "critique": reflection.get("critique", []),
                "improvement_suggestions": reflection.get("suggestions", []),
                "anomalies": anomalies,
                "total_entries": len(timetable)
            }
        }
