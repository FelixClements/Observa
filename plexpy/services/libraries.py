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
import os

from sqlalchemy import case, delete, distinct, func, insert, lateral, literal, or_, select, true, update
from sqlalchemy.orm import aliased

import plexpy
from plexpy.app import common
from plexpy.db import datatables
from plexpy.db import cleanup
from plexpy.db import queries
from plexpy.db.models import LibrarySection, SessionHistory, SessionHistoryMetadata, User
from plexpy.db.session import session_scope
from plexpy.integrations import pmsconnect
from plexpy.services import users
from plexpy.web import session
from plexpy.integrations import plextv
from plexpy.integrations.plex import Plex
from plexpy.util import helpers
from plexpy.util import logger


def refresh_libraries():
    logger.info("Tautulli Libraries :: Requesting libraries list refresh...")

    server_id = plexpy.CONFIG.PMS_IDENTIFIER
    if not server_id:
        logger.error("Tautulli Libraries :: No PMS identifier, cannot refresh libraries. Verify server in settings.")
        return

    library_sections = pmsconnect.PmsConnect().get_library_details()

    if library_sections:
        library_keys = []
        new_keys = []

        # Keep track of section_id to update is_active status
        section_ids = [common.LIVE_TV_SECTION_ID]  # Live TV library always considered active

        with session_scope() as db_session:
            for section in library_sections:
                section_id = helpers.cast_to_int(section['section_id'])
                section_ids.append(section_id)

                section_values = {'server_id': server_id,
                                  'section_id': section_id,
                                  'section_name': section['section_name'],
                                  'section_type': section['section_type'],
                                  'agent': section['agent'],
                                  'thumb': section['thumb'],
                                  'art': section['art'],
                                  'count': section['count'],
                                  'parent_count': section.get('parent_count', None),
                                  'child_count': section.get('child_count', None),
                                  'is_active': section['is_active']
                                  }

                stmt = (
                    update(LibrarySection)
                    .where(
                        LibrarySection.server_id == server_id,
                        LibrarySection.section_id == section_id,
                    )
                    .values(**section_values)
                )
                update_result = db_session.execute(stmt)
                if not update_result.rowcount or update_result.rowcount == 0:
                    stmt = insert(LibrarySection).values(**section_values).returning(LibrarySection.id)
                    inserted_id = db_session.execute(stmt).scalar_one_or_none()
                    if inserted_id is not None:
                        new_keys.append(section['section_id'])

                library_keys.append(section['section_id'])

        add_live_tv_library(refresh=True)

        with session_scope() as db_session:
            stmt = (
                update(LibrarySection)
                .where(
                    or_(
                        LibrarySection.server_id != plexpy.CONFIG.PMS_IDENTIFIER,
                        LibrarySection.section_id.notin_(section_ids),
                    )
                )
                .values(is_active=0)
            )
            db_session.execute(stmt)

        new_keys = plexpy.CONFIG.HOME_LIBRARY_CARDS + new_keys
        plexpy.CONFIG.__setattr__('HOME_LIBRARY_CARDS', new_keys)
        plexpy.CONFIG.write()

        logger.info("Tautulli Libraries :: Libraries list refreshed.")
        return True
    else:
        logger.warn("Tautulli Libraries :: Unable to refresh libraries list.")
        return False


def add_live_tv_library(refresh=False):
    with session_scope() as db_session:
        stmt = (
            select(LibrarySection.id)
            .where(
                LibrarySection.section_id == common.LIVE_TV_SECTION_ID,
                LibrarySection.server_id == plexpy.CONFIG.PMS_IDENTIFIER,
            )
            .limit(1)
        )
        result = db_session.execute(stmt).scalar_one_or_none()

        if result and not refresh or not result and refresh:
            return

        if not refresh:
            logger.info("Tautulli Libraries :: Adding Live TV library to the database.")

        section_values = {'server_id': plexpy.CONFIG.PMS_IDENTIFIER,
                          'section_id': common.LIVE_TV_SECTION_ID,
                          'section_name': common.LIVE_TV_SECTION_NAME,
                          'section_type': 'live',
                          'thumb': common.DEFAULT_LIVE_TV_THUMB,
                          'art': common.DEFAULT_LIVE_TV_ART_FULL,
                          'is_active': 1
                          }

        stmt = (
            update(LibrarySection)
            .where(
                LibrarySection.server_id == plexpy.CONFIG.PMS_IDENTIFIER,
                LibrarySection.section_id == common.LIVE_TV_SECTION_ID,
            )
            .values(**section_values)
        )
        update_result = db_session.execute(stmt)
        if not update_result.rowcount or update_result.rowcount == 0:
            db_session.execute(insert(LibrarySection).values(**section_values))


def has_library_type(section_type):
    with session_scope() as db_session:
        stmt = (
            select(LibrarySection.id)
            .where(
                LibrarySection.section_type == section_type,
                LibrarySection.deleted_section == 0,
            )
            .limit(1)
        )
        result = db_session.execute(stmt).scalar_one_or_none()
    return bool(result)


