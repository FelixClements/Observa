# Observa Modernization Plan - Consolidated

> **Consolidated from**: MODERNIZATION_2026.md, docs-readme.md, plan-update.md, update-agents-md.md
> **Last Updated**: February 16, 2026
> **Status**: In Progress - Sprint 3 Complete

---

## TL;DR

> **Objective**: Complete the modernization of Observa (fork of Tautulli) from 2014-era Python patterns to 2026 industry standards.
>
> **Key Deliverables**:
> - Remove Python 2 compatibility layer
> - Upgrade dependencies (configobj → Pydantic, requests → httpx, simplejson → orjson)
> - Migrate database layer to Advanced Alchemy + Service pattern
> - Complete test infrastructure setup
> - Update AGENTS.md and documentation
>
> **Timeline**: 6-8 weeks
> **Breaking Changes**: Yes (documented in Section 8)
> **Risk Level**: Medium

---

## 1. Current State Assessment

### 1.1 Already Modernized ✅

| Area | Status | Details |
|------|--------|---------|
| **Database Engine** | ✅ Done | SQLAlchemy 2.0.36 in `plexpy/db/engine.py` |
| **Models** | ✅ Done | SQLAlchemy 2.0 declarative in `plexpy/db/models/` |
| **Repository Pattern** | ✅ Done | Implemented in `plexpy/db/repository/` |
| **Migrations** | ✅ Done | Alembic configured with `alembic.ini` |
| **PostgreSQL** | ✅ Done | `psycopg[binary]==3.2.4` in requirements.txt |
| **Entry Point** | ✅ Done | `Tautulli.py` as main entry |
| **DTOs (partial)** | 🔄 Partial | Pydantic DTOs in `plexpy/db/dto/` |

### 1.2 Completed in Sprint 1 ✅

| Area | Status | Details |
|------|--------|---------|
| **Python 2 compat (future)** | ✅ Done | Removed `future==1.0.0` from requirements.txt |
| **Python 2 compat (IPy)** | ✅ Done | Removed `IPy==1.01` from requirements.txt |
| **itertools replacement** | ✅ Done | Replaced `future.moves.itertools` with builtins in helpers.py |
| **IPy removal** | ✅ Done | Replaced with built-in `ipaddress` module |
| **httpx migration** | ✅ Done | Created `plexpy/util/http.py` wrapper, updated 5 files |
| **orjson added** | ✅ Done | Added `orjson>=3.9` to requirements.txt |
| **structlog added** | ✅ Done | Added `structlog>=24.0` to requirements.txt |
| **pydantic-settings added** | ✅ Done | Added `pydantic-settings>=2.0` to requirements.txt |
| **Repository layer** | ✅ Done | Created async_base.py + 4 new repositories |
| **configobj removed** | ✅ Done | Replaced with configparser in core.py and settings.py |
| **Testing infrastructure** | ✅ Done | Created pyproject.toml, conftest.py, test structure |

### 1.3 Completed in Sprint 2 ✅

| Area | Status | Details |
|------|--------|---------|
| **SessionHistoryRepository extended** | ✅ Done | Added aggregation methods, count methods, filter methods |
| **NotifyLogRepository extended** | ✅ Done | Added filter methods, delete_old_logs |
| **NewsletterLogRepository extended** | ✅ Done | Added filter methods, delete_old_logs |

### 1.4 Completed in Sprint 3 ✅

| Area | Status | Details |
|------|--------|---------|
| **Web config DI** | ✅ Done | Created `plexpy/web/dependencies.py`, migrated 6 files |
| **Integrations config DI** | ✅ Done | Created `plexpy/integrations/dependencies.py`, migrated 4 files |
| **api2.py migrated** | ✅ Done | 53 plexpy.CONFIG → _get_config() |
| **webserve.py migrated** | ✅ Done | 109 plexpy.CONFIG → _get_config() |
| **webauth.py migrated** | ✅ Done | 16 plexpy.CONFIG → _get_config() |
| **web_socket.py migrated** | ✅ Done | 12 plexpy.CONFIG → _get_config() |
| **webstart.py migrated** | ✅ Done | 12 plexpy.CONFIG → _get_config() |
| **session.py migrated** | ✅ Done | 1 plexpy.CONFIG → _get_config() |
| **plex.py migrated** | ✅ Done | 2 plexpy.CONFIG → _get_config() |
| **plextv.py migrated** | ✅ Done | 17 plexpy.CONFIG → _get_config() |
| **pmsconnect.py migrated** | ✅ Done | 8 plexpy.CONFIG → _get_config() |
| **http_handler.py migrated** | ✅ Done | 2 plexpy.CONFIG → _get_config() |
| **Test factories** | ✅ Done | Created extensive factories in `tests/factories/` |
| **Repository tests** | ✅ Done | Created `tests/unit/test_repositories/test_users.py` |
| **Service tests** | ✅ Done | Created `tests/unit/test_services/test_users.py` |

