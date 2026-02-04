from __future__ import annotations

from typing import Any, Dict, Iterable, Optional, Sequence, Tuple

from sqlalchemy import text

from plexpy.db import datatables
from plexpy.db.session import session_scope


def _bind_params(query: str, args: Iterable[Any]) -> Tuple[str, Dict[str, Any]]:
    if not args:
        return query, {}

    params: Dict[str, Any] = {}
    for idx, value in enumerate(args, start=1):
        param_name = f"param_{idx}"
        query = query.replace('?', f":{param_name}", 1)
        params[param_name] = value

    return query, params


def fetch_total_duration(custom_where: Optional[Sequence] = None) -> int:
    where, args = datatables.build_custom_where(custom_where=custom_where)
    query = (
        "SELECT SUM(CASE WHEN stopped > 0 THEN (stopped - started) ELSE 0 END) - "
        "SUM(CASE WHEN paused_counter IS NULL THEN 0 ELSE paused_counter END) AS total_duration "
        "FROM session_history "
        "JOIN session_history_metadata ON session_history_metadata.id = session_history.id "
        "JOIN session_history_media_info ON session_history_media_info.id = session_history.id "
        "%s " % where
    )
    query, params = _bind_params(query, args)

    with session_scope() as db_session:
        row = db_session.execute(text(query), params).mappings().first()

    return row['total_duration'] if row else 0
