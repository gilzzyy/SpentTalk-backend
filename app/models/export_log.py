from datetime import date, datetime
from sqlalchemy import BigInteger, ForeignKey, String, Date, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class ExportLog(Base):
    """
    ExportLog entity mapping to 'export_logs' table.
    Tracks spreadsheet exports requested by the user.
    """
    __tablename__ = "export_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="export_logs")

    def __init__(self, user_id: int, file_path: str, period_start: date, period_end: date):
        self.user_id = user_id
        self.file_path = file_path
        self.period_start = period_start
        self.period_end = period_end
