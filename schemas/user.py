from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional


class CreateUser(BaseModel):
    """Model for user registration."""
    full_name: str
    email: EmailStr
    password: str
    location: Optional[str] = None


class LoginUser(BaseModel):
    """Model for user login."""
    email: EmailStr
    password: str

class ResponseUser(BaseModel):
    """Response model for user data."""
    id: int
    full_name: str
    email: EmailStr
    location: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
