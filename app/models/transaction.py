from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import BigInteger, ForeignKey, Numeric, String, Date, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Transaction(Base):
    """
    Transaction parent class mapping to 'transactions' table.
    Demonstrates Inheritance (via Single Table Inheritance) and Polymorphism.
    """
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)
    chat_message_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chat_messages.id", ondelete="SET NULL"), nullable=True, default=None)
    item_name: Mapped[str] = mapped_column(String(150), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False) # Discriminator: 'pemasukan' or 'pengeluaran'
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    transaction_date: Mapped[date] = mapped_column(Date, default=date.today)
    notes: Mapped[str] = mapped_column(String(255), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
    chat_message = relationship("ChatMessage", foreign_keys=[chat_message_id])


    __mapper_args__ = {
        "polymorphic_on": "type",
        "polymorphic_identity": "transaction",
    }

    def get_signed_amount(self) -> Decimal:
        """
        Polymorphic method. Overridden by subclasses.
        """
        return self.amount

    def format_detail(self) -> str:
        """
        Polymorphic method. Overridden by subclasses.
        """
        return f"{self.item_name}: Rp {self.amount}"


class IncomeTransaction(Transaction):
    """
    IncomeTransaction represents cash inflow (Inheritance).
    """
    __mapper_args__ = {
        "polymorphic_identity": "pemasukan",
    }

    def get_signed_amount(self) -> Decimal:
        """Polymorphism: returns positive amount."""
        return self.amount

    def format_detail(self) -> str:
        """Polymorphism: returns format prefix for income."""
        return f"[PEMASUKAN] {self.item_name}: +Rp {self.amount}"


class ExpenseTransaction(Transaction):
    """
    ExpenseTransaction represents cash outflow (Inheritance).
    """
    __mapper_args__ = {
        "polymorphic_identity": "pengeluaran",
    }

    def get_signed_amount(self) -> Decimal:
        """Polymorphism: returns negative amount (outflow)."""
        return -self.amount

    def format_detail(self) -> str:
        """Polymorphism: returns format prefix for expense."""
        return f"[PENGELUARAN] {self.item_name}: -Rp {self.amount}"
