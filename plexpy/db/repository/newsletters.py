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
Newsletter Repository

Provides data access for Newsletter and NewsletterLog models.
"""
from typing import Optional

from sqlalchemy import select

from plexpy.db.models import Newsletter, NewsletterLog
from plexpy.db.repository.async_base import AdvancedAsyncRepository


class NewsletterRepository(AdvancedAsyncRepository[Newsletter]):
    """Repository for Newsletter model."""

    async def get_by_id_name(self, id_name: str) -> Optional[Newsletter]:
        """Get newsletter by id_name."""
        stmt = select(Newsletter).where(Newsletter.id_name == id_name)
        result = await self.execute_statement(stmt)
        return result.scalar_one_or_none()

    async def list_active(self) -> list[Newsletter]:
        """List all active newsletters."""
        stmt = select(Newsletter).where(Newsletter.active == 1)
        result = await self.execute_statement(stmt)
        return list(result.scalars().all())


class NewsletterLogRepository(AdvancedAsyncRepository[NewsletterLog]):
    """Repository for NewsletterLog model."""

    async def get_by_uuid(self, uuid: str) -> Optional[NewsletterLog]:
        """Get newsletter log by UUID."""
        stmt = select(NewsletterLog).where(NewsletterLog.uuid == uuid)
        result = await self.execute_statement(stmt)
        return result.scalar_one_or_none()

    async def list_recent(self, limit: int = 100) -> list[NewsletterLog]:
        """List recent newsletter logs."""
        stmt = select(NewsletterLog).order_by(
            NewsletterLog.timestamp.desc()
        ).limit(limit)
        result = await self.execute_statement(stmt)
        return list(result.scalars().all())

    async def get_by_newsletter_id(self, newsletter_id: int, limit: int = 100) -> list[NewsletterLog]:
        """Get newsletter logs by newsletter ID."""
        stmt = (
            select(NewsletterLog)
            .where(NewsletterLog.newsletter_id == newsletter_id)
            .order_by(NewsletterLog.timestamp.desc())
            .limit(limit)
        )
        result = await self.execute_statement(stmt)
        return list(result.scalars().all())

    async def get_by_status(self, status: str, limit: int = 100) -> list[NewsletterLog]:
        """Get newsletter logs by status (e.g., 'failed', 'sent')."""
        stmt = (
            select(NewsletterLog)
            .where(NewsletterLog.status == status)
            .order_by(NewsletterLog.timestamp.desc())
            .limit(limit)
        )
        result = await self.execute_statement(stmt)
        return list(result.scalars().all())

    async def count_by_status(self, status: str) -> int:
        """Count newsletter logs by status."""
        from sqlalchemy import func
        stmt = select(func.count()).select_from(NewsletterLog).where(NewsletterLog.status == status)
        result = await self.execute_statement(stmt)
        return result.scalar() or 0

    async def delete_old_logs(self, before_timestamp: int) -> int:
        """Delete newsletter logs older than timestamp. Returns count of deleted rows."""
        stmt = NewsletterLog.__table__.delete().where(NewsletterLog.timestamp < before_timestamp)
        result = await self.execute_statement(stmt)
        return result.rowcount


__all__ = [
    'NewsletterRepository',
    'NewsletterLogRepository',
]
