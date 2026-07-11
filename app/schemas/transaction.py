from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.category import CategoryOut

class TransactionTypeEnum(str, Enum):
    INCOME = "pemasukan"
    EXPENSE = "pengeluaran"

class TransactionBase(BaseModel):
    item_name: str = Field(..., max_length=150)
    amount: Decimal = Field(..., gt=0)
    category_id: int
    type: TransactionTypeEnum
    transaction_date: date = Field(default_factory=date.today)
    notes: Optional[str] = Field(None, max_length=255)

class TransactionCreate(TransactionBase):
    chat_message_id: Optional[int] = None

class TransactionUpdate(BaseModel):
    item_name: Optional[str] = Field(None, max_length=150)
    amount: Optional[Decimal] = Field(None, gt=0)
    category_id: Optional[int] = None
    type: Optional[TransactionTypeEnum] = None
    transaction_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=255)

class TransactionOut(TransactionBase):
    id: int
    user_id: int
    chat_message_id: Optional[int] = None
    created_at: datetime
    formatted_detail: Optional[str] = None
    category: Optional[CategoryOut] = None

    class Config:
        from_attributes = True

class HistorySummary(BaseModel):
    total_transaksi: int
    total_pemasukan: Decimal
    total_pengeluaran: Decimal
    transactions: List[TransactionOut]

class DashboardSummary(BaseModel):
    saldo_terkini: Decimal
    total_pemasukan_bulan_ini: Decimal
    total_pengeluaran_bulan_ini: Decimal
    budget_progress: List[dict]
    recent_transactions: List[TransactionOut]
    ai_insight: Optional[str] = None
