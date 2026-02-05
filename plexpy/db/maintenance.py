import os
import os
import shutil
import subprocess
import time
from typing import Optional

import plexpy
from plexpy.util import helpers
from plexpy.util import logger


BACKUP_EXTENSION = '.dump'
BACKUP_PREFIX = 'tautulli.backup-'
DOWNLOAD_FILENAME = 'tautulli.dump'


def _pg_dump_path():
    return shutil.which('pg_dump')


def _pg_restore_path():
    return shutil.which('pg_restore')


def _build_pg_dump_command(output_path, config=None):
    if config is None:
        config = plexpy.CONFIG

    cmd = [
        _pg_dump_path(),
        '--format', 'custom',
        '--file', output_path,
    ]

    host = getattr(config, 'DB_HOST', None) or None
    port = getattr(config, 'DB_PORT', None) or None
    user = getattr(config, 'DB_USER', None) or None
    name = getattr(config, 'DB_NAME', None) or None

    if host:
        cmd.extend(['--host', str(host)])
    if port:
        cmd.extend(['--port', str(port)])
    if user:
        cmd.extend(['--username', str(user)])
    if name:
        cmd.extend(['--dbname', str(name)])

    cmd.extend(['--no-owner', '--no-privileges'])
    return cmd


def _build_pg_restore_command(backup_path, config=None):
    if config is None:
        config = plexpy.CONFIG

    cmd = [
        _pg_restore_path(),
        '--clean',
        '--if-exists',
        '--exit-on-error',
    ]

    host = getattr(config, 'DB_HOST', None) or None
    port = getattr(config, 'DB_PORT', None) or None
    user = getattr(config, 'DB_USER', None) or None
    name = getattr(config, 'DB_NAME', None) or None

    if host:
        cmd.extend(['--host', str(host)])
    if port:
        cmd.extend(['--port', str(port)])
    if user:
        cmd.extend(['--username', str(user)])
    if name:
        cmd.extend(['--dbname', str(name)])

    cmd.extend(['--no-owner', '--no-privileges'])
    cmd.append(backup_path)
    return cmd


def _build_pg_dump_env(config=None):
    if config is None:
        config = plexpy.CONFIG

    env = os.environ.copy()
    password = getattr(config, 'DB_PASSWORD', None)
    sslmode = getattr(config, 'DB_SSLMODE', None)
    if password:
        env['PGPASSWORD'] = str(password)
    if sslmode:
        env['PGSSLMODE'] = str(sslmode)
    return env


def _run_pg_dump(output_path, config=None):
    pg_dump = _pg_dump_path()
    if not pg_dump:
        logger.error('Tautulli Database :: pg_dump not found in PATH.')
        return False

    cmd = _build_pg_dump_command(output_path, config=config)
    env = _build_pg_dump_env(config=config)

    try:
        subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        logger.error('Tautulli Database :: pg_dump failed: %s', exc.stderr or exc)
        return False

    return os.path.exists(output_path)


def has_pg_restore():
    return bool(_pg_restore_path())


def has_recent_backup(backup_dir, max_age_seconds):
    if not os.path.isdir(backup_dir):
        return False

    now = time.time()
    for file_ in os.listdir(backup_dir):
        if not file_.endswith(BACKUP_EXTENSION):
            continue
        file_path = os.path.join(backup_dir, file_)
        if os.path.getctime(file_path) > (now - max_age_seconds):
            return True
    return False


