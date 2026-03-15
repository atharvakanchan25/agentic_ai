"""
Resource Allocation Agent - Manages room and faculty resource allocation
"""
from typing import Dict, Any, List
from .base_agent import BaseAgent


class ResourceAllocationAgent(BaseAgent):

    def __init__(self):
        super().__init__("ResourceAllocationAgent", [
            "allocate_resources",
            "check_availability",
            "optimize_room_usage"
        ])

    async def _initialize_agent(self):
        self.log_action("ResourceAllocationAgent initialized")

    def _register_custom_handlers(self):
        pass

    async def _cleanup_agent(self):
        pass

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        method = request.get("method")
        params = request.get("params", {})

        if method == "allocate_resources":
            return await self.allocate_resources(params)
        elif method == "check_availability":
            return await self.check_availability(params)
        elif method == "optimize_room_usage":
            return await self.optimize_room_usage(params)
        return {"status": "error", "message": f"Unknown method: {method}"}

    async def allocate_resources(self, data: Dict[str, Any]) -> Dict[str, Any]:
        divisions = data.get("divisions", [])
        subjects = data.get("subjects", [])
        rooms = data.get("rooms", [])
        faculty = data.get("faculty", [])

        allocations = []
        unallocated = []

        for division in divisions:
            student_count = division.get("student_count", 0)
            dept_id = division.get("department_id")

            # Find suitable rooms sorted by best fit (smallest sufficient room)
            suitable_rooms = sorted(
                [r for r in rooms if r.get("capacity", 0) >= student_count],
                key=lambda r: r.get("capacity", 0)
            )

            # Find faculty for this department
            dept_faculty = [f for f in faculty if f.get("department_id") == dept_id]

            for subject in subjects:
                is_lab = subject.get("is_lab", False)

                # Filter rooms by lab requirement
                candidate_rooms = [
                    r for r in suitable_rooms
                    if r.get("is_lab", False) == is_lab
                ]

                if not candidate_rooms:
                    # Fallback: any suitable room
                    candidate_rooms = suitable_rooms

                if candidate_rooms:
                    assigned_room = candidate_rooms[0]
                    assigned_faculty = dept_faculty[0] if dept_faculty else None

                    allocations.append({
                        "division_id": division["id"],
                        "division_name": division["name"],
                        "subject_id": subject["id"],
                        "subject_name": subject["name"],
                        "room_id": assigned_room["id"],
                        "room_number": assigned_room["room_number"],
                        "faculty_id": assigned_faculty["id"] if assigned_faculty else None,
                        "faculty_name": assigned_faculty["name"] if assigned_faculty else "TBD",
                        "is_lab": is_lab
                    })
                else:
                    unallocated.append({
                        "division_id": division["id"],
                        "subject_id": subject["id"],
                        "reason": "No suitable room found"
                    })

        self.log_action(f"Allocated {len(allocations)} resources, {len(unallocated)} unallocated")
        return {
            "status": "success",
            "allocations": allocations,
            "unallocated": unallocated,
            "allocation_rate": round(len(allocations) / max(len(allocations) + len(unallocated), 1) * 100, 2)
        }

    async def check_availability(self, data: Dict[str, Any]) -> Dict[str, Any]:
        timetable = data.get("timetable", [])
        rooms = data.get("rooms", [])
        timeslots = data.get("timeslots", [])

        # Build occupied slots per room
        occupied: Dict[str, set] = {}
        for entry in timetable:
            room_id = str(entry["room_id"])
            slot_key = f"{entry['day']}_{entry['slot_number']}"
            occupied.setdefault(room_id, set()).add(slot_key)

        availability = {}
        for room in rooms:
            room_id = str(room["id"])
            all_slots = {f"{ts['day']}_{ts['slot_number']}" for ts in timeslots}
            used_slots = occupied.get(room_id, set())
            free_slots = all_slots - used_slots

            availability[room_id] = {
                "room_number": room["room_number"],
                "total_slots": len(all_slots),
                "used_slots": len(used_slots),
                "free_slots": len(free_slots),
                "utilization_pct": round(len(used_slots) / max(len(all_slots), 1) * 100, 2)
            }

        return {"status": "success", "availability": availability}

    async def optimize_room_usage(self, data: Dict[str, Any]) -> Dict[str, Any]:
        timetable = data.get("timetable", [])
        rooms = data.get("rooms", [])

        room_usage: Dict[Any, int] = {}
        for entry in timetable:
            rid = entry["room_id"]
            room_usage[rid] = room_usage.get(rid, 0) + 1

        suggestions = []
        for room in rooms:
            rid = room["id"]
            usage = room_usage.get(rid, 0)
            if usage == 0:
                suggestions.append(f"Room {room['room_number']} is unused — consider removing or reassigning")
            elif usage < 3:
                suggestions.append(f"Room {room['room_number']} is underutilized ({usage} slots)")

        return {
            "status": "success",
            "room_usage": room_usage,
            "suggestions": suggestions
        }