### 1.5 Still Legacy (To Do) ❌

#### Python 2/3 Compatibility (REMOVE)
- [x] `future==1.0.0` in `requirements.txt` (line 15) ✅ DONE
- [x] `from future.moves.itertools import islice, zip_longest` in `plexpy/util/helpers.py` (line 28) ✅ DONE
- [x] `from IPy import IP` in `plexpy/util/helpers.py` (line 33) ✅ DONE
- [x] `from __future__ import annotations` in 8 files: ⏭️ SKIPPED (harmless in Python 3.12+)

#### Outdated Libraries (REPLACE)
- [x] `configobj==5.0.9` → configparser (stdlib) ✅ DONE (Feb 15, 2026)
- [x] `requests==2.32.4` → httpx (async) ✅ DONE
- [x] `simplejson==3.19.3` → orjson ✅ DONE (already using stdlib json)
- [x] Add: `structlog` or `loguru` for structured logging ✅ DONE
- [x] Add: `pydantic-settings` for config validation ✅ DONE

#### Global State Abuse (REFACTOR)
- [x] Config dependency injection infrastructure ✅ DONE (Feb 15, 2026)
  - Created `plexpy/config/dependencies.py` with `get_config()`, `set_config()`, `get_config_optional()`
  - Integrated `set_config()` into `plexpy/app/bootstrap.py`
- [x] Refactored db files to use config DI ✅ DONE
  - `plexpy/db/datafactory.py` - added _config() helper
  - `plexpy/db/engine.py` - added _get_config() helper
  - `plexpy/db/maintenance.py` - added _get_config() helper
- [x] Refactored util files to use config DI ✅ DONE
  - `plexpy/util/request.py` - added _get_config() helper
  - `plexpy/util/logger.py` - added _get_config() helper
- [x] Refactored services files to use config DI ✅ DONE (Feb 15, 2026)
  - `plexpy/services/users.py` - added _get_config() helper
  - `plexpy/services/libraries.py` - added _get_config() helper  
  - `plexpy/services/graphs.py` - added _get_config() helper
  - `plexpy/services/versioncheck.py` - added _get_config() helper
  - `plexpy/services/activity_handler.py` - added _get_config() helper
  - `plexpy/services/notification_handler.py` - added _get_config() helper
  - `plexpy/services/notifiers.py` - added _get_config() helper
  - `plexpy/services/newsletters.py` - added _get_config() helper
  - `plexpy/services/newsletter_handler.py` - added _get_config() helper
  - `plexpy/services/activity_processor.py` - added _get_config() helper
  - `plexpy/services/activity_pinger.py` - added _get_config() helper
  - `plexpy/services/log_reader.py` - added _get_config() helper
  - `plexpy/services/exporter.py` - added _get_config() helper
- [x] Refactored web files to use config DI ✅ DONE (Feb 16, 2026)
  - `plexpy/web/dependencies.py` - created
  - `plexpy/web/api2.py` - added _get_config() helper
  - `plexpy/web/webserve.py` - added _get_config() helper
  - `plexpy/web/webauth.py` - added _get_config() helper
  - `plexpy/web/web_socket.py` - added _get_config() helper
  - `plexpy/web/webstart.py` - added _get_config() helper
  - `plexpy/web/session.py` - added _get_config() helper
- [x] Refactored integrations files to use config DI ✅ DONE (Feb 16, 2026)
  - `plexpy/integrations/dependencies.py` - created
  - `plexpy/integrations/plex.py` - added _get_config() helper
  - `plexpy/integrations/plextv.py` - added _get_config() helper
  - `plexpy/integrations/pmsconnect.py` - added _get_config() helper
  - `plexpy/integrations/http_handler.py` - added _get_config() helper
- [ ] Module-level side effects in bootstrap

#### Legacy Database Patterns (MIGRATE)
- [x] Repository layer - new repositories created ✅ DONE
  - `plexpy/db/repository/async_base.py` - AdvancedAsyncRepository base
  - `plexpy/db/repository/newsletters.py` - Newsletter, NewsletterLog
  - `plexpy/db/repository/exports.py` - Export
  - `plexpy/db/repository/mobile.py` - MobileDevice
  - `plexpy/db/repository/lookups.py` - 6 lookup models
