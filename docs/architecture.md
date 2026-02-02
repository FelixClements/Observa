# Architecture

## Overview
Tautulli is organized as a single `plexpy` package with focused subpackages.
The module layout is intended to be stable for future ORM and container work
without changing runtime behavior.

## Package layout
- `plexpy/app/`
  - `bootstrap.py`: application globals and initialization lifecycle.
  - `main.py`: CLI entrypoint that wires environment and starts the app.
- `plexpy/config/`
  - `core.py`: configuration model and persistence.
- `plexpy/db/`
  - `sqlite_legacy.py`: legacy SQLite implementation (temporary).
- `plexpy/web/`
  - `webserve.py`: web UI and API handlers.
  - `webstart.py`: CherryPy server wiring.
  - `web_socket.py`: websocket monitor loop.
- `plexpy/services/`
  - `activity_*`, `notification_*`, `newsletter_*`: background/service layers.
- `plexpy/integrations/`
  - `plex.py`, `plextv.py`: Plex and Plex.tv integration helpers.
- `plexpy/util/`
  - `helpers.py`, `logger.py`: shared utilities and logging.

## Compatibility shims
Legacy module paths are re-exported via small shim modules under `plexpy/` to
avoid breaking imports while code is migrated to new paths. The package
initializer re-exports `plexpy/app/bootstrap.py` to preserve the historical
`import plexpy` global access pattern.
