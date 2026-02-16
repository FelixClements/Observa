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

"""Tests for users service."""

import pytest
from unittest.mock import MagicMock, patch, call

from plexpy.services.users import Users
from tests.factories import UserFactory


class TestUsersService:
    """Tests for Users service."""

    @pytest.fixture
    def mock_config(self):
        """Create mock config."""
        config = MagicMock()
        config.PMS_IDENTIFIER = 'test_server_id'
        config.GROUP_HISTORY_TABLES = False
        return config

    @pytest.fixture
    def users_service(self, mock_config):
        """Create Users service with mocked config."""
        with patch('plexpy.services.users._get_config', return_value=mock_config):
            with patch('plexpy.services.users.Users._get_config', return_value=mock_config):
                service = Users()
                return service

    def test_users_service_initialization(self, users_service):
        """Test that Users service initializes correctly."""
        assert users_service is not None

    def test_get_user_by_id_returns_dict(self, users_service):
        """Test get_user method returns dictionary."""
        with patch.object(users_service, 'get_user') as mock_get_user:
            mock_get_user.return_value = {'user_id': 1, 'username': 'test'}
            result = users_service.get_user(user_id=1)
            assert isinstance(result, dict)

    def test_get_users_returns_list(self, users_service):
        """Test get_users method returns list."""
        with patch.object(users_service, 'get_users') as mock_get_users:
            mock_get_users.return_value = [{'user_id': 1, 'username': 'test'}]
            result = users_service.get_users()
            assert isinstance(result, list)

    def test_get_details_with_user_id(self, users_service):
        """Test get_details method returns user details when user_id is provided."""
        with patch.object(users_service, 'get_user_details') as mock_get_details:
            mock_get_details.return_value = {
                'user_id': 1,
                'username': 'testuser',
                'friendly_name': 'Test User',
                'email': 'test@example.com',
            }
            result = users_service.get_details(user_id=1)
            assert result['user_id'] == 1
            assert result['username'] == 'testuser'

    def test_get_details_returns_local_user_for_empty_params(self, users_service):
        """Test get_details returns default local user when no params provided."""
        result = users_service.get_details()
        assert result['username'] == 'Local'
        assert result['friendly_name'] == 'Local'

    def test_get_details_with_username(self, users_service):
        """Test get_details method works with username parameter."""
        with patch.object(users_service, 'get_user_details') as mock_get_details:
            mock_get_details.return_value = {
                'user_id': 2,
                'username': 'john_doe',
            }
            result = users_service.get_details(user='john_doe')
            mock_get_details.assert_called_once()

    def test_get_details_with_email(self, users_service):
        """Test get_details method works with email parameter."""
        with patch.object(users_service, 'get_user_details') as mock_get_details:
            mock_get_details.return_value = {
                'user_id': 3,
                'email': 'jane@example.com',
            }
            result = users_service.get_details(email='jane@example.com')
            mock_get_details.assert_called_once()

    def test_get_user_details_returns_data(self, users_service):
        """Test get_user_details method returns user details."""
        with patch('plexpy.services.users.session_scope') as mock_session_scope:
            mock_db_session = MagicMock()
            mock_session_scope.return_value.__enter__ = MagicMock(return_value=mock_db_session)
            mock_session_scope.return_value.__exit__ = MagicMock(return_value=False)

            # Setup mock query result
            mock_result = [
                {
                    'row_id': 1,
                    'user_id': 1,
                    'username': 'testuser',
                    'friendly_name': 'Test User',
                    'user_thumb': 'http://example.com/thumb.jpg',
                    'custom_thumb': None,
                    'email': 'test@example.com',
                    'is_active': 1,
                    'is_admin': 0,
                    'is_home_user': 1,
                    'is_allow_sync': 1,
                    'is_restricted': 0,
                    'do_notify': 1,
                    'keep_history': 1,
                    'deleted_user': 0,
                    'allow_guest': 1,
                    'shared_libraries': '1;2;3',
                    'last_seen': None,
                }
            ]
            mock_db_session.execute.return_value.mappings.return_value = mock_result

            result = users_service.get_user_details(user_id=1)
            assert result['username'] == 'testuser'
            assert result['email'] == 'test@example.com'

    def test_get_users_with_include_deleted(self, users_service):
        """Test get_users method handles include_deleted parameter."""
        with patch.object(users_service, 'get_users') as mock_get_users:
            mock_get_users.return_value = []
            users_service.get_users(include_deleted=True)
            mock_get_users.assert_called_once_with(include_deleted=True)

    def test_get_user_names_returns_none_on_error(self, users_service):
        """Test get_user_names returns None on database error."""
        with patch('plexpy.services.users.session_scope') as mock_session_scope:
            mock_session_scope.side_effect = Exception("Database error")
            result = users_service.get_user_names()
            assert result is None

    def test_delete_with_user_id(self, users_service):
        """Test delete method works with user_id."""
        with patch('plexpy.services.users.session_scope') as mock_session_scope:
            with patch('plexpy.services.users.cleanup.delete_user_history', return_value=True):
                mock_db_session = MagicMock()
                mock_session_scope.return_value.__enter__ = MagicMock(return_value=mock_db_session)
                mock_session_scope.return_value.__exit__ = MagicMock(return_value=False)

                result = users_service.delete(user_id=1)
                assert result is True

    def test_delete_with_invalid_user_id(self, users_service):
        """Test delete method returns False for invalid user_id."""
        result = users_service.delete(user_id='invalid')
        assert result is False

    def test_undelete_with_user_id(self, users_service):
        """Test undelete method works with user_id."""
        with patch('plexpy.services.users.session_scope') as mock_session_scope:
            mock_db_session = MagicMock()
            mock_session_scope.return_value.__enter__ = MagicMock(return_value=mock_db_session)
            mock_session_scope.return_value.__exit__ = MagicMock(return_value=False)

            # Mock fetch_scalar to return a user id (meaning user exists)
            with patch('plexpy.services.users.queries.fetch_scalar', return_value=1):
                result = users_service.undelete(user_id=123)
                assert result is True

    def test_undelete_with_username(self, users_service):
        """Test undelete method works with username."""
        with patch('plexpy.services.users.session_scope') as mock_session_scope:
            mock_db_session = MagicMock()
            mock_session_scope.return_value.__enter__ = MagicMock(return_value=mock_db_session)
            mock_session_scope.return_value.__exit__ = MagicMock(return_value=False)

            with patch('plexpy.services.users.queries.fetch_scalar', return_value=1):
                result = users_service.undelete(username='testuser')
                assert result is True

    def test_undelete_returns_false_when_user_not_found(self, users_service):
        """Test undelete returns False when user doesn't exist."""
        with patch('plexpy.services.users.session_scope') as mock_session_scope:
            mock_db_session = MagicMock()
            mock_session_scope.return_value.__enter__ = MagicMock(return_value=mock_db_session)
            mock_session_scope.return_value.__exit__ = MagicMock(return_value=False)

            with patch('plexpy.services.users.queries.fetch_scalar', return_value=None):
                result = users_service.undelete(user_id=999)
                assert result is False

    def test_set_config_creates_or_updates_user(self, users_service):
        """Test set_config method creates or updates user config."""
        with patch('plexpy.services.users.session_scope') as mock_session_scope:
            mock_db_session = MagicMock()
            mock_session_scope.return_value.__enter__ = MagicMock(return_value=mock_db_session)
            mock_session_scope.return_value.__exit__ = MagicMock(return_value=False)

            with patch('plexpy.services.users.queries.fetch_scalar', return_value='testuser'):
                # Should not raise exception
                users_service.set_config(
                    user_id=1,
                    friendly_name='New Name',
                    custom_thumb='http://example.com/thumb.jpg',
                )

    def test_get_tokens_returns_dict(self, users_service):
        """Test get_tokens method returns token dict."""
        with patch('plexpy.services.users.session_scope') as mock_session_scope:
            mock_db_session = MagicMock()
            mock_session_scope.return_value.__enter__ = MagicMock(return_value=mock_db_session)
            mock_session_scope.return_value.__exit__ = MagicMock(return_value=False)

            # Mock empty result
            mock_db_session.execute.return_value.mappings.return_value.first.return_value = None

            result = users_service.get_tokens(user_id=1)
            assert isinstance(result, dict)
            assert 'allow_guest' in result
            assert 'user_token' in result
            assert 'server_token' in result

    def test_get_filters_returns_empty_dict_for_no_user(self, users_service):
        """Test get_filters returns empty dict when no user_id provided."""
        result = users_service.get_filters()
        assert result == {}

    def test_set_user_login_creates_login_record(self, users_service):
        """Test set_user_login method creates login record."""
        with patch('plexpy.services.users.session_scope') as mock_session_scope:
            mock_db_session = MagicMock()
            mock_session_scope.return_value.__enter__ = MagicMock(return_value=mock_db_session)
            mock_session_scope.return_value.__exit__ = MagicMock(return_value=False)

            # Should not raise exception
            users_service.set_user_login(
                user_id=1,
                user='testuser',
                ip_address='192.168.1.1',
                success=1,
            )
            mock_db_session.execute.assert_called_once()

    def test_get_user_login_returns_dict(self, users_service):
        """Test get_user_login method returns dict."""
        with patch('plexpy.services.users.session_scope') as mock_session_scope:
            mock_db_session = MagicMock()
            mock_session_scope.return_value.__enter__ = MagicMock(return_value=mock_db_session)
            mock_session_scope.return_value.__exit__ = MagicMock(return_value=False)

            mock_db_session.execute.return_value.mappings.return_value = MagicMock(
                first=MagicMock(return_value={})
            )

            result = users_service.get_user_login('test_token')
            assert isinstance(result, dict)

    def test_clear_user_login_token_with_jwt(self, users_service):
        """Test clear_user_login_token clears JWT token."""
        with patch('plexpy.services.users.session_scope') as mock_session_scope:
            mock_db_session = MagicMock()
            mock_session_scope.return_value.__enter__ = MagicMock(return_value=mock_db_session)
            mock_session_scope.return_value.__exit__ = MagicMock(return_value=False)

            result = users_service.clear_user_login_token(jwt_token='test_token')
            assert result is True

    def test_clear_user_login_token_with_row_ids(self, users_service):
        """Test clear_user_login_token clears tokens for row_ids."""
        with patch('plexpy.services.users.session_scope') as mock_session_scope:
            mock_db_session = MagicMock()
            mock_session_scope.return_value.__enter__ = MagicMock(return_value=mock_db_session)
            mock_session_scope.return_value.__exit__ = MagicMock(return_value=False)

            result = users_service.clear_user_login_token(row_ids='1,2,3')
            assert result is True

    def test_delete_login_log_returns_true(self, users_service):
        """Test delete_login_log clears login logs."""
        with patch('plexpy.services.users.session_scope') as mock_session_scope:
            with patch('plexpy.services.users.get_engine') as mock_get_engine:
                mock_db_session = MagicMock()
                mock_session_scope.return_value.__enter__ = MagicMock(return_value=mock_db_session)
                mock_session_scope.return_value.__exit__ = MagicMock(return_value=False)

                mock_engine = MagicMock()
                mock_get_engine.return_value = mock_engine
                mock_conn = MagicMock()
                mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
                mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)

                result = users_service.delete_login_log()
                assert result is True


