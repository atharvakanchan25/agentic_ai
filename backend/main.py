
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import sys
sys.path.append('..')

from database.database import get_db, init_db
from database.models import Department, Subject, Room, Faculty, Division, TimeSlot
from agents.orchestrator import AgentOrchestrator
from agents.chatbot_agent import ChatbotAgent
from pydantic import BaseModel

app = FastAPI(
    title="University Timetable Management System",
    description="AI-powered timetable generation using multi-agent system",
    version="1.0.0"
)

# Create API router
from fastapi import APIRouter
api_router = APIRouter(prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

chatbot = ChatbotAgent()

class DepartmentCreate(BaseModel):
    name: str
    code: str

class SubjectCreate(BaseModel):
    name: str
    code: str
    hours_per_week: int
    is_lab: bool
    department_id: int

class RoomCreate(BaseModel):
    room_number: str
    floor: int
    capacity: int
    bench_count: int
    is_lab: bool
    room_type: str

class FacultyCreate(BaseModel):
    name: str
    employee_id: str
    department_id: int

class DivisionCreate(BaseModel):
    name: str
    year: int
    student_count: int
    department_id: int

class TimetableRequest(BaseModel):
    department_ids: List[int]

class ChatMessage(BaseModel):
    message: str
    context: dict = {}

@api_router.post("/departments/")
def create_department(dept: DepartmentCreate, db: Session = Depends(get_db)):
    try:
        # Check if department already exists
        existing = db.query(Department).filter(
            (Department.name == dept.name) | (Department.code == dept.code)
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Department already exists")
        
        db_dept = Department(**dept.dict())
        db.add(db_dept)
        db.commit()
        db.refresh(db_dept)
        return db_dept
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/departments/")
def get_departments(db: Session = Depends(get_db)):
    try:
        return db.query(Department).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/subjects/")
def create_subject(subject: SubjectCreate, db: Session = Depends(get_db)):
    try:
        existing = db.query(Subject).filter(Subject.code == subject.code).first()
        if existing:
            raise HTTPException(status_code=400, detail="Subject code already exists")
        
        db_subject = Subject(**subject.dict())
        db.add(db_subject)
        db.commit()
        db.refresh(db_subject)
        return db_subject
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/subjects/")
def get_subjects(db: Session = Depends(get_db)):
    try:
        return db.query(Subject).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/rooms/")
def create_room(room: RoomCreate, db: Session = Depends(get_db)):
    try:
        existing = db.query(Room).filter(Room.room_number == room.room_number).first()
        if existing:
            raise HTTPException(status_code=400, detail="Room number already exists")
        
        db_room = Room(**room.dict())
        db.add(db_room)
        db.commit()
        db.refresh(db_room)
        return db_room
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/rooms/")
def get_rooms(db: Session = Depends(get_db)):
    try:
        return db.query(Room).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/faculty/")
def create_faculty(faculty: FacultyCreate, db: Session = Depends(get_db)):
    try:
        existing = db.query(Faculty).filter(Faculty.employee_id == faculty.employee_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Employee ID already exists")
        
        db_faculty = Faculty(**faculty.dict())
        db.add(db_faculty)
        db.commit()
        db.refresh(db_faculty)
        return db_faculty
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/faculty/")
def get_faculty(db: Session = Depends(get_db)):
    try:
        return db.query(Faculty).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/divisions/")
def create_division(division: DivisionCreate, db: Session = Depends(get_db)):
    try:
        existing = db.query(Division).filter(
            (Division.name == division.name) & (Division.department_id == division.department_id)
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Division already exists in this department")
        
        db_division = Division(**division.dict())
        db.add(db_division)
        db.commit()
        db.refresh(db_division)
        return db_division
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/divisions/")
def get_divisions(db: Session = Depends(get_db)):
    try:
        return db.query(Division).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/generate-timetable/")
def generate_timetable(request: TimetableRequest, db: Session = Depends(get_db)):
    divisions = db.query(Division).filter(Division.department_id.in_(request.department_ids)).all()
    subjects = db.query(Subject).filter(Subject.department_id.in_(request.department_ids)).all()
    rooms = db.query(Room).all()
    faculty = db.query(Faculty).filter(Faculty.department_id.in_(request.department_ids)).all()
    timeslots = db.query(TimeSlot).all()
    
    input_data = {
        'divisions': [{'id': d.id, 'name': d.name, 'student_count': d.student_count} for d in divisions],
        'subjects': [{'id': s.id, 'name': s.name, 'hours_per_week': s.hours_per_week, 'is_lab': s.is_lab} for s in subjects],
        'rooms': [{'id': r.id, 'room_number': r.room_number, 'capacity': r.capacity, 'is_lab': r.is_lab, 'floor': r.floor, 'bench_count': r.bench_count} for r in rooms],
        'faculty': [{'id': f.id, 'name': f.name} for f in faculty],
        'timeslots': [{'id': t.id, 'day': t.day, 'slot_number': t.slot_number} for t in timeslots],
        'requirements': [
            {
                'division_id': d.id,
                'subject_id': s.id,
                'student_count': d.student_count,
                'is_lab': s.is_lab
            }
            for d in divisions for s in subjects
        ]
    }
    
    orchestrator = AgentOrchestrator()
    result = orchestrator.generate_timetable(input_data)
    
    return result

@api_router.post("/chat/")
def chat(message: ChatMessage, db: Session = Depends(get_db)):
    """Natural language chatbot interface"""
    response = chatbot.process_message(message.message)
    
    if response['action'] == 'generate_timetable':
        departments = db.query(Department).all()
        if departments:
            dept_ids = [d.id for d in departments]
            result = generate_timetable(TimetableRequest(department_ids=dept_ids), db)
            response['timetable_result'] = result
    
    elif response['action'] == 'request_view_type':
        view_type = message.message.lower()
        if 'department' in view_type:
            response['data'] = [{'id': d.id, 'name': d.name, 'code': d.code} for d in db.query(Department).all()]
        elif 'subject' in view_type:
            response['data'] = [{'id': s.id, 'name': s.name, 'code': s.code} for s in db.query(Subject).all()]
        elif 'room' in view_type:
            response['data'] = [{'id': r.id, 'room_number': r.room_number, 'capacity': r.capacity} for r in db.query(Room).all()]
        elif 'faculty' in view_type:
            response['data'] = [{'id': f.id, 'name': f.name, 'employee_id': f.employee_id} for f in db.query(Faculty).all()]
        elif 'division' in view_type:
            response['data'] = [{'id': d.id, 'name': d.name, 'year': d.year} for d in db.query(Division).all()]
    
    return response

@api_router.get("/chat/suggestions/")
def get_suggestions(partial: str = ""):
    """Get autocomplete suggestions"""
    return {"suggestions": chatbot.get_suggestions(partial)}

@app.get("/")
def root():
    return {
        "message": "University Timetable Management System API",
        "status": "running",
        "version": "1.0.0"
    }

# Include API router
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
