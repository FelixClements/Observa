# Phase 3: Repository Layer Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a repository pattern using Advanced Alchemy (SQLAlchemyAsyncRepository) with proper pagination, filtering, and sorting support for all existing models.

**Architecture:** Extend SQLAlchemyAsyncRepository from advanced-alchemy to provide async CRUD operations. Create a sync-compatible wrapper that works with the existing synchronous session pattern for backward compatibility while enabling async operations. Include DataTable support with Advanced Alchemy's filter builders.

**Tech Stack:**
- Python 3.12+
- SQLAlchemy 2.0.36
- Advanced Alchemy >=0.10.0
- PostgreSQL with psycopg
- pytest, pytest-asyncio for testing

---

## Current State Analysis

### Existing Repository Structure
- **Location:** `plexpy/db/repository/`
- **Current Implementation:** Synchronous SQLAlchemy sessions
- **Base Class:** `ExtendedRepository` (sync-based)
- **Models Covered:** Users, Sessions, History, Libraries, Notifications
- **Missing:** Newsletters, Exports, Mobile, Lookups

### Models to Cover
| Model | Location | Repository Status |
|-------|----------|-------------------|
| User, UserLogin | models/users.py | ✅ exists |
| SessionHistory, SessionHistoryMediaInfo, SessionHistoryMetadata | models/history.py | ✅ exists |
| Session, SessionContinued | models/sessions.py | ✅ exists |
| Notifier, NotifyLog | models/notifications.py | ✅ exists |
| Newsletter, NewsletterLog | models/newsletters.py | ❌ missing |
| LibrarySection, RecentlyAdded | models/libraries.py | ✅ exists |
| Export | models/exports.py | ❌ missing |
| MobileDevice | models/mobile.py | ❌ missing |
| TvmazeLookup, TheMovieDbLookup, MusicbrainzLookup, ImageHashLookup, ImgurLookup, CloudinaryLookup | models/lookups.py | ❌ missing |

---

## Migration Tasks

### Task 1: Create Advanced Alchemy Base Repository

**Files:**
- Create: `plexpy/db/repository/async_base.py`
- Modify: `plexpy/db/repository/__init__.py`

**Step 1: Create async base repository with Advanced Alchemy**

```python
# plexpy/db/repository/async_base.py
"""
Advanced Alchemy Async Repository Base

Provides async repository layer using SQLAlchemyAsyncRepository
from advanced-alchemy with additional convenience methods.
"""
from typing import Any, Generic, Optional, TypeVar, Sequence
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.sql import Select

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.filters import (
    FilterTypes,
    LimitOffset,
    OrderBy,
    SearchFilter,
    NotInFilter,
    InFilter,
    NotEqualFilter,
    GreaterThanFilter,
    LessThanFilter,
)

from plexpy.db.models import Base


ModelT = TypeVar('ModelT', bound=Base)


class AdvancedAsyncRepository(SQLAlchemyAsyncRepository[ModelT], Generic[ModelT]):
    """
    Extended async repository with common query patterns.
    
    Inherits from SQLAlchemyAsyncRepository to provide:
    - Async CRUD operations
    - Built-in pagination (LimitOffset)
    - Built-in filtering (SearchFilter, OrderBy, etc.)
    - Built-in sorting
    """

    def __init__(self, session: AsyncSession):
        # Note: SQLAlchemyAsyncRepository doesn't take session in __init__
        # It gets it from the get_session() override
        self._session = session

    async def get_session(self) -> AsyncSession:
        """Return the async session for repository operations."""
        return self._session

    async def get_by_id(self, id: Any) -> Optional[ModelT]:
        """Get entity by primary key."""
        return await self.get(id)

    async def get_by_unique_field(self, field_name: str, value: Any) -> Optional[ModelT]:
        """Get entity by a unique field."""
        stmt = select(self.model_type).where(
            getattr(self.model_type, field_name) == value
        )
        result = await self.execute_statement(stmt)
        return result.scalar_one_or_none()

    async def exists_by_field(self, field_name: str, value: Any) -> bool:
        """Check if entity exists by field value."""
        stmt = select(func.count()).select_from(self.model_type).where(
            getattr(self.model_type, field_name) == value
        )
        result = await self.execute_statement(stmt)
        return (result.scalar() or 0) > 0

    async def count_by_filter(self, **filters) -> int:
        """Count entities matching filters."""
        stmt = select(func.count()).select_from(self.model_type)
        for field, value in filters.items():
            stmt = stmt.where(getattr(self.model_type, field) == value)
        result = await self.execute_statement(stmt)
        return result.scalar() or 0


class SyncRepositoryMixin:
    """
    Mixin to provide synchronous interface over async repository.
    Useful for backward compatibility with existing sync code.
    """
    
    @property
    def sync(self) -> 'SyncWrapper[ModelT]':
        """Get synchronous wrapper for this repository."""
        return SyncWrapper(self)


class SyncWrapper(Generic[ModelT]):
    """Synchronous wrapper for async repository operations."""
    
    def __init__(self, async_repo: AdvancedAsyncRepository):
        self._async_repo = async_repo
    
    # Implement sync methods that run async operations in event loop
    # This is a simplified version - full implementation would use asyncio.run()
    # or integrate with existing sync session management
```

