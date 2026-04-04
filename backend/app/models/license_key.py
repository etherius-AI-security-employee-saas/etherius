from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.sql import func
from app.database import Base
import uuid


class LicenseKey(Base):
    __tablename__ = "license_keys"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, ForeignKey("companies.id"), nullable=True, index=True)
    issued_by_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    used_by_endpoint_id = Column(String, ForeignKey("endpoints.id"), nullable=True)
    key_value = Column(String, nullable=False, unique=True, index=True)
    key_type = Column(String, nullable=False, default="employee")  # subscription / employee
    label = Column(String, nullable=True)
    seat_limit = Column(Integer, default=10)  # subscription seat count (employees/devices)
    max_activations = Column(Integer, default=1)
    current_activations = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
