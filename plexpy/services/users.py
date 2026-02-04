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

from urllib.parse import parse_qsl

import arrow
import httpagentparser
from sqlalchemy import case, delete, distinct, func, insert, lateral, literal, or_, select, text, true, update
from sqlalchemy.orm import aliased

import plexpy
from plexpy.app import common
from plexpy.db import datatables
from plexpy.db import cleanup
from plexpy.db import queries
from plexpy.db.engine import get_engine
from plexpy.db.models import SessionHistory, SessionHistoryMediaInfo, SessionHistoryMetadata, User, UserLogin
from plexpy.db.session import session_scope
from plexpy.services import libraries
from plexpy.web import session
from plexpy.integrations import plextv
from plexpy.util import helpers
from plexpy.util import logger


def refresh_users():
    logger.info("Tautulli Users :: Requesting users list refresh...")
    result = plextv.PlexTV().get_full_users_list()

    server_id = plexpy.CONFIG.PMS_IDENTIFIER
    if not server_id:
        logger.error("Tautulli Users :: No PMS identifier, cannot refresh users. Verify server in settings.")
        return

    if result:
        # Keep track of user_id to update is_active status
        user_ids = [0]  # Local user always considered active
        new_users = []
        with session_scope() as db_session:
            for item in result:
                if item.get('shared_libraries'):
                    item['shared_libraries'] = ';'.join(item['shared_libraries'])
                    # Only append user if libraries are shared
                    user_ids.append(helpers.cast_to_int(item['user_id']))
                elif item.get('server_token'):
                    libs = libraries.Libraries().get_sections()
                    item['shared_libraries'] = ';'.join([str(l['section_id']) for l in libs])
                    # Only append user if libraries are shared
                    user_ids.append(helpers.cast_to_int(item['user_id']))

                keys_dict = {"user_id": helpers.cast_to_int(item.pop('user_id'))}

                # Check if we've set a custom avatar if so don't overwrite it.
                if keys_dict['user_id']:
                    stmt = (
                        select(User.thumb, User.custom_avatar_url)
                        .where(User.user_id == keys_dict['user_id'])
                    )
                    avatar_urls = db_session.execute(stmt).mappings().first()
                    if avatar_urls:
                        if not avatar_urls['custom_avatar_url'] or \
                                avatar_urls['custom_avatar_url'] == avatar_urls['thumb']:
                            item['custom_avatar_url'] = item['thumb']
                    else:
                        item['custom_avatar_url'] = item['thumb']

                # Check if title is the same as the username
                if item['title'] == item['username']:
                    item['title'] = None

                # Check if username is blank (Managed Users)
                if not item['username']:
                    item['username'] = item['title']

                stmt = update(User).where(User.user_id == keys_dict['user_id']).values(**item)
                update_result = db_session.execute(stmt)
                if not update_result.rowcount or update_result.rowcount == 0:
                    insert_values = {**item, **keys_dict}
                    stmt = insert(User).values(**insert_values).returning(User.id)
                    inserted_id = db_session.execute(stmt).scalar_one_or_none()
                    if inserted_id is not None:
                        new_users.append(item['username'])

            stmt = update(User).where(User.user_id.notin_(user_ids)).values(is_active=0)
            db_session.execute(stmt)

        # Add new users to logger username filter
        logger.filter_usernames(new_users)

        logger.info("Tautulli Users :: Users list refreshed.")
        return True
    else:
        logger.warn("Tautulli Users :: Unable to refresh users list.")
        return False


