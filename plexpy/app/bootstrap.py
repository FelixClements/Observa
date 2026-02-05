# This file is part of Tautulli.
#
#  Tautulli is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Tautulli is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Tautulli.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import os
import queue
import sys
import threading
import uuid

# Some cut down versions of Python may not include this module and it's not critical for us
try:
    import webbrowser
    no_browser = False
except ImportError:
    no_browser = True

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from ga4mp import GtagMP
import pytz

from plexpy.app import common
from plexpy.db import maintenance
from plexpy.db.migrations import manager as migration_manager
from plexpy.services import exporter
from plexpy.services import libraries
from plexpy.services import mobile_app
from plexpy.services import newsletters
from plexpy.services import notifiers
from plexpy.services import users
from plexpy.services import versioncheck
from plexpy.config import core as config
from plexpy.integrations import plex
from plexpy.integrations import plextv
from plexpy.services import activity_handler
from plexpy.services import activity_pinger
from plexpy.services import newsletter_handler
from plexpy.services import notification_handler
from plexpy.util import helpers
from plexpy.util import logger
from plexpy.web import web_socket
from plexpy.web import webstart


PROG_DIR = None
FULL_PATH = None
ASSETS_DIR = None

ARGS = None
SIGNAL = None

SYS_PLATFORM = None
SYS_LANGUAGE = None
SYS_ENCODING = None

QUIET = False
VERBOSE = False
DAEMON = False
CREATEPID = False
PIDFILE = None
NOFORK = False
DOCKER = False
DOCKER_MOUNT = False
FROZEN = False

SCHED = None
SCHED_LOCK = threading.Lock()

NOTIFY_QUEUE = queue.Queue()

INIT_LOCK = threading.Lock()
_INITIALIZED = False
_STARTED = False
_UPDATE = False

DATA_DIR = None

CONFIG = None
CONFIG_FILE = None


INSTALL_TYPE = None
CURRENT_VERSION = None
LATEST_VERSION = None
COMMITS_BEHIND = None
PREV_RELEASE = None
LATEST_RELEASE = None
UPDATE_AVAILABLE = False

UMASK = None

HTTP_PORT = None
HTTP_ROOT = None
AUTH_ENABLED = None

DEV = False

WEBSOCKET = None
WS_CONNECTED = False
PLEX_SERVER_UP = None
PLEX_REMOTE_ACCESS_UP = None

TRACKER = None

SYS_TIMEZONE = None
SYS_UTC_OFFSET = None


def _sync_package_globals(*keys):
    import plexpy as _plexpy
    for key in keys:
        setattr(_plexpy, key, globals().get(key))


