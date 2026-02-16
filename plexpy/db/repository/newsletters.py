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

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from plexpy.db.models import Newsletter, NewsletterLog
from plexpy.db.repository.async_base import AdvancedAsyncRepository
from plexpy.db.repository.base import Repository, DataTableParams, DataTableResponse


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


class NewsletterLogRepository(Repository[NewsletterLog]):
    """Repository for NewsletterLog model."""

    # Searchable columns for datatable queries
    _SEARCHABLE_COLUMNS = [
        NewsletterLog.agent_name,
        NewsletterLog.notify_action,
        NewsletterLog.subject_text,
        NewsletterLog.body_text,
        NewsletterLog.message_text,
    ]

    # Orderable columns for datatable queries
    _ORDERABLE_COLUMNS = {
        'id': NewsletterLog.id,
        'timestamp': NewsletterLog.timestamp,
        'newsletter_id': NewsletterLog.newsletter_id,
        'agent_id': NewsletterLog.agent_id,
        'agent_name': NewsletterLog.agent_name,
        'notify_action': NewsletterLog.notify_action,
        'subject_text': NewsletterLog.subject_text,
        'body_text': NewsletterLog.body_text,
        'message_text': NewsletterLog.message_text,
        'start_date': NewsletterLog.start_date,
        'end_date': NewsletterLog.end_date,
        'start_time': NewsletterLog.start_time,
        'end_time': NewsletterLog.end_time,
        'uuid': NewsletterLog.uuid,
        'filename': NewsletterLog.filename,
        'email_msg_id': NewsletterLog.email_msg_id,
        'success': NewsletterLog.success,
    }

    def get_by_uuid(self, uuid: str) -> Optional[NewsletterLog]:
        """Get newsletter log by UUID."""
        stmt = select(NewsletterLog).where(NewsletterLog.uuid == uuid)
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def list_recent(self, limit: int = 100) -> list[NewsletterLog]:
        """List recent newsletter logs."""
        stmt = select(NewsletterLog).order_by(
            NewsletterLog.timestamp.desc()
        ).limit(limit)
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def get_by_newsletter_id(self, newsletter_id: int, limit: int = 100) -> list[NewsletterLog]:
        """Get newsletter logs by newsletter ID."""
        stmt = (
            select(NewsletterLog)
            .where(NewsletterLog.newsletter_id == newsletter_id)
            .order_by(NewsletterLog.timestamp.desc())
            .limit(limit)
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def get_by_status(self, status: str, limit: int = 100) -> list[NewsletterLog]:
        """Get newsletter logs by status (e.g., 'failed', 'sent')."""
        stmt = (
            select(NewsletterLog)
            .where(NewsletterLog.status == status)
            .order_by(NewsletterLog.timestamp.desc())
            .limit(limit)
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def count_by_status(self, status: str) -> int:
        """Count newsletter logs by status."""
        stmt = select(func.count()).select_from(NewsletterLog).where(NewsletterLog.status == status)
        result = self.session.execute(stmt)
        return result.scalar() or 0

    def delete_old_logs(self, before_timestamp: int) -> int:
        """Delete newsletter logs older than timestamp. Returns count of deleted rows."""
        stmt = NewsletterLog.__table__.delete().where(NewsletterLog.timestamp < before_timestamp)
        result = self.session.execute(stmt)
        return result.rowcount

    def datatable_query(
        self,
        params: DataTableParams,
        searchable_columns: list = None,
        orderable_columns: dict = None,
        formatter=None,
        extra_filters: list = None,
    ) -> DataTableResponse:
        """
        Execute a datatable query with search, sort, and pagination.

        This method provides the same functionality as the legacy datatables.py
        but uses the repository pattern with SQLAlchemy ORM.

        Args:
            params: DataTableParams with draw, start, length, search, order, columns
            searchable_columns: Columns to search (optional, uses default)
            orderable_columns: Columns to sort by (optional, uses default)
            formatter: Custom row formatter (optional)
            extra_filters: Additional SQLAlchemy filters (optional)

        Returns:
            DataTableResponse with recordsTotal, recordsFiltered, data, draw
        """
        return super().datatable_query(
            params=params,
            searchable_columns=searchable_columns or self._SEARCHABLE_COLUMNS,
            orderable_columns=orderable_columns or self._ORDERABLE_COLUMNS,
            formatter=formatter,
            extra_filters=extra_filters,
        )


__all__ = [
    'NewsletterRepository',
    'NewsletterLogRepository',
]
