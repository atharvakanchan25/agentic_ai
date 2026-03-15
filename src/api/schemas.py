"""
Pydantic schemas for API request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=2, max_length=10)

class DepartmentOut(DepartmentCreate):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True


class SubjectCreate(BaseModel):
    name: str = Field(..., min_length=2)
    code: str = Field(..., min_length=2, max_length=20)
    hours_per_week: int = Field(..., ge=1, le=10)
    is_lab: bool = False
    department_id: int

class SubjectOut(SubjectCreate):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True


class RoomCreate(BaseModel):
    room_number: str = Field(..., min_length=1)
    floor: int = Field(0, ge=0, le=20)
    capacity: int = Field(..., ge=10, le=500)
    is_lab: bool = False
    room_type: str = "classroom"

class RoomOut(RoomCreate):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True


class FacultyCreate(BaseModel):
    name: str = Field(..., min_length=2)
    employee_id: str = Field(..., min_length=3)
    department_id: int

class FacultyOut(FacultyCreate):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True


class DivisionCreate(BaseModel):
    name: str = Field(..., min_length=1)
    year: int = Field(..., ge=1, le=4)
    student_count: int = Field(..., ge=1, le=200)
    department_id: int

class DivisionOut(DivisionCreate):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True


class TimeSlotOut(BaseModel):
    id: int
    day: str
    slot_number: int
    start_time: str
    end_time: str
    class Config:
        from_attributes = True


class TimetableRequest(BaseModel):
    department_ids: List[int]

class ChatRequest(BaseModel):
    message: str
    context: dict = {}
