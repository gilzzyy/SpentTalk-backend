from datetime import datetime
from sqlalchemy import BigInteger, ForeignKey, String, Text, DateTime, CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class AIInsight(Base):
    """
    AIInsight entity mapping to 'ai_insights' table.
    Stores generated AI observations and budget alert messages.
    """
    __tablename__ = "ai_insights"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, default=None)
    period: Mapped[str] = mapped_column(CHAR(7), nullable=False) # Format: 'YYYY-MM'
    insight_type: Mapped[str] = mapped_column(String(30), nullable=False) # 'budget_warning', 'boros_category', 'general'
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="ai_insights")
    category = relationship("Category")

    def __init__(self, user_id: int, period: str, insight_type: str, message: str, category_id: int = None):
        self.user_id = user_id
        self.period = period
        self.insight_type = insight_type
        self.message = message
        self.category_id = category_id
