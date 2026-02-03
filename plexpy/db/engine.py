from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, URL

import plexpy


_ENGINE: Optional[Engine] = None


def _as_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def build_database_url(config=None):
    if config is None:
        config = plexpy.CONFIG

    query = {}
    sslmode = getattr(config, 'DB_SSLMODE', None)
    if sslmode:
        query['sslmode'] = sslmode

    return URL.create(
        'postgresql+psycopg',
        username=getattr(config, 'DB_USER', None) or None,
        password=getattr(config, 'DB_PASSWORD', None) or None,
        host=getattr(config, 'DB_HOST', None) or None,
        port=_as_int(getattr(config, 'DB_PORT', None)),
        database=getattr(config, 'DB_NAME', None) or None,
        query=query or None,
    )


def create_engine_from_config(config=None):
    if config is None:
        config = plexpy.CONFIG

    url = build_database_url(config=config)
    pool_size = _as_int(getattr(config, 'DB_POOL_SIZE', None)) or 5
    max_overflow = _as_int(getattr(config, 'DB_MAX_OVERFLOW', None)) or 10
    pool_timeout = _as_int(getattr(config, 'DB_POOL_TIMEOUT', None)) or 30

    return create_engine(
        url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_pre_ping=True,
        connect_args={
            'options': '-c timezone=utc',
        },
    )


def get_engine(config=None):
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = create_engine_from_config(config=config)
    return _ENGINE


def dispose_engine():
    global _ENGINE
    if _ENGINE is not None:
        _ENGINE.dispose()
        _ENGINE = None
