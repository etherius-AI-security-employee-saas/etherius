from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.sql import func
from app.database import Base
import uuid


class UsbDevice(Base):
    __tablename__ = "usb_devices"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    device_id = Column(String, nullable=False)
    device_name = Column(String, nullable=True)
    vendor = Column(String, nullable=True)
    size = Column(String, nullable=True)
    is_whitelisted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
