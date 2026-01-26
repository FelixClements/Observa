Tautulli SQLAlchemy Migration Plan

This plan details phases, sub-phases, and tasks for migrating the Tautulli
codebase from raw sqlite3 usage to SQLAlchemy Core and ORM with Alembic.

Current State Summary
- Raw sqlite3 access is centralized in plexpy/database.py (MonitorDatabase) and
  used across many modules (datafactory, graphs, datatables, users, libraries,
  notifiers, newsletters, notification_handler, mobile_app, exporter, webserve).
- Schema creation and legacy migrations are defined in plexpy/__init__.py in
  dbcheck() via CREATE TABLE and ALTER TABLE statements.
- Import tools (plexivity_import.py, plexwatch_import.py) use sqlite3 directly.
- SQLAlchemy and Alembic are not yet present in dependencies or repo structure.
- There is no project-level tests/ directory; vendored libs include their own
  tests but are not relevant to the app.

Phase 0 - Discovery and Baseline
Goal: Freeze the current schema and query surface to scope later PRs.

Sub-phase 0.1 - Schema inventory
- Extract all table definitions from plexpy/__init__.py dbcheck().
- Record columns, types, defaults, primary keys, and unique constraints.
- Capture implicit relationships (session_history -> metadata/media_info).
- Catalog existing indexes (if any) and target indexes for Phase 4.

Sub-phase 0.2 - Query surface inventory
- Enumerate every raw SQL statement in plexpy/.
- Map queries to owning module and target table(s).
- Categorize as read, write, upsert, delete, or schema touch.
- Identify high-traffic or performance-sensitive queries (history, home stats).
- Include non-DAL entry points that execute SQL (api2.py api_sql, web auth).

Sub-phase 0.3 - Test harness design
- Define a new tests/ structure with fixtures for in-memory SQLite.
- Plan parity tests comparing legacy SQL results to new DAL results.
- Identify minimal seed datasets that exercise joins, filters, and groupings.

Phase 1 - DAL (Data Access Layer)
Goal: Introduce a DAL that wraps SQL access without behavior changes.

Deliverables
- New plexpy/db/ package with DAL modules per domain.
- Central error type TautulliDBError and consistent logging.
- DAL uses sqlite3 under the hood but isolates SQL from callers.
- Tests for each DAL module with parity checks where feasible.

Sub-phase 1.1 - DAL skeleton and error handling
- Add plexpy/db/__init__.py and plexpy/db/errors.py (or add to exceptions.py).
- Create a SQLite executor helper that uses MonitorDatabase internally.
- Provide helper for retries and consistent error wrapping.

Sub-phase 1.2 - Per-module DAL migrations (small PRs)
- PR: users -> DAL + tests
- PR: libraries -> DAL + tests
- PR: newsletters and notification_handler -> DAL + tests
- PR: mobile_app and exports -> DAL + tests
- PR: graphs -> DAL + tests
- PR: datafactory -> DAL + tests
- PR: datatables query builder -> DAL adapter + tests
- PR: activity_processor -> DAL + tests
- PR: api2 raw SQL path -> DAL wrapper + tests
- PR: webauth and newsletter_handler -> DAL + tests

Testing requirements (Phase 1)
- Add tests/conftest.py with engine fixture using in-memory SQLite.
- Each DAL module has at least one pytest verifying results.
- Add data parity helper to compare legacy SQL vs DAL result sets.

Phase 2 - SQLAlchemy Core (All-or-Nothing)
Goal: Replace all sqlite3 usage with SQLAlchemy Core and Alembic.

Sub-phase 2.1 - Engine and connection layer
- Add SQLAlchemy and Alembic dependencies.
- Create plexpy/db/engine.py with DB URL parsing and engine creation.
- Replace MonitorDatabase with a Core-based executor.
- Update requirements.txt and package/requirements-package.txt as needed for new deps.

Sub-phase 2.2 - Core schema definitions
- Create plexpy/db/schema.py with Table definitions for every existing table.
- Match column types and defaults exactly to current SQLite schema.
- Capture explicit and implicit constraints.