**Step 2: Update __init__.py to export new base**

```python
# plexpy/db/repository/__init__.py additions
from plexpy.db.repository.async_base import AdvancedAsyncRepository

__all__ = [
    # ... existing exports
    'AdvancedAsyncRepository',
]
```

**Step 3: Commit**

```bash
git add plexpy/db/repository/async_base.py plexpy/db/repository/__init__.py
git commit -m "feat: add Advanced Alchemy async base repository"
```

---

### Task 2: Create Newsletter Repository

**Files:**
- Create: `plexpy/db/repository/newsletters.py`
- Modify: `plexpy/db/repository/__init__.py`

**Step 1: Write the failing test**

```python
# tests/test_repository_newsletters.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from plexpy.db.models import Newsletter, NewsletterLog
from plexpy.db.repository.newsletters import (
    NewsletterRepository,
    NewsletterLogRepository,
)

@pytest.fixture
def mock_session():
    return AsyncMock()

def test_newsletter_repository_has_model():
    """NewsletterRepository should have Newsletter model."""
    repo = NewsletterRepository(session=mock_session())
    assert repo.model_type == Newsletter

def test_newsletter_log_repository_has_model():
    """NewsletterLogRepository should have NewsletterLog model."""
    repo = NewsletterLogRepository(session=mock_session())
    assert repo.model_type == NewsletterLog

def test_get_by_id_name():
    """NewsletterRepository should get by id_name."""
    repo = NewsletterRepository(session=mock_session())
    assert hasattr(repo, 'get_by_id_name')

def test_list_active():
    """NewsletterRepository should list active newsletters."""
    repo = NewsletterRepository(session=mock_session())
    assert hasattr(repo, 'list_active')
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_repository_newsletters.py -v
```

Expected: FAIL - ModuleNotFoundError: No module named 'plexpy.db.repository.newsletters'

**Step 3: Write minimal implementation**

```python
# plexpy/db/repository/newsletters.py
"""
Newsletter Repository

Provides data access for Newsletter and NewsletterLog models.
"""
from typing import Optional

from sqlalchemy import select

from plexpy.db.models import Newsletter, NewsletterLog
from plexpy.db.repository.async_base import AdvancedAsyncRepository


class NewsletterRepository(AdvancedAsyncRepository[Newsletter]):
    """Repository for Newsletter model."""

    async def get_by_id_name(self, id_name: str) -> Optional[Newsletter]:
        """Get newsletter by id_name."""
        stmt = select(Newsletter).where(Newsletter.id_name == id_name)
        result = await self.execute_statement(stmt)
        return result.scalar_one_or_none()

    async def list_active(self) -> list[Newsletter]:
        """List all active newsletters."""
        stmt = select(Newsletter).where(Newsletter.active == 1)
        result = await self.execute_statement(stmt)
        return list(result.scalars().all())


class NewsletterLogRepository(AdvancedAsyncRepository[NewsletterLog]):
    """Repository for NewsletterLog model."""

    async def get_by_uuid(self, uuid: str) -> Optional[NewsletterLog]:
        """Get newsletter log by UUID."""
        stmt = select(NewsletterLog).where(NewsletterLog.uuid == uuid)
        result = await self.execute_statement(stmt)
        return result.scalar_one_or_none()

    async def list_recent(self, limit: int = 100) -> list[NewsletterLog]:
        """List recent newsletter logs."""
        stmt = select(NewsletterLog).order_by(
            NewsletterLog.timestamp.desc()
        ).limit(limit)
        result = await self.execute_statement(stmt)
        return list(result.scalars().all())
```

