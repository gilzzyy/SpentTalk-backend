from decimal import Decimal
from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.transaction import TransactionTypeEnum

class ChatMessage(BaseModel):
    message: str

class ParsedItem(BaseModel):
    item_name: str
    amount: Decimal
    category: str
    type: TransactionTypeEnum

class ParseResult(BaseModel):
    items: List[ParsedItem]
    raw_message: str

class ChatResponse(BaseModel):
    reply: str
    parse_result: Optional[ParseResult] = None
    needs_confirmation: bool = False

class ConfirmTransactionRequest(BaseModel):
    raw_message: str
    items: List[ParsedItem]
    confirmed: bool
