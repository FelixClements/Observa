from __future__ import annotations

import logging
import os
from typing import Optional

from alembic import command
from alembic.config import Config as AlembicConfig
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import URL
from sqlalchemy.pool import NullPool

from plexpy.db.migrations import settings as migration_settings


LOGGER = logging.getLogger(__name__)

_MIGRATIONS_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_MIGRATIONS_DIR, os.pardir, os.pardir, os.pardir))
_ALEMBIC_INI = os.path.join(_PROJECT_ROOT, 'alembic.ini')


class MigrationError(RuntimeError):
    pass


def _alembic_config() -> AlembicConfig:
    config = AlembicConfig(_ALEMBIC_INI if os.path.isfile(_ALEMBIC_INI) else None)
    config.set_main_option('script_location', _MIGRATIONS_DIR)
    config.set_main_option('prepend_sys_path', _PROJECT_ROOT)
    return config


def _create_engine(url: URL):
    return create_engine(
        url,
        poolclass=NullPool,
        connect_args={'options': '-c timezone=utc'},
    )


def _resolve_database_url(config=None, config_path: Optional[str] = None) -> URL:
    return migration_settings.resolve_database_url(config_path=config_path, config=config)


def get_head_revision() -> Optional[str]:
    script = ScriptDirectory.from_config(_alembic_config())
    return script.get_current_head()


def get_current_revision(url: URL) -> Optional[str]:
    engine = _create_engine(url)
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        return context.get_current_revision()


def is_database_empty(url: URL) -> bool:
    engine = _create_engine(url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    non_meta_tables = [name for name in tables if name != 'alembic_version']
    return len(non_meta_tables) == 0


def upgrade_head(url: URL) -> None:
    config = _alembic_config()
    engine = _create_engine(url)
    with engine.connect() as connection:
        config.attributes['connection'] = connection
        command.upgrade(config, 'head')


def check_or_initialize(config=None, config_path: Optional[str] = None) -> str:
    url = _resolve_database_url(config=config, config_path=config_path)
    head_rev = get_head_revision()
    if head_rev is None:
        raise MigrationError('No Alembic revisions found. Verify migration scripts are present.')

    if is_database_empty(url):
        LOGGER.info('Database is empty; initializing schema via Alembic.')
        upgrade_head(url)
        return 'initialized'

    current_rev = get_current_revision(url)
    if current_rev is None:
        raise MigrationError(
            'Database schema is not under Alembic control. Run Tautulli with --migrate-db '
            'to initialize migrations.'
        )

    if current_rev != head_rev:
        raise MigrationError(
            f'Database schema is not at head (current={current_rev}, head={head_rev}). '
            'Run Tautulli with --migrate-db to apply migrations.'
        )

    return 'up-to-date'


def migrate_database(config=None, config_path: Optional[str] = None) -> None:
    url = _resolve_database_url(config=config, config_path=config_path)
    upgrade_head(url)
