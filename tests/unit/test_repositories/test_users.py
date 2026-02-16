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

"""Tests for UsersRepository."""

import pytest
from unittest.mock import MagicMock, call
from sqlalchemy import select

from plexpy.db.repository.users import UsersRepository, UserLoginRepository
from plexpy.db.models import User, UserLogin
from tests.factories import UserFactory, UserLoginFactory


class TestUsersRepository:
    """Tests for UsersRepository."""

    @pytest.fixture
    def mock_session(self):
        session = MagicMock()
        session.execute = MagicMock()
        return session

    @pytest.fixture
    def repository(self, mock_session):
        return UsersRepository(mock_session)

    def test_get_by_user_id_returns_user(self, repository, mock_session):
        """Test get_by_user_id returns user when found."""
        mock_user = UserFactory.build(user_id=123)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        result = repository.get_by_user_id(123)

        assert result is mock_user
        mock_session.execute.assert_called_once()
        call_args = mock_session.execute.call_args[0][0]
        assert isinstance(call_args, select)

    def test_get_by_user_id_returns_none_when_not_found(self, repository, mock_session):
        """Test get_by_user_id returns None when user not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = repository.get_by_user_id(999)

        assert result is None

    def test_get_by_username_returns_user(self, repository, mock_session):
        """Test get_by_username returns user when found."""
        mock_user = UserFactory.build(username="testuser")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        result = repository.get_by_username("testuser")

        assert result is mock_user

    def test_get_by_username_returns_none_when_not_found(self, repository, mock_session):
        """Test get_by_username returns None when user not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = repository.get_by_username("nonexistent")

        assert result is None

    def test_list_active_returns_active_users(self, repository, mock_session):
        """Test list_active returns only active users."""
        mock_users = [UserFactory.build(is_active=1), UserFactory.build(is_active=1)]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_users
        mock_session.execute.return_value = mock_result

        result = repository.list_active()

        assert len(result) == 2

    def test_get_by_id_returns_user(self, repository, mock_session):
        """Test get_by_id returns user by primary key."""
        mock_user = UserFactory.build(id=1)
        mock_session.get = MagicMock(return_value=mock_user)

        result = repository.get_by_id(1)

        assert result is mock_user

    def test_get_by_id_returns_none_when_not_found(self, repository, mock_session):
        """Test get_by_id returns None when not found."""
        mock_session.get = MagicMock(return_value=None)

        result = repository.get_by_id(999)

        assert result is None

    def test_list_all_returns_all_users(self, repository, mock_session):
        """Test list_all returns all users."""
        mock_users = [UserFactory.build(), UserFactory.build(), UserFactory.build()]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_users
        mock_session.execute.return_value = mock_result

        result = repository.list_all()

        assert len(result) == 3

    def test_first_by_returns_first_matching_user(self, repository, mock_session):
        """Test first_by returns first user matching filters."""
        mock_user = UserFactory.build(username="testuser", is_admin=1)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        result = repository.first_by(username="testuser", is_admin=1)

        assert result is mock_user

    def test_first_by_returns_none_when_not_found(self, repository, mock_session):
        """Test first_by returns None when no match."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = repository.first_by(username="nonexistent")

        assert result is None

    def test_list_by_returns_matching_users(self, repository, mock_session):
        """Test list_by returns all users matching filters."""
        mock_users = [
            UserFactory.build(is_active=1),
            UserFactory.build(is_active=1),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_users
        mock_session.execute.return_value = mock_result

        result = repository.list_by(is_active=1)

        assert len(result) == 2

    def test_count_returns_total_count(self, repository, mock_session):
        """Test count returns total number of users."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 10
        mock_session.execute.return_value = mock_result

        result = repository.count()

        assert result == 10

    def test_count_returns_zero_when_empty(self, repository, mock_session):
        """Test count returns 0 when no users."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result

        result = repository.count()

        assert result == 0

    def test_exists_returns_true_when_user_exists(self, repository, mock_session):
        """Test exists returns True when user exists."""
        mock_user = UserFactory.build()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        result = repository.exists(user_id=123)

        assert result is True

    def test_exists_returns_false_when_user_not_exists(self, repository, mock_session):
        """Test exists returns False when user does not exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = repository.exists(user_id=999)

        assert result is False

    def test_add_adds_user_to_session(self, repository, mock_session):
        """Test add adds user to session."""
        mock_user = UserFactory.build()

        result = repository.add(mock_user)

        mock_session.add.assert_called_once_with(mock_user)
        assert result is mock_user

    def test_add_all_adds_all_users_to_session(self, repository, mock_session):
        """Test add_all adds multiple users to session."""
        mock_users = [UserFactory.build(), UserFactory.build()]

        result = repository.add_all(mock_users)

        mock_session.add_all.assert_called_once_with(mock_users)
        assert result == mock_users

    def test_delete_removes_user_from_session(self, repository, mock_session):
        """Test delete removes user from session."""
        mock_user = UserFactory.build()

        repository.delete(mock_user)

        mock_session.delete.assert_called_once_with(mock_user)

    def test_update_flushes_session(self, repository, mock_session):
        """Test update flushes session and returns instance."""
        mock_user = UserFactory.build()

        result = repository.update(mock_user)

        mock_session.flush.assert_called_once()
        assert result is mock_user


class TestUserLoginRepository:
    """Tests for UserLoginRepository."""

    @pytest.fixture
    def mock_session(self):
        session = MagicMock()
        session.execute = MagicMock()
        return session

    @pytest.fixture
    def repository(self, mock_session):
        return UserLoginRepository(mock_session)

    def test_list_recent_returns_recent_logins(self, repository, mock_session):
        """Test list_recent returns recent login records."""
        mock_logins = [UserLoginFactory.build(), UserLoginFactory.build()]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_logins
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

    def test_get_by_id_returns_login(self, repository, mock_session):
        """Test get_by_id returns login record."""
        mock_login = UserLoginFactory.build(id=1)
        mock_session.get = MagicMock(return_value=mock_login)

        result = repository.get_by_id(1)

        assert result is mock_login

    def test_count_returns_total_count(self, repository, mock_session):
        """Test count returns total number of login records."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 25
        mock_session.execute.return_value = mock_result

        result = repository.count()

        assert result == 25
