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
Export Repository

Provides data access for Export model.
"""
from typing import Optional

from sqlalchemy import select

from plexpy.db.models import Export
from plexpy.db.repository.async_base import AdvancedAsyncRepository


class ExportRepository(AdvancedAsyncRepository[Export]):
    """Repository for Export model."""

    async def get_by_section_id(
        self,
        section_id: int,
        user_id: Optional[int] = None,
    ) -> list[Export]:
        """Get exports by section_id, optionally filtered by user_id."""
        stmt = select(Export).where(Export.section_id == section_id)
        if user_id is not None:
            stmt = stmt.where(Export.user_id == user_id)
        stmt = stmt.order_by(Export.timestamp.desc())
        result = await self.execute_statement(stmt)
        return list(result.scalars().all())

    async def get_incomplete(self) -> list[Export]:
        """Get incomplete exports."""
        stmt = select(Export).where(Export.complete == 0)
        result = await self.execute_statement(stmt)
        return list(result.scalars().all())


__all__ = [
    'ExportRepository',
]
