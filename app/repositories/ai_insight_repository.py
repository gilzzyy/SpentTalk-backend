from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.ai_insight import AIInsight
from app.repositories.base import BaseRepository

class AIInsightRepository(BaseRepository[AIInsight]):
    """
    AIInsightRepository implements database operations for AIInsight entities.
    """
    def __init__(self, db: Session):
        super().__init__(db)

    def create(self, obj: AIInsight) -> AIInsight:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_by_id(self, id: int) -> Optional[AIInsight]:
        return self.db.query(AIInsight).filter(AIInsight.id == id).first()

    def get_user_insights(self, user_id: int, period: str) -> List[AIInsight]:
        return self.db.query(AIInsight).filter(
            AIInsight.user_id == user_id,
            AIInsight.period == period
        ).order_by(AIInsight.created_at.desc()).all()

    def get_all(self) -> List[AIInsight]:
        return self.db.query(AIInsight).all()

    def update(self, obj: AIInsight) -> AIInsight:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, id: int) -> bool:
        insight = self.get_by_id(id)
        if insight:
            self.db.delete(insight)
            self.db.commit()
            return True
        return False
