from typing import Any, Generic, Iterable, Optional, Sequence, TypeVar

from sqlalchemy.orm import Session
from sqlalchemy import select

from plexpy.db.models import Base


ModelT = TypeVar('ModelT', bound=Base)


class Repository(Generic[ModelT]):
    model: Optional[type[ModelT]] = None

    def __init__(self, session: Session):
        self.session = session

    def add(self, instance: ModelT) -> ModelT:
        self.session.add(instance)
        return instance

    def add_all(self, instances: Iterable[ModelT]) -> Iterable[ModelT]:
        instance_list = list(instances)
        self.session.add_all(instance_list)
        return instance_list

    def delete(self, instance: ModelT) -> None:
        self.session.delete(instance)

    def get(self, model, primary_key):
        return self.session.get(model, primary_key)

    def get_by_id(self, primary_key: Any) -> Optional[ModelT]:
        if self.model is None:
            raise ValueError("Repository model is not set")
        return self.session.get(self.model, primary_key)

    def list_all(self) -> Sequence[ModelT]:
        if self.model is None:
            raise ValueError("Repository model is not set")
        return self.session.execute(select(self.model)).scalars().all()

    def first_by(self, **filters: Any) -> Optional[ModelT]:
        if self.model is None:
            raise ValueError("Repository model is not set")
        stmt = select(self.model).filter_by(**filters).limit(1)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_by(self, **filters: Any) -> Sequence[ModelT]:
        if self.model is None:
            raise ValueError("Repository model is not set")
        stmt = select(self.model).filter_by(**filters)
        return self.session.execute(stmt).scalars().all()
