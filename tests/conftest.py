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
#  Purpose: Provide shared pytest fixtures for database-related tests.

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Generator

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
LIB_ROOT = os.path.join(PROJECT_ROOT, "lib")
for path in (PROJECT_ROOT, LIB_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)


@pytest.fixture
def engine() -> Generator[sqlite3.Connection, None, None]:
    """Provide an in-memory SQLite connection for fast tests."""
    connection = sqlite3.connect(":memory:")
    try:
        yield connection
    finally:
        connection.close()


@pytest.fixture
def plexpy_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Configure minimal plexpy globals needed for database helpers.

    Args:
        tmp_path: Temporary filesystem path.
        monkeypatch: Pytest monkeypatch utility.

    Returns:
        A SimpleNamespace with the required config attributes.
    """
    import plexpy

    config = SimpleNamespace(
        SYNCHRONOUS_MODE="NORMAL",
        JOURNAL_MODE="WAL",
        CACHE_SIZEMB=0,
    )
    monkeypatch.setattr(plexpy, "CONFIG", config, raising=False)
    monkeypatch.setattr(plexpy, "DATA_DIR", str(tmp_path), raising=False)
    return config
