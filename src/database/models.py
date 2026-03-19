"""
Database Models
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String, nullable=False)
    email           = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime, default=datetime.utcnow)


class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    code = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    subjects  = relationship("Subject", back_populates="department")
    faculty   = relationship("Faculty", back_populates="department")
    divisions = relationship("Division", back_populates="department")


class Subject(Base):
    __tablename__ = "subjects"
    id             = Column(Integer, primary_key=True, index=True)
    name           = Column(String, nullable=False)
    code           = Column(String, unique=True, nullable=False)
    hours_per_week = Column(Integer, default=3)
    is_lab         = Column(Boolean, default=False)
    department_id  = Column(Integer, ForeignKey("departments.id"), nullable=False)
    created_at     = Column(DateTime, default=datetime.utcnow)

    department = relationship("Department", back_populates="subjects")


class Room(Base):
    __tablename__ = "rooms"
    id          = Column(Integer, primary_key=True, index=True)
    room_number = Column(String, unique=True, nullable=False)
    floor       = Column(Integer, default=0)
    capacity    = Column(Integer, nullable=False)
    is_lab      = Column(Boolean, default=False)
    room_type   = Column(String, default="classroom")
    created_at  = Column(DateTime, default=datetime.utcnow)


class Faculty(Base):
    __tablename__ = "faculty"
    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String, nullable=False)
    employee_id   = Column(String, unique=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)

    department = relationship("Department", back_populates="faculty")


class Division(Base):
    __tablename__ = "divisions"
    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String, nullable=False)
    year          = Column(Integer, nullable=False)
    student_count = Column(Integer, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)

    department = relationship("Department", back_populates="divisions")


class TimeSlot(Base):
    __tablename__ = "timeslots"
    id          = Column(Integer, primary_key=True, index=True)
    day         = Column(String, nullable=False)
    slot_number = Column(Integer, nullable=False)
    start_time  = Column(String, nullable=False)
    end_time    = Column(String, nullable=False)


class TimetableEntry(Base):
    __tablename__ = "timetable_entries"
    id           = Column(Integer, primary_key=True, index=True)
    division_id  = Column(Integer, ForeignKey("divisions.id"), nullable=False)
    subject_id   = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    room_id      = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    faculty_id   = Column(Integer, ForeignKey("faculty.id"), nullable=True)
    timeslot_id  = Column(Integer, ForeignKey("timeslots.id"), nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)


class AgentMemory(Base):
    """Long-term memory store for all agents."""
    __tablename__ = "agent_memory"
    id         = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String, nullable=False, index=True)
    key        = Column(String, nullable=False, index=True)
    value      = Column(Text, nullable=False)
    run_id     = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PipelineRun(Base):
    """Tracks each timetable generation run for HITL checkpoints."""
    __tablename__ = "pipeline_runs"
    id              = Column(String, primary_key=True)
    status          = Column(String, default="running")
    stage           = Column(String, nullable=True)
    input_data      = Column(Text, nullable=True)
    checkpoint_data = Column(Text, nullable=True)
    result          = Column(Text, nullable=True)
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SavedTimetable(Base):
    __tablename__ = "saved_timetables"
    id             = Column(Integer, primary_key=True, index=True)
    name           = Column(String, nullable=False)
    department_ids = Column(String, nullable=False)
    result_json    = Column(Text, nullable=False)
    created_by     = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at     = Column(DateTime, default=datetime.utcnow)
