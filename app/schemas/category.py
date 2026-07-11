from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

from decimal import Decimal

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    icon: Optional[str] = Field(None, max_length=50)

class CategoryCreate(CategoryBase):
    budget_amount: Optional[Decimal] = Field(None, ge=0)
    period: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}$")


class CategoryOut(CategoryBase):
    id: int
    user_id: int
    is_default: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
