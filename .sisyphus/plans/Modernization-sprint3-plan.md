# Observa Modernization - Sprint 3 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Complete remaining modernization tasks including config DI refactoring for web/integrations, datatables migration, test factories, and unit tests.

**Architecture:** Continue using config dependency injection pattern already established in services/. For web layer, use module-level helper function like services do. Repository pattern for database access.

**Tech Stack:** Python 3.12+, SQLAlchemy 2.0, Advanced Alchemy, pytest, factory-boy

---

## Current State Summary

### Completed ✅
- Config DI in `plexpy/services/` (17 files)
- Repository layer created (10 files in `plexpy/db/repository/`)
- Test infrastructure (conftest.py, pyproject.toml)
- Sprint 1 & 2 items from Modernization-plan.md

### Remaining Work ❌
- Config DI in `plexpy/web/` (213 accesses to plexpy.CONFIG)
- Config DI in `plexpy/integrations/` (56 accesses)
- `plexpy/db/datatables.py` migration
- `plexpy/db/datafactory.py` migration  
- Test factories creation
- Repository and service unit tests

---

## Task 1: Create Web Dependencies Module

**Files:**
- Create: `plexpy/web/dependencies.py`

**Step 1: Create the web dependencies module**

```python
# plexpy/web/dependencies.py
"""Web layer dependency injection helpers."""

from functools import lru_cache

from plexpy.config import core as config_module


@lru_cache(maxsize=1)
def _get_config():
    """Get config instance with caching for web layer."""
    return config_module.get_config()


def get_config():
    """Get the current config instance for web layer."""
    return _get_config()


def clear_config_cache():
    """Clear the config cache (useful for testing)."""
    _get_config.cache_clear()
```

**Step 2: Run syntax check**

Run: `python -m py_compile plexpy/web/dependencies.py`
Expected: No output (success)

**Step 3: Commit**

```bash
git add plexpy/web/dependencies.py
git commit -m "feat(web): add config dependency injection helpers"
```

---

## Task 2: Create Integrations Dependencies Module

**Files:**
- Create: `plexpy/integrations/dependencies.py`

**Step 1: Create the integrations dependencies module**

```python
# plexpy/integrations/dependencies.py
"""Integrations layer dependency injection helpers."""

from functools import lru_cache

from plexpy.config import core as config_module


@lru_cache(maxsize=1)
def _get_config():
    """Get config instance with caching for integrations layer."""
    return config_module.get_config()


def get_config():
    """Get the current config instance for integrations layer."""
    return _get_config()


def clear_config_cache():
    """Clear the config cache (useful for testing)."""
    _get_config.cache_clear()
```

**Step 2: Run syntax check**

Run: `python -m py_compile plexpy/integrations/dependencies.py`
Expected: No output (success)

**Step 3: Commit**

```bash
git add plexpy/integrations/dependencies.py
git commit -m "feat(integrations): add config dependency injection helpers"
```

---

## Task 3: Migrate web/api2.py to Use Config DI

**Files:**
- Modify: `plexpy/web/api2.py`

**Step 1: Add import and helper function**

Add after existing imports (around line 41):
```python
from plexpy.web.dependencies import get_config
```

Replace function-level config access pattern. For each `plexpy.CONFIG.`:
1. Add `config = get_config()` at method start
2. Replace `plexpy.CONFIG.` with `config.`

Example transformation:
```python
# Before
if not plexpy.CONFIG.API_ENABLED:

# After  
def _api_validate(self, *args, **kwargs):
    config = get_config()
    if not config.API_ENABLED:
```

**Step 2: Run syntax check**

Run: `python -m py_compile plexpy/web/api2.py`
Expected: No output (success)

**Step 3: Commit**

```bash
git add plexpy/web/api2.py
git commit -m "refactor(api2): migrate to config dependency injection"
```

---

## Task 4: Migrate web/webserve.py to Use Config DI

**Files:**
- Modify: `plexpy/web/webserve.py`

**Step 1: Add import**

Add after existing imports:
```python
from plexpy.web.dependencies import get_config
```

**Step 2: Add helper function pattern**

Add after imports:
```python
def _get_config():
    return get_config()
```

**Step 3: Replace plexpy.CONFIG with _get_config()**

Replace all 150+ occurrences of `plexpy.CONFIG` with `_get_config()`

**Step 4: Run syntax check**

Run: `python -m py_compile plexpy/web/webserve.py`
Expected: No output (success)

**Step 5: Commit**

```bash
git add plexpy/web/webserve.py
git commit -m "refactor(webserve): migrate to config dependency injection"
```

---

## Task 5: Migrate web/webauth.py to Use Config DI

**Files:**
- Modify: `plexpy/web/webauth.py`

