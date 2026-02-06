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

from collections import defaultdict
import json

import plexpy
from sqlalchemy import Integer, delete, func, insert, select, update
from sqlalchemy.exc import IntegrityError

from plexpy.integrations import pmsconnect
from plexpy.services import libraries
from plexpy.services import users
from plexpy.db import maintenance
from plexpy.db import queries
from plexpy.db.models import Session as SessionModel
from plexpy.db.models import SessionContinued, SessionHistory, SessionHistoryMediaInfo, SessionHistoryMetadata
from plexpy.db.queries import time as time_queries
from plexpy.db.session import session_scope
from plexpy.util import helpers
from plexpy.util import logger


class ActivityProcessor(object):

    def write_session(self, session=None, notify=True):
        if session:
            def _optional_int(value):
                if value is None or value == '':
                    return None
                return helpers.cast_to_int(value)

            session_key = _optional_int(session.get('session_key'))
            rating_key = _optional_int(session.get('rating_key'))

            values = {'session_key': session.get('session_key', ''),
                      'session_id': session.get('session_id', ''),
                      'transcode_key': session.get('transcode_key', ''),
                      'section_id': session.get('section_id', ''),
                      'rating_key': session.get('rating_key', ''),
                      'media_type': session.get('media_type', ''),
                      'state': session.get('state', ''),
                      'user_id': session.get('user_id', ''),
                      'user': session.get('user', ''),
                      'machine_id': session.get('machine_id', ''),
                      'title': session.get('title', ''),
                      'parent_title': session.get('parent_title', ''),
                      'grandparent_title': session.get('grandparent_title', ''),
                      'original_title': session.get('original_title', ''),
                      'full_title': session.get('full_title', ''),
                      'media_index': session.get('media_index', ''),
                      'parent_media_index': session.get('parent_media_index', ''),
                      'thumb': session.get('thumb', ''),
                      'parent_thumb': session.get('parent_thumb', ''),
                      'grandparent_thumb': session.get('grandparent_thumb', ''),
                      'year': session.get('year', ''),
                      'friendly_name': session.get('friendly_name', ''),
                      'ip_address': session.get('ip_address', ''),
                      'bandwidth': session.get('bandwidth', 0),
                      'location': session.get('location', ''),
                      'player': session.get('player', ''),
                      'product': session.get('product', ''),
                      'platform': session.get('platform', ''),
                      'parent_rating_key': session.get('parent_rating_key', ''),
                      'grandparent_rating_key': session.get('grandparent_rating_key', ''),
                      'originally_available_at': session.get('originally_available_at', ''),
                      'added_at': session.get('added_at', ''),
                      'guid': session.get('guid', ''),
                      'view_offset': session.get('view_offset', ''),
                      'duration': session.get('duration', '') or 0,
                      'video_decision': session.get('video_decision', ''),
                      'audio_decision': session.get('audio_decision', ''),
                      'transcode_decision': session.get('transcode_decision', ''),
                      'width': session.get('width', ''),
                      'height': session.get('height', ''),
                      'container': session.get('container', ''),
                      'bitrate': session.get('bitrate', ''),
                      'video_codec': session.get('video_codec', ''),
                      'video_bitrate': session.get('video_bitrate', ''),
                      'video_width': session.get('video_width', ''),
                      'video_height': session.get('video_height', ''),
                      'video_resolution': session.get('video_resolution', ''),
                      'video_framerate': session.get('video_framerate', ''),
                      'video_scan_type': session.get('video_scan_type', ''),
                      'video_full_resolution': session.get('video_full_resolution', ''),
                      'video_dynamic_range': session.get('video_dynamic_range', ''),
                      'aspect_ratio': session.get('aspect_ratio', ''),
                      'audio_codec': session.get('audio_codec', ''),
                      'audio_bitrate': session.get('audio_bitrate', ''),
                      'audio_channels': session.get('audio_channels', ''),
                      'audio_language': session.get('audio_language', ''),
                      'audio_language_code': session.get('audio_language_code', ''),
                      'subtitle_codec': session.get('subtitle_codec', ''),
                      'subtitle_forced': session.get('subtitle_forced', ''),
                      'subtitle_language': session.get('subtitle_language', ''),
                      'transcode_protocol': session.get('transcode_protocol', ''),
                      'transcode_container': session.get('transcode_container', ''),
                      'transcode_video_codec': session.get('transcode_video_codec', ''),
                      'transcode_audio_codec': session.get('transcode_audio_codec', ''),
                      'transcode_audio_channels': session.get('transcode_audio_channels', ''),
                      'transcode_width': session.get('stream_video_width', ''),
                      'transcode_height': session.get('stream_video_height', ''),
                      'transcode_hw_decoding': session.get('transcode_hw_decoding', ''),
                      'transcode_hw_encoding': session.get('transcode_hw_encoding', ''),
                      'synced_version': session.get('synced_version', ''),
                      'synced_version_profile': session.get('synced_version_profile', ''),
                      'optimized_version': session.get('optimized_version', ''),
                      'optimized_version_profile': session.get('optimized_version_profile', ''),
                      'optimized_version_title': session.get('optimized_version_title', ''),
                      'stream_bitrate': session.get('stream_bitrate', ''),
                      'stream_video_resolution': session.get('stream_video_resolution', ''),
                      'quality_profile': session.get('quality_profile', ''),
                      'stream_container_decision': session.get('stream_container_decision', ''),
                      'stream_container': session.get('stream_container', ''),
                      'stream_video_decision': session.get('stream_video_decision', ''),
                      'stream_video_codec': session.get('stream_video_codec', ''),
                      'stream_video_bitrate': session.get('stream_video_bitrate', ''),
                      'stream_video_width': session.get('stream_video_width', ''),
                      'stream_video_height': session.get('stream_video_height', ''),
                      'stream_video_framerate': session.get('stream_video_framerate', ''),
                      'stream_video_scan_type': session.get('stream_video_scan_type', ''),
                      'stream_video_full_resolution': session.get('stream_video_full_resolution', ''),
                      'stream_video_dynamic_range': session.get('stream_video_dynamic_range', ''),
                      'stream_audio_decision': session.get('stream_audio_decision', ''),
                      'stream_audio_codec': session.get('stream_audio_codec', ''),
                      'stream_audio_bitrate': session.get('stream_audio_bitrate', ''),
                      'stream_audio_channels': session.get('stream_audio_channels', ''),
                      'stream_audio_language': session.get('stream_audio_language', ''),
                      'stream_audio_language_code': session.get('stream_audio_language_code', ''),
                      'stream_subtitle_decision': session.get('stream_subtitle_decision', ''),
                      'stream_subtitle_codec': session.get('stream_subtitle_codec', ''),
                      'stream_subtitle_forced': session.get('stream_subtitle_forced', ''),
                      'stream_subtitle_language': session.get('stream_subtitle_language', ''),
                      'subtitles': session.get('subtitles', 0),
                      'live': session.get('live', 0),
                      'live_uuid': session.get('live_uuid', ''),
                      'secure': session.get('secure', None),
                      'relayed': session.get('relayed', 0),
                      'rating_key_websocket': session.get('rating_key_websocket', ''),
                      'raw_stream_info': json.dumps(session),
                      'channel_call_sign': session.get('channel_call_sign', ''),
                      'channel_id': session.get('channel_id', ''),
                      'channel_identifier': session.get('channel_identifier', ''),
                      'channel_title': session.get('channel_title', ''),
                      'channel_thumb': session.get('channel_thumb', ''),
                      'channel_vcn': session.get('channel_vcn', ''),
                      'stopped': helpers.timestamp()
                      }

            values['session_key'] = session_key
            values['rating_key'] = rating_key

            for column in SessionModel.__table__.columns:
                if column.name not in values:
                    continue
                if isinstance(column.type, Integer):
                    values[column.name] = _optional_int(values[column.name])

            keys = {'session_key': session_key}

            cleaned_keys = {key: value for key, value in keys.items() if value is not None}
            inserted = False
            inserted_id = None

            with session_scope() as db_session:
                if cleaned_keys:
                    conditions = [SessionModel.session_key == session_key]
                    stmt = update(SessionModel).where(*conditions).values(**values)
                    result = db_session.execute(stmt)
                    if not result.rowcount or result.rowcount == 0:
                        inserted = True
                else:
                    inserted = True

                if inserted:
                    stmt = insert(SessionModel).values(**values).returning(SessionModel.id)
                    try:
                        inserted_id = db_session.execute(stmt).scalar_one_or_none()
                    except IntegrityError:
                        inserted = False
                        if cleaned_keys:
                            stmt = (
                                update(SessionModel)
                                .where(SessionModel.session_key == session_key)
                                .values(**values)
                            )
                            db_session.execute(stmt)

            if inserted:
                # If it's our first write then time stamp it.
                started = helpers.timestamp()
                initial_stream = self.is_initial_stream(user_id=values['user_id'],
                                                        machine_id=values['machine_id'],
                                                        media_type=values['media_type'],
                                                        started=started)
                timestamp = {'started': started, 'initial_stream': initial_stream}

                with session_scope() as db_session:
                    if inserted_id is not None:
                        stmt = update(SessionModel).where(SessionModel.id == inserted_id).values(**timestamp)
                        db_session.execute(stmt)
                    elif cleaned_keys:
                        stmt = (
                            update(SessionModel)
                            .where(SessionModel.session_key == session_key)
                            .values(**timestamp)
                        )
                        db_session.execute(stmt)

                # Check if any notification agents have notifications enabled
                if notify:
                    session.update(timestamp)
                    plexpy.NOTIFY_QUEUE.put({'stream_data': session.copy(), 'notify_action': 'on_play'})

                # Add Live TV library if it hasn't been added
                if values['live']:
                    libraries.add_live_tv_library()

                return True

    def write_session_history(self, session=None, import_metadata=None, is_import=False, import_ignore_interval=0):
        section_id = session['section_id'] if not is_import else import_metadata['section_id']

        if not is_import:
            user_data = users.Users()
            user_details = user_data.get_details(user_id=session['user_id'])

            library_data = libraries.Libraries()
            library_details = library_data.get_details(section_id=section_id)

            # Return false if failed to retrieve user or library details
            if not user_details or not library_details:
                return False

        if session:
            logging_enabled = False

            # Reload json from raw stream info
            if session.get('raw_stream_info'):
                raw_stream_info = json.loads(session['raw_stream_info'])
                # Don't overwrite id, session_key, stopped, view_offset
                raw_stream_info.pop('id', None)
                raw_stream_info.pop('session_key', None)
                raw_stream_info.pop('stopped', None)
                raw_stream_info.pop('view_offset', None)
                session.update(raw_stream_info)

            session = defaultdict(str, session)

            if is_import:
                if str(session['stopped']).isdigit():
                    stopped = int(session['stopped'])
                else:
                    stopped = helpers.timestamp()
            elif session['stopped']:
                stopped = int(session['stopped'])
            else:
                stopped = helpers.timestamp()
                self.set_session_state(session_key=session['session_key'],
                                       state='stopped',
                                       stopped=stopped)

            if not is_import:
                self.write_continued_session(user_id=session['user_id'],
                                             machine_id=session['machine_id'],
                                             media_type=session['media_type'],
                                             stopped=stopped)

            if str(session['rating_key']).isdigit() and session['media_type'] in ('movie', 'episode', 'track'):
                logging_enabled = True
            else:
                logger.debug("Tautulli ActivityProcessor :: Session %s ratingKey %s not logged. "
                             "Does not meet logging criteria. Media type is '%s'" %
                             (session['session_key'], session['rating_key'], session['media_type']))
                return session['id']

            real_play_time = stopped - helpers.cast_to_int(session['started']) - helpers.cast_to_int(session['paused_counter'])

            if not is_import and plexpy.CONFIG.LOGGING_IGNORE_INTERVAL:
                if (session['media_type'] == 'movie' or session['media_type'] == 'episode') and \
                        (real_play_time < int(plexpy.CONFIG.LOGGING_IGNORE_INTERVAL)):
                    logging_enabled = False
                    logger.debug("Tautulli ActivityProcessor :: Play duration for session %s ratingKey %s is %s secs "
                                 "which is less than %s seconds, so we're not logging it." %
                                 (session['session_key'], session['rating_key'], str(real_play_time),
                                  plexpy.CONFIG.LOGGING_IGNORE_INTERVAL))
            if not is_import and session['media_type'] == 'track':
                if real_play_time < 15 and helpers.cast_to_int(session['duration']) >= 30:
                    logging_enabled = False
                    logger.debug("Tautulli ActivityProcessor :: Play duration for session %s ratingKey %s is %s secs, "
                                 "looks like it was skipped so we're not logging it" %
                                 (session['session_key'], session['rating_key'], str(real_play_time)))
            elif is_import and import_ignore_interval:
                if (session['media_type'] == 'movie' or session['media_type'] == 'episode') and \
                        (real_play_time < int(import_ignore_interval)):
                    logging_enabled = False
                    logger.debug("Tautulli ActivityProcessor :: Play duration for ratingKey %s is %s secs which is less than %s "
                                 "seconds, so we're not logging it." %
                                 (session['rating_key'], str(real_play_time), import_ignore_interval))

            if not is_import and not user_details['keep_history']:
                logging_enabled = False
                logger.debug("Tautulli ActivityProcessor :: History logging for user '%s' is disabled." % user_details['username'])
            elif not is_import and not library_details['keep_history']:
                logging_enabled = False
                logger.debug("Tautulli ActivityProcessor :: History logging for library '%s' is disabled." % library_details['section_name'])

            if logging_enabled:
                media_info = {}

                # Fetch metadata first so we can return false if it fails
                if not is_import:
                    logger.debug("Tautulli ActivityProcessor :: Fetching metadata for item ratingKey %s" % session['rating_key'])
                    pms_connect = pmsconnect.PmsConnect()
                    if session['live']:
                        metadata = pms_connect.get_metadata_details(rating_key=str(session['rating_key']),
                                                                    cache_key=session['session_key'],
                                                                    return_cache=True)
                    else:
                        metadata = pms_connect.get_metadata_details(rating_key=str(session['rating_key']))

                    if session['live'] and not metadata:
                        metadata = session
                    elif not metadata:
                        return False
                    else:
                        if 'media_info' in metadata and len(metadata['media_info']) > 0:
                            media_info = metadata['media_info'][0]
                else:
                    metadata = import_metadata
                    ## TODO: Fix media info from imports. Temporary media info from import session.
                    media_info = session

                # logger.debug("Tautulli ActivityProcessor :: Attempting to write sessionKey %s to session_history table..."
                #              % session['session_key'])
                values = {'started': session['started'],
                          'stopped': stopped,
                          'rating_key': session['rating_key'],
                          'parent_rating_key': session['parent_rating_key'],
                          'grandparent_rating_key': session['grandparent_rating_key'],
                          'media_type': session['media_type'],
                          'user_id': session['user_id'],
                          'user': session['user'],
                          'ip_address': session['ip_address'],
                          'paused_counter': session['paused_counter'],
                          'player': session['player'],
                          'product': session['product'],
                          'product_version': session['product_version'],
                          'platform': session['platform'],
                          'platform_version': session['platform_version'],
                          'profile': session['profile'],
                          'machine_id': session['machine_id'],
                          'bandwidth': session['bandwidth'],
                          'location': session['location'],
                          'quality_profile': session['quality_profile'],
                          'view_offset': session['view_offset'],
                          'section_id': metadata['section_id'],
                          'secure': session['secure'],
                          'relayed': session['relayed']
                          }

                # logger.debug("Tautulli ActivityProcessor :: Writing sessionKey %s session_history transaction..."
                #              % session['session_key'])
                def _optional_int(value):
                    if value is None or value == '':
                        return None
                    try:
                        return int(value)
                    except (TypeError, ValueError):
                        return None

                def _dedupe_clause(column, value):
                    if value is None:
                        return column.is_(None)
                    return column == value

                dedupe_user_id = _optional_int(session.get('user_id'))
                dedupe_rating_key = _optional_int(session.get('rating_key'))
                dedupe_started = _optional_int(session.get('started'))
                dedupe_machine_id = session.get('machine_id') or None

                last_id = None
                inserted = False
                with session_scope() as db_session:
                    dedupe_conditions = [
                        _dedupe_clause(SessionHistory.user_id, dedupe_user_id),
                        _dedupe_clause(SessionHistory.rating_key, dedupe_rating_key),
                        _dedupe_clause(SessionHistory.started, dedupe_started),
                        _dedupe_clause(SessionHistory.machine_id, dedupe_machine_id),
                    ]
                    stmt = (
                        select(SessionHistory.id)
                        .where(*dedupe_conditions)
                        .order_by(SessionHistory.id.desc())
                        .limit(1)
                    )
                    existing_id = db_session.execute(stmt).scalar_one_or_none()
                    if existing_id:
                        last_id = existing_id
                        stmt = (
                            update(SessionHistory)
                            .where(SessionHistory.id == existing_id)
                            .values(
                                stopped=stopped,
                                view_offset=values['view_offset'],
                                paused_counter=values['paused_counter'],
                            )
                        )
                        db_session.execute(stmt)
                    else:
                        stmt = insert(SessionHistory).values(**values).returning(SessionHistory.id)
                        last_id = db_session.execute(stmt).scalar_one_or_none()
                        inserted = True

                if inserted and last_id:
                    self.group_history(last_id, session, metadata)

                if not last_id:
                    return session['id']
                
                # logger.debug("Tautulli ActivityProcessor :: Successfully written history item, last id for session_history is %s"
                #              % last_id)

                # Write the session_history_media_info table

                # logger.debug("Tautulli ActivityProcessor :: Attempting to write to sessionKey %s session_history_media_info table..."
                #              % session['session_key'])
                keys = {'id': last_id}
                values = {'rating_key': session['rating_key'],
                          'video_decision': session['video_decision'],
                          'audio_decision': session['audio_decision'],
                          'transcode_decision': session['transcode_decision'],
                          'duration': session['duration'],
                          'container': session['container'],
                          'bitrate': session['bitrate'],
                          'width': session['width'],
                          'height': session['height'],
                          'video_bit_depth': session['video_bit_depth'],
                          'video_bitrate': session['video_bitrate'],
                          'video_codec': session['video_codec'],
                          'video_codec_level': session['video_codec_level'],
                          'video_width': session['video_width'],
                          'video_height': session['video_height'],
                          'video_resolution': session['video_resolution'],
                          'video_framerate': session['video_framerate'],
                          'video_scan_type': session['video_scan_type'],
                          'video_full_resolution': session['video_full_resolution'],
                          'video_dynamic_range': session['video_dynamic_range'],
                          'aspect_ratio': session['aspect_ratio'],
                          'audio_codec': session['audio_codec'],
                          'audio_bitrate': session['audio_bitrate'],
                          'audio_channels': session['audio_channels'],
                          'audio_language': session['audio_language'],
                          'audio_language_code': session['audio_language_code'],
                          'subtitle_codec': session['subtitle_codec'],
                          'subtitle_forced': session['subtitle_forced'],
                          'subtitle_language': session['subtitle_language'],
                          'transcode_protocol': session['transcode_protocol'],
                          'transcode_container': session['transcode_container'],
                          'transcode_video_codec': session['transcode_video_codec'],
                          'transcode_audio_codec': session['transcode_audio_codec'],
                          'transcode_audio_channels': session['transcode_audio_channels'],
                          'transcode_width': session['transcode_width'],
                          'transcode_height': session['transcode_height'],
                          'transcode_hw_requested': session['transcode_hw_requested'],
                          'transcode_hw_full_pipeline': session['transcode_hw_full_pipeline'],
                          'transcode_hw_decoding': session['transcode_hw_decoding'],
                          'transcode_hw_decode': session['transcode_hw_decode'],
                          'transcode_hw_decode_title': session['transcode_hw_decode_title'],
                          'transcode_hw_encoding': session['transcode_hw_encoding'],
                          'transcode_hw_encode': session['transcode_hw_encode'],
                          'transcode_hw_encode_title': session['transcode_hw_encode_title'],
                          'stream_container': session['stream_container'],
                          'stream_container_decision': session['stream_container_decision'],
                          'stream_bitrate': session['stream_bitrate'],
                          'stream_video_decision': session['stream_video_decision'],
                          'stream_video_bitrate': session['stream_video_bitrate'],
                          'stream_video_codec': session['stream_video_codec'],
                          'stream_video_codec_level': session['stream_video_codec_level'],
                          'stream_video_bit_depth': session['stream_video_bit_depth'],
                          'stream_video_height': session['stream_video_height'],
                          'stream_video_width': session['stream_video_width'],
                          'stream_video_resolution': session['stream_video_resolution'],
                          'stream_video_framerate': session['stream_video_framerate'],
                          'stream_video_scan_type': session['stream_video_scan_type'],
                          'stream_video_full_resolution': session['stream_video_full_resolution'],
                          'stream_video_dynamic_range': session['stream_video_dynamic_range'],
                          'stream_audio_decision': session['stream_audio_decision'],
                          'stream_audio_codec': session['stream_audio_codec'],
                          'stream_audio_bitrate': session['stream_audio_bitrate'],
                          'stream_audio_channels': session['stream_audio_channels'],
                          'stream_audio_language': session['stream_audio_language'],
                          'stream_audio_language_code': session['stream_audio_language_code'],
                          'stream_subtitle_decision': session['stream_subtitle_decision'],
                          'stream_subtitle_codec': session['stream_subtitle_codec'],
                          'stream_subtitle_container': session['stream_subtitle_container'],
                          'stream_subtitle_forced': session['stream_subtitle_forced'],
                          'stream_subtitle_language': session['stream_subtitle_language'],
                          'subtitles': session['subtitles'],
                          'synced_version': session['synced_version'],
                          'synced_version_profile': session['synced_version_profile'],
                          'optimized_version': session['optimized_version'],
                          'optimized_version_profile': session['optimized_version_profile'],
                          'optimized_version_title': session['optimized_version_title']
                          }

                def _optional_int(value):
                    if value is None or value == '':
                        return None
                    return helpers.cast_to_int(value)

                for column in SessionHistoryMediaInfo.__table__.columns:
                    if column.name in values and isinstance(column.type, Integer):
                        values[column.name] = _optional_int(values[column.name])

                # logger.debug("Tautulli ActivityProcessor :: Writing sessionKey %s session_history_media_info transaction..."
                #              % session['session_key'])
                with session_scope() as db_session:
                    stmt = (
                        update(SessionHistoryMediaInfo)
                        .where(SessionHistoryMediaInfo.id == last_id)
                        .values(**values)
                    )
                    result = db_session.execute(stmt)
                    if not result.rowcount or result.rowcount == 0:
                        insert_values = {**values, **keys}
                        db_session.execute(insert(SessionHistoryMediaInfo).values(**insert_values))

                # Write the session_history_metadata table
                directors = ";".join(metadata['directors'])
                writers = ";".join(metadata['writers'])
                actors = ";".join(metadata['actors'])
                genres = ";".join(metadata['genres'])
                labels = ";".join(metadata['labels'])

                marker_credits_first = None
                marker_credits_final = None
                for marker in metadata['markers']:
                    if marker['first']:
                        marker_credits_first = marker['start_time_offset']
                    if marker['final']:
                        marker_credits_final = marker['start_time_offset']

                # logger.debug("Tautulli ActivityProcessor :: Attempting to write to sessionKey %s session_history_metadata table..."
                #              % session['session_key'])
                keys = {'id': last_id}
                values = {'rating_key': session['rating_key'],
                          'parent_rating_key': session['parent_rating_key'],
                          'grandparent_rating_key': session['grandparent_rating_key'],
                          'title': session['title'],
                          'parent_title': session['parent_title'],
                          'grandparent_title': session['grandparent_title'],
                          'original_title': session['original_title'],
                          'full_title': session['full_title'],
                          'media_index': metadata['media_index'],
                          'parent_media_index': metadata['parent_media_index'],
                          'thumb': metadata['thumb'],
                          'parent_thumb': metadata['parent_thumb'],
                          'grandparent_thumb': metadata['grandparent_thumb'],
                          'art': metadata['art'],
                          'media_type': session['media_type'],
                          'year': metadata['year'],
                          'originally_available_at': metadata['originally_available_at'],
                          'added_at': metadata['added_at'],
                          'updated_at': metadata['updated_at'],
                          'last_viewed_at': metadata['last_viewed_at'],
                          'content_rating': metadata['content_rating'],
                          'summary': metadata['summary'],
                          'tagline': metadata['tagline'],
                          'rating': metadata['rating'],
                          'duration': metadata['duration'],
                          'guid': metadata['guid'],
                          'directors': directors,
                          'writers': writers,
                          'actors': actors,
                          'genres': genres,
                          'studio': metadata['studio'],
                          'labels': labels,
                          'live': session['live'],
                          'channel_call_sign': media_info.get('channel_call_sign', session.get('channel_call_sign', '')),
                          'channel_id': media_info.get('channel_id', session.get('channel_id', '')),
                          'channel_identifier': media_info.get('channel_identifier', session.get('channel_identifier', '')),
                          'channel_title': media_info.get('channel_title', session.get('channel_title', '')),
                          'channel_thumb': media_info.get('channel_thumb', session.get('channel_thumb', '')),
                          'channel_vcn': media_info.get('channel_vcn', session.get('channel_vcn', '')),
                          'marker_credits_first': marker_credits_first,
                          'marker_credits_final': marker_credits_final
                          }

                for column in SessionHistoryMetadata.__table__.columns:
                    if column.name in values and isinstance(column.type, Integer):
                        values[column.name] = _optional_int(values[column.name])

                # logger.debug("Tautulli ActivityProcessor :: Writing sessionKey %s session_history_metadata transaction..."
                #              % session['session_key'])
                with session_scope() as db_session:
                    stmt = (
                        update(SessionHistoryMetadata)
                        .where(SessionHistoryMetadata.id == last_id)
                        .values(**values)
                    )
                    result = db_session.execute(stmt)
                    if not result.rowcount or result.rowcount == 0:
                        insert_values = {**values, **keys}
                        db_session.execute(insert(SessionHistoryMetadata).values(**insert_values))

            # Return the session row id when the session is successfully written to the database
            return session['id']

    def group_history(self, last_id, session, metadata=None):
        new_session = prev_session = None
        prev_watched = None

        if session['live']:
            # Check if we should group the session, select the last guid from the user within the last day
            min_started = helpers.timestamp() - 24 * 60 * 60
            with session_scope() as db_session:
                stmt = (
                    select(
                        SessionHistory.id,
                        SessionHistoryMetadata.guid,
                        SessionHistory.reference_id,
                    )
                    .join(SessionHistoryMetadata, SessionHistory.id == SessionHistoryMetadata.id)
                    .where(
                        SessionHistory.id <= last_id,
                        SessionHistory.user_id == session['user_id'],
                        SessionHistory.started >= min_started,
                    )
                    .order_by(SessionHistory.id.desc())
                    .limit(1)
                )
                result = queries.fetch_mappings(db_session, stmt)

            if len(result) > 0:
                new_session = {'id': last_id,
                               'guid': metadata['guid'] if metadata else session['guid'],
                               'reference_id': last_id}

                prev_session = {'id': result[0]['id'],
                                'guid': result[0]['guid'],
                                'reference_id': result[0]['reference_id']}
                
                prev_watched = False

        else:
            # Check if we should group the session, select the last two rows from the user
            user_id = session.get('user_id')
            if str(user_id).isdigit():
                user_id = helpers.cast_to_int(user_id)
            else:
                user_id = None

            rating_key = session.get('rating_key')
            if str(rating_key).isdigit():
                rating_key = helpers.cast_to_int(rating_key)
            else:
                rating_key = None

            if user_id is None or rating_key is None:
                result = []
            else:
                with session_scope() as db_session:
                    stmt = (
                        select(
                            SessionHistory.id,
                            SessionHistory.rating_key,
                            SessionHistory.view_offset,
                            SessionHistory.reference_id,
                        )
                        .where(
                            SessionHistory.id <= last_id,
                            SessionHistory.user_id == user_id,
                            SessionHistory.rating_key == rating_key,
                        )
                        .order_by(SessionHistory.id.desc())
                        .limit(2)
                    )
                    result = queries.fetch_mappings(db_session, stmt)

            if len(result) > 1:
                new_session = {'id': result[0]['id'],
                               'rating_key': result[0]['rating_key'],
                               'view_offset': helpers.cast_to_int(result[0]['view_offset']),
                               'reference_id': result[0]['reference_id']}

                prev_session = {'id': result[1]['id'],
                                'rating_key': result[1]['rating_key'],
                                'view_offset': helpers.cast_to_int(result[1]['view_offset']),
                                'reference_id': result[1]['reference_id']}

                if metadata:
                    marker_first, marker_final = helpers.get_first_final_marker(metadata['markers'])
                else:
                    marker_first = session['marker_credits_first']
                    marker_final = session['marker_credits_final']

                prev_watched = helpers.check_watched(
                    session['media_type'], prev_session['view_offset'], session['duration'],
                    marker_first, marker_final
                )

        # If previous session view offset less than watched threshold,
        # and new session view offset is greater,
        # then set the reference_id to the previous row,
        # else set the reference_id to the new id
        if prev_watched is False and (
            not session['live'] and prev_session['view_offset'] <= new_session['view_offset'] or 
            session['live'] and prev_session['guid'] == new_session['guid']
        ):
            if metadata:
                logger.debug("Tautulli ActivityProcessor :: Grouping history for sessionKey %s", session['session_key'])
            reference_id = prev_session['reference_id']
            target_id = new_session['id']

        else:
            if metadata:
                logger.debug("Tautulli ActivityProcessor :: Not grouping history for sessionKey %s", session['session_key'])
            reference_id = last_id
            target_id = last_id

        with session_scope() as db_session:
            stmt = (
                update(SessionHistory)
                .where(SessionHistory.id == target_id)
                .values(reference_id=reference_id)
            )
            db_session.execute(stmt)

    def get_sessions(self, user_id=None, ip_address=None):
        stmt = select(SessionModel.__table__)

        if str(user_id).isdigit():
            user_id = helpers.cast_to_int(user_id)
            stmt = stmt.where(SessionModel.user_id == user_id)
            if ip_address:
                stmt = stmt.distinct(SessionModel.ip_address)

        with session_scope() as db_session:
            return queries.fetch_mappings(db_session, stmt)

    def get_session_by_key(self, session_key=None):
        if str(session_key).isdigit():
            session_key = helpers.cast_to_int(session_key)
            with session_scope() as db_session:
                stmt = select(SessionModel.__table__).where(SessionModel.session_key == session_key)
                session_data = queries.fetch_mapping(db_session, stmt, default={})
            if session_data:
                return session_data

        return None

    def get_session_by_id(self, session_id=None):
        if session_id:
            with session_scope() as db_session:
                stmt = select(SessionModel.__table__).where(SessionModel.session_id == session_id)
                session_data = queries.fetch_mapping(db_session, stmt, default={})
            if session_data:
                return session_data

        return None

    def set_session_state(self, session_key=None, state=None, **kwargs):
        if str(session_key).isdigit():
            session_key = helpers.cast_to_int(session_key)
            values = {}

            if state:
                values['state'] = state

            for k, v in kwargs.items():
                values[k] = v

            with session_scope() as db_session:
                stmt = (
                    update(SessionModel)
                    .where(SessionModel.session_key == session_key)
                    .values(**values)
                )
                result = db_session.execute(stmt)
                if result.rowcount and result.rowcount > 0:
                    return 'update'

                insert_values = {'session_key': session_key}
                insert_values.update(values)
                try:
                    db_session.execute(insert(SessionModel).values(**insert_values))
                    return 'insert'
                except IntegrityError:
                    stmt = (
                        update(SessionModel)
                        .where(SessionModel.session_key == session_key)
                        .values(**values)
                    )
                    db_session.execute(stmt)
                    return 'update'

        return None

    def delete_session(self, session_key=None, row_id=None):
        if str(session_key).isdigit():
            session_key = helpers.cast_to_int(session_key)
            with session_scope() as db_session:
                stmt = delete(SessionModel).where(SessionModel.session_key == session_key)
                db_session.execute(stmt)
        elif str(row_id).isdigit():
            row_id = helpers.cast_to_int(row_id)
            with session_scope() as db_session:
                stmt = delete(SessionModel).where(SessionModel.id == row_id)
                db_session.execute(stmt)

    def set_session_last_paused(self, session_key=None, timestamp=None):
        if str(session_key).isdigit():
            session_key = helpers.cast_to_int(session_key)
            with session_scope() as db_session:
                stmt = (
                    select(SessionModel.last_paused, SessionModel.paused_counter)
                    .where(SessionModel.session_key == session_key)
                )
                result = queries.fetch_mappings(db_session, stmt)

            paused_counter = None
            for session in result:
                if session['last_paused']:
                    paused_offset = helpers.timestamp() - int(session['last_paused'])
                    if session['paused_counter']:
                        paused_counter = int(session['paused_counter']) + int(paused_offset)
                    else:
                        paused_counter = int(paused_offset)

            values = {'last_paused': timestamp}

            if paused_counter:
                values['paused_counter'] = paused_counter

            with session_scope() as db_session:
                stmt = (
                    update(SessionModel)
                    .where(SessionModel.session_key == session_key)
                    .values(**values)
                )
                result = db_session.execute(stmt)
                if result.rowcount and result.rowcount > 0:
                    return

                insert_values = {'session_key': session_key}
                insert_values.update(values)
                try:
                    db_session.execute(insert(SessionModel).values(**insert_values))
                except IntegrityError:
                    stmt = (
                        update(SessionModel)
                        .where(SessionModel.session_key == session_key)
                        .values(**values)
                    )
                    db_session.execute(stmt)

    def increment_session_buffer_count(self, session_key=None):
        if str(session_key).isdigit():
            session_key = helpers.cast_to_int(session_key)
            with session_scope() as db_session:
                stmt = (
                    update(SessionModel)
                    .where(SessionModel.session_key == session_key)
                    .values(buffer_count=SessionModel.buffer_count + 1)
                )
                db_session.execute(stmt)

    def get_session_buffer_count(self, session_key=None):
        if str(session_key).isdigit():
            session_key = helpers.cast_to_int(session_key)
            with session_scope() as db_session:
                stmt = (
                    select(SessionModel.buffer_count)
                    .where(SessionModel.session_key == session_key)
                )
                buffer_count = queries.fetch_scalar(db_session, stmt)
            if buffer_count is not None:
                return buffer_count

            return 0

    def set_session_buffer_trigger_time(self, session_key=None):
        if str(session_key).isdigit():
            session_key = helpers.cast_to_int(session_key)
            with session_scope() as db_session:
                stmt = (
                    update(SessionModel)
                    .where(SessionModel.session_key == session_key)
                    .values(buffer_last_triggered=time_queries.epoch(func.now()))
                )
                db_session.execute(stmt)

    def get_session_buffer_trigger_time(self, session_key=None):
        if str(session_key).isdigit():
            session_key = helpers.cast_to_int(session_key)
            with session_scope() as db_session:
                stmt = (
                    select(SessionModel.buffer_last_triggered)
                    .where(SessionModel.session_key == session_key)
                )
                last_time = queries.fetch_scalar(db_session, stmt)
            if last_time is not None:
                return last_time

            return None

    def set_temp_stopped(self):
        stopped_time = helpers.timestamp()
        with session_scope() as db_session:
            stmt = update(SessionModel).values(stopped=stopped_time)
            db_session.execute(stmt)

    def increment_write_attempts(self, session_key=None):
        if str(session_key).isdigit():
            session_key = helpers.cast_to_int(session_key)
            session = self.get_session_by_key(session_key=session_key)
            if not session:
                return
            with session_scope() as db_session:
                stmt = (
                    update(SessionModel)
                    .where(SessionModel.session_key == session_key)
                    .values(write_attempts=session['write_attempts'] + 1)
                )
                db_session.execute(stmt)

    def set_marker(self, session_key=None, marker_idx=None, marker_type=None):
        if not str(session_key).isdigit():
            return
        session_key = helpers.cast_to_int(session_key)
        marker_args = [
            int(marker_type == 'intro'),
            int(marker_type == 'commercial'),
            int(marker_type == 'credits')
        ]
        with session_scope() as db_session:
            stmt = (
                update(SessionModel)
                .where(SessionModel.session_key == session_key)
                .values(
                    intro=marker_args[0],
                    commercial=marker_args[1],
                    credits=marker_args[2],
                    marker=marker_idx,
                )
            )
            db_session.execute(stmt)

    def set_watched(self, session_key=None):
        if not str(session_key).isdigit():
            return
        session_key = helpers.cast_to_int(session_key)
        with session_scope() as db_session:
            stmt = (
                update(SessionModel)
                .where(SessionModel.session_key == session_key)
                .values(watched=1)
            )
            db_session.execute(stmt)

    def write_continued_session(self, user_id=None, machine_id=None, media_type=None, stopped=None):
        values = {'stopped': stopped}
        with session_scope() as db_session:
            stmt = (
                update(SessionContinued)
                .where(
                    SessionContinued.user_id == user_id,
                    SessionContinued.machine_id == machine_id,
                    SessionContinued.media_type == media_type,
                )
                .values(**values)
            )
            result = db_session.execute(stmt)
            if result.rowcount and result.rowcount > 0:
                return

            insert_values = {
                'user_id': user_id,
                'machine_id': machine_id,
                'media_type': media_type,
                'stopped': stopped,
            }
            db_session.execute(insert(SessionContinued).values(**insert_values))

    def is_initial_stream(self, user_id=None, machine_id=None, media_type=None, started=None):
        with session_scope() as db_session:
            stmt = (
                select(SessionContinued.stopped)
                .where(
                    SessionContinued.user_id == user_id,
                    SessionContinued.machine_id == machine_id,
                    SessionContinued.media_type == media_type,
                )
                .order_by(SessionContinued.stopped.desc())
            )
            last_stopped = queries.fetch_scalar(db_session, stmt, default=0) or 0
        return int(started - last_stopped >= plexpy.CONFIG.NOTIFY_CONTINUED_SESSION_THRESHOLD)

    def regroup_history(self):
        logger.info("Tautulli ActivityProcessor :: Creating database backup...")
        if not maintenance.make_backup():
            return False

        logger.info("Tautulli ActivityProcessor :: Regrouping session history...")

        with session_scope() as db_session:
            stmt = (
                select(
                    SessionHistory.id,
                    SessionHistory.user_id,
                    SessionHistory.rating_key,
                    SessionHistory.view_offset,
                    SessionHistory.media_type,
                    SessionHistoryMetadata.duration,
                    SessionHistoryMetadata.marker_credits_first,
                    SessionHistoryMetadata.marker_credits_final,
                    SessionHistoryMetadata.live,
                    SessionHistoryMetadata.guid,
                )
                .join(SessionHistoryMetadata, SessionHistory.id == SessionHistoryMetadata.id)
            )
            results = queries.fetch_mappings(db_session, stmt)
        count = len(results)
        progress = 0

        for i, session in enumerate(results, start=1):
            if int(i / count * 10) > progress:
                progress = int(i / count * 10)
                logger.info("Tautulli ActivityProcessor :: Regrouping session history: %d%%", progress * 10)

            try:
                self.group_history(session['id'], session)
            except Exception as e:
                logger.error("Tautulli ActivityProcessor :: Error regrouping session history: %s", e)
                return False

        logger.info("Tautulli ActivityProcessor :: Regrouping session history complete.")
        return True


def regroup_history():
    ActivityProcessor().regroup_history()
