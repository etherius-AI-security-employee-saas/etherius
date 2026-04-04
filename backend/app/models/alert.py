from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.sql import func
from app.database import Base
import uuid

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    endpoint_id = Column(String, ForeignKey("endpoints.id"), nullable=True)
    event_id = Column(String, ForeignKey("events.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String, nullable=False)
    status = Column(String, default="open")
    assigned_to = Column(String, nullable=True)
    ai_explanation = Column(Text, nullable=True)
    risk_score = Column(String, default="0")
    auto_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
