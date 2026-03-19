"""
API Routes
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.database.database import get_db, SessionLocal
from src.database.models import Department, Subject, Room, Faculty, Division, TimeSlot, PipelineRun, User, SavedTimetable
from src.agents.orchestrator import AgentOrchestrator
from src.api.auth import hash_password, verify_password, create_access_token, get_current_user
from src.api.schemas import (
    RegisterRequest, LoginRequest, TokenResponse,
    DepartmentCreate, DepartmentUpdate, DepartmentOut,
    SubjectCreate, SubjectUpdate, SubjectOut,
    RoomCreate, RoomUpdate, RoomOut,
    FacultyCreate, FacultyUpdate, FacultyOut,
    DivisionCreate, DivisionUpdate, DivisionOut,
    TimeSlotOut, TimetableRequest, SavedTimetableOut, ChatRequest
)

router = APIRouter(prefix="/api")


# ── Auth ──────────────────────────────────────────────────────────────────────

@router.post("/auth/register", response_model=TokenResponse)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, "Email already registered")
    user = User(name=data.name, email=data.email, hashed_password=hash_password(data.password))
    db.add(user); db.commit(); db.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user={"id": user.id, "name": user.name, "email": user.email})

@router.post("/auth/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(401, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(403, "Account is disabled")
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user={"id": user.id, "name": user.name, "email": user.email})

@router.get("/auth/me")
def me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "name": current_user.name, "email": current_user.email}


# ── Departments ───────────────────────────────────────────────────────────────

@router.get("/departments", response_model=List[DepartmentOut])
def get_departments(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Department).all()

@router.post("/departments", response_model=DepartmentOut)
def create_department(data: DepartmentCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    if db.query(Department).filter(Department.code == data.code).first():
        raise HTTPException(400, "Department code already exists")
    dept = Department(**data.model_dump())
    db.add(dept); db.commit(); db.refresh(dept)
    return dept

@router.put("/departments/{dept_id}", response_model=DepartmentOut)
def update_department(dept_id: int, data: DepartmentUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(404, "Department not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(dept, field, value)
    db.commit(); db.refresh(dept)
    return dept

@router.delete("/departments/{dept_id}")
def delete_department(dept_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(404, "Department not found")
    db.delete(dept); db.commit()
    return {"message": "Deleted"}


# ── Subjects ──────────────────────────────────────────────────────────────────

@router.get("/subjects", response_model=List[SubjectOut])
def get_subjects(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Subject).all()

@router.post("/subjects", response_model=SubjectOut)
def create_subject(data: SubjectCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    if db.query(Subject).filter(Subject.code == data.code).first():
        raise HTTPException(400, "Subject code already exists")
    subject = Subject(**data.model_dump())
    db.add(subject); db.commit(); db.refresh(subject)
    return subject

@router.put("/subjects/{subject_id}", response_model=SubjectOut)
def update_subject(subject_id: int, data: SubjectUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(404, "Subject not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(subject, field, value)
    db.commit(); db.refresh(subject)
    return subject

@router.delete("/subjects/{subject_id}")
def delete_subject(subject_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(404, "Subject not found")
    db.delete(subject); db.commit()
    return {"message": "Deleted"}


# ── Rooms ─────────────────────────────────────────────────────────────────────

@router.get("/rooms", response_model=List[RoomOut])
def get_rooms(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Room).all()

@router.post("/rooms", response_model=RoomOut)
def create_room(data: RoomCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    if db.query(Room).filter(Room.room_number == data.room_number).first():
        raise HTTPException(400, "Room number already exists")
    room = Room(**data.model_dump())
    db.add(room); db.commit(); db.refresh(room)
    return room

@router.put("/rooms/{room_id}", response_model=RoomOut)
def update_room(room_id: int, data: RoomUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(404, "Room not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(room, field, value)
    db.commit(); db.refresh(room)
    return room

@router.delete("/rooms/{room_id}")
def delete_room(room_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(404, "Room not found")
    db.delete(room); db.commit()
    return {"message": "Deleted"}


# ── Faculty ───────────────────────────────────────────────────────────────────

@router.get("/faculty", response_model=List[FacultyOut])
def get_faculty(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Faculty).all()

@router.post("/faculty", response_model=FacultyOut)
def create_faculty(data: FacultyCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    if db.query(Faculty).filter(Faculty.employee_id == data.employee_id).first():
        raise HTTPException(400, "Employee ID already exists")
    faculty = Faculty(**data.model_dump())
    db.add(faculty); db.commit(); db.refresh(faculty)
    return faculty

@router.put("/faculty/{faculty_id}", response_model=FacultyOut)
def update_faculty(faculty_id: int, data: FacultyUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    f = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not f:
        raise HTTPException(404, "Faculty not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(f, field, value)
    db.commit(); db.refresh(f)
    return f

@router.delete("/faculty/{faculty_id}")
def delete_faculty(faculty_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    f = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not f:
        raise HTTPException(404, "Faculty not found")
    db.delete(f); db.commit()
    return {"message": "Deleted"}


# ── Divisions ─────────────────────────────────────────────────────────────────

@router.get("/divisions", response_model=List[DivisionOut])
def get_divisions(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Division).all()

@router.post("/divisions", response_model=DivisionOut)
def create_division(data: DivisionCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    division = Division(**data.model_dump())
    db.add(division); db.commit(); db.refresh(division)
    return division

@router.put("/divisions/{division_id}", response_model=DivisionOut)
def update_division(division_id: int, data: DivisionUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    d = db.query(Division).filter(Division.id == division_id).first()
    if not d:
        raise HTTPException(404, "Division not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(d, field, value)
    db.commit(); db.refresh(d)
    return d

@router.delete("/divisions/{division_id}")
def delete_division(division_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    d = db.query(Division).filter(Division.id == division_id).first()
    if not d:
        raise HTTPException(404, "Division not found")
    db.delete(d); db.commit()
    return {"message": "Deleted"}


# ── Timeslots ─────────────────────────────────────────────────────────────────

@router.get("/timeslots", response_model=List[TimeSlotOut])
def get_timeslots(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(TimeSlot).all()


# ── Timetable Generation & Persistence ───────────────────────────────────────

@router.post("/timetable/generate")
def generate_timetable(
    request: TimetableRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dept_ids  = request.department_ids
    divisions = db.query(Division).filter(Division.department_id.in_(dept_ids)).all()
    subjects  = db.query(Subject).filter(Subject.department_id.in_(dept_ids)).all()
    rooms     = db.query(Room).all()
    faculty   = db.query(Faculty).filter(Faculty.department_id.in_(dept_ids)).all()
    timeslots = db.query(TimeSlot).all()

    if not divisions or not subjects or not rooms or not timeslots:
        raise HTTPException(400, "Insufficient data. Add departments, subjects, rooms, and divisions first.")

    input_data = {
        "divisions": [{"id": d.id, "name": d.name, "student_count": d.student_count, "department_id": d.department_id} for d in divisions],
        "subjects":  [{"id": s.id, "name": s.name, "code": s.code, "hours_per_week": s.hours_per_week, "is_lab": s.is_lab, "department_id": s.department_id} for s in subjects],
        "rooms":     [{"id": r.id, "room_number": r.room_number, "capacity": r.capacity, "is_lab": r.is_lab, "floor": r.floor} for r in rooms],
        "faculty":   [{"id": f.id, "name": f.name, "employee_id": f.employee_id, "department_id": f.department_id} for f in faculty],
        "timeslots": [{"id": t.id, "day": t.day, "slot_number": t.slot_number, "start_time": t.start_time, "end_time": t.end_time} for t in timeslots],
    }

    hitl = request.hitl_enabled if hasattr(request, "hitl_enabled") else False
    orchestrator = AgentOrchestrator(db_session_factory=SessionLocal)
    result = orchestrator.generate_timetable(input_data, hitl_enabled=hitl)

    if request.save and result.get("status") == "success":
        saved = SavedTimetable(
            name=request.name or f"Timetable {db.query(SavedTimetable).count() + 1}",
            department_ids=",".join(str(i) for i in dept_ids),
            result_json=json.dumps(result),
            created_by=current_user.id
        )
        db.add(saved); db.commit(); db.refresh(saved)
        result["saved_id"] = saved.id

    return result

@router.get("/timetable/saved", response_model=List[SavedTimetableOut])
def list_saved_timetables(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(SavedTimetable).filter(SavedTimetable.created_by == current_user.id).order_by(SavedTimetable.created_at.desc()).all()

@router.get("/timetable/saved/{timetable_id}")
def get_saved_timetable(timetable_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    saved = db.query(SavedTimetable).filter(SavedTimetable.id == timetable_id, SavedTimetable.created_by == current_user.id).first()
    if not saved:
        raise HTTPException(404, "Timetable not found")
    return json.loads(saved.result_json)

@router.delete("/timetable/saved/{timetable_id}")
def delete_saved_timetable(timetable_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    saved = db.query(SavedTimetable).filter(SavedTimetable.id == timetable_id, SavedTimetable.created_by == current_user.id).first()
    if not saved:
        raise HTTPException(404, "Timetable not found")
    db.delete(saved); db.commit()
    return {"message": "Deleted"}


# ── HITL Approval ─────────────────────────────────────────────────────────────

@router.get("/timetable/status/{run_id}")
def get_run_status(run_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
    if not run:
        raise HTTPException(404, "Run not found")
    checkpoint = json.loads(run.checkpoint_data) if run.checkpoint_data else None
    return {"run_id": run_id, "status": run.status, "stage": run.stage, "checkpoint": checkpoint}

@router.post("/timetable/approve/{run_id}")
def approve_run(run_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    import asyncio
    orchestrator = AgentOrchestrator(db_session_factory=SessionLocal)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(orchestrator.resume(run_id, approved=True, db_session_factory=SessionLocal))
    finally:
        loop.close()
    return result

@router.post("/timetable/reject/{run_id}")
def reject_run(run_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
    if not run:
        raise HTTPException(404, "Run not found")
    run.status = "rejected"
    db.commit()
    return {"run_id": run_id, "status": "rejected"}


# ── Chat ──────────────────────────────────────────────────────────────────────

@router.post("/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    msg = request.message.lower().strip()

    if any(w in msg for w in ["generate", "create timetable", "make timetable"]):
        depts = db.query(Department).all()
        if not depts:
            return {"reply": "No departments found. Please add data first.", "action": None}
        result = generate_timetable(TimetableRequest(department_ids=[d.id for d in depts]), db, current_user)
        return {"reply": "Timetable generated successfully!", "action": "timetable_generated", "data": result}

    if "department" in msg:
        data = [{"id": d.id, "name": d.name, "code": d.code} for d in db.query(Department).all()]
        return {"reply": f"Found {len(data)} department(s).", "action": "show_data", "data": data}

    if "subject" in msg:
        data = [{"id": s.id, "name": s.name, "code": s.code} for s in db.query(Subject).all()]
        return {"reply": f"Found {len(data)} subject(s).", "action": "show_data", "data": data}

    if "room" in msg:
        data = [{"id": r.id, "room_number": r.room_number, "capacity": r.capacity} for r in db.query(Room).all()]
        return {"reply": f"Found {len(data)} room(s).", "action": "show_data", "data": data}

    if "faculty" in msg:
        data = [{"id": f.id, "name": f.name, "employee_id": f.employee_id} for f in db.query(Faculty).all()]
        return {"reply": f"Found {len(data)} faculty member(s).", "action": "show_data", "data": data}

    if "division" in msg:
        data = [{"id": d.id, "name": d.name, "year": d.year} for d in db.query(Division).all()]
        return {"reply": f"Found {len(data)} division(s).", "action": "show_data", "data": data}

    return {
        "reply": "I can help you generate a timetable or show data. Try: 'generate timetable', 'show departments', 'show rooms', etc.",
        "action": "help"
    }


# ── Health ────────────────────────────────────────────────────────────────────

@router.get("/health")
def health():
    return {"status": "ok"}
