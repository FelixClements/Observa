# AGENTS.md - Observa Development Guide

This file provides guidance for AI agents working in the Observa codebase.

## Project Overview

- **Project**: Observa (fork of Tautulli) - Plex Media Server monitoring/analytics
- **Language**: Python 3.12+ (Docker-only, Linux-only runtime)
- **Database**: PostgreSQL with SQLAlchemy 2.x + Alembic migrations
- **Testing**: pytest, pytest-asyncio, httpx, factory-boy, advanced-alchemy
- **Key Dependencies**: See `requirements.txt`

## Build, Lint, and Test Commands

### Virtual Environment Setup

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running Tests

```bash
# Run all tests
pytest

# Run a single test file
pytest tests/test_phase3_schema.py

# Run a specific test function
pytest tests/test_phase3_schema.py::test_postgres_engine_session_smoke

# Run tests with verbose output
pytest -v

# Run tests matching a pattern
pytest -k "test_name_pattern"

# Run tests with coverage (if configured)
pytest --cov=plexpy --cov-report=html
```

### Database Migrations (Alembic)

```bash
# Apply migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Rollback one migration
alembic downgrade -1

# Show migration history
alembic history --verbose
```

### Running the Application

```bash
# Run with Docker Compose (includes PostgreSQL)
docker-compose up -d

# Run the Python application directly (requires PostgreSQL)
python Tautulli.py

# Run with migration mode
python Tautulli.py --migrate-db
```

### Code Quality (Manual)

```bash
# Type checking (if mypy installed)
mypy plexpy/

# Format code (if black installed)
black plexpy/

# Lint code (if ruff installed)
ruff check plexpy/
```

## Code Style Guidelines

### General Conventions

- **Python Version**: 3.12+ (targets Docker-only Linux containers)
- **Line Length**: Maximum 80 characters
- **Indentation**: 4 spaces (no tabs)
- **Encoding**: UTF-8 (`# -*- coding: utf-8 -*-` at top of files)
- **License Header**: Include GPL header in new files (see existing files)

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Modules/Packages | snake_case | `plexpy.util.logger` |
| Classes | PascalCase | `class User(Base):` |
| Functions/Methods | snake_case | `def refresh_users():` |
| Variables | snake_case | `user_ids = []` |
| Constants | UPPER_SNAKE | `DB_POOL_SIZE = 5` |
| Private (internal) | prefix `_` | `_private_method()` |
| Dunder (special) | prefix and suffix `__` | `__init__()` |
| Database Tables | snake_case (plural) | `__tablename__ = 'users'` |

### Import Organization

Order imports with blank lines between groups:

```python
# Standard library
import os
import sys
from pathlib import Path
from typing import Optional

# Third-party packages
import arrow
import httpagentparser
from sqlalchemy import case, delete, func

# Local application imports
import plexpy
from plexpy.app import common
from plexpy.db import datatables
from plexpy.db.engine import get_engine
from plexpy.db.models import User
from plexpy.services import libraries
from plexpy.web import session
from plexpy.util import helpers
from plexpy.util import logger
```

### Type Annotations

Use Python 3.12+ type hints:

```python
from typing import Optional

# Function annotations
def get_user(user_id: int) -> Optional[User]:
    ...

# Class attributes (SQLAlchemy 2.x style)
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = auto_pk()
    username: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(Text)
```

### Documentation (Docstrings)