Sub-phase 2.3 - Alembic setup
- Add alembic/ directory and config.
- Generate initial_orm migration that mirrors the current schema exactly.
- Ensure autogenerate yields a non-empty migration file.
- Port dbcheck() ALTER TABLE and data migration logic into Alembic revisions.

Sub-phase 2.4 - Cutover
- Update DAL modules to use SQLAlchemy Core select/insert/update/delete.
- Replace dbcheck() schema management with Alembic usage.
- Ensure legacy sqlite3 usage remains only in import tools if needed.
- Define explicit handling for api2.py api_sql (Core text() or legacy path).
- Decide whether import/merge workflows in plexpy/database.py stay on sqlite3 or migrate to Core.

Testing requirements (Phase 2)
- Update DAL tests to use Core engine fixture.
- Add parity tests for history queries and user/library retrievals.
- Run migration tests that create DB via Alembic and run sample queries.

Phase 3 - SQLAlchemy ORM (Per-Entity)
Goal: Incrementally adopt ORM models where beneficial.

Sub-phase 3.1 - ORM base and models
- Add plexpy/db/orm/base.py for declarative base.
- Define ORM models for each table with relationships.
- Prioritize session_history relationships and users/libraries.

Sub-phase 3.2 - Per-entity migrations (small PRs)
- PR: ORM users (replace DAL implementation)
- PR: ORM libraries
- PR: ORM notifications and newsletters
- PR: ORM history (likely split into read vs write paths)
- PR: ORM lookups and exports

Testing requirements (Phase 3)
- ORM tests use temporary SQLite file: tmp_path / "test.db".
- Parity tests comparing Core vs ORM for same queries.

Phase 4 - Config, Backup, Performance, Docs
Goal: Add DB URL config, safety backups, performance improvements, and docs.

Sub-phase 4.1 - Configurable DB URL
- Add CONFIG key (DB_URL) in plexpy/config.py.
- Support TAUTULLI_DB_URL env override.
- Default to sqlite file URL if unset.
- Ensure Docker/runtime entrypoints honor DB_URL and env overrides.

Sub-phase 4.2 - Backup on first run
- Add plexpy/db/backup_on_first_run.py bootstrap script.
- Create timestamped backup into backups/ at first run.
- Hook into startup flow in plexpy/__init__.py.
- Reuse existing database.make_backup logic to avoid duplicate backup behaviors.

Sub-phase 4.3 - History performance
- Add indexes on session_history.play_date (or started) and user_id.
- Refactor heavy history queries to avoid nested subqueries where possible.
- Add pytest-benchmark for top 3 history queries with <= 5 percent regression.

Sub-phase 4.4 - Documentation
- Add docs/migration_guide.md (backup, restore, PostgreSQL switch).
- Update README.md with DB URL and migration instructions.

Cross-cutting Requirements
- Each PR under ~500 LOC except Phase 2 Core cutover.
- Add full type hints and Google-style docstrings to new public functions.
- Wrap DB operations in try/except, raise TautulliDBError, and log original error.
- Keep formatting consistent with ruff/black expectations.
- Add requirements-dev.txt and update CI to install dev deps if needed.

Risk and Safety Notes
- Phase 2 Core cutover must be the only DB access change in its PR.
- Warn reviewers: close running Tautulli instances before applying Core PR.
- Always provide data parity tests to protect semantics.

Suggested Branch and Commit Naming
- feature/dal-users -> feat: add users DAL and tests
- feature/dal-libraries -> feat: add libraries DAL and tests
- feature/dal-history -> feat: add history DAL and parity tests
- feature/sqlalchemy-core -> feat: migrate data layer to SQLAlchemy Core
- feature/orm-users -> feat: introduce ORM model for users
- feature/orm-history -> feat: introduce ORM model for session history
- feature/config-db-url -> feat: add configurable db_url and backup script
- perf/history-indexes -> perf: add history indexes and query refactor
- docs/migration-guide -> docs: add SQLAlchemy migration guide