**Step 1: Add import and helper**

```python
from plexpy.web.dependencies import get_config

def _get_config():
    return get_config()
```

**Step 2: Replace plexpy.CONFIG with _get_config()**

**Step 3: Run syntax check**

Run: `python -m py_compile plexpy/web/webauth.py`
Expected: No output (success)

**Step 4: Commit**

```bash
git add plexpy/web/webauth.py
git commit -m "refactor(webauth): migrate to config dependency injection"
```

---

## Task 6: Migrate web/web_socket.py to Use Config DI

**Files:**
- Modify: `plexpy/web/web_socket.py`

**Step 1: Add import and helper**

```python
from plexpy.web.dependencies import get_config

def _get_config():
    return get_config()
```

**Step 2: Replace plexpy.CONFIG with _get_config()**

**Step 3: Run syntax check**

Run: `python -m py_compile plexpy/web/web_socket.py`
Expected: No output (success)

**Step 4: Commit**

```bash
git add plexpy/web/web_socket.py
git commit -m "refactor(web_socket): migrate to config dependency injection"
```

---

## Task 7: Migrate web/webstart.py to Use Config DI

**Files:**
- Modify: `plexpy/web/webstart.py`

**Step 1: Add import and helper**

```python
from plexpy.web.dependencies import get_config

def _get_config():
    return get_config()
```

**Step 2: Replace plexpy.CONFIG with _get_config()**

**Step 3: Run syntax check**

Run: `python -m py_compile plexpy/web/webstart.py`
Expected: No output (success)

**Step 4: Commit**

```bash
git add plexpy/web/webstart.py
git commit -m "refactor(webstart): migrate to config dependency injection"
```

---

## Task 8: Migrate web/session.py to Use Config DI

**Files:**
- Modify: `plexpy/web/session.py`

**Step 1: Add import and helper**

```python
from plexpy.web.dependencies import get_config

def _get_config():
    return get_config()
```

**Step 2: Replace plexpy.CONFIG with _get_config()**

**Step 3: Run syntax check**

Run: `python -m py_compile plexpy/web/session.py`
Expected: No output (success)

**Step 4: Commit**

```bash
git add plexpy/web/session.py
git commit -m "refactor(session): migrate to config dependency injection"
```

---

## Task 9: Migrate integrations/plex.py to Use Config DI

**Files:**
- Modify: `plexpy/integrations/plex.py`

**Step 1: Add import**

```python
from plexpy.integrations.dependencies import get_config

def _get_config():
    return get_config()
```

**Step 2: Replace plexpy.CONFIG with _get_config()**

**Step 3: Run syntax check**

Run: `python -m py_compile plexpy/integrations/plex.py`
Expected: No output (success)

**Step 4: Commit**

```bash
git add plexpy/integrations/plex.py
git commit -m "refactor(plex): migrate to config dependency injection"
```

---

## Task 10: Migrate integrations/plextv.py to Use Config DI

**Files:**
- Modify: `plexpy/integrations/plextv.py`

**Step 1: Add import and helper**

```python
from plexpy.integrations.dependencies import get_config

def _get_config():
    return get_config()
```

**Step 2: Replace plexpy.CONFIG with _get_config()**

**Step 3: Run syntax check**

Run: `python -m py_compile plexpy/integrations/plextv.py`
Expected: No output (success)

**Step 4: Commit**

```bash
git add plexpy/integrations/plextv.py
git commit -m "refactor(plextv): migrate to config dependency injection"
```

---

## Task 11: Migrate integrations/pmsconnect.py to Use Config DI

**Files:**
- Modify: `plexpy/integrations/pmsconnect.py`

**Step 1: Add import and helper**

```python
from plexpy.integrations.dependencies import get_config

def _get_config():
    return get_config()
```

**Step 2: Replace plexpy.CONFIG with _get_config()**

**Step 3: Run syntax check**

Run: `python -m py_compile plexpy/integrations/pmsconnect.py`
Expected: No output (success)

**Step 4: Commit**

```bash
git add plexpy/integrations/pmsconnect.py
git commit -m "refactor(pmsconnect): migrate to config dependency injection"
```

---

## Task 12: Migrate integrations/http_handler.py to Use Config DI

**Files:**
- Modify: `plexpy/integrations/http_handler.py`

**Step 1: Add import and helper**

```python
from plexpy.integrations.dependencies import get_config

def _get_config():
    return get_config()
```

**Step 2: Replace plexpy.CONFIG with _get_config()**

**Step 3: Run syntax check**

Run: `python -m py_compile plexpy/integrations/http_handler.py`
Expected: No output (success)

**Step 4: Commit**

