from __future__ import annotations

import os
import time
from typing import Dict, Iterable, List, Optional, Sequence

from sqlalchemy import Integer, Text, create_engine, inspect, insert, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import CircularDependencyError, SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import UniqueConstraint

import plexpy
from plexpy.db import engine as db_engine
from plexpy.db.migrations import manager as migration_manager
from plexpy.db.migrations import settings as migration_settings
from plexpy.db.models import Base
from plexpy.util import helpers, logger


CHUNK_SIZE = 1000
REQUIRED_TABLES = {
    'session_history',
    'version_info',
}


class MigrationError(RuntimeError):
    pass


def run_migration(sqlite_path: Optional[str] = None, confirm_overwrite: bool = False) -> bool:
    start_time = time.monotonic()
    logger.info("SQLite migration :: Starting SQLite -> Postgres migration.")

    if not sqlite_path:
        logger.error("SQLite migration :: No SQLite database path provided.")
        return False

    sqlite_path = os.path.abspath(sqlite_path)

    try:
        _validate_sqlite(sqlite_path)
    except MigrationError as exc:
        logger.error("SQLite migration :: SQLite validation failed: %s", exc)
        helpers.delete_file(sqlite_path)
        return False
    except Exception as exc:
        logger.exception("SQLite migration :: SQLite validation error: %s", exc)
        helpers.delete_file(sqlite_path)
        return False

    config = getattr(plexpy, 'CONFIG', None)
    if config is None:
        logger.error("SQLite migration :: Application configuration not initialized.")
        helpers.delete_file(sqlite_path)
        return False

    try:
        url = migration_settings.resolve_database_url(config=config)
        db_settings = migration_settings.settings_from_object(config)
        logger.info(
            "SQLite migration :: Target Postgres %s:%s/%s (user=%s, sslmode=%s)",
            db_settings.host,
            db_settings.port,
            db_settings.name,
            db_settings.user,
            db_settings.sslmode,
        )
    except Exception as exc:
        logger.exception("SQLite migration :: Failed to resolve Postgres settings: %s", exc)
        helpers.delete_file(sqlite_path)
        return False

    try:
        database_empty = migration_manager.is_database_empty(url)
        if not database_empty and not helpers.bool_true(confirm_overwrite):
            logger.error("SQLite migration :: Target Postgres database is not empty. Aborting.")
            helpers.delete_file(sqlite_path)
            return False

        migration_state = migration_manager.check_or_initialize(config=config)
        logger.info("SQLite migration :: Migration state: %s", migration_state)
    except Exception as exc:
        logger.exception("SQLite migration :: Postgres preflight failed: %s", exc)
        helpers.delete_file(sqlite_path)
        return False

    engine = db_engine.create_engine_from_config(config=config)
    sqlite_connection = None
    sqlite_engine = None
    try:
        sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")
        sqlite_connection = sqlite_engine.connect()
        try:
            tables = list(Base.metadata.sorted_tables)
        except CircularDependencyError as exc:
            raise MigrationError(
                "SQLite migration :: Foreign key dependency cycle detected in metadata."
            ) from exc

        _truncate_tables(engine, tables)

        report = _migrate_tables(sqlite_connection, engine, tables)
        _verify_row_counts(engine, report)
        _verify_indexes(engine, tables)
        _align_sequences(engine, tables)
    except MigrationError as exc:
        logger.error("SQLite migration :: Migration failed: %s", exc)
        return False
    except SQLAlchemyError as exc:
        logger.exception("SQLite migration :: Database error during migration: %s", exc)
        return False
    except Exception as exc:
        logger.exception("SQLite migration :: Unexpected migration error: %s", exc)
        return False
    finally:
        if sqlite_connection is not None:
            sqlite_connection.close()
        if sqlite_engine is not None:
            sqlite_engine.dispose()
        engine.dispose()
        helpers.delete_file(sqlite_path)

    elapsed = time.monotonic() - start_time
    logger.info("SQLite migration :: Migration completed in %.2f seconds.", elapsed)
    return True


def _validate_sqlite(sqlite_path: str) -> None:
    if not os.path.isfile(sqlite_path):
        raise MigrationError("SQLite database file does not exist.")
    if os.path.getsize(sqlite_path) == 0:
        raise MigrationError("SQLite database file is empty.")

    engine = None
    connection = None
    try:
        engine = create_engine(f"sqlite:///{sqlite_path}")
        connection = engine.connect()
        result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = {row[0] for row in result.fetchall()}
        missing = REQUIRED_TABLES - tables
        if missing:
            raise MigrationError(
                "SQLite database missing required tables: %s" % ", ".join(sorted(missing))
            )

        integrity = connection.execute(text("PRAGMA quick_check")).fetchone()
        if not integrity or integrity[0] != 'ok':
            raise MigrationError("SQLite integrity check failed: %s" % (integrity[0] if integrity else 'unknown'))

        _validate_fk_orphans(connection)
    except SQLAlchemyError as exc:
        raise MigrationError("SQLite validation error: %s" % exc)
    finally:
        if connection is not None:
            connection.close()
        if engine is not None:
            engine.dispose()