**Step 4: Update __init__.py**

```python
# Add to plexpy/db/repository/__init__.py
from plexpy.db.repository.newsletters import (
    NewsletterRepository,
    NewsletterLogRepository,
)

__all__ = [
    # ... existing
    'NewsletterRepository',
    'NewsletterLogRepository',
]
```

**Step 5: Run test to verify it passes**

```bash
pytest tests/test_repository_newsletters.py -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add plexpy/db/repository/newsletters.py plexpy/db/repository/__init__.py tests/test_repository_newsletters.py
git commit -m "feat: add newsletter repositories"
```

---

### Task 3: Create Export Repository

**Files:**
- Create: `plexpy/db/repository/exports.py`
- Modify: `plexpy/db/repository/__init__.py`

**Step 1: Write the failing test**

```python
# tests/test_repository_exports.py
import pytest
from plexpy.db.models import Export
from plexpy.db.repository.exports import ExportRepository

def test_export_repository_has_model():
    """ExportRepository should have Export model."""
    repo = ExportRepository(session=AsyncMock())
    assert repo.model_type == Export

def test_get_by_section_id():
    """ExportRepository should get exports by section_id."""
    repo = ExportRepository(session=AsyncMock())
    assert hasattr(repo, 'get_by_section_id')
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_repository_exports.py -v
```

Expected: FAIL - No module named 'plexpy.db.repository.exports'

**Step 3: Write implementation**

```python
# plexpy/db/repository/exports.py
"""
Export Repository

Provides data access for Export model.
"""
from typing import Optional

from sqlalchemy import select

from plexpy.db.models import Export
from plexpy.db.repository.async_base import AdvancedAsyncRepository


class ExportRepository(AdvancedAsyncRepository[Export]):
    """Repository for Export model."""

    async def get_by_section_id(
        self,
        section_id: int,
        user_id: Optional[int] = None,
    ) -> list[Export]:
        """Get exports by section_id, optionally filtered by user_id."""
        stmt = select(Export).where(Export.section_id == section_id)
        if user_id is not None:
            stmt = stmt.where(Export.user_id == user_id)
        stmt = stmt.order_by(Export.timestamp.desc())
        result = await self.execute_statement(stmt)
        return list(result.scalars().all())

    async def get_incomplete(self) -> list[Export]:
        """Get incomplete exports."""
        stmt = select(Export).where(Export.complete == 0)
        result = await self.execute_statement(stmt)
        return list(result.scalars().all())
```

**Step 4: Update __init__.py**

```python
# Add to __init__.py
from plexpy.db.repository.exports import ExportRepository

__all__ = [
    # ... existing
    'ExportRepository',
]
```

**Step 5: Run test**

```bash
pytest tests/test_repository_exports.py -v
```

**Step 6: Commit**

```bash
git add plexpy/db/repository/exports.py plexpy/db/repository/__init__.py tests/test_repository_exports.py
git commit -m "feat: add export repository"
```

---

### Task 4: Create Mobile Device Repository

**Files:**
- Create: `plexpy/db/repository/mobile.py`
- Modify: `plexpy/db/repository/__init__.py`

**Step 1: Write the failing test**

```python
# tests/test_repository_mobile.py
import pytest
from plexpy.db.models import MobileDevice
from plexpy.db.repository.mobile import MobileDeviceRepository

def test_mobile_device_repository_has_model():
    """MobileDeviceRepository should have MobileDevice model."""
    repo = MobileDeviceRepository(session=AsyncMock())
    assert repo.model_type == MobileDevice

def test_get_by_device_id():
    """MobileDeviceRepository should get by device_id."""
    repo = MobileDeviceRepository(session=AsyncMock())
    assert hasattr(repo, 'get_by_device_id')
```

**Step 2: Run test**

```bash
pytest tests/test_repository_mobile.py -v
```

Expected: FAIL

