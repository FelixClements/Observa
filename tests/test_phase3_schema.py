import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from plexpy.db.engine import create_engine_from_config
from plexpy.db.session import init_session_factory, session_scope


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
