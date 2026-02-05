from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional

from alembic import command
from alembic.config import Config as AlembicConfig
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from alembic.script.revision import RangeNotAncestorError, ResolutionError
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


@dataclass(frozen=True)
class MigrationState:
    state: str
    current_rev: Optional[str]
    head_rev: Optional[str]
    message: Optional[str] = None


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


def get_migration_state(config=None, config_path: Optional[str] = None) -> MigrationState:
    url = _resolve_database_url(config=config, config_path=config_path)
    head_rev = get_head_revision()
    if head_rev is None:
        raise MigrationError('No Alembic revisions found. Verify migration scripts are present.')

    if is_database_empty(url):
        return MigrationState(state='empty', current_rev=None, head_rev=head_rev)

    current_rev = get_current_revision(url)
    if current_rev is None:
        return MigrationState(
            state='uncontrolled',
            current_rev=None,
            head_rev=head_rev,
            message=(
                'Database schema is not under Alembic control. Run Tautulli with --migrate-db '
                'to initialize migrations.'
            ),
        )

    if current_rev == head_rev:
        return MigrationState(state='up-to-date', current_rev=current_rev, head_rev=head_rev)

    script = ScriptDirectory.from_config(_alembic_config())
    try:
        script.get_revision(current_rev)
    except ResolutionError:
        return MigrationState(
            state='unknown',
            current_rev=current_rev,
            head_rev=head_rev,
            message=(
                'Database schema revision %s is not recognized by this Tautulli version.'
                % current_rev
            ),
        )

    try:
        list(script.iterate_revisions(head_rev, current_rev))
    except RangeNotAncestorError:
        return MigrationState(
            state='ahead',
            current_rev=current_rev,
            head_rev=head_rev,
            message=(
                'Database schema revision %s is newer than this Tautulli version (head=%s). '
                'Update Tautulli to match the database schema.'
                % (current_rev, head_rev)
            ),
        )

    return MigrationState(
        state='needs-upgrade',
        current_rev=current_rev,
        head_rev=head_rev,
        message=(
            'Database schema is not at head (current=%s, head=%s). '
            'Run Tautulli with --migrate-db to apply migrations.'
            % (current_rev, head_rev)
        ),
    )


def check_or_initialize(config=None, config_path: Optional[str] = None) -> str:
    state = get_migration_state(config=config, config_path=config_path)
    if state.state == 'empty':
        LOGGER.info('Database is empty; initializing schema via Alembic.')
        url = _resolve_database_url(config=config, config_path=config_path)
        upgrade_head(url)
        return 'initialized'

    if state.state == 'up-to-date':
        return 'up-to-date'

    raise MigrationError(state.message or 'Database migrations are required.')


def migrate_database(config=None, config_path: Optional[str] = None) -> None:
    url = _resolve_database_url(config=config, config_path=config_path)
    upgrade_head(url)
