Execution Checklist: PostgreSQL + ORM + Containers Only

Phase 1: Cleanup legacy imports
- [x] Remove modules: `plexpy/plexwatch_import.py`, `plexpy/plexivity_import.py`
- [x] Update API endpoint imports and logic: `plexpy/webserve.py` (remove PlexWatch/Plexivity paths)
- [x] Remove template/JS references if any: `plexpy/web/assets/interfaces/**` (search for import UI)
- [x] Update docs/API references: `README.md`, `API.md`, `CHANGELOG.md`
- [x] Success criteria: import endpoints removed; UI has no legacy import entry points
- [X] Tests: app starts; import endpoints removed without 500s

Phase 2: Project organization (no behavior change)
- [x] Add package directories under `plexpy/`:
  - `plexpy/app/`
  - `plexpy/config/`
  - `plexpy/db/`
  - `plexpy/web/`
  - `plexpy/services/`
  - `plexpy/integrations/`
  - `plexpy/util/`
  - `plexpy/platform/`
- [x] Move files (no logic changes), update imports:
  - `plexpy/__init__.py` -> `plexpy/app/bootstrap.py` (keep a minimal `plexpy/__init__.py` for globals if needed)
  - `plexpy/webserve.py` -> `plexpy/web/webserve.py`
  - `plexpy/api2.py` -> `plexpy/web/api2.py`
  - `plexpy/webauth.py` -> `plexpy/web/webauth.py`
  - `plexpy/session.py` -> `plexpy/web/session.py`
  - `plexpy/config.py` -> `plexpy/config/core.py`
  - `plexpy/database.py` -> `plexpy/db/sqlite_legacy.py` (temporary until removed)
  - `plexpy/helpers.py` -> `plexpy/util/helpers.py`
  - `plexpy/logger.py` -> `plexpy/util/logger.py`
  - `plexpy/request.py` -> `plexpy/util/request.py`
  - `plexpy/lock.py` -> `plexpy/util/lock.py`
  - `plexpy/exceptions.py` -> `plexpy/util/exceptions.py`
  - `plexpy/webstart.py` -> `plexpy/web/webstart.py`
  - `plexpy/web_socket.py` -> `plexpy/web/web_socket.py`
  - `plexpy/plextv.py` -> `plexpy/integrations/plextv.py`
  - `plexpy/plex.py` -> `plexpy/integrations/plex.py`
  - `plexpy/pmsconnect.py` -> `plexpy/integrations/pmsconnect.py`
  - `plexpy/http_handler.py` -> `plexpy/integrations/http_handler.py`
  - `plexpy/common.py` -> `plexpy/app/common.py`
  - `plexpy/version.py` -> `plexpy/app/version.py`
  - `plexpy/activity_*` -> `plexpy/services/`
  - `plexpy/notification_*` -> `plexpy/services/`
  - `plexpy/newsletter_*` -> `plexpy/services/`
  - `plexpy/users.py` -> `plexpy/services/users.py`
  - `plexpy/libraries.py` -> `plexpy/services/libraries.py`
  - `plexpy/datafactory.py` -> `plexpy/db/datafactory.py`
  - `plexpy/datatables.py` -> `plexpy/db/datatables.py`
  - `plexpy/graphs.py` -> `plexpy/services/graphs.py`
  - `plexpy/exporter.py` -> `plexpy/services/exporter.py`
  - `plexpy/log_reader.py` -> `plexpy/services/log_reader.py`
  - `plexpy/mobile_app.py` -> `plexpy/services/mobile_app.py`
  - `plexpy/notifiers.py` -> `plexpy/services/notifiers.py`
  - `plexpy/newsletters.py` -> `plexpy/services/newsletters.py`
  - `plexpy/versioncheck.py` -> `plexpy/services/versioncheck.py`
  - `plexpy/macos.py` -> `plexpy/platform/macos.py`
  - `plexpy/windows.py` -> `plexpy/platform/windows.py`
