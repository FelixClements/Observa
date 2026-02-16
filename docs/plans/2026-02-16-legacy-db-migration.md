# Observa Modernization - Legacy Database Methods Migration Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Migrate the remaining legacy methods in datafactory.py to use SQLAlchemy repositories instead of string SQL and deprecated datatables.

**Status:** PARTIALLY COMPLETED - Feb 16, 2026
- ✅ get_notification_log() - Migrated to NotifyLogRepository
- ✅ get_newsletter_log() - Migrated to NewsletterLogRepository
- ✅ get_total_duration() - Migrated to SQLAlchemy
- ✅ delete_notification_log() - Removed raw_pg.vacuum()
- ✅ delete_newsletter_log() - Removed raw_pg.vacuum()
- ⏳ get_datatables_history() - Complex method, deferred

**Architecture:** Replace direct string SQL queries and datatables.DataTables() calls with SQLAlchemy repository methods. The repositories already have most methods needed - we just need to wire them up in datafactory.py.

**Tech Stack:** Python 3.12+, SQLAlchemy 2.0, Advanced Alchemy, pytest

---

## Completed Tasks ✅

### Task 2: Migrate get_notification_log() to NotifyLogRepository
**Status:** ✅ COMPLETED

- Modified `plexpy/db/datafactory.py:3157-3223`
- Replaced datatables.DataTables().ssp_query() with NotifyLogRepository.datatable_query()
- Uses DataTableParams to map legacy parameters

### Task 3: Migrate get_newsletter_log() to NewsletterLogRepository
**Status:** ✅ COMPLETED

- Modified `plexpy/db/datafactory.py:3235-3293`
- Replaced datatables.DataTables().ssp_query() with NewsletterLogRepository.datatable_query()
- Uses DataTableParams to map legacy parameters

### Task 4: Migrate get_total_duration() to SQLAlchemy
**Status:** ✅ COMPLETED

- Modified `plexpy/db/datafactory.py:2468-2515`
- Replaced raw_pg.fetch_total_duration() with SQLAlchemy select() + func.sum()
- Uses proper JOINs with SessionHistoryMetadata and SessionHistoryMediaInfo

### Task 5: Migrate delete_notification_log()
**Status:** ✅ COMPLETED

- Modified `plexpy/db/datafactory.py:3219-3229`
- Removed raw_pg.vacuum() call (already used SQLAlchemy delete)

### Task 6: Migrate delete_newsletter_log()
**Status:** ✅ COMPLETED

- Modified `plexpy/db/datafactory.py:3285-3294`
- Removed raw_pg.vacuum() call (already used SQLAlchemy delete)

---

## Remaining Tasks ⏳

## Task 1: Migrate get_datatables_history() to SessionHistoryRepository

**Files:**
- Modify: `plexpy/db/datafactory.py:129-458` (get_datatables_history method)
- Reference: `plexpy/db/repository/history.py:143` (datatable_query method)
- Test: `tests/unit/test_repositories/test_history.py`

**Step 1: Write the test**

First, verify current behavior by checking what parameters get_datatables_history accepts:

```python
# Test should verify get_datatables_history returns same format as before
# Run: pytest tests/ -k "test_datatables" -v
# Expected: Existing tests pass
```

**Step 2: Examine current implementation**

Read `plexpy/db/datafactory.py` lines 129-458 to understand:
- What parameters are passed (kwargs, custom_where, grouping, include_activity)
- What format the result returns
- How it uses datatables.DataTables()

**Step 3: Implement migration**

Replace the datatables.DataTables() call with repository:

```python
# OLD (lines ~129-200):
from plexpy.db import datatables
dt = datatables.DataTables()
result = dt.ssp_query(...)

# NEW:
from plexpy.db.repository.history import SessionHistoryRepository
from plexpy.db.repository.base import DataTableParams

with session_scope() as db_session:
    repo = SessionHistoryRepository(session=db_session)
    params = DataTableParams(
        draw=kwargs.get('draw', 1),
        start=kwargs.get('start', 0),
        length=kwargs.get('length', 25),
        search_value=kwargs.get('search[value]', ''),
        # ... other params
    )
    result = repo.datatable_query(params, custom_where=custom_where, grouping=grouping)
```

**Step 4: Run tests to verify**

```bash
cd /workspace/Observa
pytest tests/ -v --tb=short 2>&1 | head -50
```

**Step 5: Commit**

```bash
git add plexpy/db/datafactory.py
git commit -m "refactor: migrate get_datatables_history to use SessionHistoryRepository"
```

---

## Task 2: Migrate get_notification_log() to NotifyLogRepository

**Files:**
- Modify: `plexpy/db/datafactory.py:3157-3223` (get_notification_log method)
- Reference: `plexpy/db/repository/notifications.py:92` (datatable_query)

**Step 1: Examine current implementation**

Read lines 3157-3223 to understand parameters and return format.

**Step 2: Implement migration**

Replace datatables.DataTables() with NotifyLogRepository.datatable_query():

