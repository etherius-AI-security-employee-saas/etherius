from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EndpointRegister(BaseModel):
    hostname: str
    os: str
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    agent_version: Optional[str] = None

class EndpointEnroll(BaseModel):
    company_code: str
    employee_key: Optional[str] = None
    hostname: str
    os: str
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    agent_version: Optional[str] = None
    device_user: Optional[str] = None

class EndpointOut(BaseModel):
    id: str
    hostname: str
    os: str
    ip_address: Optional[str] = None
    status: str
    risk_score: str
    is_isolated: bool
    last_seen: Optional[datetime] = None
    created_at: datetime
    model_config = {"from_attributes": True}
