from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.sql import func
from app.database import Base
import uuid


class BlockedDomain(Base):
    __tablename__ = "blocked_domains"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    domain = Column(String, nullable=False)
    category = Column(String, nullable=True)  # gambling | adult | social | custom
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
