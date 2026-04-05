from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.sql import func
from app.database import Base
import uuid


class AgentCommand(Base):
    __tablename__ = "agent_commands"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    endpoint_id = Column(String, ForeignKey("endpoints.id"), nullable=False)
    command_type = Column(String, nullable=False)  # lock_screen | show_message | restart_agent
    payload = Column(JSON, nullable=True)
    status = Column(String, nullable=False, default="pending")  # pending | executed | failed
    result_text = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    executed_at = Column(DateTime(timezone=True), nullable=True)