- [x] Keep entrypoint shim: `Tautulli.py` -> call `plexpy.app.main`
- [x] Add backward-compatible import shims or re-export modules for moved files
- [x] Add architecture doc: `docs/architecture.md`
- [x] Success criteria: imports resolve with new paths; shims prevent breakage
- [x] Tests: app starts; core routes/UI load with new import paths -> you can test the app by running bash test_start.sh

Phase 2.5: Docker-only cleanup + asset relocation
- Remove non-Docker root folders and workflows:
  - [x] `snap/`
  - [x] `init-scripts/`
  - [x] installer packaging assets in `package/`
  - [x] `.github/workflows/publish-installers.yml`
  - [x] `.github/workflows/publish-snap.yml`
- Update docs to reflect Docker-only support:
  - [x] `README.md`
  - [x] `CONTRIBUTING.md`
  - [x] `CHANGELOG.md`
- Relocate UI assets:
  - [x] Move `data/` -> `plexpy/web/assets/`
  - [x] Update asset paths in templates/JS/Python
  - [x] Update Dockerfile/runtime paths that reference `/app/data`
- Success criteria: assets load from new root; Docker image runs without old paths
- Tests: Docker build succeeds; UI assets served from new paths

Phase 2.6: UI templates + static asset wiring
- [x] Update CherryPy static mounts to new asset root:
  - `plexpy/web/webstart.py` (paths for `/css`, `/js`, `/images`, `/fonts`, `/interfaces`)
- [x] Update Mako template asset URLs:
  - `plexpy/web/assets/interfaces/default/base.html` (CSS/JS/image includes)
- [x] Confirm template lookup path for interfaces:
  - `plexpy/web/webserve.py` (TemplateLookup root)
- [x] Success criteria: template lookup uses new root; assets resolve under new URLs
- Tests: login page renders; CSS/JS/images load without 404s

Phase 3: ORM 2.0 foundation
- Add DB core:
  - `plexpy/db/engine.py` (Postgres engine + pool config)
  - `plexpy/db/session.py` (SessionLocal + context manager)
- Add ORM models:
  - `plexpy/db/models/__init__.py`
  - `plexpy/db/models/*.py` (one per table or grouped)
- Add repository layer:
  - `plexpy/db/repository/*.py`
- Define ORM conventions:
  - SQLAlchemy 2.0 style, naming convention for constraints/indexes
  - UTC timezone handling; explicit sequence behavior for integer PKs
- Add config keys for Postgres connection:
  - `plexpy/config/core.py`
- Phase 3 completion plan (SQLite is source of truth):
  - [x] Ensure SQLAlchemy 2.x is pinned in `requirements.txt`
  - [x] Build a schema comparison test that:
    - Creates a SQLite in-memory DB using the CREATE TABLE SQL in `plexpy/app/bootstrap.py`
    - Introspects table/column/PK/index definitions via SQLAlchemy inspector
    - Compares against ORM metadata and reports mismatches (names, nullability, defaults, indexes)
  - [x] Add a Postgres smoke test that creates the ORM metadata and verifies engine/session
- Success criteria: models map to current schema without destructive diffs
- Tests: engine/session creation works; model metadata loads

Phase 4: Alembic migrations
- [x] Add Alembic config:
  - `alembic.ini`
  - `plexpy/db/migrations/` (env + versions)
- [x] Generate initial migration from ORM models with schema diff review
- [x] Remove schema creation from app startup:
  - `plexpy/app/bootstrap.py` (remove `dbcheck()` schema creation)
- [x] Add migration version check at startup
- [x] Add migration entrypoint for fresh installs (auto-init empty DB)
- [x] Add explicit migrate command for existing installs (no auto-destructive changes)
- [x] Success criteria: fresh container initializes DB; existing DB requires explicit migrate
- [x] Tests: `alembic upgrade head` works on empty DB; version check blocks mismatches