- [x] Extended SessionHistoryRepository with aggregation methods ✅ DONE
- [x] Extended NotifyLogRepository with filter/delete methods ✅ DONE
- [x] Extended NewsletterLogRepository with filter/delete methods ✅ DONE
- [x] Added datatable_query support to NotifyLogRepository ✅ DONE (Feb 16, 2026)
- [x] Added datatable_query support to NewsletterLogRepository ✅ DONE (Feb 16, 2026)
- [x] Added deprecation warnings to database.py ✅ DONE (Feb 16, 2026)
- [ ] `plexpy/db/datatables.py` → Use existing Repository.datatable_query()
- [ ] `plexpy/db/datafactory.py` → Migrate complex aggregation queries to repositories
- [ ] `plexpy/db/database.py` → Advanced Alchemy
- [ ] String-based SQL queries → ORM/Core

#### Legacy Web Framework
- [ ] CherryPy class-based handlers (consider FastAPI migration path)
- [ ] Monkey-patching cookies (`Morsel._reserved` in `plexpy/web/webauth.py`)
- [x] No dependency injection ✅ DONE (Feb 16, 2026)

#### Type Safety
- [ ] Minimal type hints - add comprehensive coverage
- [ ] No runtime validation - add Pydantic models
- [ ] Legacy config typing patterns

---

## 2. Target Tech Stack

### 2.1 Technology Stack

| Component | Current | Target |
|-----------|---------|--------|
| **Language** | Python 3.14+ | ✅ (unchanged) |
| **Web** | CherryPy | CherryPy (current) → FastAPI (future) |
| **DB** | SQLAlchemy 2.0 + Alembic + PostgreSQL | ✅ (already done) |
| **ORM Extensions** | Basic | Advanced Alchemy |
| **Config** | configobj | Pydantic Settings |
| **HTTP** | requests | httpx (async) |
| **JSON** | simplejson | orjson |
| **Logging** | standard logging | structlog |
| **Testing** | pytest (partial) | pytest + pytest-asyncio + factory-boy |
| **Types** | Minimal | Full coverage (pyright strict) |
| **DTOs** | Partial | Pydantic 2.x |

### 2.2 Dependency Changes

```diff
requirements.txt
@@
- future==1.0.0
- configobj==5.0.9
- requests==2.32.4
- simplejson==3.19.3
- IPy==1.01

+ advanced-alchemy>=0.10.0
+ pydantic>=2.0
+ pydantic-settings>=2.0
+ httpx>=0.27
+ orjson>=3.9
+ structlog>=24.0
+ pytest>=8.0
+ pytest-asyncio>=0.23
+ factory-boy>=3.3
```

---

## 3. Why Advanced Alchemy

### 3.1 What is Advanced Alchemy?

Advanced Alchemy is a production-grade library from the Litestar team that provides:
- **Type-safe repositories** with full generic support
- **Built-in filtering, pagination, sorting** via filter classes
- **Async support** out of the box
- **Bulk operations** optimized for performance
- **5,000+ GitHub stars** and active maintenance

### 3.2 Comparison

| Pattern | Legacy Code | Advanced Alchemy |
|---------|-------------|------------------|
| **CRUD** | 50 lines per model | 0 lines (automatic) |
| **Pagination** | Manual offset/limit | `LimitOffset(limit=10, offset=0)` |
| **Filtering** | String-based where | `.list(Model.field == value)` |
| **Sorting** | Manual ORDER BY | `OrderBy(field_name="created", sort_order="desc")` |
| **Search** | Manual LIKE query | `SearchFilter(field_name="title", value="query")` |
| **Get total + results** | Two queries | `.list_and_count(*filters)` |
| **Bulk Create** | Loop + add | `.add_many([...])` |
| **Type Safety** | Partial | Full generics |

### 3.3 DataTables Example

**Before (datatables.py - string SQL):**
```python
query = 'SELECT * FROM sessions %s %s' % (where, order)
query = query.replace('?', f":param_{i}", 1)
```

**After (Advanced Alchemy - 3 lines):**
```python
filters = [
    LimitOffset(limit=params.length, offset=params.start),
    OrderBy(field_name="started", sort_order="desc"),
    SearchFilter(field_name="title", value=params.search) if params.search else None,
]
results, total = await repo.list_and_count(*[f for f in filters if f])
```

### 3.4 Standard Database Access Pattern

