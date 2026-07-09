from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.profile import FinancialProfile
from app.repositories.base import BaseRepository

class ProfileRepository(BaseRepository[FinancialProfile]):
    """
    ProfileRepository implements BaseRepository for FinancialProfile entities.
    """
    def __init__(self, db: Session):
        super().__init__(db)

    def create(self, obj: FinancialProfile) -> FinancialProfile:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_by_id(self, id: int) -> Optional[FinancialProfile]:
        return self.db.query(FinancialProfile).filter(FinancialProfile.id == id).first()

    def get_by_user_id(self, user_id: int) -> Optional[FinancialProfile]:
        return self.db.query(FinancialProfile).filter(FinancialProfile.user_id == user_id).first()

    def get_all(self) -> List[FinancialProfile]:
        return self.db.query(FinancialProfile).all()

    def update(self, obj: FinancialProfile) -> FinancialProfile:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, id: int) -> bool:
        profile = self.get_by_id(id)
        if profile:
            self.db.delete(profile)
            self.db.commit()
            return True
        return False
