import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from database import create_document, get_documents

app = FastAPI(title="School ERP API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"name": "School ERP Backend", "version": "1.0.0"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        from database import db
        if db is not None:
            response["database"] = "✅ Connected & Working"
            response["database_url"] = "✅ Set"
            response["database_name"] = getattr(db, 'name', '✅ Connected')
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:20]
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# ----------------------------- Simple Helpers -----------------------------

class CreateResult(BaseModel):
    id: str

# Generic list endpoints for quick UI population (read-only)

@app.get("/students")
def list_students(limit: int = 50):
    items = get_documents("student", {}, limit)
    # Convert ObjectId to str for _id if present
    for x in items:
        if "_id" in x:
            x["_id"] = str(x["_id"])
    return items

@app.get("/teachers")
def list_teachers(limit: int = 50):
    items = get_documents("teacher", {}, limit)
    for x in items:
        if "_id" in x:
            x["_id"] = str(x["_id"])
    return items

@app.get("/classes")
def list_classes(limit: int = 50):
    items = get_documents("classroom", {}, limit)
    for x in items:
        if "_id" in x:
            x["_id"] = str(x["_id"])
    return items

# Minimal create endpoints for key entities

class StudentCreate(BaseModel):
    admission_number: str
    first_name: str
    last_name: str
    class_id: Optional[str] = None

@app.post("/students", response_model=CreateResult)
def create_student(payload: StudentCreate):
    student_data = payload.model_dump()
    student_data.setdefault("status", "active")
    new_id = create_document("student", student_data)
    return {"id": new_id}

class TeacherCreate(BaseModel):
    first_name: str
    last_name: str
    email: str

@app.post("/teachers", response_model=CreateResult)
def create_teacher(payload: TeacherCreate):
    new_id = create_document("teacher", payload.model_dump())
    return {"id": new_id}

class ClassCreate(BaseModel):
    name: str
    year: int

@app.post("/classes", response_model=CreateResult)
def create_class(payload: ClassCreate):
    new_id = create_document("classroom", payload.model_dump())
    return {"id": new_id}

# Finance quick endpoints
class InvoiceCreate(BaseModel):
    student_id: str
    invoice_number: str
    issue_date: date
    due_date: date
    amount: float

@app.post("/invoices", response_model=CreateResult)
def create_invoice(payload: InvoiceCreate):
    data = payload.model_dump()
    data.setdefault("status", "unpaid")
    new_id = create_document("feeinvoice", data)
    return {"id": new_id}

@app.get("/invoices")
def list_invoices(limit: int = 50):
    items = get_documents("feeinvoice", {}, limit)
    for x in items:
        if "_id" in x:
            x["_id"] = str(x["_id"])
    return items

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
