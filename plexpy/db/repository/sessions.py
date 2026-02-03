from typing import Optional

from sqlalchemy import select

from plexpy.db.models import Session, SessionContinued
from plexpy.db.repository.base import Repository


class SessionsRepository(Repository[Session]):
    model = Session

    def get_by_session_key(self, session_key: int) -> Optional[Session]:
        stmt = select(Session).where(Session.session_key == session_key)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_session_id(self, session_id: str) -> Optional[Session]:
        stmt = select(Session).where(Session.session_id == session_id)
        return self.session.execute(stmt).scalar_one_or_none()


class SessionsContinuedRepository(Repository[SessionContinued]):
    model = SessionContinued

    def get_by_identity(self, user_id: int, machine_id: str, media_type: str) -> Optional[SessionContinued]:
        stmt = select(SessionContinued).where(
            SessionContinued.user_id == user_id,
            SessionContinued.machine_id == machine_id,
            SessionContinued.media_type == media_type,
        )
        return self.session.execute(stmt).scalar_one_or_none()
