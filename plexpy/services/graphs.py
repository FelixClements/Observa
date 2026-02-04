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

import datetime

import arrow
from sqlalchemy import Integer, and_, case, cast, distinct, func, or_, select

import plexpy
from plexpy.app import common
from plexpy.services import libraries
from plexpy.web import session
from plexpy.db import queries
from plexpy.db.models import SessionHistory, SessionHistoryMediaInfo, SessionHistoryMetadata, User
from plexpy.db.session import session_scope
from plexpy.db.queries import time as time_queries
from plexpy.util import helpers
from plexpy.util import logger


class Graphs(object):

    def __init__(self):
        pass

    def _timezone_name(self):
        timezone = plexpy.SYS_TIMEZONE or 'UTC'
        tz_name = getattr(timezone, 'zone', None) or str(timezone)
        return tz_name.replace("'", "''")

    def _localtime_expr(self, column=SessionHistory.started):
        tz_name = self._timezone_name()
        return time_queries.timezone(tz_name, time_queries.to_timestamp(column))

    def _local_date_expr(self, column=SessionHistory.started):
        return time_queries.to_char(self._localtime_expr(column), 'YYYY-MM-DD')

    def _local_month_expr(self, column=SessionHistory.started):
        return time_queries.to_char(self._localtime_expr(column), 'YYYY-MM')

    def _local_hour_expr(self, column=SessionHistory.started):
        return time_queries.to_char(self._localtime_expr(column), 'HH24')

    def _local_dow_expr(self, column=SessionHistory.started):
        return cast(time_queries.extract('dow', self._localtime_expr(column)), Integer)

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

    def get_total_plays_per_day(self, time_range='30', y_axis='plays', user_id=None, grouping=None):
        time_range = helpers.cast_to_int(time_range) or 30
        timestamp = helpers.timestamp() - time_range * 24 * 60 * 60
        user_filters = self._make_user_cond(user_id)

        if grouping is None:
            grouping = plexpy.CONFIG.GROUP_HISTORY_TABLES

        group_key = self._group_key_expr(grouping)
        duration_expr = self._duration_expr()
        date_played_expr = self._local_date_expr()

        try:
            if y_axis == 'plays':
                tv_count = func.count(distinct(case(
                    (and_(SessionHistory.media_type == 'episode', SessionHistoryMetadata.live == 0), group_key),
                    else_=None,
                )))
                movie_count = func.count(distinct(case(
                    (and_(SessionHistory.media_type == 'movie', SessionHistoryMetadata.live == 0), group_key),
                    else_=None,
                )))
                music_count = func.count(distinct(case(
                    (and_(SessionHistory.media_type == 'track', SessionHistoryMetadata.live == 0), group_key),
                    else_=None,
                )))
                live_count = func.count(distinct(case(
                    (SessionHistoryMetadata.live == 1, group_key),
                    else_=None,
                )))
            else:
                tv_count = func.sum(case(
                    (and_(SessionHistory.media_type == 'episode', SessionHistoryMetadata.live == 0), duration_expr),
                    else_=0,
                ))
                movie_count = func.sum(case(
                    (and_(SessionHistory.media_type == 'movie', SessionHistoryMetadata.live == 0), duration_expr),
                    else_=0,
                ))
                music_count = func.sum(case(
                    (and_(SessionHistory.media_type == 'track', SessionHistoryMetadata.live == 0), duration_expr),
                    else_=0,
                ))
                live_count = func.sum(case(
                    (SessionHistoryMetadata.live == 1, duration_expr),
                    else_=0,
                ))

            stmt = (
                select(
                    date_played_expr.label('date_played'),
                    tv_count.label('tv_count'),
                    movie_count.label('movie_count'),
                    music_count.label('music_count'),
                    live_count.label('live_count'),
                )
                .select_from(SessionHistory)
                .join(SessionHistoryMetadata, SessionHistoryMetadata.id == SessionHistory.id)
                .where(SessionHistory.stopped >= timestamp)
                .group_by(date_played_expr)
                .order_by(date_played_expr)
            )
            for cond in user_filters:
                stmt = stmt.where(cond)

            with session_scope() as db_session:
                result = queries.fetch_mappings(db_session, stmt)
        except Exception as e:
            logger.warn("Tautulli Graphs :: Unable to execute database query for get_total_plays_per_day: %s." % e)
            return None

        result_by_date_played = {item['date_played']: item for item in result}

        # create our date range as some days may not have any data
        # but we still want to display them
        base = datetime.date.today()
        date_list = [base - datetime.timedelta(days=x) for x in range(0, int(time_range))]

        categories = []
        series_1 = []
        series_2 = []
        series_3 = []
        series_4 = []

        for date_item in sorted(date_list):
            date_string = date_item.strftime('%Y-%m-%d')
            categories.append(date_string)

            result_date = result_by_date_played.get(date_string, {})

            series_1_value = result_date.get('tv_count', 0)
            series_2_value = result_date.get('movie_count', 0)
            series_3_value = result_date.get('music_count', 0)
            series_4_value = result_date.get('live_count', 0)

            series_1.append(series_1_value)
            series_2.append(series_2_value)
            series_3.append(series_3_value)
            series_4.append(series_4_value)

        series_1_output = {'name': 'TV',
                           'data': series_1}
        series_2_output = {'name': 'Movies',
                           'data': series_2}
        series_3_output = {'name': 'Music',
                           'data': series_3}
        series_4_output = {'name': 'Live TV',
                           'data': series_4}

        series_output = []
        if libraries.has_library_type('show'):
            series_output.append(series_1_output)
        if libraries.has_library_type('movie'):
            series_output.append(series_2_output)
        if libraries.has_library_type('artist'):
            series_output.append(series_3_output)
        if libraries.has_library_type('live'):
            series_output.append(series_4_output)

        if len(series_output) > 0:
            series_total = [sum(x) for x in zip(*[x['data'] for x in series_output])]
            series_total_output = {'name': 'Total',
                                   'data': series_total}
            series_output.append(series_total_output)

        output = {'categories': categories,
                  'series': series_output}
        return output

    def get_total_plays_per_dayofweek(self, time_range='30', y_axis='plays', user_id=None, grouping=None):
        time_range = helpers.cast_to_int(time_range) or 30
        timestamp = helpers.timestamp() - time_range * 24 * 60 * 60
        user_filters = self._make_user_cond(user_id)

        if grouping is None:
            grouping = plexpy.CONFIG.GROUP_HISTORY_TABLES

        group_key = self._group_key_expr(grouping)
        duration_expr = self._duration_expr()
        daynumber_expr = self._local_dow_expr()
        dayofweek_expr = case(
            (daynumber_expr == 0, 'Sunday'),
            (daynumber_expr == 1, 'Monday'),
            (daynumber_expr == 2, 'Tuesday'),
            (daynumber_expr == 3, 'Wednesday'),
            (daynumber_expr == 4, 'Thursday'),
            (daynumber_expr == 5, 'Friday'),
            else_='Saturday',
        )

        try:
            if y_axis == 'plays':
                tv_count = func.count(distinct(case(
                    (and_(SessionHistory.media_type == 'episode', SessionHistoryMetadata.live == 0), group_key),
                    else_=None,
                )))
                movie_count = func.count(distinct(case(
                    (and_(SessionHistory.media_type == 'movie', SessionHistoryMetadata.live == 0), group_key),
                    else_=None,
                )))
                music_count = func.count(distinct(case(
                    (and_(SessionHistory.media_type == 'track', SessionHistoryMetadata.live == 0), group_key),
                    else_=None,
                )))
                live_count = func.count(distinct(case(
                    (SessionHistoryMetadata.live == 1, group_key),
                    else_=None,
                )))
            else:
                tv_count = func.sum(case(
                    (and_(SessionHistory.media_type == 'episode', SessionHistoryMetadata.live == 0), duration_expr),
                    else_=0,
                ))
                movie_count = func.sum(case(
                    (and_(SessionHistory.media_type == 'movie', SessionHistoryMetadata.live == 0), duration_expr),
                    else_=0,
                ))
                music_count = func.sum(case(
                    (and_(SessionHistory.media_type == 'track', SessionHistoryMetadata.live == 0), duration_expr),
                    else_=0,
                ))
                live_count = func.sum(case(
                    (SessionHistoryMetadata.live == 1, duration_expr),
                    else_=0,
                ))

            stmt = (
                select(
                    daynumber_expr.label('daynumber'),
                    dayofweek_expr.label('dayofweek'),
                    tv_count.label('tv_count'),
                    movie_count.label('movie_count'),
                    music_count.label('music_count'),
                    live_count.label('live_count'),
                )
                .select_from(SessionHistory)
                .join(SessionHistoryMetadata, SessionHistoryMetadata.id == SessionHistory.id)
                .where(SessionHistory.stopped >= timestamp)
                .group_by(daynumber_expr, dayofweek_expr)
                .order_by(daynumber_expr)
            )
            for cond in user_filters:
                stmt = stmt.where(cond)

            with session_scope() as db_session:
                result = queries.fetch_mappings(db_session, stmt)
        except Exception as e:
            logger.warn("Tautulli Graphs :: Unable to execute database query for get_total_plays_per_dayofweek: %s." % e)
            return None

        result_by_dayofweek = {item['dayofweek']: item for item in result}

        if plexpy.CONFIG.WEEK_START_MONDAY:
            days_list = ['Monday', 'Tuesday', 'Wednesday',
                         'Thursday', 'Friday', 'Saturday', 'Sunday']
        else:
            days_list = ['Sunday', 'Monday', 'Tuesday', 'Wednesday',
                         'Thursday', 'Friday', 'Saturday']

        categories = []
        series_1 = []
        series_2 = []
        series_3 = []
        series_4 = []

        for day_item in days_list:
            categories.append(day_item)

            result_day = result_by_dayofweek.get(day_item, {})

            series_1_value = result_day.get('tv_count', 0)
            series_2_value = result_day.get('movie_count', 0)
            series_3_value = result_day.get('music_count', 0)
            series_4_value = result_day.get('live_count', 0)

            series_1.append(series_1_value)
            series_2.append(series_2_value)
            series_3.append(series_3_value)
            series_4.append(series_4_value)

        series_1_output = {'name': 'TV',
                           'data': series_1}
        series_2_output = {'name': 'Movies',
                           'data': series_2}
        series_3_output = {'name': 'Music',
                           'data': series_3}
        series_4_output = {'name': 'Live TV',
                           'data': series_4}

        series_output = []
        if libraries.has_library_type('show'):
            series_output.append(series_1_output)
        if libraries.has_library_type('movie'):
            series_output.append(series_2_output)
        if libraries.has_library_type('artist'):
            series_output.append(series_3_output)
        if libraries.has_library_type('live'):
            series_output.append(series_4_output)

        output = {'categories': categories,
                  'series': series_output}
        return output

    def get_total_plays_per_hourofday(self, time_range='30', y_axis='plays', user_id=None, grouping=None):
        time_range = helpers.cast_to_int(time_range) or 30
        timestamp = helpers.timestamp() - time_range * 24 * 60 * 60
        user_filters = self._make_user_cond(user_id)

        if grouping is None:
            grouping = plexpy.CONFIG.GROUP_HISTORY_TABLES

        group_key = self._group_key_expr(grouping)
        duration_expr = self._duration_expr()
        hourofday_expr = self._local_hour_expr()

        try:
            if y_axis == 'plays':
                tv_count = func.count(distinct(case(
                    (and_(SessionHistory.media_type == 'episode', SessionHistoryMetadata.live == 0), group_key),
                    else_=None,
                )))
                movie_count = func.count(distinct(case(
                    (and_(SessionHistory.media_type == 'movie', SessionHistoryMetadata.live == 0), group_key),
                    else_=None,
                )))
                music_count = func.count(distinct(case(
                    (and_(SessionHistory.media_type == 'track', SessionHistoryMetadata.live == 0), group_key),
                    else_=None,
                )))
                live_count = func.count(distinct(case(
                    (SessionHistoryMetadata.live == 1, group_key),
                    else_=None,
                )))
            else:
                tv_count = func.sum(case(
                    (and_(SessionHistory.media_type == 'episode', SessionHistoryMetadata.live == 0), duration_expr),
                    else_=0,
                ))
                movie_count = func.sum(case(
                    (and_(SessionHistory.media_type == 'movie', SessionHistoryMetadata.live == 0), duration_expr),
                    else_=0,
                ))
                music_count = func.sum(case(
                    (and_(SessionHistory.media_type == 'track', SessionHistoryMetadata.live == 0), duration_expr),
                    else_=0,
                ))
                live_count = func.sum(case(
                    (SessionHistoryMetadata.live == 1, duration_expr),
                    else_=0,
                ))

            stmt = (
                select(
                    hourofday_expr.label('hourofday'),
                    tv_count.label('tv_count'),
                    movie_count.label('movie_count'),
                    music_count.label('music_count'),
                    live_count.label('live_count'),
                )
                .select_from(SessionHistory)
                .join(SessionHistoryMetadata, SessionHistoryMetadata.id == SessionHistory.id)
                .where(SessionHistory.stopped >= timestamp)
                .group_by(hourofday_expr)
                .order_by(hourofday_expr)
            )
            for cond in user_filters:
                stmt = stmt.where(cond)

            with session_scope() as db_session:
                result = queries.fetch_mappings(db_session, stmt)
        except Exception as e:
            logger.warn("Tautulli Graphs :: Unable to execute database query for get_total_plays_per_hourofday: %s." % e)
            return None

        result_by_hourofday = {item['hourofday']: item for item in result}

        hours_list = ['00', '01', '02', '03', '04', '05',
                      '06', '07', '08', '09', '10', '11',
                      '12', '13', '14', '15', '16', '17',
                      '18', '19', '20', '21', '22', '23']

        categories = []
        series_1 = []
        series_2 = []
        series_3 = []
        series_4 = []

        for hour_item in hours_list:
            categories.append(hour_item)

            result_hour = result_by_hourofday.get(hour_item, {})

            series_1_value = result_hour.get('tv_count', 0)
            series_2_value = result_hour.get('movie_count', 0)
            series_3_value = result_hour.get('music_count', 0)
            series_4_value = result_hour.get('live_count', 0)

            series_1.append(series_1_value)
            series_2.append(series_2_value)
            series_3.append(series_3_value)
            series_4.append(series_4_value)

        series_1_output = {'name': 'TV',
                           'data': series_1}
        series_2_output = {'name': 'Movies',
                           'data': series_2}
        series_3_output = {'name': 'Music',
                           'data': series_3}
        series_4_output = {'name': 'Live TV',
                           'data': series_4}

        series_output = []
        if libraries.has_library_type('show'):
            series_output.append(series_1_output)
        if libraries.has_library_type('movie'):
            series_output.append(series_2_output)
        if libraries.has_library_type('artist'):
            series_output.append(series_3_output)
        if libraries.has_library_type('live'):
            series_output.append(series_4_output)

        output = {'categories': categories,
                  'series': series_output}
        return output

    def get_total_plays_per_month(self, time_range='12', y_axis='plays', user_id=None, grouping=None):
        time_range = helpers.cast_to_int(time_range) or 12
        timestamp = arrow.get(helpers.timestamp()).shift(months=-time_range).floor('month').timestamp()
        user_filters = self._make_user_cond(user_id)

        if grouping is None:
            grouping = plexpy.CONFIG.GROUP_HISTORY_TABLES

        group_key = self._group_key_expr(grouping)
        datestring_expr = self._local_month_expr()
        duration_expr = self._duration_expr()

        try:
            if y_axis == 'plays':
                metric_label = 'plays'
                metric_expr = func.count(distinct(group_key))
            else:
                metric_label = 'duration'
                metric_expr = func.sum(duration_expr)

            inner_stmt = (
                select(
                    datestring_expr.label('datestring'),
                    SessionHistory.media_type.label('media_type'),
                    SessionHistoryMetadata.live.label('live'),
                    metric_expr.label(metric_label),
                )
                .select_from(SessionHistory)
                .join(SessionHistoryMetadata, SessionHistoryMetadata.id == SessionHistory.id)
                .where(SessionHistory.stopped >= timestamp)
                .group_by(datestring_expr, SessionHistory.media_type, SessionHistoryMetadata.live)
            )
            for cond in user_filters:
                inner_stmt = inner_stmt.where(cond)
            inner = inner_stmt.subquery()
            metric_col = getattr(inner.c, metric_label)

            tv_count = func.sum(case(
                (and_(inner.c.media_type == 'episode', inner.c.live == 0), metric_col),
                else_=0,
            ))
            movie_count = func.sum(case(
                (and_(inner.c.media_type == 'movie', inner.c.live == 0), metric_col),
                else_=0,
            ))
            music_count = func.sum(case(
                (and_(inner.c.media_type == 'track', inner.c.live == 0), metric_col),
                else_=0,
            ))
            live_count = func.sum(case(
                (inner.c.live == 1, metric_col),
                else_=0,
            ))

            stmt = (
                select(
                    inner.c.datestring,
                    tv_count.label('tv_count'),
                    movie_count.label('movie_count'),
                    music_count.label('music_count'),
                    live_count.label('live_count'),
                )
                .group_by(inner.c.datestring)
                .order_by(inner.c.datestring)
            )
            with session_scope() as db_session:
                result = queries.fetch_mappings(db_session, stmt)
        except Exception as e:
            logger.warn("Tautulli Graphs :: Unable to execute database query for get_total_plays_per_month: %s." % e)
            return None

        result_by_datestring = {item['datestring']: item for item in result}

        # create our date range as some months may not have any data
        # but we still want to display them
        dt_today = datetime.date.today()
        dt = dt_today
        month_range = [dt]
        for n in range(int(time_range)-1):
            if not ((dt_today.month-n) % 12)-1:
                dt = datetime.date(dt.year-1, 12, 1)
            else:
                dt = datetime.date(dt.year, dt.month-1, 1)
            month_range.append(dt)

        categories = []
        series_1 = []
        series_2 = []
        series_3 = []
        series_4 = []

        for dt in sorted(month_range):
            date_string = dt.strftime('%Y-%m')
            categories.append(dt.strftime('%b %Y'))

            result_date = result_by_datestring.get(date_string, {})

            series_1_value = result_date.get('tv_count', 0)
            series_2_value = result_date.get('movie_count', 0)
            series_3_value = result_date.get('music_count', 0)
            series_4_value = result_date.get('live_count', 0)

            series_1.append(series_1_value)
            series_2.append(series_2_value)
            series_3.append(series_3_value)
            series_4.append(series_4_value)

        series_1_output = {'name': 'TV',
                           'data': series_1}
        series_2_output = {'name': 'Movies',
                           'data': series_2}
        series_3_output = {'name': 'Music',
                           'data': series_3}
        series_4_output = {'name': 'Live TV',
                           'data': series_4}

        series_output = []
        if libraries.has_library_type('show'):
            series_output.append(series_1_output)
        if libraries.has_library_type('movie'):
            series_output.append(series_2_output)
        if libraries.has_library_type('artist'):
            series_output.append(series_3_output)
        if libraries.has_library_type('live'):
            series_output.append(series_4_output)

        output = {'categories': categories,
                  'series': series_output}
        return output

    def get_total_plays_by_top_10_platforms(self, time_range='30', y_axis='plays', user_id=None, grouping=None):
        time_range = helpers.cast_to_int(time_range) or 30
        timestamp = helpers.timestamp() - time_range * 24 * 60 * 60
        user_filters = self._make_user_cond(user_id)

        if grouping is None:
            grouping = plexpy.CONFIG.GROUP_HISTORY_TABLES

        group_key = self._group_key_expr(grouping)
        duration_expr = self._duration_expr()

        try:
            if y_axis == 'plays':
                tv_count = func.count(distinct(case(
                    (and_(SessionHistory.media_type == 'episode', SessionHistoryMetadata.live == 0), group_key),
                    else_=None,
                )))
                movie_count = func.count(distinct(case(
                    (and_(SessionHistory.media_type == 'movie', SessionHistoryMetadata.live == 0), group_key),
                    else_=None,
                )))
                music_count = func.count(distinct(case(
                    (and_(SessionHistory.media_type == 'track', SessionHistoryMetadata.live == 0), group_key),
                    else_=None,
                )))
                live_count = func.count(distinct(case(
                    (SessionHistoryMetadata.live == 1, group_key),
                    else_=None,
                )))
                total_count = func.count(distinct(group_key))
                order_by = (total_count.desc(), SessionHistory.platform.asc())
                total_metric = total_count.label('total_count')
            else:
                tv_count = func.sum(case(
                    (and_(SessionHistory.media_type == 'episode', SessionHistoryMetadata.live == 0), duration_expr),
                    else_=0,
                ))
                movie_count = func.sum(case(
                    (and_(SessionHistory.media_type == 'movie', SessionHistoryMetadata.live == 0), duration_expr),
                    else_=0,
                ))
                music_count = func.sum(case(
                    (and_(SessionHistory.media_type == 'track', SessionHistoryMetadata.live == 0), duration_expr),
                    else_=0,
                ))
                live_count = func.sum(case(
                    (SessionHistoryMetadata.live == 1, duration_expr),
                    else_=0,
                ))
                total_metric = func.sum(duration_expr).label('total_duration')
                order_by = (total_metric.desc(),)

            stmt = (
                select(
                    SessionHistory.platform,
                    tv_count.label('tv_count'),
                    movie_count.label('movie_count'),
                    music_count.label('music_count'),
                    live_count.label('live_count'),
                    total_metric,
                )
                .select_from(SessionHistory)
                .join(SessionHistoryMetadata, SessionHistoryMetadata.id == SessionHistory.id)
                .where(SessionHistory.stopped >= timestamp)
                .group_by(SessionHistory.platform)
                .order_by(*order_by)
                .limit(10)
            )
            for cond in user_filters:
                stmt = stmt.where(cond)

            with session_scope() as db_session:
                result = queries.fetch_mappings(db_session, stmt)
        except Exception as e:
            logger.warn("Tautulli Graphs :: Unable to execute database query for get_total_plays_by_top_10_platforms: %s." % e)
            return None

        categories = []
        series_1 = []
        series_2 = []
        series_3 = []
        series_4 = []

        for item in result:
            categories.append(common.PLATFORM_NAME_OVERRIDES.get(item['platform'], item['platform']))

            series_1.append(item['tv_count'])
            series_2.append(item['movie_count'])
            series_3.append(item['music_count'])
            series_4.append(item['live_count'])

        series_1_output = {'name': 'TV',
                           'data': series_1}
        series_2_output = {'name': 'Movies',
                           'data': series_2}
        series_3_output = {'name': 'Music',
                           'data': series_3}
        series_4_output = {'name': 'Live TV',
                           'data': series_4}

        series_output = []
        if libraries.has_library_type('show'):
            series_output.append(series_1_output)
        if libraries.has_library_type('movie'):
            series_output.append(series_2_output)
        if libraries.has_library_type('artist'):
            series_output.append(series_3_output)
        if libraries.has_library_type('live'):
            series_output.append(series_4_output)

        output = {'categories': categories,
                  'series': series_output}
        return output

    def get_total_plays_by_top_10_users(self, time_range='30', y_axis='plays', user_id=None, grouping=None):
        time_range = helpers.cast_to_int(time_range) or 30
        timestamp = helpers.timestamp() - time_range * 24 * 60 * 60
        user_filters = self._make_user_cond(user_id)

        if grouping is None:
            grouping = plexpy.CONFIG.GROUP_HISTORY_TABLES

        group_key = self._group_key_expr(grouping)
        duration_expr = self._duration_expr()
        friendly_name_expr = case(
            (or_(User.friendly_name.is_(None), func.trim(User.friendly_name) == ''), User.username),
            else_=User.friendly_name,
        )

        try:
            if y_axis == 'plays':
                tv_count = func.count(distinct(case(
                    (and_(SessionHistory.media_type == 'episode', SessionHistoryMetadata.live == 0), group_key),
                    else_=None,
                )))
                movie_count = func.count(distinct(case(
                    (and_(SessionHistory.media_type == 'movie', SessionHistoryMetadata.live == 0), group_key),
                    else_=None,
                )))
                music_count = func.count(distinct(case(
                    (and_(SessionHistory.media_type == 'track', SessionHistoryMetadata.live == 0), group_key),
                    else_=None,
                )))
                live_count = func.count(distinct(case(
                    (SessionHistoryMetadata.live == 1, group_key),
                    else_=None,
                )))
                total_metric = func.count(distinct(group_key)).label('total_count')
                order_by = (total_metric.desc(),)
            else:
                tv_count = func.sum(case(
                    (and_(SessionHistory.media_type == 'episode', SessionHistoryMetadata.live == 0), duration_expr),
                    else_=0,
                ))
                movie_count = func.sum(case(
                    (and_(SessionHistory.media_type == 'movie', SessionHistoryMetadata.live == 0), duration_expr),
                    else_=0,
                ))
                music_count = func.sum(case(
                    (and_(SessionHistory.media_type == 'track', SessionHistoryMetadata.live == 0), duration_expr),
                    else_=0,
                ))
                live_count = func.sum(case(
                    (SessionHistoryMetadata.live == 1, duration_expr),
                    else_=0,
                ))
                total_metric = func.sum(duration_expr).label('total_duration')
                order_by = (total_metric.desc(),)

            stmt = (
                select(
                    User.user_id,
                    User.username,
                    friendly_name_expr.label('friendly_name'),
                    tv_count.label('tv_count'),
                    movie_count.label('movie_count'),
                    music_count.label('music_count'),
                    live_count.label('live_count'),
                    total_metric,
                )
                .select_from(SessionHistory)
                .join(SessionHistoryMetadata, SessionHistoryMetadata.id == SessionHistory.id)
                .join(User, User.user_id == SessionHistory.user_id)
                .where(SessionHistory.stopped >= timestamp)
                .group_by(User.user_id, User.username, User.friendly_name)
                .order_by(*order_by)
                .limit(10)
            )
            for cond in user_filters:
                stmt = stmt.where(cond)

            with session_scope() as db_session:
                result = queries.fetch_mappings(db_session, stmt)
        except Exception as e:
            logger.warn("Tautulli Graphs :: Unable to execute database query for get_total_plays_by_top_10_users: %s." % e)
            return None

        categories = []
        series_1 = []
        series_2 = []
        series_3 = []
        series_4 = []

        session_user_id = session.get_session_user_id()

        for item in result:
            if session_user_id:
                categories.append(item['username'] if str(item['user_id']) == session_user_id else 'Plex User')
            else:
                categories.append(item['friendly_name'])

            series_1.append(item['tv_count'])
            series_2.append(item['movie_count'])
            series_3.append(item['music_count'])
            series_4.append(item['live_count'])

        series_1_output = {'name': 'TV',
                           'data': series_1}
        series_2_output = {'name': 'Movies',
                           'data': series_2}
        series_3_output = {'name': 'Music',
                           'data': series_3}
        series_4_output = {'name': 'Live TV',
                           'data': series_4}

        series_output = []
        if libraries.has_library_type('show'):
            series_output.append(series_1_output)
        if libraries.has_library_type('movie'):
            series_output.append(series_2_output)
        if libraries.has_library_type('artist'):
            series_output.append(series_3_output)
        if libraries.has_library_type('live'):
            series_output.append(series_4_output)

        output = {'categories': categories,
                  'series': series_output}
        return output

    def get_total_plays_per_stream_type(self, time_range='30', y_axis='plays', user_id=None, grouping=None):
        time_range = helpers.cast_to_int(time_range) or 30
        timestamp = helpers.timestamp() - time_range * 24 * 60 * 60
        user_filters = self._make_user_cond(user_id)

        if grouping is None:
            grouping = plexpy.CONFIG.GROUP_HISTORY_TABLES

        group_key = self._group_key_expr(grouping)
        duration_expr = self._duration_expr()
        date_played_expr = self._local_date_expr()

        try:
            if y_axis == 'plays':
                dp_count = func.count(distinct(case(
                    (SessionHistoryMediaInfo.transcode_decision == 'direct play', group_key),
                    else_=None,
                )))
                ds_count = func.count(distinct(case(
                    (SessionHistoryMediaInfo.transcode_decision == 'copy', group_key),
                    else_=None,
                )))
                tc_count = func.count(distinct(case(
                    (SessionHistoryMediaInfo.transcode_decision == 'transcode', group_key),
                    else_=None,
                )))
            else:
                dp_count = func.sum(case(
                    (SessionHistoryMediaInfo.transcode_decision == 'direct play', duration_expr),
                    else_=0,
                ))
                ds_count = func.sum(case(
                    (SessionHistoryMediaInfo.transcode_decision == 'copy', duration_expr),
                    else_=0,
                ))
                tc_count = func.sum(case(
                    (SessionHistoryMediaInfo.transcode_decision == 'transcode', duration_expr),
                    else_=0,
                ))

            stmt = (
                select(
                    date_played_expr.label('date_played'),
                    dp_count.label('dp_count'),
                    ds_count.label('ds_count'),
                    tc_count.label('tc_count'),
                )
                .select_from(SessionHistory)
                .join(SessionHistoryMediaInfo, SessionHistoryMediaInfo.id == SessionHistory.id)
                .where(SessionHistory.stopped >= timestamp)
                .group_by(date_played_expr)
                .order_by(date_played_expr)
            )
            for cond in user_filters:
                stmt = stmt.where(cond)

            with session_scope() as db_session:
                result = queries.fetch_mappings(db_session, stmt)
        except Exception as e:
            logger.warn("Tautulli Graphs :: Unable to execute database query for get_total_plays_per_stream_type: %s." % e)
            return None

        result_by_date_played = {item['date_played']: item for item in result}

        # create our date range as some days may not have any data
        # but we still want to display them
        base = datetime.date.today()
        date_list = [base - datetime.timedelta(days=x) for x in range(0, int(time_range))]

        categories = []
        series_1 = []
        series_2 = []
        series_3 = []

        for date_item in sorted(date_list):
            date_string = date_item.strftime('%Y-%m-%d')
            categories.append(date_string)

            result_date = result_by_date_played.get(date_string, {})

            series_1_value = result_date.get('dp_count', 0)
            series_2_value = result_date.get('ds_count', 0)
            series_3_value = result_date.get('tc_count', 0)

            series_1.append(series_1_value)
            series_2.append(series_2_value)
            series_3.append(series_3_value)

        series_1_output = {'name': 'Direct Play',
                           'data': series_1}
        series_2_output = {'name': 'Direct Stream',
                           'data': series_2}
        series_3_output = {'name': 'Transcode',
                           'data': series_3}

        output = {'categories': categories,
                  'series': [series_1_output, series_2_output, series_3_output]}
        return output

    def get_total_concurrent_streams_per_stream_type(self, time_range='30', user_id=None):
        time_range = helpers.cast_to_int(time_range) or 30
        timestamp = helpers.timestamp() - time_range * 24 * 60 * 60

        user_filters = self._make_user_cond(user_id)
        date_played_expr = self._local_date_expr()
        
        def calc_most_concurrent(result):
            times = []
            for item in result:
                times.append({'time': str(item['started']) + 'B', 'count': 1})
                times.append({'time': str(item['stopped']) + 'A', 'count': -1})
            times = sorted(times, key=lambda k: k['time'])

            count = 0
            final_count = 0
            last_count = 0

            for d in times:
                if d['count'] == 1:
                    count += d['count']
                else:
                    if count >= last_count:
                        last_count = count
                        final_count = count
                    count += d['count']

            return final_count

        try:
            stmt = (
                select(
                    date_played_expr.label('date_played'),
                    SessionHistory.started,
                    SessionHistory.stopped,
                    SessionHistoryMediaInfo.transcode_decision,
                )
                .select_from(SessionHistory)
                .join(SessionHistoryMediaInfo, SessionHistoryMediaInfo.id == SessionHistory.id)
                .where(SessionHistory.stopped >= timestamp)
                .order_by(SessionHistory.started)
            )
            for cond in user_filters:
                stmt = stmt.where(cond)

            with session_scope() as db_session:
                result = queries.fetch_mappings(db_session, stmt)
        except Exception as e:
            logger.warn("Tautulli Graphs :: Unable to execute database query for get_total_plays_per_stream_type: %s." % e)
            return None

        result_by_date_and_decision = helpers.group_by_keys(result, ('date_played', 'transcode_decision'))
        result_by_date = helpers.group_by_keys(result, 'date_played')

        # create our date range as some days may not have any data
        # but we still want to display them
        base = datetime.date.today()
        date_list = [base - datetime.timedelta(days=x) for x in range(0, int(time_range))]

        categories = []
        series_1 = []
        series_2 = []
        series_3 = []
        series_4 = []

        for date_item in sorted(date_list):
            date_string = date_item.strftime('%Y-%m-%d')
            categories.append(date_string)

            series_1_value = calc_most_concurrent(
                result_by_date_and_decision.get((date_string, 'direct play'), [])
            )
            series_2_value = calc_most_concurrent(
                result_by_date_and_decision.get((date_string, 'copy'), [])
            )
            series_3_value = calc_most_concurrent(
                result_by_date_and_decision.get((date_string, 'transcode'), [])
            )
            series_4_value = calc_most_concurrent(
                result_by_date.get(date_string, [])
            )

            series_1.append(series_1_value)
            series_2.append(series_2_value)
            series_3.append(series_3_value)
            series_4.append(series_4_value)

        series_1_output = {'name': 'Direct Play',
                           'data': series_1}
        series_2_output = {'name': 'Direct Stream',
                           'data': series_2}
        series_3_output = {'name': 'Transcode',
                           'data': series_3}
        series_4_output = {'name': 'Max. Concurrent Streams',
                           'data': series_4}

        output = {'categories': categories,
                  'series': [series_1_output, series_2_output, series_3_output, series_4_output]}
        return output

    def get_total_plays_by_source_resolution(self, time_range='30', y_axis='plays', user_id=None, grouping=None):
        time_range = helpers.cast_to_int(time_range) or 30
        timestamp = helpers.timestamp() - time_range * 24 * 60 * 60
        user_filters = self._make_user_cond(user_id)

        if grouping is None:
            grouping = plexpy.CONFIG.GROUP_HISTORY_TABLES

        group_key = self._group_key_expr(grouping)
        duration_expr = self._duration_expr()

        try:
            if y_axis == 'plays':
                dp_count = func.count(distinct(case(
                    (SessionHistoryMediaInfo.transcode_decision == 'direct play', group_key),
                    else_=None,
                )))
                ds_count = func.count(distinct(case(
                    (SessionHistoryMediaInfo.transcode_decision == 'copy', group_key),
                    else_=None,
                )))
                tc_count = func.count(distinct(case(
                    (SessionHistoryMediaInfo.transcode_decision == 'transcode', group_key),
                    else_=None,
                )))
                total_metric = func.count(distinct(group_key)).label('total_count')
                order_by = (total_metric.desc(),)
            else:
                dp_count = func.sum(case(
                    (SessionHistoryMediaInfo.transcode_decision == 'direct play', duration_expr),
                    else_=0,
                ))
                ds_count = func.sum(case(
                    (SessionHistoryMediaInfo.transcode_decision == 'copy', duration_expr),
                    else_=0,
                ))
                tc_count = func.sum(case(
                    (SessionHistoryMediaInfo.transcode_decision == 'transcode', duration_expr),
                    else_=0,
                ))
                total_metric = func.sum(duration_expr).label('total_duration')
                order_by = (total_metric.desc(),)

            stmt = (
                select(
                    SessionHistoryMediaInfo.video_full_resolution.label('resolution'),
                    dp_count.label('dp_count'),
                    ds_count.label('ds_count'),
                    tc_count.label('tc_count'),
                    total_metric,
                )
                .select_from(SessionHistory)
                .join(SessionHistoryMediaInfo, SessionHistoryMediaInfo.id == SessionHistory.id)
                .where(
                    SessionHistory.stopped >= timestamp,
                    SessionHistory.media_type.in_(['movie', 'episode']),
                )
                .group_by(SessionHistoryMediaInfo.video_full_resolution)
                .order_by(*order_by)
                .limit(10)
            )
            for cond in user_filters:
                stmt = stmt.where(cond)

            with session_scope() as db_session:
                result = queries.fetch_mappings(db_session, stmt)
        except Exception as e:
            logger.warn("Tautulli Graphs :: Unable to execute database query for get_total_plays_by_source_resolution: %s." % e)
            return None

        categories = []
        series_1 = []
        series_2 = []
        series_3 = []

        for item in result:
            categories.append(item['resolution'])

            series_1.append(item['dp_count'])
            series_2.append(item['ds_count'])
            series_3.append(item['tc_count'])

        series_1_output = {'name': 'Direct Play',
                           'data': series_1}
        series_2_output = {'name': 'Direct Stream',
                           'data': series_2}
        series_3_output = {'name': 'Transcode',
                           'data': series_3}

        output = {'categories': categories,
                  'series': [series_1_output, series_2_output, series_3_output]}
        return output

    def get_total_plays_by_stream_resolution(self, time_range='30', y_axis='plays', user_id=None, grouping=None):
        time_range = helpers.cast_to_int(time_range) or 30
        timestamp = helpers.timestamp() - time_range * 24 * 60 * 60
        user_filters = self._make_user_cond(user_id)

        if grouping is None:
            grouping = plexpy.CONFIG.GROUP_HISTORY_TABLES

        group_key = self._group_key_expr(grouping)
        duration_expr = self._duration_expr()

        transcode_resolution = case(
            (SessionHistoryMediaInfo.transcode_height <= 360, 'SD'),
            (SessionHistoryMediaInfo.transcode_height <= 480, '480'),
            (SessionHistoryMediaInfo.transcode_height <= 576, '576'),
            (SessionHistoryMediaInfo.transcode_height <= 720, '720'),
            (SessionHistoryMediaInfo.transcode_height <= 1080, '1080'),
            (SessionHistoryMediaInfo.transcode_height <= 1440, 'QHD'),
            (SessionHistoryMediaInfo.transcode_height <= 2160, '4k'),
            else_='unknown',
        )
        resolved_transcode = case(
            (SessionHistoryMediaInfo.video_decision == 'transcode', transcode_resolution),
            else_=SessionHistoryMediaInfo.video_full_resolution,
        )
        resolution_expr = case(
            (SessionHistoryMediaInfo.stream_video_full_resolution.is_(None), resolved_transcode),
            else_=SessionHistoryMediaInfo.stream_video_full_resolution,
        )

        try:
            if y_axis == 'plays':
                dp_count = func.count(distinct(case(
                    (SessionHistoryMediaInfo.transcode_decision == 'direct play', group_key),
                    else_=None,
                )))
                ds_count = func.count(distinct(case(
                    (SessionHistoryMediaInfo.transcode_decision == 'copy', group_key),
                    else_=None,
                )))
                tc_count = func.count(distinct(case(
                    (SessionHistoryMediaInfo.transcode_decision == 'transcode', group_key),
                    else_=None,
                )))
                total_metric = func.count(distinct(group_key)).label('total_count')
                order_by = (total_metric.desc(),)
            else:
                dp_count = func.sum(case(
                    (SessionHistoryMediaInfo.transcode_decision == 'direct play', duration_expr),
                    else_=0,
                ))
                ds_count = func.sum(case(
                    (SessionHistoryMediaInfo.transcode_decision == 'copy', duration_expr),
                    else_=0,
                ))
                tc_count = func.sum(case(
                    (SessionHistoryMediaInfo.transcode_decision == 'transcode', duration_expr),
                    else_=0,
                ))
                total_metric = func.sum(duration_expr).label('total_duration')
                order_by = (total_metric.desc(),)

            stmt = (
                select(
                    resolution_expr.label('resolution'),
                    dp_count.label('dp_count'),
                    ds_count.label('ds_count'),
                    tc_count.label('tc_count'),
                    total_metric,
                )
                .select_from(SessionHistory)
                .join(SessionHistoryMediaInfo, SessionHistoryMediaInfo.id == SessionHistory.id)
                .where(
                    SessionHistory.stopped >= timestamp,
                    SessionHistory.media_type.in_(['movie', 'episode']),
                )
                .group_by(resolution_expr)
                .order_by(*order_by)
                .limit(10)
            )
            for cond in user_filters:
                stmt = stmt.where(cond)

            with session_scope() as db_session:
                result = queries.fetch_mappings(db_session, stmt)
        except Exception as e:
            logger.warn("Tautulli Graphs :: Unable to execute database query for get_total_plays_by_stream_resolution: %s." % e)
            return None

        categories = []
        series_1 = []
        series_2 = []
        series_3 = []

        for item in result:
            categories.append(item['resolution'])

            series_1.append(item['dp_count'])
            series_2.append(item['ds_count'])
            series_3.append(item['tc_count'])

        series_1_output = {'name': 'Direct Play',
                           'data': series_1}
        series_2_output = {'name': 'Direct Stream',
                           'data': series_2}
        series_3_output = {'name': 'Transcode',
                           'data': series_3}

        output = {'categories': categories,
                  'series': [series_1_output, series_2_output, series_3_output]}
        return output

    def get_stream_type_by_top_10_platforms(self, time_range='30', y_axis='plays', user_id=None, grouping=None):
        time_range = helpers.cast_to_int(time_range) or 30
        timestamp = helpers.timestamp() - time_range * 24 * 60 * 60
        user_filters = self._make_user_cond(user_id)

        if grouping is None:
            grouping = plexpy.CONFIG.GROUP_HISTORY_TABLES

        group_key = self._group_key_expr(grouping)
        duration_expr = self._duration_expr()

        try:
            if y_axis == 'plays':
                dp_count = func.count(distinct(case(
                    (SessionHistoryMediaInfo.transcode_decision == 'direct play', group_key),
                    else_=None,
                )))
                ds_count = func.count(distinct(case(
                    (SessionHistoryMediaInfo.transcode_decision == 'copy', group_key),
                    else_=None,
                )))
                tc_count = func.count(distinct(case(
                    (SessionHistoryMediaInfo.transcode_decision == 'transcode', group_key),
                    else_=None,
                )))
                total_metric = func.count(distinct(group_key)).label('total_count')
                order_by = (total_metric.desc(),)
            else:
                dp_count = func.sum(case(
                    (SessionHistoryMediaInfo.transcode_decision == 'direct play', duration_expr),
                    else_=0,
                ))
                ds_count = func.sum(case(
                    (SessionHistoryMediaInfo.transcode_decision == 'copy', duration_expr),
                    else_=0,
                ))
                tc_count = func.sum(case(
                    (SessionHistoryMediaInfo.transcode_decision == 'transcode', duration_expr),
                    else_=0,
                ))
                total_metric = func.sum(duration_expr).label('total_duration')
                order_by = (total_metric.desc(),)

            stmt = (
                select(
                    SessionHistory.platform,
                    dp_count.label('dp_count'),
                    ds_count.label('ds_count'),
                    tc_count.label('tc_count'),
                    total_metric,
                )
                .select_from(SessionHistory)
                .join(SessionHistoryMediaInfo, SessionHistoryMediaInfo.id == SessionHistory.id)
                .where(SessionHistory.stopped >= timestamp)
                .group_by(SessionHistory.platform)
                .order_by(*order_by)
                .limit(10)
            )
            for cond in user_filters:
                stmt = stmt.where(cond)

            with session_scope() as db_session:
                result = queries.fetch_mappings(db_session, stmt)
        except Exception as e:
            logger.warn("Tautulli Graphs :: Unable to execute database query for get_stream_type_by_top_10_platforms: %s." % e)
            return None

        categories = []
        series_1 = []
        series_2 = []
        series_3 = []

        for item in result:
            categories.append(common.PLATFORM_NAME_OVERRIDES.get(item['platform'], item['platform']))

            series_1.append(item['dp_count'])
            series_2.append(item['ds_count'])
            series_3.append(item['tc_count'])

        series_1_output = {'name': 'Direct Play',
                           'data': series_1}
        series_2_output = {'name': 'Direct Stream',
                           'data': series_2}
        series_3_output = {'name': 'Transcode',
                           'data': series_3}

        output = {'categories': categories,
                  'series': [series_1_output, series_2_output, series_3_output]}

        return output

    def get_stream_type_by_top_10_users(self, time_range='30', y_axis='plays', user_id=None, grouping=None):
        time_range = helpers.cast_to_int(time_range) or 30
        timestamp = helpers.timestamp() - time_range * 24 * 60 * 60
        user_filters = self._make_user_cond(user_id)

        if grouping is None:
            grouping = plexpy.CONFIG.GROUP_HISTORY_TABLES

        group_key = self._group_key_expr(grouping)
        duration_expr = self._duration_expr()
        friendly_name_expr = case(
            (or_(User.friendly_name.is_(None), func.trim(User.friendly_name) == ''), User.username),
            else_=User.friendly_name,
        )

        try:
            if y_axis == 'plays':
                dp_count = func.count(distinct(case(
                    (SessionHistoryMediaInfo.transcode_decision == 'direct play', group_key),
                    else_=None,
                )))
                ds_count = func.count(distinct(case(
                    (SessionHistoryMediaInfo.transcode_decision == 'copy', group_key),
                    else_=None,
                )))
                tc_count = func.count(distinct(case(
                    (SessionHistoryMediaInfo.transcode_decision == 'transcode', group_key),
                    else_=None,
                )))
                total_metric = func.count(distinct(group_key)).label('total_count')
                order_by = (total_metric.desc(),)
            else:
                dp_count = func.sum(case(
                    (SessionHistoryMediaInfo.transcode_decision == 'direct play', duration_expr),
                    else_=0,
                ))
                ds_count = func.sum(case(
                    (SessionHistoryMediaInfo.transcode_decision == 'copy', duration_expr),
                    else_=0,
                ))
                tc_count = func.sum(case(
                    (SessionHistoryMediaInfo.transcode_decision == 'transcode', duration_expr),
                    else_=0,
                ))
                total_metric = func.sum(duration_expr).label('total_duration')
                order_by = (total_metric.desc(),)

            stmt = (
                select(
                    User.user_id,
                    User.username,
                    friendly_name_expr.label('friendly_name'),
                    dp_count.label('dp_count'),
                    ds_count.label('ds_count'),
                    tc_count.label('tc_count'),
                    total_metric,
                )
                .select_from(SessionHistory)
                .join(SessionHistoryMediaInfo, SessionHistoryMediaInfo.id == SessionHistory.id)
                .join(User, User.user_id == SessionHistory.user_id)
                .where(SessionHistory.stopped >= timestamp)
                .group_by(User.user_id, User.username, User.friendly_name)
                .order_by(*order_by)
                .limit(10)
            )
            for cond in user_filters:
                stmt = stmt.where(cond)

            with session_scope() as db_session:
                result = queries.fetch_mappings(db_session, stmt)
        except Exception as e:
            logger.warn("Tautulli Graphs :: Unable to execute database query for get_stream_type_by_top_10_users: %s." % e)
            return None

        categories = []
        series_1 = []
        series_2 = []
        series_3 = []

        session_user_id = session.get_session_user_id()

        for item in result:
            if session_user_id:
                categories.append(item['username'] if str(item['user_id']) == session_user_id else 'Plex User')
            else:
                categories.append(item['friendly_name'])

            series_1.append(item['dp_count'])
            series_2.append(item['ds_count'])
            series_3.append(item['tc_count'])

        series_1_output = {'name': 'Direct Play',
                           'data': series_1}
        series_2_output = {'name': 'Direct Stream',
                           'data': series_2}
        series_3_output = {'name': 'Transcode',
                           'data': series_3}

        output = {'categories': categories,
                  'series': [series_1_output, series_2_output, series_3_output]}

        return output

    def _make_user_cond(self, user_id):
        """
        Expects user_id to be a comma-separated list of ints.
        Returns a list of SQLAlchemy filter expressions.
        """
        user_filters = []

        session_user_id = session.get_session_user_id()
        if session_user_id and user_id and user_id != str(session_user_id):
            user_filters.append(SessionHistory.user_id == helpers.cast_to_int(session_user_id))
        elif user_id:
            user_ids = helpers.split_strip(user_id)
            if all(id.isdigit() for id in user_ids):
                user_filters.append(SessionHistory.user_id.in_(list(map(helpers.cast_to_int, user_ids))))
        return user_filters
