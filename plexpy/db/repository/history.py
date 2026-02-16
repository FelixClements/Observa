from typing import Optional, Sequence

from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from plexpy.db.models import SessionHistory, SessionHistoryMediaInfo, SessionHistoryMetadata
from plexpy.db.repository.base import Repository, DataTableParams, DataTableResponse


class SessionHistoryRepository(Repository[SessionHistory]):
    model = SessionHistory

    # Searchable columns for datatable queries
    _SEARCHABLE_COLUMNS = [
        SessionHistory.user,
        SessionHistory.player,
        SessionHistory.product,
        SessionHistory.platform,
        SessionHistory.media_type,
        SessionHistory.ip_address,
        SessionHistory.machine_id,
    ]

    # Orderable columns for datatable queries
    _ORDERABLE_COLUMNS = {
        'id': SessionHistory.id,
        'reference_id': SessionHistory.reference_id,
        'started': SessionHistory.started,
        'stopped': SessionHistory.stopped,
        'rating_key': SessionHistory.rating_key,
        'user_id': SessionHistory.user_id,
        'user': SessionHistory.user,
        'ip_address': SessionHistory.ip_address,
        'paused_counter': SessionHistory.paused_counter,
        'player': SessionHistory.player,
        'product': SessionHistory.product,
        'product_version': SessionHistory.product_version,
        'platform': SessionHistory.platform,
        'platform_version': SessionHistory.platform_version,
        'profile': SessionHistory.profile,
        'machine_id': SessionHistory.machine_id,
        'bandwidth': SessionHistory.bandwidth,
        'location': SessionHistory.location,
        'quality_profile': SessionHistory.quality_profile,
        'media_type': SessionHistory.media_type,
        'section_id': SessionHistory.section_id,
        'view_offset': SessionHistory.view_offset,
    }

    def get_by_reference_id(self, reference_id: int) -> Optional[SessionHistory]:
        stmt = select(SessionHistory).where(SessionHistory.reference_id == reference_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_recent(self, limit: int = 100) -> Sequence[SessionHistory]:
        stmt = select(SessionHistory).order_by(SessionHistory.stopped.desc()).limit(limit)
        return self.session.execute(stmt).scalars().all()

    def get_by_user_id(self, user_id: int, limit: int = 100) -> Sequence[SessionHistory]:
        stmt = (
            select(SessionHistory)
            .where(SessionHistory.user_id == user_id)
            .order_by(SessionHistory.started.desc())
            .limit(limit)
        )
        return self.session.execute(stmt).scalars().all()

    def get_by_media_type(self, media_type: str, limit: int = 100) -> Sequence[SessionHistory]:
        stmt = (
            select(SessionHistory)
            .where(SessionHistory.media_type == media_type)
            .order_by(SessionHistory.stopped.desc())
            .limit(limit)
        )
        return self.session.execute(stmt).scalars().all()

    def get_total_duration_by_user(self, user_id: int) -> int:
        stmt = (
            select(func.sum(SessionHistory.stopped - SessionHistory.started - SessionHistory.paused_counter))
            .where(SessionHistory.user_id == user_id)
            .where(SessionHistory.stopped > 0)
        )
        result = self.session.execute(stmt).scalar()
        return result or 0

    def get_total_duration_by_library(self, section_id: int) -> int:
        stmt = (
            select(func.sum(SessionHistory.stopped - SessionHistory.started - SessionHistory.paused_counter))
            .where(SessionHistory.section_id == section_id)
            .where(SessionHistory.stopped > 0)
        )
        result = self.session.execute(stmt).scalar()
        return result or 0

    def get_total_duration_by_media_type(self, media_type: str) -> int:
        stmt = (
            select(func.sum(SessionHistory.stopped - SessionHistory.started - SessionHistory.paused_counter))
            .where(SessionHistory.media_type == media_type)
            .where(SessionHistory.stopped > 0)
        )
        result = self.session.execute(stmt).scalar()
        return result or 0

    def count_by_user(self, user_id: int) -> int:
        stmt = select(func.count()).select_from(SessionHistory).where(SessionHistory.user_id == user_id)
        result = self.session.execute(stmt).scalar()
        return result or 0

    def count_by_media_type(self, media_type: str) -> int:
        stmt = select(func.count()).select_from(SessionHistory).where(SessionHistory.media_type == media_type)
        result = self.session.execute(stmt).scalar()
        return result or 0

    def count_by_user_and_media_type(self, user_id: int, media_type: str) -> int:
        stmt = (
            select(func.count())
            .select_from(SessionHistory)
            .where(SessionHistory.user_id == user_id)
            .where(SessionHistory.media_type == media_type)
        )
        result = self.session.execute(stmt).scalar()
        return result or 0

    def get_distinct_users(self) -> Sequence[int]:
        stmt = select(SessionHistory.user_id).distinct().where(SessionHistory.user_id.isnot(None))
        result = self.session.execute(stmt).scalars().all()
        return result

    def get_distinct_media_types(self) -> Sequence[str]:
        stmt = select(SessionHistory.media_type).distinct().where(SessionHistory.media_type.isnot(None))
        result = self.session.execute(stmt).scalars().all()
        return result

    def get_distinct_libraries(self) -> Sequence[int]:
        stmt = select(SessionHistory.section_id).distinct().where(SessionHistory.section_id.isnot(None))
        result = self.session.execute(stmt).scalars().all()
        return result

    def get_distinct_platforms(self) -> Sequence[str]:
        stmt = select(SessionHistory.platform).distinct().where(SessionHistory.platform.isnot(None))
        result = self.session.execute(stmt).scalars().all()
        return result

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


class SessionHistoryMetadataRepository(Repository[SessionHistoryMetadata]):
    model = SessionHistoryMetadata

    def get_by_rating_key(self, rating_key: int) -> Optional[SessionHistoryMetadata]:
        stmt = select(SessionHistoryMetadata).where(SessionHistoryMetadata.rating_key == rating_key)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_grandparent_rating_key(self, grandparent_rating_key: int) -> Sequence[SessionHistoryMetadata]:
        stmt = (
            select(SessionHistoryMetadata)
            .where(SessionHistoryMetadata.grandparent_rating_key == grandparent_rating_key)
        )
        return self.session.execute(stmt).scalars().all()

    def get_by_parent_rating_key(self, parent_rating_key: int) -> Sequence[SessionHistoryMetadata]:
        stmt = (
            select(SessionHistoryMetadata)
            .where(SessionHistoryMetadata.parent_rating_key == parent_rating_key)
        )
        return self.session.execute(stmt).scalars().all()


class SessionHistoryMediaInfoRepository(Repository[SessionHistoryMediaInfo]):
    model = SessionHistoryMediaInfo

    def get_by_rating_key(self, rating_key: int) -> Optional[SessionHistoryMediaInfo]:
        stmt = select(SessionHistoryMediaInfo).where(SessionHistoryMediaInfo.rating_key == rating_key)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_history_id(self, history_id: int) -> Optional[SessionHistoryMediaInfo]:
        stmt = select(SessionHistoryMediaInfo).where(SessionHistoryMediaInfo.id == history_id)
        return self.session.execute(stmt).scalar_one_or_none()