class Users(object):

    def __init__(self):
        pass

    def get_datatables_list(self, kwargs=None, grouping=None):
        default_return = {'recordsFiltered': 0,
                          'recordsTotal': 0,
                          'draw': 0,
                          'data': []}

        kwargs = kwargs or {}
        json_data = helpers.process_json_kwargs(json_kwargs=kwargs.get('json_data'))
        if not json_data:
            return default_return

        if grouping is None:
            grouping = plexpy.CONFIG.GROUP_HISTORY_TABLES

        filters = [User.deleted_user == 0]
        session_user_id = session.get_session_user_id()
        if session_user_id:
            filters.append(User.user_id == helpers.cast_to_int(session_user_id))

        requested_user_id = kwargs.get('user_id')
        if requested_user_id is not None and str(requested_user_id).isdigit():
            filters.append(User.user_id == int(requested_user_id))

        group_key = func.coalesce(SessionHistory.reference_id, SessionHistory.id) if grouping else SessionHistory.id
        duration_expr = (
            func.sum(
                case(
                    (SessionHistory.stopped > 0, SessionHistory.stopped - SessionHistory.started),
                    else_=0,
                )
            )
            - func.sum(
                case(
                    (SessionHistory.paused_counter.is_(None), 0),
                    else_=SessionHistory.paused_counter,
                )
            )
        ).label('duration')

        sh_stats = (
            select(
                func.count(distinct(group_key)).label('plays'),
                duration_expr,
            )
            .where(SessionHistory.user_id == User.user_id)
            .lateral()
        )

        last_sh = (
            select(
                SessionHistory.id.label('id'),
                SessionHistory.rating_key.label('rating_key'),
                SessionHistory.started.label('started'),
                SessionHistory.ip_address.label('ip_address'),
                SessionHistory.platform.label('platform'),
                SessionHistory.player.label('player'),
            )
            .where(SessionHistory.user_id == User.user_id)
            .order_by(SessionHistory.started.desc(), SessionHistory.id.desc())
            .limit(1)
            .lateral()
        )

        friendly_name_expr = case(
            (
                or_(User.friendly_name.is_(None), func.trim(User.friendly_name) == ''),
                User.username,
            ),
            else_=User.friendly_name,
        ).label('friendly_name')

        stmt = (
            select(
                User.id.label('row_id'),
                User.user_id,
                User.username,
                friendly_name_expr,
                User.title,
                User.email,
                User.thumb.label('user_thumb'),
                User.custom_avatar_url.label('custom_thumb'),
                func.coalesce(sh_stats.c.plays, 0).label('plays'),
                func.coalesce(sh_stats.c.duration, 0).label('duration'),
                last_sh.c.started.label('last_seen'),
                last_sh.c.id.label('history_row_id'),
                SessionHistoryMetadata.full_title.label('last_played'),
                last_sh.c.ip_address,
                last_sh.c.platform,
                last_sh.c.player,
                last_sh.c.rating_key,
                SessionHistoryMetadata.media_type,
                SessionHistoryMetadata.thumb,
                SessionHistoryMetadata.parent_thumb,
                SessionHistoryMetadata.grandparent_thumb,
                SessionHistoryMetadata.parent_title,
                SessionHistoryMetadata.year,
                SessionHistoryMetadata.media_index,
                SessionHistoryMetadata.parent_media_index,
                SessionHistoryMetadata.live,
                SessionHistoryMetadata.added_at,
                SessionHistoryMetadata.originally_available_at,
                SessionHistoryMetadata.guid,
                SessionHistoryMediaInfo.transcode_decision,
                User.do_notify.label('do_notify'),
                User.keep_history.label('keep_history'),
                User.allow_guest.label('allow_guest'),
                User.is_active.label('is_active'),
            )
            .select_from(User)
            .outerjoin(sh_stats, true())
            .outerjoin(last_sh, true())
            .outerjoin(SessionHistoryMetadata, SessionHistoryMetadata.id == last_sh.c.id)
            .outerjoin(SessionHistoryMediaInfo, SessionHistoryMediaInfo.id == last_sh.c.id)
        )

        for condition in filters:
            stmt = stmt.where(condition)

        try:
            with session_scope() as db_session:
                users = queries.fetch_mappings(db_session, stmt)
                total_count = queries.fetch_scalar(
                    db_session,
                    select(func.count(User.id)),
                    default=0,
                )
        except Exception as e:
            logger.warn("Tautulli Users :: Unable to execute database query for get_list: %s." % e)
            return default_return

        rows = []
        for item in users:
            if item['media_type'] == 'episode' and item['parent_thumb']:
                thumb = item['parent_thumb']
            elif item['media_type'] == 'episode':
                thumb = item['grandparent_thumb']
            else:
                thumb = item['thumb']

            if item['custom_thumb'] and item['custom_thumb'] != item['user_thumb']:
                user_thumb = item['custom_thumb']
            elif item['user_thumb']:
                user_thumb = item['user_thumb']
            else:
                user_thumb = common.DEFAULT_USER_THUMB

            # Rename Mystery platform names
            platform = common.PLATFORM_NAME_OVERRIDES.get(item['platform'], item['platform'])

            row = {'row_id': item['row_id'],
                   'user_id': item['user_id'],
                   'username': item['username'],
                   'friendly_name': item['friendly_name'],
                   'title': item['title'],
                   'email': item['email'],
                   'user_thumb': user_thumb,
                   'plays': item['plays'],
                   'duration': item['duration'],
                   'last_seen': item['last_seen'],
                   'last_played': item['last_played'],
                   'history_row_id': item['history_row_id'],
                   'ip_address': item['ip_address'],
                   'platform': platform,
                   'player': item['player'],
                   'rating_key': item['rating_key'],
                   'media_type': item['media_type'],
                   'thumb': thumb,
                   'parent_title': item['parent_title'],
                   'year': item['year'],
                   'media_index': item['media_index'],
                   'parent_media_index': item['parent_media_index'],
                   'live': item['live'],
                   'originally_available_at': item['originally_available_at'],
                   'guid': item['guid'],
                   'transcode_decision': item['transcode_decision'],
                   'do_notify': item['do_notify'],
                   'keep_history': item['keep_history'],
                   'allow_guest': item['allow_guest'],
                   'is_active': item['is_active']
                   }

            rows.append(row)

        results = helpers.process_datatable_rows(rows, json_data, default_sort='friendly_name')

        data = {'recordsFiltered': results['filtered_count'],
                'recordsTotal': total_count,
                'data': session.friendly_name_to_username(results['results']),
                'draw': int(json_data.get('draw', 0))
                }

        return data

    def get_datatables_unique_ips(self, user_id=None, kwargs=None):
        default_return = {'recordsFiltered': 0,
                          'recordsTotal': 0,
                          'draw': 0,
                          'data': []}

        if not session.allow_session_user(user_id):
            return default_return

        data_tables = datatables.DataTables()

        custom_where = ['users.user_id', user_id]

        columns = ["MAX(session_history.id) AS history_row_id",
                   "MIN(session_history.started) AS first_seen",
                   "MAX(session_history.started) AS last_seen",
                   "session_history.ip_address",
                   "COUNT(session_history.id) AS play_count",
                   "MAX(session_history.platform) AS platform",
                   "MAX(session_history.player) AS player",
                   "MAX(session_history.rating_key) AS rating_key",
                   "MAX(session_history_metadata.full_title) AS last_played",
                   "MAX(session_history_metadata.thumb) AS thumb",
                   "MAX(session_history_metadata.parent_thumb) AS parent_thumb",
                   "MAX(session_history_metadata.grandparent_thumb) AS grandparent_thumb",
                   "MAX(session_history_metadata.media_type) AS media_type",
                   "MAX(session_history_metadata.parent_title) AS parent_title",
                   "MAX(session_history_metadata.year) AS year",
                   "MAX(session_history_metadata.media_index) AS media_index",
                   "MAX(session_history_metadata.parent_media_index) AS parent_media_index",
                   "MAX(session_history_metadata.live) AS live",
                   "MAX(session_history_metadata.added_at) AS added_at",
                   "MAX(session_history_metadata.originally_available_at) AS originally_available_at",
                   "MAX(session_history_metadata.guid) AS guid",
                   "MAX(session_history_media_info.transcode_decision) AS transcode_decision",
                   "MAX(session_history.user) AS user",
                   "MAX(session_history.user_id) as custom_user_id",
                   "MAX(CASE WHEN users.friendly_name IS NULL OR TRIM(users.friendly_name) = '' \
                    THEN users.username ELSE users.friendly_name END) AS friendly_name"
                   ]

        try:
            query = data_tables.ssp_query(table_name='session_history',
                                          columns=columns,
                                          custom_where=[custom_where],
                                          group_by=['ip_address'],
                                          join_types=['JOIN',
                                                      'JOIN',
                                                      'JOIN'],
                                          join_tables=['users',
                                                       'session_history_metadata',
                                                       'session_history_media_info'],
                                          join_evals=[['session_history.user_id', 'users.user_id'],
                                                      ['session_history.id', 'session_history_metadata.id'],
                                                      ['session_history.id', 'session_history_media_info.id']],
                                          kwargs=kwargs)
        except Exception as e:
            logger.warn("Tautulli Users :: Unable to execute database query for get_unique_ips: %s." % e)
            return default_return

        results = query['result']

        rows = []
        for item in results:
            if item["media_type"] == 'episode' and item["parent_thumb"]:
                thumb = item["parent_thumb"]
            elif item["media_type"] == 'episode':
                thumb = item["grandparent_thumb"]
            else:
                thumb = item["thumb"]

            # Rename Mystery platform names
            platform = common.PLATFORM_NAME_OVERRIDES.get(item["platform"], item["platform"])

            row = {'history_row_id': item['history_row_id'],
                   'last_seen': item['last_seen'],
                   'first_seen': item['first_seen'],
                   'ip_address': item['ip_address'],
                   'play_count': item['play_count'],
                   'platform': platform,
                   'player': item['player'],
                   'last_played': item['last_played'],
                   'rating_key': item['rating_key'],
                   'thumb': thumb,
                   'media_type': item['media_type'],
                   'parent_title': item['parent_title'],
                   'year': item['year'],
                   'media_index': item['media_index'],
                   'parent_media_index': item['parent_media_index'],
                   'live': item['live'],
                   'originally_available_at': item['originally_available_at'],
                   'guid': item['guid'],
                   'transcode_decision': item['transcode_decision'],
                   'friendly_name': item['friendly_name'],
                   'user_id': item['custom_user_id']
                   }

            rows.append(row)

        dict = {'recordsFiltered': query['filteredCount'],
                'recordsTotal': query['totalCount'],
                'data': session.friendly_name_to_username(rows),
                'draw': query['draw']
                }

        return dict

    def set_config(self, user_id=None, friendly_name='', custom_thumb='', do_notify=1, keep_history=1, allow_guest=1):
        if str(user_id).isdigit():
            try:
                with session_scope() as db_session:
                    stmt = select(User.username).where(User.user_id == user_id)
                    username = queries.fetch_scalar(db_session, stmt)

                    if username == friendly_name:
                        friendly_name = None

                    value_dict = {
                        'friendly_name': friendly_name,
                        'custom_avatar_url': custom_thumb,
                        'do_notify': do_notify,
                        'keep_history': keep_history,
                        'allow_guest': allow_guest,
                    }
                    update_stmt = (
                        update(User)
                        .where(User.user_id == user_id)
                        .values(**value_dict)
                    )
                    result = db_session.execute(update_stmt)
                    if not (result.rowcount and result.rowcount > 0):
                        insert_values = {'user_id': user_id}
                        insert_values.update(value_dict)
                        db_session.execute(insert(User).values(**insert_values))
            except Exception as e:
                logger.warn("Tautulli Users :: Unable to execute database query for set_config: %s." % e)

    def get_details(self, user_id=None, user=None, email=None, include_last_seen=False):
        default_return = {'row_id': 0,
                          'user_id': 0,
                          'username': 'Local',
                          'friendly_name': 'Local',
                          'user_thumb': common.DEFAULT_USER_THUMB,
                          'email': '',
                          'is_active': 1,
                          'is_admin': '',
                          'is_home_user': 0,
                          'is_allow_sync': 0,
                          'is_restricted': 0,
                          'do_notify': 0,
                          'keep_history': 1,
                          'allow_guest': 0,
                          'deleted_user': 0,
                          'shared_libraries': (),
                          'last_seen': None
                          }

        if user_id in (None, '') and not user and not email:
            return default_return

        user_details = self.get_user_details(user_id=user_id, user=user, email=email,
                                             include_last_seen=include_last_seen)

        if user_details:
            return user_details

        else:
            logger.warn("Tautulli Users :: Unable to retrieve user %s from database. Requesting user list refresh."
                        % user_id if user_id else user)
            # Let's first refresh the user list to make sure the user isn't newly added and not in the db yet
            refresh_users()

            user_details = self.get_user_details(user_id=user_id, user=user, email=email,
                                                 include_last_seen=include_last_seen)

            if user_details:
                return user_details

            else:
                logger.warn("Tautulli Users :: Unable to retrieve user %s from database. Returning 'Local' user."
                            % user_id if user_id else user)
                # If there is no user data we must return something
                # Use "Local" user to retain compatibility with legacy database values
                return default_return

    def get_user_details(self, user_id=None, user=None, email=None, include_last_seen=False):
        try:
            if include_last_seen:
                last_seen_column = (
                    select(func.max(SessionHistory.started))
                    .where(SessionHistory.user_id == User.user_id)
                    .scalar_subquery()
                    .label('last_seen')
                )
            else:
                last_seen_column = literal(None).label('last_seen')

            stmt = select(
                User.id.label('row_id'),
                User.user_id,
                User.username,
                User.friendly_name,
                User.thumb.label('user_thumb'),
                User.custom_avatar_url.label('custom_thumb'),
                User.email,
                User.is_active,
                User.is_admin,
                User.is_home_user,
                User.is_allow_sync,
                User.is_restricted,
                User.do_notify,
                User.keep_history,
                User.deleted_user,
                User.allow_guest,
                User.shared_libraries,
                last_seen_column,
            )

            if str(user_id).isdigit():
                stmt = stmt.where(User.user_id == helpers.cast_to_int(user_id))
            elif user:
                stmt = stmt.where(User.username.ilike(user))
            elif email:
                stmt = stmt.where(User.email.ilike(email))
            else:
                raise Exception("Missing user_id, username, or email")

            with session_scope() as db_session:
                result = queries.fetch_mappings(db_session, stmt)
        except Exception as e:
            logger.warn("Tautulli Users :: Unable to execute database query for get_user_details: %s." % e)
            result = []

        user_details = {}
        if result:
            for item in result:
                if session.get_session_user_id():
                    friendly_name = session.get_session_user()
                elif item['friendly_name']:
                    friendly_name = item['friendly_name']
                else:
                    friendly_name = item['username']

                if item['custom_thumb'] and item['custom_thumb'] != item['user_thumb']:
                    user_thumb = item['custom_thumb']
                elif item['user_thumb']:
                    user_thumb = item['user_thumb']
                else:
                    user_thumb = common.DEFAULT_USER_THUMB

                shared_libraries = tuple(item['shared_libraries'].split(';')) if item['shared_libraries'] else ()

                user_details = {'row_id': item['row_id'],
                                'user_id': item['user_id'],
                                'username': item['username'],
                                'friendly_name': friendly_name,
                                'user_thumb': user_thumb,
                                'email': item['email'],
                                'is_active': item['is_active'],
                                'is_admin': item['is_admin'],
                                'is_home_user': item['is_home_user'],
                                'is_allow_sync': item['is_allow_sync'],
                                'is_restricted': item['is_restricted'],
                                'do_notify': item['do_notify'],
                                'keep_history': item['keep_history'],
                                'deleted_user': item['deleted_user'],
                                'allow_guest': item['allow_guest'],
                                'shared_libraries': shared_libraries,
                                'last_seen': item['last_seen']
                                }
        return user_details

    def get_watch_time_stats(self, user_id=None, grouping=None, query_days=None):
        if not session.allow_session_user(user_id):
            return []

        if grouping is None:
            grouping = plexpy.CONFIG.GROUP_HISTORY_TABLES

        if query_days and query_days is not None:
            query_days = map(helpers.cast_to_int, str(query_days).split(','))
        else:
            query_days = [1, 7, 30, 0]

        timestamp = helpers.timestamp()

        user_watch_time_stats = []
        user_id_int = helpers.cast_to_int(user_id) if str(user_id).isdigit() else None

        group_key = SessionHistory.reference_id if grouping else SessionHistory.id
        total_time_expr = (
            func.sum(SessionHistory.stopped - SessionHistory.started)
            - func.sum(func.coalesce(SessionHistory.paused_counter, 0))
        ).label('total_time')
        total_plays_expr = func.count(distinct(group_key)).label('total_plays')

        for days in query_days:
            timestamp_query = timestamp - days * 24 * 60 * 60
            result = {}
            try:
                if user_id_int is not None:
                    stmt = select(total_time_expr, total_plays_expr).where(SessionHistory.user_id == user_id_int)
                    if days > 0:
                        stmt = stmt.where(SessionHistory.stopped >= timestamp_query)
                    with session_scope() as db_session:
                        result = queries.fetch_mapping(db_session, stmt, default={})
            except Exception as e:
                logger.warn("Tautulli Users :: Unable to execute database query for get_watch_time_stats: %s." % e)
                result = {}

            if result:
                total_time = result.get('total_time') or 0
                total_plays = result.get('total_plays') or 0

                row = {'query_days': days,
                       'total_time': total_time,
                       'total_plays': total_plays
                       }

                user_watch_time_stats.append(row)

        return user_watch_time_stats

    def get_player_stats(self, user_id=None, grouping=None):
        if not session.allow_session_user(user_id):
            return []

        if grouping is None:
            grouping = plexpy.CONFIG.GROUP_HISTORY_TABLES

        player_stats = []
        result_id = 0

        user_id_int = helpers.cast_to_int(user_id) if str(user_id).isdigit() else None
        group_key = SessionHistory.reference_id if grouping else SessionHistory.id
        total_time_expr = (
            func.sum(SessionHistory.stopped - SessionHistory.started)
            - func.sum(func.coalesce(SessionHistory.paused_counter, 0))
        )
        total_plays_expr = func.count(distinct(group_key))

        try:
            result = []
            if user_id_int is not None:
                stmt = (
                    select(
                        SessionHistory.player.label('player'),
                        total_plays_expr.label('total_plays'),
                        total_time_expr.label('total_time'),
                        func.max(SessionHistory.platform).label('platform'),
                    )
                    .where(SessionHistory.user_id == user_id_int)
                    .group_by(SessionHistory.player)
                    .order_by(total_plays_expr.desc(), total_time_expr.desc())
                )
                with session_scope() as db_session:
                    result = queries.fetch_mappings(db_session, stmt)
        except Exception as e:
            logger.warn("Tautulli Users :: Unable to execute database query for get_player_stats: %s." % e)
            result = []

        for item in result:
            # Rename Mystery platform names
            platform = common.PLATFORM_NAME_OVERRIDES.get(item['platform'], item['platform'])
            platform_name = next((v for k, v in common.PLATFORM_NAMES.items() if k in platform.lower()), 'default')

            row = {'player_name': item['player'],
                   'platform': platform,
                   'platform_name': platform_name,
                   'total_plays': item['total_plays'],
                   'total_time': item['total_time'],
                   'result_id': result_id
                   }
            player_stats.append(row)
            result_id += 1

        return player_stats

    def get_recently_watched(self, user_id=None, limit='10'):
        if not session.allow_session_user(user_id):
            return []

        recently_watched = []
        user_id_int = helpers.cast_to_int(user_id) if str(user_id).isdigit() else None

        if not limit.isdigit():
            limit = '10'

        try:
            result = []
            if user_id_int is not None:
                limit_value = helpers.cast_to_int(limit) or 10
                sh = aliased(SessionHistory)
                sh_inner = aliased(SessionHistory)
                outer_key = case((sh.media_type == 'track', sh.parent_rating_key), else_=sh.rating_key)
                inner_key = case((sh_inner.media_type == 'track', sh_inner.parent_rating_key), else_=sh_inner.rating_key)

                latest_session = (
                    select(sh_inner.id)
                    .where(
                        sh_inner.user_id == sh.user_id,
                        inner_key == outer_key,
                    )
                    .order_by(sh_inner.started.desc(), sh_inner.id.desc())
                    .limit(1)
                    .scalar_subquery()
                )

                stmt = (
                    select(
                        sh.id,
                        sh.media_type,
                        SessionHistoryMetadata.guid,
                        sh.rating_key,
                        sh.parent_rating_key,
                        sh.grandparent_rating_key,
                        SessionHistoryMetadata.title,
                        SessionHistoryMetadata.parent_title,
                        SessionHistoryMetadata.grandparent_title,
                        SessionHistoryMetadata.original_title,
                        SessionHistoryMetadata.thumb,
                        SessionHistoryMetadata.parent_thumb,
                        SessionHistoryMetadata.grandparent_thumb,
                        SessionHistoryMetadata.media_index,
                        SessionHistoryMetadata.parent_media_index,
                        SessionHistoryMetadata.year,
                        SessionHistoryMetadata.originally_available_at,
                        SessionHistoryMetadata.added_at,
                        SessionHistoryMetadata.live,
                        sh.started,
                        sh.user,
                    )
                    .join(SessionHistoryMetadata, SessionHistoryMetadata.id == sh.id)
                    .where(
                        sh.user_id == user_id_int,
                        sh.id == latest_session,
                    )
                    .order_by(sh.started.desc())
                    .limit(limit_value)
                )
                with session_scope() as db_session:
                    result = queries.fetch_mappings(db_session, stmt)
        except Exception as e:
            logger.warn("Tautulli Users :: Unable to execute database query for get_recently_watched: %s." % e)
            result = []

        for row in result:
            if row['media_type'] == 'episode' and row['parent_thumb']:
                thumb = row['parent_thumb']
            elif row['media_type'] == 'episode':
                thumb = row['grandparent_thumb']
            else:
                thumb = row['thumb']

            recent_output = {'row_id': row['id'],
                             'media_type': row['media_type'],
                             'rating_key': row['rating_key'],
                             'parent_rating_key': row['parent_rating_key'],
                             'grandparent_rating_key': row['grandparent_rating_key'],
                             'title': row['title'],
                             'parent_title': row['parent_title'],
                             'grandparent_title': row['grandparent_title'],
                             'original_title': row['original_title'],
                             'thumb': thumb,
                             'media_index': row['media_index'],
                             'parent_media_index': row['parent_media_index'],
                             'year': row['year'],
                             'originally_available_at': row['originally_available_at'],
                             'live': row['live'],
                             'guid': row['guid'],
                             'time': row['started'],
                             'user': row['user']
                             }
            recently_watched.append(recent_output)

        return recently_watched

    def get_users(self, include_deleted=False):
        try:
            with session_scope() as db_session:
                stmt = select(
                    User.id.label('row_id'),
                    User.user_id,
                    User.username,
                    User.friendly_name,
                    User.thumb,
                    User.custom_avatar_url,
                    User.email,
                    User.is_active,
                    User.is_admin,
                    User.is_home_user,
                    User.is_allow_sync,
                    User.is_restricted,
                    User.do_notify,
                    User.keep_history,
                    User.allow_guest,
                    User.shared_libraries,
                    User.filter_all,
                    User.filter_movies,
                    User.filter_tv,
                    User.filter_music,
                    User.filter_photos,
                )
                if not include_deleted:
                    stmt = stmt.where(User.deleted_user == 0)
                result = queries.fetch_mappings(db_session, stmt)
        except Exception as e:
            logger.warn("Tautulli Users :: Unable to execute database query for get_users: %s." % e)
            return []

        users = []
        for item in result:
            shared_libraries = tuple(item['shared_libraries'].split(';')) if item['shared_libraries'] else ()

            user = {'row_id': item['row_id'],
                    'user_id': item['user_id'],
                    'username': item['username'],
                    'friendly_name': item['friendly_name'] or item['username'],
                    'thumb': item['custom_avatar_url'] or item['thumb'],
                    'email': item['email'],
                    'is_active': item['is_active'],
                    'is_admin': item['is_admin'],
                    'is_home_user': item['is_home_user'],
                    'is_allow_sync': item['is_allow_sync'],
                    'is_restricted': item['is_restricted'],
                    'do_notify': item['do_notify'],
                    'keep_history': item['keep_history'],
                    'allow_guest': item['allow_guest'],
                    'shared_libraries': shared_libraries,
                    'filter_all': item['filter_all'],
                    'filter_movies': item['filter_movies'],
                    'filter_tv': item['filter_tv'],
                    'filter_music': item['filter_music'],
                    'filter_photos': item['filter_photos'],
                    }
            users.append(user)

        return users

    def delete(self, user_id=None, row_ids=None, purge_only=False):
        if row_ids and row_ids is not None:
            row_ids = list(map(helpers.cast_to_int, row_ids.split(',')))

            # Get the user_ids corresponding to the row_ids
            with session_scope() as db_session:
                stmt = select(User.user_id).where(User.id.in_(row_ids))
                result = queries.fetch_mappings(db_session, stmt)

            success = []
            for user in result:
                success.append(self.delete(user_id=user['user_id'],
                                           purge_only=purge_only))
            return all(success)

        elif str(user_id).isdigit():
            delete_success = cleanup.delete_user_history(user_id=user_id)

            if purge_only:
                return delete_success
            else:
                logger.info("Tautulli Users :: Deleting user with user_id %s from database."
                            % user_id)
                try:
                    with session_scope() as db_session:
                        stmt = (
                            update(User)
                            .where(User.user_id == user_id)
                            .values(deleted_user=1, keep_history=0, do_notify=0)
                        )
                        db_session.execute(stmt)
                    return delete_success
                except Exception as e:
                    logger.warn("Tautulli Users :: Unable to execute database query for delete: %s." % e)

        else:
            return False

    def undelete(self, user_id=None, username=None):
        try:
            if user_id and str(user_id).isdigit():
                with session_scope() as db_session:
                    stmt = select(User.id).where(User.user_id == user_id)
                    exists = queries.fetch_scalar(db_session, stmt)
                    if exists is not None:
                        logger.info("Tautulli Users :: Re-adding user with id %s to database." % user_id)
                        update_stmt = (
                            update(User)
                            .where(User.user_id == user_id)
                            .values(deleted_user=0, keep_history=1, do_notify=1)
                        )
                        db_session.execute(update_stmt)
                        return True
                    return False

            elif username:
                with session_scope() as db_session:
                    stmt = select(User.id).where(User.username == username)
                    exists = queries.fetch_scalar(db_session, stmt)
                    if exists is not None:
                        logger.info("Tautulli Users :: Re-adding user with username %s to database." % username)
                        update_stmt = (
                            update(User)
                            .where(User.username == username)
                            .values(deleted_user=0, keep_history=1, do_notify=1)
                        )
                        db_session.execute(update_stmt)
                        return True
                    return False

        except Exception as e:
            logger.warn("Tautulli Users :: Unable to execute database query for undelete: %s." % e)

    # Keep method for legacy imports
    def get_user_id(self, user=None):
        if user:
            try:
                with session_scope() as db_session:
                    stmt = select(User.user_id).where(User.username == user)
                    return queries.fetch_scalar(db_session, stmt)
            except Exception:
                return None

        return None

    def get_user_names(self, kwargs=None):
        try:
            with session_scope() as db_session:
                friendly_name_expr = case(
                    (
                        (User.friendly_name.is_(None)) | (func.trim(User.friendly_name) == ''),
                        User.username,
                    ),
                    else_=User.friendly_name,
                ).label('friendly_name')
                stmt = select(User.user_id, friendly_name_expr).where(User.deleted_user == 0)
                session_user_id = session.get_session_user_id()
                if session_user_id:
                    stmt = stmt.where(User.user_id == session_user_id)
                result = queries.fetch_mappings(db_session, stmt)
        except Exception as e:
            logger.warn("Tautulli Users :: Unable to execute database query for get_user_names: %s." % e)
            return None

        return session.friendly_name_to_username(result)

    def get_tokens(self, user_id=None):
        tokens = {
            'allow_guest': 0,
            'user_token': '',
            'server_token': ''
        }

        if user_id:
            try:
                with session_scope() as db_session:
                    stmt = (
                        select(User.allow_guest, User.user_token, User.server_token)
                        .where(User.user_id == user_id, User.deleted_user == 0)
                    )
                    result = queries.fetch_mapping(db_session, stmt, default={})
                if result:
                    tokens = {
                        'allow_guest': result.get('allow_guest'),
                        'user_token': result.get('user_token'),
                        'server_token': result.get('server_token'),
                    }
                return tokens
            except Exception:
                return tokens

        return tokens

    def get_filters(self, user_id=None):
        if not user_id:
            return {}

        try:
            with session_scope() as db_session:
                stmt = select(
                    User.filter_all,
                    User.filter_movies,
                    User.filter_tv,
                    User.filter_music,
                    User.filter_photos,
                ).where(User.user_id == user_id)
                result = queries.fetch_mapping(db_session, stmt, default={})
        except Exception as e:
            logger.warn("Tautulli Users :: Unable to execute database query for get_filters: %s." % e)
            result = {}

        filters_list = {}
        for k, v in result.items():
            filters = {}

            for f in v.split('|'):
                if 'contentRating=' in f or 'label=' in f:
                    filters.update(dict(parse_qsl(f)))

            filters['content_rating'] = tuple(f for f in filters.pop('contentRating', '').split(',') if f)
            filters['labels'] = tuple(f for f in filters.pop('label', '').split(',') if f)

            filters_list[k] = filters

        return filters_list

    def set_user_login(self, user_id=None, user=None, user_group=None, ip_address=None, host=None,
                       user_agent=None, success=0, expiry=None, jwt_token=None):

        if user_id is None or str(user_id).isdigit():
            if expiry is not None:
                expiry = helpers.datetime_to_iso(expiry)

            try:
                values = {
                    'timestamp': helpers.timestamp(),
                    'user_id': user_id,
                    'user': user,
                    'user_group': user_group,
                    'ip_address': ip_address,
                    'host': host,
                    'user_agent': user_agent,
                    'success': success,
                    'expiry': expiry,
                    'jwt_token': jwt_token,
                }
                with session_scope() as db_session:
                    db_session.execute(insert(UserLogin).values(**values))
            except Exception as e:
                logger.warn("Tautulli Users :: Unable to execute database query for set_login_log: %s." % e)

    def get_user_login(self, jwt_token):
        try:
            with session_scope() as db_session:
                stmt = select(UserLogin.__table__).where(UserLogin.jwt_token == jwt_token)
                return queries.fetch_mapping(db_session, stmt, default={})
        except Exception as e:
            logger.warn("Tautulli Users :: Unable to execute database query for get_user_login: %s." % e)
            return {}

    def clear_user_login_token(self, jwt_token=None, row_ids=None):
        if jwt_token:
            logger.debug("Tautulli Users :: Clearing user JWT token.")
            try:
                with session_scope() as db_session:
                    stmt = update(UserLogin).where(UserLogin.jwt_token == jwt_token).values(jwt_token=None)
                    db_session.execute(stmt)
            except Exception as e:
                logger.error("Tautulli Users :: Unable to clear user JWT token: %s.", e)
                return False

        elif row_ids and row_ids is not None:
            row_ids = list(map(helpers.cast_to_int, row_ids.split(',')))
            logger.debug("Tautulli Users :: Clearing JWT tokens for row_ids %s.", row_ids)
            try:
                if not row_ids:
                    return True
                with session_scope() as db_session:
                    stmt = update(UserLogin).where(UserLogin.id.in_(row_ids)).values(jwt_token=None)
                    db_session.execute(stmt)
            except Exception as e:
                logger.error("Tautulli Users :: Unable to clear JWT tokens: %s.", e)
                return False

        return True

    def get_datatables_user_login(self, user_id=None, jwt_token=None, kwargs=None):
        default_return = {'recordsFiltered': 0,
                          'recordsTotal': 0,
                          'draw': 0,
                          'data': []}

        if not session.allow_session_user(user_id):
            return default_return

        data_tables = datatables.DataTables()

        if session.get_session_user_id():
            custom_where = [['user_login.user_id', session.get_session_user_id()]]
        else:
            custom_where = [['user_login.user_id', user_id]] if user_id else []

        columns = ["user_login.id AS row_id",
                   "user_login.timestamp",
                   "user_login.user_id",
                   "user_login.user",
                   "user_login.user_group",
                   "user_login.ip_address",
                   "user_login.host",
                   "user_login.user_agent",
                   "user_login.success",
                   "user_login.expiry",
                   "user_login.jwt_token",
                   "(CASE WHEN users.friendly_name IS NULL OR TRIM(users.friendly_name) = '' \
                    THEN users.username ELSE users.friendly_name END) AS friendly_name"
                   ]

        try:
            query = data_tables.ssp_query(table_name='user_login',
                                          columns=columns,
                                          custom_where=custom_where,
                                          group_by=[],
                                          join_types=['LEFT OUTER JOIN'],
                                          join_tables=['users'],
                                          join_evals=[['user_login.user_id', 'users.user_id']],
                                          kwargs=kwargs)
        except Exception as e:
            logger.warn("Tautulli Users :: Unable to execute database query for get_datatables_user_login: %s." % e)
            return default_return

        results = query['result']

        rows = []
        for item in results:
            (os, browser) = httpagentparser.simple_detect(item['user_agent'])

            expiry = None
            current = False
            if item['jwt_token'] and item['expiry']:
                _expiry = helpers.iso_to_datetime(item['expiry'])
                if _expiry > arrow.now():
                    expiry = _expiry.strftime('%Y-%m-%d %H:%M:%S')
                current = (item['jwt_token'] == jwt_token)

            row = {'row_id': item['row_id'],
                   'timestamp': item['timestamp'],
                   'user_id': item['user_id'],
                   'user_group': item['user_group'],
                   'ip_address': item['ip_address'],
                   'host': item['host'],
                   'user_agent': item['user_agent'],
                   'os': os,
                   'browser': browser,
                   'success': item['success'],
                   'expiry': expiry,
                   'current': current,
                   'friendly_name': item['friendly_name'] or item['user']
                   }

            rows.append(row)

        dict = {'recordsFiltered': query['filteredCount'],
                'recordsTotal': query['totalCount'],
                'data': session.friendly_name_to_username(rows),
                'draw': query['draw']
                }

        return dict

    def delete_login_log(self):
        try:
            logger.info("Tautulli Users :: Clearing login logs from database.")
            with session_scope() as db_session:
                db_session.execute(delete(UserLogin))

            engine = get_engine()
            with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
                connection.execute(text('VACUUM'))
            return True
        except Exception as e:
            logger.warn("Tautulli Users :: Unable to execute database query for delete_login_log: %s." % e)
            return False
