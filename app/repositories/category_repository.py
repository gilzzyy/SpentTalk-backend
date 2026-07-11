from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.category import Category
from app.repositories.base import BaseRepository

class CategoryRepository(BaseRepository[Category]):
    """
    CategoryRepository implements database operations for Category entities.
    """
    def __init__(self, db: Session):
        super().__init__(db)

    def create(self, obj: Category) -> Category:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_by_id(self, id: int) -> Optional[Category]:
        return self.db.query(Category).filter(Category.id == id).first()

    def get_user_categories(self, user_id: int, only_active: bool = True) -> List[Category]:
        query = self.db.query(Category).filter(Category.user_id == user_id)
        if only_active:
            query = query.filter(Category.is_active == True)
        return query.all()

    def get_by_name(self, user_id: int, name: str) -> Optional[Category]:
        return self.db.query(Category).filter(
            Category.user_id == user_id,
            Category.name.ilike(name)
        ).first()


    def get_all(self) -> List[Category]:
        return self.db.query(Category).all()

    def update(self, obj: Category) -> Category:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, id: int) -> bool:
        category = self.get_by_id(id)
        if category:
            self.db.delete(category)
            self.db.commit()
            return True
        return False
