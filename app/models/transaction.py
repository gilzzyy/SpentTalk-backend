from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Integer, ForeignKey, Numeric, String, Date, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Transaction(Base):
    """
    Transaction parent class mapping to 'transactions' table.
    Demonstrates Inheritance (via Single Table Inheritance) and Polymorphism.
    """
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False) # Discriminator: 'income' or 'expense'
    transaction_date: Mapped[date] = mapped_column(Date, default=date.today)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="transactions")

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
        "polymorphic_identity": "income",
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
        "polymorphic_identity": "expense",
    }

    def get_signed_amount(self) -> Decimal:
        """Polymorphism: returns negative amount (outflow)."""
        return -self.amount

    def format_detail(self) -> str:
        """Polymorphism: returns format prefix for expense."""
        return f"[PENGELUARAN] {self.item_name}: -Rp {self.amount}"
