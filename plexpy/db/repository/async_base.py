# -*- coding: utf-8 -*-

#  This file is part of Tautulli.
#
#  Tautulli is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Tautulli is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Tautulli.  If not, see <http://www.gnu.org/licenses/>.

"""
Advanced Alchemy Async Repository Base

Provides async repository layer using SQLAlchemyAsyncRepository
from advanced-alchemy with additional convenience methods.
"""
from typing import Any, Generic, Optional, TypeVar

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from advanced_alchemy.repository import SQLAlchemyAsyncRepository

from plexpy.db.models import Base


ModelT = TypeVar('ModelT', bound=Base)


class AdvancedAsyncRepository(SQLAlchemyAsyncRepository[ModelT], Generic[ModelT]):
    """
    Extended async repository with common query patterns.

    Inherits from SQLAlchemyAsyncRepository to provide:
    - Async CRUD operations
    - Built-in pagination (LimitOffset)
    - Built-in filtering (SearchFilter, OrderBy, etc.)
    - Built-in sorting
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_session(self) -> AsyncSession:
        """Return the async session for repository operations."""
        return self._session

    async def get_by_id(self, id: Any) -> Optional[ModelT]:
        """Get entity by primary key."""
        return await self.get(id)

    async def get_by_unique_field(
        self,
        field_name: str,
        value: Any,
    ) -> Optional[ModelT]:
        """Get entity by a unique field."""
        stmt = select(self.model_type).where(
            getattr(self.model_type, field_name) == value
        )
        result = await self.execute_statement(stmt)
        return result.scalar_one_or_none()

    async def exists_by_field(self, field_name: str, value: Any) -> bool:
        """Check if entity exists by field value."""
        stmt = select(func.count()).select_from(self.model_type).where(
            getattr(self.model_type, field_name) == value
        )
        result = await self.execute_statement(stmt)
        return (result.scalar() or 0) > 0

    async def count_by_filter(self, **filters) -> int:
        """Count entities matching filters."""
        stmt = select(func.count()).select_from(self.model_type)
        for field, value in filters.items():
            stmt = stmt.where(getattr(self.model_type, field) == value)
        result = await self.execute_statement(stmt)
        return result.scalar() or 0


__all__ = [
    'AdvancedAsyncRepository',
]
