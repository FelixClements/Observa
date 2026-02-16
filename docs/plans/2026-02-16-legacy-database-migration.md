# Legacy Database Patterns Modernization Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Migrate remaining legacy database patterns (datatables.py, datafactory.py, database.py) to use the Advanced Alchemy repository pattern.

**Architecture:** Replace raw SQL string building with SQLAlchemy 2.0 ORM queries via repository classes. Use the existing repository infrastructure created in Sprint 3.

**Tech Stack:** SQLAlchemy 2.0, Advanced Alchemy, Python 3.12+

---

## Background

The modernization plan identified these legacy database files that need migration:

1. **plexpy/db/datatables.py** - Raw SQL string building with manual parameter binding
2. **plexpy/db/datafactory.py** - Complex aggregation queries using SQLAlchemy ORM but legacy patterns
3. **plexpy/db/database.py** - Legacy wrapper with raw SQL execution

The repository layer (`plexpy/db/repository/`) already exists with:
- `async_base.py` - AdvancedAsyncRepository base class
- `users.py`, `history.py`, `notifications.py`, `libraries.py`, `sessions.py`, etc.

---

## Task 1: Migrate datatables.py to Repository Pattern

**Files:**
- Modify: `plexpy/db/datatables.py`
- Reference: `plexpy/db/repository/` for existing patterns

### Step 1: Analyze datatables.py methods

Read the full file to understand all query patterns:

```bash
# Get full file to understand all methods
wc -l plexpy/db/datatables.py
```

### Step 2: Identify migration candidates

The DataTables class has these key methods:
- `_bind_params()` - Manual parameter binding (can be removed)
- `_select()` - Raw SQL execution (replace with repository)
- `ssp_query()` - Main DataTables server-side processing (migrate to repository)

### Step 3: Replace with repository calls

Instead of:
```python
query = "SELECT * FROM sessions WHERE user_id = ?"
query, params = self._bind_params(query, [user_id])
result = connection.execute(text(query), params)
```

Use:
```python
from plexpy.db.repository.sessions import SessionRepository
from plexpy.db.session import session_scope

async def get_sessions(user_id: int):
    async with session_scope() as db_session:
        repo = SessionRepository(session=db_session)
        return await repo.list(Session.user_id == user_id)
```

### Step 4: Keep backward compatibility

The datatables.py endpoints are called from web handlers. Either:
- Option A: Migrate callers to use repositories directly
- Option B: Keep datatables.py as thin wrapper calling repositories

**Recommendation:** Option B for gradual migration.

---

## Task 2: Migrate datafactory.py to Service Pattern

**Files:**
- Modify: `plexpy/db/datafactory.py`
- Reference: `plexpy/services/` for existing service patterns

### Step 1: Analyze datafactory.py methods

Read the file to understand all methods:
- Uses SQLAlchemy ORM already
- Has complex aggregation queries
- Already has `_config()` helper for DI

### Step 2: Identify which methods to migrate

Methods that should use repositories:
- `get_history()` - Use SessionHistoryRepository
- `get_users()` - Use UserRepository  
- `get_libraries()` - Use LibraryRepository
- etc.

### Step 3: Add repository calls

Instead of:
```python
from plexpy.db.models import SessionHistory
from plexpy.db.session import session_scope

def get_history(self):
    with session_scope() as db_session:
        return db_session.query(SessionHistory).all()
```

Use:
```python
from plexpy.db.repository.history import SessionHistoryRepository

def get_history(self):
    with session_scope() as db_session:
        repo = SessionHistoryRepository(session=db_session)
        return await repo.list()
```

### Step 4: Keep backward compatibility

datafactory.py is used throughout the codebase. Migrate incrementally.

---

## Task 3: Deprecate database.py

**Files:**
- Modify: `plexpy/db/database.py`
- Reference: `plexpy/db/repository/` patterns

### Step 1: Analyze database.py usage

The `MonitorDatabase` class provides:
- `action()` - Execute raw SQL
- `select()` - Execute raw SELECT
- Table reflection

### Step 2: Add deprecation warnings

```python
import warnings

class MonitorDatabase:
    def __init__(self, engine=None):
        warnings.warn(
            "MonitorDatabase is deprecated. Use repositories instead.",
            DeprecationWarning,
            stacklevel=2
        )
        ...
```

### Step 3: Redirect to repositories

For code that still uses MonitorDatabase, it should work but log warnings.

---

## Task 4: Verify No Breaking Changes

**Files:**
- Test: `tests/` existing tests should pass

### Step 1: Run existing tests

```bash
pytest tests/ -v --tb=short
```

### Step 2: Fix any failures

If tests fail, fix the implementation (not the tests).

---

## Implementation Order

1. First: Analyze each file completely
2. Second: Add repository methods where gaps exist
3. Third: Update datatables.py to use repositories
4. Fourth: Update datafactory.py to use repositories
5. Fifth: Add deprecation warnings to database.py
6. Sixth: Run tests and verify

---

## Key Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `plexpy/db/datatables.py` | Modify | Replace raw SQL with repository calls |
| `plexpy/db/datafactory.py` | Modify | Replace ORM queries with repository calls |
| `plexpy/db/database.py` | Modify | Add deprecation warnings |
| `plexpy/db/repository/*.py` | Create | Add missing repository methods as needed |

---

## Success Criteria

- [ ] All datatables.py queries use repositories
- [ ] All datafactory.py methods use repositories or services
- [ ] database.py has deprecation warnings
- [ ] All existing tests pass
- [ ] No breaking changes to API consumers
