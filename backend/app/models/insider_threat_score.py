from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.sql import func
from app.database import Base
import uuid


class InsiderThreatScore(Base):
    __tablename__ = "insider_threat_scores"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    endpoint_id = Column(String, ForeignKey("endpoints.id"), nullable=False)
    score = Column(Integer, default=0)
    trend = Column(String, default="stable")  # rising | stable | falling
    factors = Column(JSON, nullable=True)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
