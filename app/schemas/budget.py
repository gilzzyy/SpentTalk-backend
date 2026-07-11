from decimal import Decimal
from pydantic import BaseModel, Field
from typing import List

class BudgetBase(BaseModel):
    category_id: int
    period: str = Field(..., pattern=r"^\d{4}-\d{2}$") # Format: 'YYYY-MM'
    amount: Decimal = Field(default=Decimal("0.00"), ge=0, le=Decimal("9999999999.99"))

class BudgetCreate(BudgetBase):
    pass

class BudgetOut(BudgetBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

from typing import Optional

class OnboardingBudget(BaseModel):
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    period: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    amount: Decimal = Field(..., ge=0, le=Decimal("9999999999.99"))

class OnboardingRequest(BaseModel):
    initial_balance: Decimal = Field(..., ge=0, le=Decimal("9999999999.99"))
    monthly_income: Decimal = Field(default=Decimal("0.00"), ge=0, le=Decimal("9999999999.99"))
    budgets: List[OnboardingBudget]


