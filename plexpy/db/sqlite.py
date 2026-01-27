#  This file is part of Tautulli.
#
#  Tautulli is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Tautulli is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Tautulli.  If not, see <http://www.gnu.org/licenses/>.
#
#  Purpose: Provide a SQLite executor wrapper with retries and error handling.

from __future__ import annotations

import logging
import sqlite3
import time
from typing import Any, Callable, Sequence, TypeVar

from plexpy import database
from plexpy.db.errors import TautulliDBError


logger = logging.getLogger(__name__)
T = TypeVar("T")


class SQLiteExecutor:
    """Execute SQLite queries with consistent retries and error wrapping."""

    def __init__(
        self,
        filename: str | None = None,
        max_retries: int = 2,
        retry_delay: float = 1.0,
    ) -> None:
        """Initialize the executor with optional retry configuration.

        Args:
            filename: Optional SQLite database file path.
            max_retries: Number of retry attempts for transient errors.
            retry_delay: Seconds to wait between retry attempts.
        """
        self._db = database.MonitorDatabase(filename=filename)
        self._max_retries = max(0, int(max_retries))
        self._retry_delay = max(0.0, float(retry_delay))

    def action(self, query: str, args: Sequence[Any] | None = None) -> sqlite3.Cursor | None:
        """Execute a write query and return the cursor.

        Args:
            query: SQL statement to execute.
            args: Optional sequence of query arguments.

        Returns:
            The sqlite3 cursor returned by the execution.

        Raises:
            TautulliDBError: If the query execution fails.
        """
        return self._execute(self._db.action, query, args)

    def select(self, query: str, args: Sequence[Any] | None = None) -> list[dict[str, Any]]:
        """Execute a read query and return all rows.

        Args:
            query: SQL statement to execute.
            args: Optional sequence of query arguments.

        Returns:
            A list of row dictionaries.

        Raises:
            TautulliDBError: If the query execution fails.
        """
        return self._execute(self._db.select, query, args)

    def select_single(self, query: str, args: Sequence[Any] | None = None) -> dict[str, Any]:
        """Execute a read query and return a single row.

        Args:
            query: SQL statement to execute.
            args: Optional sequence of query arguments.

        Returns:
            A single row dictionary, or an empty dict if no result.

        Raises:
            TautulliDBError: If the query execution fails.
        """
        return self._execute(self._db.select_single, query, args)

    def close(self) -> None:
        """Close the underlying database connection."""
        self._db.connection.close()

    def _execute(
        self,
        operation: Callable[[str, Sequence[Any] | None], T],
        query: str,
        args: Sequence[Any] | None,
    ) -> T:
        attempts = 0
        while True:
            try:
                return operation(query, args)
            except sqlite3.OperationalError as exc:
                if self._should_retry(exc) and attempts < self._max_retries:
                    attempts += 1
                    logger.debug(
                        "Tautulli DAL :: Retrying database operation (attempt %s/%s).",
                        attempts,
                        self._max_retries,
                    )
                    time.sleep(self._retry_delay)
                    continue
                logger.exception("Tautulli DAL :: Database operation failed: %s", query)
                raise TautulliDBError("Database operation failed.") from exc
            except sqlite3.DatabaseError as exc:
                logger.exception("Tautulli DAL :: Database operation failed: %s", query)
                raise TautulliDBError("Database operation failed.") from exc
            except Exception as exc:
                logger.exception("Tautulli DAL :: Database operation failed: %s", query)
                raise TautulliDBError("Database operation failed.") from exc

    @staticmethod
    def _should_retry(error: sqlite3.OperationalError) -> bool:
        """Determine whether an OperationalError is transient.

        Args:
            error: The OperationalError encountered during execution.

        Returns:
            True if the error should be retried.
        """
        message = str(error).lower()
        return "database is locked" in message or "unable to open database file" in message
