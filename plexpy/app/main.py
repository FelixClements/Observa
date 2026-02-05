#!/usr/bin/env python

# -*- coding: utf-8 -*-

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

import os
import sys

_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir))


import argparse
import datetime
import locale
import platformdirs
import pytz
import signal
import time
import tzlocal

import plexpy
from plexpy.app import bootstrap as _bootstrap
from plexpy.app import common
from plexpy.config import core as config
from plexpy.util import helpers
from plexpy.util import logger
from plexpy.web import webstart

# Register signals, such as CTRL + C
signal.signal(signal.SIGINT, plexpy.sig_handler)
signal.signal(signal.SIGTERM, plexpy.sig_handler)


def _sync_bootstrap_globals():
    for key in (
        'PROG_DIR',
        'FULL_PATH',
        'ASSETS_DIR',
        'ARGS',
        'SYS_PLATFORM',
        'SYS_LANGUAGE',
        'SYS_ENCODING',
        'SYS_TIMEZONE',
        'SYS_UTC_OFFSET',
        'QUIET',
        'VERBOSE',
        'DAEMON',
        'CREATEPID',
        'PIDFILE',
        'NOFORK',
        'DOCKER',
        'DOCKER_MOUNT',
        'FROZEN',
        'DEV',
        'DATA_DIR',
    ):
        setattr(_bootstrap, key, getattr(plexpy, key))


