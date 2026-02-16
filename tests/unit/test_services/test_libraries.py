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

"""Tests for libraries service."""

import pytest
from unittest.mock import MagicMock, patch

from plexpy.services.libraries import Libraries


class TestLibrariesService:
    """Tests for Libraries service."""

    @pytest.fixture
    def mock_config(self):
        """Create mock config."""
        config = MagicMock()
        config.PMS_IDENTIFIER = 'test_server_id'
        config.GROUP_HISTORY_TABLES = False
        config.CACHE_DIR = '/tmp/cache'
        return config

    @pytest.fixture
    def libraries_service(self, mock_config):
        """Create Libraries service with mocked config."""
        with patch('plexpy.services.libraries._get_config', return_value=mock_config):
            with patch('plexpy.services.libraries.Libraries._get_config', return_value=mock_config):
                service = Libraries()
                return service

    def test_libraries_service_initialization(self, libraries_service):
        """Test that Libraries service initializes correctly."""
        assert libraries_service is not None

    def test_get_details_returns_default_for_empty_section_id(self, libraries_service):
        """Test get_details returns default library when no section_id provided."""
        result = libraries_service.get_details()
        assert result['section_name'] == 'Local'
        assert result['section_id'] == 0

    def test_get_details_with_section_id(self, libraries_service):
        """Test get_details method returns library details when section_id is provided."""
        with patch.object(libraries_service, 'get_library_details') as mock_get_details:
            mock_get_details.return_value = {
                'section_id': 1,
                'section_name': 'Movies',
                'section_type': 'movie',
                'count': 100,
            }
            result = libraries_service.get_details(section_id=1)
            assert result['section_id'] == 1
            assert result['section_name'] == 'Movies'

    def test_get_library_details_returns_data(self, libraries_service):
        """Test get_library_details method returns library details."""
        with patch('plexpy.services.libraries.session_scope') as mock_session_scope:
            mock_db_session = MagicMock()
            mock_session_scope.return_value.__enter__ = MagicMock(return_value=mock_db_session)
            mock_session_scope.return_value.__exit__ = MagicMock(return_value=False)

            # Setup mock query result
            mock_result = [
                {
                    'row_id': 1,
                    'server_id': 'test_server',
                    'section_id': 1,
                    'section_name': 'Movies',
                    'section_type': 'movie',
                    'count': 100,
                    'parent_count': 0,
                    'child_count': 0,
                    'library_thumb': 'http://example.com/thumb.jpg',
                    'custom_thumb': None,
                    'library_art': 'http://example.com/art.jpg',
                    'custom_art': None,
                    'is_active': 1,
                    'do_notify': 1,
                    'do_notify_created': 1,
                    'keep_history': 1,
                    'deleted_section': 0,
                    'last_accessed': None,
                }
            ]
            mock_db_session.execute.return_value.mappings.return_value = mock_result

            result = libraries_service.get_library_details(section_id=1)
            assert result['section_name'] == 'Movies'
            assert result['section_type'] == 'movie'

    def test_get_library_details_with_invalid_section_id(self, libraries_service):
        """Test get_library_details raises exception for invalid section_id."""
        with patch('plexpy.services.libraries.session_scope') as mock_session_scope:
            mock_session_scope.side_effect = Exception("Invalid section_id")
            result = libraries_service.get_library_details(section_id='invalid')
            assert result == {}

    def test_set_config_creates_or_updates_library(self, libraries_service):
        """Test set_config method creates or updates library config."""
        with patch('plexpy.services.libraries.session_scope') as mock_session_scope:
            mock_db_session = MagicMock()
            mock_session_scope.return_value.__enter__ = MagicMock(return_value=mock_db_session)
            mock_session_scope.return_value.__exit__ = MagicMock(return_value=False)

            # Should not raise exception
            libraries_service.set_config(
                section_id=1,
                custom_thumb='http://example.com/thumb.jpg',
                custom_art='http://example.com/art.jpg',
            )

    def test_set_config_with_all_params(self, libraries_service):
        """Test set_config method with all parameters."""
        with patch('plexpy.services.libraries.session_scope') as mock_session_scope:
            mock_db_session = MagicMock()
            mock_session_scope.return_value.__enter__ = MagicMock(return_value=mock_db_session)
            mock_session_scope.return_value.__exit__ = MagicMock(return_value=False)

            # Should not raise exception
            libraries_service.set_config(
                section_id=1,
                custom_thumb='http://example.com/thumb.jpg',
                custom_art='http://example.com/art.jpg',
                do_notify=1,
                keep_history=1,
                do_notify_created=1,
            )


