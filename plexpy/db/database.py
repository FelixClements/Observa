from __future__ import annotations

import warnings
from typing import Any, Dict, Iterable, Optional, Tuple

from sqlalchemy import MetaData, Table, and_, insert, text
from sqlalchemy.engine import Engine

from plexpy.db.engine import get_engine
from plexpy.db.models import Base


class MonitorDatabase(object):
    """
    DEPRECATED: This class is deprecated. Use repository classes instead.

    Legacy database wrapper for raw SQL execution. This class provides
    backwards compatibility but should not be used for new code.

    Migration guide:
    - Use plexpy.db.repository.users.UserRepository for user queries
    - Use plexpy.db.repository.history.SessionHistoryRepository for history queries
    - Use plexpy.db.repository.notifications.* for notification queries
    - Use plexpy.db.repository.libraries.* for library queries

    Example migration:
        # Old (deprecated):
        from plexpy.db.database import MonitorDatabase
        db = MonitorDatabase()
        db.select("SELECT * FROM users WHERE user_id = ?", [1])

        # New (recommended):
        from plexpy.db.repository.users import UserRepository
        from plexpy.db.session import session_scope

        with session_scope() as db_session:
            repo = UserRepository(session=db_session)
            user = repo.get(1)
    """

    _DEPRECATION_WARNING = (
        "MonitorDatabase is deprecated. Use repository classes instead. "
        "See plexpy.db.repository for available repositories."
    )

    def __init__(self, engine: Optional[Engine] = None):
        warnings.warn(self._DEPRECATION_WARNING, DeprecationWarning, stacklevel=2)
        self.engine = engine or get_engine()
        self._last_insert_id: Optional[int] = None
        self._tables: Dict[str, Table] = {}

    def _bind_params(self, query: str, args: Iterable[Any]) -> Tuple[str, Dict[str, Any]]:
        if not args:
            return query, {}

        params: Dict[str, Any] = {}
        for idx, value in enumerate(args, start=1):
            param_name = f"param_{idx}"
            query = query.replace('?', f":{param_name}", 1)
            params[param_name] = value

        return query, params

    def _get_table(self, table_name: str) -> Table:
        table = self._tables.get(table_name)
        if table is not None:
            return table

        table = Base.metadata.tables.get(table_name)
        if table is None:
            table = Table(table_name, MetaData(), autoload_with=self.engine)

        self._tables[table_name] = table
        return table

    def action(self, query: str, args: Optional[Iterable[Any]] = None):
        if query is None:
            return None

        query, params = self._bind_params(query, args or [])
        with self.engine.begin() as connection:
            return connection.execute(text(query), params)

    def select(self, query: str, args: Optional[Iterable[Any]] = None):
        query, params = self._bind_params(query, args or [])
        with self.engine.connect() as connection:
            result = connection.execute(text(query), params)
            return [dict(row) for row in result.mappings().all()]

    def select_single(self, query: str, args: Optional[Iterable[Any]] = None):
        query, params = self._bind_params(query, args or [])
        with self.engine.connect() as connection:
            result = connection.execute(text(query), params).mappings().first()
            if not result:
                return {}
            return dict(result)

    def upsert(self, table_name: str, value_dict: Dict[str, Any], key_dict: Dict[str, Any]):
        table = self._get_table(table_name)
        key_dict = key_dict or {}
        value_dict = value_dict or {}

        cleaned_keys = {key: value for key, value in key_dict.items() if value is not None}
        insert_values = {**value_dict, **cleaned_keys}
        if not insert_values:
            return 'update'

        pk_columns = list(table.primary_key.columns)

        with self.engine.begin() as connection:
            if cleaned_keys:
                conditions = [table.c[key] == value for key, value in cleaned_keys.items()]
                update_stmt = table.update().where(and_(*conditions)).values(**value_dict)
                update_result = connection.execute(update_stmt)
                if update_result.rowcount and update_result.rowcount > 0:
                    return 'update'

            insert_stmt = insert(table).values(**insert_values)
            if pk_columns:
                insert_stmt = insert_stmt.returning(*pk_columns)
            insert_result = connection.execute(insert_stmt)
            row = insert_result.mappings().first() if insert_result.returns_rows else None

        if row and pk_columns:
            pk_name = pk_columns[0].name
            self._last_insert_id = row.get(pk_name)

        return 'insert'

    def last_insert_id(self) -> Optional[int]:
        return self._last_insert_id
