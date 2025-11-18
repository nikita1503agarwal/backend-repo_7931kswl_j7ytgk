"""
Database Schemas for School ERP

Each Pydantic model below represents a MongoDB collection. The collection
name is the lowercase of the class name (e.g., Student -> "student").

These schemas are used for data validation and to power the database
viewer. You can safely extend them as your needs grow.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import date, datetime

# ----------------------------- Core People -----------------------------

class Parent(BaseModel):
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    relationship: Optional[str] = Field(None, description="Relationship to student e.g., father, mother, guardian")

class Student(BaseModel):
    admission_number: str = Field(..., description="Unique admission/enrollment number")
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, description="male/female/other")
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    class_id: Optional[str] = Field(None, description="Reference to ClassRoom _id as string")
    parent_ids: List[str] = Field(default_factory=list, description="List of Parent _id as strings")
    status: str = Field("active", description="active, graduated, transferred, suspended")

class Teacher(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    hire_date: Optional[date] = None
    subjects: List[str] = Field(default_factory=list, description="Subject _ids as strings they teach")
    status: str = Field("active", description="active, inactive")

# ----------------------------- Academic Structure -----------------------------

class Subject(BaseModel):
    name: str
    code: str
    description: Optional[str] = None

class ClassRoom(BaseModel):
    name: str = Field(..., description="e.g., Grade 10 - A")
    year: int
    class_teacher_id: Optional[str] = Field(None, description="Teacher _id as string")
    subject_ids: List[str] = Field(default_factory=list)

class Course(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    subject_ids: List[str] = Field(default_factory=list)

class Enrollment(BaseModel):
    student_id: str
    class_id: str
    year: int
    status: str = Field("enrolled", description="enrolled, completed, dropped")

class TimetableEntry(BaseModel):
    class_id: str
    subject_id: str
    teacher_id: str
    day_of_week: str = Field(..., description="Mon, Tue, Wed, Thu, Fri, Sat, Sun")
    start_time: str = Field(..., description="24h format HH:MM")
    end_time: str = Field(..., description="24h format HH:MM")
    room: Optional[str] = None

# ----------------------------- Attendance & Grading -----------------------------

class AttendanceRecord(BaseModel):
    class_id: str
    student_id: str
    date: date
    status: str = Field(..., description="present, absent, late, excused")
    remarks: Optional[str] = None

class Exam(BaseModel):
    name: str
    subject_id: str
    class_id: str
    date: date
    max_marks: int = 100

class Grade(BaseModel):
    student_id: str
    exam_id: str
    marks_obtained: float
    grade: Optional[str] = None
    remark: Optional[str] = None

# ----------------------------- Finance -----------------------------

class FeeInvoice(BaseModel):
    student_id: str
    invoice_number: str
    issue_date: date
    due_date: date
    description: Optional[str] = None
    amount: float
    status: str = Field("unpaid", description="unpaid, partial, paid")

class Payment(BaseModel):
    student_id: str
    invoice_id: str
    amount: float
    date: date
    method: str = Field(..., description="cash, card, bank, online")
    reference: Optional[str] = None

# ----------------------------- Communication -----------------------------

class Announcement(BaseModel):
    title: str
    body: str
    audience: str = Field("all", description="all, students, teachers, class:<id>")
    published_at: Optional[datetime] = None
    author_id: Optional[str] = None

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You can still create custom API endpoints for business workflows
