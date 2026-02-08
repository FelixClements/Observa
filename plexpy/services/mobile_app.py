# -*- coding: utf-8 -*-

#  This file is part of Tautulli.
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

import requests
import threading
from sqlalchemy import delete, func, select, update

from plexpy.db.models import MobileDevice
from plexpy.db.session import session_scope
from plexpy.util import helpers
from plexpy.util import logger


_ONESIGNAL_APP_ID = '3b4b666a-d557-4b92-acdf-e2c8c4b95357'
_ONESIGNAL_DISABLED = 'onesignal-disabled'

TEMP_DEVICE_TOKENS = {}


def _device_to_dict(device: MobileDevice) -> dict:
    return {
        'id': device.id,
        'device_id': device.device_id,
        'device_token': device.device_token,
        'device_name': device.device_name,
        'platform': device.platform,
        'version': device.version,
        'friendly_name': device.friendly_name,
        'onesignal_id': device.onesignal_id,
        'last_seen': device.last_seen,
        'official': device.official,
    }


def set_temp_device_token(token=None, remove=False, add=False, success=False):
    global TEMP_DEVICE_TOKENS

    if token in TEMP_DEVICE_TOKENS and success:
        if isinstance(TEMP_DEVICE_TOKENS[token], threading.Timer):
            TEMP_DEVICE_TOKENS[token].cancel()
        TEMP_DEVICE_TOKENS[token] = True

    elif token in TEMP_DEVICE_TOKENS and remove:
        if isinstance(TEMP_DEVICE_TOKENS[token], threading.Timer):
            TEMP_DEVICE_TOKENS[token].cancel()
        del TEMP_DEVICE_TOKENS[token]

    elif token not in TEMP_DEVICE_TOKENS and add:
        invalidate_time = 5 * 60  # 5 minutes
        TEMP_DEVICE_TOKENS[token] = threading.Timer(invalidate_time, set_temp_device_token, args=[token, True])
        TEMP_DEVICE_TOKENS[token].start()
        logger._BLACKLIST_WORDS.add(token)


def get_temp_device_token(token=None):
    return TEMP_DEVICE_TOKENS.get(token)


def get_mobile_devices(device_id=None, device_token=None):
    stmt = select(MobileDevice)
    if device_id:
        stmt = stmt.where(MobileDevice.device_id == device_id)
    if device_token:
        stmt = stmt.where(MobileDevice.device_token == device_token)

    with session_scope() as session:
        devices = session.execute(stmt).scalars().all()

    return [_device_to_dict(device) for device in devices]


def get_mobile_device_by_token(device_token=None):
    if not device_token:
        return None

    return get_mobile_devices(device_token=device_token)


def add_mobile_device(device_id=None, device_name=None, device_token=None,
                      platform=None, version=None, friendly_name=None, onesignal_id=None):
    try:
        with session_scope() as session:
            stmt = select(MobileDevice).where(MobileDevice.device_id == device_id)
            device = session.execute(stmt).scalar_one_or_none()
            is_insert = device is None

            if device is None:
                device = MobileDevice(device_id=device_id)
                session.add(device)

            device.device_name = device_name
            device.device_token = device_token
            device.platform = platform
            device.version = version
            device.onesignal_id = onesignal_id
            if friendly_name:
                device.friendly_name = friendly_name

        blacklist_logger()
    except Exception as e:
        logger.warn("Tautulli MobileApp :: Failed to register mobile device in the database: %s." % e)
        return

    if is_insert:
        logger.info("Tautulli MobileApp :: Registered mobile device '%s' in the database." % device_name)
    else:
        logger.info("Tautulli MobileApp :: Re-registered mobile device '%s' in the database." % device_name)

    set_last_seen(device_token=device_token)
    threading.Thread(target=set_official, args=[device_id, onesignal_id]).start()
    return True


