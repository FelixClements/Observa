Execution Checklist: PostgreSQL + ORM + Containers Only

Phase 1: Cleanup legacy imports
- [x] Remove modules: `plexpy/plexwatch_import.py`, `plexpy/plexivity_import.py`
- [x] Update API endpoint imports and logic: `plexpy/webserve.py` (remove PlexWatch/Plexivity paths)
- [x] Remove template/JS references if any: `data/interfaces/**` (search for import UI)
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
- [x] Move files (no logic changes), update imports:
  - `plexpy/__init__.py` -> `plexpy/app/bootstrap.py` (keep a minimal `plexpy/__init__.py` for globals if needed)
  - `plexpy/webserve.py` -> `plexpy/web/webserve.py`
  - `plexpy/config.py` -> `plexpy/config/core.py`
  - `plexpy/database.py` -> `plexpy/db/sqlite_legacy.py` (temporary until removed)
  - `plexpy/helpers.py` -> `plexpy/util/helpers.py`
  - `plexpy/logger.py` -> `plexpy/util/logger.py`
  - `plexpy/webstart.py` -> `plexpy/web/webstart.py`
  - `plexpy/web_socket.py` -> `plexpy/web/web_socket.py`
  - `plexpy/plextv.py` -> `plexpy/integrations/plextv.py`
  - `plexpy/plex.py` -> `plexpy/integrations/plex.py`
  - `plexpy/activity_*` -> `plexpy/services/`
  - `plexpy/notification_*` -> `plexpy/services/`
  - `plexpy/newsletter_*` -> `plexpy/services/`
- [x] Keep entrypoint shim: `Tautulli.py` -> call `plexpy.app.main`
- [x] Add backward-compatible import shims or re-export modules for moved files
- [x] Add architecture doc: `docs/architecture.md`
- [x] Success criteria: imports resolve with new paths; shims prevent breakage
- [x] Tests: app starts; core routes/UI load with new import paths

Phase 2.5: Docker-only cleanup + asset relocation
- Remove non-Docker root folders and workflows:
  - [ ] `snap/`
  - [ ] `init-scripts/`
  - [ ] installer packaging assets in `package/`
  - [x] `.github/workflows/publish-installers.yml`
  - [x] `.github/workflows/publish-snap.yml`
- Update docs to reflect Docker-only support:
  - `README.md`
  - `CONTRIBUTING.md`
  - `CHANGELOG.md`
- Relocate UI assets:
  - Move `data/` -> `plexpy/web/assets/`
  - Update asset paths in templates/JS/Python
  - Update Dockerfile/runtime paths that reference `/app/data`
- Success criteria: assets load from new root; Docker image runs without old paths
- Tests: Docker build succeeds; UI assets served from new paths

Phase 2.6: UI templates + static asset wiring
- Update CherryPy static mounts to new asset root:
  - `plexpy/web/webstart.py` (paths for `/css`, `/js`, `/images`, `/fonts`, `/interfaces`)
- Update Mako template asset URLs:
  - `plexpy/web/assets/interfaces/default/base.html` (CSS/JS/image includes)
- Confirm template lookup path for interfaces:
  - `plexpy/web/webserve.py` (TemplateLookup root)
- Success criteria: template lookup uses new root; assets resolve under new URLs
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
- Success criteria: models map to current schema without destructive diffs
- Tests: engine/session creation works; model metadata loads

Phase 4: Alembic migrations
- Add Alembic config:
  - `alembic.ini`
  - `plexpy/db/migrations/` (env + versions)
- Generate initial migration from ORM models with schema diff review
- Remove schema creation from app startup:
  - `plexpy/app/bootstrap.py` (remove `dbcheck()` schema creation)
- Add migration version check at startup
- Add migration entrypoint for fresh installs (auto-init empty DB)
- Add explicit migrate command for existing installs (no auto-destructive changes)
- Success criteria: fresh container initializes DB; existing DB requires explicit migrate
- Tests: `alembic upgrade head` works on empty DB; version check blocks mismatches

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
- Remove sqlite3 imports and SQLite code paths:
  - `plexpy/db/sqlite_legacy.py` (delete when no longer used)
  - `plexpy/app/bootstrap.py`
  - `plexpy/services/*` (replace SQL calls with ORM)
- Remove SQLite settings from config
- Update backup/export tooling to Postgres
- Success criteria: no sqlite3 imports remain; backups/exports work on Postgres
- Tests: app runs without sqlite3; key features operate via ORM

Phase 8: Linux containers only + Python 3.15
- Update container base:
  - `Dockerfile` (Python 3.15, gated by dependency compatibility)
- Simplify entry script:
  - `start.sh` (container-only execution)
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
- Remove Windows/macOS/Snap runtime code:
  - Delete OS modules: `plexpy/windows.py`, `plexpy/macos.py`
  - Remove platform-specific imports/branches:
    - `Tautulli.py` (Windows/macOS imports, Snap env/migration)
    - `plexpy/webserve.py` (Windows/macOS imports)
    - `plexpy/versioncheck.py` (install type = snap/windows/macos)
    - `plexpy/__init__.py` (tray globals, platform-specific restart/alerts)
    - `plexpy/notification_handler.py` (update assets for .exe/.pkg)
    - `plexpy/notifiers.py` (remove OSX notifier agent)
  - Update update-bar messaging in `data/interfaces/default/base.html` for Docker-only installs
- Remove Windows/macOS/Snap packaging assets (if not already removed in Phase 2.5/8):
  - `snap/`, `package/`, `init-scripts/init.osx`, `contrib/clean_pyc.bat`
  - `.github/workflows/publish-snap.yml`, `.github/workflows/publish-installers.yml`, `.github/workflows/submit-winget.yml`
  - Clean docs: `README.md`, `CHANGELOG.md`, `.gitignore`, `.dockerignore`
- De-vendor `lib/` so deps are installed via pip:
  - Move `lib/hashing_passwords.py` -> `plexpy/util/hashing_passwords.py`
  - Move `lib/certgen.py` -> `plexpy/util/certgen.py`
  - Update imports in `plexpy/webserve.py`, `plexpy/webauth.py`, `plexpy/api2.py`, `plexpy/config.py`, `plexpy/helpers.py`
  - Remove `sys.path` manipulation in `Tautulli.py`
  - Delete `lib/` after all imports are resolved
  - Ensure all runtime deps are in `requirements.txt` and Docker build runs `pip install -r requirements.txt`
- Keep client platform icons/mappings (Windows/macOS Plex clients) intact
- Success criteria: platform-specific code removed without breaking UI mappings
- Tests: app runs without vendored libs; pip deps install cleanly in Docker build
