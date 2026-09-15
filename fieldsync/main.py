from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI(
    title="FieldSync API",
    description="Demo field inspection API used by FlexGuard.",
    version="0.1.0",
)


class InspectionCreate(BaseModel):
    location: str
    inspector: str
    finding: str
    risk_level: str


inspections = []


@app.get("/")
def root():
    return {
        "message": "FieldSync API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/inspections")
def create_inspection(inspection: InspectionCreate):
    inspection_id = len(inspections) + 1

    new_inspection = {
        "id": inspection_id,
        "location": inspection.location,
        "inspector": inspection.inspector,
        "finding": inspection.finding,
        "risk_level": inspection.risk_level,
        "status": "created",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    inspections.append(new_inspection)

    return new_inspection


@app.get("/inspections")
def get_inspections():
    return inspections

@app.get("/inspections/{inspection_id}")
def get_inspection(inspection_id: int):
    for inspection in inspections:
        if inspection["id"] == inspection_id:
            return inspection

    raise HTTPException(
        status_code=404,
        detail="Inspection not found"
    )