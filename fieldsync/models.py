from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from fieldsync.database import Base


class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)

    location = Column(String, nullable=False)

    inspector = Column(String, nullable=False)

    finding = Column(String, nullable=False)

    notes = Column(
        Text,
        nullable=True
    )

    evidence_path = Column(
        String,
        nullable=True
    )

    risk_level = Column(String, nullable=False)

    status = Column(
        String,
        nullable=False,
        default="created"
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )