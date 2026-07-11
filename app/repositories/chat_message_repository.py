from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.chat_message import ChatMessage
from app.repositories.base import BaseRepository

class ChatMessageRepository(BaseRepository[ChatMessage]):
    """
    ChatMessageRepository implements database operations for ChatMessage entities.
    """
    def __init__(self, db: Session):
        super().__init__(db)

    def create(self, obj: ChatMessage) -> ChatMessage:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_by_id(self, id: int) -> Optional[ChatMessage]:
        return self.db.query(ChatMessage).filter(ChatMessage.id == id).first()

    def get_user_messages(self, user_id: int, limit: int = 50) -> List[ChatMessage]:
        return self.db.query(ChatMessage).filter(
            ChatMessage.user_id == user_id
        ).order_by(ChatMessage.created_at.desc()).limit(limit).all()

    def get_all(self) -> List[ChatMessage]:
        return self.db.query(ChatMessage).all()

    def update(self, obj: ChatMessage) -> ChatMessage:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, id: int) -> bool:
        msg = self.get_by_id(id)
        if msg:
            self.db.delete(msg)
            self.db.commit()
            return True
        return False

    def get_pending_by_raw_text(self, user_id: int, raw_text: str) -> List[ChatMessage]:
        return self.db.query(ChatMessage).filter(
            ChatMessage.user_id == user_id,
            ChatMessage.raw_text == raw_text,
            ChatMessage.status == "pending"
        ).all()

