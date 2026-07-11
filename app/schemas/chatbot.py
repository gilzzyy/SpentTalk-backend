from decimal import Decimal
from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.transaction import TransactionTypeEnum

class ChatMessage(BaseModel):
    message: str

class ParsedItem(BaseModel):
    item_name: str
    amount: Decimal
    category_name: str
    type: TransactionTypeEnum

class ParseResult(BaseModel):
    items: List[ParsedItem]
    raw_message: str
    chat_message_id: int

class ChatResponse(BaseModel):
    reply: str
    parse_result: Optional[ParseResult] = None
    needs_confirmation: bool = False

class ConfirmTransactionRequest(BaseModel):
    chat_message_id: int
    confirmed: bool
    override_item_name: Optional[str] = None
    override_amount: Optional[Decimal] = None
    override_category_id: Optional[int] = None
    override_type: Optional[TransactionTypeEnum] = None