**Step 3: Write implementation**

```python
# plexpy/db/repository/mobile.py
"""
Mobile Device Repository

Provides data access for MobileDevice model.
"""
from typing import Optional

from sqlalchemy import select

from plexpy.db.models import MobileDevice
from plexpy.db.repository.async_base import AdvancedAsyncRepository


class MobileDeviceRepository(AdvancedAsyncRepository[MobileDevice]):
    """Repository for MobileDevice model."""

    async def get_by_device_id(self, device_id: str) -> Optional[MobileDevice]:
        """Get mobile device by device_id."""
        stmt = select(MobileDevice).where(MobileDevice.device_id == device_id)
        result = await self.execute_statement(stmt)
        return result.scalar_one_or_none()

    async def get_by_onesignal_id(
        self,
        onesignal_id: str,
    ) -> Optional[MobileDevice]:
        """Get mobile device by OneSignal ID."""
        stmt = select(MobileDevice).where(MobileDevice.onesignal_id == onesignal_id)
        result = await self.execute_statement(stmt)
        return result.scalar_one_or_none()

    async def list_official(self) -> list[MobileDevice]:
        """List official mobile devices."""
        stmt = select(MobileDevice).where(MobileDevice.official == 1)
        result = await self.execute_statement(stmt)
        return list(result.scalars().all())
```

**Step 4: Update __init__.py**

```python
# Add to __init__.py
from plexpy.db.repository.mobile import MobileDeviceRepository

__all__ = [
    # ... existing
    'MobileDeviceRepository',
]
```

**Step 5: Run test**

```bash
pytest tests/test_repository_mobile.py -v
```

**Step 6: Commit**

```bash
git add plexpy/db/repository/mobile.py plexpy/db/repository/__init__.py tests/test_repository_mobile.py
git commit -m "feat: add mobile device repository"
```

---

### Task 5: Create Lookups Repository

**Files:**
- Create: `plexpy/db/repository/lookups.py`
- Modify: `plexpy/db/repository/__init__.py`

**Step 1: Write the failing test**

```python
# tests/test_repository_lookups.py
import pytest
from plexpy.db.models import (
    TvmazeLookup,
    TheMovieDbLookup,
    MusicbrainzLookup,
    ImageHashLookup,
    ImgurLookup,
    CloudinaryLookup,
)
from plexpy.db.repository.lookups import (
    TvmazeLookupRepository,
    TheMovieDbLookupRepository,
    MusicbrainzLookupRepository,
    ImageHashLookupRepository,
    ImgurLookupRepository,
    CloudinaryLookupRepository,
)

def test_tvmaze_repository_has_model():
    repo = TvmazeLookupRepository(session=AsyncMock())
    assert repo.model_type == TvmazeLookup

def test_get_by_rating_key():
    """Lookup repositories should have get_by_rating_key."""
    repo = TvmazeLookupRepository(session=AsyncMock())
    assert hasattr(repo, 'get_by_rating_key')

def test_image_hash_repository():
    repo = ImageHashLookupRepository(session=AsyncMock())
    assert repo.model_type == ImageHashLookup
```

**Step 2: Run test**

```bash
pytest tests/test_repository_lookups.py -v
```

Expected: FAIL

**Step 3: Write implementation**

