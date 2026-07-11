from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.repositories.base import BaseRepository

class NotificationRepository(BaseRepository[Notification]):
    """
    NotificationRepository implements data methods for managing user notifications.
    """
    def __init__(self, db: Session):
        super().__init__(db)

    def create(self, obj: Notification) -> Notification:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_by_id(self, id: int) -> Optional[Notification]:
        return self.db.query(Notification).filter(Notification.id == id).first()

    def get_all(self) -> List[Notification]:
        return self.db.query(Notification).all()

    def get_user_notifications(self, user_id: int, limit: int = 50) -> List[Notification]:
        return (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .all()
        )

    def mark_all_read(self, user_id: int) -> None:
        self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update({"is_read": True}, synchronize_session=False)
        self.db.commit()

    def update(self, obj: Notification) -> Notification:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, id: int) -> bool:
        obj = self.get_by_id(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False
