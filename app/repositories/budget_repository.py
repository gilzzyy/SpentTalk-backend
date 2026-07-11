from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.budget import Budget
from app.repositories.base import BaseRepository

class BudgetRepository(BaseRepository[Budget]):
    """
    BudgetRepository implements database operations for Budget entities.
    """
    def __init__(self, db: Session):
        super().__init__(db)

    def create(self, obj: Budget) -> Budget:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_by_id(self, id: int) -> Optional[Budget]:
        return self.db.query(Budget).filter(Budget.id == id).first()

    def get_user_budgets(self, user_id: int, period: str) -> List[Budget]:
        return self.db.query(Budget).filter(
            Budget.user_id == user_id,
            Budget.period == period
        ).all()

    def get_by_user_and_category(self, user_id: int, category_id: int, period: str) -> Optional[Budget]:
        return self.db.query(Budget).filter(
            Budget.user_id == user_id,
            Budget.category_id == category_id,
            Budget.period == period
        ).first()

    def get_all(self) -> List[Budget]:
        return self.db.query(Budget).all()

    def update(self, obj: Budget) -> Budget:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, id: int) -> bool:
        budget = self.get_by_id(id)
        if budget:
            self.db.delete(budget)
            self.db.commit()
            return True
        return False