def get_mobile_device_config(mobile_device_id=None):
    if str(mobile_device_id).isdigit():
        mobile_device_id = int(mobile_device_id)
    else:
        logger.error("Tautulli MobileApp :: Unable to retrieve mobile device config: invalid mobile_device_id %s." % mobile_device_id)
        return None

    with session_scope() as session:
        device = session.get(MobileDevice, mobile_device_id)
        if device is None:
            return None
        result = _device_to_dict(device)

    if result['onesignal_id'] == _ONESIGNAL_DISABLED:
        result['onesignal_id'] = ''

    return result


def set_mobile_device_config(mobile_device_id=None, **kwargs):
    if str(mobile_device_id).isdigit():
        mobile_device_id = int(mobile_device_id)
    else:
        logger.error("Tautulli MobileApp :: Unable to set existing mobile device: invalid mobile_device_id %s." % mobile_device_id)
        return False

    try:
        with session_scope() as session:
            device = session.get(MobileDevice, mobile_device_id)
            if device is None:
                return False
            device.friendly_name = kwargs.get('friendly_name', '')

        logger.info("Tautulli MobileApp :: Updated mobile device agent: mobile_device_id %s." % mobile_device_id)
        blacklist_logger()
        return True
    except Exception as e:
        logger.warn("Tautulli MobileApp :: Unable to update mobile device: %s." % e)
        return False


def delete_mobile_device(mobile_device_id=None, device_id=None):
    if mobile_device_id:
        if str(mobile_device_id).isdigit():
            mobile_device_id = int(mobile_device_id)
        else:
            logger.error("Tautulli MobileApp :: Unable to delete mobile device: invalid mobile_device_id %s." % mobile_device_id)
            return False
        logger.debug("Tautulli MobileApp :: Deleting mobile_device_id %s from the database." % mobile_device_id)
        with session_scope() as session:
            session.execute(delete(MobileDevice).where(MobileDevice.id == mobile_device_id))
        return True
    elif device_id:
        logger.debug("Tautulli MobileApp :: Deleting device_id %s from the database." % device_id)
        with session_scope() as session:
            session.execute(delete(MobileDevice).where(MobileDevice.device_id == device_id))
        return True
    else:
        return False


def set_official(device_id, onesignal_id):
    official = validate_onesignal_id(onesignal_id=onesignal_id)
    platform = 'android' if official > 0 else None

    try:
        with session_scope() as session:
            session.execute(
                update(MobileDevice)
                .where(MobileDevice.device_id == device_id)
                .values(
                    official=official,
                    platform=func.coalesce(MobileDevice.platform, platform),
                )
            )
    except Exception as e:
        logger.warn("Tautulli MobileApp :: Failed to set official flag for device: %s." % e)
        return


def set_last_seen(device_token=None):
    last_seen = helpers.timestamp()

    try:
        with session_scope() as session:
            session.execute(
                update(MobileDevice)
                .where(MobileDevice.device_token == device_token)
                .values(last_seen=last_seen)
            )
    except Exception as e:
        logger.warn("Tautulli MobileApp :: Failed to set last_seen time for device: %s." % e)
        return


def validate_onesignal_id(onesignal_id):
    if onesignal_id is None:
        return 0
    elif onesignal_id == _ONESIGNAL_DISABLED:
        return 2

    headers = {'Content-Type': 'application/json'}

    logger.info("Tautulli MobileApp :: Validating OneSignal ID")
    try:
        r = requests.get(f'https://api.onesignal.com/apps/{_ONESIGNAL_APP_ID}/subscriptions/{onesignal_id}/user/identity', headers=headers)
        status_code = r.status_code
        logger.info("Tautulli MobileApp :: OneSignal ID validation returned status code %s", status_code)
        return int(status_code == 200)
    except Exception as e:
        logger.warn("Tautulli MobileApp :: Failed to validate OneSignal ID: %s." % e)
        return -1


def revalidate_onesignal_ids():
    for device in get_mobile_devices():
        set_official(device['device_id'], device['onesignal_id'])


def blacklist_logger():
    devices = get_mobile_devices()
    for d in devices:
        logger.blacklist_config(d)
