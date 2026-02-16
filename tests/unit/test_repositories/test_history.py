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

"""Tests for SessionHistoryRepository."""

import pytest
from unittest.mock import MagicMock
from sqlalchemy import select, func

from plexpy.db.repository.history import (
    SessionHistoryRepository,
    SessionHistoryMetadataRepository,
    SessionHistoryMediaInfoRepository,
)
from plexpy.db.models import SessionHistory, SessionHistoryMetadata, SessionHistoryMediaInfo
from tests.factories import (
    SessionHistoryFactory,
    SessionHistoryMetadataFactory,
    SessionHistoryMediaInfoFactory,
)


class TestSessionHistoryRepository:
    """Tests for SessionHistoryRepository."""

    @pytest.fixture
    def mock_session(self):
        session = MagicMock()
        session.execute = MagicMock()
        return session

    @pytest.fixture
    def repository(self, mock_session):
        return SessionHistoryRepository(mock_session)

    def test_get_by_reference_id_returns_history(self, repository, mock_session):
        """Test get_by_reference_id returns history when found."""
        mock_history = SessionHistoryFactory.build(reference_id=123)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_history
        mock_session.execute.return_value = mock_result

        result = repository.get_by_reference_id(123)

        assert result is mock_history

    def test_get_by_reference_id_returns_none_when_not_found(self, repository, mock_session):
        """Test get_by_reference_id returns None when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = repository.get_by_reference_id(999)

        assert result is None

    def test_list_recent_returns_recent_history(self, repository, mock_session):
        """Test list_recent returns recent history records."""
        mock_history = [SessionHistoryFactory.build(), SessionHistoryFactory.build()]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_history
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

    def test_get_by_user_id_returns_user_history(self, repository, mock_session):
        """Test get_by_user_id returns history for specific user."""
        mock_history = [
            SessionHistoryFactory.build(user_id=123),
            SessionHistoryFactory.build(user_id=123),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_history
        mock_session.execute.return_value = mock_result

        result = repository.get_by_user_id(123, limit=50)

        assert len(result) == 2

    def test_get_by_media_type_returns_filtered_history(self, repository, mock_session):
        """Test get_by_media_type returns history for specific media type."""
        mock_history = [
            SessionHistoryFactory.build(media_type="movie"),
            SessionHistoryFactory.build(media_type="movie"),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_history
        mock_session.execute.return_value = mock_result

        result = repository.get_by_media_type("movie", limit=50)

        assert len(result) == 2

    def test_get_total_duration_by_user_returns_duration(self, repository, mock_session):
        """Test get_total_duration_by_user returns total watch time."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 3600
        mock_session.execute.return_value = mock_result

        result = repository.get_total_duration_by_user(123)

        assert result == 3600

    def test_get_total_duration_by_user_returns_zero_when_null(self, repository, mock_session):
        """Test get_total_duration_by_user returns 0 when result is None."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result

        result = repository.get_total_duration_by_user(123)

        assert result == 0

    def test_get_total_duration_by_library_returns_duration(self, repository, mock_session):
        """Test get_total_duration_by_library returns total watch time."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 7200
        mock_session.execute.return_value = mock_result

        result = repository.get_total_duration_by_library(1)

        assert result == 7200

    def test_get_total_duration_by_media_type_returns_duration(self, repository, mock_session):
        """Test get_total_duration_by_media_type returns total watch time."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1800
        mock_session.execute.return_value = mock_result

        result = repository.get_total_duration_by_media_type("movie")

        assert result == 1800

    def test_count_by_user_returns_count(self, repository, mock_session):
        """Test count_by_user returns count of history for user."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 50
        mock_session.execute.return_value = mock_result

        result = repository.count_by_user(123)

        assert result == 50

    def test_count_by_media_type_returns_count(self, repository, mock_session):
        """Test count_by_media_type returns count of history for media type."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 100
        mock_session.execute.return_value = mock_result

        result = repository.count_by_media_type("movie")

        assert result == 100

    def test_count_by_user_and_media_type_returns_count(self, repository, mock_session):
        """Test count_by_user_and_media_type returns combined count."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 25
        mock_session.execute.return_value = mock_result

        result = repository.count_by_user_and_media_type(123, "movie")

        assert result == 25

    def test_get_distinct_users_returns_user_ids(self, repository, mock_session):
        """Test get_distinct_users returns unique user IDs."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [1, 2, 3]
        mock_session.execute.return_value = mock_result

        result = repository.get_distinct_users()

        assert result == [1, 2, 3]

    def test_get_distinct_media_types_returns_types(self, repository, mock_session):
        """Test get_distinct_media_types returns unique media types."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = ["movie", "episode", "track"]
        mock_session.execute.return_value = mock_result

        result = repository.get_distinct_media_types()

        assert result == ["movie", "episode", "track"]

    def test_get_distinct_libraries_returns_section_ids(self, repository, mock_session):
        """Test get_distinct_libraries returns unique library IDs."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [1, 2, 5]
        mock_session.execute.return_value = mock_result

        result = repository.get_distinct_libraries()

        assert result == [1, 2, 5]

    def test_get_distinct_platforms_returns_platforms(self, repository, mock_session):
        """Test get_distinct_platforms returns unique platforms."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = ["Windows", "Android", "iOS"]
        mock_session.execute.return_value = mock_result

        result = repository.get_distinct_platforms()

        assert result == ["Windows", "Android", "iOS"]

    def test_get_by_id_returns_history(self, repository, mock_session):
        """Test get_by_id returns history by primary key."""
        mock_history = SessionHistoryFactory.build(id=1)
        mock_session.get = MagicMock(return_value=mock_history)

        result = repository.get_by_id(1)

        assert result is mock_history

    def test_list_all_returns_all_history(self, repository, mock_session):
        """Test list_all returns all history records."""
        mock_history = [SessionHistoryFactory.build(), SessionHistoryFactory.build()]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_history
        mock_session.execute.return_value = mock_result

        result = repository.list_all()

        assert len(result) == 2

    def test_exists_returns_true_when_exists(self, repository, mock_session):
        """Test exists returns True when history exists."""
        mock_history = SessionHistoryFactory.build()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_history
        mock_session.execute.return_value = mock_result

        result = repository.exists(reference_id=123)

        assert result is True

    def test_exists_returns_false_when_not_exists(self, repository, mock_session):
        """Test exists returns False when history does not exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = repository.exists(reference_id=999)

        assert result is False


class TestSessionHistoryMetadataRepository:
    """Tests for SessionHistoryMetadataRepository."""

    @pytest.fixture
    def mock_session(self):
        session = MagicMock()
        session.execute = MagicMock()
        return session

    @pytest.fixture
    def repository(self, mock_session):
        return SessionHistoryMetadataRepository(mock_session)

    def test_get_by_rating_key_returns_metadata(self, repository, mock_session):
        """Test get_by_rating_key returns metadata when found."""
        mock_metadata = SessionHistoryMetadataFactory.build(rating_key=123)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_metadata
        mock_session.execute.return_value = mock_result

        result = repository.get_by_rating_key(123)

        assert result is mock_metadata

    def test_get_by_rating_key_returns_none_when_not_found(self, repository, mock_session):
        """Test get_by_rating_key returns None when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = repository.get_by_rating_key(999)

        assert result is None

    def test_get_by_grandparent_rating_key_returns_metadata_list(self, repository, mock_session):
        """Test get_by_grandparent_rating_key returns matching metadata."""
        mock_metadata = [
            SessionHistoryMetadataFactory.build(grandparent_rating_key=123),
            SessionHistoryMetadataFactory.build(grandparent_rating_key=123),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_metadata
        mock_session.execute.return_value = mock_result

        result = repository.get_by_grandparent_rating_key(123)

        assert len(result) == 2

    def test_get_by_parent_rating_key_returns_metadata_list(self, repository, mock_session):
        """Test get_by_parent_rating_key returns matching metadata."""
        mock_metadata = [
            SessionHistoryMetadataFactory.build(parent_rating_key=456),
            SessionHistoryMetadataFactory.build(parent_rating_key=456),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_metadata
        mock_session.execute.return_value = mock_result

        result = repository.get_by_parent_rating_key(456)

        assert len(result) == 2


class TestSessionHistoryMediaInfoRepository:
    """Tests for SessionHistoryMediaInfoRepository."""

    @pytest.fixture
    def mock_session(self):
        session = MagicMock()
        session.execute = MagicMock()
        return session

    @pytest.fixture
    def repository(self, mock_session):
        return SessionHistoryMediaInfoRepository(mock_session)

    def test_get_by_rating_key_returns_media_info(self, repository, mock_session):
        """Test get_by_rating_key returns media info when found."""
        mock_media_info = SessionHistoryMediaInfoFactory.build(rating_key=123)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_media_info
        mock_session.execute.return_value = mock_result

        result = repository.get_by_rating_key(123)

        assert result is mock_media_info

    def test_get_by_rating_key_returns_none_when_not_found(self, repository, mock_session):
        """Test get_by_rating_key returns None when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = repository.get_by_rating_key(999)

        assert result is None

    def test_get_by_history_id_returns_media_info(self, repository, mock_session):
        """Test get_by_history_id returns media info when found."""
        mock_media_info = SessionHistoryMediaInfoFactory.build(id=1)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_media_info
        mock_session.execute.return_value = mock_result

        result = repository.get_by_history_id(1)

        assert result is mock_media_info

    def test_get_by_history_id_returns_none_when_not_found(self, repository, mock_session):
        """Test get_by_history_id returns None when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = repository.get_by_history_id(999)

        assert result is None
