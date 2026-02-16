from typing import Optional, Sequence

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from plexpy.db.models import Notifier, NotifyLog
from plexpy.db.repository.base import Repository, DataTableParams, DataTableResponse


class NotifiersRepository(Repository[Notifier]):
    model = Notifier

    def get_by_agent_id(self, agent_id: int) -> Optional[Notifier]:
        stmt = select(Notifier).where(Notifier.agent_id == agent_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_active(self) -> Sequence[Notifier]:
        stmt = select(Notifier).where(Notifier.agent_id.isnot(None))
        return self.session.execute(stmt).scalars().all()


class NotifyLogRepository(Repository[NotifyLog]):
    model = NotifyLog

    # Searchable columns for datatable queries
    _SEARCHABLE_COLUMNS = [
        NotifyLog.user,
        NotifyLog.agent_name,
        NotifyLog.notify_action,
        NotifyLog.subject_text,
        NotifyLog.body_text,
    ]

    # Orderable columns for datatable queries
    _ORDERABLE_COLUMNS = {
        'id': NotifyLog.id,
        'timestamp': NotifyLog.timestamp,
        'session_key': NotifyLog.session_key,
        'rating_key': NotifyLog.rating_key,
        'user_id': NotifyLog.user_id,
        'user': NotifyLog.user,
        'notifier_id': NotifyLog.notifier_id,
        'agent_id': NotifyLog.agent_id,
        'agent_name': NotifyLog.agent_name,
        'notify_action': NotifyLog.notify_action,
        'subject_text': NotifyLog.subject_text,
        'body_text': NotifyLog.body_text,
        'success': NotifyLog.success,
    }

    def list_recent(self, limit: int = 100) -> Sequence[NotifyLog]:
        stmt = select(NotifyLog).order_by(NotifyLog.timestamp.desc()).limit(limit)
        return self.session.execute(stmt).scalars().all()

    def get_by_notifier_id(self, notifier_id: int, limit: int = 100) -> Sequence[NotifyLog]:
        stmt = (
            select(NotifyLog)
            .where(NotifyLog.notifier_id == notifier_id)
            .order_by(NotifyLog.timestamp.desc())
            .limit(limit)
        )
        return self.session.execute(stmt).scalars().all()

    def get_by_user_id(self, user_id: int, limit: int = 100) -> Sequence[NotifyLog]:
        stmt = (
            select(NotifyLog)
            .where(NotifyLog.user_id == user_id)
            .order_by(NotifyLog.timestamp.desc())
            .limit(limit)
        )
        return self.session.execute(stmt).scalars().all()

    def get_by_rating_key(self, rating_key: int, limit: int = 100) -> Sequence[NotifyLog]:
        stmt = (
            select(NotifyLog)
            .where(NotifyLog.rating_key == rating_key)
            .order_by(NotifyLog.timestamp.desc())
            .limit(limit)
        )
        return self.session.execute(stmt).scalars().all()

    def count_by_notifier(self, notifier_id: int) -> int:
        stmt = select(func.count()).select_from(NotifyLog).where(NotifyLog.notifier_id == notifier_id)
        result = self.session.execute(stmt).scalar()
        return result or 0

    def delete_old_logs(self, before_timestamp: int) -> int:
        stmt = NotifyLog.__table__.delete().where(NotifyLog.timestamp < before_timestamp)
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
