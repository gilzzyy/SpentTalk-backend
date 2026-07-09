from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    nama: str = Field(..., min_length=2, max_length=100)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)
    password_confirm: str = Field(..., min_length=6, max_length=100)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    nama: str = Field(None, min_length=2, max_length=100)
    email: EmailStr = Field(None)
    old_password: str = Field(None, min_length=6)
    new_password: str = Field(None, min_length=6)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: str = None

class UserOut(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
