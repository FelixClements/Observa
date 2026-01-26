<!-- Purpose: Define the Phase 0 test harness structure and parity strategy. -->
# Phase 0 Test Harness Design

Goal: establish a minimal, repeatable pytest harness that supports DAL parity tests and future Core/ORM migrations.

## Proposed structure

```
tests/
  conftest.py
  fixtures/
    seed_users.py
    seed_libraries.py
    seed_history.py
  legacy/
    test_legacy_queries.py
  dal/
    test_users_dal.py
    test_libraries_dal.py
    test_history_dal.py
```

## Fixtures

`engine` (in-memory SQLite)
- Scope: function
- Creates `sqlite:///:memory:` engine for fast unit tests.
- Used by DAL tests that do not require on-disk file semantics.

`sqlite_file_engine` (tmp_path)
- Scope: function
- Creates `sqlite:///{tmp_path}/test.db` engine for ORM tests (Phase 3).

`legacy_db` (MonitorDatabase wrapper)
- Scope: function
- Uses a temporary sqlite file and the legacy `MonitorDatabase` to run parity comparisons.

## Seed datasets

Minimal datasets are intentionally small but should exercise joins, filters, and aggregations.

Users
- 1 admin, 1 regular, 1 deleted
- Include `friendly_name` NULL and non-NULL cases

Libraries
- 2 sections with different types (movie, show)
- 1 deleted section

History
- 3 session_history rows across two users and two libraries
- At least one with `paused_counter > 0`, one with `view_offset`, and one with `relayed = 1`
- Matching rows in `session_history_metadata` and `session_history_media_info`

## Parity test strategy

Baseline pattern
- Arrange: seed legacy sqlite using `dbcheck()` schema and minimal seed data.
- Act: run the legacy SQL query and new DAL/Core/ORM query.
- Assert: compare row counts and key fields (ids, rating_key, user_id, section_id).

Priority parity tests (Phase 1)
- Users list and user lookup (users.py)
- Library list and section lookup (libraries.py)
- History list and last-watched queries (datafactory.py)

Performance-sensitive parity tests (Phase 2+)
- History aggregates: total plays, total duration
- Graphs queries for daily/weekly aggregates

## CI considerations

`pytest -q` should pass with no network access and no external services.
All tests must be idempotent and order-independent.