def make_backup(cleanup=False, scheduler=False):
    if not plexpy.CONFIG.BACKUP_DIR:
        logger.error('Tautulli Database :: Backup directory is not configured.')
        return False

    backup_folder = plexpy.CONFIG.BACKUP_DIR
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)

    suffix = '.sched' if scheduler else ''
    backup_file = '{prefix}{timestamp}{suffix}{ext}'.format(
        prefix=BACKUP_PREFIX,
        timestamp=helpers.now(),
        suffix=suffix,
        ext=BACKUP_EXTENSION,
    )
    backup_file_fp = os.path.join(backup_folder, backup_file)

    if not _run_pg_dump(backup_file_fp):
        return False

    if cleanup:
        now = time.time()
        for root, _, files in os.walk(backup_folder):
            dump_files = [os.path.join(root, f) for f in files if '.sched' in f and f.endswith(BACKUP_EXTENSION)]
            for file_ in dump_files:
                if os.stat(file_).st_mtime < now - plexpy.CONFIG.BACKUP_DAYS * 86400:
                    try:
                        os.remove(file_)
                    except OSError as exc:
                        logger.error('Tautulli Database :: Failed to delete %s from the backup folder: %s', file_, exc)

    if backup_file in os.listdir(backup_folder):
        logger.debug('Tautulli Database :: Successfully backed up to %s', backup_file)
        return True

    logger.error('Tautulli Database :: Failed to backup to %s', backup_file)
    return False


def make_migration_backup():
    if not plexpy.CONFIG.BACKUP_DIR:
        logger.error('Tautulli Database :: Backup directory is not configured.')
        return None

    backup_folder = plexpy.CONFIG.BACKUP_DIR
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)

    backup_file = '{prefix}{timestamp}.migrate{ext}'.format(
        prefix=BACKUP_PREFIX,
        timestamp=helpers.now(),
        ext=BACKUP_EXTENSION,
    )
    backup_file_fp = os.path.join(backup_folder, backup_file)

    if not _run_pg_dump(backup_file_fp):
        return None

    if backup_file in os.listdir(backup_folder):
        logger.debug('Tautulli Database :: Migration backup created at %s', backup_file_fp)
        return backup_file_fp

    logger.error('Tautulli Database :: Failed to create migration backup at %s', backup_file_fp)
    return None


def restore_backup(backup_path, config=None):
    if not backup_path or not os.path.exists(backup_path):
        logger.error('Tautulli Database :: Backup file not found: %s', backup_path)
        return False

    pg_restore = _pg_restore_path()
    if not pg_restore:
        logger.error('Tautulli Database :: pg_restore not found in PATH.')
        return False

    cmd = _build_pg_restore_command(backup_path, config=config)
    env = _build_pg_dump_env(config=config)

    try:
        subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        logger.error('Tautulli Database :: pg_restore failed: %s', exc.stderr or exc)
        return False

    return True


def create_database_dump(cache_dir, filename: Optional[str] = None):
    if not cache_dir:
        raise ValueError('Cache directory is required')

    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    dump_name = filename or DOWNLOAD_FILENAME
    dump_path = os.path.join(cache_dir, dump_name)

    if not _run_pg_dump(dump_path):
        raise RuntimeError('pg_dump failed')

    return dump_path


def integrity_check():
    try:
        from plexpy.db.engine import get_engine

        engine = get_engine()
        with engine.connect() as connection:
            connection.exec_driver_sql('SELECT 1')
        return {'integrity_check': 'ok'}
    except Exception as exc:
        logger.error('Tautulli Database :: Integrity check failed: %s', exc)
        return {'integrity_check': 'fail'}


def vacuum():
    try:
        from plexpy.db.engine import get_engine

        engine = get_engine()
        with engine.connect().execution_options(isolation_level='AUTOCOMMIT') as connection:
            connection.exec_driver_sql('VACUUM')
    except Exception as exc:
        logger.error('Tautulli Database :: Failed to vacuum database: %s', exc)


def optimize():
    try:
        from plexpy.db.engine import get_engine

        engine = get_engine()
        with engine.connect().execution_options(isolation_level='AUTOCOMMIT') as connection:
            connection.exec_driver_sql('ANALYZE')
    except Exception as exc:
        logger.error('Tautulli Database :: Failed to analyze database: %s', exc)


def optimize_db():
    vacuum()
    optimize()