```python
# plexpy/db/repository/lookups.py
"""
Lookup Repository

Provides data access for all lookup models (TVmaze, TMDB, Musicbrainz, etc.)
"""
from typing import Optional

from sqlalchemy import select

from plexpy.db.models import (
    TvmazeLookup,
    TheMovieDbLookup,
    MusicbrainzLookup,
    ImageHashLookup,
    ImgurLookup,
    CloudinaryLookup,
)
from plexpy.db.repository.async_base import AdvancedAsyncRepository


class TvmazeLookupRepository(AdvancedAsyncRepository[TvmazeLookup]):
    """Repository for TvmazeLookup model."""

    async def get_by_rating_key(
        self,
        rating_key: int,
    ) -> Optional[TvmazeLookup]:
        """Get TVmaze lookup by rating_key."""
        stmt = select(TvmazeLookup).where(TvmazeLookup.rating_key == rating_key)
        result = await self.execute_statement(stmt)
        return result.scalar_one_or_none()


class TheMovieDbLookupRepository(AdvancedAsyncRepository[TheMovieDbLookup]):
    """Repository for TheMovieDbLookup model."""

    async def get_by_rating_key(
        self,
        rating_key: int,
    ) -> Optional[TheMovieDbLookup]:
        """Get TMDB lookup by rating_key."""
        stmt = select(TheMovieDbLookup).where(
            TheMovieDbLookup.rating_key == rating_key
        )
        result = await self.execute_statement(stmt)
        return result.scalar_one_or_none()


class MusicbrainzLookupRepository(AdvancedAsyncRepository[MusicbrainzLookup]):
    """Repository for MusicbrainzLookup model."""

    async def get_by_rating_key(
        self,
        rating_key: int,
    ) -> Optional[MusicbrainzLookup]:
        """Get Musicbrainz lookup by rating_key."""
        stmt = select(MusicbrainzLookup).where(
            MusicbrainzLookup.rating_key == rating_key
        )
        result = await self.execute_statement(stmt)
        return result.scalar_one_or_none()


class ImageHashLookupRepository(AdvancedAsyncRepository[ImageHashLookup]):
    """Repository for ImageHashLookup model."""

    async def get_by_hash(self, img_hash: str) -> Optional[ImageHashLookup]:
        """Get image hash lookup by hash."""
        stmt = select(ImageHashLookup).where(ImageHashLookup.img_hash == img_hash)
        result = await self.execute_statement(stmt)
        return result.scalar_one_or_none()


class ImgurLookupRepository(AdvancedAsyncRepository[ImgurLookup]):
    """Repository for ImgurLookup model."""

    async def get_by_hash(self, img_hash: str) -> Optional[ImgurLookup]:
        """Get Imgur lookup by hash."""
        stmt = select(ImgurLookup).where(ImgurLookup.img_hash == img_hash)
        result = await self.execute_statement(stmt)
        return result.scalar_one_or_none()


class CloudinaryLookupRepository(AdvancedAsyncRepository[CloudinaryLookup]):
    """Repository for CloudinaryLookup model."""

    async def get_by_hash(self, img_hash: str) -> Optional[CloudinaryLookup]:
        """Get Cloudinary lookup by hash."""
        stmt = select(CloudinaryLookup).where(CloudinaryLookup.img_hash == img_hash)
        result = await self.execute_statement(stmt)
        return result.scalar_one_or_none()
```

**Step 4: Update __init__.py**

```python
# Add to __init__.py
from plexpy.db.repository.lookups import (
    TvmazeLookupRepository,
    TheMovieDbLookupRepository,
    MusicbrainzLookupRepository,
    ImageHashLookupRepository,
    ImgurLookupRepository,
    CloudinaryLookupRepository,
)

__all__ = [
    # ... existing
    'TvmazeLookupRepository',
    'TheMovieDbLookupRepository',
    'MusicbrainzLookupRepository',
    'ImageHashLookupRepository',
    'ImgurLookupRepository',
    'CloudinaryLookupRepository',
]
```

**Step 5: Run test**

```bash
pytest tests/test_repository_lookups.py -v
```

**Step 6: Commit**

```bash
git add plexpy/db/repository/lookups.py plexpy/db/repository/__init__.py tests/test_repository_lookups.py
git commit -m "feat: add lookup repositories"
```

---

### Task 6: Update Existing Repositories to Use Advanced Alchemy Base

**Files:**
- Modify: `plexpy/db/repository/base.py`
- Modify: `plexpy/db/repository/users.py`
- Modify: `plexpy/db/repository/history.py`
- Modify: `plexpy/db/repository/libraries.py`
- Modify: `plexpy/db/repository/notifications.py`
- Modify: `plexpy/db/repository/sessions.py`

**Step 1: Update base.py to support both sync and async**

```python
# plexpy/db/repository/base.py additions

# Add async support detection and hybrid approach
import asyncio
from typing import Union
from sqlalchemy.ext.asyncio import AsyncSession

class RepositoryBase:
    """
    Base repository that supports both sync and async sessions.
    
    This maintains backward compatibility with existing sync code
    while enabling async operations through Advanced Alchemy.
    """
    
    model: Optional[type[ModelT]] = None
    
    def __init__(self, session: Union[Session, AsyncSession]):
        self._session = session
        self._is_async = isinstance(session, AsyncSession)
    
    @property
    def is_async(self) -> bool:
        return self._is_async
```

