from datetime import datetime
from sqlalchemy import BigInteger, ForeignKey, String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Notification(Base):
    """
    Notification entity mapping to the 'notifications' table.
    Tracks user alerts for transaction entries, Excel exports, and budget warnings.
    """
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(String(255), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    type: Mapped[str] = mapped_column(String(50), default="info") # "transaction", "export", "alert"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="notifications")

    def __init__(self, user_id: int, title: str, message: str, type: str = "info"):
        self.user_id = user_id
        self.title = title
        self.message = message
        self.type = type
        self.is_read = False
