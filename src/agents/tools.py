"""
Agent Tools - Discrete, testable functions agents call explicitly.
Each tool takes plain dicts and returns a plain dict result.
"""
from typing import Any


def check_room_availability(room_id: Any, day: str, slot_number: int, timetable: list[dict]) -> dict:
    """Returns whether a room is free at a given day+slot."""
    occupied = any(
        e["room_id"] == room_id and e["day"] == day and e["slot_number"] == slot_number
        for e in timetable
    )
    return {"room_id": room_id, "day": day, "slot": slot_number, "available": not occupied}


def get_faculty_load(faculty_id: Any, timetable: list[dict]) -> dict:
    """Returns how many slots a faculty member is currently assigned."""
    count = sum(1 for e in timetable if e.get("faculty_id") == faculty_id)
    return {"faculty_id": faculty_id, "assigned_slots": count}


def find_alternative_slot(
    division_id: Any,
    room_id: Any,
    timetable: list[dict],
    all_timeslots: list[dict],
) -> dict:
    """
    Finds the first timeslot where both the division and room are free.
    Returns the timeslot dict or None.
    """
    busy_division = {
        (e["day"], e["slot_number"])
        for e in timetable if e["division_id"] == division_id
    }
    busy_room = {
        (e["day"], e["slot_number"])
        for e in timetable if e["room_id"] == room_id
    }

    for ts in all_timeslots:
        key = (ts["day"], ts["slot_number"])
        if key not in busy_division and key not in busy_room:
            return {"found": True, "timeslot": ts}

    return {"found": False, "timeslot": None}


def find_alternative_room(
    division_id: Any,
    day: str,
    slot_number: int,
    student_count: int,
    is_lab: bool,
    timetable: list[dict],
    all_rooms: list[dict],
) -> dict:
    """Finds a free room that fits the division at a given slot."""
    busy_rooms = {
        e["room_id"]
        for e in timetable if e["day"] == day and e["slot_number"] == slot_number
    }
    for room in all_rooms:
        if (
            room["id"] not in busy_rooms
            and room.get("capacity", 0) >= student_count
            and room.get("is_lab", False) == is_lab
        ):
            return {"found": True, "room": room}
    return {"found": False, "room": None}


def score_timetable(timetable: list[dict]) -> dict:
    """
    Quick quality score used by self-reflection.
    Returns per-issue counts and an overall score 0-100.
    """
    issues = []

    # Check consecutive lectures per division per day
    from collections import defaultdict
    div_day_slots: dict = defaultdict(list)
    for e in timetable:
        div_day_slots[(e["division_id"], e["day"])].append(e["slot_number"])

    for (div_id, day), slots in div_day_slots.items():
        slots_sorted = sorted(slots)
        consecutive = 1
        max_consec = 1
        for i in range(1, len(slots_sorted)):
            if slots_sorted[i] == slots_sorted[i - 1] + 1:
                consecutive += 1
                max_consec = max(max_consec, consecutive)
            else:
                consecutive = 1
        if max_consec >= 4:
            issues.append({
                "type": "consecutive_overload",
                "division_id": div_id,
                "day": day,
                "consecutive_count": max_consec
            })

    # Check gaps (free slots between classes)
    total_gaps = 0
    for (div_id, day), slots in div_day_slots.items():
        slots_sorted = sorted(slots)
        for i in range(1, len(slots_sorted)):
            gap = slots_sorted[i] - slots_sorted[i - 1] - 1
            total_gaps += max(0, gap)

    penalty = len(issues) * 10 + total_gaps * 3
    score = max(0, 100 - penalty)

    return {"score": score, "issues": issues, "total_gaps": total_gaps}
