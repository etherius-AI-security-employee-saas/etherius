from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base
import uuid


class UsbPolicy(Base):
    __tablename__ = "usb_policies"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, ForeignKey("companies.id"), nullable=False, unique=True)
    policy = Column(String, nullable=False, default="allow_all")  # allow_all | block_all | whitelist
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