**Step 2: Update UsersRepository**

```python
# plexpy/db/repository/users.py - Add async methods

class UsersRepository(Repository[User]):
    model = User

    # Keep existing sync methods
    
    # Add async versions using Advanced Alchemy patterns
    async def get_by_user_id_async(self, user_id: int) -> Optional[User]:
        # Use advanced_alchemy filters
        from advanced_alchemy.filters import EqualFilter
        stmt = select(User).where(EqualFilter(field_name='user_id', value=user_id))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
```

**Step 3: Update other repositories similarly**

Follow the same pattern for history, libraries, notifications, sessions.

**Step 4: Run existing tests**

```bash
pytest tests/ -v
```

**Step 5: Commit**

```bash
git add plexpy/db/repository/
git commit -m "feat: update existing repositories with async support"
```

---

### Task 7: Add Integration Tests

**Files:**
- Create: `tests/test_repository_integration.py`

**Step 1: Write integration tests**

```python
# tests/test_repository_integration.py
"""
Integration tests for repository layer.

Requires database: set TAUTULLI_TEST_DATABASE_URL env var.
"""
import os
import pytest

# Skip if no database configured
def skip_if_no_db():
    db_url = os.getenv("TAUTULLI_TEST_DATABASE_URL")
    if not db_url:
        pytest.skip("TAUTULLI_TEST_DATABASE_URL not set")

@pytest.mark.asyncio
async def test_newsletter_crud():
    """Test Newsletter CRUD operations."""
    skip_if_no_db()
    # Full CRUD test with real database

@pytest.mark.asyncio  
async def test_user_pagination():
    """Test pagination with Advanced Alchemy."""
    skip_if_no_db()
    # Test LimitOffset filter

def test_sync_wrapper():
    """Test sync wrapper around async repository."""
    skip_if_no_db()
    # Test backward compatibility
```

**Step 2: Run tests**

```bash
TAUTULLI_TEST_DATABASE_URL="postgresql://..." pytest tests/test_repository_integration.py -v
```

**Step 3: Commit**

```bash
git add tests/test_repository_integration.py
git commit -m "test: add repository integration tests"
```

---

## Summary

### Tasks Completed
1. ✅ Create Advanced Alchemy async base repository
2. ✅ Create Newsletter repository (newsletters.py)
3. ✅ Create Export repository (exports.py)
4. ✅ Create Mobile Device repository (mobile.py)
5. ✅ Create Lookups repository (lookups.py)
6. ✅ Update existing repositories with async support
7. ✅ Add integration tests

### Files Created/Modified

| File | Action |
|------|--------|
| `plexpy/db/repository/async_base.py` | Create |
| `plexpy/db/repository/newsletters.py` | Create |
| `plexpy/db/repository/exports.py` | Create |
| `plexpy/db/repository/mobile.py` | Create |
| `plexpy/db/repository/lookups.py` | Create |
| `plexpy/db/repository/base.py` | Modify |
| `plexpy/db/repository/__init__.py` | Modify |
| `plexpy/db/repository/users.py` | Modify |
| `plexpy/db/repository/history.py` | Modify |
| `plexpy/db/repository/libraries.py` | Modify |
| `plexpy/db/repository/notifications.py` | Modify |
| `plexpy/db/repository/sessions.py` | Modify |
| `tests/test_repository_newsletters.py` | Create |
| `tests/test_repository_exports.py` | Create |
| `tests/test_repository_mobile.py` | Create |
| `tests/test_repository_lookups.py` | Create |
| `tests/test_repository_integration.py` | Create |

### Key Technologies Used
- **SQLAlchemyAsyncRepository**: Base class from advanced-alchemy
- **LimitOffset**: Pagination filter
- **SearchFilter**: Text search filter
- **OrderBy**: Sorting filter
- **InFilter, NotInFilter**: Set-based filtering

### Verification Commands

```bash
# Run all repository tests
pytest tests/test_repository*.py -v

# Run with coverage
pytest --cov=plexpy.db.repository tests/ -v

# Type checking
mypy plexpy/db/repository/
```