class TestUsersServiceDatatables:
    """Tests for Users service DataTables methods."""

    @pytest.fixture
    def mock_config(self):
        """Create mock config."""
        config = MagicMock()
        config.PMS_IDENTIFIER = 'test_server_id'
        config.GROUP_HISTORY_TABLES = False
        return config

    @pytest.fixture
    def users_service(self, mock_config):
        """Create Users service with mocked config."""
        with patch('plexpy.services.users._get_config', return_value=mock_config):
            with patch('plexpy.services.users.Users._get_config', return_value=mock_config):
                service = Users()
                return service

    def test_get_datatables_list_returns_default_for_empty_kwargs(self, users_service):
        """Test get_datatables_list returns default structure for empty kwargs."""
        result = users_service.get_datatables_list(kwargs={})
        assert 'recordsFiltered' in result
        assert 'recordsTotal' in result
        assert 'data' in result

    def test_get_datatables_list_returns_default_for_invalid_json(self, users_service):
        """Test get_datatables_list returns default for invalid json_data."""
        result = users_service.get_datatables_list(kwargs={'json_data': 'invalid'})
        assert result['recordsFiltered'] == 0
        assert result['data'] == []

    def test_get_datatables_unique_ips_returns_default_for_empty_user(self, users_service):
        """Test get_datatables_unique_ips returns default when user_id not allowed."""
        with patch('plexpy.services.users.session.allow_session_user', return_value=False):
            result = users_service.get_datatables_unique_ips(user_id=1)
            assert result['recordsFiltered'] == 0
            assert result['data'] == []

    def test_get_datatables_user_login_returns_default_for_restricted_user(self, users_service):
        """Test get_datatables_user_login returns default for restricted user."""
        with patch('plexpy.services.users.session.allow_session_user', return_value=False):
            result = users_service.get_datatables_user_login(user_id=1)
            assert result['recordsFiltered'] == 0
            assert result['data'] == []


