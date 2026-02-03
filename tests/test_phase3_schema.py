import ast
import os
import re
import sqlite3
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.sql.schema import UniqueConstraint

REPO_ROOT = Path(__file__).resolve().parents[1]
LIB_PATH = REPO_ROOT / "lib"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(LIB_PATH) not in sys.path:
    sys.path.insert(0, str(LIB_PATH))

from plexpy.db.engine import create_engine_from_config
from plexpy.db.models import Base
from plexpy.db.session import init_session_factory, session_scope

BOOTSTRAP_PATH = REPO_ROOT / "plexpy" / "app" / "bootstrap.py"


def _extract_sqlite_schema_sql():
    source = BOOTSTRAP_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    dbcheck = None

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "dbcheck":
            dbcheck = node
            break

    if dbcheck is None:
        raise AssertionError("Unable to locate dbcheck() in bootstrap.py")

    table_statements = {}
    index_statements = []

    for node in ast.walk(dbcheck):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "execute":
            continue
        if not node.args:
            continue

        arg = node.args[0]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            sql = arg.value.strip()
        else:
            continue

        sql_upper = sql.upper()
        if sql_upper.startswith("CREATE TABLE IF NOT EXISTS"):
            match = re.search(r"CREATE TABLE IF NOT EXISTS\s+([a-zA-Z0-9_]+)", sql, re.IGNORECASE)
            if not match:
                continue
            table_name = match.group(1)
            if table_name.endswith("_temp"):
                continue

            table_statements.setdefault(table_name, sql)
            continue

        if sql_upper.startswith("CREATE INDEX IF NOT EXISTS") or sql_upper.startswith(
            "CREATE UNIQUE INDEX IF NOT EXISTS"
        ):
            index_statements.append(sql)

    if not table_statements:
        raise AssertionError("No CREATE TABLE statements found in bootstrap.py")

    return table_statements, index_statements


def _normalize_unique_columns(column_names):
    return tuple(sorted(column_names))


def _is_null_default(value):
    if value is None:
        return True
    if not isinstance(value, str):
        return False
    normalized = value.strip().strip("()").strip().strip("'").upper()
    return normalized == "NULL"


def _collect_orm_unique_constraints(table):
    uniques = set()
    for constraint in table.constraints:
        if isinstance(constraint, UniqueConstraint):
            uniques.add(_normalize_unique_columns(constraint.columns.keys()))
    for column in table.columns:
        if column.unique:
            uniques.add((column.name,))
    for index in table.indexes:
        if index.unique:
            uniques.add(_normalize_unique_columns(index.columns.keys()))
    if table.primary_key.columns:
        uniques.add(_normalize_unique_columns(table.primary_key.columns.keys()))
    return uniques


