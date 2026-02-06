# Architecture

## Overview
Tautulli runs as a single Python application packaged under the `plexpy` namespace.
`Tautulli.py` is the thin CLI entrypoint; `plexpy.app.main` handles argument parsing,
data-directory selection, and startup. Runtime state is centralized in
`plexpy.app.bootstrap` and re-exported through `plexpy.__init__` for legacy access.

The web UI and API run on CherryPy, render Mako templates from
`plexpy/web/assets/interfaces`, and expose JSON/XML endpoints under `/api/v2`.
Plex server events are tracked via polling and a Plex WebSocket connection.
Active playback sessions are stored in `sessions` and keyed by Plex `session_key`
to prevent duplicate active stream rows.

The runtime database is PostgreSQL, accessed through SQLAlchemy. Alembic migrations
manage schema versions. SQLite is supported only as a one-time migration source.

## Runtime flow
1. `Tautulli.py` calls `plexpy.app.main.main`.
2. `plexpy.app.main` parses CLI args, resolves data/config paths, and (optionally)
   runs `--migrate-db` via Alembic.
3. `plexpy.initialize` (`plexpy.app.bootstrap`) loads config, initializes logging,
   validates migrations, and applies schema upgrades after creating a database backup.
4. `plexpy.start` starts schedulers, background workers, notifications, and analytics.
5. `plexpy.web.webstart` configures and starts the CherryPy server; the WebSocket
   listener connects to Plex and feeds activity processors.

## Package layout
- `Tautulli.py`: CLI entrypoint wrapper.
- `plexpy/app/`
  - `main.py`: CLI, environment setup, startup/shutdown loop.
  - `bootstrap.py`: global state, config loading, scheduler/threads, lifecycle helpers.
  - `common.py`, `version.py`: release and platform metadata.
- `plexpy/config/`
  - `core.py`: config schema, environment overrides (`TAUTULLI_*`), backups.
- `plexpy/db/`
  - `engine.py`, `session.py`: SQLAlchemy engine/session factories for Postgres.
  - `models/`: ORM models and metadata conventions.
  - `migrations/`: Alembic config and migration scripts.
  - `migrate_sqlite.py`: one-time SQLite -> Postgres data migration.
  - `maintenance.py`: `pg_dump` backups and VACUUM/ANALYZE maintenance.
  - `datafactory.py`, `database.py`: query helpers and data aggregation for UI/API.
  - `datatables.py`, `queries/`: raw SQL helpers and Postgres-specific query utilities.
  - `repository/`: data-access helpers.
- `plexpy/web/`
  - `webstart.py`: CherryPy server configuration (HTTPS, auth, static assets).
  - `webserve.py`: request handlers, template rendering, UI endpoints.
  - `api2.py`: API v2 command dispatcher and response formatting.
  - `webauth.py`, `session.py`: JWT/session auth and access filtering.
  - `web_socket.py`: Plex WebSocket listener and event processing.
- `plexpy/services/`
  - `activity_*`: monitor Plex sessions, ingest playback events, and process history.
  - `notification_*`, `newsletter_*`, `mobile_app.py`: outbound notifications.
  - `libraries.py`, `users.py`, `graphs.py`, `log_reader.py`, `exporter.py`, `versioncheck.py`: domain services.
- `plexpy/integrations/`
  - `plex.py`, `plextv.py`, `pmsconnect.py`: Plex/Plex.tv integration clients.
  - `http_handler.py`: outbound HTTP helper for Plex APIs.
- `plexpy/util/`
  - `logger.py`, `helpers.py`, `request.py`: shared utilities and logging.
  - `hashing_passwords.py`, `certgen.py`, `lock.py`, `exceptions.py`: security and infra helpers.
- `plexpy/web/assets/interfaces/`
  - `default/`: Mako templates, JS/CSS, images, fonts for the UI.
  - `newsletters/`: email/newsletter templates.

## Data directory
Runtime state lives under `DATA_DIR` (resolved in `plexpy.app.main`): `config.ini`,
logs, cache, backups, exports, newsletter renders, and HTTPS cert/key material.

## Compatibility shims
`plexpy/__init__.py` re-exports `plexpy.app.bootstrap` globals to preserve the
historical `import plexpy` access pattern while internal modules move to new
paths.