def get_collections(section_id=None):
    plex = Plex(token=session.get_session_user_token())
    library = plex.get_library(section_id)

    if library.type not in ('movie', 'show', 'artist'):
        return []

    collections = library.collections()

    collections_list = []
    for collection in collections:
        collection._autoReload = False

        collection_mode = collection.collectionMode
        if collection_mode is None:
            collection_mode = -1

        collection_sort = collection.collectionSort
        if collection_sort is None:
            collection_sort = 0

        collection_dict = {
            'addedAt': helpers.datetime_to_iso(collection.addedAt),
            'art': collection.art,
            'childCount': collection.childCount,
            'collectionMode': collection_mode,
            'collectionPublished': collection.collectionPublished,
            'collectionSort': collection_sort,
            'contentRating': collection.contentRating,
            'guid': collection.guid,
            'librarySectionID': collection.librarySectionID,
            'librarySectionTitle': collection.librarySectionTitle,
            'maxYear': collection.maxYear,
            'minYear': collection.minYear,
            'ratingKey': collection.ratingKey,
            'smart': collection.smart,
            'subtype': collection.subtype,
            'summary': collection.summary,
            'thumb': collection.thumb,
            'title': collection.title,
            'titleSort': collection.titleSort or collection.title,
            'type': collection.type,
            'updatedAt': helpers.datetime_to_iso(collection.updatedAt)
        }
        collections_list.append(collection_dict)

    return collections_list


def get_collections_list(section_id=None, **kwargs):
    if not section_id:
        default_return = {'recordsFiltered': 0,
                          'recordsTotal': 0,
                          'draw': 0,
                          'data': []}
        return default_return

    collections = get_collections(section_id=section_id)

    # Get datatables JSON data
    json_data = helpers.process_json_kwargs(json_kwargs=kwargs['json_data'])

    search_cols = ['title']

    sort_keys = {
        'collectionMode': {
            -1: 'Library Default',
            0: 'Hide collection',
            1: 'Hide items in this collection',
            2: 'Show this collection and its items'
        },
        'collectionSort': {
            0: 'Release date',
            1: 'Alphabetical',
            2: 'Custom'
        }
    }

    results = helpers.process_datatable_rows(
        collections, json_data, default_sort='titleSort',
        search_cols=search_cols, sort_keys=sort_keys)

    data = {
        'recordsFiltered': results['filtered_count'],
        'recordsTotal': results['total_count'],
        'data': results['results'],
        'draw': int(json_data['draw'])
    }

    return data


def get_playlists(section_id=None, user_id=None):
    if user_id and not session.get_session_user_id():
        user_tokens = users.Users().get_tokens(user_id=user_id)
        plex_token = user_tokens['server_token']
    else:
        plex_token = session.get_session_user_token()

    if not plex_token:
        return []

    plex = Plex(token=plex_token)

    if user_id:
        playlists = plex.PlexServer.playlists()
    else:
        library = plex.get_library(section_id)
        playlists = library.playlists()

    playlists_list = []
    for playlist in playlists:
        playlist._autoReload = False

        playlist_dict = {
            'addedAt': helpers.datetime_to_iso(playlist.addedAt),
            'composite': playlist.composite,
            'duration': playlist.duration,
            'guid': playlist.guid,
            'leafCount': playlist.leafCount,
            'librarySectionID': section_id,
            'playlistType': playlist.playlistType,
            'ratingKey': playlist.ratingKey,
            'smart': playlist.smart,
            'summary': playlist.summary,
            'title': playlist.title,
            'type': playlist.type,
            'updatedAt': helpers.datetime_to_iso(playlist.updatedAt),
            'userID': user_id
        }
        playlists_list.append(playlist_dict)

    return playlists_list


def get_playlists_list(section_id=None, user_id=None, **kwargs):
    if not section_id and not user_id:
        default_return = {'recordsFiltered': 0,
                          'recordsTotal': 0,
                          'draw': 0,
                          'data': []}
        return default_return

    playlists = get_playlists(section_id=section_id, user_id=user_id)

    # Get datatables JSON data
    json_data = helpers.process_json_kwargs(json_kwargs=kwargs['json_data'])

    results = helpers.process_datatable_rows(
        playlists, json_data, default_sort='title')

    data = {
        'recordsFiltered': results['filtered_count'],
        'recordsTotal': results['total_count'],
        'data': results['results'],
        'draw': int(json_data['draw'])
    }

    return data