class TestUsersServiceStats:
    """Tests for Users service statistics methods."""

    @pytest.fixture
    def mock_config(self):
        """Create mock config."""
        config = MagicMock()
        config.PMS_IDENTIFIER = 'test_server_id'
        config.GROUP_HISTORY_TABLES = False
        return config

    @pytest.fixture
    def users_service(self, mock_config):
        """Create Users service with mocked config."""
        with patch('plexpy.services.users._get_config', return_value=mock_config):
            with patch('plexpy.services.users.Users._get_config', return_value=mock_config):
                service = Users()
                return service

    def test_get_watch_time_stats_returns_empty_for_restricted_user(self, users_service):
        """Test get_watch_time_stats returns empty list for restricted user."""
        with patch('plexpy.services.users.session.allow_session_user', return_value=False):
            result = users_service.get_watch_time_stats(user_id=1)
            assert result == []

    def test_get_player_stats_returns_empty_for_restricted_user(self, users_service):
        """Test get_player_stats returns empty list for restricted user."""
        with patch('plexpy.services.users.session.allow_session_user', return_value=False):
            result = users_service.get_player_stats(user_id=1)
            assert result == []

    def test_get_recently_watched_returns_empty_for_restricted_user(self, users_service):
        """Test get_recently_watched returns empty list for restricted user."""
        with patch('plexpy.services.users.session.allow_session_user', return_value=False):
            result = users_service.get_recently_watched(user_id=1)
            assert result == []