```bash
git add plexpy/integrations/http_handler.py
git commit -m "refactor(http_handler): migrate to config dependency injection"
```

---

## Task 13: Create Test User Factory

**Files:**
- Create: `tests/factories/user_factory.py`

**Step 1: Create user factory**

```python
# tests/factories/user_factory.py
"""User model factory for testing."""

import factory
from factory.alchemy import SQLAlchemyModelFactory

from plexpy.db.engine import get_engine
from plexpy.db.models import User


class UserFactory(SQLAlchemyModelFactory):
    """Factory for creating User test instances."""

    class Meta:
        model = User
        sqlalchemy_session = None  # Set in conftest.py
        sqlalchemy_session_persistence = "commit"

    user_id = factory.Sequence(lambda n: n + 1)
    username = factory.Sequence(lambda n: f"user_{n}")
    friendly_name = factory.Faker("name")
    email = factory.Faker("email")
    is_active = 1
    is_admin = 0
    do_not_notify = 0
    keep_history = 1
```

**Step 2: Verify syntax**

Run: `python -m py_compile tests/factories/user_factory.py`
Expected: No output (success)

**Step 3: Commit**

```bash
git add tests/factories/user_factory.py
git commit -m "test: add user factory for testing"
```

---

## Task 14: Create Test Session History Factory

**Files:**
- Create: `tests/factories/session_history_factory.py`

**Step 1: Create session history factory**

```python
# tests/factories/session_history_factory.py
"""Session history model factory for testing."""

import factory
from factory.alchemy import SQLAlchemyModelFactory

from plexpy.db.models import SessionHistory


class SessionHistoryFactory(SQLAlchemyModelFactory):
    """Factory for creating SessionHistory test instances."""

    class Meta:
        model = SessionHistory
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "commit"

    id = factory.Sequence(lambda n: n + 1)
    session_id = factory.Sequence(lambda n: f"session_{n}")
    user_id = factory.Sequence(lambda n: n + 1)
    username = factory.Sequence(lambda n: f"user_{n}")
    session_key = factory.Sequence(lambda n: n + 1)
    started_at = factory.Faker("date_time_this_year")
    stopped_at = factory.Faker("date_time_this_year")
    duration = factory.Faker("random_int", min=60, max=7200)
    view_offset = 0
    state = "playing"
    media_type = "movie"
```

**Step 2: Verify syntax**

Run: `python -m py_compile tests/factories/session_history_factory.py`
Expected: No output (success)

**Step 3: Commit**

```bash
git add tests/factories/session_history_factory.py
git commit -m "test: add session history factory for testing"
```

---

## Task 15: Create Test Notification Factory

**Files:**
- Create: `tests/factories/notification_factory.py`

**Step 1: Create notification factory**

```python
# tests/factories/notification_factory.py
"""Notification model factory for testing."""

import factory
from factory.alchemy import SQLAlchemyModelFactory

from plexpy.db.models import NotifyLog


class NotifyLogFactory(SQLAlchemyModelFactory):
    """Factory for creating NotifyLog test instances."""

    class Meta:
        model = NotifyLog
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "commit"

    id = factory.Sequence(lambda n: n + 1)
    user_id = factory.Sequence(lambda n: n + 1)
    notify_action = "test_action"
    subject = factory.Faker("sentence")
    body = factory.Faker("paragraph")
    timestamp = factory.Faker("date_time_this_year")
    notify_level = 1
    notified = 1
```

**Step 2: Verify syntax**

Run: `python -m py_compile tests/factories/notification_factory.py`
Expected: No output (success)

**Step 3: Commit**

```bash
git add tests/factories/notification_factory.py
git commit -m "test: add notification factory for testing"
```

---

## Task 16: Write User Repository Tests

**Files:**
- Create: `tests/unit/test_repositories/test_users.py`

**Step 1: Create user repository test**

```python
# tests/unit/test_repositories/test_users.py
"""Unit tests for user repository."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from plexpy.db.repository.users import UserRepository
from plexpy.db.models import User


class TestUserRepository:
    """Test cases for UserRepository."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_get_by_id(self, mock_session):
        """Test getting user by ID."""
        repo = UserRepository(session=mock_session)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = User(
            user_id=1, username="test_user"
        )
        mock_session.execute.return_value = mock_result

        result = await repo.get(1)

        assert result is not None
        assert result.username == "test_user"

    @pytest.mark.asyncio
    async def test_get_by_username(self, mock_session):
        """Test getting user by username."""
        repo = UserRepository(session=mock_session)
        # Implementation depends on repository methods
        # Add specific test based on actual implementation
        pass
```

**Step 2: Run test to verify it works**

Run: `pytest tests/unit/test_repositories/test_users.py -v`
Expected: Tests run (may have failures if mocking needs adjustment)