class Libraries(object):

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

        filters = [LibrarySection.deleted_section == 0]
        shared_libraries = session.get_session_shared_libraries()
        if shared_libraries:
            filters.append(LibrarySection.section_id.in_(shared_libraries))

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
            .where(SessionHistory.section_id == LibrarySection.section_id)
            .lateral()
        )

        last_sh = (
            select(
                SessionHistory.id.label('id'),
                SessionHistory.rating_key.label('rating_key'),
                SessionHistory.started.label('started'),
            )
            .where(SessionHistory.section_id == LibrarySection.section_id)
            .order_by(SessionHistory.started.desc(), SessionHistory.id.desc())
            .limit(1)
            .lateral()
        )

        stmt = (
            select(
                LibrarySection.id.label('row_id'),
                LibrarySection.server_id,
                LibrarySection.section_id,
                LibrarySection.section_name,
                LibrarySection.section_type,
                LibrarySection.count,
                LibrarySection.parent_count,
                LibrarySection.child_count,
                LibrarySection.thumb.label('library_thumb'),
                LibrarySection.custom_thumb_url.label('custom_thumb'),
                LibrarySection.art.label('library_art'),
                LibrarySection.custom_art_url.label('custom_art'),
                func.coalesce(sh_stats.c.plays, 0).label('plays'),
                func.coalesce(sh_stats.c.duration, 0).label('duration'),
                last_sh.c.started.label('last_accessed'),
                last_sh.c.id.label('history_row_id'),
                SessionHistoryMetadata.full_title.label('last_played'),
                last_sh.c.rating_key,
                SessionHistoryMetadata.media_type,
                SessionHistoryMetadata.thumb,
                SessionHistoryMetadata.parent_thumb,
                SessionHistoryMetadata.grandparent_thumb,
                SessionHistoryMetadata.parent_title,
                SessionHistoryMetadata.year,
                SessionHistoryMetadata.media_index,
                SessionHistoryMetadata.parent_media_index,
                SessionHistoryMetadata.content_rating,
                SessionHistoryMetadata.labels,
                SessionHistoryMetadata.live,
                SessionHistoryMetadata.added_at,
                SessionHistoryMetadata.originally_available_at,
                SessionHistoryMetadata.guid,
                LibrarySection.do_notify,
                LibrarySection.do_notify_created,
                LibrarySection.keep_history,
                LibrarySection.is_active,
            )
            .select_from(LibrarySection)
            .outerjoin(sh_stats, true())
            .outerjoin(last_sh, true())
            .outerjoin(SessionHistoryMetadata, SessionHistoryMetadata.id == last_sh.c.id)
        )

        for condition in filters:
            stmt = stmt.where(condition)

        try:
            with session_scope() as db_session:
                result = queries.fetch_mappings(db_session, stmt)
                total_count = queries.fetch_scalar(
                    db_session,
                    select(func.count(LibrarySection.id)),
                    default=0,
                )
        except Exception as e:
            logger.warn("Tautulli Libraries :: Unable to execute database query for get_list: %s." % e)
            return default_return

        rows = []
        for item in result:
            if item['media_type'] == 'episode' and item['parent_thumb']:
                thumb = item['parent_thumb']
            elif item['media_type'] == 'episode':
                thumb = item['grandparent_thumb']
            else:
                thumb = item['thumb']

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

            row = {'row_id': item['row_id'],
                   'server_id': item['server_id'],
                   'section_id': item['section_id'],
                   'section_name': item['section_name'],
                   'section_type': item['section_type'],
                   'count': item['count'],
                   'parent_count': item['parent_count'],
                   'child_count': item['child_count'],
                   'library_thumb': library_thumb,
                   'library_art': library_art,
                   'plays': item['plays'],
                   'duration': item['duration'],
                   'last_accessed': item['last_accessed'],
                   'history_row_id': item['history_row_id'],
                   'last_played': item['last_played'],
                   'rating_key': item['rating_key'],
                   'media_type': item['media_type'],
                   'thumb': thumb,
                   'parent_title': item['parent_title'],
                   'year': item['year'],
                   'media_index': item['media_index'],
                   'parent_media_index': item['parent_media_index'],
                   'content_rating': item['content_rating'],
                   'labels': item['labels'].split(';') if item['labels'] else (),
                   'live': item['live'],
                   'originally_available_at': item['originally_available_at'],
                   'guid': item['guid'],
                   'do_notify': item['do_notify'],
                   'do_notify_created': item['do_notify_created'],
                   'keep_history': item['keep_history'],
                   'is_active': item['is_active']
                   }

            rows.append(row)

        results = helpers.process_datatable_rows(rows, json_data, default_sort='section_name')

        data = {'recordsFiltered': results['filtered_count'],
                'recordsTotal': total_count,
                'data': session.mask_session_info(results['results']),
                'draw': int(json_data.get('draw', 0))
                }

        return data

    def get_datatables_media_info(self, section_id=None, section_type=None, rating_key=None, refresh=False, kwargs=None):
        default_return = {'recordsFiltered': 0,
                          'recordsTotal': 0,
                          'draw': 0,
                          'data': [],
                          'filtered_file_size': 0,
                          'total_file_size': 0,
                          'last_refreshed': None}

        if not session.allow_session_library(section_id):
            return default_return

        if section_id and not str(section_id).isdigit():
            logger.warn("Tautulli Libraries :: Datatable media info called but invalid section_id provided.")
            return default_return
        elif rating_key and not str(rating_key).isdigit():
            logger.warn("Tautulli Libraries :: Datatable media info called but invalid rating_key provided.")
            return default_return
        elif not section_id and not rating_key:
            logger.warn("Tautulli Libraries :: Datatable media info called but no input provided.")
            return default_return

        # Get the library details
        library_details = self.get_details(section_id=section_id)
        if library_details['section_id'] == None:
            logger.debug("Tautulli Libraries :: Library section_id %s not found." % section_id)
            return default_return

        if not section_type:
            section_type = library_details['section_type']

        # Get play counts from the database
        group_key = SessionHistory.reference_id if plexpy.CONFIG.GROUP_HISTORY_TABLES else SessionHistory.id

        if section_type in ('show', 'artist'):
            group_column = SessionHistory.grandparent_rating_key
        elif section_type in ('season', 'album'):
            group_column = SessionHistory.parent_rating_key
        else:
            group_column = SessionHistory.rating_key

        group_name = group_column.name

        try:
            stmt = (
                select(
                    func.max(SessionHistory.started).label('last_played'),
                    func.count(distinct(group_key)).label('play_count'),
                    group_column.label(group_name),
                )
                .where(SessionHistory.section_id == helpers.cast_to_int(section_id))
                .group_by(group_column)
            )
            with session_scope() as db_session:
                result = queries.fetch_mappings(db_session, stmt)
        except Exception as e:
            logger.warn("Tautulli Libraries :: Unable to execute database query for get_datatables_media_info2: %s." % e)
            return default_return

        watched_list = {}
        for item in result:
            watched_list[str(item.get(group_name))] = {'last_played': item.get('last_played'),
                                                       'play_count': item.get('play_count')}

        # Import media info cache from json file
        cache_time, rows, library_count = self._load_media_info_cache(section_id=section_id, rating_key=rating_key)

        # If no cache was imported, get all library children items
        cached_items = {d['rating_key']: d['file_size'] for d in rows} if not refresh else {}

        if refresh or not rows:
            pms_connect = pmsconnect.PmsConnect()

            if rating_key:
                library_children = pms_connect.get_library_children_details(rating_key=rating_key,
                                                                            section_id=section_id,
                                                                            section_type=section_type,
                                                                            get_media_info=True)
            elif section_id:
                library_children = pms_connect.get_library_children_details(section_id=section_id,
                                                                            section_type=section_type,
                                                                            get_media_info=True)
            if library_children:
                library_count = library_children['library_count']
                children_list = library_children['children_list']
            else:
                logger.warn("Tautulli Libraries :: Unable to get a list of library items.")
                return default_return

            new_rows = []
            for item in children_list:
                ## TODO: Check list of media info items, currently only grabs first item

                cached_file_size = cached_items.get(item['rating_key'], None)
                file_size = cached_file_size if cached_file_size else item.get('file_size', '')

                row = {'section_id': library_details['section_id'],
                       'section_type': library_details['section_type'],
                       'added_at': item['added_at'],
                       'media_type': item['media_type'],
                       'rating_key': item['rating_key'],
                       'parent_rating_key': item['parent_rating_key'],
                       'grandparent_rating_key': item['grandparent_rating_key'],
                       'title': item['title'],
                       'sort_title': item['sort_title'] or item['title'],
                       'year': item['year'],
                       'media_index': item['media_index'],
                       'parent_media_index': item['parent_media_index'],
                       'thumb': item['thumb'],
                       'container': item.get('container', ''),
                       'bitrate': item.get('bitrate', ''),
                       'video_codec': item.get('video_codec', ''),
                       'video_resolution': item.get('video_resolution', ''),
                       'video_framerate': item.get('video_framerate', ''),
                       'audio_codec': item.get('audio_codec', ''),
                       'audio_channels': item.get('audio_channels', ''),
                       'file_size': file_size
                       }
                new_rows.append(row)

            rows = new_rows
            if not rows:
                return default_return

            # Cache the media info to a json file
            self._save_media_info_cache(section_id=section_id, rating_key=rating_key, rows=rows)

        # Update the last_played and play_count
        for item in rows:
            watched_item = watched_list.get(item['rating_key'], None)
            if watched_item:
                item['last_played'] = watched_item['last_played']
                item['play_count'] = watched_item['play_count']
            else:
                item['last_played'] = None
                item['play_count'] = None

        results = []

        # Get datatables JSON data
        if kwargs.get('json_data'):
            json_data = helpers.process_json_kwargs(json_kwargs=kwargs.get('json_data'))
            #print json_data

        # Search results
        search_value = json_data['search']['value'].lower()
        if search_value:
            searchable_columns = [d['data'] for d in json_data['columns'] if d['searchable']] + ['title']
            for row in rows:
                for k,v in row.items():
                    if k in searchable_columns and search_value in v.lower():
                        results.append(row)
                        break
        else:
            results = rows

        filtered_count = len(results)

        # Sort results
        results = sorted(results, key=lambda k: k['sort_title'].lower())
        sort_order = json_data['order']
        for order in reversed(sort_order):
            sort_key = json_data['columns'][int(order['column'])]['data']
            reverse = True if order['dir'] == 'desc' else False
            if rating_key and sort_key == 'sort_title':
                results = sorted(results, key=lambda k: helpers.cast_to_int(k['media_index']), reverse=reverse)
            elif sort_key in ('file_size', 'bitrate', 'added_at', 'last_played', 'play_count'):
                results = sorted(results, key=lambda k: helpers.cast_to_int(k[sort_key]), reverse=reverse)
            elif sort_key == 'video_resolution':
                results = sorted(results, key=lambda k: helpers.cast_to_int(k[sort_key].replace('4k', '2160p').rstrip('p')), reverse=reverse)
            else:
                results = sorted(results, key=lambda k: k[sort_key].lower(), reverse=reverse)

        total_file_size = sum([helpers.cast_to_int(d['file_size']) for d in results])

        # Paginate results
        results = results[json_data['start']:(json_data['start'] + json_data['length'])]

        filtered_file_size = sum([helpers.cast_to_int(d['file_size']) for d in results])

        output = {
            'recordsFiltered': filtered_count,
            'recordsTotal': int(library_count),
            'data': results,
            'draw': int(json_data['draw']),
            'filtered_file_size': filtered_file_size,
            'total_file_size': total_file_size,
            'last_refreshed': cache_time
        }

        return output

    def get_media_info_file_sizes(self, section_id=None, rating_key=None):
        if not session.allow_session_library(section_id):
            return False

        if section_id and not str(section_id).isdigit():
            logger.warn("Tautulli Libraries :: Datatable media info file size called but invalid section_id provided.")
            return False
        elif rating_key and not str(rating_key).isdigit():
            logger.warn("Tautulli Libraries :: Datatable media info file size called but invalid rating_key provided.")
            return False

        # Get the library details
        library_details = self.get_details(section_id=section_id)
        if library_details['section_id'] == None:
            logger.debug("Tautulli Libraries :: Library section_id %s not found." % section_id)
            return False
        if library_details['section_type'] == 'photo':
            return False

        # Import media info cache from json file
        _, rows, _ = self._load_media_info_cache(section_id=section_id, rating_key=rating_key)

        # Get the total file size for each item
        if rating_key:
            logger.debug("Tautulli Libraries :: Getting file sizes for rating_key %s." % rating_key)
        elif section_id:
            logger.debug("Tautulli Libraries :: Fetting file sizes for section_id %s." % section_id)

        pms_connect = pmsconnect.PmsConnect()

        for item in rows:
            if item['rating_key'] and not item['file_size']:
                file_size = 0

                metadata = pms_connect.get_metadata_children_details(rating_key=item['rating_key'],
                                                                     get_children=True,
                                                                     media_type=item['media_type'],
                                                                     section_id=section_id)

                for child_metadata in metadata:
                    ## TODO: Check list of media info items, currently only grabs first item
                    media_info = media_part_info = {}
                    if 'media_info' in child_metadata and len(child_metadata['media_info']) > 0:
                        media_info = child_metadata['media_info'][0]
                        if 'parts' in media_info and len (media_info['parts']) > 0:
                            media_part_info = next((p for p in media_info['parts'] if p['selected']),
                                                   media_info['parts'][0])

                    file_size += helpers.cast_to_int(media_part_info.get('file_size', 0))

                item['file_size'] = file_size

        # Cache the media info to a json file
        self._save_media_info_cache(section_id=section_id, rating_key=rating_key, rows=rows)

        if rating_key:
            logger.debug("Tautulli Libraries :: File sizes updated for rating_key %s." % rating_key)
        elif section_id:
            logger.debug("Tautulli Libraries :: File sizes updated for section_id %s." % section_id)

        return True
    
    def _load_media_info_cache(self, section_id=None, rating_key=None):
        cache_time = None
        rows = []
        library_count = 0

        # Import media info cache from json file
        if rating_key:
            try:
                inFilePath = os.path.join(plexpy.CONFIG.CACHE_DIR,'media_info_%s-%s.json' % (section_id, rating_key))
                with open(inFilePath, 'r') as inFile:
                    data = json.load(inFile)
                    if isinstance(data, dict):
                        cache_time = data['last_refreshed']
                        rows = data['rows']
                    else:
                        rows = data
                    library_count = len(rows)
                logger.debug("Tautulli Libraries :: Loaded media info from cache for rating_key %s (%s items)." % (rating_key, library_count))
            except IOError as e:
                logger.debug("Tautulli Libraries :: No media info cache for rating_key %s." % rating_key)

        elif section_id:
            try:
                inFilePath = os.path.join(plexpy.CONFIG.CACHE_DIR,'media_info_%s.json' % section_id)
                with open(inFilePath, 'r') as inFile:
                    data = json.load(inFile)
                    if isinstance(data, dict):
                        cache_time = data['last_refreshed']
                        rows = data['rows']
                    else:
                        rows = data
                    library_count = len(rows)
                logger.debug("Tautulli Libraries :: Loaded media info from cache for section_id %s (%s items)." % (section_id, library_count))
            except IOError as e:
                logger.debug("Tautulli Libraries :: No media info cache for section_id %s." % section_id)

        return cache_time, rows, library_count
    
    def _save_media_info_cache(self, section_id=None, rating_key=None, rows=None):
        cache_time = helpers.timestamp()

        if rows is None:
            rows = []
        
        if rating_key:
            try:
                outFilePath = os.path.join(plexpy.CONFIG.CACHE_DIR,'media_info_%s-%s.json' % (section_id, rating_key))
                with open(outFilePath, 'w') as outFile:
                    json.dump({'last_refreshed': cache_time, 'rows': rows}, outFile)
                logger.debug("Tautulli Libraries :: Saved media info cache for rating_key %s." % rating_key)
            except IOError as e:
                logger.debug("Tautulli Libraries :: Unable to create cache file for rating_key %s." % rating_key)

        elif section_id:
            try:
                outFilePath = os.path.join(plexpy.CONFIG.CACHE_DIR,'media_info_%s.json' % section_id)
                with open(outFilePath, 'w') as outFile:
                    json.dump({'last_refreshed': cache_time, 'rows': rows}, outFile)
                logger.debug("Tautulli Libraries :: Saved media info cache for section_id %s." % section_id)
            except IOError as e:
                logger.debug("Tautulli Libraries :: Unable to create cache file for section_id %s." % section_id)

    def set_config(self, section_id=None, custom_thumb='', custom_art='',
                   do_notify=1, keep_history=1, do_notify_created=1):
        if section_id:
            value_dict = {'custom_thumb_url': custom_thumb,
                          'custom_art_url': custom_art,
                          'do_notify': do_notify,
                          'do_notify_created': do_notify_created,
                          'keep_history': keep_history}
            try:
                with session_scope() as db_session:
                    stmt = (
                        update(LibrarySection)
                        .where(LibrarySection.section_id == section_id)
                        .values(**value_dict)
                    )
                    update_result = db_session.execute(stmt)
                    if not update_result.rowcount or update_result.rowcount == 0:
                        insert_values = {'section_id': section_id, **value_dict}
                        db_session.execute(insert(LibrarySection).values(**insert_values))
            except Exception as e:
                logger.warn("Tautulli Libraries :: Unable to execute database query for set_config: %s." % e)

    def get_details(self, section_id=None, server_id=None, include_last_accessed=False):
        default_return = {'row_id': 0,
                          'server_id': '',
                          'section_id': 0,
                          'section_name': 'Local',
                          'section_type': '',
                          'library_thumb': common.DEFAULT_COVER_THUMB,
                          'library_art': '',
                          'count': 0,
                          'parent_count': 0,
                          'child_count': 0,
                          'is_active': 1,
                          'do_notify': 0,
                          'do_notify_created': 0,
                          'keep_history': 1,
                          'deleted_section': 0,
                          'last_accessed': None,
                          }

        if not section_id:
            return default_return

        if server_id is None:
            server_id = plexpy.CONFIG.PMS_IDENTIFIER

        library_details = self.get_library_details(section_id=section_id, server_id=server_id,
                                                   include_last_accessed=include_last_accessed)

        if library_details:
            return library_details

        else:
            logger.warn("Tautulli Libraries :: Unable to retrieve library %s from database. Requesting library list refresh."
                        % section_id)
            # Let's first refresh the libraries list to make sure the library isn't newly added and not in the db yet
            refresh_libraries()

            library_details = self.get_library_details(section_id=section_id, server_id=server_id,
                                                       include_last_accessed=include_last_accessed)

            if library_details:
                return library_details

            else:
                logger.warn("Tautulli Users :: Unable to retrieve library %s from database. Returning 'Local' library."
                            % section_id)
                # If there is no library data we must return something
                return default_return

    def get_library_details(self, section_id=None, server_id=None, include_last_accessed=False):
        if server_id is None:
            server_id = plexpy.CONFIG.PMS_IDENTIFIER

        last_accessed_expr = (
            select(func.max(SessionHistory.started))
            .where(SessionHistory.section_id == LibrarySection.section_id)
            .scalar_subquery()
            if include_last_accessed else literal(None)
        )

        try:
            if str(section_id).isdigit():
                section_id_int = helpers.cast_to_int(section_id)
            else:
                raise Exception('Missing section_id')

            stmt = (
                select(
                    LibrarySection.id.label('row_id'),
                    LibrarySection.server_id,
                    LibrarySection.section_id,
                    LibrarySection.section_name,
                    LibrarySection.section_type,
                    LibrarySection.count,
                    LibrarySection.parent_count,
                    LibrarySection.child_count,
                    LibrarySection.thumb.label('library_thumb'),
                    LibrarySection.custom_thumb_url.label('custom_thumb'),
                    LibrarySection.art.label('library_art'),
                    LibrarySection.custom_art_url.label('custom_art'),
                    LibrarySection.is_active,
                    LibrarySection.do_notify,
                    LibrarySection.do_notify_created,
                    LibrarySection.keep_history,
                    LibrarySection.deleted_section,
                    last_accessed_expr.label('last_accessed'),
                )
                .where(
                    LibrarySection.section_id == section_id_int,
                    LibrarySection.server_id == server_id,
                )
            )
            with session_scope() as db_session:
                result = queries.fetch_mappings(db_session, stmt)
        except Exception as e:
            logger.warn("Tautulli Libraries :: Unable to execute database query for get_library_details: %s." % e)
            result = []

        library_details = {}
        if result:
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

                library_details = {'row_id': item['row_id'],
                                   'server_id': item['server_id'],
                                   'section_id': item['section_id'],
                                   'section_name': item['section_name'],
                                   'section_type': item['section_type'],
                                   'library_thumb': library_thumb,
                                   'library_art': library_art,
                                   'count': item['count'],
                                   'parent_count': item['parent_count'],
                                   'child_count': item['child_count'],
                                   'is_active': item['is_active'],
                                   'do_notify': item['do_notify'],
                                   'do_notify_created': item['do_notify_created'],
                                   'keep_history': item['keep_history'],
                                   'deleted_section': item['deleted_section'],
                                   'last_accessed': item['last_accessed']
                                   }
        return library_details

    def get_watch_time_stats(self, section_id=None, grouping=None, query_days=None):
        if not session.allow_session_library(section_id):
            return []

        if grouping is None:
            grouping = plexpy.CONFIG.GROUP_HISTORY_TABLES

        if query_days and query_days is not None:
            query_days = map(helpers.cast_to_int, str(query_days).split(','))
        else:
            query_days = [1, 7, 30, 0]

        timestamp = helpers.timestamp()
        library_watch_time_stats = []
        section_id_int = helpers.cast_to_int(section_id) if str(section_id).isdigit() else None

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
                if section_id_int is not None:
                    stmt = (
                        select(total_time_expr, total_plays_expr)
                        .select_from(SessionHistory)
                        .join(SessionHistoryMetadata, SessionHistoryMetadata.id == SessionHistory.id)
                        .where(SessionHistory.section_id == section_id_int)
                    )
                    if days > 0:
                        stmt = stmt.where(SessionHistory.stopped >= timestamp_query)
                    with session_scope() as db_session:
                        result = queries.fetch_mapping(db_session, stmt, default={})
            except Exception as e:
                logger.warn("Tautulli Libraries :: Unable to execute database query for get_watch_time_stats: %s." % e)
                result = {}

            if result:
                total_time = result.get('total_time') or 0
                total_plays = result.get('total_plays') or 0

                row = {'query_days': days,
                       'total_time': total_time,
                       'total_plays': total_plays
                       }

                library_watch_time_stats.append(row)

        return library_watch_time_stats

    def get_user_stats(self, section_id=None, grouping=None):
        if not session.allow_session_library(section_id):
            return []

        if grouping is None:
            grouping = plexpy.CONFIG.GROUP_HISTORY_TABLES

        user_stats = []
        section_id_int = helpers.cast_to_int(section_id) if str(section_id).isdigit() else None

        group_key = SessionHistory.reference_id if grouping else SessionHistory.id
        total_time_expr = (
            func.sum(SessionHistory.stopped - SessionHistory.started)
            - func.sum(func.coalesce(SessionHistory.paused_counter, 0))
        )
        total_plays_expr = func.count(distinct(group_key))
        friendly_name_expr = case(
            (
                or_(User.friendly_name.is_(None), func.trim(User.friendly_name) == ''),
                User.username,
            ),
            else_=User.friendly_name,
        )

        try:
            result = []
            if section_id_int is not None:
                stmt = (
                    select(
                        friendly_name_expr.label('friendly_name'),
                        User.user_id,
                        User.username,
                        User.thumb,
                        User.custom_avatar_url.label('custom_thumb'),
                        total_plays_expr.label('total_plays'),
                        total_time_expr.label('total_time'),
                    )
                    .select_from(SessionHistory)
                    .join(SessionHistoryMetadata, SessionHistoryMetadata.id == SessionHistory.id)
                    .join(User, User.user_id == SessionHistory.user_id)
                    .where(SessionHistory.section_id == section_id_int)
                    .group_by(User.user_id, User.username, User.friendly_name, User.thumb, User.custom_avatar_url)
                    .order_by(total_plays_expr.desc(), total_time_expr.desc())
                )
                with session_scope() as db_session:
                    result = queries.fetch_mappings(db_session, stmt)
        except Exception as e:
            logger.warn("Tautulli Libraries :: Unable to execute database query for get_user_stats: %s." % e)
            result = []

        for item in result:
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

        return session.mask_session_info(user_stats, mask_metadata=False)

    def get_recently_watched(self, section_id=None, limit='10'):
        if not session.allow_session_library(section_id):
            return []

        recently_watched = []
        section_id_int = helpers.cast_to_int(section_id) if str(section_id).isdigit() else None

        if not limit.isdigit():
            limit = '10'

        try:
            result = []
            if section_id_int is not None:
                limit_value = helpers.cast_to_int(limit) or 10
                sh = aliased(SessionHistory)
                sh_inner = aliased(SessionHistory)

                latest_session = (
                    select(sh_inner.id)
                    .where(
                        sh_inner.section_id == sh.section_id,
                        sh_inner.rating_key == sh.rating_key,
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
                        SessionHistoryMetadata.content_rating,
                        SessionHistoryMetadata.labels,
                        sh.section_id,
                    )
                    .join(SessionHistoryMetadata, SessionHistoryMetadata.id == sh.id)
                    .where(
                        sh.section_id == section_id_int,
                        sh.id == latest_session,
                    )
                    .order_by(sh.started.desc())
                    .limit(limit_value)
                )
                with session_scope() as db_session:
                    result = queries.fetch_mappings(db_session, stmt)
        except Exception as e:
            logger.warn("Tautulli Libraries :: Unable to execute database query for get_recently_watched: %s." % e)
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
                                 'user': row['user'],
                                 'section_id': row['section_id'],
                                 'content_rating': row['content_rating'],
                                 'labels': row['labels'].split(';') if row['labels'] else (),
                                 }
                recently_watched.append(recent_output)

        return session.mask_session_info(recently_watched)

    def get_sections(self):
        try:
            stmt = (
                select(
                    LibrarySection.section_id,
                    LibrarySection.section_name,
                    LibrarySection.section_type,
                    LibrarySection.agent,
                )
                .where(LibrarySection.deleted_section == 0)
            )
            with session_scope() as db_session:
                result = queries.fetch_mappings(db_session, stmt)
        except Exception as e:
            logger.warn("Tautulli Libraries :: Unable to execute database query for get_sections: %s." % e)
            return None

        libraries = []
        for item in result:
            library = {'section_id': item['section_id'],
                       'section_name': item['section_name'],
                       'section_type': item['section_type'],
                       'agent': item['agent']
                       }
            libraries.append(library)

        return libraries

    def delete(self, server_id=None, section_id=None, row_ids=None, purge_only=False):
        if row_ids and row_ids is not None:
            row_ids = list(map(helpers.cast_to_int, row_ids.split(',')))

            # Get the section_ids corresponding to the row_ids
            with session_scope() as db_session:
                stmt = (
                    select(LibrarySection.server_id, LibrarySection.section_id)
                    .where(LibrarySection.id.in_(row_ids))
                )
                result = queries.fetch_mappings(db_session, stmt)

            success = []
            for library in result:
                success.append(self.delete(server_id=library['server_id'], section_id=library['section_id'],
                                           purge_only=purge_only))
            return all(success)

        elif str(section_id).isdigit():
            server_id = server_id or plexpy.CONFIG.PMS_IDENTIFIER
            if server_id == plexpy.CONFIG.PMS_IDENTIFIER:
                delete_success = cleanup.delete_library_history(section_id=section_id)
            else:
                logger.warn("Tautulli Libraries :: Library history not deleted for library section_id %s "
                            "because library server_id %s does not match Plex server identifier %s."
                            % (section_id, server_id, plexpy.CONFIG.PMS_IDENTIFIER))
                delete_success = True

            if purge_only:
                return delete_success
            else:
                logger.info("Tautulli Libraries :: Deleting library with server_id %s and section_id %s from database."
                            % (server_id, section_id))
                try:
                    with session_scope() as db_session:
                        stmt = (
                            update(LibrarySection)
                            .where(
                                LibrarySection.server_id == server_id,
                                LibrarySection.section_id == section_id,
                            )
                            .values(
                                deleted_section=1,
                                keep_history=0,
                                do_notify=0,
                                do_notify_created=0,
                            )
                        )
                        db_session.execute(stmt)
                    return delete_success
                except Exception as e:
                    logger.warn("Tautulli Libraries :: Unable to execute database query for delete: %s." % e)

        else:
            return False

    def undelete(self, section_id=None, section_name=None):
        try:
            if section_id and section_id.isdigit():
                section_id_int = helpers.cast_to_int(section_id)
                with session_scope() as db_session:
                    stmt = select(LibrarySection.id).where(LibrarySection.section_id == section_id_int)
                    result = queries.fetch_mapping(db_session, stmt, default={})
                if result:
                    logger.info("Tautulli Libraries :: Re-adding library with id %s to database." % section_id)
                    with session_scope() as db_session:
                        stmt = (
                            update(LibrarySection)
                            .where(LibrarySection.section_id == section_id_int)
                            .values(
                                deleted_section=0,
                                keep_history=1,
                                do_notify=1,
                                do_notify_created=1,
                            )
                        )
                        db_session.execute(stmt)
                    return True
                else:
                    return False

            elif section_name:
                with session_scope() as db_session:
                    stmt = select(LibrarySection.id).where(LibrarySection.section_name == section_name)
                    result = queries.fetch_mapping(db_session, stmt, default={})
                if result:
                    logger.info("Tautulli Libraries :: Re-adding library with name %s to database." % section_name)
                    with session_scope() as db_session:
                        stmt = (
                            update(LibrarySection)
                            .where(LibrarySection.section_name == section_name)
                            .values(
                                deleted_section=0,
                                keep_history=1,
                                do_notify=1,
                                do_notify_created=1,
                            )
                        )
                        db_session.execute(stmt)
                    return True
                else:
                    return False

        except Exception as e:
            logger.warn("Tautulli Libraries :: Unable to execute database query for undelete: %s." % e)

    def delete_media_info_cache(self, section_id=None):
        import os

        try:
            if section_id.isdigit():
                [os.remove(os.path.join(plexpy.CONFIG.CACHE_DIR, f)) for f in os.listdir(plexpy.CONFIG.CACHE_DIR)
                 if f.startswith('media_info_%s' % section_id) and f.endswith('.json')]

                logger.debug("Tautulli Libraries :: Deleted media info table cache for section_id %s." % section_id)
                return 'Deleted media info table cache for library with id %s.' % section_id
            else:
                return 'Unable to delete media info table cache, section_id not valid.'
        except Exception as e:
            logger.warn("Tautulli Libraries :: Unable to delete media info table cache: %s." % e)

    def delete_duplicate_libraries(self):
        # Refresh the PMS_URL to make sure the server_id is updated
        plextv.get_server_resources()

        server_id = plexpy.CONFIG.PMS_IDENTIFIER

        try:
            logger.debug("Tautulli Libraries :: Deleting libraries where server_id does not match %s." % server_id)
            with session_scope() as db_session:
                stmt = delete(LibrarySection).where(LibrarySection.server_id != server_id)
                db_session.execute(stmt)

            return 'Deleted duplicate libraries from the database.'
        except Exception as e:
            logger.warn("Tautulli Libraries :: Unable to delete duplicate libraries: %s." % e)
