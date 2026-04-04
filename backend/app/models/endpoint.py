from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base
import uuid

class Endpoint(Base):
    __tablename__ = "endpoints"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    hostname = Column(String, nullable=False)
    os = Column(String, nullable=False)
    ip_address = Column(String, nullable=True)
    mac_address = Column(String, nullable=True)
    agent_token = Column(String, nullable=True, unique=True)
    agent_version = Column(String, nullable=True)
    is_isolated = Column(Boolean, default=False)
    risk_score = Column(String, default="0")
    status = Column(String, default="offline")  # online/offline/isolated
    last_seen = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
