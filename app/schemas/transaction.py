from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class TransactionTypeEnum(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"

class TransactionBase(BaseModel):
    item_name: str = Field(..., max_length=200)
    amount: Decimal = Field(..., gt=0)
    category: str = Field(..., max_length=50)
    type: TransactionTypeEnum
    transaction_date: date = Field(default_factory=date.today)

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(BaseModel):
    item_name: Optional[str] = Field(None, max_length=200)
    amount: Optional[Decimal] = Field(None, gt=0)
    category: Optional[str] = Field(None, max_length=50)
    type: Optional[TransactionTypeEnum] = Field(None)
    transaction_date: Optional[date] = Field(None)

class TransactionOut(TransactionBase):
    id: int
    user_id: int
    created_at: datetime
    formatted_detail: Optional[str] = None

    class Config:
        from_attributes = True

class DashboardSummary(BaseModel):
    saldo_terkini: Decimal
    total_pemasukan_bulan_ini: Decimal
    total_pengeluaran_bulan_ini: Decimal
    budget_progress: Dict[str, Dict[str, Decimal]]
    recent_transactions: List[TransactionOut]
    ai_insight: Optional[str] = None
