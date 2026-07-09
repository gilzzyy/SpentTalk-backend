from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.transaction import Transaction
from app.repositories.base import BaseRepository

class TransactionRepository(BaseRepository[Transaction]):
    """
    TransactionRepository implements BaseRepository for Transaction entities.
    Supports querying transactions with filters (date range, category, etc.).
    """
    def __init__(self, db: Session):
        super().__init__(db)

    def create(self, obj: Transaction) -> Transaction:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_by_id(self, id: int) -> Optional[Transaction]:
        return self.db.query(Transaction).filter(Transaction.id == id).first()

    def get_all(self) -> List[Transaction]:
        return self.db.query(Transaction).all()

    def get_by_user(
        self,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Transaction]:
        query = self.db.query(Transaction).filter(Transaction.user_id == user_id)
        
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)
        if category:
            query = query.filter(Transaction.category == category)
            
        query = query.order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
        
        if limit:
            query = query.limit(limit)
            
        return query.all()

    def update(self, obj: Transaction) -> Transaction:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, id: int) -> bool:
        transaction = self.get_by_id(id)
        if transaction:
            self.db.delete(transaction)
            self.db.commit()
            return True
        return False
