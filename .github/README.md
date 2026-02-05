# Tautulli (Fork)

A Python web application for monitoring, analytics, and notifications for
[Plex Media Server](https://plex.tv).

This fork focuses on a modernized, container-only deployment model while keeping
feature parity with the upstream project wherever possible.

## What is different in this fork

-   **Docker-only, Linux-only runtime.** All non-container installers and
    platform-specific runtime code paths have been removed.
-   **PostgreSQL-only runtime.** SQLite is supported only as a one-time migration
    source for existing installs.
-   **SQLAlchemy 2.x + Alembic migrations.** Schema changes are managed via
    migrations and validated against ORM metadata.
-   **De-vendored dependencies.** Runtime libraries are installed via `pip` and
    tracked in `requirements.txt`.
-   **Reorganized codebase.** Application modules are grouped under `plexpy/`
    subpackages (web, services, db, config, util) for clearer boundaries.

## Features

Most features match upstream Tautulli. Highlights include:

-   Responsive web UI for desktop, tablet, and mobile.
-   Current Plex Media Server activity monitoring.
-   Custom notifications for streams and recently added media.
-   Home page stats, global history, user comparisons, and library analytics.
-   Highcharts-based graphs and rich media detail pages.

## Preview

![Tautulli Homepage](https://tautulli.com/images/screenshots/activity-compressed.jpg?v=2)

## Installation (Docker only)

Use the `docker-compose.yml` in this repo or run the container directly.
The container runs as user `tautulli` (UID/GID 1000); ensure `/config` is writable
or override with `--user`.

### Database

-   PostgreSQL is required at runtime.
-   Provide connection details via environment variables or `config.ini` under
    `[Database]`.
-   `docker-compose.yml` includes a Postgres 16 service and wiring for Tautulli.

### Configuration

-   Environment variables: `TAUTULLI_DB_HOST`, `TAUTULLI_DB_PORT`, `TAUTULLI_DB_NAME`,
    `TAUTULLI_DB_USER`, `TAUTULLI_DB_PASSWORD`, `TAUTULLI_DB_SSLMODE`,
    `TAUTULLI_DB_POOL_SIZE`, `TAUTULLI_DB_MAX_OVERFLOW`, `TAUTULLI_DB_POOL_TIMEOUT`.
-   `config.ini` keys (under `[Database]`): `db_host`, `db_port`, `db_name`, `db_user`,
    `db_password`, `db_sslmode`, `db_pool_size`, `db_max_overflow`, `db_pool_timeout`.

### Migration

-   SQLite is supported only as a one-time migration source into Postgres.
-   New installs initialize an empty Postgres database automatically.
-   Existing installs must run migrations explicitly using `--migrate-db`.

### Backups

-   Backups use `pg_dump`. Ensure the Postgres client tools are available in the
    container/host.

## Architecture

See `docs/architecture.md` for the updated project structure and runtime flow.

## Support

Open issues and feature requests in this repository.

## License

This is free software under the GPL v3 open source license. Feel free to do with it what you
wish, but any modification must be open sourced. A copy of the license is included.

This software includes Highsoft software libraries which you may freely distribute for
non-commercial use. Commercial users must license this software, for more information visit
https://shop.highsoft.com/faq/non-commercial#non-commercial-redistribution.
