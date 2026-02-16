# This file is part of Observa.
#
#  Observa is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Observa is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Observa.  If not, see <http://www.gnu.org/licenses/>.

import os
import pytest
from unittest.mock import MagicMock, AsyncMock

os.environ.setdefault('TAUTULLI_CONFIG', '/dev/null')


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.DB_HOST = 'localhost'
    config.DB_PORT = 5432
    config.DB_NAME = 'tautulli'
    config.DB_USER = 'tautulli'
    config.DB_PASSWORD = ''
    config.DB_SSLMODE = 'prefer'
    config.DB_POOL_SIZE = 5
    config.DB_MAX_OVERFLOW = 10
    config.DB_POOL_TIMEOUT = 30
    return config


@pytest.fixture
def mock_engine():
    engine = MagicMock()
    engine.connect.return_value.__enter__ = MagicMock(return_value=MagicMock())
    engine.connect.return_value.__exit__ = MagicMock(return_value=False)
    return engine


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.execute = MagicMock(return_value=MagicMock(mappings=MagicMock(return_value=[])))
    return session
