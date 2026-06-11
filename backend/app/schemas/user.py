from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    auth_provider: str

class UserCreate(UserBase):
    id: UUID  # Synchronized from Supabase sub identifier

class UserUpdate(BaseModel):
    name: Optional[str] = None

class User(UserBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