```python
# OLD:
from plexpy.db import datatables
dt = datatables.DataTables()
result = dt.ssp_query(...)

# NEW:
from plexpy.db.repository.notifications import NotifyLogRepository
from plexpy.db.repository.base import DataTableParams

with session_scope() as db_session:
    repo = NotifyLogRepository(session=db_session)
    params = DataTableParams(...)
    result = repo.datatable_query(params)
```

**Step 3: Run tests**

```bash
pytest tests/ -v --tb=short 2>&1 | head -50
```

**Step 4: Commit**

```bash
git add plexpy/db/datafactory.py
git commit -m "refactor: migrate get_notification_log to use NotifyLogRepository"
```

---

## Task 3: Migrate get_newsletter_log() to NewsletterLogRepository

**Files:**
- Modify: `plexpy/db/datafactory.py:3235-3294` (get_newsletter_log method)
- Reference: `plexpy/db/repository/newsletters.py:130` (datatable_query)

**Step 1: Examine current implementation**

Read lines 3235-3294.

**Step 2: Implement migration**

Replace datatables.DataTables() with NewsletterLogRepository.datatable_query().

**Step 3: Run tests and commit**

```bash
pytest tests/ -v --tb=short 2>&1 | head -50
git add plexpy/db/datafactory.py
git commit -m "refactor: migrate get_newsletter_log to use NewsletterLogRepository"
```

---

## Task 4: Migrate get_total_duration() to SQLAlchemy

**Files:**
- Modify: `plexpy/db/datafactory.py:2468-2476` (get_total_duration method)
- Reference: `plexpy/db/repository/history.py:76-94` (get_total_duration_* methods)
- Modify: `plexpy/db/queries/raw_pg.py:23-38` (fetch_total_duration)

**Step 1: Examine current implementation**

Read lines 2468-2476 and raw_pg.py:23-38.

**Step 2: Implement migration**

The existing repository has:
- `get_total_duration_by_user(user_id)`
- `get_total_duration_by_library(section_id)`
- `get_total_duration_by_media_type(media_type)`

Create a generic method or use func.sum() directly:

```python
# In repository (if needed):
async def get_total_duration(self, custom_where=None) -> int:
    from sqlalchemy import func, case
    from plexpy.db.models import SessionHistory, SessionHistoryMetadata, SessionHistoryMediaInfo
    
    query = (
        select(
            func.sum(
                case(
                    (SessionHistory.stopped > 0,
                     SessionHistory.stopped - SessionHistory.started),
                    else_=0
                )
            ) - func.coalesce(func.sum(SessionHistory.paused_counter), 0)
        )
        .select_from(SessionHistory)
        .join(SessionHistoryMetadata)
        .join(SessionHistoryMediaInfo)
    )
    if custom_where:
        query = query.where(*custom_where)
    
    result = await self.session.execute(query)
    return result.scalar() or 0
```

**Step 3: Update datafactory.py to use repository**

**Step 4: Run tests and commit**

---

## Task 5: Migrate delete_notification_log() to NotifyLogRepository.delete_old_logs()

**Files:**
- Modify: `plexpy/db/datafactory.py:3224-3234` (delete_notification_log method)
- Reference: `plexpy/db/repository/notifications.py:87` (delete_old_logs)

**Step 1: Examine current implementation**

Read lines 3224-3234 - it calls `raw_pg.vacuum()`.

**Step 2: Implement migration**

Replace vacuum() with repository delete_old_logs():

```python
# OLD:
raw_pg.vacuum()

# NEW:
with session_scope() as db_session:
    repo = NotifyLogRepository(session=db_session)
    # Get timestamp for 30 days ago (or whatever the original logic was)
    import time
    timestamp = int(time.time()) - (30 * 24 * 60 * 60)
    repo.delete_old_logs(timestamp)
```

**Step 3: Run tests and commit**

---

## Task 6: Migrate delete_newsletter_log() to NewsletterLogRepository.delete_old_logs()

**Files:**
- Modify: `plexpy/db/datafactory.py:3295-3305` (delete_newsletter_log method)
- Reference: `plexpy/db/repository/newsletters.py:124` (delete_old_logs)

**Step 1-3: Same pattern as Task 5**

**Step 4: Commit**

```bash
git add plexpy/db/datafactory.py
git commit -m "refactor: migrate delete_newsletter_log to use NewsletterLogRepository"
```

---

## Task 7: Final Verification

**Step 1: Run full test suite**

```bash
cd /workspace/Observa
pytest tests/ -v --tb=short 2>&1 | tail -30
```

**Step 2: Check for any remaining legacy imports**

```bash
grep -r "from plexpy.db import datatables" plexpy/ --include="*.py"
grep -r "raw_pg\." plexpy/db/datafactory.py
```

**Step 3: Commit final changes**

```bash
git add -A
git commit -m "refactor: complete legacy database method migrations"
```

---

## Success Criteria

- [ ] All 6 methods migrated to use SQLAlchemy repositories
- [ ] No remaining calls to datatables.DataTables() in datafactory.py
- [ ] No remaining calls to raw_pg.vacuum() in datafactory.py
- [ ] All existing tests pass
- [ ] Code runs without deprecation warnings for these methods