**This is the ONE pattern to use for ALL database queries:**

```python
from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.filters import LimitOffset, OrderBy, SearchFilter
from sqlalchemy import select, func  # Only for aggregations

class SessionHistoryRepository(SQLAlchemyAsyncRepository[SessionHistory]):
    model_type = SessionHistory

# === SIMPLE QUERIES (most common) ===

# Get list with pagination, sorting, search
async def get_history(session: AsyncSession, params: DataTableParams):
    repo = SessionHistoryRepository(session=session)
    results, total = await repo.list_and_count(
        SessionHistory.media_type == 'movie',  # filter
        OrderBy(field_name="started", sort_order="desc"),  # sort
        LimitOffset(limit=10, offset=0),  # pagination
        load=[selectinload(SessionHistory.metadata)]  # eager load
    )
    return results

# Get single by ID
async def get_by_id(session: AsyncSession, id: int):
    repo = SessionHistoryRepository(session=session)
    return await repo.get(id)

# Create new
async def create(session: AsyncSession, data: dict):
    repo = SessionHistoryRepository(session=session)
    return await repo.add(SessionHistory(**data))

# Update
async def update(session: AsyncSession, id: int, data: dict):
    repo = SessionHistoryRepository(session=session)
    return await repo.update(id, data)

# Delete
async def delete(session: AsyncSession, id: int):
    repo = SessionHistoryRepository(session=session)
    return await repo.delete(id)

# === AGGREGATIONS (for stats like "top 5 movies") ===

async def get_top_movies(session: AsyncSession, limit: int = 5):
    query = (
        select(
            SessionHistory.reference_id,
            SessionHistoryMetadata.title,
            func.count(SessionHistory.reference_id).label('play_count')
        )
        .join(SessionHistoryMetadata)
        .where(SessionHistory.media_type == 'movie')
        .group_by(SessionHistory.reference_id, SessionHistoryMetadata.title)
        .order_by(func.count(SessionHistory.reference_id).desc())
        .limit(limit)
    )
    result = await session.execute(query)
    return result.all()
```

**Rule**: If it's not an aggregation, use `.list_and_count()` with filters. Only use raw `select()` for aggregations.

---

## 4. Implementation Roadmap

### Phase 4.1: Remove Python 2 Compatibility (Week 1)

- [ ] 1.1 Remove `future==1.0.0` from `requirements.txt`
- [ ] 1.2 Replace `from future.moves.itertools import islice, zip_longest` with built-in `itertools.islice` and `itertools.zip_longest` in `plexpy/util/helpers.py`
- [ ] 1.3 Remove `from __future__ import annotations` from 8 db files (unnecessary in Python 3.15+)
- [ ] 1.4 Replace `IPy==1.01` with built-in `ipaddress` module in `plexpy/util/helpers.py`
- [ ] 1.5 Verify: `python -c "from itertools import islice, zip_longest; from ipaddress import ip_network"` works

### Phase 4.2: Dependency Upgrades (Week 1-2)

- [ ] 2.1 Replace `configobj` with Pydantic Settings
- [ ] 2.2 Replace `requests` with `httpx` (async)
- [ ] 2.3 Replace `simplejson` with `orjson`
- [ ] 2.4 Add `structlog` for structured logging
- [ ] 2.5 Add `pydantic-settings` for config validation
- [ ] 2.6 Update `requirements.txt` with modern dependencies

### Phase 4.3: Repository Layer Migration (Week 2-3)

Create the new repository structure:
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

### Phase 4.4: Service Layer Implementation (Week 3-4)

Create service layer structure:
```
plexpy/services/
├── __init__.py
├── base.py              # BaseService with DI
├── history.py           # HistoryService
├── users.py             # UsersService
├── libraries.py         # LibrariesService
├── notifications.py     # NotificationsService
├── newsletters.py       # NewslettersService
├── exporter.py          # ExporterService
└── activity.py          # ActivityService
```

### Phase 4.5: Migrate datatables.py to Repositories (Week 3)

Replace string-based SQL in `datatables.py` with Advanced Alchemy repository methods:
- Use `.list_and_count()` with `LimitOffset` for pagination
- Use `SearchFilter` for search
- Use `OrderBy` for sorting

No custom query builder needed - Advanced Alchemy provides all necessary filters.

### Phase 4.6: Web Layer Update (Week 4-5)

- [ ] Update `plexpy/web/api2.py` to use services
- [ ] Update `plexpy/web/webserve.py` to use services
- [ ] Add dependency injection helpers in `plexpy/web/dependencies.py`