Follow [PEP-257](https://www.python.org/dev/peps/pep-0257/):

```python
def refresh_users():
    """Request a fresh user list from Plex.tv and update the database."""
    
    # For complex functions, use expanded format:
    """
    Short summary.

    Longer description if needed.

    Args:
        param1: Description of param1.

    Returns:
        Description of return value.
    """
```

### Error Handling

- **Always use the logger**: `from plexpy.util import logger`
- **Log at appropriate levels**: `logger.info()`, `logger.warning()`, `logger.error()`, `logger.debug()`
- **Include context in errors**: `logger.error("Failed to process X: {error}")`
- **Use exceptions from plexpy.util.exceptions**: Define custom exceptions inheriting from `PlexPyException`

```python
from plexpy.util import logger

def my_function():
    try:
        result = risky_operation()
    except SomeError as e:
        logger.error(f"Operation failed: {e}")
        raise
```

### Web Requests

Use the built-in request utilities:

```python
from plexpy.util import request

# Do NOT use requests directly - use plexpy.util.request
response = request('GET', url, params=params)
```

### Database Operations (SQLAlchemy 2.x)

```python
from sqlalchemy import select, insert, update, delete
from plexpy.db.session import session_scope

# Use context manager for sessions
with session_scope() as db_session:
    stmt = select(User).where(User.user_id == user_id)
    user = db_session.execute(stmt).scalar_one_or_none()
    
# For writes
with session_scope() as db_session:
    stmt = update(User).where(User.id == user_id).values(username="newname")
    db_session.execute(stmt)
```

### SQLAlchemy Model Patterns

```python
from sqlalchemy import Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from plexpy.db.models import Base, auto_pk

class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = auto_pk()
    username: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('1'))
```

### Migrations (Alembic)

- Store migrations in `plexpy/db/migrations/versions/`
- Use `autogenerate` when possible
- Test migrations against a clean database before committing

```bash
alembic revision --autogenerate -m "add users table"
alembic upgrade head
```

### Pydantic Models

For new configuration/data validation, use Pydantic v2+:

```python
from pydantic import BaseModel, Field

class DatabaseConfig(BaseModel):
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    sslmode: str = Field(default="prefer")
```

### Testing Guidelines

- Use pytest fixtures for setup/teardown
- Use `pytest-asyncio` for async tests
- Use `factory-boy` for test data factories
- Use `httpx` for HTTP client testing
- Skip tests that require external resources:

```python
import os
import pytest

def test_postgres_connection():
    db_url = os.getenv("TAUTULLI_TEST_DATABASE_URL")
    if not db_url:
        pytest.skip("TAUTULLI_TEST_DATABASE_URL not set")
    # Test code...
```

## Project Structure

```
Observa/
├── plexpy/                    # Main application package
│   ├── app/                   # Application entry points
│   ├── config/                # Configuration management
│   ├── db/                    # Database layer
│   │   ├── dto/               # Data transfer objects
│   │   ├── models/            # SQLAlchemy models
│   │   ├── queries/           # Query builders
│   │   ├── repository/        # Repository pattern
│   │   └── migrations/       # Alembic migrations
│   ├── integrations/          # External integrations (Plex, etc.)
│   ├── services/              # Business logic services
│   ├── util/                  # Utilities (logger, request, etc.)
│   └── web/                   # Web handlers
├── tests/                     # Test suite
├── docs/                      # Documentation
├── requirements.txt           # Python dependencies
├── alembic.ini               # Alembic configuration
└── docker-compose.yml        # Docker development setup
```

## Branch Strategy

- **Target Branch**: Submit PRs against `nightly` branch
- **Feature Branches**: Name as `FEATURE_NAME` or `fix/description`
- **Commits**: Use meaningful commit messages

## Key Files Reference

### Core Application

| File | Purpose |
|------|---------|
| `Tautulli.py` | Application entry point |
| `plexpy/__init__.py` | Main package initialization |
| `plexpy/app/bootstrap.py` | Application bootstrap and initialization |
| `plexpy/app/common.py` | Shared application logic |
| `plexpy/app/main.py` | Main application loop |
| `plexpy/app/version.py` | Version management |

### Database

| File | Purpose |
|------|---------|
| `plexpy/db/engine.py` | Database engine setup and configuration |
| `plexpy/db/session.py` | Session context manager |
| `plexpy/db/database.py` | Database operations and helpers |
| `plexpy/db/datatables.py` | DataTables integration for AJAX tables |
| `plexpy/db/maintenance.py` | Database maintenance tasks |
| `plexpy/db/cleanup.py` | Database cleanup operations |
| `plexpy/db/datafactory.py` | Data factory for building queries |
| `plexpy/db/migrate_sqlite.py` | SQLite to PostgreSQL migration |
| `plexpy/db/models/__init__.py` | SQLAlchemy model definitions |
| `plexpy/db/repository/` | Repository pattern implementations |
| `plexpy/db/repository/users.py` | User data repository |
| `plexpy/db/repository/libraries.py` | Library data repository |
| `plexpy/db/repository/sessions.py` | Session data repository |
| `plexpy/db/repository/history.py` | History data repository |
| `plexpy/db/repository/notifications.py` | Notification data repository |
| `plexpy/db/dto/` | Data transfer objects |
| `plexpy/db/queries/` | Raw query builders |

### Configuration

| File | Purpose |
|------|---------|
| `plexpy/config/core.py` | Configuration management |
| `plexpy/config/__init__.py` | Configuration module |

### Utilities

| File | Purpose |
|------|---------|
| `plexpy/util/logger.py` | Logging utilities |
| `plexpy/util/request.py` | HTTP request wrapper |
| `plexpy/util/exceptions.py` | Custom exceptions |
| `plexpy/util/helpers.py` | Helper functions |
| `plexpy/util/lock.py` | Locking mechanisms |
| `plexpy/util/hashing_passwords.py` | Password hashing utilities |
| `plexpy/util/certgen.py` | Certificate generation |

### Services (Business Logic)

| File | Purpose |
|------|---------|
| `plexpy/services/base.py` | Base service class |
| `plexpy/services/users.py` | User management service |
| `plexpy/services/libraries.py` | Library management service |
| `plexpy/services/notifiers.py` | Notification service |
| `plexpy/services/notifier_handler.py` | Notification delivery |
| `plexpy/services/newsletters.py` | Newsletter service |
| `plexpy/services/newsletter_handler.py` | Newsletter delivery |
| `plexpy/services/activity_handler.py` | Activity tracking |
| `plexpy/services/activity_processor.py` | Activity processing |
| `plexpy/services/activity_pinger.py` | Plex server pinger |
| `plexpy/services/log_reader.py` | Log file parsing |
| `plexpy/services/graphs.py` | Graph data generation |
| `plexpy/services/exporter.py` | Data export functionality |
| `plexpy/services/mobile_app.py` | Mobile app API |
| `plexpy/services/versioncheck.py` | Version checking |

### Web/API

| File | Purpose |
|------|---------|
| `plexpy/web/webstart.py` | Web server startup |
| `plexpy/web/webserve.py` | Web request handling |
| `plexpy/web/webauth.py` | Authentication handlers |
| `plexpy/web/web_socket.py` | WebSocket support |
| `plexpy/web/session.py` | Web session management |
| `plexpy/web/api2.py` | API v2 endpoints |

### Integrations

| File | Purpose |
|------|---------|
| `plexpy/integrations/plex.py` | Plex integration |
| `plexpy/integrations/plextv.py` | Plex.tv API integration |
| `plexpy/integrations/pmsconnect.py` | Plex Media Server connection |
| `plexpy/integrations/http_handler.py` | HTTP handler for integrations |
