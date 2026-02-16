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

"""Tests for NotifierRepository and NotifyLogRepository."""

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import select

from plexpy.db.repository.notifications import NotifiersRepository, NotifyLogRepository
from plexpy.db.models import Notifier, NotifyLog
from tests.factories import (
    NotifierFactory,
    NotifyLogFactory,
    EmailNotifierFactory,
    TelegramNotifierFactory,
)


class TestNotifiersRepository:
    """Tests for NotifiersRepository."""

    @pytest.fixture
    def mock_session(self):
        session = MagicMock()
        session.execute = MagicMock()
        return session

    @pytest.fixture
    def repository(self, mock_session):
        return NotifiersRepository(mock_session)

    def test_get_by_agent_id_returns_notifier(self, repository, mock_session):
        """Test get_by_agent_id returns notifier when found."""
        mock_notifier = NotifierFactory.build(agent_id=123)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_notifier
        mock_session.execute.return_value = mock_result

        result = repository.get_by_agent_id(123)

        assert result is mock_notifier

    def test_get_by_agent_id_returns_none_when_not_found(self, repository, mock_session):
        """Test get_by_agent_id returns None when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = repository.get_by_agent_id(999)

        assert result is None

    def test_get_active_returns_active_notifiers(self, repository, mock_session):
        """Test get_active returns all active notifiers."""
        mock_notifiers = [
            EmailNotifierFactory.build(agent_id=1),
            TelegramNotifierFactory.build(agent_id=2),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_notifiers
        mock_session.execute.return_value = mock_result

        result = repository.get_active()

        assert len(result) == 2

    def test_get_by_id_returns_notifier(self, repository, mock_session):
        """Test get_by_id returns notifier by primary key."""
        mock_notifier = NotifierFactory.build(id=1)
        mock_session.get = MagicMock(return_value=mock_notifier)

        result = repository.get_by_id(1)

        assert result is mock_notifier

    def test_get_by_id_returns_none_when_not_found(self, repository, mock_session):
        """Test get_by_id returns None when not found."""
        mock_session.get = MagicMock(return_value=None)

        result = repository.get_by_id(999)

        assert result is None

    def test_list_all_returns_all_notifiers(self, repository, mock_session):
        """Test list_all returns all notifiers."""
        mock_notifiers = [NotifierFactory.build(), NotifierFactory.build()]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_notifiers
        mock_session.execute.return_value = mock_result

        result = repository.list_all()

        assert len(result) == 2

    def test_first_by_returns_first_matching_notifier(self, repository, mock_session):
        """Test first_by returns first notifier matching filters."""
        mock_notifier = NotifierFactory.build(agent_id=1, id=1)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_notifier
        mock_session.execute.return_value = mock_result

        result = repository.first_by(agent_id=1)

        assert result is mock_notifier

    def test_first_by_returns_none_when_not_found(self, repository, mock_session):
        """Test first_by returns None when no match."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = repository.first_by(agent_id=999)

        assert result is None

    def test_list_by_returns_matching_notifiers(self, repository, mock_session):
        """Test list_by returns all notifiers matching filters."""
        mock_notifiers = [
            NotifierFactory.build(agent_id=1),
            NotifierFactory.build(agent_id=1),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_notifiers
        mock_session.execute.return_value = mock_result

        result = repository.list_by(agent_id=1)

        assert len(result) == 2

    def test_count_returns_total_count(self, repository, mock_session):
        """Test count returns total number of notifiers."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_session.execute.return_value = mock_result

        result = repository.count()

        assert result == 5

    def test_count_returns_zero_when_empty(self, repository, mock_session):
        """Test count returns 0 when no notifiers."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result

        result = repository.count()

        assert result == 0

    def test_exists_returns_true_when_notifier_exists(self, repository, mock_session):
        """Test exists returns True when notifier exists."""
        mock_notifier = NotifierFactory.build()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_notifier
        mock_session.execute.return_value = mock_result

        result = repository.exists(agent_id=1)

        assert result is True

    def test_exists_returns_false_when_notifier_not_exists(self, repository, mock_session):
        """Test exists returns False when notifier does not exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = repository.exists(agent_id=999)

        assert result is False

    def test_add_adds_notifier_to_session(self, repository, mock_session):
        """Test add adds notifier to session."""
        mock_notifier = NotifierFactory.build()

        result = repository.add(mock_notifier)

        mock_session.add.assert_called_once_with(mock_notifier)
        assert result is mock_notifier

    def test_add_all_adds_all_notifiers_to_session(self, repository, mock_session):
        """Test add_all adds multiple notifiers to session."""
        mock_notifiers = [NotifierFactory.build(), NotifierFactory.build()]

        result = repository.add_all(mock_notifiers)

        mock_session.add_all.assert_called_once_with(mock_notifiers)
        assert result == mock_notifiers

    def test_delete_removes_notifier_from_session(self, repository, mock_session):
        """Test delete removes notifier from session."""
        mock_notifier = NotifierFactory.build()

        repository.delete(mock_notifier)

        mock_session.delete.assert_called_once_with(mock_notifier)


class TestNotifyLogRepository:
    """Tests for NotifyLogRepository."""

    @pytest.fixture
    def mock_session(self):
        session = MagicMock()
        session.execute = MagicMock()
        return session

    @pytest.fixture
    def repository(self, mock_session):
        return NotifyLogRepository(mock_session)

    def test_list_recent_returns_recent_logs(self, repository, mock_session):
        """Test list_recent returns recent notification logs."""
        mock_logs = [NotifyLogFactory.build(), NotifyLogFactory.build()]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_session.execute.return_value = mock_result

        result = repository.list_recent(limit=50)

        assert len(result) == 2

    def test_list_recent_respects_limit(self, repository, mock_session):
        """Test list_recent respects the limit parameter."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        repository.list_recent(limit=10)

        call_args = mock_session.execute.call_args[0][0]
        assert "LIMIT" in str(call_args)

    def test_get_by_notifier_id_returns_notifier_logs(self, repository, mock_session):
        """Test get_by_notifier_id returns logs for specific notifier."""
        mock_logs = [
            NotifyLogFactory.build(notifier_id=1),
            NotifyLogFactory.build(notifier_id=1),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_session.execute.return_value = mock_result

        result = repository.get_by_notifier_id(1, limit=50)

        assert len(result) == 2

    def test_get_by_notifier_id_respects_limit(self, repository, mock_session):
        """Test get_by_notifier_id respects the limit parameter."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        repository.get_by_notifier_id(1, limit=10)

        call_args = mock_session.execute.call_args[0][0]
        assert "LIMIT" in str(call_args)

    def test_get_by_user_id_returns_user_logs(self, repository, mock_session):
        """Test get_by_user_id returns logs for specific user."""
        mock_logs = [
            NotifyLogFactory.build(user_id=123),
            NotifyLogFactory.build(user_id=123),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_session.execute.return_value = mock_result

        result = repository.get_by_user_id(123, limit=50)

        assert len(result) == 2

    def test_get_by_rating_key_returns_media_logs(self, repository, mock_session):
        """Test get_by_rating_key returns logs for specific media."""
        mock_logs = [
            NotifyLogFactory.build(rating_key=456),
            NotifyLogFactory.build(rating_key=456),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_session.execute.return_value = mock_result

        result = repository.get_by_rating_key(456, limit=50)

        assert len(result) == 2

    def test_count_by_notifier_returns_count(self, repository, mock_session):
        """Test count_by_notifier returns count of logs for notifier."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 100
        mock_session.execute.return_value = mock_result

        result = repository.count_by_notifier(1)

        assert result == 100

    def test_count_by_notifier_returns_zero_when_no_logs(self, repository, mock_session):
        """Test count_by_notifier returns 0 when no logs."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result

        result = repository.count_by_notifier(999)

        assert result == 0

    def test_delete_old_logs_returns_rowcount(self, repository, mock_session):
        """Test delete_old_logs returns number of deleted rows."""
        mock_result = MagicMock()
        mock_result.rowcount = 50
        mock_session.execute.return_value = mock_result

        result = repository.delete_old_logs(1700000000)

        assert result == 50

    def test_delete_old_logs_deletes_correct_logs(self, repository, mock_session):
        """Test delete_old_logs deletes logs older than timestamp."""
        repository.delete_old_logs(1700000000)

        mock_session.execute.assert_called_once()

    def test_get_by_id_returns_log(self, repository, mock_session):
        """Test get_by_id returns log by primary key."""
        mock_log = NotifyLogFactory.build(id=1)
        mock_session.get = MagicMock(return_value=mock_log)

        result = repository.get_by_id(1)

        assert result is mock_log

    def test_get_by_id_returns_none_when_not_found(self, repository, mock_session):
        """Test get_by_id returns None when not found."""
        mock_session.get = MagicMock(return_value=None)

        result = repository.get_by_id(999)

        assert result is None

    def test_list_all_returns_all_logs(self, repository, mock_session):
        """Test list_all returns all notification logs."""
        mock_logs = [NotifyLogFactory.build(), NotifyLogFactory.build()]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_session.execute.return_value = mock_result

        result = repository.list_all()

        assert len(result) == 2

    def test_first_by_returns_first_matching_log(self, repository, mock_session):
        """Test first_by returns first log matching filters."""
        mock_log = NotifyLogFactory.build(notifier_id=1, id=1)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_log
        mock_session.execute.return_value = mock_result

        result = repository.first_by(notifier_id=1)

        assert result is mock_log

    def test_first_by_returns_none_when_not_found(self, repository, mock_session):
        """Test first_by returns None when no match."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = repository.first_by(notifier_id=999)

        assert result is None

    def test_list_by_returns_matching_logs(self, repository, mock_session):
        """Test list_by returns all logs matching filters."""
        mock_logs = [
            NotifyLogFactory.build(notifier_id=1),
            NotifyLogFactory.build(notifier_id=1),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_session.execute.return_value = mock_result

        result = repository.list_by(notifier_id=1)

        assert len(result) == 2

    def test_count_returns_total_count(self, repository, mock_session):
        """Test count returns total number of logs."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 200
        mock_session.execute.return_value = mock_result

        result = repository.count()

        assert result == 200

    def test_exists_returns_true_when_log_exists(self, repository, mock_session):
        """Test exists returns True when log exists."""
        mock_log = NotifyLogFactory.build()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_log
        mock_session.execute.return_value = mock_result

        result = repository.exists(notifier_id=1)

        assert result is True

    def test_exists_returns_false_when_log_not_exists(self, repository, mock_session):
        """Test exists returns False when log does not exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = repository.exists(notifier_id=999)

        assert result is False

    def test_add_adds_log_to_session(self, repository, mock_session):
        """Test add adds log to session."""
        mock_log = NotifyLogFactory.build()

        result = repository.add(mock_log)

        mock_session.add.assert_called_once_with(mock_log)
        assert result is mock_log

    def test_add_all_adds_all_logs_to_session(self, repository, mock_session):
        """Test add_all adds multiple logs to session."""
        mock_logs = [NotifyLogFactory.build(), NotifyLogFactory.build()]

        result = repository.add_all(mock_logs)

        mock_session.add_all.assert_called_once_with(mock_logs)
        assert result == mock_logs
