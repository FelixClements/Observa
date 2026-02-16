from typing import Optional, Sequence

from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from plexpy.db.models import SessionHistory, SessionHistoryMediaInfo, SessionHistoryMetadata
from plexpy.db.repository.base import Repository


class SessionHistoryRepository(Repository[SessionHistory]):
    model = SessionHistory

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
