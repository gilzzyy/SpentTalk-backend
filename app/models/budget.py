from datetime import datetime
from decimal import Decimal
from sqlalchemy import BigInteger, ForeignKey, Numeric, DateTime, CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Budget(Base):
    """
    Budget entity mapping to the 'budgets' table.
    Stores spending limits for categories on a monthly basis ('YYYY-MM').
    """
    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    period: Mapped[str] = mapped_column(CHAR(7), nullable=False) # Format: 'YYYY-MM'
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="budgets")
    category = relationship("Category", back_populates="budgets")

    def __init__(self, user_id: int, category_id: int, period: str, amount: Decimal = Decimal("0.00")):
        self.user_id = user_id
        self.category_id = category_id
        self.period = period
        self.amount = amount