def test_sqlite_schema_matches_orm():
    db_path = REPO_ROOT / "TEST" / "tautulli.db"
    if db_path.exists():
        engine = create_engine(
            f"sqlite:///{db_path}?mode=ro",
            connect_args={"uri": True},
        )
        inspector = inspect(engine)
    else:
        table_statements, index_statements = _extract_sqlite_schema_sql()

        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            conn = sqlite3.connect(tmp.name)
            try:
                for sql in table_statements.values():
                    conn.execute(sql)
                for sql in index_statements:
                    conn.execute(sql)
                conn.commit()
            finally:
                conn.close()

            engine = create_engine(f"sqlite:///{tmp.name}")
            inspector = inspect(engine)

    sqlite_tables = set(inspector.get_table_names())
    orm_tables = {table.name for table in Base.metadata.sorted_tables}

    mismatches = []
    if sqlite_tables != orm_tables:
        mismatches.append(
            f"table set mismatch: sqlite={sorted(sqlite_tables)} orm={sorted(orm_tables)}"
        )

    for table_name in sorted(sqlite_tables & orm_tables):
        sqlite_columns = {col["name"]: col for col in inspector.get_columns(table_name)}
        orm_table = Base.metadata.tables[table_name]

        sqlite_column_names = set(sqlite_columns)
        orm_column_names = {col.name for col in orm_table.columns}
        if sqlite_column_names != orm_column_names:
            mismatches.append(
                f"{table_name} columns mismatch: sqlite={sorted(sqlite_column_names)} orm={sorted(orm_column_names)}"
            )

        sqlite_pk = tuple(inspector.get_pk_constraint(table_name).get("constrained_columns") or [])
        orm_pk = tuple(col.name for col in orm_table.primary_key.columns)

        sqlite_uniques = {
            _normalize_unique_columns(constraint.get("column_names") or [])
            for constraint in inspector.get_unique_constraints(table_name)
        }
        sqlite_unique_indexes = {
            _normalize_unique_columns(index.get("column_names") or [])
            for index in inspector.get_indexes(table_name)
            if index.get("unique")
        }
        sqlite_uniques |= sqlite_unique_indexes
        if sqlite_pk:
            sqlite_uniques.add(_normalize_unique_columns(sqlite_pk))

        pk_matches = sqlite_pk == orm_pk
        if not sqlite_pk and orm_pk:
            pk_matches = _normalize_unique_columns(orm_pk) in sqlite_uniques

        if not pk_matches:
            mismatches.append(
                f"{table_name} pk mismatch: sqlite={sqlite_pk} orm={orm_pk}"
            )

        sqlite_not_null = {
            name
            for name, col in sqlite_columns.items()
            if col.get("nullable") is False and name not in sqlite_pk
        }
        orm_not_null = {
            col.name
            for col in orm_table.columns
            if col.nullable is False and col.name not in orm_pk
        }
        if sqlite_not_null != orm_not_null:
            mismatches.append(
                f"{table_name} not-null mismatch: sqlite={sorted(sqlite_not_null)} orm={sorted(orm_not_null)}"
            )

        sqlite_defaults = {
            name
            for name, col in sqlite_columns.items()
            if not _is_null_default(col.get("default")) and name not in sqlite_pk
        }
        orm_defaults = {
            col.name
            for col in orm_table.columns
            if col.server_default is not None and col.name not in orm_pk
        }
        if sqlite_defaults != orm_defaults:
            mismatches.append(
                f"{table_name} default mismatch: sqlite={sorted(sqlite_defaults)} orm={sorted(orm_defaults)}"
            )

        orm_uniques = _collect_orm_unique_constraints(orm_table)
        if sqlite_uniques != orm_uniques:
            mismatches.append(
                f"{table_name} unique mismatch: sqlite={sorted(sqlite_uniques)} orm={sorted(orm_uniques)}"
            )

        sqlite_indexes = {
            _normalize_unique_columns(index.get("column_names") or [])
            for index in inspector.get_indexes(table_name)
            if not index.get("unique")
        }
        orm_indexes = {
            _normalize_unique_columns(index.columns.keys()) for index in orm_table.indexes
            if not index.unique
        }
        if sqlite_indexes != orm_indexes:
            mismatches.append(
                f"{table_name} index mismatch: sqlite={sorted(sqlite_indexes)} orm={sorted(orm_indexes)}"
            )

    assert not mismatches, "\n".join(mismatches)


def test_postgres_engine_session_smoke():
    db_url = os.getenv("TAUTULLI_TEST_DATABASE_URL")
    if not db_url:
        pytest.skip("TAUTULLI_TEST_DATABASE_URL not set")

    url = make_url(db_url)
    if url.get_backend_name() != "postgresql":
        pytest.skip("TAUTULLI_TEST_DATABASE_URL is not PostgreSQL")

    cfg = SimpleNamespace(
        DB_USER=url.username,
        DB_PASSWORD=url.password,
        DB_HOST=url.host,
        DB_PORT=url.port,
        DB_NAME=url.database,
        DB_SSLMODE=url.query.get("sslmode") if url.query else None,
        DB_POOL_SIZE=1,
        DB_MAX_OVERFLOW=0,
        DB_POOL_TIMEOUT=5,
    )

    engine = create_engine_from_config(cfg)
    init_session_factory(engine)

    with session_scope() as session:
        assert session.execute(text("SELECT 1")).scalar() == 1