def initialize(config_file):
    with INIT_LOCK:

        global CONFIG
        global CONFIG_FILE
        global VERBOSE
        global _INITIALIZED
        global CURRENT_VERSION
        global LATEST_VERSION
        global PREV_RELEASE
        global UMASK
        global _UPDATE

        try:
            CONFIG = config.Config(config_file)
        except:
            alert_message('Failed to start Tautulli: Config file is corrupted.\n\n%s' % config_file)
            raise SystemExit("Unable to initialize Tautulli due to a corrupted config file. Exiting...")

        CONFIG_FILE = config_file
        _sync_package_globals('CONFIG', 'CONFIG_FILE')

        assert CONFIG is not None

        if _INITIALIZED:
            return False

        if CONFIG.HTTP_PORT < 21 or CONFIG.HTTP_PORT > 65535:
            logger.warn("HTTP_PORT out of bounds: 21 < %s < 65535", CONFIG.HTTP_PORT)
            CONFIG.HTTP_PORT = 8181

        if not CONFIG.HTTPS_CERT:
            CONFIG.HTTPS_CERT = os.path.join(DATA_DIR, 'server.crt')
        if not CONFIG.HTTPS_KEY:
            CONFIG.HTTPS_KEY = os.path.join(DATA_DIR, 'server.key')

        CONFIG.LOG_DIR, log_writable = check_folder_writable(
            CONFIG.LOG_DIR, os.path.join(DATA_DIR, 'logs'), 'logs')
        if not log_writable and not QUIET:
            sys.stderr.write("Unable to create the log directory. Logging to screen only.\n")

        VERBOSE = VERBOSE or bool(CONFIG.VERBOSE_LOGS)

        # Start the logger, disable console if needed
        logger.initLogger(console=not QUIET, log_dir=CONFIG.LOG_DIR if log_writable else None,
                          verbose=VERBOSE)

        os.environ['PLEXAPI_CONFIG_PATH'] = os.path.join(DATA_DIR, 'plexapi.config.ini')
        os.environ['PLEXAPI_LOG_PATH'] = os.path.join(CONFIG.LOG_DIR, 'plexapi.log')
        os.environ['PLEXAPI_LOG_LEVEL'] = 'DEBUG'
        plex.initialize_plexapi()

        if DOCKER:
            build = '[Docker] '
        elif FROZEN:
            build = '[Bundle] '
        else:
            build = ''

        logger.info("Starting Tautulli {}".format(
            common.RELEASE
        ))
        logger.info("{}{} {} ({}{})".format(
            build, common.PLATFORM, common.PLATFORM_RELEASE, common.PLATFORM_VERSION,
            ' - {}'.format(common.PLATFORM_LINUX_DISTRO) if common.PLATFORM_LINUX_DISTRO else ''
        ))
        logger.info("{} (UTC{})".format(
            str(SYS_TIMEZONE), SYS_UTC_OFFSET
        ))
        logger.info("Language {}{} / Encoding {}".format(
            SYS_LANGUAGE, f' (override {CONFIG.PMS_LANGUAGE})' if CONFIG.PMS_LANGUAGE else '', SYS_ENCODING
        ))
        logger.info("Python {}".format(
            sys.version.replace('\n', '')
        ))
        logger.info("Program Dir: {}".format(
            PROG_DIR
        ))
        logger.info("Config File: {}".format(
            CONFIG_FILE
        ))

        if DOCKER and not DOCKER_MOUNT:
            logger.warn(
                "Docker /config volume not mounted. Using a Docker volume instead. "
                "All data may be cleared when the container is recreated or updated."
            )

        CONFIG.BACKUP_DIR, _ = check_folder_writable(
            CONFIG.BACKUP_DIR, os.path.join(DATA_DIR, 'backups'), 'backups')
        CONFIG.CACHE_DIR, _ = check_folder_writable(
            CONFIG.CACHE_DIR, os.path.join(DATA_DIR, 'cache'), 'cache')
        CONFIG.EXPORT_DIR, _ = check_folder_writable(
            CONFIG.EXPORT_DIR, os.path.join(DATA_DIR, 'exports'), 'exports')
        CONFIG.NEWSLETTER_DIR, _ = check_folder_writable(
            CONFIG.NEWSLETTER_DIR, os.path.join(DATA_DIR, 'newsletters'), 'newsletters')

        logger.info("Checking database migrations...")
        try:
            migration_state = migration_manager.get_migration_state(config=CONFIG)
        except Exception as e:
            logger.error("Database migration check failed: %s" % e)
            raise SystemExit("Database migration check failed. See logs for details.")

        if migration_state.state == 'empty':
            try:
                migration_manager.check_or_initialize(config=CONFIG)
            except Exception as e:
                logger.error("Database initialization failed: %s" % e)
                raise SystemExit("Database initialization failed. See logs for details.")
        elif migration_state.state == 'up-to-date':
            pass
        elif migration_state.state == 'needs-upgrade':
            logger.info(
                "Database schema upgrade required (current=%s, head=%s).",
                migration_state.current_rev,
                migration_state.head_rev,
            )

            if not maintenance.has_pg_restore():
                logger.error("Database migration requires pg_restore in PATH.")
                raise SystemExit("Database migration requires pg_restore (install it and retry).")

            backup_path = maintenance.make_migration_backup()
            if not backup_path:
                raise SystemExit("Database migration aborted: failed to create backup.")

            logger.info(
                "Database backup created at %s. Verify the upgrade and delete it when ready.",
                backup_path,
            )

            try:
                migration_manager.migrate_database(config=CONFIG)
            except Exception as e:
                logger.error("Database migration failed: %s" % e)
                logger.info("Attempting to restore database from backup...")
                restored = maintenance.restore_backup(backup_path, config=CONFIG)
                if restored:
                    logger.info("Database restored from backup: %s", backup_path)
                else:
                    logger.error("Database restore failed. Backup remains at %s", backup_path)
                raise SystemExit("Database migration failed. See logs for details.")

            logger.info("Database migrations applied successfully.")
        else:
            message = migration_state.message or "Database migrations are required."
            logger.error("Database migration check failed: %s", message)
            raise SystemExit(message)

        # Perform upgrades
        logger.info("Checking if configuration upgrades are required...")
        try:
            upgrade()
        except Exception as e:
            logger.error("Could not perform upgrades: %s" % e)

        # Add notifier configs to logger blacklist
        newsletters.blacklist_logger()
        notifiers.blacklist_logger()
        mobile_app.blacklist_logger()

        # Check if Tautulli has a uuid
        if CONFIG.PMS_UUID == '' or not CONFIG.PMS_UUID:
            logger.debug("Generating UUID...")
            CONFIG.PMS_UUID = generate_uuid()
            CONFIG.write()

        # Check if Tautulli has an API key
        if CONFIG.API_KEY == '':
            logger.debug("Generating API key...")
            CONFIG.API_KEY = generate_uuid()
            CONFIG.write()

        # Check if Tautulli has a jwt_secret
        if CONFIG.JWT_SECRET == '' or not CONFIG.JWT_SECRET or CONFIG.JWT_UPDATE_SECRET:
            logger.debug("Generating JWT secret...")
            CONFIG.JWT_SECRET = generate_uuid()
            CONFIG.JWT_UPDATE_SECRET = False
            CONFIG.write()

        # Get the previous version from the file
        version_lock_file = os.path.join(DATA_DIR, "version.lock")
        prev_version = None
        if os.path.isfile(version_lock_file):
            try:
                with open(version_lock_file, "r") as fp:
                    prev_version = fp.read()
            except IOError as e:
                logger.error("Unable to read previous version from file '%s': %s" %
                             (version_lock_file, e))

        # Get the currently installed version. Returns None, 'win32' or the git
        # hash.
        CURRENT_VERSION, CONFIG.GIT_REMOTE, CONFIG.GIT_BRANCH = versioncheck.get_version()

        # Write current version to a file, so we know which version did work.
        # This allows one to restore to that version. The idea is that if we
        # arrive here, most parts of Tautulli seem to work.
        if CURRENT_VERSION:
            try:
                with open(version_lock_file, "w") as fp:
                    fp.write(CURRENT_VERSION)
            except IOError as e:
                logger.error("Unable to write current version to file '%s': %s" %
                             (version_lock_file, e))

        # Check for new versions
        if CONFIG.CHECK_GITHUB_ON_STARTUP and CONFIG.CHECK_GITHUB:
            try:
                versioncheck.check_update(use_cache=True)
            except:
                logger.exception("Unhandled exception")
                LATEST_VERSION = CURRENT_VERSION
        else:
            LATEST_VERSION = CURRENT_VERSION

        # Get the previous release from the file
        release_file = os.path.join(DATA_DIR, "release.lock")
        PREV_RELEASE = common.RELEASE
        if os.path.isfile(release_file):
            try:
                with open(release_file, "r") as fp:
                    PREV_RELEASE = fp.read()
            except IOError as e:
                logger.error("Unable to read previous release from file '%s': %s" %
                             (release_file, e))

        # Check if the release was updated
        if common.RELEASE != PREV_RELEASE:
            CONFIG.UPDATE_SHOW_CHANGELOG = 1
            CONFIG.write()
            _UPDATE = True

        # Write current release version to file for update checking
        try:
            with open(release_file, "w") as fp:
                fp.write(common.RELEASE)
        except IOError as e:
            logger.error("Unable to write current release to file '%s': %s" %
                         (release_file, e))

        # Store the original umask
        UMASK = os.umask(0)
        os.umask(UMASK)

        _sync_package_globals(
            'CONFIG',
            'CONFIG_FILE',
            'CURRENT_VERSION',
            'LATEST_VERSION',
            'PREV_RELEASE',
            'UPDATE_AVAILABLE',
            'UMASK',
            'DATA_DIR',
            'PROG_DIR',
            'ASSETS_DIR',
            'SYS_TIMEZONE',
            'SYS_UTC_OFFSET',
        )

        _INITIALIZED = True
        return True


