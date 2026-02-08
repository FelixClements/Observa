from typing import Generic, TypeVar
from sqlalchemy.orm import Session

from plexpy.db.repository.base import ExtendedRepository


ModelT = TypeVar('ModelT', bound='Base')


class BaseService:
    """Base service class for dependency injection and session management."""

    def __init__(self, session: Session):
        self.session = session


class RepositoryService(BaseService, Generic[ModelT]):
    """Base service with repository access."""

    def __init__(self, session: Session, repository: ExtendedRepository[ModelT]):
        super().__init__(session)
        self.repository = repository
