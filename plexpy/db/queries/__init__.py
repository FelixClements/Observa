from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from plexpy.util import logger


def fetch_mappings(session: Session, stmt: Select) -> list[dict[str, Any]]:
    return [dict(row) for row in session.execute(stmt).mappings().all()]


def fetch_mapping(
    session: Session,
    stmt: Select,
    default: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    row = session.execute(stmt).mappings().first()
    if row is None:
        return dict(default or {})
    return dict(row)


def fetch_scalar(session: Session, stmt: Select, default: Any = None) -> Any:
    value = session.execute(stmt).scalar_one_or_none()
    if value is None:
        return default
    return value


def apply_pagination(
    stmt: Select,
    start: Optional[int] = None,
    length: Optional[int] = None,
) -> Select:
    if start is not None:
        stmt = stmt.offset(start)
    if length is not None:
        stmt = stmt.limit(length)
    return stmt


def log_query_failure(message: str, exc: Exception) -> None:
    logger.warn("%s: %s.", message, exc)
