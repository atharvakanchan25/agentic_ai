"""
Conflict Resolution Agent - ReAct loop: Reason → Act (tools) → Observe → repeat.
Uses LongTermMemory to avoid historically problematic slots/rooms.
"""
from typing import Any
from .base_agent import BaseAgent
from .state_machine import AgentState
from .tools import (
    check_room_availability,
    find_alternative_slot,
    find_alternative_room,
)


class ConflictResolutionAgent(BaseAgent):

    MAX_REACT_ITERATIONS = 5

    def __init__(self):
        super().__init__("ConflictResolutionAgent", [
            "detect_conflicts", "resolve_conflicts", "suggest_alternatives"
        ])

    async def _initialize_agent(self):
        self.register_tool("check_room_availability", check_room_availability)
        self.register_tool("find_alternative_slot", find_alternative_slot)
        self.register_tool("find_alternative_room", find_alternative_room)
        self.log_action("ConflictResolutionAgent initialized with ReAct + tools")

    def _register_custom_handlers(self): pass
    async def _cleanup_agent(self): pass

    async def process_request(self, request: dict[str, Any]) -> dict[str, Any]:
        method = request.get("method")
        params = request.get("params", {})
        if method == "detect_conflicts":
            return await self.detect_conflicts(params)
        elif method == "resolve_conflicts":
            return await self.resolve_conflicts(params)
        elif method == "suggest_alternatives":
            return await self.suggest_alternatives(params)
        return {"status": "error", "message": f"Unknown method: {method}"}

    # ── Detect ────────────────────────────────────────────────────────────────

    async def detect_conflicts(self, data: dict[str, Any]) -> dict[str, Any]:
        timetable: list[dict] = data.get("timetable", [])
        conflicts = []

        slot_index: dict[str, list[dict]] = {}
        for entry in timetable:
            key = f"{entry['day']}_{entry['slot_number']}"
            slot_index.setdefault(key, []).append(entry)

        for key, entries in slot_index.items():
            room_seen: dict[Any, dict] = {}
            div_seen:  dict[Any, dict] = {}
            for e in entries:
                rid = e["room_id"]
                if rid in room_seen:
                    conflicts.append({"type": "room_conflict", "slot": key, "room_id": rid, "entries": [room_seen[rid], e]})
                else:
                    room_seen[rid] = e

                did = e["division_id"]
                if did in div_seen:
                    conflicts.append({"type": "division_conflict", "slot": key, "division_id": did, "entries": [div_seen[did], e]})
                else:
                    div_seen[did] = e

        self.log_action(f"Detected {len(conflicts)} conflicts")
        return {"status": "success", "conflict_count": len(conflicts), "conflicts": conflicts}

    # ── Resolve via ReAct loop ────────────────────────────────────────────────

    async def resolve_conflicts(self, data: dict[str, Any]) -> dict[str, Any]:
        timetable: list[dict]      = list(data.get("timetable", []))
        conflicts: list[dict]      = data.get("conflicts", [])
        all_timeslots: list[dict]  = data.get("timeslots", [])
        all_rooms: list[dict]      = data.get("rooms", [])
        divisions_map: dict[Any, dict] = {d["id"]: d for d in data.get("divisions", [])}

        if not conflicts:
            return {"status": "success", "resolved_timetable": timetable, "removed": 0, "react_log": []}

        # ── Load historical bad slots/rooms from long-term memory ─────────────
        historically_bad_slots: set[str] = set()
        historically_bad_rooms: set[Any] = set()
        if self.long_term_memory:
            past = self.long_term_memory.recall_conflicts(limit=50)
            for pc in past:
                if pc.get("slot"):
                    historically_bad_slots.add(pc["slot"])
                if pc.get("room_id"):
                    historically_bad_rooms.add(pc["room_id"])

        self._set_state(AgentState.RUNNING)
        react_log: list[dict] = []

        if historically_bad_slots or historically_bad_rooms:
            react_log.append({
                "phase": "reason",
                "message": (
                    f"Loaded {len(historically_bad_slots)} historically bad slots and "
                    f"{len(historically_bad_rooms)} historically bad rooms from long-term memory."
                )
            })

        removed   = 0
        iteration = 0
        remaining = list(conflicts)

        while remaining and iteration < self.MAX_REACT_ITERATIONS:
            iteration += 1

            for conflict in remaining:
                entries = conflict.get("entries", [])
                if len(entries) < 2:
                    continue

                victim = entries[1]

                # ── REASON ────────────────────────────────────────────────────
                react_log.append({
                    "phase": "reason",
                    "message": (
                        f"Iter {iteration}: {conflict['type']} at slot {conflict['slot']}. "
                        f"Trying to relocate division {victim.get('division_id')}."
                    )
                })

                resolved = False

                if conflict["type"] == "room_conflict" and all_rooms:
                    # ── ACT: prefer rooms not in historically bad set ──────────
                    preferred_rooms = [r for r in all_rooms if r["id"] not in historically_bad_rooms] or all_rooms
                    div = divisions_map.get(victim["division_id"], {})
                    result = self.use_tool(
                        "find_alternative_room",
                        division_id=victim["division_id"],
                        day=victim["day"],
                        slot_number=victim["slot_number"],
                        student_count=div.get("student_count", 0),
                        is_lab=victim.get("is_lab", False),
                        timetable=timetable,
                        all_rooms=preferred_rooms,
                    )
                    # ── OBSERVE ───────────────────────────────────────────────
                    if result["found"]:
                        new_room = result["room"]
                        idx = timetable.index(victim)
                        timetable[idx] = {**victim, "room_id": new_room["id"], "room_number": new_room["room_number"]}
                        react_log.append({"phase": "observe", "message": f"Moved to room {new_room['room_number']}"})
                        resolved = True
                    else:
                        react_log.append({"phase": "observe", "message": "No alternative room found."})

                if not resolved and all_timeslots:
                    # ── ACT: prefer slots not in historically bad set ──────────
                    preferred_slots = [
                        ts for ts in all_timeslots
                        if f"{ts['day']}_{ts['slot_number']}" not in historically_bad_slots
                    ] or all_timeslots
                    result = self.use_tool(
                        "find_alternative_slot",
                        division_id=victim["division_id"],
                        room_id=victim["room_id"],
                        timetable=timetable,
                        all_timeslots=preferred_slots,
                    )
                    # ── OBSERVE ───────────────────────────────────────────────
                    if result["found"]:
                        ts = result["timeslot"]
                        idx = timetable.index(victim)
                        timetable[idx] = {
                            **victim,
                            "day": ts["day"],
                            "slot_number": ts["slot_number"],
                            "timeslot_id": ts["id"],
                            "start_time": ts.get("start_time"),
                            "end_time": ts.get("end_time"),
                        }
                        react_log.append({"phase": "observe", "message": f"Moved to {ts['day']} slot {ts['slot_number']}"})
                        resolved = True
                    else:
                        react_log.append({"phase": "observe", "message": "No alternative slot found. Dropping entry."})
                        timetable = [e for e in timetable if e is not victim]
                        removed += 1
                        resolved = True

            detect_result = await self.detect_conflicts({"timetable": timetable})
            remaining = detect_result.get("conflicts", [])
            react_log.append({"phase": "observe", "message": f"After iter {iteration}: {len(remaining)} conflicts remain."})

        # Persist conflict patterns to long-term memory
        if self.long_term_memory:
            for c in conflicts:
                self.long_term_memory.remember(
                    self.agent_name, "conflict_pattern",
                    {"type": c["type"], "slot": c.get("slot"), "room_id": c.get("room_id")}
                )

        self._set_state(AgentState.COMPLETED)
        self.log_action(f"ReAct resolved conflicts in {iteration} iterations, removed {removed} entries")
        return {
            "status": "success",
            "resolved_timetable": timetable,
            "removed": removed,
            "iterations": iteration,
            "react_log": react_log,
        }

    async def suggest_alternatives(self, data: dict[str, Any]) -> dict[str, Any]:
        conflicts: list[dict] = data.get("conflicts", [])
        suggestions = []
        for conflict in conflicts:
            if conflict["type"] == "room_conflict":
                suggestions.append({"conflict": conflict, "suggestion": "Assign one conflicting class to a different available room"})
            elif conflict["type"] == "division_conflict":
                suggestions.append({"conflict": conflict, "suggestion": "Move one conflicting subject to a different time slot"})
        return {"status": "success", "suggestions": suggestions}
