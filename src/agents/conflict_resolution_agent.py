"""
Conflict Resolution Agent - Detects and resolves timetable conflicts
"""
from typing import Dict, Any, List
from .base_agent import BaseAgent


class ConflictResolutionAgent(BaseAgent):

    def __init__(self):
        super().__init__("ConflictResolutionAgent", [
            "detect_conflicts",
            "resolve_conflicts",
            "suggest_alternatives"
        ])

    async def _initialize_agent(self):
        self.log_action("ConflictResolutionAgent initialized")

    def _register_custom_handlers(self):
        pass

    async def _cleanup_agent(self):
        pass

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        method = request.get("method")
        params = request.get("params", {})

        if method == "detect_conflicts":
            return await self.detect_conflicts(params)
        elif method == "resolve_conflicts":
            return await self.resolve_conflicts(params)
        elif method == "suggest_alternatives":
            return await self.suggest_alternatives(params)
        return {"status": "error", "message": f"Unknown method: {method}"}

    async def detect_conflicts(self, data: Dict[str, Any]) -> Dict[str, Any]:
        timetable: List[Dict] = data.get("timetable", [])
        conflicts = []

        # Index by (day, slot) for fast lookup
        slot_index: Dict[str, List[Dict]] = {}
        for entry in timetable:
            key = f"{entry['day']}_{entry['slot_number']}"
            slot_index.setdefault(key, []).append(entry)

        for key, entries in slot_index.items():
            # Room conflict: same room, same slot
            room_seen: Dict[Any, Dict] = {}
            for e in entries:
                rid = e["room_id"]
                if rid in room_seen:
                    conflicts.append({
                        "type": "room_conflict",
                        "slot": key,
                        "room_id": rid,
                        "entries": [room_seen[rid], e]
                    })
                else:
                    room_seen[rid] = e

            # Division conflict: same division, same slot
            div_seen: Dict[Any, Dict] = {}
            for e in entries:
                did = e["division_id"]
                if did in div_seen:
                    conflicts.append({
                        "type": "division_conflict",
                        "slot": key,
                        "division_id": did,
                        "entries": [div_seen[did], e]
                    })
                else:
                    div_seen[did] = e

        self.log_action(f"Detected {len(conflicts)} conflicts")
        return {
            "status": "success",
            "conflict_count": len(conflicts),
            "conflicts": conflicts
        }

    async def resolve_conflicts(self, data: Dict[str, Any]) -> Dict[str, Any]:
        timetable: List[Dict] = data.get("timetable", [])
        conflicts: List[Dict] = data.get("conflicts", [])

        if not conflicts:
            return {"status": "success", "resolved_timetable": timetable, "removed": 0}

        # Build a set of entries to remove (keep first, remove duplicates)
        to_remove = []
        for conflict in conflicts:
            entries = conflict.get("entries", [])
            if len(entries) > 1:
                to_remove.extend(entries[1:])

        resolved = [e for e in timetable if e not in to_remove]

        self.log_action(f"Resolved {len(conflicts)} conflicts, removed {len(to_remove)} entries")
        return {
            "status": "success",
            "resolved_timetable": resolved,
            "removed": len(to_remove),
            "original_count": len(timetable),
            "resolved_count": len(resolved)
        }

    async def suggest_alternatives(self, data: Dict[str, Any]) -> Dict[str, Any]:
        conflicts: List[Dict] = data.get("conflicts", [])
        suggestions = []

        for conflict in conflicts:
            if conflict["type"] == "room_conflict":
                suggestions.append({
                    "conflict": conflict,
                    "suggestion": "Assign one of the conflicting classes to a different available room"
                })
            elif conflict["type"] == "division_conflict":
                suggestions.append({
                    "conflict": conflict,
                    "suggestion": "Move one of the conflicting subjects to a different time slot"
                })

        return {"status": "success", "suggestions": suggestions}
