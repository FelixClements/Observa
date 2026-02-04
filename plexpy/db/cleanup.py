from typing import Iterable, List, Optional

from sqlalchemy import delete, select

from plexpy.db.models import (
    RecentlyAdded,
    Session,
    SessionHistory,
    SessionHistoryMediaInfo,
    SessionHistoryMetadata,
)
from plexpy.db.session import session_scope
from plexpy.util import helpers


def delete_sessions() -> bool:
    with session_scope() as session:
        session.execute(delete(Session))
    return True


def delete_recently_added() -> bool:
    with session_scope() as session:
        session.execute(delete(RecentlyAdded))
    return True


def delete_session_history_rows(row_ids: Optional[Iterable[int]] = None) -> bool:
    if row_ids and isinstance(row_ids, str):
        row_ids = list(map(helpers.cast_to_int, row_ids.split(',')))

    if not row_ids:
        return True

    clean_ids: List[int] = [row_id for row_id in row_ids if row_id is not None]
    if not clean_ids:
        return True

    with session_scope() as session:
        session.execute(
            delete(SessionHistoryMediaInfo).where(SessionHistoryMediaInfo.id.in_(clean_ids))
        )
        session.execute(
            delete(SessionHistoryMetadata).where(SessionHistoryMetadata.id.in_(clean_ids))
        )
        session.execute(
            delete(SessionHistory).where(SessionHistory.id.in_(clean_ids))
        )

    return True


def delete_user_history(user_id: Optional[int] = None) -> bool:
    if not str(user_id).isdigit():
        return False

    with session_scope() as session:
        stmt = select(SessionHistory.id).where(SessionHistory.user_id == int(user_id))
        row_ids = [row.id for row in session.execute(stmt).all()]

    return delete_session_history_rows(row_ids=row_ids)


def delete_library_history(section_id: Optional[int] = None) -> bool:
    if not str(section_id).isdigit():
        return False

    with session_scope() as session:
        stmt = select(SessionHistory.id).where(SessionHistory.section_id == int(section_id))
        row_ids = [row.id for row in session.execute(stmt).all()]

    return delete_session_history_rows(row_ids=row_ids)
