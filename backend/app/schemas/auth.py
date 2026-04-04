from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class CompanyRegister(BaseModel):
    company_name: str
    domain: Optional[str] = None
    admin_email: EmailStr
    admin_password: str
    admin_full_name: str
    subscription_key: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: str = "viewer"

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    company_id: str
    role: str
    full_name: Optional[str] = None


class EmployeeLicenseCreate(BaseModel):
    label: Optional[str] = None
    max_activations: int = 1
    valid_days: int = 365


class LicenseOut(BaseModel):
    id: str
    key_value: str
    key_type: str
    label: Optional[str] = None
    is_active: bool
    max_activations: int
    current_activations: int
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
