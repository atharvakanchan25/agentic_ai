from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Time, DateTime
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class Department(Base):
    __tablename__ = 'departments'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    code = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    subjects = relationship('Subject', back_populates='department', cascade='all, delete-orphan')
    faculty = relationship('Faculty', back_populates='department')
    divisions = relationship('Division', back_populates='department')

class Subject(Base):
    __tablename__ = 'subjects'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    hours_per_week = Column(Integer, nullable=False, default=1)
    is_lab = Column(Boolean, default=False)
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    department = relationship('Department', back_populates='subjects')
    timetable_entries = relationship('TimetableEntry', back_populates='subject')

class Room(Base):
    __tablename__ = 'rooms'
    id = Column(Integer, primary_key=True)
    room_number = Column(String, unique=True, nullable=False)
    floor = Column(Integer, nullable=False)
    capacity = Column(Integer, nullable=False)
    bench_count = Column(Integer, nullable=False, default=0)
    is_lab = Column(Boolean, default=False)
    room_type = Column(String, nullable=False, default='Classroom')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    timetable_entries = relationship('TimetableEntry', back_populates='room')

class Faculty(Base):
    __tablename__ = 'faculty'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    employee_id = Column(String, unique=True, nullable=False)
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    department = relationship('Department', back_populates='faculty')
    timetable_entries = relationship('TimetableEntry', back_populates='faculty')

class Division(Base):
    __tablename__ = 'divisions'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    student_count = Column(Integer, nullable=False)
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    department = relationship('Department', back_populates='divisions')
    timetable_entries = relationship('TimetableEntry', back_populates='division')

class TimeSlot(Base):
    __tablename__ = 'timeslots'
    id = Column(Integer, primary_key=True)
    day = Column(String, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    slot_number = Column(Integer, nullable=False)
    
    # Relationships
    timetable_entries = relationship('TimetableEntry', back_populates='timeslot')

class TimetableEntry(Base):
    __tablename__ = 'timetable_entries'
    id = Column(Integer, primary_key=True)
    division_id = Column(Integer, ForeignKey('divisions.id'), nullable=False)
    subject_id = Column(Integer, ForeignKey('subjects.id'), nullable=False)
    faculty_id = Column(Integer, ForeignKey('faculty.id'), nullable=False)
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)
    timeslot_id = Column(Integer, ForeignKey('timeslots.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    division = relationship('Division', back_populates='timetable_entries')
    subject = relationship('Subject', back_populates='timetable_entries')
    faculty = relationship('Faculty', back_populates='timetable_entries')
    room = relationship('Room', back_populates='timetable_entries')
    timeslot = relationship('TimeSlot', back_populates='timetable_entries')
