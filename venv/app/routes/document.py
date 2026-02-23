import os
import time
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.database import SessionLocal
from app.models.document import Document
from app.models.document_status_history import DocumentStatusHistory
from app.schemas.document_schema import DocumentResponse
from app.dependencies.auth_dependency import get_current_user
from app.dependencies.role_dependency import admin_only
from app.models.user import User


router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


# ---------------- DATABASE DEPENDENCY ---------------- #

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------- FILE VALIDATION ---------------- #

ALLOWED_TYPES = ["application/pdf", "image/jpeg", "image/png"]
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


# ---------------- BACKGROUND FUNCTION ---------------- #

def log_document_review(document_id: int, status: str):
    time.sleep(2)
    print(f"Document {document_id} has been {status}. Email sent to user.")


# ---------------- USER: UPLOAD ---------------- #

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type")

    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")

    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{file.filename}"

    with open(file_path, "wb") as f:
        f.write(contents)

    document = Document(
        filename=file.filename,
        file_path=file_path,
        uploaded_by=current_user.id,
        status="pending",
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document


# ---------------- USER: VIEW OWN ---------------- #

@router.get("/my", response_model=list[DocumentResponse])
def get_my_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    documents = db.query(Document).filter(
        Document.uploaded_by == current_user.id
    ).all()

    return documents


# ---------------- ADMIN: ADVANCED FILTERING ---------------- #

@router.get("/all", response_model=list[DocumentResponse])
def get_all_documents(
    status: str = Query(None),
    search: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(5, ge=1),
    current_user: User = Depends(admin_only),
    db: Session = Depends(get_db),
):

    query = db.query(Document)

    # Filter by status
    if status:
        query = query.filter(Document.status == status)

    # Search by filename
    if search:
        query = query.filter(Document.filename.ilike(f"%{search}%"))

    # Filter by date range
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(
                and_(Document.created_at >= start, Document.created_at <= end)
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Pagination
    offset = (page - 1) * limit
    documents = query.offset(offset).limit(limit).all()

    return documents


# ---------------- ADMIN: REVIEW DOCUMENT ---------------- #

@router.put("/review/{document_id}")
def review_document(
    document_id: int,
    new_status: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    document = db.query(Document).filter(
        Document.id == document_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if new_status not in ["approved", "rejected"]:
        raise HTTPException(
            status_code=400,
            detail="Status must be 'approved' or 'rejected'"
        )

    old_status = document.status
    document.status = new_status

    history = DocumentStatusHistory(
        document_id=document.id,
        old_status=old_status,
        new_status=new_status
    )

    db.add(history)
    db.commit()
    db.refresh(document)

    background_tasks.add_task(log_document_review, document.id, new_status)

    return {
        "message": f"Document {new_status} successfully",
        "document_id": document.id
    }
