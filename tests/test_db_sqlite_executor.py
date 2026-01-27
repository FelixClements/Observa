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
#  Purpose: Validate SQLite executor behavior and error wrapping.

from __future__ import annotations

import pytest

from plexpy.db.errors import TautulliDBError
from plexpy.db.sqlite import SQLiteExecutor


def test_sqlite_executor_select_roundtrip(tmp_path, plexpy_config) -> None:
    db_path = tmp_path / "test.db"
    executor = SQLiteExecutor(filename=str(db_path))
    try:
        executor.action("CREATE TABLE example (id INTEGER PRIMARY KEY, name TEXT)")
        executor.action("INSERT INTO example (name) VALUES (?)", ["Tautulli"])
        result = executor.select_single("SELECT name FROM example WHERE id = 1")
        assert result["name"] == "Tautulli"
    finally:
        executor.close()


def test_sqlite_executor_wraps_errors(tmp_path, plexpy_config) -> None:
    db_path = tmp_path / "test.db"
    executor = SQLiteExecutor(filename=str(db_path))
    try:
        with pytest.raises(TautulliDBError):
            executor.select("SELECT * FROM missing_table")
    finally:
        executor.close()
