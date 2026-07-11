from datetime import datetime
from decimal import Decimal
from sqlalchemy import BigInteger, ForeignKey, String, Numeric, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class ChatMessage(Base):
    """
    ChatMessage entity mapping to 'chat_messages' table.
    Caches parsed NLP items before confirmation.
    """
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_item_name: Mapped[str] = mapped_column(String(150), nullable=True, default=None)
    parsed_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=True, default=None)
    parsed_category_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, default=None)
    parsed_type: Mapped[str] = mapped_column(String(20), nullable=True, default=None) # 'pemasukan' or 'pengeluaran'
    status: Mapped[str] = mapped_column(String(20), default="pending") # 'pending', 'confirmed', 'rejected'
    transaction_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="chat_messages")
    parsed_category = relationship("Category")
    transaction = relationship("Transaction", foreign_keys=[transaction_id], post_update=True)



    def __init__(
        self,
        user_id: int,
        raw_text: str,
        parsed_item_name: str = None,
        parsed_amount: Decimal = None,
        parsed_category_id: int = None,
        parsed_type: str = None,
        status: str = "pending"
    ):
        self.user_id = user_id
        self.raw_text = raw_text
        self.parsed_item_name = parsed_item_name
        self.parsed_amount = parsed_amount
        self.parsed_category_id = parsed_category_id
        self.parsed_type = parsed_type
        self.status = status
