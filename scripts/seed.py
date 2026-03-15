"""
Seed script - populates the database with sample university data
Run: python scripts/seed.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database.database import SessionLocal, init_db
from src.database.models import Department, Subject, Room, Faculty, Division, TimeSlot

def seed():
    init_db()
    db = SessionLocal()

    try:
        # Skip if already seeded
        if db.query(Department).first():
            print("Database already seeded.")
            return

        # Departments
        cs = Department(name="Computer Science", code="CS")
        it = Department(name="Information Technology", code="IT")
        db.add_all([cs, it])
        db.flush()

        # Subjects
        subjects = [
            Subject(name="Data Structures", code="CS301", hours_per_week=3, is_lab=False, department_id=cs.id),
            Subject(name="Algorithms", code="CS302", hours_per_week=3, is_lab=False, department_id=cs.id),
            Subject(name="Database Systems", code="CS303", hours_per_week=3, is_lab=False, department_id=cs.id),
            Subject(name="OS Lab", code="CS304L", hours_per_week=2, is_lab=True, department_id=cs.id),
            Subject(name="Web Development", code="IT301", hours_per_week=3, is_lab=False, department_id=it.id),
            Subject(name="Networking", code="IT302", hours_per_week=3, is_lab=False, department_id=it.id),
            Subject(name="Network Lab", code="IT303L", hours_per_week=2, is_lab=True, department_id=it.id),
        ]
        db.add_all(subjects)

        # Rooms
        rooms = [
            Room(room_number="101", floor=1, capacity=60, is_lab=False, room_type="classroom"),
            Room(room_number="102", floor=1, capacity=60, is_lab=False, room_type="classroom"),
            Room(room_number="201", floor=2, capacity=60, is_lab=False, room_type="classroom"),
            Room(room_number="202", floor=2, capacity=60, is_lab=False, room_type="classroom"),
            Room(room_number="L01", floor=0, capacity=30, is_lab=True,  room_type="lab"),
            Room(room_number="L02", floor=0, capacity=30, is_lab=True,  room_type="lab"),
        ]
        db.add_all(rooms)

        # Faculty
        faculty = [
            Faculty(name="Dr. Sharma", employee_id="CS001", department_id=cs.id),
            Faculty(name="Dr. Mehta",  employee_id="CS002", department_id=cs.id),
            Faculty(name="Dr. Patel",  employee_id="IT001", department_id=it.id),
            Faculty(name="Dr. Gupta",  employee_id="IT002", department_id=it.id),
        ]
        db.add_all(faculty)
        db.flush()

        # Divisions
        divisions = [
            Division(name="CS-A", year=2, student_count=55, department_id=cs.id),
            Division(name="CS-B", year=2, student_count=55, department_id=cs.id),
            Division(name="IT-A", year=2, student_count=50, department_id=it.id),
        ]
        db.add_all(divisions)

        # Time Slots (Mon–Fri, 6 slots/day)
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        times = [
            (1, "09:00", "10:00"),
            (2, "10:00", "11:00"),
            (3, "11:15", "12:15"),
            (4, "13:00", "14:00"),
            (5, "14:00", "15:00"),
            (6, "15:15", "16:15"),
        ]
        slots = [
            TimeSlot(day=day, slot_number=slot, start_time=start, end_time=end)
            for day in days
            for slot, start, end in times
        ]
        db.add_all(slots)

        db.commit()
        print(f"Seeded: 2 departments, {len(subjects)} subjects, {len(rooms)} rooms, "
              f"{len(faculty)} faculty, {len(divisions)} divisions, {len(slots)} timeslots")

    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()
