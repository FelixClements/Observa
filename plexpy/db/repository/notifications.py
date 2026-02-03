from typing import Optional

from sqlalchemy import select

from plexpy.db.models import Notifier, NotifyLog
from plexpy.db.repository.base import Repository


class NotifiersRepository(Repository[Notifier]):
    model = Notifier

    def get_by_agent_id(self, agent_id: int) -> Optional[Notifier]:
        stmt = select(Notifier).where(Notifier.agent_id == agent_id)
        return self.session.execute(stmt).scalar_one_or_none()


class NotifyLogRepository(Repository[NotifyLog]):
    model = NotifyLog

    def list_recent(self, limit: int = 100):
        stmt = select(NotifyLog).order_by(NotifyLog.timestamp.desc()).limit(limit)
        return self.session.execute(stmt).scalars().all()
