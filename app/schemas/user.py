from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)
    password_confirm: str = Field(..., min_length=6, max_length=100)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = Field(None)
    university: Optional[str] = Field(None, max_length=255)
    old_password: Optional[str] = Field(None, min_length=6)
    new_password: Optional[str] = Field(None, min_length=6)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None

class UserOut(UserBase):
    id: int
    profile_photo_url: Optional[str] = None
    initial_balance: Decimal
    current_balance: Decimal
    onboarding_completed: bool
    is_active: bool
    university: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