### Phase 4.7: Testing Infrastructure (Week 5-6)

- [x] Add comprehensive pytest configuration ✅ Done
- [x] Create factory fixtures for all models ✅ Done
- [x] Write unit tests for repositories ✅ Done
- [x] Write unit tests for services ✅ Done
- [ ] Write integration tests for API endpoints

### Phase 4.8: Documentation Updates (Week 6)

- [ ] Update `AGENTS.md` to reflect modern stack
- [ ] Update `README.md` with current status
- [ ] Create `ARCHITECTURE.md` if needed

---

## 5. File Change Summary

### 5.1 Files to Create

| File | Purpose | Status |
|------|---------|--------|
| `plexpy/db/repository/base.py` | Extended repository base | ✅ Done |
| `plexpy/db/repository/history.py` | History repositories | ✅ Done |
| `plexpy/db/repository/users.py` | User repositories | ✅ Done |
| `plexpy/db/repository/notifications.py` | Notification repositories | ✅ Done |
| `plexpy/db/repository/libraries.py` | Library repositories | ✅ Done |
| `plexpy/db/repository/sessions.py` | Session repositories | ✅ Done |
| `plexpy/db/repository/newsletters.py` | Newsletter repositories | ✅ Done |
| `plexpy/db/repository/exports.py` | Export repositories | ✅ Done |
| `plexpy/db/repository/mobile.py` | Mobile repositories | ✅ Done |
| `plexpy/db/repository/lookups.py` | Lookup repositories | ✅ Done |
| `plexpy/services/base.py` | Base service class | ✅ Done |
| `plexpy/services/history.py` | History service | ✅ Done |
| `plexpy/services/users.py` | Users service | ✅ Done |
| `plexpy/services/libraries.py` | Libraries service | ✅ Done |
| `plexpy/services/notifications.py` | Notifications service | ✅ Done |
| `plexpy/services/newsletters.py` | Newsletters service | ✅ Done |
| `plexpy/services/exporter.py` | Exporter service | ✅ Done |
| `plexpy/services/activity.py` | Activity service | ✅ Done |
| `pyproject.toml` | Pytest configuration | ✅ Done |
| `tests/conftest.py` | Pytest fixtures | ✅ Done |
| `tests/unit/test_config.py` | Config tests | ✅ Done |
| `tests/factories/*.py` | Test factories | ✅ Done |
| `tests/unit/test_repositories/*.py` | Repository tests | ✅ Done |
| `tests/unit/test_services/*.py` | Service tests | ✅ Done |
| `plexpy/web/dependencies.py` | Web layer config DI | ✅ Done |
| `plexpy/integrations/dependencies.py` | Integrations config DI | ✅ Done |

### 5.2 Files to Delete

| File | Reason |
|------|--------|
| `plexpy/db/datatables.py` | Replaced by Advanced Alchemy repositories (use `.list_and_count()` with filters) |
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
| `AGENTS.md` | Update to modern tech stack |
| `README.md` | Update current status |

---

## 6. Testing Strategy

### 6.1 Test Structure

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
│   └── test_services/
│       ├── __init__.py
│       ├── test_history.py
│       └── test_users.py
└── integration/
    ├── __init__.py
    ├── test_database.py
    └── test_api.py
```

### 6.2 Coverage Targets

| Test Type | Target | Purpose |
|-----------|--------|---------|
| Unit Tests | 80% | Fast feedback |
| Integration Tests | 60% | Database correctness |
| E2E Tests | 40% | Critical paths |

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

## 9. Priority Recommendations

| Priority | Task | Rationale |
|----------|------|-----------|
| **HIGH** | Remove Python 2 compat (`future`, `IPy`, `__future__`) | Unblocks Python 3.15+ features |
| **HIGH** | Replace configobj with Pydantic Settings | Improves type safety |
| **HIGH** | Migrate database layer to Advanced Alchemy | Core modernization |
| **MEDIUM** | Add type hints | Improves maintainability |
| **MEDIUM** | Replace requests with httpx | Enables async |
| **MEDIUM** | Complete test infrastructure | Quality assurance |
| **LOW** | FastAPI migration | Long-term consideration |

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
- [ ] Python 2 compatibility removed
- [ ] All dependencies upgraded

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
- [httpx Documentation](https://www.python-httpx.org/)
- [orjson Documentation](https://github.com/ijl/orjson)
- [structlog Documentation](https://www.structlog.org/)

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

**Document Version**: 1.0 (Consolidated)
**Status**: Draft - Awaiting Approval