Phase 5: Setup wizard migration flow (manual trigger)
- Add wizard UI step for migration:
  - `plexpy/web/assets/interfaces/default/*.html` (setup wizard templates)
  - `plexpy/web/assets/interfaces/default/js/*` (wizard JS if present)
- Add upload handler and migration kickoff:
  - `plexpy/web/webserve.py`
- Add confirmation dialog:
  - Warn about overwriting existing Postgres DB
- Success criteria: wizard exposes migration flow and protects existing Postgres
- Tests: wizard flow triggers migration endpoint; confirmation required

Phase 6: One-time migration tool (SQLite -> Postgres)
- Add migration runner module:
  - `plexpy/db/migrate_sqlite.py`
- Implement:
  - SQLite file validation
  - Postgres truncation in dependency order
  - Bulk inserts via ORM
  - Type normalization (bools/timestamps/text)
  - Row count and integrity checks
  - Index/constraint verification
  - Sequence alignment after inserts
  - Migration report logging
- Wire migration runner to wizard endpoint
- Success criteria: migrated DB passes data integrity and schema verification
- Tests: migrate sample SQLite -> Postgres; row counts + key integrity checks pass

Phase 7: Postgres-only cleanup
- [x] Remove sqlite3 imports and SQLite code paths:
  - `plexpy/db/sqlite_legacy.py` (delete when no longer used)
  - `plexpy/app/bootstrap.py`
  - `plexpy/services/*` (replace SQL calls with ORM)
- [x] Remove SQLite settings from config
- [x] Update backup tooling to Postgres (pg_dump backups, dump download, integrity check)
- [x] Update export tooling to Postgres
- [x] Success criteria: no sqlite3 imports remain; backups/exports work on Postgres
- [x] Tests: app runs without sqlite3; key features operate via ORM
- Next step: Ensure `pg_dump` is available in the container and verify `backup_db` + `download_database` in the UI/API

Phase 8: Linux containers only + Python 3.15
- Update container base:
  - `Dockerfile` (Python 3.15, gated by dependency compatibility)
- Simplify entry script:
  - Docker entrypoint runs via `CMD` (no `start.sh`)
- Verify non-container CI workflows removed in Phase 2.5
- Update docs to container-only + Python 3.15
- Success criteria: container runs on target Python; docs match runtime support
- Tests: container build + start; runtime smoke on Python 3.15

Phase 9: Type safety rollout
- Add typing config:
  - `pyproject.toml`
- Start with DB layer:
  - `plexpy/db/engine.py`, `plexpy/db/session.py`, `plexpy/db/models/*.py`
- Expand to services and web layer:
  - `plexpy/services/*`, `plexpy/web/*`, `plexpy/config/*`
- Incrementally raise strictness in config
- Success criteria: typing gate passes for targeted layers
- Tests: type checker passes at current strictness; no runtime regressions

Phase 10: Linux-only runtime + de-vendor libs (Docker builds)
- [x] Remove Windows/macOS/Snap runtime code:
  - [x] Delete OS modules: `plexpy/platform/windows.py`, `plexpy/platform/macos.py`
  - [x] Remove platform-specific imports/branches:
    - [x] `Tautulli.py` (Windows/macOS imports, Snap env/migration)
    - [x] `plexpy/web/webserve.py` (Windows/macOS imports)
    - [x] `plexpy/services/versioncheck.py` (install type = snap/windows/macos)
    - [x] `plexpy/__init__.py` (tray globals, platform-specific restart/alerts)
    - [x] `plexpy/services/notification_handler.py` (update assets for .exe/.pkg)
    - [x] `plexpy/services/notifiers.py` (remove OSX notifier agent)
  - [x] Update update-bar messaging in `plexpy/web/assets/interfaces/default/base.html` for Docker-only installs