def daemonize():
    if threading.activeCount() != 1:
        logger.warn(
            "There are %r active threads. Daemonizing may cause"
            " strange behavior.",
            threading.enumerate())

    sys.stdout.flush()
    sys.stderr.flush()

    # Do first fork
    try:
        pid = os.fork()  # @UndefinedVariable - only available in UNIX
        if pid != 0:
            sys.exit(0)
    except OSError as e:
        raise RuntimeError("1st fork failed: %s [%d]", e.strerror, e.errno)

    os.setsid()

    # Make sure I can read my own files and shut out others
    prev = os.umask(0)  # @UndefinedVariable - only available in UNIX
    os.umask(prev and int('077', 8))

    # Make the child a session-leader by detaching from the terminal
    try:
        pid = os.fork()  # @UndefinedVariable - only available in UNIX
        if pid != 0:
            sys.exit(0)
    except OSError as e:
        raise RuntimeError("2nd fork failed: %s [%d]", e.strerror, e.errno)

    dev_null = open('/dev/null', 'r')
    os.dup2(dev_null.fileno(), sys.stdin.fileno())

    si = open('/dev/null', "r")
    so = open('/dev/null', "a+")
    se = open('/dev/null', "a+")

    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())

    pid = os.getpid()
    logger.info("Daemonized to PID: %d", pid)

    if CREATEPID:
        logger.info("Writing PID %d to %s", pid, PIDFILE)
        with open(PIDFILE, 'w') as fp:
            fp.write("%s\n" % pid)


