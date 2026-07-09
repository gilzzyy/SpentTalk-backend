from datetime import datetime
from decimal import Decimal
from sqlalchemy import Integer, ForeignKey, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class FinancialProfile(Base):
    """
    FinancialProfile entity mapping to the 'financial_profiles' table.
    Enforces Encapsulation of financial settings and target budgets.
    """
    __tablename__ = "financial_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    saldo_awal: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0.00)
    penghasilan_bulanan: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0.00)
    budget_makan: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0.00)
    budget_transport: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0.00)
    budget_jajan: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0.00)
    budget_lainnya: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0.00)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="financial_profile")

    def __init__(
        self,
        user_id: int,
        saldo_awal: Decimal = Decimal("0.0"),
        penghasilan_bulanan: Decimal = Decimal("0.0"),
        budget_makan: Decimal = Decimal("0.0"),
        budget_transport: Decimal = Decimal("0.0"),
        budget_jajan: Decimal = Decimal("0.0"),
        budget_lainnya: Decimal = Decimal("0.0"),
    ):
        self.user_id = user_id
        self.saldo_awal = saldo_awal
        self.penghasilan_bulanan = penghasilan_bulanan
        self.budget_makan = budget_makan
        self.budget_transport = budget_transport
        self.budget_jajan = budget_jajan
        self.budget_lainnya = budget_lainnya

    @property
    def total_budget(self) -> Decimal:
        """Returns the sum of all monthly budgets (Encapsulation logic)."""
        return self.budget_makan + self.budget_transport + self.budget_jajan + self.budget_lainnya