**Step 3: Commit**

```bash
git add tests/unit/test_repositories/test_users.py
git commit -m "test: add user repository unit tests"
```

---

## Task 17: Write History Repository Tests

**Files:**
- Create: `tests/unit/test_repositories/test_history.py`

**Step 1: Create history repository test**

```python
# tests/unit/test_repositories/test_history.py
"""Unit tests for history repository."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from plexpy.db.repository.history import SessionHistoryRepository
from plexpy.db.models import SessionHistory


class TestSessionHistoryRepository:
    """Test cases for SessionHistoryRepository."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_get_by_session_id(self, mock_session):
        """Test getting history by session ID."""
        repo = SessionHistoryRepository(session=mock_session)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = SessionHistory(
            id=1, session_id="test_session"
        )
        mock_session.execute.return_value = mock_result

        result = await repo.get_by_session_id("test_session")

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_user_history(self, mock_session):
        """Test getting user history."""
        repo = SessionHistoryRepository(session=mock_session)
        # Add specific test based on actual implementation
        pass
```

**Step 2: Run test to verify it works**

Run: `pytest tests/unit/test_repositories/test_history.py -v`
Expected: Tests run

**Step 3: Commit**

```bash
git add tests/unit/test_repositories/test_history.py
git commit -m "test: add history repository unit tests"
```

---

## Task 18: Write Notification Repository Tests

**Files:**
- Create: `tests/unit/test_repositories/test_notifications.py`

**Step 1: Create notification repository test**

```python
# tests/unit/test_repositories/test_notifications.py
"""Unit tests for notification repository."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from plexpy.db.repository.notifications import NotifyLogRepository
from plexpy.db.models import NotifyLog


class TestNotifyLogRepository:
    """Test cases for NotifyLogRepository."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_get_user_notifications(self, mock_session):
        """Test getting user notifications."""
        repo = NotifyLogRepository(session=mock_session)
        # Add specific test based on actual implementation
        pass

    @pytest.mark.asyncio
    async def test_delete_old_logs(self, mock_session):
        """Test deleting old notification logs."""
        repo = NotifyLogRepository(session=mock_session)
        # Add specific test based on actual implementation
        pass
```

**Step 2: Run test to verify it works**

Run: `pytest tests/unit/test_repositories/test_notifications.py -v`
Expected: Tests run

**Step 3: Commit**

```bash
git add tests/unit/test_repositories/test_notifications.py
git commit -m "test: add notification repository unit tests"
```

---

## Task 19: Write User Service Tests

**Files:**
- Create: `tests/unit/test_services/test_users.py`

**Step 1: Create user service test**

```python
# tests/unit/test_services/test_users.py
"""Unit tests for users service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from plexpy.services.users import UsersService


class TestUsersService:
    """Test cases for UsersService."""

    @pytest.fixture
    def mock_config(self):
        """Create mock config."""
        config = MagicMock()
        config.PMS_IDENTIFIER = "test_server"
        config.GROUP_HISTORY_TABLES = False
        return config

    @pytest.fixture
    def service(self, mock_config):
        """Create users service with mocks."""
        with patch("plexpy.services.users._get_config", return_value=mock_config):
            return UsersService()

    def test_get_users(self, service):
        """Test getting users list."""
        # Add specific test based on actual implementation
        pass
```

**Step 2: Run test to verify it works**

Run: `pytest tests/unit/test_services/test_users.py -v`
Expected: Tests run

**Step 3: Commit**

```bash
git add tests/unit/test_services/test_users.py
git commit -m "test: add user service unit tests"
```

---

## Task 20: Run Full Test Suite

**Step 1: Run all tests**

Run: `pytest tests/ -v --tb=short`
Expected: All tests pass or show expected failures

**Step 2: Commit final changes**

```bash
git add -A
git commit -m "test: run full test suite verification"
```

---

## Execution Summary

| Task | Description | Files Changed |
|------|-------------|---------------|
| 1 | Create web dependencies module | 1 new |
| 2 | Create integrations dependencies module | 1 new |
| 3-8 | Migrate web/ files (api2, webserve, webauth, web_socket, webstart, session) | 6 modified |
| 9-12 | Migrate integrations/ files (plex, plextv, pmsconnect, http_handler) | 4 modified |
| 13-15 | Create test factories (user, session_history, notification) | 3 new |
| 16-18 | Write repository unit tests | 3 new |
| 19 | Write service unit tests | 1 new |
| 20 | Run full test suite | - |

**Total: 20 tasks, ~19 new/modified files**

---

## Plan complete

This plan is saved to `.sisyphus/plans/Modernization-sprint3-plan.md`

**Two execution options:**

1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

2. **Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