def _truncate_tables(engine: Engine, tables: Sequence) -> None:
    logger.info("SQLite migration :: Truncating Postgres tables.")
    with engine.begin() as connection:
        for table in reversed(tables):
            table_name = _quote_identifier(table.name)
            connection.execute(text("TRUNCATE TABLE %s RESTART IDENTITY CASCADE" % table_name))


def _migrate_tables(sqlite_connection, engine: Engine, tables: Sequence) -> List[Dict[str, object]]:
    report = []
    for table in tables:
        table_name = table.name
        sqlite_columns = _sqlite_columns(sqlite_connection, table_name)
        if not sqlite_columns:
            logger.warning("SQLite migration :: Skipping missing SQLite table '%s'.", table_name)
            report.append({'table': table_name, 'sqlite_count': 0, 'postgres_count': 0})
            continue

        target_columns = [column.name for column in table.columns]
        columns_to_copy = [name for name in target_columns if name in sqlite_columns]

        if not columns_to_copy:
            logger.warning("SQLite migration :: No matching columns for table '%s'.", table_name)
            report.append({'table': table_name, 'sqlite_count': 0, 'postgres_count': 0})
            continue

        missing_columns = [name for name in target_columns if name not in sqlite_columns]
        if missing_columns:
            logger.warning(
                "SQLite migration :: SQLite table '%s' missing columns: %s",
                table_name,
                ", ".join(missing_columns),
            )

        sqlite_count = _sqlite_row_count(sqlite_connection, table_name)
        logger.info("SQLite migration :: Migrating table '%s' (%s rows).", table_name, sqlite_count)

        postgres_count = _copy_table_data(
            sqlite_connection,
            engine,
            table,
            columns_to_copy,
        )

        report.append({
            'table': table_name,
            'sqlite_count': sqlite_count,
            'postgres_count': postgres_count,
        })

    return report


def _validate_fk_orphans(sqlite_connection) -> None:
    checks = [
        (
            'session_history_metadata.id -> session_history.id',
            "SELECT COUNT(*) FROM session_history_metadata shm "
            "LEFT JOIN session_history sh ON sh.id = shm.id "
            "WHERE sh.id IS NULL",
        ),
        (
            'session_history_media_info.id -> session_history.id',
            "SELECT COUNT(*) FROM session_history_media_info shmi "
            "LEFT JOIN session_history sh ON sh.id = shmi.id "
            "WHERE sh.id IS NULL",
        ),
        (
            'session_history.user_id -> users.user_id',
            "SELECT COUNT(*) FROM session_history sh "
            "LEFT JOIN users u ON u.user_id = sh.user_id "
            "WHERE sh.user_id IS NOT NULL AND u.user_id IS NULL",
        ),
        (
            'notify_log.notifier_id -> notifiers.id',
            "SELECT COUNT(*) FROM notify_log nl "
            "LEFT JOIN notifiers n ON n.id = nl.notifier_id "
            "WHERE nl.notifier_id IS NOT NULL AND n.id IS NULL",
        ),
        (
            'newsletter_log.newsletter_id -> newsletters.id',
            "SELECT COUNT(*) FROM newsletter_log nwl "
            "LEFT JOIN newsletters n ON n.id = nwl.newsletter_id "
            "WHERE nwl.newsletter_id IS NOT NULL AND n.id IS NULL",
        ),
    ]

    for label, query in checks:
        result = sqlite_connection.execute(text(query)).fetchone()
        count = result[0] if result else 0
        if count:
            raise MigrationError("SQLite database has %s orphaned rows for %s." % (count, label))


def _copy_table_data(
    sqlite_connection,
    engine: Engine,
    table,
    columns: Sequence[str],
) -> int:
    insert_stmt = insert(table)
    normalizers = _column_normalizers(table, columns)
    column_list = ", ".join(_quote_identifier(column) for column in columns)
    table_identifier = _quote_identifier(table.name)
    cursor = sqlite_connection.execute(
        text("SELECT %s FROM %s" % (column_list, table_identifier))
    )

    inserted = 0
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = Session()
    try:
        while True:
            rows = cursor.fetchmany(CHUNK_SIZE)
            if not rows:
                break

            payload = []
            for row in rows:
                item = {}
                row_map = row._mapping
                for column in columns:
                    item[column] = normalizers[column](row_map[column])
                payload.append(item)

            session.execute(insert_stmt, payload)
            session.commit()
            inserted += len(payload)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return inserted


