# Tautulli 2026 Modernization Plan

## Executive Summary

This document outlines the comprehensive modernization of Tautulli's database layer from 2015-era patterns to 2026 industry standards. The migration will replace legacy string-based SQL, custom repository implementations, and mixed architecture with a clean, type-safe, and maintainable codebase using Advanced Alchemy and modern Python patterns.

**Timeline**: 6-8 weeks
**Breaking Changes**: Yes (documented in Section 7)
**Risk Level**: Medium

---

## Table of Contents

1. [Current State Assessment](#1-current-state-assessment)
2. [Technology Stack](#2-technology-stack)
3. [Why Advanced Alchemy](#3-why-advanced-alchemy)
4. [Implementation Roadmap](#4-implementation-roadmap)
5. [File Change Summary](#5-file-change-summary)
6. [Testing Strategy](#6-testing-strategy)
7. [Breaking Changes](#7-breaking-changes)
8. [Rollback Plan](#8-rollback-plan)

---

## 1. Current State Assessment

### 1.1 Architecture Overview

| Component | Location | Status | Lines |
|-----------|----------|--------|-------|
| **Legacy DataTables** | `plexpy/db/datatables.py` | 🔴 Needs Migration | 387 |
| **Data Factory** | `plexpy/db/datafactory.py` | 🔴 Needs Migration | 3,395 |
| **Database Wrapper** | `plexpy/db/database.py` | 🔴 Needs Migration | 98 |
| **Raw SQL Queries** | `plexpy/db/queries/raw_pg.py` | 🔴 Needs Migration | 47 |
| **Repository Base** | `plexpy/db/repository/base.py` | ⚠️ Basic | 54 |
| **Repository Impl** | `plexpy/db/repository/*.py` | ⚠️ Basic | ~200 |
| **Query Helpers** | `plexpy/db/queries/__init__.py` | ⚠️ Basic | 47 |
| **Models** | `plexpy/db/models/*.py` | ✅ Modern | ~800 |
| **Web Layer** | `plexpy/web/*.py` | 🔄 Mixed | ~5,000 |

### 1.2 Legacy Patterns to Eliminate

```python
# BAD: String-based SQL (datatables.py:73-173)
query = 'SELECT * FROM (SELECT %s FROM %s %s %s %s %s) AS data %s %s' \
        % (extracted_columns['column_string'], table_name, join, c_where, group, union, where, order)

# BAD: Manual parameter binding (datatables.py:42-65)
for idx, value in enumerate(args, start=1):
    param_name = f"param_{idx}"
    query = query.replace('?', f":{param_name}", 1)
    params[param_name] = value

# BAD: Raw text() queries (api2.py)
result = connection.execute(text("SELECT * FROM sessions WHERE..."))
```

### 1.3 What Works Well

- SQLAlchemy 2.0.36 (already modern)
- Model definitions with Mapped types
- Basic Repository pattern (foundation to extend)
- Query helpers (pagination, fetch mappings)

---

## 2. Technology Stack

### 2.1 Target Stack

| Component | Target Version | Justification |
|-----------|---------------|---------------|
| **SQLAlchemy** | 2.0.x (latest patch) | Already at 2.0.36 |
| **Advanced Alchemy** | Latest | Industry-standard repository pattern |
| **Pydantic** | 2.x | Type validation, serialization |
| **Pytest** | 8.x | Modern test framework |
| **factory_boy** | 3.3.x | Test fixtures |
| **httpx** | 0.27.x | Async HTTP testing |

### 2.2 Dependency Changes

```diff
requirements.txt
@@
+advanced-alchemy>=0.10.0
+pydantic>=2.0
+pytest>=8.0
+pytest-asyncio>=0.23
+factory-boy>=3.3
+httpx>=0.27
```

---

## 3. Why Advanced Alchemy

### 3.1 What is Advanced Alchemy?

Advanced Alchemy is a production-grade library from the Litestar team that provides:

- **Type-safe repositories** with full generic support
- **Built-in filtering, pagination, sorting**
- **Async support** out of the box
- **Bulk operations** optimized for performance
- **5,000+ GitHub stars** and active maintenance

### 3.2 Comparison

| Pattern | Legacy Code | Advanced Alchemy |
|---------|-------------|------------------|
| **CRUD** | 50 lines per model | 0 lines (automatic) |
| **Pagination** | Manual offset/limit | `.paginate(page=1, per_page=25)` |
| **Filtering** | String-based where | `.filter(Model.field == value)` |
| **Sorting** | Manual ORDER BY | `.order_by(Model.field.desc())` |
| **Bulk Create** | Loop + add | `.create_many([...])` |
| **Type Safety** | Partial | Full generics |

### 3.3 Example: Before vs After

**Before (Legacy Pattern - datafactory.py:177-233)**
```python
columns = [
    "session_history.reference_id",
    "MAX(session_history.id) AS row_id",
    "MAX(started) AS date",
    "MIN(started) AS started",
    # ... 30 more string columns
]

query = 'SELECT * FROM (SELECT %s FROM %s %s %s %s %s) AS data %s %s' \
        % (extracted_columns['column_string'], table_name, join, c_where, group, union, where, order)

# Manually parse results
for item in history:
    row = {
        'reference_id': item['reference_id'],
        'row_id': item['row_id'],
        # ... 40 more field mappings
    }
```

**After (Modern Pattern)**
```python
# repository/history.py
class SessionHistoryRepository(AdvancedAlchemyRepository[SessionHistory]):
    async def get_history_datatable(
        self,
        params: DataTableParams,
        user_id: int | None = None,
        media_type: str | None = None,
    ) -> DataTableResponse[SessionHistoryDTO]:
        query = select(SessionHistory)
        
        if user_id:
            query = query.where(SessionHistory.user_id == user_id)
        if media_type:
            query = query.where(SessionHistory.media_type == media_type)
        
        return await self.to_datatable(
            query=query,
            params=params,
            dto=SessionHistoryDTO,
            # Automatic filtering, sorting, pagination
        )
```

---

## 4. Implementation Roadmap

### Phase 1: Foundation (Week 1)

#### 1.1 Add Dependencies
```bash
pip install advanced-alchemy pydantic pytest pytest-asyncio factory-boy httpx
```

#### 1.2 Create Repository Layer Structure

```
plexpy/db/repository/
├── __init__.py
├── base.py              # Extended AdvancedAlchemyRepository
├── history.py           # SessionHistory, Metadata, MediaInfo
├── users.py             # User, UserLogin
├── notifications.py     # Notifier, NotifyLog
├── newsletters.py      # Newsletter, NewsletterLog
├── libraries.py         # LibrarySection, RecentlyAdded
├── sessions.py          # Session, SessionContinued
├── exports.py           # Export
├── mobile.py            # MobileDevice
└── lookups.py          # All lookup repositories
```

#### 1.3 Create Service Layer Structure

```
plexpy/services/
├── __init__.py
├── base.py              # BaseService with DI
├── history.py           # HistoryService├── users.py             # UsersService
├── libraries.py        
 # LibrariesService
├── notifications.py     # NotificationsService
├── newsletters.py       # NewslettersService
├── exporter.py          # ExporterService
└── activity.py          # ActivityService
```

#### 1.4 Create DataTables Query Builder

```python
# plexpy/db/querybuilder.py
from typing import Any, Callable
from advanced_alchemy.repository import SQLAlchemyRepository
from pydantic import BaseModel

class DataTableParams(BaseModel):
    draw: int
    start: int = 0
    length: int = 25
    search: str | None = None
    order: list[dict[str, Any]] = []
    columns: list[dict[str, Any]] = []

class DataTableResponse(BaseModel):
    draw: int
    recordsTotal: int
    recordsFiltered: int
    data: list[dict[str, Any]]

class DataTableQuery:
    """Build DataTables-compatible queries with type safety."""
    
    def __init__(
        self,
        model: type[Base],
        session: Session,
    ):
        self.model = model
        self.session = session
        self.searchable_columns: list[Column] = []
        self.orderable_columns: dict[str, Column] = {}
        self.filter_columns: dict[str, Column] = {}
    
    def add_searchable(self, *columns: Column) -> 'DataTableQuery':
        """Add columns for global search."""
        self.searchable_columns.extend(columns)
        return self
    
    def add_orderable(self, name: str, column: Column) -> 'DataTableQuery':
        """Add orderable column mapping."""
        self.orderable_columns[name] = column
        return self
    
    def add_filterable(self, name: str, column: Column) -> 'DataTableQuery':
        """Add filterable column mapping."""
        self.filter_columns[name] = column
        return self
    
    async def execute(
        self,
        params: DataTableParams,
        formatter: Callable[[Any], dict] | None = None,
    ) -> DataTableResponse:
        """Execute query and return DataTables response."""
        # Build base query
        query = select(self.model)
        
        # Apply search
        if params.search:
            search_filters = [
                col.ilike(f"%{params.search}%")
                for col in self.searchable_columns
            ]
            query = query.where(or_(*search_filters))
        
        # Apply ordering
        if params.order:
            for order_item in params.order:
                col_idx = int(order_item['column'])
                direction = order_item['dir']
                col_name = params.columns[col_idx].get('data')
                
                if col_name and col_name in self.orderable_columns:
                    col = self.orderable_columns[col_name]
                    if direction == 'desc':
                        query = query.order_by(col.desc())
                    else:
                        query = query.order_by(col.asc())
        
        # Get total count
        total_query = select(func.count()).select_from(query.subquery())
        total = await self.session.execute(total_query)
        recordsTotal = total.scalar()
        
        # Apply pagination
        query = query.offset(params.start).limit(params.length)
        
        # Execute
        result = await self.session.execute(query)
        recordsFiltered = len(result.scalars().all())
        
        # Format results
        data = [
            formatter(row) if formatter else self._default_formatter(row)
            for row in result.scalars().all()
        ]
        
        return DataTableResponse(
            draw=params.draw,
            recordsTotal=recordsTotal,
            recordsFiltered=recordsFiltered,
            data=data,
        )
```

---

### Phase 2: Model Enhancement (Week 2)

#### 2.1 Add Hybrid Properties

```python
# plexpy/db/models/history.py
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func

class SessionHistory(Base):
    __tablename__ = 'session_history'
    
    reference_id: Mapped[int | None] = mapped_column(Integer)
    started: Mapped[int | None] = mapped_column(Integer)
    stopped: Mapped[int | None] = mapped_column(Integer)
    paused_counter: Mapped[int | None] = mapped_column(Integer, default=0)
    
    @hybrid_property
    def duration(self) -> int:
        """Calculate duration in seconds."""
        if self.stopped and self.started:
            return (self.stopped - self.started) - (self.paused_counter or 0)
        return 0
    
    @duration.expression
    def duration(cls) -> ColumnElement[int]:
        """Expression for database-side calculation."""
        return func.coalesce(cls.stopped, 0) - cls.started - func.coalesce(cls.paused_counter, 0)
    
    @hybrid_property
    def percent_complete(self) -> float | None:
        """Calculate percent complete from view offset."""
        return None  # Requires joined metadata
```

#### 2.2 Add Table Indexes

```python
class SessionHistory(Base):
    __tablename__ = 'session_history'
    __table_args__ = (
        Index('idx_sh_user_id', 'user_id'),
        Index('idx_sh_started', 'started'),
        Index('idx_sh_reference_id', 'reference_id'),
        Index('idx_sh_section_id', 'section_id'),
        Index('idx_sh_media_type', 'media_type'),
        {'schema': 'public'}
    )
```

#### 2.3 Add Pydantic DTOs

```python
# plexpy/db/dto/history.py
from pydantic import BaseModel, field_validator

class SessionHistoryDTO(BaseModel):
    id: int
    reference_id: int | None
    started: int | None
    stopped: int | None
    user_id: int | None
    media_type: str | None
    title: str | None
    friendly_name: str | None
    platform: str | None
    
    @field_validator('platform', mode='before')
    @classmethod
    def normalize_platform(cls, v: str | None) -> str | None:
        if v in PLATFORM_NAME_OVERRIDES:
            return PLATFORM_NAME_OVERRIDES[v]
        return v
    
    model_config = {
        'from_attributes': True,
        'populate_by_name': True,
    }
```

---

### Phase 3: Service Migration (Week 3-4)

#### 3.1 Pattern: Repository + Service

```python
# plexpy/services/history.py
from advanced_alchemy.repository import SQLAlchemyRepository
from typing import Annotated
from fastapi import Depends

class HistoryService:
    """Service layer for history operations."""
    
    def __init__(
        self,
        history_repo: Annotated[SessionHistoryRepository, Depends()],
        metadata_repo: Annotated[SessionHistoryMetadataRepository, Depends()],
        media_info_repo: Annotated[SessionHistoryMediaInfoRepository, Depends()],
    ):
        self.history = history_repo
        self.metadata = metadata_repo
        self.media_info = media_info_repo
    
    async def get_history_datatable(
        self,
        params: DataTableParams,
        user_id: int | None = None,
        grouping: bool = True,
    ) -> DataTableResponse:
        """Get session history with DataTables server-side processing."""
        
        # Build query with joins
        query = (
            select(SessionHistory)
            .options(
                selectinload(SessionHistory.metadata),
                selectinload(SessionHistory.media_info),
                selectinload(SessionHistory.user),
            )
        )
        
        # Apply filters
        if user_id:
            query = query.where(SessionHistory.user_id == user_id)
        
        # Get totals
        total = await self.history.count(query)
        
        # Apply ordering
        query = self._apply_ordering(query, params)
        
        # Apply pagination
        query = query.offset(params.start).limit(params.length)
        
        # Execute
        result = await self.history.session.execute(query)
        
        # Format results
        data = [
            self._format_history_row(row)
            for row in result.unique().scalars().all()
        ]
        
        return DataTableResponse(
            draw=params.draw,
            recordsTotal=total,
            recordsFiltered=total,
            data=data,
        )
    
    async def get_home_stats(
        self,
        time_range: int = 30,
        stats_type: str = 'plays',
        stats_count: int = 10,
    ) -> list[dict]:
        """Get home dashboard statistics."""
        from_date = datetime.utcnow() - timedelta(days=time_range)
        
        query = (
            select(
                SessionHistoryMetadata.full_title,
                func.count(distinct(SessionHistory.reference_id)).label('total_plays'),
                func.sum(func.coalesce(SessionHistory.stopped, 0) - SessionHistory.started).label('total_duration'),
            )
            .select_from(SessionHistory)
            .join(SessionHistoryMetadata)
            .where(SessionHistory.started >= from_date)
            .where(SessionHistory.media_type == 'movie')
            .group_by(SessionHistoryMetadata.full_title)
            .order_by(
                desc('total_plays') if stats_type == 'plays' else desc('total_duration')
            )
            .limit(stats_count)
        )
        
        result = await self.history.session.execute(query)
        return [dict(row) for row in result.all()]
    
    def _apply_ordering(self, query: Select, params: DataTableParams) -> Select:
        """Apply DataTables ordering."""
        if not params.order:
            return query.order_by(SessionHistory.started.desc())
        
        for order_item in params.order:
            col_idx = int(order_item['column'])
            direction = order_item['dir']
            col_name = params.columns[col_idx].get('data')
            
            column_map = {
                'date': SessionHistory.started,
                'user': User.friendly_name,
                'title': SessionHistoryMetadata.full_title,
                # ... more columns
            }
            
            if col_name in column_map:
                col = column_map[col_name]
                if direction == 'desc':
                    query = query.order_by(col.desc())
                else:
                    query = query.order_by(col.asc())
        
        return query
    
    def _format_history_row(self, row: SessionHistory) -> dict:
        """Format a history row for DataTables response."""
        metadata = row.metadata
        
        watched_percent = {
            'movie': MOVIE_WATCHED_PERCENT,
            'episode': TV_WATCHED_PERCENT,
            'track': MUSIC_WATCHED_PERCENT,
        }.get(row.media_type, 0)
        
        watched_status = self._calculate_watched_status(
            row.media_type,
            row.view_offset,
            metadata.duration if metadata else None,
            watched_percent,
        )
        
        return {
            'id': row.id,
            'reference_id': row.reference_id,
            'started': row.started,
            'stopped': row.stopped,
            'user_id': row.user_id,
            'user': row.user.username if row.user else None,
            'friendly_name': row.user.friendly_name if row.user else None,
            'media_type': row.media_type,
            'title': metadata.full_title if metadata else None,
            'platform': self._normalize_platform(row.platform),
            'watched_status': watched_status,
        }
```

#### 3.2 Migrated Services

| Service | Source | Target |
|---------|--------|--------|
| **UsersService** | `services/users.py` + `datafactory.py` | `services/users.py` |
| **HistoryService** | `datafactory.py` | `services/history.py` |
| **LibrariesService** | `services/libraries.py` | `services/libraries.py` |
| **NotificationsService** | `datafactory.py` | `services/notifications.py` |
| **NewslettersService** | `datafactory.py` | `services/newsletters.py` |
| **ExportService** | `services/exporter.py` | `services/exporter.py` |
| **ActivityService** | `activity_handler.py` | `services/activity.py` |

---

### Phase 4: Web Layer Update (Week 5)

#### 4.1 Dependency Injection Setup

```python
# plexpy/web/dependencies.py
from fastapi import Depends, Request

async def get_session(request: Request) -> AsyncSession:
    """Get database session from request state."""
    return request.state.db_session

def get_history_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> HistoryService:
    """Inject HistoryService with session."""
    return HistoryService(
        history_repo=SessionHistoryRepository(session),
        metadata_repo=SessionHistoryMetadataRepository(session),
        media_info_repo=SessionHistoryMediaInfoRepository(session),
    )

def get_users_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UsersService:
    """Inject UsersService with session."""
    return UsersService(
        user_repo=UserRepository(session),
        login_repo=UserLoginRepository(session),
    )
```

#### 4.2 Updated API Endpoints

```python
# plexpy/web/api2.py (updated pattern)
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()

@router.get("/api/v2/history")
async def get_history(
    params: DataTableParams,
    service: Annotated[HistoryService, Depends(get_history_service)],
) -> DataTableResponse:
    """Get session history with server-side processing."""
    return await service.get_history_datatable(params)

@router.get("/api/v2/users")
async def get_users(
    include_inactive: bool = False,
    service: Annotated[UsersService, Depends(get_users_service)],
) -> list[UserDTO]:
    """Get all users."""
    return await service.get_users(include_inactive=include_inactive)

@router.post("/api/v2/users")
async def create_user(
    data: CreateUserRequest,
    service: Annotated[UsersService, Depends(get_users_service)],
) -> UserDTO:
    """Create a new user."""
    return await service.create_user(data)
```

#### 4.3 Updated Webserve.py

```python
# plexpy/web/webserve.py (updated pattern)
class WebInterface(object):
    """Main web interface handler."""
    
    async def get_history(self, request):
        """GET /history - Render history page."""
        return await self._render_template('history.html')
    
    async def get_history_data(self, request):
        """GET /history/data - Get history data."""
        params = await self._parse_datatable_params(request)
        service = self._get_history_service()
        result = await service.get_history_datatable(params)
        return jsonify(result.model_dump())
```

---

### Phase 5: Testing (Week 6)

#### 5.1 Test Structure

```
tests/
├── conftest.py                 # Pytest configuration
├── factories/
│   ├── __init__.py
│   ├── user_factory.py
│   ├── session_factory.py
│   ├── history_factory.py
│   └── notification_factory.py
├── unit/
│   ├── test_repositories/
│   │   ├── __init__.py
│   │   ├── test_history.py
│   │   ├── test_users.py
│   │   └── test_notifications.py
│   ├── test_services/
│   │   ├── __init__.py
│   │   ├── test_history.py
│   │   └── test_users.py
│   └── test_querybuilder.py
├── integration/
│   ├── __init__.py
│   ├── test_database.py
│   ├── test_api.py
│   └── test_repositories.py
└── fixtures/
    ├── test_db.py
    └── test_data.py
```

#### 5.2 Pytest Configuration

```python
# tests/conftest.py
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_engine():
    """Create test database engine."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    return engine

@pytest.fixture
async def async_engine():
    """Create async test database engine."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    yield engine
    await engine.dispose()

@pytest.fixture
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async session for testing."""
    async_session = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session

@pytest.fixture
def db_session(test_engine):
    """Create sync session for testing."""
    # Create tables
    Base.metadata.create_all(test_engine)
    
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.close()
```

#### 5.3 Factory Boy Fixtures

```python
# tests/factories/__init__.py
import factory
from factory.alchemy import SQLAlchemyFactory

# Import all models
from plexpy.db.models import User, SessionHistory, SessionHistoryMetadata

# tests/factories/user_factory.py
class UserFactory(SQLAlchemyFactory):
    class Meta:
        model = User
    
    user_id = factory.Sequence(lambda n: n + 1)
    username = factory.Sequence(lambda n: f"user_{n}")
    friendly_name = None
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    deleted_user = 0
    is_active = 1

# tests/factories/history_factory.py
class SessionHistoryFactory(SQLAlchemyFactory):
    class Meta:
        model = SessionHistory
    
    id = factory.Sequence(lambda n: n + 1)
    reference_id = factory.Sequence(lambda n: n + 1)
    started = factory.LazyFunction(lambda: int(datetime.utcnow().timestamp()))
    stopped = factory.LazyFunction(lambda: int(datetime.utcnow().timestamp()) + 3600)
    user_id = factory.SubFactory(UserFactory)
    media_type = 'movie'
    title = factory.Sequence(lambda n: f"Movie {n}")

class SessionHistoryMetadataFactory(SQLAlchemyFactory):
    class Meta:
        model = SessionHistoryMetadata
    
    id = factory.Sequence(lambda n: n + 1)
    rating_key = factory.Sequence(lambda n: n + 1000)
    full_title = factory.Sequence(lambda n: f"Movie {n}")
    title = factory.Sequence(lambda n: f"Movie {n}")
    year = 2024
    duration = 7200
```

#### 5.4 Example Tests

```python
# tests/unit/test_repositories/test_history.py
import pytest
from tests.factories import SessionHistoryFactory, UserFactory

class TestSessionHistoryRepository:
    @pytest.mark.asyncio
    async def test_get_history_datatable_returns_filtered_results(
        self,
        async_session: AsyncSession,
    ):
        """Test that datatable query returns correct filtered results."""
        # Arrange
        user = await UserFactory.create()
        await SessionHistoryFactory.create_batch(5, user_id=user.user_id, media_type='movie')
        await SessionHistoryFactory.create_batch(3, user_id=user.user_id, media_type='episode')
        
        repo = SessionHistoryRepository(async_session)
        
        params = DataTableParams(
            draw=1,
            start=0,
            length=10,
            search='',
            order=[],
            columns=[
                {'data': 'media_type'},
            ],
        )
        
        # Act
        result = await repo.datatable_query(
            params=params,
            filter_by={'user_id': user.user_id},
        )
        
        # Assert
        assert result.recordsTotal == 8
        assert len(result.data) == 8
    
    @pytest.mark.asyncio
    async def test_get_history_with_search_filter(
        self,
        async_session: AsyncSession,
    ):
        """Test that search filter works correctly."""
        # Arrange
        await SessionHistoryFactory.create(title='Action Movie')
        await SessionHistoryFactory.create(title='Comedy Movie')
        await SessionHistoryFactory.create(title='Drama Series')
        
        repo = SessionHistoryRepository(async_session)
        
        params = DataTableParams(
            draw=1,
            start=0,
            length=10,
            search='Movie',
            order=[],
            columns=[],
        )
        
        # Act
        result = await repo.datatable_query(
            params=params,
            searchable_columns=[SessionHistory.title],
        )
        
        # Assert
        assert result.recordsFiltered == 2

# tests/unit/test_services/test_history.py
class TestHistoryService:
    @pytest.mark.asyncio
    async def test_get_home_stats_returns_correct_format(
        self,
        async_session: AsyncSession,
    ):
        """Test that home stats return correctly formatted data."""
        # Arrange
        await SessionHistoryFactory.create_batch(5, media_type='movie')
        await SessionHistoryFactory.create_batch(3, media_type='episode')
        
        service = HistoryService(
            history_repo=SessionHistoryRepository(async_session),
            metadata_repo=SessionHistoryMetadataRepository(async_session),
            media_info_repo=SessionHistoryMediaInfoRepository(async_session),
        )
        
        # Act
        result = await service.get_home_stats(
            time_range=30,
            stats_type='plays',
            stats_count=10,
        )
        
        # Assert
        assert isinstance(result, list)
        assert len(result) <= 10
```

---

## 5. File Change Summary

### 5.1 Files to Create

| File | Purpose | Lines |
|------|---------|-------|
| `advanced-alchemy` | Dependency (pip install) | - |
| `plexpy/db/repository/base.py` | Extended repository base | 200 |
| `plexpy/db/repository/history.py` | History repositories | 150 |
| `plexpy/db/repository/users.py` | User repositories | 100 |
| `plexpy/db/repository/notifications.py` | Notification repositories | 100 |
| `plexpy/db/repository/libraries.py` | Library repositories | 100 |
| `plexpy/db/repository/sessions.py` | Session repositories | 100 |
| `plexpy/db/repository/newsletters.py` | Newsletter repositories | 100 |
| `plexpy/db/repository/exports.py` | Export repositories | 50 |
| `plexpy/db/repository/mobile.py` | Mobile repositories | 50 |
| `plexpy/db/repository/lookups.py` | Lookup repositories | 100 |
| `plexpy/services/base.py` | Base service class | 100 |
| `plexpy/services/history.py` | History service | 300 |
| `plexpy/services/users.py` | Users service | 200 |
| `plexpy/services/libraries.py` | Libraries service | 150 |
| `plexpy/services/notifications.py` | Notifications service | 150 |
| `plexpy/services/newsletters.py` | Newsletters service | 150 |
| `plexpy/services/exporter.py` | Exporter service | 200 |
| `plexpy/services/activity.py` | Activity service | 150 |
| `plexpy/db/querybuilder.py` | DataTables query builder | 200 |
| `plexpy/db/dto/__init__.py` | DTO exports | 50 |
| `plexpy/db/dto/history.py` | History DTOs | 100 |
| `plexpy/db/dto/users.py` | User DTOs | 100 |
| `tests/conftest.py` | Pytest configuration | 100 |
| `tests/factories/__init__.py` | Factory exports | 50 |
| `tests/factories/user_factory.py` | User factory | 50 |
| `tests/factories/history_factory.py` | History factory | 50 |
| `tests/unit/test_repositories/...` | Repository tests | 300 |
| `tests/unit/test_services/...` | Service tests | 300 |
| `ARCHITECTURE.md` | Architecture documentation | 500 |

### 5.2 Files to Delete

| File | Reason |
|------|--------|
| `plexpy/db/datatables.py` | Replaced by querybuilder.py |
| `plexpy/db/database.py` | Replaced by Advanced Alchemy |
| `plexpy/db/datafactory.py` | Replaced by services/ |
| `plexpy/db/queries/raw_pg.py` | Replaced by repositories |
| `plexpy/web/old_api.py` | Replaced by api2.py |

### 5.3 Files to Rewrite

| File | Changes |
|------|---------|
| `plexpy/web/api2.py` | Replace datafactory calls with services |
| `plexpy/web/webserve.py` | Replace datafactory calls with services |
| `plexpy/services/users.py` | Rewrite with new pattern |
| `plexpy/services/exporter.py` | Rewrite with new pattern |
| `plexpy/services/libraries.py` | Rewrite with new pattern |

---

## 6. Testing Strategy

### 6.1 Test Pyramid

```
        /\
       /  \          Integration Tests
      /____\         (API, Database)
     /      \
    /        \       Unit Tests
   /__________\      (Repositories, Services)
  /            \
 /              \    E2E Tests
/________________\   (Full workflows)
```

### 6.2 Coverage Targets

| Test Type | Target | Purpose |
|-----------|--------|---------|
| Unit Tests | 80% | Fast feedback |
| Integration Tests | 60% | Database correctness |
| E2E Tests | 40% | Critical paths |

### 6.3 Critical Test Cases

1. **Repository Tests**
   - CRUD operations
   - Filtering with all operators
   - Pagination correctness
   - Ordering correctness
   - Search functionality

2. **Service Tests**
   - Business logic
   - Response formatting
   - Error handling
   - Data transformation

3. **API Tests**
   - Request validation
   - Response format
   - Authentication/authorization
   - Error responses

---

## 7. Breaking Changes

### 7.1 API Changes

| Old Endpoint | New Endpoint | Notes |
|--------------|---------------|-------|
| `GET /api/v2/history/data` | `GET /api/v2/history` | Same params, different response format |
| `POST /api/v2/update_metadata` | `POST /api/v2/metadata/{id}` | RESTful pattern |

### 7.2 Response Format Changes

**Before (Legacy)**
```json
{
  "result": [...],
  "draw": 1,
  "filteredCount": 100,
  "totalCount": 500
}
```

**After (Modern)**
```json
{
  "draw": 1,
  "recordsTotal": 500,
  "recordsFiltered": 100,
  "data": [...]
}
```

### 7.3 Parameter Changes

| Old Parameter | New Parameter | Notes |
|---------------|---------------|-------|
| `json_data` | `params` | Structured request body |
| `start` | `offset` | Consistent naming |
| `length` | `limit` | Consistent naming |

### 7.4 Migration Guide

```python
# Old usage
result = DataFactory().get_datatables_history(
    kwargs={'json_data': request.json}
)

# New usage
service = HistoryService(...)
result = await service.get_history_datatable(
    params=DataTableParams(**request.json)
)
```

---

## 8. Rollback Plan

### 8.1 Git Strategy

1. Create feature branch: `feature/database-modernization`
2. Commit incrementally with meaningful messages
3. Tag releases: `v2.0.0-rc1`, `v2.0.0-rc2`, `v2.0.0`
4. Main branch always deployable

### 8.2 Database Migrations

1. No schema changes required (same tables, same columns)
2. Only code migration (no data migration)
3. Zero-downtime deployment possible

### 8.3 Rollback Steps

```bash
# If critical bug found:
git checkout main
git revert <commit-hash>
pip install -r requirements.txt  # Restore old deps
```

---

## 9. Timeline

### Week 1: Foundation (COMPLETED)
- [x] Add dependencies (advanced-alchemy, pydantic, pytest, factory-boy, httpx)
- [x] Create repository base (ExtendedRepository, DataTableQueryBuilder)
- [x] Create DataTables query builder
- [x] Create DTOs (history, users, libraries, notifications, newsletters, sessions, lookups)
- [x] Create service layer base (BaseService, RepositoryService)

### Week 2: Model Enhancement
- [ ] Add hybrid properties (duration, percent_complete)
- [ ] Add table indexes
- [ ] Create DataTransferObjects for all models

### Week 3: Repository Implementation
- [ ] Implement history repositories
- [ ] Implement user repositories
- [ ] Implement notification repositories

### Week 4: Service Migration
- [ ] Migrate history service
- [ ] Migrate users service
- [ ] Migrate other services

### Week 5: Web Layer
- [ ] Update API endpoints
- [ ] Update webserve handlers
- [ ] Remove legacy imports

### Week 6: Testing & Documentation
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Update documentation

---

## 10. Success Criteria

### Functional
- [ ] All existing features work identically
- [ ] No data loss
- [ ] Same performance or better

### Technical
- [ ] 80% unit test coverage
- [ ] Type hints on 100% of public APIs
- [ ] No legacy patterns in new code

### Process
- [ ] CI/CD passes
- [ ] Code reviewed
- [ ] Documentation updated

---

## Appendix A: Technology References

- [Advanced Alchemy Documentation](https://alchemy-docs.litestar.dev/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Factory Boy Documentation](https://factoryboy.readthedocs.io/)

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **Repository** | Pattern for abstracting database access |
| **Service Layer** | Pattern for business logic abstraction |
| **DTO** | Data Transfer Object |
| **Hybrid Property** | SQLAlchemy property with Python and SQL expressions |
| **DataTables** | jQuery plugin for interactive tables |

---

**Document Version**: 1.0
**Last Updated**: 2026-02-08
**Status**: Draft - Awaiting Approval