def main():
    """
    Tautulli application entry point. Parses arguments, setups encoding and
    initializes the application.
    """

    # Fixed paths to Tautulli
    if hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):
        plexpy.FROZEN = True
        plexpy.FULL_PATH = os.path.abspath(sys.executable)
        plexpy.PROG_DIR = sys._MEIPASS
    else:
        plexpy.FULL_PATH = os.path.join(_ROOT_DIR, 'Tautulli.py')
        plexpy.PROG_DIR = _ROOT_DIR

    plexpy.ASSETS_DIR = os.path.join(plexpy.PROG_DIR, 'plexpy', 'web', 'assets')

    plexpy.ARGS = sys.argv[1:]

    # From sickbeard
    plexpy.SYS_PLATFORM = sys.platform
    plexpy.SYS_ENCODING = None

    try:

        # Attempt to get the system's locale settings
        language_code, encoding = locale.getlocale()

        # Get the preferred encoding
        encoding = locale.getpreferredencoding()

        # Assign values to application-specific variable
        plexpy.SYS_LANGUAGE = language_code
        plexpy.SYS_ENCODING = encoding

    except (locale.Error, IOError):
        pass

    # for OSes that are poorly configured I'll just force UTF-8
    if not plexpy.SYS_ENCODING or plexpy.SYS_ENCODING in ('ANSI_X3.4-1968', 'US-ASCII', 'ASCII'):
        plexpy.SYS_ENCODING = 'UTF-8'

    # Set up and gather command line arguments
    parser = argparse.ArgumentParser(
        description='A Python based monitoring and tracking tool for Plex Media Server.')

    parser.add_argument(
        '-v', '--verbose', action='store_true', help='Increase console logging verbosity')
    parser.add_argument(
        '-q', '--quiet', action='store_true', help='Turn off console logging')
    parser.add_argument(
        '-d', '--daemon', action='store_true', help='Run as a daemon')
    parser.add_argument(
        '-p', '--port', type=int, help='Force Tautulli to run on a specified port')
    parser.add_argument(
        '--dev', action='store_true', help='Start Tautulli in the development environment')
    parser.add_argument(
        '--datadir', help='Specify a directory where to store your data files')
    parser.add_argument(
        '--config', help='Specify a config file to use')
    parser.add_argument(
        '--migrate-db', action='store_true', help='Run database migrations and exit')
    parser.add_argument(
        '--nolaunch', action='store_true', help='Prevent browser from launching on startup')
    parser.add_argument(
        '--pidfile', help='Create a pid file (only relevant when running as a daemon)')
    parser.add_argument(
        '--nofork', action='store_true', help='Start Tautulli as a service, do not fork when restarting')

    args = parser.parse_args()

    if args.verbose:
        plexpy.VERBOSE = True
    if args.quiet:
        plexpy.QUIET = True

    # Do an initial setup of the logger.
    # Require verbose for pre-initilization to see critical errors
    logger.initLogger(console=not plexpy.QUIET, log_dir=False, verbose=True)

    try:
        plexpy.SYS_TIMEZONE = tzlocal.get_localzone()
    except (pytz.UnknownTimeZoneError, LookupError, ValueError) as e:
        logger.error("Could not determine system timezone: %s" % e)
        plexpy.SYS_TIMEZONE = pytz.UTC

    plexpy.SYS_UTC_OFFSET = datetime.datetime.now(plexpy.SYS_TIMEZONE).strftime('%z')

    if helpers.bool_true(os.getenv('TAUTULLI_DOCKER', False)):
        plexpy.DOCKER = True
        plexpy.DOCKER_MOUNT = not os.path.isfile('/config/DOCKER')

    if args.dev:
        plexpy.DEV = True
        logger.debug("Tautulli is running in the dev environment.")

    if args.daemon:
        plexpy.DAEMON = True
        plexpy.QUIET = True

    if args.nofork:
        plexpy.NOFORK = True
        logger.info("Tautulli is running as a service, it will not fork when restarted.")

    if args.pidfile:
        plexpy.PIDFILE = str(args.pidfile)

        # If the pidfile already exists, plexpy may still be running, so
        # exit
        if os.path.exists(plexpy.PIDFILE):
            try:
                with open(plexpy.PIDFILE, 'r') as fp:
                    pid = int(fp.read())
            except IOError as e:
                raise SystemExit("Unable to read PID file: %s", e)

            try:
                os.kill(pid, 0)
            except OSError:
                logger.warn("PID file '%s' already exists, but PID %d is "
                            "not running. Ignoring PID file." %
                            (plexpy.PIDFILE, pid))
            else:
                # The pidfile exists and points to a live PID. plexpy may
                # still be running, so exit.
                raise SystemExit("PID file '%s' already exists. Exiting." %
                                 plexpy.PIDFILE)

        # The pidfile is only useful in daemon mode, make sure we can write the
        # file properly
        if plexpy.DAEMON:
            plexpy.CREATEPID = True

            try:
                with open(plexpy.PIDFILE, 'w') as fp:
                    fp.write("pid\n")
            except IOError as e:
                raise SystemExit("Unable to write PID file: %s", e)
        else:
            logger.warn("Not running in daemon mode. PID file creation " \
                        "disabled.")

    # Determine which data directory and config file to use
    if args.datadir:
        plexpy.DATA_DIR = args.datadir
    elif plexpy.FROZEN:
        plexpy.DATA_DIR = platformdirs.user_data_dir("Tautulli", False)
    else:
        plexpy.DATA_DIR = plexpy.PROG_DIR

    if args.config:
        config_file = args.config
    else:
        config_file = os.path.join(plexpy.DATA_DIR, config.FILENAME)

    # Try to create the DATA_DIR if it doesn't exist
    if not os.path.exists(plexpy.DATA_DIR):
        try:
            os.makedirs(plexpy.DATA_DIR)
        except OSError:
            raise SystemExit(
                'Could not create data directory: ' + plexpy.DATA_DIR + '. Exiting....')

    # Make sure the DATA_DIR is writeable
    test_file = os.path.join(plexpy.DATA_DIR, '.TEST')
    try:
        with open(test_file, 'w'):
            pass
    except IOError:
        raise SystemExit(
            'Cannot write to the data directory: ' + plexpy.DATA_DIR + '. Exiting...')
    finally:
        try:
            os.remove(test_file)
        except OSError:
            pass

    if args.migrate_db:
        from plexpy.db.migrations import manager as migration_manager

        try:
            migration_manager.migrate_database(config_path=config_file)
        except Exception as e:
            logger.error("Database migration failed: %s" % e)
            raise SystemExit(1)

        logger.info("Database migrations applied successfully.")
        return

    _sync_bootstrap_globals()

    if plexpy.DAEMON:
        plexpy.daemonize()

    # Read config and start logging
    plexpy.initialize(config_file)

    # Start the background threads
    plexpy.start()

    # Force the http port if necessary
    if args.port:
        plexpy.HTTP_PORT = args.port
        logger.info('Using forced web server port: %i', plexpy.HTTP_PORT)
    else:
        plexpy.HTTP_PORT = int(plexpy.CONFIG.HTTP_PORT)

    # Try to start the server. Will exit here is address is already in use.
    webstart.start()

    # Open webbrowser
    if plexpy.CONFIG.LAUNCH_BROWSER and not args.nolaunch and not plexpy.DEV:
        plexpy.launch_browser(plexpy.CONFIG.HTTP_HOST, plexpy.HTTP_PORT,
                              plexpy.HTTP_ROOT)

    wait()


def wait():
    logger.info("Tautulli is ready!")

    # Wait endlessly for a signal to happen
    while True:
        if not plexpy.SIGNAL:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                plexpy.SIGNAL = 'shutdown'
        else:
            logger.info('Received signal: %s', plexpy.SIGNAL)

            if plexpy.SIGNAL == 'shutdown':
                plexpy.shutdown()
            elif plexpy.SIGNAL == 'restart':
                plexpy.shutdown(restart=True)
            elif plexpy.SIGNAL == 'checkout':
                plexpy.shutdown(restart=True, checkout=True)
            elif plexpy.SIGNAL == 'reset':
                plexpy.shutdown(restart=True, reset=True)
            elif plexpy.SIGNAL == 'update':
                plexpy.shutdown(restart=True, update=True)
            else:
                logger.error('Unknown signal. Shutting down...')
                plexpy.shutdown()

            plexpy.SIGNAL = None


if __name__ == "__main__":
    main()
