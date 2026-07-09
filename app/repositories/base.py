from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional
from sqlalchemy.orm import Session

T = TypeVar("T")

class BaseRepository(ABC, Generic[T]):
    """
    Abstract Base Class for all Repositories.
    Demonstrates Abstraction by defining core CRUD interface without implementation details.
    """
    def __init__(self, db: Session):
        self.db = db

    @abstractmethod
    def create(self, obj: T) -> T:
        pass

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]:
        pass

    @abstractmethod
    def get_all(self) -> List[T]:
        pass

    @abstractmethod
    def update(self, obj: T) -> T:
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        pass
