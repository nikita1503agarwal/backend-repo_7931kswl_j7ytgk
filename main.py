import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date
from database import create_document, get_documents
from bson import ObjectId

app = FastAPI(title="School ERP API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"name": "School ERP Backend", "version": "1.1.0"}

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

# ----------------------------- Utilities -----------------------------

def to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")


def serialize(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not doc:
        return doc
    d = dict(doc)
    if "_id" in d:
        d["_id"] = str(d["_id"])
    return d


def serialize_many(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [serialize(x) for x in items]


def build_search_query(q: Optional[str], fields: List[str]) -> Dict[str, Any]:
    if not q:
        return {}
    # Case-insensitive regex OR across fields
    regex = {"$regex": q, "$options": "i"}
    return {"$or": [{f: regex} for f in fields]}

# ----------------------------- Models -----------------------------

class CreateResult(BaseModel):
    id: str

# Students
class StudentCreate(BaseModel):
    admission_number: str
    first_name: str
    last_name: str
    class_id: Optional[str] = None
    status: Optional[str] = None

class StudentUpdate(BaseModel):
    admission_number: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    class_id: Optional[str] = None
    status: Optional[str] = None

# Teachers
class TeacherCreate(BaseModel):
    first_name: str
    last_name: str
    email: str

class TeacherUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None

# Classes
class ClassCreate(BaseModel):
    name: str
    year: int

class ClassUpdate(BaseModel):
    name: Optional[str] = None
    year: Optional[int] = None
    class_teacher_id: Optional[str] = None

# Finance
class InvoiceCreate(BaseModel):
    student_id: str
    invoice_number: str
    issue_date: date
    due_date: date
    amount: float

class InvoiceUpdate(BaseModel):
    student_id: Optional[str] = None
    invoice_number: Optional[str] = None
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    amount: Optional[float] = None
    status: Optional[str] = None

# ----------------------------- CRUD: Students -----------------------------

@app.get("/students")
def list_students(limit: int = 50, q: Optional[str] = None, page: Optional[int] = None, page_size: Optional[int] = None):
    from database import db
    fields = ["admission_number", "first_name", "last_name", "status"]
    query = build_search_query(q, fields)
    cursor = db["student"].find(query).sort("created_at", -1)

    if page and page_size:
        total = cursor.count() if hasattr(cursor, 'count') else db["student"].count_documents(query)
        skip = (page - 1) * page_size
        items = list(cursor.skip(skip).limit(page_size))
        return {"items": serialize_many(items), "total": int(total)}

    items = list(cursor.limit(limit))
    return serialize_many(items)

@app.post("/students", response_model=CreateResult)
def create_student(payload: StudentCreate):
    student_data = payload.model_dump(exclude_none=True)
    student_data.setdefault("status", "active")
    new_id = create_document("student", student_data)
    return {"id": new_id}

@app.get("/students/{id}")
def get_student(id: str):
    from database import db
    doc = db["student"].find_one({"_id": to_object_id(id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Student not found")
    return serialize(doc)

@app.put("/students/{id}")
def update_student(id: str, payload: StudentUpdate):
    from database import db
    data = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
    res = db["student"].update_one({"_id": to_object_id(id)}, {"$set": data})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"updated": True}

@app.delete("/students/{id}")
def delete_student(id: str):
    from database import db
    res = db["student"].delete_one({"_id": to_object_id(id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"deleted": True}

# ----------------------------- CRUD: Teachers -----------------------------

@app.get("/teachers")
def list_teachers(limit: int = 50, q: Optional[str] = None, page: Optional[int] = None, page_size: Optional[int] = None):
    from database import db
    fields = ["first_name", "last_name", "email", "status"]
    query = build_search_query(q, fields)
    cursor = db["teacher"].find(query).sort("created_at", -1)

    if page and page_size:
        total = cursor.count() if hasattr(cursor, 'count') else db["teacher"].count_documents(query)
        skip = (page - 1) * page_size
        items = list(cursor.skip(skip).limit(page_size))
        return {"items": serialize_many(items), "total": int(total)}

    items = list(cursor.limit(limit))
    return serialize_many(items)

@app.post("/teachers", response_model=CreateResult)
def create_teacher(payload: TeacherCreate):
    new_id = create_document("teacher", payload.model_dump(exclude_none=True))
    return {"id": new_id}

@app.get("/teachers/{id}")
def get_teacher(id: str):
    from database import db
    doc = db["teacher"].find_one({"_id": to_object_id(id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return serialize(doc)

@app.put("/teachers/{id}")
def update_teacher(id: str, payload: TeacherUpdate):
    from database import db
    data = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
    res = db["teacher"].update_one({"_id": to_object_id(id)}, {"$set": data})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return {"updated": True}

@app.delete("/teachers/{id}")
def delete_teacher(id: str):
    from database import db
    res = db["teacher"].delete_one({"_id": to_object_id(id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return {"deleted": True}

# ----------------------------- CRUD: Classes -----------------------------

@app.get("/classes")
def list_classes(limit: int = 50, q: Optional[str] = None, page: Optional[int] = None, page_size: Optional[int] = None):
    from database import db
    fields = ["name", "year", "class_teacher_id"]
    query = build_search_query(q, fields)
    cursor = db["classroom"].find(query).sort("created_at", -1)

    if page and page_size:
        total = cursor.count() if hasattr(cursor, 'count') else db["classroom"].count_documents(query)
        skip = (page - 1) * page_size
        items = list(cursor.skip(skip).limit(page_size))
        return {"items": serialize_many(items), "total": int(total)}

    items = list(cursor.limit(limit))
    return serialize_many(items)

@app.post("/classes", response_model=CreateResult)
def create_class(payload: ClassCreate):
    new_id = create_document("classroom", payload.model_dump(exclude_none=True))
    return {"id": new_id}

@app.get("/classes/{id}")
def get_class(id: str):
    from database import db
    doc = db["classroom"].find_one({"_id": to_object_id(id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Class not found")
    return serialize(doc)

@app.put("/classes/{id}")
def update_class(id: str, payload: ClassUpdate):
    from database import db
    data = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
    res = db["classroom"].update_one({"_id": to_object_id(id)}, {"$set": data})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Class not found")
    return {"updated": True}

@app.delete("/classes/{id}")
def delete_class(id: str):
    from database import db
    res = db["classroom"].delete_one({"_id": to_object_id(id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Class not found")
    return {"deleted": True}

# ----------------------------- CRUD: Invoices -----------------------------

@app.get("/invoices")
def list_invoices(limit: int = 50, q: Optional[str] = None, page: Optional[int] = None, page_size: Optional[int] = None):
    from database import db
    fields = ["invoice_number", "student_id", "status"]
    query = build_search_query(q, fields)
    cursor = db["feeinvoice"].find(query).sort("created_at", -1)

    if page and page_size:
        total = cursor.count() if hasattr(cursor, 'count') else db["feeinvoice"].count_documents(query)
        skip = (page - 1) * page_size
        items = list(cursor.skip(skip).limit(page_size))
        return {"items": serialize_many(items), "total": int(total)}

    items = list(cursor.limit(limit))
    return serialize_many(items)

@app.post("/invoices", response_model=CreateResult)
def create_invoice(payload: InvoiceCreate):
    data = payload.model_dump(exclude_none=True)
    data.setdefault("status", "unpaid")
    new_id = create_document("feeinvoice", data)
    return {"id": new_id}

@app.get("/invoices/{id}")
def get_invoice(id: str):
    from database import db
    doc = db["feeinvoice"].find_one({"_id": to_object_id(id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return serialize(doc)

@app.put("/invoices/{id}")
def update_invoice(id: str, payload: InvoiceUpdate):
    from database import db
    data = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
    res = db["feeinvoice"].update_one({"_id": to_object_id(id)}, {"$set": data})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {"updated": True}

@app.delete("/invoices/{id}")
def delete_invoice(id: str):
    from database import db
    res = db["feeinvoice"].delete_one({"_id": to_object_id(id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {"deleted": True}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
