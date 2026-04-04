from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AlertOut(BaseModel):
    id: str
    company_id: str
    endpoint_id: Optional[str] = None
    title: str
    description: str
    severity: str
    status: str
    risk_score: str
    ai_explanation: Optional[str] = None
    assigned_to: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class AlertUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[str] = None
