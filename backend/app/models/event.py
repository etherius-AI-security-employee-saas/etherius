from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.sql import func
from app.database import Base
import uuid

class Event(Base):
    __tablename__ = "events"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    endpoint_id = Column(String, ForeignKey("endpoints.id"), nullable=False)
    event_type = Column(String, nullable=False)
    severity = Column(String, default="info")
    payload = Column(JSON, nullable=False)
    risk_score = Column(String, default="0")
    flagged = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
