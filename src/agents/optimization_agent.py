"""
Optimization Agent - Timetable optimization via CP-SAT or greedy fallback.
"""
from typing import Dict, Any, List
import time
from ortools.sat.python import cp_model
import numpy as np

from .base_agent import BaseAgent


class OptimizationAgent(BaseAgent):

    def __init__(self):
        super().__init__("OptimizationAgent", [
            "optimize_timetable",
            "calculate_utilization",
            "evaluate_solution_quality",
        ])
        self.max_solve_time = 60

    async def _initialize_agent(self):
        self.log_action("OptimizationAgent initialized with OR-Tools CP-SAT + greedy fallback")

    def _register_custom_handlers(self):
        if self.mcp_client:
            self.mcp_client.register_handler("set_optimization_params", self._handle_set_params)

    async def _cleanup_agent(self):
        pass

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        method = request.get("method")
        params = request.get("params", {})
        if method == "optimize_timetable":
            return await self.optimize_timetable(params)
        elif method == "calculate_utilization":
            return await self.calculate_utilization(params)
        elif method == "evaluate_solution_quality":
            return await self.evaluate_solution_quality(params)
        return {"status": "error", "message": f"Unknown method: {method}"}

    # ── Public entry point ────────────────────────────────────────────────────

    async def optimize_timetable(self, data: Dict[str, Any]) -> Dict[str, Any]:
        solver_mode = data.get("solver_mode", "cp_sat")
        if solver_mode == "greedy":
            return await self._greedy_solve(data)
        result = await self._cp_sat_solve(data)
        # Fallback: if CP-SAT fails, try greedy automatically
        if result.get("status") != "success":
            self.log_action("CP-SAT failed — falling back to greedy solver")
            greedy = await self._greedy_solve(data)
            if greedy.get("status") == "success":
                greedy["fallback_used"] = True
                greedy["cp_sat_failure_reason"] = result.get("solver_status", "unknown")
            return greedy
        return result

    # ── CP-SAT solver ─────────────────────────────────────────────────────────

    async def _cp_sat_solve(self, data: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        try:
            divisions = data.get("divisions", [])
            subjects  = data.get("subjects", [])
            rooms     = data.get("rooms", [])
            timeslots = data.get("timeslots", [])
            faculty   = data.get("faculty", [])

            if not all([divisions, subjects, rooms, timeslots]):
                return {"status": "error", "message": "Missing required data"}

            model = cp_model.CpModel()
            D, S, R, T = len(divisions), len(subjects), len(rooms), len(timeslots)

            x = {
                (d, s, r, t): model.NewBoolVar(f"x_{d}_{s}_{r}_{t}")
                for d in range(D) for s in range(S) for r in range(R) for t in range(T)
            }

            # 1. Each division-subject scheduled for required hours
            for d in range(D):
                for s in range(S):
                    hours = subjects[s].get("hours_per_week", 1)
                    model.Add(sum(x[(d, s, r, t)] for r in range(R) for t in range(T)) == hours)

            # 2. One class per room per timeslot
            for r in range(R):
                for t in range(T):
                    model.Add(sum(x[(d, s, r, t)] for d in range(D) for s in range(S)) <= 1)

            # 3. One class per division per timeslot
            for d in range(D):
                for t in range(T):
                    model.Add(sum(x[(d, s, r, t)] for s in range(S) for r in range(R)) <= 1)

            # 4. Room capacity
            for d in range(D):
                for s in range(S):
                    for r in range(R):
                        if divisions[d].get("student_count", 0) > rooms[r].get("capacity", 0):
                            for t in range(T):
                                model.Add(x[(d, s, r, t)] == 0)

            # 5. Lab rooms for lab subjects
            for d in range(D):
                for s in range(S):
                    if subjects[s].get("is_lab", False):
                        for r in range(R):
                            if not rooms[r].get("is_lab", False):
                                for t in range(T):
                                    model.Add(x[(d, s, r, t)] == 0)

            # 6. Faculty: no double-booking
            if faculty:
                self._add_faculty_constraints(model, x, data, D, S, R, T)

            # 7. Max 6 hours/day per division
            day_slots: Dict[str, list] = {}
            for i, ts in enumerate(timeslots):
                day_slots.setdefault(ts["day"], []).append(i)
            for d in range(D):
                for slots in day_slots.values():
                    if len(slots) > 6:
                        model.Add(
                            sum(x[(d, s, r, t)] for s in range(S) for r in range(R) for t in slots) <= 6
                        )

            # 8. Soft objective: minimise daily load variance per division
            objective_terms = []
            for d in range(D):
                daily_loads = []
                for slots in day_slots.values():
                    load = sum(x[(d, s, r, t)] for s in range(S) for r in range(R) for t in slots)
                    daily_loads.append(load)
                if len(daily_loads) > 1:
                    max_load = model.NewIntVar(0, T, f"max_load_{d}")
                    min_load = model.NewIntVar(0, T, f"min_load_{d}")
                    for load in daily_loads:
                        model.Add(max_load >= load)
                        model.Add(min_load <= load)
                    objective_terms.append(max_load - min_load)

            if objective_terms:
                model.Minimize(sum(objective_terms))

            solver = cp_model.CpSolver()
            solver.parameters.max_time_in_seconds = self.max_solve_time
            solver.parameters.log_search_progress = False
            status = solver.Solve(model)
            solve_time = round(time.time() - start, 2)

            if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
                timetable = []
                for d in range(D):
                    for s in range(S):
                        for r in range(R):
                            for t in range(T):
                                if solver.Value(x[(d, s, r, t)]) == 1:
                                    timetable.append(self._make_entry(
                                        divisions[d], subjects[s], rooms[r], timeslots[t]
                                    ))
                quality = await self._calculate_solution_quality(timetable, data)
                return {
                    "status": "success",
                    "solver_status": "optimal" if status == cp_model.OPTIMAL else "feasible",
                    "solver_mode": "cp_sat",
                    "timetable": timetable,
                    "solve_time": solve_time,
                    "quality_metrics": quality,
                    "statistics": {
                        "total_assignments": len(timetable),
                        "solver_iterations": solver.NumBranches(),
                        "solver_conflicts": solver.NumConflicts(),
                    }
                }

            return {
                "status": "failed",
                "solver_status": solver.StatusName(status),
                "message": f"No feasible solution: {solver.StatusName(status)}",
                "solve_time": solve_time,
                "suggestions": self._infeasibility_suggestions(data),
            }

        except Exception as e:
            return {"status": "error", "message": str(e), "solve_time": round(time.time() - start, 2)}

    # ── Greedy solver ─────────────────────────────────────────────────────────

    async def _greedy_solve(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Greedy slot-filling: for each (division, subject) pair, assign the
        first available (room, timeslot) that satisfies hard constraints.
        """
        start = time.time()
        divisions = data.get("divisions", [])
        subjects  = data.get("subjects", [])
        rooms     = data.get("rooms", [])
        timeslots = data.get("timeslots", [])

        timetable: list[dict] = []
        # Occupied sets for fast lookup
        room_slot_used:  set[tuple] = set()   # (room_id, day, slot_number)
        div_slot_used:   set[tuple] = set()   # (division_id, day, slot_number)
        faculty_slot_used: set[tuple] = set() # (faculty_id, day, slot_number)

        unscheduled = []

        for division in divisions:
            for subject in subjects:
                hours_needed = subject.get("hours_per_week", 1)
                scheduled = 0

                for ts in timeslots:
                    if scheduled >= hours_needed:
                        break
                    day, slot = ts["day"], ts["slot_number"]

                    if (division["id"], day, slot) in div_slot_used:
                        continue

                    # Find a suitable room
                    chosen_room = None
                    for room in sorted(rooms, key=lambda r: r.get("capacity", 0)):
                        if room.get("capacity", 0) < division.get("student_count", 0):
                            continue
                        if subject.get("is_lab", False) and not room.get("is_lab", False):
                            continue
                        if (room["id"], day, slot) in room_slot_used:
                            continue
                        chosen_room = room
                        break

                    if not chosen_room:
                        continue

                    timetable.append(self._make_entry(division, subject, chosen_room, ts))
                    room_slot_used.add((chosen_room["id"], day, slot))
                    div_slot_used.add((division["id"], day, slot))
                    scheduled += 1

                if scheduled < hours_needed:
                    unscheduled.append({
                        "division": division["name"],
                        "subject": subject["name"],
                        "scheduled": scheduled,
                        "needed": hours_needed,
                    })

        solve_time = round(time.time() - start, 2)
        quality = await self._calculate_solution_quality(timetable, data)

        result = {
            "status": "success",
            "solver_status": "greedy_complete",
            "solver_mode": "greedy",
            "timetable": timetable,
            "solve_time": solve_time,
            "quality_metrics": quality,
            "statistics": {"total_assignments": len(timetable)},
        }
        if unscheduled:
            result["warnings"] = [
                f"{u['division']}/{u['subject']}: scheduled {u['scheduled']}/{u['needed']} slots"
                for u in unscheduled
            ]
        return result

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _make_entry(self, division, subject, room, ts) -> dict:
        return {
            "division_id":   division.get("id"),
            "division_name": division.get("name"),
            "subject_id":    subject.get("id"),
            "subject_name":  subject.get("name"),
            "subject_code":  subject.get("code"),
            "room_id":       room.get("id"),
            "room_number":   room.get("room_number"),
            "timeslot_id":   ts.get("id"),
            "day":           ts.get("day"),
            "slot_number":   ts.get("slot_number"),
            "start_time":    ts.get("start_time"),
            "end_time":      ts.get("end_time"),
            "is_lab":        subject.get("is_lab", False),
        }

    def _add_faculty_constraints(self, model, x, data, D, S, R, T):
        faculty  = data.get("faculty", [])
        subjects = data.get("subjects", [])
        # Map subject index → faculty id (first matching dept faculty)
        subj_faculty: dict[int, Any] = {}
        for i, subj in enumerate(subjects):
            dept_id = subj.get("department_id")
            for f in faculty:
                if f.get("department_id") == dept_id:
                    subj_faculty[i] = f["id"]
                    break

        faculty_ids = set(subj_faculty.values())
        for fid in faculty_ids:
            for t in range(T):
                assignments = [
                    x[(d, s, r, t)]
                    for d in range(D)
                    for s in range(S)
                    for r in range(R)
                    if subj_faculty.get(s) == fid
                ]
                if assignments:
                    model.Add(sum(assignments) <= 1)

    def _infeasibility_suggestions(self, data: Dict[str, Any]) -> List[str]:
        suggestions = []
        divisions = data.get("divisions", [])
        subjects  = data.get("subjects", [])
        rooms     = data.get("rooms", [])
        timeslots = data.get("timeslots", [])

        total_hours = sum(s.get("hours_per_week", 0) for s in subjects) * len(divisions)
        if total_hours > len(timeslots):
            suggestions.append(f"Add more time slots: need {total_hours}, have {len(timeslots)}")

        max_students   = max((d.get("student_count", 0) for d in divisions), default=0)
        max_room_cap   = max((r.get("capacity", 0) for r in rooms), default=0)
        if max_students > max_room_cap:
            suggestions.append("Add rooms with higher capacity or reduce division sizes")

        if any(s.get("is_lab") for s in subjects) and not any(r.get("is_lab") for r in rooms):
            suggestions.append("Add lab rooms for lab subjects")

        return suggestions

    async def _calculate_solution_quality(self, timetable: List[Dict], data: Dict[str, Any]) -> Dict[str, Any]:
        if not timetable:
            return {"overall_score": 0, "metrics": {}}

        metrics: dict = {}

        room_usage: dict = {}
        for e in timetable:
            room_usage[e["room_id"]] = room_usage.get(e["room_id"], 0) + 1

        unique_slots = len(set(f"{e['day']}_{e['slot_number']}" for e in timetable))
        unique_rooms = len(room_usage)
        metrics["room_utilization"] = round(
            sum(room_usage.values()) / max(unique_rooms * unique_slots, 1) * 100, 2
        )

        daily: dict = {}
        for e in timetable:
            key = f"{e['division_id']}_{e['day']}"
            daily[key] = daily.get(key, 0) + 1
        if daily:
            vals = list(daily.values())
            metrics["daily_balance_score"] = round(max(0, 100 - float(np.var(vals)) * 10), 2)
        else:
            metrics["daily_balance_score"] = 0

        div_day: dict = {}
        for e in timetable:
            div_day.setdefault((e["division_id"], e["day"]), []).append(e["slot_number"])
        total_gaps = sum(
            max(0, sorted(slots)[i + 1] - sorted(slots)[i] - 1)
            for slots in div_day.values()
            for i in range(len(slots) - 1)
        )
        metrics["gap_score"] = round(max(0, 100 - total_gaps * 5), 2)

        weights = {"room_utilization": 0.3, "daily_balance_score": 0.4, "gap_score": 0.3}
        overall = sum(metrics[k] * weights[k] for k in weights)
        return {"overall_score": round(overall, 2), "metrics": metrics}

    async def calculate_utilization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        timetable = data.get("timetable", [])
        if not timetable:
            return {"status": "error", "message": "No timetable data provided"}

        room_stats: dict = {}
        for e in timetable:
            rid = e.get("room_id")
            if rid not in room_stats:
                room_stats[rid] = {"room_number": e.get("room_number"), "usage_count": 0, "subjects": set(), "divisions": set()}
            room_stats[rid]["usage_count"] += 1
            room_stats[rid]["subjects"].add(e.get("subject_name"))
            room_stats[rid]["divisions"].add(e.get("division_name"))

        for rid in room_stats:
            room_stats[rid]["subjects"]  = list(room_stats[rid]["subjects"])
            room_stats[rid]["divisions"] = list(room_stats[rid]["divisions"])

        timeslot_stats: dict = {}
        for e in timetable:
            key = f"{e.get('day')}_{e.get('slot_number')}"
            if key not in timeslot_stats:
                timeslot_stats[key] = {"day": e.get("day"), "slot_number": e.get("slot_number"), "usage_count": 0}
            timeslot_stats[key]["usage_count"] += 1

        total = len(timetable)
        ur    = len(room_stats)
        ut    = len(timeslot_stats)
        return {
            "status": "success",
            "overall_metrics": {
                "total_assignments":          total,
                "unique_rooms_used":          ur,
                "unique_timeslots_used":      ut,
                "average_room_utilization":   total / ur if ur else 0,
                "average_timeslot_utilization": total / ut if ut else 0,
            },
            "room_utilization":     room_stats,
            "timeslot_utilization": timeslot_stats,
        }

    async def evaluate_solution_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        timetable = data.get("timetable", [])
        return await self._calculate_solution_quality(timetable, data)

    async def _handle_set_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if "max_solve_time" in params:
            self.max_solve_time = params["max_solve_time"]
        return {"status": "success"}
