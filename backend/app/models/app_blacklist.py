from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.sql import func
from app.database import Base
import uuid


class AppBlacklist(Base):
    __tablename__ = "app_blacklist"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    app_name = Column(String, nullable=False)
    action = Column(String, nullable=False, default="kill")  # alert | kill
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
