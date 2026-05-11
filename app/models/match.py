"""
Sanos y Salvos — Match Models (PostgreSQL + SQLAlchemy)
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pydantic import BaseModel, Field
from typing import Optional

from app.config import Base


# --- SQLAlchemy Models ---

class MatchDB(Base):
    __tablename__ = "matches"
    __table_args__ = {"schema": "match_service"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_lost_id = Column(Integer, nullable=False)
    report_found_id = Column(Integer, nullable=False)
    score = Column(Float, nullable=False)
    score_breakdown = Column(JSONB)
    status = Column(String(20), default="pendiente")
    pet_lost_name = Column(String(100))
    pet_found_name = Column(String(100))
    user_lost_id = Column(Integer)
    user_found_id = Column(Integer)
    notified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ReportCacheDB(Base):
    __tablename__ = "report_cache"
    __table_args__ = {"schema": "match_service"}

    report_id = Column(Integer, primary_key=True)
    report_type = Column(String(20), nullable=False)
    pet_name = Column(String(100))
    species = Column(String(50))
    breed = Column(String(100))
    color = Column(String(100))
    size = Column(String(20))
    latitude = Column(Float)
    longitude = Column(Float)
    date_event = Column(Date)
    user_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


# --- Pydantic Schemas (API Layer) ---

class MatchResult(BaseModel):
    """Represents a match between a lost and found pet report."""
    report_lost_id: int
    report_found_id: int
    score: float = Field(..., ge=0, le=100, description="Match confidence score (0-100)")
    score_breakdown: dict = Field(default_factory=dict, description="Detailed scoring by criteria")
    status: str = Field(default="pendiente", description="pendiente, confirmado, descartado")
    pet_lost_name: Optional[str] = None
    pet_found_name: Optional[str] = None
    user_lost_id: int = 0
    user_found_id: int = 0
    notified: bool = False

    class Config:
        from_attributes = True
