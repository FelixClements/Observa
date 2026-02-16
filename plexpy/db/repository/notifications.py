from typing import Optional, Sequence

from sqlalchemy import select, func

from plexpy.db.models import Notifier, NotifyLog
from plexpy.db.repository.base import Repository


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
