from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.sql import func
from app.database import Base
import uuid


class SoftwareInventory(Base):
    __tablename__ = "software_inventory"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    endpoint_id = Column(String, ForeignKey("endpoints.id"), nullable=False)
    software_name = Column(String, nullable=False)
    version = Column(String, nullable=True)
    cve_id = Column(String, nullable=True)
    severity = Column(String, nullable=True)
    is_vulnerable = Column(Boolean, default=False)
    last_scanned_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