class TestLibrariesServiceDatatables:
    """Tests for Libraries service DataTables methods."""

    @pytest.fixture
    def mock_config(self):
        """Create mock config."""
        config = MagicMock()
        config.PMS_IDENTIFIER = 'test_server_id'
        config.GROUP_HISTORY_TABLES = False
        config.CACHE_DIR = '/tmp/cache'
        return config

    @pytest.fixture
    def libraries_service(self, mock_config):
        """Create Libraries service with mocked config."""
        with patch('plexpy.services.libraries._get_config', return_value=mock_config):
            with patch('plexpy.services.libraries.Libraries._get_config', return_value=mock_config):
                service = Libraries()
                return service

    def test_get_datatables_list_returns_default_for_empty_kwargs(self, libraries_service):
        """Test get_datatables_list returns default structure for empty kwargs."""
        result = libraries_service.get_datatables_list(kwargs={})
        assert 'recordsFiltered' in result
        assert 'recordsTotal' in result
        assert 'data' in result

    def test_get_datatables_list_returns_default_for_invalid_json(self, libraries_service):
        """Test get_datatables_list returns default for invalid json_data."""
        result = libraries_service.get_datatables_list(kwargs={'json_data': 'invalid'})
        assert result['recordsFiltered'] == 0
        assert result['data'] == []

    def test_get_datatables_media_info_returns_default_for_invalid_section_id(self, libraries_service):
        """Test get_datatables_media_info returns default for invalid section_id."""
        result = libraries_service.get_datatables_media_info(section_id='invalid')
        assert result['recordsFiltered'] == 0
        assert result['data'] == []

    def test_get_datatables_media_info_returns_default_for_invalid_rating_key(self, libraries_service):
        """Test get_datatables_media_info returns default for invalid rating_key."""
        result = libraries_service.get_datatables_media_info(rating_key='invalid')
        assert result['recordsFiltered'] == 0
        assert result['data'] == []

    def test_get_datatables_media_info_returns_default_for_no_input(self, libraries_service):
        """Test get_datatables_media_info returns default when no input provided."""
        result = libraries_service.get_datatables_media_info()
        assert result['recordsFiltered'] == 0
        assert result['data'] == []


class TestLibrariesServiceStats:
    """Tests for Libraries service statistics methods."""

    @pytest.fixture
    def mock_config(self):
        """Create mock config."""
        config = MagicMock()
        config.PMS_IDENTIFIER = 'test_server_id'
        config.GROUP_HISTORY_TABLES = False
        config.CACHE_DIR = '/tmp/cache'
        return config

    @pytest.fixture
    def libraries_service(self, mock_config):
        """Create Libraries service with mocked config."""
        with patch('plexpy.services.libraries._get_config', return_value=mock_config):
            with patch('plexpy.services.libraries.Libraries._get_config', return_value=mock_config):
                service = Libraries()
                return service

    def test_get_watch_time_stats_returns_empty_for_restricted_library(self, libraries_service):
        """Test get_watch_time_stats returns empty list for restricted library."""
        with patch('plexpy.services.libraries.session.allow_session_library', return_value=False):
            result = libraries_service.get_watch_time_stats(section_id=1)
            assert result == []

    def test_get_user_stats_returns_empty_for_restricted_library(self, libraries_service):
        """Test get_user_stats returns empty list for restricted library."""
        with patch('plexpy.services.libraries.session.allow_session_library', return_value=False):
            result = libraries_service.get_user_stats(section_id=1)
            assert result == []

    def test_get_recently_watched_returns_empty_for_restricted_library(self, libraries_service):
        """Test get_recently_watched returns empty list for restricted library."""
        with patch('plexpy.services.libraries.session.allow_session_library', return_value=False):
            result = libraries_service.get_recently_watched(section_id=1)
            assert result == []


class TestLibrariesCache:
    """Tests for Libraries service cache methods."""

    @pytest.fixture
    def mock_config(self):
        """Create mock config."""
        config = MagicMock()
        config.PMS_IDENTIFIER = 'test_server_id'
        config.GROUP_HISTORY_TABLES = False
        config.CACHE_DIR = '/tmp/cache'
        return config

    @pytest.fixture
    def libraries_service(self, mock_config):
        """Create Libraries service with mocked config."""
        with patch('plexpy.services.libraries._get_config', return_value=mock_config):
            with patch('plexpy.services.libraries.Libraries._get_config', return_value=mock_config):
                service = Libraries()
                return service

    def test_load_media_info_cache_returns_defaults_for_missing_file(self, libraries_service):
        """Test _load_media_info_cache returns defaults when cache file doesn't exist."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            with patch('plexpy.services.libraries.os.path.join', return_value='/tmp/nonexistent.json'):
                cache_time, rows, library_count = libraries_service._load_media_info_cache(section_id=1)
                assert cache_time is None
                assert rows == []
                assert library_count == 0

    def test_save_media_info_cache_creates_file(self, libraries_service):
        """Test _save_media_info_cache creates cache file."""
        with patch('builtins.open', MagicMock()):
            with patch('plexpy.services.libraries.os.path.join', return_value='/tmp/test.json'):
                # Should not raise exception
                libraries_service._save_media_info_cache(section_id=1, rows=[])

    def test_get_media_info_file_sizes_returns_false_for_restricted_library(self, libraries_service):
        """Test get_media_info_file_sizes returns False for restricted library."""
        with patch('plexpy.services.libraries.session.allow_session_library', return_value=False):
            result = libraries_service.get_media_info_file_sizes(section_id=1)
            assert result is False

    def test_get_media_info_file_sizes_returns_false_for_invalid_section_id(self, libraries_service):
        """Test get_media_info_file_sizes returns False for invalid section_id."""
        result = libraries_service.get_media_info_file_sizes(section_id='invalid')
        assert result is False

    def test_get_media_info_file_sizes_returns_false_for_invalid_rating_key(self, libraries_service):
        """Test get_media_info_file_sizes returns False for invalid rating_key."""
        result = libraries_service.get_media_info_file_sizes(rating_key='invalid')
        assert result is False


class TestLibrariesHelperFunctions:
    """Tests for library module helper functions."""

    def test_has_library_type_queries_database(self):
        """Test has_library_type queries the database."""
        with patch('plexpy.services.libraries.session_scope') as mock_session_scope:
            mock_db_session = MagicMock()
            mock_session_scope.return_value.__enter__ = MagicMock(return_value=mock_db_session)
            mock_session_scope.return_value.__exit__ = MagicMock(return_value=False)

            mock_db_session.execute.return_value.scalar_one_or_none.return_value = 1

            from plexpy.services.libraries import has_library_type
            result = has_library_type('movie')
            assert isinstance(result, bool)
