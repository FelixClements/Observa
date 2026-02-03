from typing import Optional

from sqlalchemy import select

from plexpy.db.models import SessionHistory, SessionHistoryMediaInfo, SessionHistoryMetadata
from plexpy.db.repository.base import Repository


class SessionHistoryRepository(Repository[SessionHistory]):
    model = SessionHistory

    def get_by_reference_id(self, reference_id: int) -> Optional[SessionHistory]:
        stmt = select(SessionHistory).where(SessionHistory.reference_id == reference_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_recent(self, limit: int = 100):
        stmt = select(SessionHistory).order_by(SessionHistory.stopped.desc()).limit(limit)
        return self.session.execute(stmt).scalars().all()


class SessionHistoryMetadataRepository(Repository[SessionHistoryMetadata]):
    model = SessionHistoryMetadata

    def get_by_rating_key(self, rating_key: int) -> Optional[SessionHistoryMetadata]:
        stmt = select(SessionHistoryMetadata).where(SessionHistoryMetadata.rating_key == rating_key)
        return self.session.execute(stmt).scalar_one_or_none()


class SessionHistoryMediaInfoRepository(Repository[SessionHistoryMediaInfo]):
    model = SessionHistoryMediaInfo

    def get_by_rating_key(self, rating_key: int) -> Optional[SessionHistoryMediaInfo]:
        stmt = select(SessionHistoryMediaInfo).where(SessionHistoryMediaInfo.rating_key == rating_key)
        return self.session.execute(stmt).scalar_one_or_none()