- [x] Remove Windows/macOS/Snap packaging assets (if not already removed in Phase 2.5/8):
  - [x] `snap/`, `package/`, `init-scripts/init.osx`, `contrib/clean_pyc.bat`
  - [x] `.github/workflows/publish-snap.yml`, `.github/workflows/publish-installers.yml`, `.github/workflows/submit-winget.yml`
  - [x] Clean docs: `README.md`, `CHANGELOG.md`, `.gitignore`, `.dockerignore`
- [x] De-vendor `lib/` so deps are installed via pip:
  - [x] Move `lib/hashing_passwords.py` -> `plexpy/util/hashing_passwords.py`
  - [x] Move `lib/certgen.py` -> `plexpy/util/certgen.py`
  - [x] Update imports in `plexpy/web/webserve.py`, `plexpy/web/webauth.py`, `plexpy/web/api2.py`, `plexpy/config/core.py`, `plexpy/util/helpers.py`
  - [x] Remove `sys.path` manipulation in `Tautulli.py`
  - [x] Delete `lib/` after all imports are resolved
  - [x] Ensure all runtime deps are in `requirements.txt` and Docker build runs `pip install -r requirements.txt`
- [x] Keep client platform icons/mappings (Windows/macOS Plex clients) intact
- [x] Success criteria: platform-specific code removed without breaking UI mappings
- [ ] Tests: app runs without vendored libs; pip deps install cleanly in Docker build

Phase 11: ORM/Core migration (Postgres runtime, SQLite migration-only)
- [x] Establish a query layer for Core/ORM results:
  - `plexpy/db/queries/__init__.py`
  - helpers for consistent `mappings()` results, pagination, and error handling
- [x] Add Core time helpers for Postgres-only functions:
  - `timezone`, `to_char`, `extract`, `epoch` utilities using `sqlalchemy.func`
  - centralize in `plexpy/db/queries/time.py`
- [x] Convert low-risk CRUD to ORM/Core (remove `MonitorDatabase` usage):
  - `plexpy/services/activity_processor.py`
  - `plexpy/services/activity_pinger.py`
  - `plexpy/services/notifiers.py`
  - `plexpy/services/users.py` (simple reads/updates)
- [ ] Convert reporting queries to SQLAlchemy Core (Postgres-specific allowed):
  - [x] `plexpy/services/graphs.py` (replace string-built SQL)
  - [x] `plexpy/services/users.py` LATERAL datatable stats
  - [x] `plexpy/services/libraries.py` LATERAL datatable stats
  - [x] `plexpy/services/notifiers.py` LATERAL last-notify lookup
- [ ] Convert `plexpy/db/datafactory.py` stats queries to Core:
  - [x] move total-duration raw SQL into `plexpy/db/queries/raw_pg.py`
  - use `lateral()` and Postgres `distinct on` (SQLAlchemy supports PG dialect)
  - keep any remaining raw SQL isolated in `plexpy/db/queries/raw_pg.py`
- [x] Keep `plexpy/db/datatables.py` as raw SQL, but:
  - tighten parameter binding and consolidate SQL construction utilities
  - document that this module is intentionally raw SQL
- [x] Add/extend FK constraints and relationships where safe:
  - session history <-> metadata/media_info, users, notifiers/newsletters
  - add Alembic migrations for new constraints
  - add preflight checks for orphans before enabling FKs
- [x] Ensure SQLite -> Postgres migration remains compatible:
  - update `plexpy/db/migrate_sqlite.py` if new constraints require ordering or cleanup
  - validate `Base.metadata.sorted_tables` order is still acyclic
- [x] Update docs to state: Postgres-only runtime, SQLite is migration-only
  - `README.md`, `docs/architecture.md`, `plan.md`
- [ ] Success criteria: >=80% of raw SQL in services moved to ORM/Core; remaining raw SQL isolated
- [ ] Tests: parity checks for key stats queries; migration still completes on sample SQLite DB
