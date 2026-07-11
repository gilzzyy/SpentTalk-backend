from datetime import datetime
from sqlalchemy import BigInteger, ForeignKey, String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Category(Base):
    """
    Category entity mapping to the 'categories' table.
    """
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    icon: Mapped[str] = mapped_column(String(50), nullable=True, default=None)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="categories")
    budgets = relationship("Budget", back_populates="category", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="category")

    def __init__(self, user_id: int, name: str, icon: str = None, is_default: bool = False):
        self.user_id = user_id
        self.name = name
        self.icon = icon
        self.is_default = is_default
        self.is_active = True
