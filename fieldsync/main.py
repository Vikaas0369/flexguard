from typing import Literal
from fastapi import ( Depends, FastAPI, File, HTTPException, UploadFile, )
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from pathlib import Path

from fieldsync import models
from fieldsync.database import Base, SessionLocal, engine


app = FastAPI(
    title="FieldSync API",
    description="Demo field inspection API used by FlexGuard.",
    version="0.1.0",
)


Base.metadata.create_all(bind=engine)

UPLOAD_DIR = Path("uploads")

UPLOAD_DIR.mkdir(
    exist_ok=True
)


class InspectionCreate(BaseModel):
    location: str = Field(min_length=2, max_length=100)
    inspector: str = Field(min_length=2, max_length=100)
    finding: str = Field(min_length=3, max_length=500)
    notes: str | None = Field(default=None, max_length=1000)
    risk_level: Literal["Low", "Medium", "High", "Critical"]


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "FieldSync API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/inspections")
def create_inspection(
    inspection: InspectionCreate,
    db: Session = Depends(get_db)
):
    new_inspection = models.Inspection(
        location=inspection.location,
        inspector=inspection.inspector,
        finding=inspection.finding,
        notes=inspection.notes,
        risk_level=inspection.risk_level,
        status="created"
    )

    db.add(new_inspection)
    db.commit()
    db.refresh(new_inspection)

    return new_inspection


@app.get("/inspections")
def get_inspections(
    db: Session = Depends(get_db)
):
    return db.query(models.Inspection).all()


@app.get("/inspections/{inspection_id}")
def get_inspection(
    inspection_id: int,
    db: Session = Depends(get_db)
):
    inspection = (
        db.query(models.Inspection)
        .filter(models.Inspection.id == inspection_id)
        .first()
    )

    if inspection is None:
        raise HTTPException(
            status_code=404,
            detail="Inspection not found"
        )

    return inspection

@app.post("/inspections/{inspection_id}/submit")
def submit_inspection(
    inspection_id: int,
    db: Session = Depends(get_db)
):
    inspection = (
        db.query(models.Inspection)
        .filter(models.Inspection.id == inspection_id)
        .first()
    )

    if inspection is None:
        raise HTTPException(
            status_code=404,
            detail="Inspection not found"
        )

    if inspection.status == "submitted":
        raise HTTPException(
            status_code=400,
            detail="Inspection is already submitted"
        )

    inspection.status = "submitted"

    db.commit()
    db.refresh(inspection)

    return {
        "message": "Inspection submitted",
        "inspection": inspection
    }

@app.post("/inspections/{inspection_id}/evidence")
async def upload_evidence(
    inspection_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    inspection = (
        db.query(models.Inspection)
        .filter(models.Inspection.id == inspection_id)
        .first()
    )

    if inspection is None:
        raise HTTPException(
            status_code=404,
            detail="Inspection not found"
        )

    allowed_types = [
        "image/jpeg",
        "image/png"
    ]

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Only JPG and PNG images are allowed"
        )

    safe_name = Path(file.filename).name

    file_name = (
        f"inspection_{inspection_id}_{safe_name}"
    )

    file_path = UPLOAD_DIR / file_name

    file_content = await file.read()

    with open(file_path, "wb") as saved_file:
        saved_file.write(file_content)

    inspection.evidence_path = str(file_path)

    db.commit()
    db.refresh(inspection)

    return {
        "message": "Evidence uploaded",
        "inspection_id": inspection.id,
        "evidence_path": inspection.evidence_path
    }