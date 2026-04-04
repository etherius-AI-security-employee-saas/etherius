from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class EventSubmit(BaseModel):
    event_type: str
    severity: Optional[str] = "info"
    payload: Dict[str, Any]

class EventOut(BaseModel):
    id: str
    endpoint_id: str
    event_type: str
    severity: str
    risk_score: str
    created_at: datetime
    model_config = {"from_attributes": True}
