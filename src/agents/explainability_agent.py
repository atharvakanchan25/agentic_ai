"""
Explainability Agent - Explains why a timetable entry was assigned
a particular room, timeslot, and faculty member.
"""
from typing import Any
from .base_agent import BaseAgent


class ExplainabilityAgent(BaseAgent):

    def __init__(self):
        super().__init__("ExplainabilityAgent", ["explain_entry", "explain_timetable"])

    async def _initialize_agent(self):
        self.log_action("ExplainabilityAgent initialized")

    def _register_custom_handlers(self): pass
    async def _cleanup_agent(self): pass

    async def process_request(self, request: dict[str, Any]) -> dict[str, Any]:
        method = request.get("method")
        params = request.get("params", {})
        if method == "explain_entry":
            return await self.explain_entry(params)
        elif method == "explain_timetable":
            return await self.explain_timetable(params)
        return {"status": "error", "message": f"Unknown method: {method}"}

    async def explain_entry(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Given a single timetable entry + full context, explain the assignment.
        """
        entry     = data.get("entry", {})
        timetable = data.get("timetable", [])
        rooms     = data.get("rooms", [])
        faculty   = data.get("faculty", [])
        divisions = data.get("divisions", [])

        if not entry:
            return {"status": "error", "message": "No entry provided"}

        reasons: list[str] = []

        # ── Room explanation ──────────────────────────────────────────────────
        room = next((r for r in rooms if r["id"] == entry.get("room_id")), None)
        division = next((d for d in divisions if d["id"] == entry.get("division_id")), None)

        if room and division:
            student_count = division.get("student_count", 0)
            capacity      = room.get("capacity", 0)
            is_lab        = entry.get("is_lab", False)

            reasons.append(
                f"Room '{room['room_number']}' (capacity {capacity}) was chosen because "
                f"division '{entry.get('division_name')}' has {student_count} students "
                f"and this is the {'smallest sufficient' if capacity >= student_count else 'best available'} room."
            )
            if is_lab:
                reasons.append(
                    f"This is a lab subject, so a lab room was required. "
                    f"Room '{room['room_number']}' is {'a lab room' if room.get('is_lab') else 'the only available room (no lab room free)'}."
                )

            # Check if other rooms were occupied at this slot
            slot_key = (entry.get("day"), entry.get("slot_number"))
            occupied_rooms = {
                e["room_id"] for e in timetable
                if e.get("day") == slot_key[0] and e.get("slot_number") == slot_key[1]
                and e is not entry
            }
            if occupied_rooms:
                reasons.append(
                    f"{len(occupied_rooms)} other room(s) were already occupied at "
                    f"{entry.get('day')} slot {entry.get('slot_number')}."
                )

        # ── Timeslot explanation ──────────────────────────────────────────────
        div_slots_on_day = [
            e for e in timetable
            if e.get("division_id") == entry.get("division_id")
            and e.get("day") == entry.get("day")
            and e is not entry
        ]
        reasons.append(
            f"Slot {entry.get('slot_number')} on {entry.get('day')} was selected. "
            f"Division '{entry.get('division_name')}' has {len(div_slots_on_day)} other class(es) on this day."
        )

        # ── Faculty explanation ───────────────────────────────────────────────
        fac = next((f for f in faculty if f["id"] == entry.get("faculty_id")), None)
        if fac:
            fac_load = sum(1 for e in timetable if e.get("faculty_id") == fac["id"])
            reasons.append(
                f"Faculty '{fac['name']}' was assigned because they belong to the same department "
                f"and currently have {fac_load} total slot(s) assigned (load-balanced selection)."
            )
        elif entry.get("faculty_id") is None:
            reasons.append("No faculty was assigned — no faculty data available for this department.")

        return {
            "status": "success",
            "entry": entry,
            "explanation": reasons,
        }

    async def explain_timetable(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Returns a high-level explanation of the overall timetable decisions.
        """
        timetable = data.get("timetable", [])
        plan      = data.get("plan", {})

        if not timetable:
            return {"status": "error", "message": "No timetable provided"}

        summary: list[str] = []

        solver_mode = plan.get("solver_mode", "unknown")
        cp_vars     = plan.get("cp_vars", 0)
        reason      = plan.get("reason", "")

        summary.append(
            f"The timetable was generated using the '{solver_mode}' solver "
            f"({cp_vars:,} decision variables). {reason}"
        )

        total = len(timetable)
        unique_divs  = len({e["division_id"] for e in timetable})
        unique_rooms = len({e["room_id"] for e in timetable})
        unique_days  = len({e["day"] for e in timetable})

        summary.append(
            f"A total of {total} class assignments were made across "
            f"{unique_divs} division(s), {unique_rooms} room(s), and {unique_days} day(s)."
        )

        lab_count = sum(1 for e in timetable if e.get("is_lab"))
        if lab_count:
            summary.append(f"{lab_count} lab session(s) were scheduled in dedicated lab rooms.")

        if plan.get("fallback_used"):
            summary.append(
                f"Note: CP-SAT solver failed ({plan.get('cp_sat_failure_reason', 'unknown reason')}). "
                "The greedy fallback solver was used instead."
            )

        return {"status": "success", "explanation": summary}