def launch_browser(host, port, root):
    if not no_browser:
        if host in ('0.0.0.0', '::'):
            host = 'localhost'

        if CONFIG.ENABLE_HTTPS:
            protocol = 'https'
        else:
            protocol = 'http'

        try:
            webbrowser.open('%s://%s:%i%s' % (protocol, host, port, root))
        except Exception as e:
            logger.error("Could not launch browser: %s" % e)


def initialize_scheduler():
    """
    Start the scheduled background tasks. Re-schedule if interval settings changed.
    """

    with SCHED_LOCK:

        # Check if scheduler should be started
        start_jobs = not len(SCHED.get_jobs())

        # Update check
        github_hours = CONFIG.CHECK_GITHUB_INTERVAL if CONFIG.CHECK_GITHUB_INTERVAL and CONFIG.CHECK_GITHUB else 0
        pms_update_check_hours = CONFIG.PMS_UPDATE_CHECK_INTERVAL if 1 <= CONFIG.PMS_UPDATE_CHECK_INTERVAL else 24

        schedule_job(versioncheck.check_update, 'Check GitHub for updates',
                     hours=github_hours, minutes=0, seconds=0, args=(True, True))

        backup_hours = CONFIG.BACKUP_INTERVAL if 1 <= CONFIG.BACKUP_INTERVAL <= 24 else 6

        schedule_job(maintenance.optimize_db, 'Optimize Tautulli database',
                     hours=24, minutes=0, seconds=0)
        schedule_job(maintenance.make_backup, 'Backup Tautulli database',
                     hours=backup_hours, minutes=0, seconds=0, args=(True, True))
        schedule_job(config.make_backup, 'Backup Tautulli config',
                     hours=backup_hours, minutes=0, seconds=0, args=(True, True))

        if WS_CONNECTED and CONFIG.PMS_IP and CONFIG.PMS_TOKEN:
            schedule_job(plextv.get_server_resources, 'Refresh Plex server URLs',
                         hours=12 * (not bool(CONFIG.PMS_URL_MANUAL)), minutes=0, seconds=0)

            schedule_job(activity_pinger.check_server_updates, 'Check for Plex updates',
                         hours=pms_update_check_hours * bool(CONFIG.MONITOR_PMS_UPDATES), minutes=0, seconds=0)

            # Refresh the users list and libraries list
            user_hours = CONFIG.REFRESH_USERS_INTERVAL if 1 <= CONFIG.REFRESH_USERS_INTERVAL <= 24 else 12
            library_hours = CONFIG.REFRESH_LIBRARIES_INTERVAL if 1 <= CONFIG.REFRESH_LIBRARIES_INTERVAL <= 24 else 12

            schedule_job(users.refresh_users, 'Refresh users list',
                         hours=user_hours, minutes=0, seconds=0)
            schedule_job(libraries.refresh_libraries, 'Refresh libraries list',
                         hours=library_hours, minutes=0, seconds=0)

            schedule_job(activity_pinger.connect_server, 'Check for server response',
                         hours=0, minutes=0, seconds=0)
            schedule_job(web_socket.send_ping, 'Websocket ping',
                         hours=0, minutes=0, seconds=10 * bool(CONFIG.WEBSOCKET_MONITOR_PING_PONG))

            schedule_job(plextv.notify_token_expired, 'Check Tautulli Plex token',
                         hours=1, minutes=0, seconds=0)

        else:
            # Cancel all jobs
            schedule_job(plextv.get_server_resources, 'Refresh Plex server URLs',
                         hours=0, minutes=0, seconds=0)

            schedule_job(activity_pinger.check_server_updates, 'Check for Plex updates',
                         hours=0, minutes=0, seconds=0)

            schedule_job(users.refresh_users, 'Refresh users list',
                         hours=0, minutes=0, seconds=0)
            schedule_job(libraries.refresh_libraries, 'Refresh libraries list',
                         hours=0, minutes=0, seconds=0)

            # Schedule job to reconnect server
            schedule_job(activity_pinger.connect_server, 'Check for server response',
                         hours=0, minutes=0, seconds=30, args=(False,))
            schedule_job(web_socket.send_ping, 'Websocket ping',
                         hours=0, minutes=0, seconds=0)

            schedule_job(plextv.notify_token_expired, 'Check Tautulli Plex token',
                         hours=0, minutes=0, seconds=0)

        # Start scheduler
        if start_jobs and len(SCHED.get_jobs()):
            try:
                SCHED.start()
            except Exception as e:
                logger.error(e)


