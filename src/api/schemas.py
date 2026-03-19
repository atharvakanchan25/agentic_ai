"""
Pydantic schemas for API request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2)
    email: str
    password: str = Field(..., min_length=6)

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


# ── Departments ───────────────────────────────────────────────────────────────

class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=2, max_length=10)

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None

class DepartmentOut(DepartmentCreate):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True


# ── Subjects ──────────────────────────────────────────────────────────────────

class SubjectCreate(BaseModel):
    name: str = Field(..., min_length=2)
    code: str = Field(..., min_length=2, max_length=20)
    hours_per_week: int = Field(..., ge=1, le=10)
    is_lab: bool = False
    department_id: int

class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    hours_per_week: Optional[int] = None
    is_lab: Optional[bool] = None
    department_id: Optional[int] = None

class SubjectOut(SubjectCreate):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True


# ── Rooms ─────────────────────────────────────────────────────────────────────

class RoomCreate(BaseModel):
    room_number: str = Field(..., min_length=1)
    floor: int = Field(0, ge=0, le=20)
    capacity: int = Field(..., ge=10, le=500)
    is_lab: bool = False
    room_type: str = "classroom"

class RoomUpdate(BaseModel):
    room_number: Optional[str] = None
    floor: Optional[int] = None
    capacity: Optional[int] = None
    is_lab: Optional[bool] = None
    room_type: Optional[str] = None

class RoomOut(RoomCreate):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True


# ── Faculty ───────────────────────────────────────────────────────────────────

class FacultyCreate(BaseModel):
    name: str = Field(..., min_length=2)
    employee_id: str = Field(..., min_length=3)
    department_id: int

class FacultyUpdate(BaseModel):
    name: Optional[str] = None
    employee_id: Optional[str] = None
    department_id: Optional[int] = None

class FacultyOut(FacultyCreate):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True


# ── Divisions ─────────────────────────────────────────────────────────────────

class DivisionCreate(BaseModel):
    name: str = Field(..., min_length=1)
    year: int = Field(..., ge=1, le=4)
    student_count: int = Field(..., ge=1, le=200)
    department_id: int

class DivisionUpdate(BaseModel):
    name: Optional[str] = None
    year: Optional[int] = None
    student_count: Optional[int] = None
    department_id: Optional[int] = None

class DivisionOut(DivisionCreate):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True


# ── Timeslots ─────────────────────────────────────────────────────────────────

class TimeSlotOut(BaseModel):
    id: int
    day: str
    slot_number: int
    start_time: str
    end_time: str
    class Config:
        from_attributes = True


# ── Timetable ─────────────────────────────────────────────────────────────────

class TimetableRequest(BaseModel):
    department_ids: List[int]
    save: bool = False
    name: Optional[str] = None

class SavedTimetableOut(BaseModel):
    id: int
    name: str
    department_ids: str
    created_at: datetime
    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    message: str
    context: dict = {}