def _verify_row_counts(engine: Engine, report: Iterable[Dict[str, object]]) -> None:
    logger.info("SQLite migration :: Verifying row counts.")
    with engine.connect() as connection:
        for entry in report:
            table_name = entry.get('table')
            if not isinstance(table_name, str):
                table_name = str(table_name)
            expected_value = entry.get('sqlite_count')
            if isinstance(expected_value, (int, float)):
                expected = int(expected_value)
            elif isinstance(expected_value, str):
                expected = int(expected_value) if expected_value.isdigit() else 0
            else:
                expected = 0
            actual = connection.execute(
                text("SELECT COUNT(*) FROM %s" % _quote_identifier(table_name))
            ).scalar()
            entry['postgres_count'] = actual or 0
            if (actual or 0) != expected:
                raise MigrationError(
                    "Row count mismatch for table '%s' (sqlite=%s, postgres=%s)"
                    % (table_name, expected, actual)
                )


def _verify_indexes(engine: Engine, tables: Sequence) -> None:
    logger.info("SQLite migration :: Verifying indexes and constraints.")
    inspector = inspect(engine)
    missing_items = []
    for table in tables:
        table_name = table.name
        existing_indexes = set()
        for index in inspector.get_indexes(table_name):
            name = index.get('name')
            if name is not None:
                existing_indexes.add(str(name))

        existing_uniques = set()
        for constraint in inspector.get_unique_constraints(table_name):
            name = constraint.get('name')
            if name is not None:
                existing_uniques.add(str(name))
        pk_constraint = inspector.get_pk_constraint(table_name)
        existing_pk = pk_constraint.get('name') if pk_constraint else None

        expected_indexes = {
            str(index.name)
            for index in table.indexes
            if index.name is not None
        }
        expected_uniques = {
            str(constraint.name)
            for constraint in table.constraints
            if isinstance(constraint, UniqueConstraint) and constraint.name is not None
        }
        expected_pk = str(table.primary_key.name) if table.primary_key is not None else None

        missing_indexes = expected_indexes - existing_indexes
        missing_uniques = expected_uniques - existing_uniques
        if expected_pk and expected_pk != existing_pk:
            missing_items.append("pk %s.%s" % (table_name, expected_pk))
        for name in sorted(missing_indexes):
            missing_items.append("index %s.%s" % (table_name, name))
        for name in sorted(missing_uniques):
            missing_items.append("unique %s.%s" % (table_name, name))

    if missing_items:
        raise MigrationError("Missing constraints or indexes: %s" % ", ".join(missing_items))


def _align_sequences(engine: Engine, tables: Sequence) -> None:
    logger.info("SQLite migration :: Aligning Postgres sequences.")
    with engine.begin() as connection:
        for table in tables:
            column = _identity_column(table)
            if column is None:
                continue

            table_name = _quote_identifier(table.name)
            column_name = _quote_identifier(column.name)
            max_value = connection.execute(
                text("SELECT MAX(%s) FROM %s" % (column_name, table_name))
            ).scalar()
            if max_value is None:
                continue

            connection.execute(
                text(
                    "SELECT setval(pg_get_serial_sequence(:table, :column)::regclass, :value, true)"
                ),
                {
                    'table': table.name,
                    'column': column.name,
                    'value': max_value,
                },
            )


def _sqlite_columns(sqlite_connection, table_name: str) -> List[str]:
    result = sqlite_connection.execute(
        text("PRAGMA table_info(%s)" % _quote_identifier(table_name))
    )
    return [row['name'] for row in result.mappings().all()]


def _sqlite_row_count(sqlite_connection, table_name: str) -> int:
    result = sqlite_connection.execute(
        text("SELECT COUNT(*) AS count FROM %s" % _quote_identifier(table_name))
    ).scalar()
    if result is None:
        return 0
    return int(result)


def _column_normalizers(table, columns: Sequence[str]):
    normalizers = {}
    for name in columns:
        column = table.c[name]
        if isinstance(column.type, Integer):
            normalizers[name] = _normalize_int
        elif isinstance(column.type, Text):
            normalizers[name] = _normalize_text
        else:
            normalizers[name] = _normalize_passthrough
    return normalizers


def _normalize_int(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, bytes):
        value = value.decode('utf-8', errors='replace')
    if isinstance(value, str):
        stripped = value.strip()
        if stripped == '':
            return None
        lowered = stripped.lower()
        if lowered in ('true', 't', 'yes', 'y', 'on'):
            return 1
        if lowered in ('false', 'f', 'no', 'n', 'off'):
            return 0
        try:
            return int(float(stripped))
        except ValueError:
            return None
    return None


def _normalize_text(value):
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='replace')
    if isinstance(value, str):
        return value
    return str(value)


def _normalize_passthrough(value):
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='replace')
    return value


def _identity_column(table):
    for column in table.columns:
        if column.primary_key and column.identity is not None:
            return column
        if column.primary_key and column.autoincrement is True:
            return column
    return None


def _quote_identifier(name: str) -> str:
    return '"%s"' % name.replace('"', '""')
