from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from bson import ObjectId

# Generic type variable
T = TypeVar('T')

class GenericDAO(ABC, Generic[T]):
    """Generic DAO interface"""

    @abstractmethod
    def get_by_id(self, _id: ObjectId) -> T | None:
        pass

    @abstractmethod
    def get_all(self) -> list[T] | None:
        pass

    @abstractmethod
    def save(self, obj: T) -> bool:
        pass

    @abstractmethod
    def update(self, obj: T) -> bool:
        pass

    @abstractmethod
    def delete(self, _id: ObjectId) -> bool:
        pass