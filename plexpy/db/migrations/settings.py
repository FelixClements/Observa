from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Optional, Tuple

from configobj import ConfigObj
from sqlalchemy.engine import URL


ENV_PREFIX = 'TAUTULLI_'
DEFAULT_CONFIG_FILENAME = 'config.ini'


@dataclass(frozen=True)
class DatabaseSettings:
    host: Optional[str]
    port: Optional[int]
    name: Optional[str]
    user: Optional[str]
    password: Optional[str]
    sslmode: Optional[str]
    pool_size: Optional[int]
    max_overflow: Optional[int]
    pool_timeout: Optional[int]


def _as_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _clean(value):
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == '':
        return None
    return value


def _defaults() -> DatabaseSettings:
    return DatabaseSettings(
        host='localhost',
        port=5432,
        name='tautulli',
        user='tautulli',
        password=None,
        sslmode='prefer',
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
    )


def _settings_from_values(**kwargs) -> DatabaseSettings:
    defaults = _defaults()
    return DatabaseSettings(
        host=_clean(kwargs.get('host', defaults.host)),
        port=_as_int(kwargs.get('port', defaults.port)),
        name=_clean(kwargs.get('name', defaults.name)),
        user=_clean(kwargs.get('user', defaults.user)),
        password=_clean(kwargs.get('password', defaults.password)),
        sslmode=_clean(kwargs.get('sslmode', defaults.sslmode)),
        pool_size=_as_int(kwargs.get('pool_size', defaults.pool_size)),
        max_overflow=_as_int(kwargs.get('max_overflow', defaults.max_overflow)),
        pool_timeout=_as_int(kwargs.get('pool_timeout', defaults.pool_timeout)),
    )


def settings_from_object(config) -> DatabaseSettings:
    return _settings_from_values(
        host=getattr(config, 'DB_HOST', None),
        port=getattr(config, 'DB_PORT', None),
        name=getattr(config, 'DB_NAME', None),
        user=getattr(config, 'DB_USER', None),
        password=getattr(config, 'DB_PASSWORD', None),
        sslmode=getattr(config, 'DB_SSLMODE', None),
        pool_size=getattr(config, 'DB_POOL_SIZE', None),
        max_overflow=getattr(config, 'DB_MAX_OVERFLOW', None),
        pool_timeout=getattr(config, 'DB_POOL_TIMEOUT', None),
    )


def _load_env_settings() -> Optional[DatabaseSettings]:
    values = {
        'host': os.environ.get(f'{ENV_PREFIX}DB_HOST'),
        'port': os.environ.get(f'{ENV_PREFIX}DB_PORT'),
        'name': os.environ.get(f'{ENV_PREFIX}DB_NAME'),
        'user': os.environ.get(f'{ENV_PREFIX}DB_USER'),
        'password': os.environ.get(f'{ENV_PREFIX}DB_PASSWORD'),
        'sslmode': os.environ.get(f'{ENV_PREFIX}DB_SSLMODE'),
        'pool_size': os.environ.get(f'{ENV_PREFIX}DB_POOL_SIZE'),
        'max_overflow': os.environ.get(f'{ENV_PREFIX}DB_MAX_OVERFLOW'),
        'pool_timeout': os.environ.get(f'{ENV_PREFIX}DB_POOL_TIMEOUT'),
    }

    if not any(value not in (None, '') for value in values.values()):
        return None

    return _settings_from_values(**values)


def _load_config_settings(config_path: str) -> Optional[DatabaseSettings]:
    if not config_path or not os.path.isfile(config_path):
        return None

    config = ConfigObj(config_path, encoding='utf-8')
    section = config.get('Database', {})

    return _settings_from_values(
        host=section.get('db_host'),
        port=section.get('db_port'),
        name=section.get('db_name'),
        user=section.get('db_user'),
        password=section.get('db_password'),
        sslmode=section.get('db_sslmode'),
        pool_size=section.get('db_pool_size'),
        max_overflow=section.get('db_max_overflow'),
        pool_timeout=section.get('db_pool_timeout'),
    )


def _default_config_path() -> Optional[str]:
    config_path = os.environ.get(f'{ENV_PREFIX}CONFIG')
    if config_path:
        return config_path

    data_dir = os.environ.get(f'{ENV_PREFIX}DATA_DIR')
    if data_dir:
        return os.path.join(data_dir, DEFAULT_CONFIG_FILENAME)

    docker_config = os.path.join(os.sep, 'config', DEFAULT_CONFIG_FILENAME)
    if os.path.isfile(docker_config):
        return docker_config

    cwd_config = os.path.join(os.getcwd(), DEFAULT_CONFIG_FILENAME)
    if os.path.isfile(cwd_config):
        return cwd_config

    return None


def resolve_db_settings(config_path: Optional[str] = None) -> Tuple[Optional[DatabaseSettings], Optional[str]]:
    env_settings = _load_env_settings()
    if env_settings is not None:
        return env_settings, 'environment'

    resolved_path = config_path or _default_config_path()
    if resolved_path:
        config_settings = _load_config_settings(resolved_path)
        if config_settings is not None:
            return config_settings, resolved_path

    return None, None


def build_database_url(settings: DatabaseSettings) -> URL:
    query = {}
    if settings.sslmode:
        query['sslmode'] = settings.sslmode

    return URL.create(
        'postgresql+psycopg',
        username=_clean(settings.user),
        password=_clean(settings.password),
        host=_clean(settings.host),
        port=_as_int(settings.port),
        database=_clean(settings.name),
        query=query or None,
    )


def resolve_database_url(config_path: Optional[str] = None, config=None) -> URL:
    if config is not None:
        return build_database_url(settings_from_object(config))

    settings, source = resolve_db_settings(config_path=config_path)
    if settings is None:
        raise RuntimeError(
            'Postgres settings not found. Set TAUTULLI_DB_* environment variables '
            'or provide a config.ini with a [Database] section.'
        )

    return build_database_url(settings)