def schedule_job(func, name, hours=0, minutes=0, seconds=0, args=None):
    """
    Start scheduled job if starting or restarting plexpy.
    Reschedule job if Interval Settings have changed.
    Remove job if if Interval Settings changed to 0

    """

    job = SCHED.get_job(name)
    if job:
        if hours == 0 and minutes == 0 and seconds == 0:
            SCHED.remove_job(name)
            logger.info("Removed background task: %s", name)
        elif job.trigger.interval != datetime.timedelta(hours=hours, minutes=minutes):
            SCHED.reschedule_job(
                name, trigger=IntervalTrigger(
                    hours=hours, minutes=minutes, seconds=seconds, timezone=pytz.UTC),
                args=args)
            logger.info("Re-scheduled background task: %s", name)
    elif hours > 0 or minutes > 0 or seconds > 0:
        SCHED.add_job(
            func, id=name, trigger=IntervalTrigger(
                hours=hours, minutes=minutes, seconds=seconds, timezone=pytz.UTC),
            args=args, misfire_grace_time=None)
        logger.info("Scheduled background task: %s", name)


def start():
    global _STARTED

    if _INITIALIZED:
        logger.filter_usernames()

        # Start refreshes on a separate thread
        threading.Thread(target=startup_refresh).start()

        global SCHED
        SCHED = BackgroundScheduler(timezone=pytz.UTC)
        activity_handler.ACTIVITY_SCHED = BackgroundScheduler(timezone=pytz.UTC)
        newsletter_handler.NEWSLETTER_SCHED = BackgroundScheduler(timezone=pytz.UTC)

        # Start the scheduler for stale stream callbacks
        activity_handler.ACTIVITY_SCHED.start()

        # Start background notification thread
        notification_handler.start_threads(num_threads=CONFIG.NOTIFICATION_THREADS)
        notifiers.check_browser_enabled()

        # Schedule newsletters
        newsletter_handler.NEWSLETTER_SCHED.start()
        newsletter_handler.schedule_newsletters()

        # Cancel processing exports
        exporter.cancel_exports()

        if CONFIG.SYSTEM_ANALYTICS:
            global TRACKER
            TRACKER = initialize_tracker()

            # Send system analytics events
            if not CONFIG.FIRST_RUN_COMPLETE:
                analytics_event(name='install')

            elif _UPDATE:
                analytics_event(name='update')

            analytics_event(name='start')

        _STARTED = True


