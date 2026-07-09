from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.base import BaseRepository

class UserRepository(BaseRepository[User]):
    """
    UserRepository implements BaseRepository for User entities.
    """
    def __init__(self, db: Session):
        super().__init__(db)

    def create(self, obj: User) -> User:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_by_id(self, id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_all(self) -> List[User]:
        return self.db.query(User).all()

    def update(self, obj: User) -> User:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, id: int) -> bool:
        user = self.get_by_id(id)
        if user:
            self.db.delete(user)
            self.db.commit()
            return True
        return False
