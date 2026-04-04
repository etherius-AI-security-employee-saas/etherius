from sqlalchemy import Column, String, Boolean, DateTime, Integer
from sqlalchemy.sql import func
from app.database import Base
import uuid

class Company(Base):
    __tablename__ = "companies"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    domain = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    plan = Column(String, default="starter")  # starter / pro / enterprise
    max_endpoints = Column(Integer, default=10)
    logo_url = Column(String, nullable=True)
    subscription_key = Column(String, nullable=True, unique=True)
    subscription_status = Column(String, default="active")
    subscription_expires_at = Column(DateTime(timezone=True), nullable=True)
    license_enforcement = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