def startup_refresh():
    # Check token hasn't expired
    if CONFIG.PMS_TOKEN:
        plextv.notify_token_expired()

    # Get the real PMS urls for SSL and remote access
    if CONFIG.PMS_TOKEN and CONFIG.PMS_IP and CONFIG.PMS_PORT:
        plextv.get_server_resources()

    # Connect server after server resource is refreshed
    if CONFIG.FIRST_RUN_COMPLETE:
        activity_pinger.connect_server(log=True, startup=True)

    # Refresh the users list on startup
    if CONFIG.PMS_TOKEN and CONFIG.REFRESH_USERS_ON_STARTUP:
        users.refresh_users()

    # Refresh the libraries list on startup
    if CONFIG.PMS_IP and CONFIG.PMS_TOKEN and CONFIG.REFRESH_LIBRARIES_ON_STARTUP:
        libraries.refresh_libraries()


def sig_handler(signum=None, frame=None):
    if signum is not None:
        logger.info("Signal %i caught, saving and exiting...", signum)
        shutdown()


def dbcheck():
    raise RuntimeError("SQLite support has been removed; use Postgres migrations instead.")

def upgrade():
    if CONFIG.UPGRADE_FLAG == 0:
        mobile_app.revalidate_onesignal_ids()
        CONFIG.UPGRADE_FLAG = 1
        CONFIG.write()

    return


def shutdown(restart=False, update=False, checkout=False, reset=False):
    webstart.stop()

    # Shutdown the websocket connection
    if WEBSOCKET:
        web_socket.shutdown()

    if SCHED.running:
        SCHED.shutdown(wait=False)
    if activity_handler.ACTIVITY_SCHED.running:
        activity_handler.ACTIVITY_SCHED.shutdown(wait=False)

    # Stop the notification threads
    for i in range(CONFIG.NOTIFICATION_THREADS):
        NOTIFY_QUEUE.put(None)

    CONFIG.write()

    if update:
        logger.info("Tautulli is updating...")
        try:
            versioncheck.update()
        except Exception as e:
            logger.warn("Tautulli failed to update: %s. Restarting." % e)

    if checkout:
        logger.info("Tautulli is switching the git branch...")
        try:
            versioncheck.checkout_git_branch()
        except Exception as e:
            logger.warn("Tautulli failed to switch git branch: %s. Restarting." % e)

    if reset:
        logger.info("Tautulli is resetting the git install...")
        try:
            versioncheck.reset_git_install()
        except Exception as e:
            logger.warn("Tautulli failed to reset git install: %s. Restarting." % e)

    if CREATEPID:
        logger.info("Removing PID file: %s", PIDFILE)
        try:
            os.remove(PIDFILE)
        except OSError:
            logger.warn("Failed to remove PID file '%s'", PIDFILE)

    if restart:
        logger.info("Tautulli is restarting...")

        exe = sys.executable
        if FROZEN:
            args = [exe]
        else:
            args = [exe, FULL_PATH]
        args += ARGS
        if '--nolaunch' not in args:
            args += ['--nolaunch']

        # Separate out logger so we can shutdown logger after
        if NOFORK:
            logger.info("Running as service, not forking. Exiting...")
        else:
            logger.info("Restarting Tautulli with %s", args)

        if NOFORK:
            pass
        else:
            os.execv(exe, args)

    else:
        logger.info("Tautulli is shutting down...")

    logger.shutdown()

    os._exit(0)


