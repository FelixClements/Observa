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

import json

from sqlalchemy import Float, and_, case, cast, delete, distinct, func, insert, lateral, literal, or_, select, true, update
from sqlalchemy.orm import aliased

import plexpy
from plexpy.app import common
from plexpy.db import datatables
from plexpy.db import queries
from plexpy.db.models import (
    CloudinaryLookup,
    ImageHashLookup,
    ImgurLookup,
    LibrarySection,
    MusicbrainzLookup,
    NewsletterLog,
    NotifyLog,
    RecentlyAdded,
    Session,
    SessionContinued,
    SessionHistory,
    SessionHistoryMediaInfo,
    SessionHistoryMetadata,
    TheMovieDbLookup,
    TvmazeLookup,
    User,
)
from plexpy.db.queries import raw_pg
from plexpy.db.queries import time as time_queries
from plexpy.db.session import session_scope
from plexpy.integrations import pmsconnect
from plexpy.services import users
from plexpy.web import session
from plexpy.util import helpers
from plexpy.util import logger

# Temporarily store update_metadata row ids in memory to prevent rating_key collisions
_UPDATE_METADATA_IDS = {
    'grandparent_rating_key_ids': set(),
    'parent_rating_key_ids': set(),
    'rating_key_ids': set()
}


class DataFactory(object):
    """
    Retrieve and process data from the monitor database
    """

    def __init__(self):
        pass

    def _group_key_expr(self, grouping):
        return func.coalesce(SessionHistory.reference_id, SessionHistory.id) if grouping else SessionHistory.id

    def _duration_expr(self):
        return case(
            (
                SessionHistory.stopped > 0,
                (SessionHistory.stopped - SessionHistory.started)
                - func.coalesce(SessionHistory.paused_counter, 0),
            ),
            else_=0,
        )

    def _timeframe_filters(self, time_range, before=None, after=None):
        filters = []
        started_date = time_queries.to_char(
            time_queries.to_timestamp(SessionHistory.started),
            'YYYY-MM-DD',
        )

        if before:
            filters.append(started_date <= before)
            if not after:
                timestamp = helpers.YMD_to_timestamp(before) - time_range * 24 * 60 * 60
                filters.append(SessionHistory.stopped >= timestamp)

        if after:
            filters.append(started_date >= after)
            if not before:
                timestamp = helpers.YMD_to_timestamp(after) + time_range * 24 * 60 * 60
                filters.append(SessionHistory.stopped <= timestamp)

        if not (before or after):
            timestamp = helpers.timestamp() - time_range * 24 * 60 * 60
            filters.append(SessionHistory.stopped >= timestamp)

        return filters

    def _bind_params(self, query, args):
        if not args:
            return query, {}

        params = {}
        for idx, value in enumerate(args, start=1):
            param_name = f"param_{idx}"
            query = query.replace('?', f":{param_name}", 1)
            params[param_name] = value

        return query, params

    def get_datatables_history(self, kwargs=None, custom_where=None, grouping=None, include_activity=None):
        data_tables = datatables.DataTables()

        if custom_where is None:
            custom_where = []

        reference_filter = any(
            clause.rstrip(' OR') == 'session_history.reference_id'
            for clause, _ in custom_where
        )

        custom_where_sql = []
        custom_where_union = []
        for clause, value in custom_where:
            if clause == 'media_type_live':
                custom_where_sql.append([
                    "(CASE WHEN session_history_metadata.live = 1 THEN 'live' "
                    "ELSE session_history.media_type END)",
                    value,
                ])
                custom_where_union.append([
                    "(CASE WHEN live = 1 THEN 'live' ELSE media_type END)",
                    value,
                ])
            else:
                custom_where_sql.append([clause, value])
                custom_where_union.append([clause.split('.')[-1], value])

        custom_where = custom_where_sql

        if grouping is None:
            grouping = plexpy.CONFIG.GROUP_HISTORY_TABLES

        if include_activity is None:
            include_activity = plexpy.CONFIG.HISTORY_TABLE_ACTIVITY

        if include_activity and reference_filter:
            include_activity = False

        if session.get_session_user_id():
            session_user_id = str(session.get_session_user_id())
            added = False

            for c_where in custom_where:
                if 'user_id' in c_where[0]:
                    if isinstance(c_where[1], list) and session_user_id not in c_where[1]:
                        c_where[1].append(session_user_id)
                    elif isinstance(c_where[1], str) and c_where[1] != session_user_id:
                        c_where[1] = [c_where[1], session_user_id]
                    added = True
                    break

            if not added:
                custom_where.append(['session_history.user_id', [session.get_session_user_id()]])

        group_by = ['session_history.reference_id'] if grouping else ['session_history.id']

        columns = [
            "session_history.reference_id",
            "MAX(session_history.id) AS row_id",
            "MAX(started) AS date",
            "MIN(started) AS started",
            "MAX(stopped) AS stopped",
            "SUM(CASE WHEN stopped > 0 THEN (stopped - started) ELSE 0 END) - \
             SUM(CASE WHEN paused_counter IS NULL THEN 0 ELSE paused_counter END) AS play_duration",
            "SUM(CASE WHEN paused_counter IS NULL THEN 0 ELSE paused_counter END) AS paused_counter",
            "MAX(session_history.view_offset) AS view_offset",
            "MAX(session_history.user_id) AS user_id",
            "MAX(session_history.user) AS user",
            "MAX((CASE WHEN users.friendly_name IS NULL OR TRIM(users.friendly_name) = '' \
             THEN users.username ELSE users.friendly_name END)) AS friendly_name",
            "MAX(users.thumb) AS user_thumb",
            "MAX(users.custom_avatar_url) AS custom_thumb",
            "MAX(session_history.platform) AS platform",
            "MAX(session_history.product) AS product",
            "MAX(session_history.player) AS player",
            "MAX(session_history.ip_address) AS ip_address",
            "MAX(session_history.machine_id) AS machine_id",
            "MAX(session_history.location) AS location",
            "MAX(session_history.secure) AS secure",
            "MAX(session_history.relayed) AS relayed",
            "MAX(session_history.media_type) AS media_type",
            "MAX((CASE WHEN session_history_metadata.live = 1 THEN 'live' ELSE session_history.media_type END)) \
             AS media_type_live",
            "MAX(session_history_metadata.rating_key) AS rating_key",
            "MAX(session_history_metadata.parent_rating_key) AS parent_rating_key",
            "MAX(session_history_metadata.grandparent_rating_key) AS grandparent_rating_key",
            "MAX(session_history_metadata.full_title) AS full_title",
            "MAX(session_history_metadata.title) AS title",
            "MAX(session_history_metadata.parent_title) AS parent_title",
            "MAX(session_history_metadata.grandparent_title) AS grandparent_title",
            "MAX(session_history_metadata.original_title) AS original_title",
            "MAX(session_history_metadata.year) AS year",
            "MAX(session_history_metadata.media_index) AS media_index",
            "MAX(session_history_metadata.parent_media_index) AS parent_media_index",
            "MAX(session_history_metadata.thumb) AS thumb",
            "MAX(session_history_metadata.parent_thumb) AS parent_thumb",
            "MAX(session_history_metadata.grandparent_thumb) AS grandparent_thumb",
            "MAX(session_history_metadata.live) AS live",
            "MAX(session_history_metadata.added_at) AS added_at",
            "MAX(session_history_metadata.originally_available_at) AS originally_available_at",
            "MAX(session_history_metadata.guid) AS guid",
            "MAX((CASE WHEN session_history.view_offset IS NULL THEN 0.1 ELSE session_history.view_offset * 1.0 END) / \
             (CASE WHEN session_history_metadata.duration IS NULL \
             THEN 1.0 ELSE session_history_metadata.duration * 1.0 END) * 100) AS percent_complete",
            "MAX(session_history_metadata.duration) AS duration",
            "MAX(session_history_metadata.marker_credits_first) AS marker_credits_first",
            "MAX(session_history_metadata.marker_credits_final) AS marker_credits_final",
            "MAX(session_history_media_info.transcode_decision) AS transcode_decision",
            "COUNT(*) AS group_count",
            "string_agg(session_history.id::text, ',') AS group_ids",
            "NULL AS state",
            "NULL AS session_key"
            ]

        if include_activity:
            table_name_union = 'sessions'
            # Very hacky way to match the custom where parameters for the unioned table
            # (re-built above for media_type_live compatibility)
            group_by_union = ['session_key']

            columns_union = [
                "NULL AS reference_id",
                "NULL AS row_id",
                "MAX(started) AS date",
                "MAX(started) AS started",
                "MAX(stopped) AS stopped",
                "SUM(CASE WHEN stopped > 0 THEN (stopped - started) ELSE (EXTRACT(EPOCH FROM NOW())::int - started) END) - \
                 SUM(CASE WHEN paused_counter IS NULL THEN 0 ELSE paused_counter END) AS play_duration",
                "SUM(CASE WHEN paused_counter IS NULL THEN 0 ELSE paused_counter END) AS paused_counter",
                "MAX(view_offset) AS view_offset",
                "MAX(user_id) AS user_id",
                "MAX(user) AS user",
                "MAX((CASE WHEN friendly_name IS NULL OR TRIM(friendly_name) = '' \
                 THEN user ELSE friendly_name END)) AS friendly_name",
                "NULL AS user_thumb",
                "NULL AS custom_thumb",
                "MAX(platform) AS platform",
                "MAX(product) AS product",
                "MAX(player) AS player",
                "MAX(ip_address) AS ip_address",
                "MAX(machine_id) AS machine_id",
                "MAX(location) AS location",
                "MAX(secure) AS secure",
                "MAX(relayed) AS relayed",
                "MAX(media_type) AS media_type",
                "MAX((CASE WHEN live = 1 THEN 'live' ELSE media_type END)) AS media_type_live",
                "MAX(rating_key) AS rating_key",
                "MAX(parent_rating_key) AS parent_rating_key",
                "MAX(grandparent_rating_key) AS grandparent_rating_key",
                "MAX(full_title) AS full_title",
                "MAX(title) AS title",
                "MAX(parent_title) AS parent_title",
                "MAX(grandparent_title) AS grandparent_title",
                "MAX(original_title) AS original_title",
                "MAX(year) AS year",
                "MAX(media_index) AS media_index",
                "MAX(parent_media_index) AS parent_media_index",
                "MAX(thumb) AS thumb",
                "MAX(parent_thumb) AS parent_thumb",
                "MAX(grandparent_thumb) AS grandparent_thumb",
                "MAX(live) AS live",
                "MAX(added_at) AS added_at",
                "MAX(originally_available_at) AS originally_available_at",
                "MAX(guid) AS guid",
                "MAX((CASE WHEN view_offset IS NULL THEN 0.1 ELSE view_offset * 1.0 END) / \
                 (CASE WHEN duration IS NULL \
                 THEN 1.0 ELSE duration * 1.0 END) * 100) AS percent_complete",
                "MAX(duration) AS duration",
                "NULL AS marker_credits_first",
                "NULL AS marker_credits_final",
                "MAX(transcode_decision) AS transcode_decision",
                "NULL AS group_count",
                "NULL AS group_ids",
                "MAX(state) AS state",
                "session_key"
                ]

        else:
            table_name_union = None
            custom_where_union = group_by_union = columns_union = []

        try:
            query = data_tables.ssp_query(table_name='session_history',
                                          table_name_union=table_name_union,
                                          columns=columns,
                                          columns_union=columns_union,
                                          custom_where=custom_where,
                                          custom_where_union=custom_where_union,
                                          group_by=group_by,
                                          group_by_union=group_by_union,
                                          join_types=['LEFT OUTER JOIN',
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
            logger.warn("Tautulli DataFactory :: Unable to execute database query for get_history: %s." % e)
            return {'recordsFiltered': 0,
                    'recordsTotal': 0,
                    'draw': 0,
                    'data': [],
                    'filter_duration': '0',
                    'total_duration': '0'}

        history = query['result']

        filter_duration = 0
        total_duration = self.get_total_duration(custom_where=custom_where)

        watched_percent = {'movie': plexpy.CONFIG.MOVIE_WATCHED_PERCENT,
                           'episode': plexpy.CONFIG.TV_WATCHED_PERCENT,
                           'track': plexpy.CONFIG.MUSIC_WATCHED_PERCENT,
                           'photo': 0,
                           'clip': plexpy.CONFIG.TV_WATCHED_PERCENT
                           }

        rows = []

        users_lookup = {}

        for item in history:
            if item['state']:
                # Get user thumb from database for current activity
                if not users_lookup:
                    # Cache user lookup
                    users_lookup = {u['user_id']: u['thumb'] for u in users.Users().get_users()}

                item['user_thumb'] = users_lookup.get(item['user_id'])

            filter_duration += helpers.cast_to_int(item['play_duration'])

            if item['media_type'] == 'episode' and item['parent_thumb']:
                thumb = item['parent_thumb']
            elif item['media_type'] == 'episode':
                thumb = item['grandparent_thumb']
            else:
                thumb = item['thumb']

            if item['live']:
                item['percent_complete'] = 100

            base_watched_value = watched_percent[item['media_type']] / 4.0

            if item['live'] or helpers.check_watched(
                item['media_type'], item['view_offset'], item['duration'],
                item['marker_credits_first'], item['marker_credits_final']
            ):
                watched_status = 1
            elif item['percent_complete'] >= base_watched_value * 3.0:
                watched_status = 0.75
            elif item['percent_complete'] >= base_watched_value * 2.0:
                watched_status = 0.50
            elif item['percent_complete'] >= base_watched_value:
                watched_status = 0.25
            else:
                watched_status = 0

            # Rename Mystery platform names
            platform = common.PLATFORM_NAME_OVERRIDES.get(item['platform'], item['platform'])

            if item['custom_thumb'] and item['custom_thumb'] != item['user_thumb']:
                user_thumb = item['custom_thumb']
            elif item['user_thumb']:
                user_thumb = item['user_thumb']
            else:
                user_thumb = common.DEFAULT_USER_THUMB

            row = {'reference_id': item['reference_id'],
                   'row_id': item['row_id'],
                   'id': item['row_id'],
                   'date': item['date'],
                   'started': item['started'],
                   'stopped': item['stopped'],
                   'duration': item['play_duration'],  # Keep for backwards compatibility
                   'play_duration': item['play_duration'],
                   'paused_counter': item['paused_counter'],
                   'user_id': item['user_id'],
                   'user': item['user'],
                   'friendly_name': item['friendly_name'],
                   'user_thumb': user_thumb,
                   'platform': platform,
                   'product': item['product'],
                   'player': item['player'],
                   'ip_address': item['ip_address'],
                   'live': item['live'],
                   'machine_id': item['machine_id'],
                   'location': item['location'],
                   'secure': item['secure'],
                   'relayed': item['relayed'],
                   'media_type': item['media_type'],
                   'rating_key': item['rating_key'],
                   'parent_rating_key': item['parent_rating_key'],
                   'grandparent_rating_key': item['grandparent_rating_key'],
                   'full_title': item['full_title'],
                   'title': item['title'],
                   'parent_title': item['parent_title'],
                   'grandparent_title': item['grandparent_title'],
                   'original_title': item['original_title'],
                   'year': item['year'],
                   'media_index': item['media_index'],
                   'parent_media_index': item['parent_media_index'],
                   'thumb': thumb,
                   'originally_available_at': item['originally_available_at'],
                   'guid': item['guid'],
                   'transcode_decision': item['transcode_decision'],
                   'percent_complete': int(round(item['percent_complete'])),
                   'watched_status': watched_status,
                   'group_count': item['group_count'],
                   'group_ids': item['group_ids'],
                   'state': item['state'],
                   'session_key': item['session_key']
                   }

            rows.append(row)

        dict = {'recordsFiltered': query['filteredCount'],
                'recordsTotal': query['totalCount'],
                'data': session.friendly_name_to_username(rows),
                'draw': query['draw'],
                'filter_duration': helpers.human_duration(filter_duration, units='s'),
                'total_duration': helpers.human_duration(total_duration, units='s')
                }

        return dict

    def get_home_stats(self, grouping=None, time_range=30, stats_type='plays',
                       stats_start=0, stats_count=10, stat_id='', stats_cards=None,
                       section_id=None, user_id=None, before=None, after=None):
        time_range = helpers.cast_to_int(time_range)

        stats_start = helpers.cast_to_int(stats_start)
        stats_count = helpers.cast_to_int(stats_count)
        if stat_id:
            stats_cards = [stat_id]
        if grouping is None:
            grouping = plexpy.CONFIG.GROUP_HISTORY_TABLES
        if stats_cards is None:
            stats_cards = plexpy.CONFIG.HOME_STATS_CARDS

        filters = self._timeframe_filters(time_range=time_range, before=before, after=after)
        if section_id:
            filters.append(SessionHistory.section_id == helpers.cast_to_int(section_id))
        if user_id:
            filters.append(SessionHistory.user_id == helpers.cast_to_int(user_id))

        group_key = self._group_key_expr(grouping)
        duration_expr = self._duration_expr()
        sort_type = 'total_duration' if stats_type == 'duration' else 'total_plays'

        home_stats = []

        def apply_filters(stmt):
            for cond in filters:
                stmt = stmt.where(cond)
            return stmt

        friendly_name_expr = case(
            (or_(User.friendly_name.is_(None), func.trim(User.friendly_name) == ''), User.username),
            else_=User.friendly_name,
        )

        with session_scope() as db_session:
            for stat in stats_cards:
                if stat == 'top_movies':
                    top_movies = []
                    try:
                        total_plays_expr = func.count(distinct(group_key)).label('total_plays')
                        total_duration_expr = func.sum(duration_expr).label('total_duration')
                        last_watch_expr = func.max(SessionHistory.started).label('last_watch')

                        agg = (
                            select(
                                SessionHistoryMetadata.full_title.label('full_title'),
                                SessionHistoryMetadata.year.label('year'),
                                total_plays_expr,
                                total_duration_expr,
                                last_watch_expr,
                            )
                            .select_from(SessionHistory)
                            .join(SessionHistoryMetadata, SessionHistoryMetadata.id == SessionHistory.id)
                            .where(SessionHistory.media_type == 'movie')
                        )
                        agg = apply_filters(agg)
                        agg = agg.group_by(SessionHistoryMetadata.full_title, SessionHistoryMetadata.year).subquery()

                        last_row_stmt = (
                            select(
                                SessionHistory.id.label('id'),
                                SessionHistory.rating_key.label('rating_key'),
                                SessionHistory.section_id.label('section_id'),
                                SessionHistory.media_type.label('media_type'),
                                SessionHistoryMetadata.thumb.label('thumb'),
                                SessionHistoryMetadata.art.label('art'),
                                SessionHistoryMetadata.content_rating.label('content_rating'),
                                SessionHistoryMetadata.labels.label('labels'),
                                SessionHistoryMetadata.live.label('live'),
                                SessionHistoryMetadata.guid.label('guid'),
                            )
                            .select_from(SessionHistory)
                            .join(SessionHistoryMetadata, SessionHistoryMetadata.id == SessionHistory.id)
                            .where(
                                SessionHistory.media_type == 'movie',
                                SessionHistoryMetadata.full_title == agg.c.full_title,
                                or_(
                                    SessionHistoryMetadata.year == agg.c.year,
                                    and_(SessionHistoryMetadata.year.is_(None), agg.c.year.is_(None)),
                                ),
                            )
                        )
                        last_row_stmt = apply_filters(last_row_stmt)
                        last_row = lateral(
                            last_row_stmt
                            .order_by(SessionHistory.started.desc(), SessionHistory.id.desc())
                            .limit(1)
                        ).alias('last_row')

                        sort_metric = agg.c.total_duration if sort_type == 'total_duration' else agg.c.total_plays
                        stmt = (
                            select(
                                last_row.c.id,
                                agg.c.full_title,
                                agg.c.year,
                                last_row.c.rating_key,
                                last_row.c.thumb,
                                last_row.c.section_id,
                                last_row.c.art,
                                last_row.c.media_type,
                                last_row.c.content_rating,
                                last_row.c.labels,
                                last_row.c.live,
                                last_row.c.guid,
                                agg.c.last_watch,
                                agg.c.total_plays,
                                agg.c.total_duration,
                            )
                            .select_from(agg)
                            .join(last_row, true())
                            .order_by(sort_metric.desc(), agg.c.last_watch.desc())
                        )
                        stmt = queries.apply_pagination(stmt, stats_start, stats_count)
                        result = queries.fetch_mappings(db_session, stmt)
                    except Exception as e:
                        logger.warn("Tautulli DataFactory :: Unable to execute database query for get_home_stats: top_movies: %s." % e)
                        return None

                    for item in result:
                        row = {'title': item['full_title'],
                               'year': item['year'],
                               'total_plays': item['total_plays'],
                               'total_duration': item['total_duration'],
                               'users_watched': '',
                               'rating_key': item['rating_key'],
                               'grandparent_rating_key': '',
                               'last_play': item['last_watch'],
                               'grandparent_thumb': '',
                               'thumb': item['thumb'],
                               'art': item['art'],
                               'section_id': item['section_id'],
                               'media_type': item['media_type'],
                               'content_rating': item['content_rating'],
                               'labels': item['labels'].split(';') if item['labels'] else (),
                               'user': '',
                               'friendly_name': '',
                               'platform': '',
                               'live': item['live'],
                               'guid': item['guid'],
                               'row_id': item['id']
                               }
                        top_movies.append(row)

                    home_stats.append({'stat_id': stat,
                                       'stat_type': sort_type,
                                       'stat_title': 'Most Watched Movies',
                                       'rows': session.mask_session_info(top_movies)})

                elif stat == 'popular_movies':
                    popular_movies = []
                    try:
                        total_plays_expr = func.count(distinct(group_key)).label('total_plays')
                        total_duration_expr = func.sum(duration_expr).label('total_duration')
                        last_watch_expr = func.max(SessionHistory.started).label('last_watch')
                        users_watched_expr = func.count(distinct(SessionHistory.user_id)).label('users_watched')

                        agg = (
                            select(
                                SessionHistoryMetadata.full_title.label('full_title'),
                                SessionHistoryMetadata.year.label('year'),
                                users_watched_expr,
                                total_plays_expr,
                                total_duration_expr,
                                last_watch_expr,
                            )
                            .select_from(SessionHistory)
                            .join(SessionHistoryMetadata, SessionHistoryMetadata.id == SessionHistory.id)
                            .where(SessionHistory.media_type == 'movie')
                        )
                        agg = apply_filters(agg)
                        agg = agg.group_by(SessionHistoryMetadata.full_title, SessionHistoryMetadata.year).subquery()

                        last_row_stmt = (
                            select(
                                SessionHistory.id.label('id'),
                                SessionHistory.rating_key.label('rating_key'),
                                SessionHistory.section_id.label('section_id'),
                                SessionHistory.media_type.label('media_type'),
                                SessionHistoryMetadata.thumb.label('thumb'),
                                SessionHistoryMetadata.art.label('art'),
                                SessionHistoryMetadata.content_rating.label('content_rating'),
                                SessionHistoryMetadata.labels.label('labels'),
                                SessionHistoryMetadata.live.label('live'),
                                SessionHistoryMetadata.guid.label('guid'),
                            )
                            .select_from(SessionHistory)
                            .join(SessionHistoryMetadata, SessionHistoryMetadata.id == SessionHistory.id)
                            .where(
                                SessionHistory.media_type == 'movie',
                                SessionHistoryMetadata.full_title == agg.c.full_title,
                                or_(
                                    SessionHistoryMetadata.year == agg.c.year,
                                    and_(SessionHistoryMetadata.year.is_(None), agg.c.year.is_(None)),
                                ),
                            )
                        )
                        last_row_stmt = apply_filters(last_row_stmt)
                        last_row = lateral(
                            last_row_stmt
                            .order_by(SessionHistory.started.desc(), SessionHistory.id.desc())
                            .limit(1)
                        ).alias('last_row')

                        sort_metric = agg.c.total_duration if sort_type == 'total_duration' else agg.c.total_plays
                        stmt = (
                            select(
                                last_row.c.id,
                                agg.c.full_title,
                                agg.c.year,
                                last_row.c.rating_key,
                                last_row.c.thumb,
                                last_row.c.section_id,
                                last_row.c.art,
                                last_row.c.media_type,
                                last_row.c.content_rating,
                                last_row.c.labels,
                                last_row.c.live,
                                last_row.c.guid,
                                agg.c.users_watched,
                                agg.c.last_watch,
                                agg.c.total_plays,
                                agg.c.total_duration,
                            )
                            .select_from(agg)
                            .join(last_row, true())
                            .order_by(agg.c.users_watched.desc(), sort_metric.desc(), agg.c.last_watch.desc())
                        )
                        stmt = queries.apply_pagination(stmt, stats_start, stats_count)
                        result = queries.fetch_mappings(db_session, stmt)
                    except Exception as e:
                        logger.warn("Tautulli DataFactory :: Unable to execute database query for get_home_stats: popular_movies: %s." % e)
                        return None

                    for item in result:
                        row = {'title': item['full_title'],
                               'year': item['year'],
                               'users_watched': item['users_watched'],
                               'rating_key': item['rating_key'],
                               'grandparent_rating_key': '',
                               'last_play': item['last_watch'],
                               'total_plays': item['total_plays'],
                               'grandparent_thumb': '',
                               'thumb': item['thumb'],
                               'art': item['art'],
                               'section_id': item['section_id'],
                               'media_type': item['media_type'],
                               'content_rating': item['content_rating'],
                               'labels': item['labels'].split(';') if item['labels'] else (),
                               'user': '',
                               'friendly_name': '',
                               'platform': '',
                               'live': item['live'],
                               'guid': item['guid'],
                               'row_id': item['id']
                               }
                        popular_movies.append(row)

                    home_stats.append({'stat_id': stat,
                                       'stat_title': 'Most Popular Movies',
                                       'rows': session.mask_session_info(popular_movies)})

                elif stat == 'top_tv':
                    top_tv = []
                    try:
                        total_plays_expr = func.count(distinct(group_key)).label('total_plays')
                        total_duration_expr = func.sum(duration_expr).label('total_duration')
                        last_watch_expr = func.max(SessionHistory.started).label('last_watch')

                        agg = (
                            select(
                                SessionHistoryMetadata.grandparent_title.label('grandparent_title'),
                                total_plays_expr,
                                total_duration_expr,
                                last_watch_expr,
                            )
                            .select_from(SessionHistory)
                            .join(SessionHistoryMetadata, SessionHistoryMetadata.id == SessionHistory.id)
                            .where(SessionHistory.media_type == 'episode')
                        )
                        agg = apply_filters(agg)
                        agg = agg.group_by(SessionHistoryMetadata.grandparent_title).subquery()

                        last_row_stmt = (
                            select(
                                SessionHistory.id.label('id'),
                                SessionHistoryMetadata.grandparent_rating_key.label('grandparent_rating_key'),
                                SessionHistoryMetadata.grandparent_thumb.label('grandparent_thumb'),
                                SessionHistory.section_id.label('section_id'),
                                SessionHistoryMetadata.year.label('year'),
                                SessionHistory.rating_key.label('rating_key'),
                                SessionHistoryMetadata.art.label('art'),
                                SessionHistory.media_type.label('media_type'),
                                SessionHistoryMetadata.content_rating.label('content_rating'),
                                SessionHistoryMetadata.labels.label('labels'),
                                SessionHistoryMetadata.live.label('live'),
                                SessionHistoryMetadata.guid.label('guid'),
                            )
                            .select_from(SessionHistory)
                            .join(SessionHistoryMetadata, SessionHistoryMetadata.id == SessionHistory.id)
                            .where(
                                SessionHistory.media_type == 'episode',
                                SessionHistoryMetadata.grandparent_title == agg.c.grandparent_title,
                            )
                        )
                        last_row_stmt = apply_filters(last_row_stmt)
                        last_row = lateral(
                            last_row_stmt
                            .order_by(SessionHistory.started.desc(), SessionHistory.id.desc())
                            .limit(1)
                        ).alias('last_row')

                        sort_metric = agg.c.total_duration if sort_type == 'total_duration' else agg.c.total_plays
                        stmt = (
                            select(
                                last_row.c.id,
                                agg.c.grandparent_title,
                                last_row.c.grandparent_rating_key,
                                last_row.c.grandparent_thumb,
                                last_row.c.section_id,
                                last_row.c.year,
                                last_row.c.rating_key,
                                last_row.c.art,
                                last_row.c.media_type,
                                last_row.c.content_rating,
                                last_row.c.labels,
                                last_row.c.live,
                                last_row.c.guid,
                                agg.c.last_watch,
                                agg.c.total_plays,
                                agg.c.total_duration,
                            )
                            .select_from(agg)
                            .join(last_row, true())
                            .order_by(sort_metric.desc(), agg.c.last_watch.desc())
                        )
                        stmt = queries.apply_pagination(stmt, stats_start, stats_count)
                        result = queries.fetch_mappings(db_session, stmt)
                    except Exception as e:
                        logger.warn("Tautulli DataFactory :: Unable to execute database query for get_home_stats: top_tv: %s." % e)
                        return None

                    for item in result:
                        row = {'title': item['grandparent_title'],
                               'year': item['year'],
                               'total_plays': item['total_plays'],
                               'total_duration': item['total_duration'],
                               'users_watched': '',
                               'rating_key': item['rating_key'] if item['live'] else item['grandparent_rating_key'],
                               'grandparent_rating_key': item['grandparent_rating_key'],
                               'last_play': item['last_watch'],
                               'grandparent_thumb': item['grandparent_thumb'],
                               'thumb': item['grandparent_thumb'],
                               'art': item['art'],
                               'section_id': item['section_id'],
                               'media_type': item['media_type'],
                               'content_rating': item['content_rating'],
                               'labels': item['labels'].split(';') if item['labels'] else (),
                               'user': '',
                               'friendly_name': '',
                               'platform': '',
                               'live': item['live'],
                               'guid': item['guid'],
                               'row_id': item['id']
                               }
                        top_tv.append(row)

                    home_stats.append({'stat_id': stat,
                                       'stat_type': sort_type,
                                       'stat_title': 'Most Watched TV Shows',
                                       'rows': session.mask_session_info(top_tv)})

                elif stat == 'popular_tv':
                    popular_tv = []
                    try:
                        total_plays_expr = func.count(distinct(group_key)).label('total_plays')
                        total_duration_expr = func.sum(duration_expr).label('total_duration')
                        last_watch_expr = func.max(SessionHistory.started).label('last_watch')
                        users_watched_expr = func.count(distinct(SessionHistory.user_id)).label('users_watched')

                        agg = (
                            select(
                                SessionHistoryMetadata.grandparent_title.label('grandparent_title'),
                                users_watched_expr,
                                total_plays_expr,
                                total_duration_expr,
                                last_watch_expr,
                            )
                            .select_from(SessionHistory)
                            .join(SessionHistoryMetadata, SessionHistoryMetadata.id == SessionHistory.id)
                            .where(SessionHistory.media_type == 'episode')
                        )
                        agg = apply_filters(agg)
                        agg = agg.group_by(SessionHistoryMetadata.grandparent_title).subquery()

                        last_row_stmt = (
                            select(
                                SessionHistory.id.label('id'),
                                SessionHistoryMetadata.grandparent_rating_key.label('grandparent_rating_key'),
                                SessionHistoryMetadata.grandparent_thumb.label('grandparent_thumb'),
                                SessionHistory.section_id.label('section_id'),
                                SessionHistoryMetadata.year.label('year'),
                                SessionHistory.rating_key.label('rating_key'),
                                SessionHistoryMetadata.art.label('art'),
                                SessionHistory.media_type.label('media_type'),
                                SessionHistoryMetadata.content_rating.label('content_rating'),
                                SessionHistoryMetadata.labels.label('labels'),
                                SessionHistoryMetadata.live.label('live'),
                                SessionHistoryMetadata.guid.label('guid'),
                            )
                            .select_from(SessionHistory)
                            .join(SessionHistoryMetadata, SessionHistoryMetadata.id == SessionHistory.id)
                            .where(
                                SessionHistory.media_type == 'episode',
                                SessionHistoryMetadata.grandparent_title == agg.c.grandparent_title,
                            )
                        )
                        last_row_stmt = apply_filters(last_row_stmt)
                        last_row = lateral(
                            last_row_stmt
                            .order_by(SessionHistory.started.desc(), SessionHistory.id.desc())
                            .limit(1)
                        ).alias('last_row')

                        sort_metric = agg.c.total_duration if sort_type == 'total_duration' else agg.c.total_plays
                        stmt = (
                            select(
                                last_row.c.id,
                                agg.c.grandparent_title,
                                last_row.c.grandparent_rating_key,
                                last_row.c.grandparent_thumb,
                                last_row.c.section_id,
                                last_row.c.year,
                                last_row.c.rating_key,
                                last_row.c.art,
                                last_row.c.media_type,
                                last_row.c.content_rating,
                                last_row.c.labels,
                                last_row.c.live,
                                last_row.c.guid,
                                agg.c.users_watched,
                                agg.c.last_watch,
                                agg.c.total_plays,
                                agg.c.total_duration,
                            )
                            .select_from(agg)
                            .join(last_row, true())
                            .order_by(agg.c.users_watched.desc(), sort_metric.desc(), agg.c.last_watch.desc())
                        )
                        stmt = queries.apply_pagination(stmt, stats_start, stats_count)
                        result = queries.fetch_mappings(db_session, stmt)
                    except Exception as e:
                        logger.warn("Tautulli DataFactory :: Unable to execute database query for get_home_stats: popular_tv: %s." % e)
                        return None

                    for item in result:
                        row = {'title': item['grandparent_title'],
                               'year': item['year'],
                               'users_watched': item['users_watched'],
                               'rating_key': item['rating_key'] if item['live'] else item['grandparent_rating_key'],
                               'grandparent_rating_key': item['grandparent_rating_key'],
                               'last_play': item['last_watch'],
                               'total_plays': item['total_plays'],
                               'grandparent_thumb': item['grandparent_thumb'],
                               'thumb': item['grandparent_thumb'],
                               'art': item['art'],
                               'section_id': item['section_id'],
                               'media_type': item['media_type'],
                               'content_rating': item['content_rating'],
                               'labels': item['labels'].split(';') if item['labels'] else (),
                               'user': '',
                               'friendly_name': '',
                               'platform': '',
                               'live': item['live'],
                               'guid': item['guid'],
                               'row_id': item['id']
                               }
                        popular_tv.append(row)

                    home_stats.append({'stat_id': stat,
                                       'stat_title': 'Most Popular TV Shows',
                                       'rows': session.mask_session_info(popular_tv)})

                elif stat == 'top_music':
                    top_music = []
                    try:
                        total_plays_expr = func.count(distinct(group_key)).label('total_plays')
                        total_duration_expr = func.sum(duration_expr).label('total_duration')
                        last_watch_expr = func.max(SessionHistory.started).label('last_watch')

                        agg = (
                            select(
                                SessionHistoryMetadata.grandparent_title.label('grandparent_title'),
                                SessionHistoryMetadata.original_title.label('original_title'),
                                total_plays_expr,
                                total_duration_expr,
                                last_watch_expr,
                            )
                            .select_from(SessionHistory)
                            .join(SessionHistoryMetadata, SessionHistoryMetadata.id == SessionHistory.id)
                            .where(SessionHistory.media_type == 'track')
                        )
                        agg = apply_filters(agg)
                        agg = agg.group_by(
                            SessionHistoryMetadata.original_title,
                            SessionHistoryMetadata.grandparent_title,
                        ).subquery()

                        last_row_stmt = (
                            select(
                                SessionHistory.id.label('id'),
                                SessionHistoryMetadata.year.label('year'),
                                SessionHistoryMetadata.grandparent_rating_key.label('grandparent_rating_key'),
                                SessionHistoryMetadata.grandparent_thumb.label('grandparent_thumb'),
                                SessionHistory.section_id.label('section_id'),
                                SessionHistoryMetadata.art.label('art'),
                                SessionHistory.media_type.label('media_type'),
                                SessionHistoryMetadata.content_rating.label('content_rating'),
                                SessionHistoryMetadata.labels.label('labels'),
                                SessionHistoryMetadata.live.label('live'),
                                SessionHistoryMetadata.guid.label('guid'),
                            )
                            .select_from(SessionHistory)
                            .join(SessionHistoryMetadata, SessionHistoryMetadata.id == SessionHistory.id)
                            .where(
                                SessionHistory.media_type == 'track',
                                SessionHistoryMetadata.grandparent_title == agg.c.grandparent_title,
                                or_(
                                    SessionHistoryMetadata.original_title == agg.c.original_title,
                                    and_(
                                        SessionHistoryMetadata.original_title.is_(None),
                                        agg.c.original_title.is_(None),
                                    ),
                                ),
                            )
                        )
                        last_row_stmt = apply_filters(last_row_stmt)
                        last_row = lateral(
                            last_row_stmt
                            .order_by(SessionHistory.started.desc(), SessionHistory.id.desc())
                            .limit(1)
                        ).alias('last_row')

                        sort_metric = agg.c.total_duration if sort_type == 'total_duration' else agg.c.total_plays
                        stmt = (
                            select(
                                last_row.c.id,
                                agg.c.grandparent_title,
                                agg.c.original_title,
                                last_row.c.year,
                                last_row.c.grandparent_rating_key,
                                last_row.c.grandparent_thumb,
                                last_row.c.section_id,
                                last_row.c.art,
                                last_row.c.media_type,
                                last_row.c.content_rating,
                                last_row.c.labels,
                                last_row.c.live,
                                last_row.c.guid,
                                agg.c.last_watch,
                                agg.c.total_plays,
                                agg.c.total_duration,
                            )
                            .select_from(agg)
                            .join(last_row, true())
                            .order_by(sort_metric.desc(), agg.c.last_watch.desc())
                        )
                        stmt = queries.apply_pagination(stmt, stats_start, stats_count)
                        result = queries.fetch_mappings(db_session, stmt)
                    except Exception as e:
                        logger.warn("Tautulli DataFactory :: Unable to execute database query for get_home_stats: top_music: %s." % e)
                        return None

                    for item in result:
                        row = {'title': item['original_title'] or item['grandparent_title'],
                               'year': item['year'],
                               'total_plays': item['total_plays'],
                               'total_duration': item['total_duration'],
                               'users_watched': '',
                               'rating_key': item['grandparent_rating_key'],
                               'grandparent_rating_key': item['grandparent_rating_key'],
                               'last_play': item['last_watch'],
                               'grandparent_thumb': item['grandparent_thumb'],
                               'thumb': item['grandparent_thumb'],
                               'art': item['art'],
                               'section_id': item['section_id'],
                               'media_type': item['media_type'],
                               'content_rating': item['content_rating'],
                               'labels': item['labels'].split(';') if item['labels'] else (),
                               'user': '',
                               'friendly_name': '',
                               'platform': '',
                               'live': item['live'],
                               'guid': item['guid'],
                               'row_id': item['id']
                               }
                        top_music.append(row)

                    home_stats.append({'stat_id': stat,
                                       'stat_type': sort_type,
                                       'stat_title': 'Most Played Artists',
                                       'rows': session.mask_session_info(top_music)})

                elif stat == 'popular_music':
                    popular_music = []
                    try:
                        total_plays_expr = func.count(distinct(group_key)).label('total_plays')
                        total_duration_expr = func.sum(duration_expr).label('total_duration')
                        last_watch_expr = func.max(SessionHistory.started).label('last_watch')
                        users_watched_expr = func.count(distinct(SessionHistory.user_id)).label('users_watched')

                        agg = (
                            select(
                                SessionHistoryMetadata.grandparent_title.label('grandparent_title'),
                                SessionHistoryMetadata.original_title.label('original_title'),
                                users_watched_expr,
                                total_plays_expr,
                                total_duration_expr,
                                last_watch_expr,
                            )
                            .select_from(SessionHistory)
                            .join(SessionHistoryMetadata, SessionHistoryMetadata.id == SessionHistory.id)
                            .where(SessionHistory.media_type == 'track')
                        )
                        agg = apply_filters(agg)
                        agg = agg.group_by(
                            SessionHistoryMetadata.original_title,
                            SessionHistoryMetadata.grandparent_title,
                        ).subquery()

                        last_row_stmt = (
                            select(
                                SessionHistory.id.label('id'),
                                SessionHistoryMetadata.year.label('year'),
                                SessionHistoryMetadata.grandparent_rating_key.label('grandparent_rating_key'),
                                SessionHistoryMetadata.grandparent_thumb.label('grandparent_thumb'),
                                SessionHistory.section_id.label('section_id'),
                                SessionHistoryMetadata.art.label('art'),
                                SessionHistory.media_type.label('media_type'),
                                SessionHistoryMetadata.content_rating.label('content_rating'),
                                SessionHistoryMetadata.labels.label('labels'),
                                SessionHistoryMetadata.live.label('live'),
                                SessionHistoryMetadata.guid.label('guid'),
                            )
                            .select_from(SessionHistory)
                            .join(SessionHistoryMetadata, SessionHistoryMetadata.id == SessionHistory.id)
                            .where(
                                SessionHistory.media_type == 'track',
                                SessionHistoryMetadata.grandparent_title == agg.c.grandparent_title,
                                or_(
                                    SessionHistoryMetadata.original_title == agg.c.original_title,
                                    and_(
                                        SessionHistoryMetadata.original_title.is_(None),
                                        agg.c.original_title.is_(None),
                                    ),
                                ),
                            )
                        )
                        last_row_stmt = apply_filters(last_row_stmt)
                        last_row = lateral(
                            last_row_stmt
                            .order_by(SessionHistory.started.desc(), SessionHistory.id.desc())
                            .limit(1)
                        ).alias('last_row')

                        sort_metric = agg.c.total_duration if sort_type == 'total_duration' else agg.c.total_plays
                        stmt = (
                            select(
                                last_row.c.id,
                                agg.c.grandparent_title,
                                agg.c.original_title,
                                last_row.c.year,
                                last_row.c.grandparent_rating_key,
                                last_row.c.grandparent_thumb,
                                last_row.c.section_id,
                                last_row.c.art,
                                last_row.c.media_type,
                                last_row.c.content_rating,
                                last_row.c.labels,
                                last_row.c.live,
                                last_row.c.guid,
                                agg.c.users_watched,
                                agg.c.last_watch,
                                agg.c.total_plays,
                                agg.c.total_duration,
                            )
                            .select_from(agg)
                            .join(last_row, true())
                            .order_by(agg.c.users_watched.desc(), sort_metric.desc(), agg.c.last_watch.desc())
                        )
                        stmt = queries.apply_pagination(stmt, stats_start, stats_count)
                        result = queries.fetch_mappings(db_session, stmt)
                    except Exception as e:
                        logger.warn("Tautulli DataFactory :: Unable to execute database query for get_home_stats: popular_music: %s." % e)
                        return None

                    for item in result:
                        row = {'title': item['original_title'] or item['grandparent_title'],
                               'year': item['year'],
                               'users_watched': item['users_watched'],
                               'rating_key': item['grandparent_rating_key'],
                               'grandparent_rating_key': item['grandparent_rating_key'],
                               'last_play': item['last_watch'],
                               'total_plays': item['total_plays'],
                               'grandparent_thumb': item['grandparent_thumb'],
                               'thumb': item['grandparent_thumb'],
                               'art': item['art'],
                               'section_id': item['section_id'],
                               'media_type': item['media_type'],
                               'content_rating': item['content_rating'],
                               'labels': item['labels'].split(';') if item['labels'] else (),
                               'user': '',
                               'friendly_name': '',
                               'platform': '',
                               'live': item['live'],
                               'guid': item['guid'],
                               'row_id': item['id']
                               }
                        popular_music.append(row)

                    home_stats.append({'stat_id': stat,
                                       'stat_title': 'Most Popular Artists',
                                       'rows': session.mask_session_info(popular_music)})

                elif stat == 'top_libraries':
                    top_libraries = []
                    try:
                        total_plays_expr = func.count(distinct(group_key)).label('total_plays')
                        total_duration_expr = func.sum(duration_expr).label('total_duration')
                        last_watch_expr = func.max(SessionHistory.started).label('last_watch')

                        agg = (
                            select(
                                SessionHistory.section_id.label('section_id'),
                                total_plays_expr,
                                total_duration_expr,
                                last_watch_expr,
                            )
                            .select_from(SessionHistory)
                            .join(SessionHistoryMetadata, SessionHistoryMetadata.id == SessionHistory.id)
                        )
                        agg = apply_filters(agg)
                        agg = agg.group_by(SessionHistory.section_id).subquery()

                        last_row_stmt = (
                            select(
                                SessionHistory.id.label('id'),
                                SessionHistoryMetadata.title.label('title'),
                                SessionHistoryMetadata.grandparent_title.label('grandparent_title'),
                                SessionHistoryMetadata.full_title.label('full_title'),
                                SessionHistoryMetadata.year.label('year'),
                                SessionHistoryMetadata.media_index.label('media_index'),
                                SessionHistoryMetadata.parent_media_index.label('parent_media_index'),
                                SessionHistory.rating_key.label('rating_key'),
                                SessionHistoryMetadata.grandparent_rating_key.label('grandparent_rating_key'),
                                SessionHistoryMetadata.thumb.label('thumb'),
                                SessionHistoryMetadata.grandparent_thumb.label('grandparent_thumb'),
                                SessionHistory.user.label('user'),
                                SessionHistory.user_id.label('user_id'),
                                SessionHistory.player.label('player'),
                                SessionHistoryMetadata.art.label('art'),
                                SessionHistory.media_type.label('media_type'),
                                SessionHistoryMetadata.content_rating.label('content_rating'),
                                SessionHistoryMetadata.labels.label('labels'),
                                SessionHistoryMetadata.live.label('live'),
                                SessionHistoryMetadata.guid.label('guid'),
                            )
                            .select_from(SessionHistory)
                            .join(SessionHistoryMetadata, SessionHistoryMetadata.id == SessionHistory.id)
                            .where(SessionHistory.section_id == agg.c.section_id)
                        )
                        last_row_stmt = apply_filters(last_row_stmt)
                        last_row = lateral(
                            last_row_stmt
                            .order_by(SessionHistory.started.desc(), SessionHistory.id.desc())
                            .limit(1)
                        ).alias('last_row')

                        sort_metric = agg.c.total_duration if sort_type == 'total_duration' else agg.c.total_plays
                        stmt = (
                            select(
                                last_row.c.id,
                                last_row.c.title,
                                last_row.c.grandparent_title,
                                last_row.c.full_title,
                                last_row.c.year,
                                last_row.c.media_index,
                                last_row.c.parent_media_index,
                                last_row.c.rating_key,
                                last_row.c.grandparent_rating_key,
                                last_row.c.thumb,
                                last_row.c.grandparent_thumb,
                                last_row.c.user,
                                last_row.c.user_id,
                                last_row.c.player,
                                agg.c.section_id,
                                last_row.c.art,
                                last_row.c.media_type,
                                last_row.c.content_rating,
                                last_row.c.labels,
                                last_row.c.live,
                                last_row.c.guid,
                                LibrarySection.section_name.label('section_name'),
                                LibrarySection.section_type.label('section_type'),
                                LibrarySection.thumb.label('library_thumb'),
                                LibrarySection.custom_thumb_url.label('custom_thumb'),
                                LibrarySection.art.label('library_art'),
                                LibrarySection.custom_art_url.label('custom_art'),
                                agg.c.last_watch,
                                agg.c.total_plays,
                                agg.c.total_duration,
                            )
                            .select_from(agg)
                            .join(last_row, true())
                            .outerjoin(
                                LibrarySection,
                                and_(
                                    LibrarySection.section_id == agg.c.section_id,
                                    LibrarySection.deleted_section == 0,
                                ),
                            )
                            .order_by(sort_metric.desc(), agg.c.last_watch.desc())
                        )
                        stmt = queries.apply_pagination(stmt, stats_start, stats_count)
                        result = queries.fetch_mappings(db_session, stmt)
                    except Exception as e:
                        logger.warn("Tautulli DataFactory :: Unable to execute database query for get_home_stats: top_libraries: %s." % e)
                        return None

                    for item in result:
                        if item['custom_thumb'] and item['custom_thumb'] != item['library_thumb']:
                            library_thumb = item['custom_thumb']
                        elif item['library_thumb']:
                            library_thumb = item['library_thumb']
                        else:
                            library_thumb = common.DEFAULT_COVER_THUMB

                        if item['custom_art'] and item['custom_art'] != item['library_art']:
                            library_art = item['custom_art']
                        elif item['library_art'] == common.DEFAULT_LIVE_TV_ART_FULL:
                            library_art = common.DEFAULT_LIVE_TV_ART
                        else:
                            library_art = item['library_art']

                        if not item['grandparent_thumb'] or item['grandparent_thumb'] == '':
                            thumb = item['thumb']
                        else:
                            thumb = item['grandparent_thumb']

                        row = {
                            'total_plays': item['total_plays'],
                            'total_duration': item['total_duration'],
                            'section_type': item['section_type'],
                            'section_name': item['section_name'],
                            'section_id': item['section_id'],
                            'last_play': item['last_watch'],
                            'library_thumb': library_thumb,
                            'library_art': library_art,
                            'thumb': thumb,
                            'grandparent_thumb': item['grandparent_thumb'],
                            'art': item['art'],
                            'user': '',
                            'friendly_name': '',
                            'users_watched': '',
                            'platform': '',
                            'title': item['full_title'],
                            'grandparent_title': item['grandparent_title'],
                            'grandchild_title': item['title'],
                            'year': item['year'],
                            'media_index': item['media_index'],
                            'parent_media_index': item['parent_media_index'],
                            'rating_key': item['rating_key'],
                            'grandparent_rating_key': item['grandparent_rating_key'],
                            'media_type': item['media_type'],
                            'content_rating': item['content_rating'],
                            'labels': item['labels'].split(';') if item['labels'] else (),
                            'live': item['live'],
                            'guid': item['guid'],
                            'row_id': item['id']
                        }
                        top_libraries.append(row)

                    home_stats.append({'stat_id': stat,
                                       'stat_type': sort_type,
                                       'stat_title': 'Most Active Libraries',
                                       'rows': session.mask_session_info(top_libraries)})

                elif stat == 'top_users':
                    top_users = []
                    try:
                        total_plays_expr = func.count(distinct(group_key)).label('total_plays')
                        total_duration_expr = func.sum(duration_expr).label('total_duration')
                        last_watch_expr = func.max(SessionHistory.started).label('last_watch')

                        agg = (
                            select(
                                SessionHistory.user_id.label('user_id'),
                                total_plays_expr,
                                total_duration_expr,
                                last_watch_expr,
                            )
                            .select_from(SessionHistory)
                            .join(SessionHistoryMetadata, SessionHistoryMetadata.id == SessionHistory.id)
                        )
                        agg = apply_filters(agg)
                        agg = agg.group_by(SessionHistory.user_id).subquery()

                        last_row_stmt = (
                            select(
                                SessionHistory.id.label('id'),
                                SessionHistoryMetadata.title.label('title'),
                                SessionHistoryMetadata.grandparent_title.label('grandparent_title'),
                                SessionHistoryMetadata.full_title.label('full_title'),
                                SessionHistoryMetadata.year.label('year'),
                                SessionHistoryMetadata.media_index.label('media_index'),
                                SessionHistoryMetadata.parent_media_index.label('parent_media_index'),
                                SessionHistory.rating_key.label('rating_key'),
                                SessionHistoryMetadata.grandparent_rating_key.label('grandparent_rating_key'),
                                SessionHistoryMetadata.thumb.label('thumb'),
                                SessionHistoryMetadata.grandparent_thumb.label('grandparent_thumb'),
                                SessionHistory.user.label('user'),
                                SessionHistory.player.label('player'),
                                SessionHistoryMetadata.art.label('art'),
                                SessionHistory.media_type.label('media_type'),
                                SessionHistoryMetadata.content_rating.label('content_rating'),
                                SessionHistoryMetadata.labels.label('labels'),
                                SessionHistoryMetadata.live.label('live'),
                                SessionHistoryMetadata.guid.label('guid'),
                            )
                            .select_from(SessionHistory)
                            .join(SessionHistoryMetadata, SessionHistoryMetadata.id == SessionHistory.id)
                            .where(SessionHistory.user_id == agg.c.user_id)
                        )
                        last_row_stmt = apply_filters(last_row_stmt)
                        last_row = lateral(
                            last_row_stmt
                            .order_by(SessionHistory.started.desc(), SessionHistory.id.desc())
                            .limit(1)
                        ).alias('last_row')

                        sort_metric = agg.c.total_duration if sort_type == 'total_duration' else agg.c.total_plays
                        stmt = (
                            select(
                                last_row.c.id,
                                last_row.c.title,
                                last_row.c.grandparent_title,
                                last_row.c.full_title,
                                last_row.c.year,
                                last_row.c.media_index,
                                last_row.c.parent_media_index,
                                last_row.c.rating_key,
                                last_row.c.grandparent_rating_key,
                                last_row.c.thumb,
                                last_row.c.grandparent_thumb,
                                last_row.c.user,
                                agg.c.user_id,
                                last_row.c.player,
                                last_row.c.art,
                                last_row.c.media_type,
                                last_row.c.content_rating,
                                last_row.c.labels,
                                last_row.c.live,
                                last_row.c.guid,
                                User.thumb.label('user_thumb'),
                                User.custom_avatar_url.label('custom_thumb'),
                                friendly_name_expr.label('friendly_name'),
                                agg.c.last_watch,
                                agg.c.total_plays,
                                agg.c.total_duration,
                            )
                            .select_from(agg)
                            .join(last_row, true())
                            .outerjoin(User, agg.c.user_id == User.user_id)
                            .order_by(sort_metric.desc(), agg.c.last_watch.desc())
                        )
                        stmt = queries.apply_pagination(stmt, stats_start, stats_count)
                        result = queries.fetch_mappings(db_session, stmt)
                    except Exception as e:
                        logger.warn("Tautulli DataFactory :: Unable to execute database query for get_home_stats: top_users: %s." % e)
                        return None

                    for item in result:
                        if item['custom_thumb'] and item['custom_thumb'] != item['user_thumb']:
                            user_thumb = item['custom_thumb']
                        elif item['user_thumb']:
                            user_thumb = item['user_thumb']
                        else:
                            user_thumb = common.DEFAULT_USER_THUMB

                        if not item['grandparent_thumb'] or item['grandparent_thumb'] == '':
                            thumb = item['thumb']
                        else:
                            thumb = item['grandparent_thumb']

                        row = {'user': item['user'],
                               'user_id': item['user_id'],
                               'friendly_name': item['friendly_name'],
                               'total_plays': item['total_plays'],
                               'total_duration': item['total_duration'],
                               'last_play': item['last_watch'],
                               'user_thumb': user_thumb,
                               'thumb': thumb,
                               'grandparent_thumb': item['grandparent_thumb'],
                               'art': item['art'],
                               'users_watched': '',
                               'platform': '',
                               'title': item['full_title'],
                               'grandparent_title': item['grandparent_title'],
                               'grandchild_title': item['title'],
                               'year': item['year'],
                               'media_index': item['media_index'],
                               'parent_media_index': item['parent_media_index'],
                               'rating_key': item['rating_key'],
                               'grandparent_rating_key': item['grandparent_rating_key'],
                               'media_type': item['media_type'],
                               'content_rating': item['content_rating'],
                               'labels': item['labels'].split(';') if item['labels'] else (),
                               'live': item['live'],
                               'guid': item['guid'],
                               'row_id': item['id']
                               }
                        top_users.append(row)

                    home_stats.append({'stat_id': stat,
                                       'stat_type': sort_type,
                                       'stat_title': 'Most Active Users',
                                       'rows': session.mask_session_info(top_users)})

                elif stat == 'top_platforms':
                    top_platform = []

                    try:
                        total_plays_expr = func.count(distinct(group_key)).label('total_plays')
                        total_duration_expr = func.sum(duration_expr).label('total_duration')
                        last_watch_expr = func.max(SessionHistory.started).label('last_watch')
                        sort_metric = total_duration_expr if sort_type == 'total_duration' else total_plays_expr

                        stmt = (
                            select(
                                SessionHistory.platform,
                                last_watch_expr,
                                total_plays_expr,
                                total_duration_expr,
                            )
                            .select_from(SessionHistory)
                        )
                        stmt = apply_filters(stmt)
                        stmt = (
                            stmt.group_by(SessionHistory.platform)
                            .order_by(sort_metric.desc(), last_watch_expr.desc())
                        )
                        stmt = queries.apply_pagination(stmt, stats_start, stats_count)
                        result = queries.fetch_mappings(db_session, stmt)
                    except Exception as e:
                        logger.warn("Tautulli DataFactory :: Unable to execute database query for get_home_stats: top_platforms: %s." % e)
                        return None

                    for item in result:
                        # Rename Mystery platform names
                        platform = common.PLATFORM_NAME_OVERRIDES.get(item['platform'], item['platform'])
                        platform_name = next((v for k, v in common.PLATFORM_NAMES.items() if k in platform.lower()), 'default')

                        row = {'total_plays': item['total_plays'],
                               'total_duration': item['total_duration'],
                               'last_play': item['last_watch'],
                               'platform': platform,
                               'platform_name': platform_name,
                               'title': '',
                               'thumb': '',
                               'grandparent_thumb': '',
                               'art': '',
                               'users_watched': '',
                               'rating_key': '',
                               'grandparent_rating_key': '',
                               'user': '',
                               'friendly_name': '',
                               'row_id': ''
                               }
                        top_platform.append(row)

                    home_stats.append({'stat_id': stat,
                                       'stat_type': sort_type,
                                       'stat_title': 'Most Active Platforms',
                                       'rows': session.mask_session_info(top_platform, mask_metadata=False)})

                elif stat == 'last_watched':

                    movie_watched_percent = plexpy.CONFIG.MOVIE_WATCHED_PERCENT
                    tv_watched_percent = plexpy.CONFIG.TV_WATCHED_PERCENT

                    last_watched = []
                    try:
                        base_stmt = (
                            select(SessionHistory)
                            .where(SessionHistory.media_type.in_(['movie', 'episode']))
                        )
                        base_stmt = apply_filters(base_stmt)
                        base_stmt = (
                            base_stmt.distinct(group_key)
                            .order_by(group_key, SessionHistory.started.desc(), SessionHistory.id.desc())
                        )
                        sh_subquery = base_stmt.subquery()
                        sh = aliased(SessionHistory, sh_subquery)

                        view_offset_expr = case(
                            (sh.view_offset.is_(None), literal(0.1)),
                            else_=cast(sh.view_offset, Float),
                        )
                        duration_expr_watched = case(
                            (SessionHistoryMetadata.duration.is_(None), literal(1.0)),
                            else_=cast(SessionHistoryMetadata.duration, Float),
                        )
                        percent_complete_expr = (view_offset_expr / duration_expr_watched * 100)
                        percent_threshold_expr = duration_expr_watched * case(
                            (sh.media_type == 'movie', movie_watched_percent),
                            else_=tv_watched_percent,
                        ) / 100.0

                        if plexpy.CONFIG.WATCHED_MARKER == 1:
                            watched_threshold_expr = case(
                                (SessionHistoryMetadata.marker_credits_final.is_(None), percent_threshold_expr),
                                else_=SessionHistoryMetadata.marker_credits_final,
                            )
                            watched_where = view_offset_expr >= watched_threshold_expr
                        elif plexpy.CONFIG.WATCHED_MARKER == 2:
                            watched_threshold_expr = case(
                                (SessionHistoryMetadata.marker_credits_first.is_(None), percent_threshold_expr),
                                else_=SessionHistoryMetadata.marker_credits_first,
                            )
                            watched_where = view_offset_expr >= watched_threshold_expr
                        elif plexpy.CONFIG.WATCHED_MARKER == 3:
                            first_marker = case(
                                (SessionHistoryMetadata.marker_credits_first.is_(None), percent_threshold_expr),
                                else_=SessionHistoryMetadata.marker_credits_first,
                            )
                            watched_threshold_expr = func.least(first_marker, percent_threshold_expr)
                            watched_where = view_offset_expr >= watched_threshold_expr
                        else:
                            watched_threshold_expr = literal(None)
                            watched_where = or_(
                                and_(sh.media_type == 'movie', percent_complete_expr >= movie_watched_percent),
                                and_(sh.media_type == 'episode', percent_complete_expr >= tv_watched_percent),
                            )

                        stmt = (
                            select(
                                sh.id,
                                SessionHistoryMetadata.title,
                                SessionHistoryMetadata.grandparent_title,
                                SessionHistoryMetadata.full_title,
                                SessionHistoryMetadata.year,
                                SessionHistoryMetadata.media_index,
                                SessionHistoryMetadata.parent_media_index,
                                sh.rating_key,
                                SessionHistoryMetadata.grandparent_rating_key,
                                SessionHistoryMetadata.thumb,
                                SessionHistoryMetadata.grandparent_thumb,
                                sh.user,
                                sh.user_id,
                                User.custom_avatar_url.label('user_thumb'),
                                sh.player,
                                sh.section_id,
                                SessionHistoryMetadata.art,
                                sh.media_type,
                                SessionHistoryMetadata.content_rating,
                                SessionHistoryMetadata.labels,
                                SessionHistoryMetadata.live,
                                SessionHistoryMetadata.guid,
                                friendly_name_expr.label('friendly_name'),
                                sh.started.label('last_watch'),
                                view_offset_expr.label('_view_offset'),
                                duration_expr_watched.label('_duration'),
                                percent_complete_expr.label('percent_complete'),
                                watched_threshold_expr.label('watched_threshold'),
                            )
                            .select_from(sh)
                            .join(SessionHistoryMetadata, SessionHistoryMetadata.id == sh.id)
                            .outerjoin(User, sh.user_id == User.user_id)
                            .where(watched_where)
                            .order_by(sh.started.desc())
                        )
                        stmt = queries.apply_pagination(stmt, stats_start, stats_count)
                        result = queries.fetch_mappings(db_session, stmt)
                    except Exception as e:
                        logger.warn("Tautulli DataFactory :: Unable to execute database query for get_home_stats: last_watched: %s." % e)
                        return None

                    for item in result:
                        if not item['grandparent_thumb'] or item['grandparent_thumb'] == '':
                            thumb = item['thumb']
                        else:
                            thumb = item['grandparent_thumb']

                        row = {'row_id': item['id'],
                               'user': item['user'],
                               'friendly_name': item['friendly_name'],
                               'user_id': item['user_id'],
                               'user_thumb': item['user_thumb'],
                               'title': item['full_title'],
                               'grandparent_title': item['grandparent_title'],
                               'grandchild_title': item['title'],
                               'year': item['year'],
                               'media_index': item['media_index'],
                               'parent_media_index': item['parent_media_index'],
                               'rating_key': item['rating_key'],
                               'grandparent_rating_key': item['grandparent_rating_key'],
                               'thumb': thumb,
                               'grandparent_thumb': item['grandparent_thumb'],
                               'art': item['art'],
                               'section_id': item['section_id'],
                               'media_type': item['media_type'],
                               'content_rating': item['content_rating'],
                               'labels': item['labels'].split(';') if item['labels'] else (),
                               'last_watch': item['last_watch'],
                               'live': item['live'],
                               'guid': item['guid'],
                               'player': item['player']
                               }
                        last_watched.append(row)

                    home_stats.append({'stat_id': stat,
                                       'stat_title': 'Recently Watched',
                                       'rows': session.mask_session_info(last_watched)})

                elif stat == 'most_concurrent':

                    def calc_most_concurrent(title, result):
                        times = []
                        for item in result:
                            times.append({'time': str(item['started']) + 'B', 'count': 1})
                            times.append({'time': str(item['stopped']) + 'A', 'count': -1})
                        times = sorted(times, key=lambda k: k['time'])

                        count = 0
                        last_count = 0
                        last_start = ''
                        concurrent = {'title': title,
                                      'count': 0,
                                      'started': None,
                                      'stopped': None
                                      }

                        for d in times:
                            if d['count'] == 1:
                                count += d['count']
                                if count >= last_count:
                                    last_start = d['time']
                            else:
                                if count >= last_count:
                                    last_count = count
                                    concurrent['count'] = count
                                    concurrent['started'] = last_start[:-1]
                                    concurrent['stopped'] = d['time'][:-1]
                                count += d['count']

                        return concurrent

                    most_concurrent = []

                    try:
                        stmt = (
                            select(
                                SessionHistory.started,
                                SessionHistory.stopped,
                                SessionHistoryMediaInfo.transcode_decision,
                            )
                            .select_from(SessionHistory)
                            .join(SessionHistoryMediaInfo, SessionHistoryMediaInfo.id == SessionHistory.id)
                        )
                        stmt = apply_filters(stmt)
                        result = queries.fetch_mappings(db_session, stmt)
                    except Exception as e:
                        logger.warn("Tautulli DataFactory :: Unable to execute database query for get_home_stats: most_concurrent: %s." % e)
                        return None

                    if result:
                        most_concurrent.append(calc_most_concurrent('Concurrent Streams', result))

                        decision_map = (
                            ('transcode', 'Concurrent Transcodes'),
                            ('copy', 'Concurrent Direct Streams'),
                            ('direct play', 'Concurrent Direct Plays'),
                        )

                        for decision, title in decision_map:
                            filtered = [row for row in result if row['transcode_decision'] == decision]
                            if filtered:
                                most_concurrent.append(calc_most_concurrent(title, filtered))

                    home_stats.append({'stat_id': stat,
                                       'stat_title': 'Most Concurrent Streams',
                                       'rows': most_concurrent})

        if stat_id and home_stats:
            return home_stats[0]
        return home_stats

    def get_library_stats(self, library_cards=[]):
        if session.get_session_shared_libraries():
            library_cards = session.get_session_shared_libraries()

        library_ids = [helpers.cast_to_int(section_id) for section_id in library_cards if str(section_id).isdigit()]
        if not library_ids:
            return None

        library_stats = []

        try:
            latest_session = lateral(
                select(
                    SessionHistory.id.label('id'),
                    SessionHistory.rating_key,
                    SessionHistory.user,
                    SessionHistory.user_id,
                    SessionHistory.player,
                    SessionHistory.section_id,
                    SessionHistory.media_type,
                    SessionHistory.started,
                )
                .where(SessionHistory.section_id == LibrarySection.section_id)
                .order_by(SessionHistory.started.desc(), SessionHistory.id.desc())
                .limit(1)
            ).alias('sh')

            stmt = (
                select(
                    LibrarySection.section_id,
                    LibrarySection.section_name,
                    LibrarySection.section_type,
                    LibrarySection.thumb.label('library_thumb'),
                    LibrarySection.custom_thumb_url.label('custom_thumb'),
                    LibrarySection.art.label('library_art'),
                    LibrarySection.custom_art_url.label('custom_art'),
                    LibrarySection.count,
                    LibrarySection.parent_count,
                    LibrarySection.child_count,
                    latest_session.c.id.label('id'),
                    SessionHistoryMetadata.title,
                    SessionHistoryMetadata.grandparent_title,
                    SessionHistoryMetadata.full_title,
                    SessionHistoryMetadata.year,
                    SessionHistoryMetadata.media_index,
                    SessionHistoryMetadata.parent_media_index,
                    latest_session.c.rating_key,
                    SessionHistoryMetadata.grandparent_rating_key,
                    SessionHistoryMetadata.thumb,
                    SessionHistoryMetadata.grandparent_thumb,
                    latest_session.c.user,
                    latest_session.c.user_id,
                    latest_session.c.player,
                    SessionHistoryMetadata.art,
                    latest_session.c.media_type,
                    SessionHistoryMetadata.content_rating,
                    SessionHistoryMetadata.labels,
                    SessionHistoryMetadata.live,
                    SessionHistoryMetadata.guid,
                    latest_session.c.started.label('last_watch'),
                )
                .select_from(LibrarySection)
                .outerjoin(latest_session, true())
                .outerjoin(SessionHistoryMetadata, latest_session.c.id == SessionHistoryMetadata.id)
                .where(
                    LibrarySection.section_id.in_(library_ids),
                    LibrarySection.deleted_section == 0,
                )
                .order_by(
                    LibrarySection.section_type,
                    LibrarySection.count.desc(),
                    LibrarySection.parent_count.desc(),
                    LibrarySection.child_count.desc(),
                )
            )
            with session_scope() as db_session:
                result = queries.fetch_mappings(db_session, stmt)
        except Exception as e:
            logger.warn("Tautulli DataFactory :: Unable to execute database query for get_library_stats: %s." % e)
            return None

        for item in result:
            if item['custom_thumb'] and item['custom_thumb'] != item['library_thumb']:
                library_thumb = item['custom_thumb']
            elif item['library_thumb']:
                library_thumb = item['library_thumb']
            else:
                library_thumb = common.DEFAULT_COVER_THUMB

            if item['custom_art'] and item['custom_art'] != item['library_art']:
                library_art = item['custom_art']
            else:
                library_art = item['library_art']

            if not item['grandparent_thumb'] or item['grandparent_thumb'] == '':
                thumb = item['thumb']
            else:
                thumb = item['grandparent_thumb']

            library = {'section_id': item['section_id'],
                       'section_name': item['section_name'],
                       'section_type': item['section_type'],
                       'library_thumb': library_thumb,
                       'library_art': library_art,
                       'count': item['count'],
                       'child_count': item['parent_count'],
                       'grandchild_count': item['child_count'],
                       'thumb': thumb or '',
                       'grandparent_thumb': item['grandparent_thumb'] or '',
                       'art': item['art'] or '',
                       'title': item['full_title'],
                       'grandparent_title': item['grandparent_title'],
                       'grandchild_title': item['title'],
                       'year': item['year'],
                       'media_index': item['media_index'],
                       'parent_media_index': item['parent_media_index'],
                       'rating_key': item['rating_key'],
                       'grandparent_rating_key': item['grandparent_rating_key'],
                       'media_type': item['media_type'],
                       'content_rating': item['content_rating'],
                       'labels': item['labels'].split(';') if item['labels'] else (),
                       'live': item['live'],
                       'guid': item['guid'],
                       'row_id': item['id']
                       }
            library_stats.append(library)

        library_stats = session.mask_session_info(library_stats)
        library_stats = helpers.group_by_keys(library_stats, 'section_type')

        return library_stats

    def get_watch_time_stats(self, rating_key=None, guid=None, media_type=None, grouping=None, query_days=None):
        if rating_key is None and guid is None:
            return []

        if grouping is None:
            grouping = plexpy.CONFIG.GROUP_HISTORY_TABLES

        if query_days and query_days is not None:
            query_days = map(helpers.cast_to_int, str(query_days).split(','))
        else:
            query_days = [1, 7, 30, 0]

        timestamp = helpers.timestamp()

        item_watch_time_stats = []

        section_ids = set()

        group_key = self._group_key_expr(grouping)
        total_time_expr = (
            func.sum(SessionHistory.stopped - SessionHistory.started)
            - func.sum(func.coalesce(SessionHistory.paused_counter, 0))
        ).label('total_time')
        total_plays_expr = func.count(distinct(group_key)).label('total_plays')

        if media_type in ('collection', 'playlist'):
            pms_connect = pmsconnect.PmsConnect()
            result = pms_connect.get_item_children(rating_key=rating_key, media_type=media_type)
            rating_keys = [child['rating_key'] for child in result['children_list']]
        else:
            rating_keys = [rating_key]

        rating_keys = [helpers.cast_to_int(key) for key in rating_keys if str(key).isdigit()]
        rating_filter = None
        if rating_keys:
            rating_filter = or_(
                SessionHistory.grandparent_rating_key.in_(rating_keys),
                SessionHistory.parent_rating_key.in_(rating_keys),
                SessionHistory.rating_key.in_(rating_keys),
            )

        for days in query_days:
            timestamp_query = timestamp - days * 24 * 60 * 60

            try:
                stmt = (
                    select(
                        total_time_expr,
                        total_plays_expr,
                        func.max(SessionHistory.section_id).label('section_id'),
                    )
                    .select_from(SessionHistory)
                    .join(SessionHistoryMetadata, SessionHistoryMetadata.id == SessionHistory.id)
                )
                if days > 0:
                    stmt = stmt.where(SessionHistory.stopped >= timestamp_query)

                if rating_filter is not None:
                    stmt = stmt.where(rating_filter)
                elif guid:
                    stmt = stmt.where(SessionHistoryMetadata.guid == guid)
                else:
                    continue

                with session_scope() as db_session:
                    result = queries.fetch_mapping(db_session, stmt, default={})
            except Exception as e:
                logger.warn("Tautulli Libraries :: Unable to execute database query for get_watch_time_stats: %s." % e)
                result = {}

            if result:
                section_id = result.get('section_id')
                if section_id is not None:
                    section_ids.add(section_id)

                total_time = result.get('total_time') or 0
                total_plays = result.get('total_plays') or 0

                row = {'query_days': days,
                       'total_time': total_time,
                       'total_plays': total_plays
                       }

                item_watch_time_stats.append(row)

        if any(not session.allow_session_library(section_id) for section_id in section_ids):
            return []

        return item_watch_time_stats

    def get_user_stats(self, rating_key=None, guid=None, media_type=None, grouping=None):
        if grouping is None:
            grouping = plexpy.CONFIG.GROUP_HISTORY_TABLES
        user_stats = []

        section_ids = set()

        group_key = self._group_key_expr(grouping)
        total_time_expr = (
            func.sum(SessionHistory.stopped - SessionHistory.started)
            - func.sum(func.coalesce(SessionHistory.paused_counter, 0))
        ).label('total_time')
        total_plays_expr = func.count(distinct(group_key)).label('total_plays')
        friendly_name_expr = case(
            (or_(User.friendly_name.is_(None), func.trim(User.friendly_name) == ''), User.username),
            else_=User.friendly_name,
        )

        if media_type in ('collection', 'playlist'):
            pms_connect = pmsconnect.PmsConnect()
            result = pms_connect.get_item_children(rating_key=rating_key, media_type=media_type)
            rating_keys = [child['rating_key'] for child in result['children_list']]
        else:
            rating_keys = [rating_key]

        rating_keys = [helpers.cast_to_int(key) for key in rating_keys if str(key).isdigit()]
        rating_filter = None
        if rating_keys:
            rating_filter = or_(
                SessionHistory.grandparent_rating_key.in_(rating_keys),
                SessionHistory.parent_rating_key.in_(rating_keys),
                SessionHistory.rating_key.in_(rating_keys),
            )

        try:
            stmt = (
                select(
                    friendly_name_expr.label('friendly_name'),
                    User.user_id,
                    User.username,
                    User.thumb,
                    User.custom_avatar_url.label('custom_thumb'),
                    total_plays_expr,
                    total_time_expr,
                    func.max(SessionHistory.section_id).label('section_id'),
                )
                .select_from(SessionHistory)
                .join(SessionHistoryMetadata, SessionHistoryMetadata.id == SessionHistory.id)
                .join(User, User.user_id == SessionHistory.user_id)
            )

            if rating_filter is not None:
                stmt = stmt.where(rating_filter)
            elif guid:
                stmt = stmt.where(SessionHistoryMetadata.guid == guid)
            else:
                stmt = None

            if stmt is not None:
                stmt = (
                    stmt.group_by(User.user_id, User.username, User.friendly_name, User.thumb, User.custom_avatar_url)
                    .order_by(total_plays_expr.desc(), total_time_expr.desc())
                )
                with session_scope() as db_session:
                    result = queries.fetch_mappings(db_session, stmt)
            else:
                result = []
        except Exception as e:
            logger.warn("Tautulli Libraries :: Unable to execute database query for get_user_stats: %s." % e)
            result = []

        for item in result:
            section_ids.add(item['section_id'])

            if item['custom_thumb'] and item['custom_thumb'] != item['thumb']:
                user_thumb = item['custom_thumb']
            elif item['thumb']:
                user_thumb = item['thumb']
            else:
                user_thumb = common.DEFAULT_USER_THUMB

            row = {'friendly_name': item['friendly_name'],
                   'user_id': item['user_id'],
                   'user_thumb': user_thumb,
                   'username': item['username'],
                   'total_plays': item['total_plays'],
                   'total_time': item['total_time']
                   }
            user_stats.append(row)

        if any(not session.allow_session_library(section_id) for section_id in section_ids):
            return []

        return session.mask_session_info(user_stats, mask_metadata=False)

    def get_stream_details(self, row_id=None, session_key=None):
        session_user_id = session.get_session_user_id()
        user_id_filter = helpers.cast_to_int(session_user_id) if session_user_id else None

        if row_id:
            if not str(row_id).isdigit():
                return None
            row_id = helpers.cast_to_int(row_id)
            stmt = (
                select(
                    SessionHistoryMediaInfo.bitrate,
                    SessionHistoryMediaInfo.video_full_resolution,
                    SessionHistoryMediaInfo.optimized_version,
                    SessionHistoryMediaInfo.optimized_version_profile,
                    SessionHistoryMediaInfo.optimized_version_title,
                    SessionHistoryMediaInfo.synced_version,
                    SessionHistoryMediaInfo.synced_version_profile,
                    SessionHistoryMediaInfo.container,
                    SessionHistoryMediaInfo.video_codec,
                    SessionHistoryMediaInfo.video_bitrate,
                    SessionHistoryMediaInfo.video_width,
                    SessionHistoryMediaInfo.video_height,
                    SessionHistoryMediaInfo.video_framerate,
                    SessionHistoryMediaInfo.video_dynamic_range,
                    SessionHistoryMediaInfo.aspect_ratio,
                    SessionHistoryMediaInfo.audio_codec,
                    SessionHistoryMediaInfo.audio_bitrate,
                    SessionHistoryMediaInfo.audio_channels,
                    SessionHistoryMediaInfo.audio_language,
                    SessionHistoryMediaInfo.audio_language_code,
                    SessionHistoryMediaInfo.subtitle_codec,
                    SessionHistoryMediaInfo.subtitle_forced,
                    SessionHistoryMediaInfo.subtitle_language,
                    SessionHistoryMediaInfo.stream_bitrate,
                    SessionHistoryMediaInfo.stream_video_full_resolution,
                    SessionHistory.quality_profile,
                    SessionHistoryMediaInfo.stream_container_decision,
                    SessionHistoryMediaInfo.stream_container,
                    SessionHistoryMediaInfo.stream_video_decision,
                    SessionHistoryMediaInfo.stream_video_codec,
                    SessionHistoryMediaInfo.stream_video_bitrate,
                    SessionHistoryMediaInfo.stream_video_width,
                    SessionHistoryMediaInfo.stream_video_height,
                    SessionHistoryMediaInfo.stream_video_framerate,
                    SessionHistoryMediaInfo.stream_video_dynamic_range,
                    SessionHistoryMediaInfo.stream_audio_decision,
                    SessionHistoryMediaInfo.stream_audio_codec,
                    SessionHistoryMediaInfo.stream_audio_bitrate,
                    SessionHistoryMediaInfo.stream_audio_channels,
                    SessionHistoryMediaInfo.stream_audio_language,
                    SessionHistoryMediaInfo.stream_audio_language_code,
                    SessionHistoryMediaInfo.subtitles,
                    SessionHistoryMediaInfo.stream_subtitle_decision,
                    SessionHistoryMediaInfo.stream_subtitle_codec,
                    SessionHistoryMediaInfo.stream_subtitle_forced,
                    SessionHistoryMediaInfo.stream_subtitle_language,
                    SessionHistoryMediaInfo.transcode_hw_decoding,
                    SessionHistoryMediaInfo.transcode_hw_encoding,
                    SessionHistoryMediaInfo.video_decision,
                    SessionHistoryMediaInfo.audio_decision,
                    SessionHistoryMediaInfo.transcode_decision,
                    SessionHistoryMediaInfo.width,
                    SessionHistoryMediaInfo.height,
                    SessionHistoryMediaInfo.transcode_container,
                    SessionHistoryMediaInfo.transcode_video_codec,
                    SessionHistoryMediaInfo.transcode_audio_codec,
                    SessionHistoryMediaInfo.transcode_audio_channels,
                    SessionHistoryMediaInfo.transcode_width,
                    SessionHistoryMediaInfo.transcode_height,
                    SessionHistoryMetadata.media_type,
                    SessionHistoryMetadata.title,
                    SessionHistoryMetadata.grandparent_title,
                    SessionHistoryMetadata.original_title,
                )
                .select_from(SessionHistoryMediaInfo)
                .join(SessionHistory, SessionHistoryMediaInfo.id == SessionHistory.id)
                .join(SessionHistoryMetadata, SessionHistoryMediaInfo.id == SessionHistoryMetadata.id)
                .where(SessionHistoryMediaInfo.id == row_id)
            )
            if user_id_filter is not None:
                stmt = stmt.where(SessionHistory.user_id == user_id_filter)
            with session_scope() as db_session:
                result = queries.fetch_mappings(db_session, stmt)
        elif session_key:
            if not str(session_key).isdigit():
                return None
            session_key = helpers.cast_to_int(session_key)
            stmt = (
                select(
                    Session.bitrate,
                    Session.video_full_resolution,
                    Session.optimized_version,
                    Session.optimized_version_profile,
                    Session.optimized_version_title,
                    Session.synced_version,
                    Session.synced_version_profile,
                    Session.container,
                    Session.video_codec,
                    Session.video_bitrate,
                    Session.video_width,
                    Session.video_height,
                    Session.video_framerate,
                    Session.video_dynamic_range,
                    Session.aspect_ratio,
                    Session.audio_codec,
                    Session.audio_bitrate,
                    Session.audio_channels,
                    Session.audio_language,
                    Session.audio_language_code,
                    Session.subtitle_codec,
                    Session.subtitle_forced,
                    Session.subtitle_language,
                    Session.stream_bitrate,
                    Session.stream_video_full_resolution,
                    Session.quality_profile,
                    Session.stream_container_decision,
                    Session.stream_container,
                    Session.stream_video_decision,
                    Session.stream_video_codec,
                    Session.stream_video_bitrate,
                    Session.stream_video_width,
                    Session.stream_video_height,
                    Session.stream_video_framerate,
                    Session.stream_video_dynamic_range,
                    Session.stream_audio_decision,
                    Session.stream_audio_codec,
                    Session.stream_audio_bitrate,
                    Session.stream_audio_channels,
                    Session.stream_audio_language,
                    Session.stream_audio_language_code,
                    Session.subtitles,
                    Session.stream_subtitle_decision,
                    Session.stream_subtitle_codec,
                    Session.stream_subtitle_forced,
                    Session.stream_subtitle_language,
                    Session.transcode_hw_decoding,
                    Session.transcode_hw_encoding,
                    Session.video_decision,
                    Session.audio_decision,
                    Session.transcode_decision,
                    Session.width,
                    Session.height,
                    Session.transcode_container,
                    Session.transcode_video_codec,
                    Session.transcode_audio_codec,
                    Session.transcode_audio_channels,
                    Session.transcode_width,
                    Session.transcode_height,
                    Session.media_type,
                    Session.title,
                    Session.grandparent_title,
                    Session.original_title,
                )
                .select_from(Session)
                .where(Session.session_key == session_key)
            )
            if user_id_filter is not None:
                stmt = stmt.where(Session.user_id == user_id_filter)
            with session_scope() as db_session:
                result = queries.fetch_mappings(db_session, stmt)
        else:
            return None

        stream_output = {}

        for item in result:
            pre_tautulli = 0

            # For backwards compatibility. Pick one new Tautulli key to check and override with old values.
            if not item['stream_container']:
                item['stream_video_full_resolution'] = item['video_full_resolution']
                item['stream_container'] = item['transcode_container'] or item['container']
                item['stream_video_decision'] = item['video_decision']
                item['stream_video_codec'] = item['transcode_video_codec'] or item['video_codec']
                item['stream_video_width'] = item['transcode_width'] or item['width']
                item['stream_video_height'] = item['transcode_height'] or item['height']
                item['stream_audio_decision'] = item['audio_decision']
                item['stream_audio_codec'] = item['transcode_audio_codec'] or item['audio_codec']
                item['stream_audio_channels'] = item['transcode_audio_channels'] or item['audio_channels']
                item['video_width'] = item['width']
                item['video_height'] = item['height']
                pre_tautulli = 1

            stream_output = {'bitrate': item['bitrate'],
                             'video_full_resolution': item['video_full_resolution'],
                             'optimized_version': item['optimized_version'],
                             'optimized_version_profile': item['optimized_version_profile'],
                             'optimized_version_title': item['optimized_version_title'],
                             'synced_version': item['synced_version'],
                             'synced_version_profile': item['synced_version_profile'],
                             'container': item['container'],
                             'video_codec': item['video_codec'],
                             'video_bitrate': item['video_bitrate'],
                             'video_width': item['video_width'],
                             'video_height': item['video_height'],
                             'video_framerate': item['video_framerate'],
                             'video_dynamic_range': item['video_dynamic_range'],
                             'aspect_ratio': item['aspect_ratio'],
                             'audio_codec': item['audio_codec'],
                             'audio_bitrate': item['audio_bitrate'],
                             'audio_channels': item['audio_channels'],
                             'audio_language': item['audio_language'],
                             'audio_language_code': item['audio_language_code'],
                             'subtitle_codec': item['subtitle_codec'],
                             'subtitle_forced': item['subtitle_forced'],
                             'subtitle_language': item['subtitle_language'],
                             'stream_bitrate': item['stream_bitrate'],
                             'stream_video_full_resolution': item['stream_video_full_resolution'],
                             'quality_profile': item['quality_profile'],
                             'stream_container_decision': item['stream_container_decision'],
                             'stream_container': item['stream_container'],
                             'stream_video_decision': item['stream_video_decision'],
                             'stream_video_codec': item['stream_video_codec'],
                             'stream_video_bitrate': item['stream_video_bitrate'],
                             'stream_video_width': item['stream_video_width'],
                             'stream_video_height': item['stream_video_height'],
                             'stream_video_framerate': item['stream_video_framerate'],
                             'stream_video_dynamic_range': item['stream_video_dynamic_range'],
                             'stream_audio_decision': item['stream_audio_decision'],
                             'stream_audio_codec': item['stream_audio_codec'],
                             'stream_audio_bitrate': item['stream_audio_bitrate'],
                             'stream_audio_channels': item['stream_audio_channels'],
                             'stream_audio_language': item['stream_audio_language'],
                             'stream_audio_language_code': item['stream_audio_language_code'],
                             'subtitles': item['subtitles'],
                             'stream_subtitle_decision': item['stream_subtitle_decision'],
                             'stream_subtitle_codec': item['stream_subtitle_codec'],
                             'stream_subtitle_forced': item['stream_subtitle_forced'],
                             'stream_subtitle_language': item['stream_subtitle_language'],
                             'transcode_hw_decoding': item['transcode_hw_decoding'],
                             'transcode_hw_encoding': item['transcode_hw_encoding'],
                             'video_decision': item['video_decision'],
                             'audio_decision': item['audio_decision'],
                             'media_type': item['media_type'],
                             'title': item['title'],
                             'grandparent_title': item['grandparent_title'],
                             'original_title': item['original_title'],
                             'current_session': 1 if session_key else 0,
                             'pre_tautulli': pre_tautulli
                             }

        stream_output = {k: v or '' for k, v in stream_output.items()}
        return stream_output

    def get_metadata_details(self, rating_key='', guid=''):
        if rating_key or guid:
            if guid:
                guid_prefix = guid.split('?')[0] + '%'
                where_cond = SessionHistoryMetadata.guid.like(guid_prefix)
            else:
                where_cond = SessionHistoryMetadata.rating_key == helpers.cast_to_int(rating_key)

            stmt = (
                select(
                    SessionHistory.section_id.label('section_id'),
                    SessionHistoryMetadata.id.label('id'),
                    SessionHistoryMetadata.rating_key,
                    SessionHistoryMetadata.parent_rating_key,
                    SessionHistoryMetadata.grandparent_rating_key,
                    SessionHistoryMetadata.title,
                    SessionHistoryMetadata.parent_title,
                    SessionHistoryMetadata.grandparent_title,
                    SessionHistoryMetadata.original_title,
                    SessionHistoryMetadata.full_title,
                    LibrarySection.section_name,
                    SessionHistoryMetadata.media_index,
                    SessionHistoryMetadata.parent_media_index,
                    SessionHistoryMetadata.thumb,
                    SessionHistoryMetadata.parent_thumb,
                    SessionHistoryMetadata.grandparent_thumb,
                    SessionHistoryMetadata.art,
                    SessionHistoryMetadata.media_type,
                    SessionHistoryMetadata.year,
                    SessionHistoryMetadata.originally_available_at,
                    SessionHistoryMetadata.added_at,
                    SessionHistoryMetadata.updated_at,
                    SessionHistoryMetadata.last_viewed_at,
                    SessionHistoryMetadata.content_rating,
                    SessionHistoryMetadata.summary,
                    SessionHistoryMetadata.tagline,
                    SessionHistoryMetadata.rating,
                    SessionHistoryMetadata.duration,
                    SessionHistoryMetadata.guid,
                    SessionHistoryMetadata.directors,
                    SessionHistoryMetadata.writers,
                    SessionHistoryMetadata.actors,
                    SessionHistoryMetadata.genres,
                    SessionHistoryMetadata.studio,
                    SessionHistoryMetadata.labels,
                    SessionHistoryMediaInfo.container,
                    SessionHistoryMediaInfo.bitrate,
                    SessionHistoryMediaInfo.video_codec,
                    SessionHistoryMediaInfo.video_resolution,
                    SessionHistoryMediaInfo.video_full_resolution,
                    SessionHistoryMediaInfo.video_framerate,
                    SessionHistoryMediaInfo.audio_codec,
                    SessionHistoryMediaInfo.audio_channels,
                    SessionHistoryMetadata.live,
                    SessionHistoryMetadata.channel_call_sign,
                    SessionHistoryMetadata.channel_id,
                    SessionHistoryMetadata.channel_identifier,
                    SessionHistoryMetadata.channel_title,
                    SessionHistoryMetadata.channel_thumb,
                    SessionHistoryMetadata.channel_vcn,
                )
                .select_from(SessionHistoryMetadata)
                .join(SessionHistory, SessionHistoryMetadata.id == SessionHistory.id)
                .join(LibrarySection, SessionHistory.section_id == LibrarySection.section_id)
                .join(SessionHistoryMediaInfo, SessionHistoryMetadata.id == SessionHistoryMediaInfo.id)
                .where(where_cond)
                .order_by(SessionHistoryMetadata.id.desc())
                .limit(1)
            )
            try:
                with session_scope() as db_session:
                    result = queries.fetch_mappings(db_session, stmt)
            except Exception as e:
                logger.warn("Tautulli DataFactory :: Unable to execute database query for get_metadata_details: %s." % e)
                result = []
        else:
            result = []

        metadata_list = []

        for item in result:
            directors = item['directors'].split(';') if item['directors'] else []
            writers = item['writers'].split(';') if item['writers'] else []
            actors = item['actors'].split(';') if item['actors'] else []
            genres = item['genres'].split(';') if item['genres'] else []
            labels = item['labels'].split(';') if item['labels'] else []

            media_info = [{'container': item['container'],
                           'bitrate': item['bitrate'],
                           'video_codec': item['video_codec'],
                           'video_resolution': item['video_resolution'],
                           'video_full_resolution': item['video_full_resolution'],
                           'video_framerate': item['video_framerate'],
                           'audio_codec': item['audio_codec'],
                           'audio_channels': item['audio_channels'],
                           'channel_call_sign': item['channel_call_sign'],
                           'channel_id': item['channel_id'],
                           'channel_identifier': item['channel_identifier'],
                           'channel_title': item['channel_title'],
                           'channel_thumb': item['channel_thumb'],
                           'channel_vcn': item['channel_vcn']
                           }]

            metadata = {'media_type': item['media_type'],
                        'rating_key': item['rating_key'],
                        'parent_rating_key': item['parent_rating_key'],
                        'grandparent_rating_key': item['grandparent_rating_key'],
                        'grandparent_title': item['grandparent_title'],
                        'original_title': item['original_title'],
                        'parent_media_index': item['parent_media_index'],
                        'parent_title': item['parent_title'],
                        'media_index': item['media_index'],
                        'studio': item['studio'],
                        'title': item['title'],
                        'full_title': item['full_title'],
                        'content_rating': item['content_rating'],
                        'summary': item['summary'],
                        'tagline': item['tagline'],
                        'rating': item['rating'],
                        'duration': item['duration'],
                        'year': item['year'],
                        'thumb': item['thumb'],
                        'parent_thumb': item['parent_thumb'],
                        'grandparent_thumb': item['grandparent_thumb'],
                        'art': item['art'],
                        'originally_available_at': item['originally_available_at'],
                        'added_at': item['added_at'],
                        'updated_at': item['updated_at'],
                        'last_viewed_at': item['last_viewed_at'],
                        'guid': item['guid'],
                        'directors': directors,
                        'writers': writers,
                        'actors': actors,
                        'genres': genres,
                        'labels': labels,
                        'library_name': item['section_name'],
                        'section_id': item['section_id'],
                        'live': item['live'],
                        'media_info': media_info
                        }
            metadata_list.append(metadata)

        filtered_metadata_list = session.filter_session_info(metadata_list, filter_key='section_id')

        if filtered_metadata_list:
            return filtered_metadata_list[0]
        else:
            return []

    def get_total_duration(self, custom_where=None):
        try:
            total_duration = raw_pg.fetch_total_duration(custom_where=custom_where)
        except Exception as e:
            logger.warn("Tautulli DataFactory :: Unable to execute database query for get_total_duration: %s." % e)
            return None

        return total_duration

    def get_session_ip(self, session_key=''):
        ip_address = 'N/A'

        if session_key:
            try:
                session_key_int = int(session_key)
                stmt = select(Session.ip_address).where(Session.session_key == session_key_int)
                session_user_id = session.get_session_user_id()
                if session_user_id:
                    stmt = stmt.where(Session.user_id == helpers.cast_to_int(session_user_id))
                with session_scope() as db_session:
                    ip_address = queries.fetch_scalar(db_session, stmt, default='N/A')
            except Exception as e:
                logger.warn("Tautulli DataFactory :: Unable to execute database query for get_session_ip: %s." % e)
                return ip_address
        else:
            return ip_address

        return ip_address

    def get_img_info(self, img=None, rating_key=None, width=None, height=None,
                     opacity=None, background=None, blur=None, fallback=None,
                     order_by='', service=None):
        img_info = []

        if service == 'imgur':
            stmt = (
                select(
                    ImgurLookup.imgur_title.label('img_title'),
                    ImgurLookup.imgur_url.label('img_url'),
                )
                .select_from(ImgurLookup)
                .join(ImageHashLookup, ImgurLookup.img_hash == ImageHashLookup.img_hash)
            )
        elif service == 'cloudinary':
            stmt = (
                select(
                    CloudinaryLookup.cloudinary_title.label('img_title'),
                    CloudinaryLookup.cloudinary_url.label('img_url'),
                )
                .select_from(CloudinaryLookup)
                .join(ImageHashLookup, CloudinaryLookup.img_hash == ImageHashLookup.img_hash)
            )
        else:
            logger.warn("Tautulli DataFactory :: Unable to execute database query for get_img_info: "
                        "service not provided.")
            return img_info

        if img is not None:
            stmt = stmt.where(ImageHashLookup.img == img)
        if rating_key is not None:
            stmt = stmt.where(ImageHashLookup.rating_key == rating_key)
        if width is not None:
            stmt = stmt.where(ImageHashLookup.width == width)
        if height is not None:
            stmt = stmt.where(ImageHashLookup.height == height)
        if opacity is not None:
            stmt = stmt.where(ImageHashLookup.opacity == opacity)
        if background is not None:
            stmt = stmt.where(ImageHashLookup.background == background)
        if blur is not None:
            stmt = stmt.where(ImageHashLookup.blur == blur)
        if fallback is not None:
            stmt = stmt.where(ImageHashLookup.fallback == fallback)

        if order_by:
            order_column = getattr(ImageHashLookup, order_by, None)
            if order_column is None and service == 'imgur':
                order_column = getattr(ImgurLookup, order_by, None)
            if order_column is None and service == 'cloudinary':
                order_column = getattr(CloudinaryLookup, order_by, None)
            if order_column is not None:
                stmt = stmt.order_by(order_column.desc())

        try:
            with session_scope() as db_session:
                img_info = queries.fetch_mappings(db_session, stmt)
        except Exception as e:
            logger.warn("Tautulli DataFactory :: Unable to execute database query for get_img_info: %s." % e)

        return img_info

    def set_img_info(self, img_hash=None, img_title=None, img_url=None, delete_hash=None, service=None):
        if service == 'imgur':
            values = {'imgur_title': img_title,
                      'imgur_url': img_url,
                      'delete_hash': delete_hash}
            model = ImgurLookup
        elif service == 'cloudinary':
            values = {'cloudinary_title': img_title,
                      'cloudinary_url': img_url}
            model = CloudinaryLookup
        else:
            logger.warn("Tautulli DataFactory :: Unable to execute database query for set_img_info: "
                        "service not provided.")
            return

        keys = {'img_hash': img_hash}
        values = values or {}
        cleaned_keys = {key: value for key, value in keys.items() if value is not None}
        insert_values = {**values, **cleaned_keys}
        if not insert_values:
            return

        with session_scope() as db_session:
            if cleaned_keys:
                conditions = [getattr(model, key) == value for key, value in cleaned_keys.items()]
                result = db_session.execute(update(model).where(*conditions).values(**values))
                if result.rowcount and result.rowcount > 0:
                    return
            db_session.execute(insert(model).values(**insert_values))

    def delete_img_info(self, rating_key=None, service='', delete_all=False):
        if not delete_all:
            service = helpers.get_img_service()

        if not rating_key and not delete_all:
            logger.error("Tautulli DataFactory :: Unable to delete hosted images: rating_key not provided.")
            return False

        filters = []
        log_msg = ''
        if rating_key:
            filters.append(ImageHashLookup.rating_key == rating_key)
            log_msg = ' for rating_key %s' % rating_key

        if service.lower() == 'imgur':
            # Delete from Imgur
            stmt = (
                select(
                    ImgurLookup.imgur_title,
                    ImgurLookup.delete_hash,
                    ImageHashLookup.fallback,
                )
                .select_from(ImgurLookup)
                .join(ImageHashLookup, ImgurLookup.img_hash == ImageHashLookup.img_hash)
            )
            if filters:
                stmt = stmt.where(*filters)
            with session_scope() as db_session:
                results = queries.fetch_mappings(db_session, stmt)

            for imgur_info in results:
                if imgur_info['delete_hash']:
                    helpers.delete_from_imgur(delete_hash=imgur_info['delete_hash'],
                                              img_title=imgur_info['imgur_title'],
                                              fallback=imgur_info['fallback'])

            logger.info("Tautulli DataFactory :: Deleting Imgur info%s from the database."
                        % log_msg)
            delete_stmt = delete(ImgurLookup).where(
                ImgurLookup.img_hash.in_(
                    select(ImageHashLookup.img_hash).where(*filters)
                    if filters
                    else select(ImageHashLookup.img_hash)
                )
            )
            with session_scope() as db_session:
                db_session.execute(delete_stmt)

        elif service.lower() == 'cloudinary':
            # Delete from Cloudinary
            stmt = (
                select(
                    func.max(CloudinaryLookup.cloudinary_title).label('cloudinary_title'),
                    ImageHashLookup.rating_key,
                    func.max(ImageHashLookup.fallback).label('fallback'),
                )
                .select_from(CloudinaryLookup)
                .join(ImageHashLookup, CloudinaryLookup.img_hash == ImageHashLookup.img_hash)
                .group_by(ImageHashLookup.rating_key)
            )
            if filters:
                stmt = stmt.where(*filters)
            with session_scope() as db_session:
                results = queries.fetch_mappings(db_session, stmt)

            if delete_all:
                helpers.delete_from_cloudinary(delete_all=delete_all)
            else:
                for cloudinary_info in results:
                    helpers.delete_from_cloudinary(rating_key=cloudinary_info['rating_key'])

            logger.info("Tautulli DataFactory :: Deleting Cloudinary info%s from the database."
                        % log_msg)
            delete_stmt = delete(CloudinaryLookup).where(
                CloudinaryLookup.img_hash.in_(
                    select(ImageHashLookup.img_hash).where(*filters)
                    if filters
                    else select(ImageHashLookup.img_hash)
                )
            )
            with session_scope() as db_session:
                db_session.execute(delete_stmt)

        else:
            logger.error("Tautulli DataFactory :: Unable to delete hosted images: invalid service '%s' provided."
                         % service)

        return service

    def get_poster_info(self, rating_key='', metadata=None, service=None):
        poster_key = ''
        if str(rating_key).isdigit():
            poster_key = rating_key
        elif metadata:
            if metadata['media_type'] in ('movie', 'show', 'artist', 'collection'):
                poster_key = metadata['rating_key']
            elif metadata['media_type'] in ('season', 'album'):
                poster_key = metadata['rating_key']
            elif metadata['media_type'] in ('episode', 'track'):
                poster_key = metadata['parent_rating_key']

        poster_info = {}

        if poster_key:
            service = service or helpers.get_img_service()

            if service:
                img_info = self.get_img_info(rating_key=poster_key,
                                             order_by='height',
                                             fallback='poster',
                                             service=service)
                if img_info:
                    poster_info = {'poster_title': img_info[0]['img_title'],
                                   'poster_url': img_info[0]['img_url'],
                                   'img_service': service.capitalize()}

        return poster_info

    def get_lookup_info(self, rating_key='', metadata=None):
        lookup_key = ''
        if str(rating_key).isdigit():
            lookup_key = rating_key
        elif metadata:
            if metadata['media_type'] in ('movie', 'show', 'artist', 'album', 'track'):
                lookup_key = metadata['rating_key']
            elif metadata['media_type'] == 'season':
                lookup_key = metadata['parent_rating_key']
            elif metadata['media_type'] == 'episode':
                lookup_key = metadata['grandparent_rating_key']

        lookup_info = {'tvmaze_id': '',
                       'themoviedb_id': '',
                       'musizbrainz_id': ''}

        if lookup_key:
            try:
                lookup_key_int = helpers.cast_to_int(lookup_key)
                with session_scope() as db_session:
                    tvmaze_id = queries.fetch_scalar(
                        db_session,
                        select(TvmazeLookup.tvmaze_id).where(TvmazeLookup.rating_key == lookup_key_int),
                        default=None,
                    )
                    if tvmaze_id:
                        lookup_info['tvmaze_id'] = tvmaze_id

                    themoviedb_id = queries.fetch_scalar(
                        db_session,
                        select(TheMovieDbLookup.themoviedb_id).where(TheMovieDbLookup.rating_key == lookup_key_int),
                        default=None,
                    )
                    if themoviedb_id:
                        lookup_info['themoviedb_id'] = themoviedb_id

                    musicbrainz_id = queries.fetch_scalar(
                        db_session,
                        select(MusicbrainzLookup.musicbrainz_id).where(MusicbrainzLookup.rating_key == lookup_key_int),
                        default=None,
                    )
                    if musicbrainz_id:
                        lookup_info['musicbrainz_id'] = musicbrainz_id
            except Exception as e:
                logger.warn("Tautulli DataFactory :: Unable to execute database query for get_lookup_info: %s." % e)

        return lookup_info

    def delete_lookup_info(self, rating_key='', service='', delete_all=False):
        if not rating_key and not delete_all:
            logger.error("Tautulli DataFactory :: Unable to delete lookup info: rating_key not provided.")
            return False

        if rating_key:
            logger.info("Tautulli DataFactory :: Deleting lookup info for rating_key %s from the database."
                        % rating_key)
            rating_key_int = helpers.cast_to_int(rating_key)
            with session_scope() as db_session:
                result_themoviedb = db_session.execute(
                    delete(TheMovieDbLookup).where(TheMovieDbLookup.rating_key == rating_key_int)
                ).rowcount
                result_tvmaze = db_session.execute(
                    delete(TvmazeLookup).where(TvmazeLookup.rating_key == rating_key_int)
                ).rowcount
                result_musicbrainz = db_session.execute(
                    delete(MusicbrainzLookup).where(MusicbrainzLookup.rating_key == rating_key_int)
                ).rowcount
            return bool(result_themoviedb or result_tvmaze or result_musicbrainz)
        elif service and delete_all:
            if service.lower() in ('themoviedb', 'tvmaze', 'musicbrainz'):
                logger.info("Tautulli DataFactory :: Deleting all lookup info for '%s' from the database."
                            % service)
                with session_scope() as db_session:
                    if service.lower() == 'themoviedb':
                        result = db_session.execute(delete(TheMovieDbLookup)).rowcount
                    elif service.lower() == 'tvmaze':
                        result = db_session.execute(delete(TvmazeLookup)).rowcount
                    else:
                        result = db_session.execute(delete(MusicbrainzLookup)).rowcount
                return bool(result)
            else:
                logger.error("Tautulli DataFactory :: Unable to delete lookup info: invalid service '%s' provided."
                             % service)

    def get_search_query(self, rating_key=''):
        if rating_key:
            rating_key_int = helpers.cast_to_int(rating_key)
            stmt = (
                select(
                    SessionHistoryMetadata.rating_key,
                    SessionHistoryMetadata.parent_rating_key,
                    SessionHistoryMetadata.grandparent_rating_key,
                    SessionHistoryMetadata.title,
                    SessionHistoryMetadata.parent_title,
                    SessionHistoryMetadata.grandparent_title,
                    SessionHistoryMetadata.media_index,
                    SessionHistoryMetadata.parent_media_index,
                    SessionHistoryMetadata.year,
                    SessionHistoryMetadata.media_type,
                )
                .where(
                    or_(
                        SessionHistoryMetadata.rating_key == rating_key_int,
                        SessionHistoryMetadata.parent_rating_key == rating_key_int,
                        SessionHistoryMetadata.grandparent_rating_key == rating_key_int,
                    )
                )
                .limit(1)
            )
            try:
                with session_scope() as db_session:
                    result = queries.fetch_mapping(db_session, stmt, default={})
            except Exception as e:
                logger.warn("Tautulli DataFactory :: Unable to execute database query for get_search_query: %s." % e)
                result = {}
        else:
            result = {}

        query = {}
        query_string = None
        media_type = None

        if result:
            title = result['title']
            parent_title = result['parent_title']
            grandparent_title = result['grandparent_title']
            media_index = result['media_index']
            parent_media_index = result['parent_media_index']
            year = result['year']

            if str(result['rating_key']) == rating_key:
                query_string = result['title']
                media_type = result['media_type']

            elif str(result['parent_rating_key']) == rating_key:
                if result['media_type'] == 'episode':
                    query_string = result['grandparent_title']
                    media_type = 'season'
                elif result['media_type'] == 'track':
                    query_string = result['parent_title']
                    media_type = 'album'

            elif str(result['grandparent_rating_key']) == rating_key:
                if result['media_type'] == 'episode':
                    query_string = result['grandparent_title']
                    media_type = 'show'
                elif result['media_type'] == 'track':
                    query_string = result['grandparent_title']
                    media_type = 'artist'

        if query_string and media_type:
            query = {'query_string': query_string,
                     'title': title,
                     'parent_title': parent_title,
                     'grandparent_title': grandparent_title,
                     'media_index': media_index,
                     'parent_media_index': parent_media_index,
                     'year': year,
                     'media_type': media_type,
                     'rating_key': rating_key
                     }
        else:
            return None

        return query

    def get_rating_keys_list(self, rating_key='', media_type=''):
        if media_type == 'movie':
            key_list = {0: {'rating_key': int(rating_key)}}
            return key_list

        if media_type == 'artist' or media_type == 'album' or media_type == 'track':
            match_type = 'title'
        else:
            match_type = 'index'

        # Get the grandparent rating key
        try:
            rating_key_int = helpers.cast_to_int(rating_key)
            with session_scope() as db_session:
                stmt = (
                    select(SessionHistoryMetadata.grandparent_rating_key)
                    .where(
                        or_(
                            SessionHistoryMetadata.rating_key == rating_key_int,
                            SessionHistoryMetadata.parent_rating_key == rating_key_int,
                            SessionHistoryMetadata.grandparent_rating_key == rating_key_int,
                        )
                    )
                    .limit(1)
                )
                result = queries.fetch_mapping(db_session, stmt, default={})
                if not result:
                    return {}

                grandparent_rating_key = result['grandparent_rating_key']
                if grandparent_rating_key is None:
                    return {}

                def fetch_grouped(filter_column, filter_value, group_column):
                    if filter_value is None:
                        return []
                    grouped_stmt = (
                        select(
                            func.max(SessionHistoryMetadata.rating_key).label('rating_key'),
                            func.max(SessionHistoryMetadata.parent_rating_key).label('parent_rating_key'),
                            func.max(SessionHistoryMetadata.grandparent_rating_key).label('grandparent_rating_key'),
                            func.max(SessionHistoryMetadata.title).label('title'),
                            func.max(SessionHistoryMetadata.parent_title).label('parent_title'),
                            func.max(SessionHistoryMetadata.grandparent_title).label('grandparent_title'),
                            func.max(SessionHistoryMetadata.media_index).label('media_index'),
                            func.max(SessionHistoryMetadata.parent_media_index).label('parent_media_index'),
                        )
                        .where(filter_column == filter_value)
                        .group_by(group_column)
                        .order_by(group_column.desc())
                    )
                    return queries.fetch_mappings(db_session, grouped_stmt)

                grandparents = {}
                grandparent_rows = fetch_grouped(
                    SessionHistoryMetadata.grandparent_rating_key,
                    grandparent_rating_key,
                    SessionHistoryMetadata.grandparent_rating_key,
                )
                for grandparent_row in grandparent_rows:
                    parents = {}
                    parent_rows = fetch_grouped(
                        SessionHistoryMetadata.grandparent_rating_key,
                        grandparent_row['grandparent_rating_key'],
                        SessionHistoryMetadata.parent_rating_key,
                    )
                    for parent_row in parent_rows:
                        children = {}
                        child_rows = fetch_grouped(
                            SessionHistoryMetadata.parent_rating_key,
                            parent_row['parent_rating_key'],
                            SessionHistoryMetadata.rating_key,
                        )
                        for child_row in child_rows:
                            key = child_row['media_index'] if child_row['media_index'] else str(child_row['title']).lower()
                            children.update({key: {'rating_key': child_row['rating_key']}})

                        key = parent_row['parent_media_index'] if match_type == 'index' else str(parent_row['parent_title']).lower()
                        parents.update({key:
                                        {'rating_key': parent_row['parent_rating_key'],
                                         'children': children}
                                        })

                    key = 0 if match_type == 'index' else str(grandparent_row['grandparent_title']).lower()
                    grandparents.update({key:
                                         {'rating_key': grandparent_row['grandparent_rating_key'],
                                          'children': parents}
                                         })

                key_list = grandparents

                return key_list
        except Exception as e:
            logger.warn("Tautulli DataFactory :: Unable to execute database query for get_rating_keys_list: %s." % e)
            return {}

    def update_metadata(self, old_key_list='', new_key_list='', media_type='', single_update=False):
        pms_connect = pmsconnect.PmsConnect()

        # function to map rating keys pairs
        def get_pairs(old, new):
            pairs = {}
            for k, v in old.items():
                if k in new:
                    pairs.update({v['rating_key']: new[k]['rating_key']})
                    if 'children' in old[k]:
                        pairs.update(get_pairs(old[k]['children'], new[k]['children']))

            return pairs

        # map rating keys pairs
        mapping = {}
        if old_key_list and new_key_list:
            mapping = get_pairs(old_key_list, new_key_list)

        if mapping:
            logger.info("Tautulli DataFactory :: Updating metadata in the database.")

            global _UPDATE_METADATA_IDS
            if single_update:
                _UPDATE_METADATA_IDS = {
                    'grandparent_rating_key_ids': set(),
                    'parent_rating_key_ids': set(),
                    'rating_key_ids': set()
                }

            def _fetch_ids(column, old_value, id_cache):
                stmt = select(SessionHistory.id).where(column == old_value)
                if id_cache:
                    stmt = stmt.where(SessionHistory.id.notin_(id_cache))
                with session_scope() as db_session:
                    ids = db_session.execute(stmt).scalars().all()
                if ids:
                    id_cache.update(ids)
                return ids

            for old_key, new_key in mapping.items():
                metadata = pms_connect.get_metadata_details(new_key)

                if metadata:
                    logger.debug("Tautulli DataFactory :: Mapping for rating_key %s -> %s (%s)",
                                 old_key, new_key, metadata['media_type'])

                    if metadata['media_type'] == 'show' or metadata['media_type'] == 'artist':
                        # check grandparent_rating_key (2 tables)
                        ids = _fetch_ids(
                            SessionHistory.grandparent_rating_key,
                            old_key,
                            _UPDATE_METADATA_IDS['grandparent_rating_key_ids'],
                        )
                        if not ids:
                            continue

                        with session_scope() as db_session:
                            db_session.execute(
                                update(SessionHistory)
                                .where(SessionHistory.id.in_(ids))
                                .values(grandparent_rating_key=new_key)
                            )
                            db_session.execute(
                                update(SessionHistoryMetadata)
                                .where(SessionHistoryMetadata.id.in_(ids))
                                .values(grandparent_rating_key=new_key)
                            )

                    elif metadata['media_type'] == 'season' or metadata['media_type'] == 'album':
                        # check parent_rating_key (2 tables)
                        ids = _fetch_ids(
                            SessionHistory.parent_rating_key,
                            old_key,
                            _UPDATE_METADATA_IDS['parent_rating_key_ids'],
                        )
                        if not ids:
                            continue

                        with session_scope() as db_session:
                            db_session.execute(
                                update(SessionHistory)
                                .where(SessionHistory.id.in_(ids))
                                .values(parent_rating_key=new_key)
                            )
                            db_session.execute(
                                update(SessionHistoryMetadata)
                                .where(SessionHistoryMetadata.id.in_(ids))
                                .values(parent_rating_key=new_key)
                            )

                    else:
                        # check rating_key (2 tables)
                        ids = _fetch_ids(
                            SessionHistory.rating_key,
                            old_key,
                            _UPDATE_METADATA_IDS['rating_key_ids'],
                        )
                        if not ids:
                            continue

                        with session_scope() as db_session:
                            db_session.execute(
                                update(SessionHistory)
                                .where(SessionHistory.id.in_(ids))
                                .values(rating_key=new_key)
                            )
                            db_session.execute(
                                update(SessionHistoryMediaInfo)
                                .where(SessionHistoryMediaInfo.id.in_(ids))
                                .values(rating_key=new_key)
                            )

                        # update session_history_metadata table
                        self.update_metadata_details(old_key, new_key, metadata, ids)

            return 'Updated metadata in database.'
        else:
            return 'Unable to update metadata in database. No changes were made.'

    def update_metadata_details(self, old_rating_key='', new_rating_key='', metadata=None, ids=None):

        if metadata and ids:
            # Create full_title
            if metadata['media_type'] == 'episode':
                full_title = '%s - %s' % (metadata['grandparent_title'], metadata['title'])
            elif metadata['media_type'] == 'track':
                full_title = '%s - %s' % (metadata['title'],
                                          metadata['original_title'] or metadata['grandparent_title'])
            else:
                full_title = metadata['title']

            directors = ";".join(metadata['directors'])
            writers = ";".join(metadata['writers'])
            actors = ";".join(metadata['actors'])
            genres = ";".join(metadata['genres'])
            labels = ";".join(metadata['labels'])

            logger.debug("Tautulli DataFactory :: Updating metadata in the database for rating_key %s -> %s.",
                         old_rating_key, new_rating_key)

            metadata_values = {
                'rating_key': metadata['rating_key'],
                'parent_rating_key': metadata['parent_rating_key'],
                'grandparent_rating_key': metadata['grandparent_rating_key'],
                'title': metadata['title'],
                'parent_title': metadata['parent_title'],
                'grandparent_title': metadata['grandparent_title'],
                'original_title': metadata['original_title'],
                'full_title': full_title,
                'media_index': metadata['media_index'],
                'parent_media_index': metadata['parent_media_index'],
                'thumb': metadata['thumb'],
                'parent_thumb': metadata['parent_thumb'],
                'grandparent_thumb': metadata['grandparent_thumb'],
                'art': metadata['art'],
                'media_type': metadata['media_type'],
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
            }

            with session_scope() as db_session:
                db_session.execute(
                    update(SessionHistory)
                    .where(SessionHistory.id.in_(ids))
                    .values(section_id=metadata['section_id'])
                )
                db_session.execute(
                    update(SessionHistoryMetadata)
                    .where(SessionHistoryMetadata.id.in_(ids))
                    .values(**metadata_values)
                )

    def get_notification_log(self, kwargs=None):
        data_tables = datatables.DataTables()

        columns = ["notify_log.id",
                   "notify_log.timestamp",
                   "notify_log.session_key",
                   "notify_log.rating_key",
                   "notify_log.user_id",
                   "notify_log.user",
                   "notify_log.notifier_id",
                   "notify_log.agent_id",
                   "notify_log.agent_name",
                   "notify_log.notify_action",
                   "notify_log.subject_text",
                   "notify_log.body_text",
                   "notify_log.success"
                   ]
        try:
            query = data_tables.ssp_query(table_name='notify_log',
                                          columns=columns,
                                          custom_where=[],
                                          group_by=[],
                                          join_types=[],
                                          join_tables=[],
                                          join_evals=[],
                                          kwargs=kwargs)
        except Exception as e:
            logger.warn("Tautulli DataFactory :: Unable to execute database query for get_notification_log: %s." % e)
            return {'recordsFiltered': 0,
                    'recordsTotal': 0,
                    'draw': 0,
                    'data': []}

        notifications = query['result']

        rows = []
        for item in notifications:
            if item['body_text']:
                body_text = item['body_text'].replace('\r\n', '<br />').replace('\n', '<br />')
            else:
                body_text = ''

            row = {'id': item['id'],
                   'timestamp': item['timestamp'],
                   'session_key': item['session_key'],
                   'rating_key': item['rating_key'],
                   'user_id': item['user_id'],
                   'user': item['user'],
                   'notifier_id': item['notifier_id'],
                   'agent_id': item['agent_id'],
                   'agent_name': item['agent_name'],
                   'notify_action': item['notify_action'],
                   'subject_text': item['subject_text'],
                   'body_text': body_text,
                   'success': item['success']
                   }

            rows.append(row)

        dict = {'recordsFiltered': query['filteredCount'],
                'recordsTotal': query['totalCount'],
                'data': rows,
                'draw': query['draw']
                }

        return dict

    def delete_notification_log(self):
        try:
            logger.info("Tautulli DataFactory :: Clearing notification logs from database.")
            with session_scope() as db_session:
                db_session.execute(delete(NotifyLog))
            raw_pg.vacuum()
            return True
        except Exception as e:
            logger.warn("Tautulli DataFactory :: Unable to execute database query for delete_notification_log: %s." % e)
            return False

    def get_newsletter_log(self, kwargs=None):
        data_tables = datatables.DataTables()

        columns = ["newsletter_log.id",
                   "newsletter_log.timestamp",
                   "newsletter_log.newsletter_id",
                   "newsletter_log.agent_id",
                   "newsletter_log.agent_name",
                   "newsletter_log.notify_action",
                   "newsletter_log.subject_text",
                   "newsletter_log.body_text",
                   "newsletter_log.start_date",
                   "newsletter_log.end_date",
                   "newsletter_log.uuid",
                   "newsletter_log.success"
                   ]
        try:
            query = data_tables.ssp_query(table_name='newsletter_log',
                                          columns=columns,
                                          custom_where=[],
                                          group_by=[],
                                          join_types=[],
                                          join_tables=[],
                                          join_evals=[],
                                          kwargs=kwargs)
        except Exception as e:
            logger.warn("Tautulli DataFactory :: Unable to execute database query for get_newsletter_log: %s." % e)
            return {'recordsFiltered': 0,
                    'recordsTotal': 0,
                    'draw': 0,
                    'data': []}

        newsletters = query['result']

        rows = []
        for item in newsletters:
            row = {'id': item['id'],
                   'timestamp': item['timestamp'],
                   'newsletter_id': item['newsletter_id'],
                   'agent_id': item['agent_id'],
                   'agent_name': item['agent_name'],
                   'notify_action': item['notify_action'],
                   'subject_text': item['subject_text'],
                   'body_text': item['body_text'],
                   'start_date': item['start_date'],
                   'end_date': item['end_date'],
                   'uuid': item['uuid'],
                   'success': item['success']
                   }

            rows.append(row)

        dict = {'recordsFiltered': query['filteredCount'],
                'recordsTotal': query['totalCount'],
                'data': rows,
                'draw': query['draw']
                }

        return dict

    def delete_newsletter_log(self):
        try:
            logger.info("Tautulli DataFactory :: Clearing newsletter logs from database.")
            with session_scope() as db_session:
                db_session.execute(delete(NewsletterLog))
            raw_pg.vacuum()
            return True
        except Exception as e:
            logger.warn("Tautulli DataFactory :: Unable to execute database query for delete_newsletter_log: %s." % e)
            return False

    def get_user_devices(self, user_id='', history_only=True):
        if not user_id:
            return []

        try:
            user_id_int = int(user_id)
        except (TypeError, ValueError):
            return []

        try:
            if history_only:
                stmt = (
                    select(distinct(SessionHistory.machine_id))
                    .where(SessionHistory.user_id == user_id_int)
                )
            else:
                history_stmt = (
                    select(SessionHistory.machine_id)
                    .where(SessionHistory.user_id == user_id_int)
                )
                continued_stmt = (
                    select(SessionContinued.machine_id)
                    .where(SessionContinued.user_id == user_id_int)
                )
                union_stmt = history_stmt.union(continued_stmt).subquery()
                stmt = select(distinct(union_stmt.c.machine_id))

            with session_scope() as db_session:
                result = db_session.execute(stmt).scalars().all()
        except Exception as e:
            logger.warn("Tautulli DataFactory :: Unable to execute database query for get_user_devices: %s." % e)
            return []

        return [machine_id for machine_id in result if machine_id]

    def get_recently_added_item(self, rating_key=''):
        if not rating_key:
            return []

        try:
            rating_key_int = int(rating_key)
        except (TypeError, ValueError):
            return []

        try:
            stmt = select(RecentlyAdded.__table__).where(RecentlyAdded.rating_key == rating_key_int)
            with session_scope() as db_session:
                result = queries.fetch_mappings(db_session, stmt)
        except Exception as e:
            logger.warn("Tautulli DataFactory :: Unable to execute database query for get_recently_added_item: %s." % e)
            return []

        return result

    def set_recently_added_item(self, rating_key=''):
        pms_connect = pmsconnect.PmsConnect()
        metadata = pms_connect.get_metadata_details(rating_key)

        try:
            rating_key_int = int(metadata['rating_key'])
        except (TypeError, ValueError, KeyError):
            return False

        values = {'added_at': metadata['added_at'],
                  'section_id': metadata['section_id'],
                  'parent_rating_key': metadata['parent_rating_key'],
                  'grandparent_rating_key': metadata['grandparent_rating_key'],
                  'media_type': metadata['media_type'],
                  'media_info': json.dumps(metadata['media_info'])
                  }

        try:
            with session_scope() as db_session:
                stmt = (
                    update(RecentlyAdded)
                    .where(RecentlyAdded.rating_key == rating_key_int)
                    .values(**values)
                )
                result = db_session.execute(stmt)
                if not result.rowcount:
                    insert_values = {'rating_key': rating_key_int, **values}
                    db_session.execute(insert(RecentlyAdded).values(**insert_values))
        except Exception as e:
            logger.warn("Tautulli DataFactory :: Unable to execute database query for set_recently_added_item: %s." % e)
            return False

        return True
