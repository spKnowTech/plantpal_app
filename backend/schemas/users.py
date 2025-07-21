from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional


class CreateUser(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    location: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[str] = None


class ResponseUser(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    location: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