def generate_uuid():
    return uuid.uuid4().hex


def initialize_tracker():
    tracker = GtagMP(
        api_secret='Cl_LjAKUT26AS22YZwqaPw',
        measurement_id='G-NH1M4BYM2P',
        client_id=CONFIG.PMS_UUID
    )
    return tracker


def analytics_event(name, **kwargs):
    event = TRACKER.create_new_event(name=name)
    event.set_event_param('name', common.PRODUCT)
    event.set_event_param('version', common.RELEASE)
    event.set_event_param('install', INSTALL_TYPE)
    event.set_event_param('branch', CONFIG.GIT_BRANCH)
    event.set_event_param('platform', common.PLATFORM)
    event.set_event_param('platformRelease', common.PLATFORM_RELEASE)
    event.set_event_param('platformVersion', common.PLATFORM_VERSION[:100])
    event.set_event_param('linuxDistro', common.PLATFORM_LINUX_DISTRO)
    event.set_event_param('pythonVersion', common.PYTHON_VERSION)
    event.set_event_param('language', SYS_LANGUAGE)
    event.set_event_param('encoding', SYS_ENCODING)
    event.set_event_param('timezone', str(SYS_TIMEZONE))
    event.set_event_param('timezoneUTCOffset', f'UTC{SYS_UTC_OFFSET}')

    for key, value in kwargs.items():
        event.set_event_param(key, value)

    plex_tv = plextv.PlexTV()
    ip_address = plex_tv.get_public_ip(output_format='text')
    geolocation = plex_tv.get_geoip_lookup(ip_address) or {}

    event.set_event_param('country', geolocation.get('country', 'Unknown'))
    event.set_event_param('countryCode', geolocation.get('code', 'Unknown'))

    if TRACKER:
        try:
            TRACKER.send(events=[event])
        except Exception as e:
            logger.warn("Failed to send analytics event for name '%s': %s" % (name, e))


def check_folder_writable(folder, fallback, name):
    if not folder:
        folder = fallback

    if not os.path.exists(folder):
        try:
            os.makedirs(folder)
        except OSError as e:
            logger.error("Could not create %s dir '%s': %s" % (name, folder, e))
            if fallback and folder != fallback:
                logger.warn("Falling back to %s dir '%s'" % (name, fallback))
                return check_folder_writable(None, fallback, name)
            else:
                return folder, None

    if not os.access(folder, os.W_OK):
        logger.error("Cannot write to %s dir '%s'" % (name, folder))
        if fallback and folder != fallback:
            logger.warn("Falling back to %s dir '%s'" % (name, fallback))
            return check_folder_writable(None, fallback, name)
        else:
            return folder, False

    return folder, True


def get_tautulli_info():
    tautulli = {
        'tautulli_install_type': INSTALL_TYPE,
        'tautulli_version': common.RELEASE,
        'tautulli_branch': CONFIG.GIT_BRANCH,
        'tautulli_commit': CURRENT_VERSION,
        'tautulli_platform':common.PLATFORM,
        'tautulli_platform_release': common.PLATFORM_RELEASE,
        'tautulli_platform_version': common.PLATFORM_VERSION,
        'tautulli_platform_linux_distro': common.PLATFORM_LINUX_DISTRO,
        'tautulli_platform_device_name': common.PLATFORM_DEVICE_NAME,
        'tautulli_python_version': common.PYTHON_VERSION,
    }
    return tautulli


def alert_message(msg, title='Tautulli Startup Error'):
    sys.stderr.write("{}: {}\n".format(title, msg))
