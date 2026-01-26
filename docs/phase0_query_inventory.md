<!-- Purpose: Capture Phase 0 raw SQL inventory and query surface by module. -->
# Phase 0 Query Surface Inventory

Status: initial static scan of `plexpy/` for raw SQL strings. Validation pass added dynamic SQL construction paths in `datafactory.py`, `datatables.py`, `mobile_app.py`, `users.py`, `plexwatch_import.py`, `plexivity_import.py`, `notification_handler.py`, `webauth.py`, and `api2.py`.

Legend: READ, WRITE, UPSERT, DELETE, SCHEMA, TXN.

## Validation checklist
- `dbcheck()` block captured (all DDL, ALTERs, and migrations).
- Dynamic SQL builders noted (`datatables.py`, `datafactory.py`, `mobile_app.py`, and user_id NOT IN in `users.py`).
- Raw SQL entry points recorded (`api2.py` `sql()`, import tools in `plexwatch_import.py` and `plexivity_import.py`).
- All lookup tables covered (tvmaze/themoviedb/musicbrainz/image_hash/imgur/cloudinary).
- High-traffic history/users/libraries modules present (activity_processor, datafactory, graphs, users, libraries).

## plexpy/__init__.py (dbcheck)
```
SCHEMA: CREATE TABLE IF NOT EXISTS ... (version_info, sessions, sessions_continued, session_history, session_history_media_info, session_history_metadata, users, library_sections, user_login, notifiers, notify_log, newsletters, newsletter_log, recently_added, mobile_devices, tvmaze_lookup, themoviedb_lookup, musicbrainz_lookup, image_hash_lookup, imgur_lookup, cloudinary_lookup, exports)
SCHEMA: ALTER TABLE ... (sessions, session_history, session_history_metadata, session_history_media_info, users, notify_log, newsletter_log, newsletters, library_sections, mobile_devices, notifiers, tvmaze_lookup, themoviedb_lookup, user_login, exports)
WRITE: UPDATE session_history SET reference_id = (CASE ...)
WRITE: UPDATE session_history SET platform = 'Windows' WHERE platform = 'windows'
WRITE: UPDATE session_history SET platform = 'macOS' WHERE platform = 'macos'
WRITE: UPDATE session_history_media_info SET transcode_decision = (CASE ...)
WRITE: UPDATE session_history_media_info SET video_resolution = REPLACE(...)
WRITE: UPDATE session_history_media_info SET subtitle_codec = '' WHERE subtitle_codec IS NULL
WRITE: UPDATE session_history_media_info SET stream_container = '' WHERE stream_container IS NULL
WRITE: UPDATE session_history_media_info SET stream_video_codec = '' WHERE stream_video_codec IS NULL
WRITE: UPDATE session_history_media_info SET stream_audio_codec = '' WHERE stream_audio_codec IS NULL
WRITE: UPDATE session_history_media_info SET stream_subtitle_codec = '' WHERE stream_subtitle_codec IS NULL
WRITE: UPDATE session_history_media_info SET video_scan_type = 'progressive' WHERE video_scan_type IS NULL
WRITE: UPDATE session_history_media_info SET video_full_resolution = (CASE ...)
WRITE: UPDATE session_history_media_info SET stream_video_dynamic_range = 'SDR' WHERE ...
WRITE: UPDATE session_history SET section_id = (SELECT section_id FROM session_history_metadata ...)
SCHEMA: CREATE TABLE session_history_metadata_temp ...; INSERT INTO ... SELECT ...; DROP TABLE ...; ALTER TABLE ... RENAME TO ...
WRITE: UPDATE users SET friendly_name = NULL WHERE friendly_name = username
SCHEMA: CREATE TABLE notify_log_temp ...; INSERT INTO ... SELECT ...; DROP TABLE ...; ALTER TABLE ... RENAME TO ...
WRITE: UPDATE notify_log SET success = 1
SCHEMA: CREATE TABLE newsletters_temp ...; INSERT INTO ... SELECT ...; DROP TABLE ...; ALTER TABLE ... RENAME TO ...
SCHEMA: CREATE TABLE library_sections_temp ...; INSERT INTO ... SELECT ...; DROP TABLE ...; ALTER TABLE ... RENAME TO ...
DELETE: DELETE FROM library_sections WHERE server_id = ''
SCHEMA: CREATE TABLE users_temp ...; INSERT INTO ... SELECT ...; DROP TABLE ...; ALTER TABLE ... RENAME TO ...
SCHEMA: DROP TABLE mobile_devices; CREATE TABLE IF NOT EXISTS mobile_devices ...
WRITE: UPDATE mobile_devices SET official = ? WHERE device_id = ?
WRITE: UPDATE mobile_devices SET platform = ? WHERE device_id = ?
WRITE: UPDATE notifiers SET agent_label = 'Kodi' WHERE agent_label = 'XBMC'
WRITE: UPDATE notifiers SET agent_label = 'macOS Notification Center' WHERE agent_label = 'OSX Notify'
WRITE: UPDATE notifiers SET agent_name = 'remoteapp', agent_label = 'Tautulli Remote App' WHERE agent_name = 'androidapp'
WRITE: UPDATE exports SET thumb_level = 9 WHERE include_thumb = 1
WRITE: UPDATE exports SET art_level = 9 WHERE include_art = 1
DELETE: DELETE FROM tvmaze_lookup WHERE id NOT IN (SELECT MIN(id) FROM tvmaze_lookup GROUP BY rating_key)
DELETE: DELETE FROM themoviedb_lookup WHERE id NOT IN (SELECT MIN(id) FROM themoviedb_lookup GROUP BY rating_key)
DELETE: DELETE FROM musicbrainz_lookup WHERE id NOT IN (SELECT MIN(id) FROM musicbrainz_lookup GROUP BY rating_key)
DELETE: DELETE FROM image_hash_lookup WHERE id NOT IN (SELECT MIN(id) FROM image_hash_lookup GROUP BY img_hash)
DELETE: DELETE FROM cloudinary_lookup WHERE id NOT IN (SELECT MIN(id) FROM cloudinary_lookup GROUP BY img_hash)
DELETE: DELETE FROM imgur_lookup WHERE id NOT IN (SELECT MIN(id) FROM imgur_lookup GROUP BY img_hash)
READ: SELECT id FROM users WHERE username = 'Local'
WRITE: INSERT INTO users (user_id, username) VALUES (0, 'Local')
SCHEMA: CREATE INDEX IF NOT EXISTS ... (session_history, session_history_metadata, session_history_media_info)
SCHEMA: CREATE UNIQUE INDEX IF NOT EXISTS ... (lookup tables, sessions_continued)
READ: SELECT value FROM version_info WHERE key = 'version'
WRITE: INSERT OR REPLACE INTO version_info (key, value) VALUES ('version', ?)
WRITE: UPDATE version_info SET value = ? WHERE key = 'version'
READ/SCHEMA: SELECT SQL FROM sqlite_master WHERE type='table' AND name='poster_urls'
READ: SELECT * FROM poster_urls
SCHEMA: DROP TABLE poster_urls
```

## plexpy/database.py
```
READ: SELECT started FROM session_history
TXN: BEGIN IMMEDIATE
SCHEMA: ATTACH ? AS import_db; DETACH import_db
READ: SELECT * FROM import_db.version_info WHERE key = 'version'
READ: SELECT seq FROM sqlite_sequence WHERE name = 'session_history'
SCHEMA: CREATE TABLE {table}_copy AS SELECT * FROM import_db.{table}
WRITE: UPDATE {table}_copy SET id = id + ?
WRITE: UPDATE session_history_copy SET reference_id = reference_id + ?
SCHEMA: ALTER TABLE {from_db}.session_history{copy} ADD COLUMN section_id INTEGER
WRITE: UPDATE {from_db}.session_history{copy} SET section_id = (SELECT section_id FROM {from_db}.session_history_metadata{copy} ...)
READ: SELECT name FROM import_db.sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name
READ: PRAGMA main.table_info({table})
READ: PRAGMA {from_db}.table_info({from_table})
WRITE: DELETE FROM {table}
WRITE: DELETE FROM sqlite_sequence WHERE name = ?
WRITE: INSERT OR IGNORE INTO {table} ({columns}) SELECT {columns} FROM {from_db}.{from_table}
DELETE: DELETE FROM {table} WHERE id NOT IN (SELECT id FROM session_history)
DELETE: DELETE FROM {table} WHERE id NOT IN (SELECT MIN(id) FROM {table} GROUP BY {columns})
SCHEMA: DROP TABLE {table}_copy
READ: PRAGMA integrity_check
WRITE: VACUUM
WRITE: PRAGMA optimize
SCHEMA: PRAGMA synchronous = ...; PRAGMA journal_mode = ...; PRAGMA cache_size = ...
UPSERT: UPDATE {table} SET ... WHERE ...; INSERT INTO {table} (...) VALUES (...)
READ: SELECT last_insert_rowid() AS last_id
DELETE: DELETE FROM {table} WHERE id IN (?,...)
```

## plexpy/activity_processor.py
```
UPSERT: UPDATE sessions ...; INSERT INTO sessions (...) VALUES (...)
READ: SELECT session_history.id, session_history_metadata.guid, session_history.reference_id FROM session_history JOIN session_history_metadata ... ORDER BY ... LIMIT 1
READ: SELECT id, rating_key, view_offset, reference_id FROM session_history WHERE ... ORDER BY id DESC LIMIT 2
WRITE: UPDATE session_history SET reference_id = ? WHERE id = ?
READ: SELECT * FROM sessions
READ: SELECT * FROM sessions WHERE user_id = ?
READ: SELECT * FROM sessions WHERE session_key = ?
READ: SELECT * FROM sessions WHERE session_id = ?
DELETE: DELETE FROM sessions WHERE session_key = ?
DELETE: DELETE FROM sessions WHERE id = ?
READ: SELECT last_paused, paused_counter FROM sessions WHERE session_key = ?
WRITE: UPDATE sessions SET buffer_count = buffer_count + 1 WHERE session_key = ?
READ: SELECT buffer_count FROM sessions WHERE session_key = ?
WRITE: UPDATE sessions SET buffer_last_triggered = strftime('%s','now') WHERE session_key = ?
READ: SELECT buffer_last_triggered FROM sessions WHERE session_key = ?
WRITE: UPDATE sessions SET stopped = ?
WRITE: UPDATE sessions SET write_attempts = ? WHERE session_key = ?
WRITE: UPDATE sessions SET intro = ?, commercial = ?, credits = ?, marker = ? WHERE session_key = ?
WRITE: UPDATE sessions SET watched = ? WHERE session_key = ?
READ: SELECT stopped FROM sessions_continued WHERE user_id = ? AND machine_id = ? AND media_type = ? ORDER BY stopped DESC
READ: SELECT * FROM session_history JOIN session_history_metadata ON ...
```

## plexpy/activity_pinger.py
```
WRITE: UPDATE sessions SET paused_counter = ? WHERE session_key = ? AND rating_key = ?
WRITE: UPDATE sessions SET buffer_count = buffer_count + 1 WHERE session_key = ? AND rating_key = ?
READ: SELECT buffer_count, buffer_last_triggered FROM sessions WHERE session_key = ? AND rating_key = ?
WRITE: UPDATE sessions SET buffer_last_triggered = strftime('%s','now') WHERE session_key = ? AND rating_key = ?
WRITE: UPDATE sessions SET stopped = ?, state = ? WHERE session_key = ? AND rating_key = ?
```

## plexpy/datatables.py
```
READ: SELECT * FROM (SELECT {columns} FROM {table} {join} {custom_where} {group} {union}) {where} {order}
READ: SELECT COUNT(id) AS total_count FROM {table}
NOTE: Dynamic SQL assembled from request-provided table/columns/joins (string formatting).
```

## plexpy/datafactory.py
```
READ: SELECT ... FROM (SELECT ... FROM session_history ... GROUP BY ...) AS sh JOIN session_history_metadata ... (home stats)
READ: SELECT ls.id, ls.section_id, ... FROM library_sections ... (library cards)
READ: SELECT (SUM(stopped - started) - SUM(...paused_counter...)) ... FROM session_history ... (duration aggregates)
READ: SELECT (CASE WHEN users.friendly_name ...) ... FROM session_history JOIN users ... (user aggregates)
READ: SELECT bitrate, video_full_resolution, ... FROM session_history_media_info ... (stream stats)
READ: SELECT session_history.section_id, session_history_metadata.id, ... (history lookups)
READ: SELECT imgur_title AS img_title, imgur_url AS img_url FROM imgur_lookup ...
READ: SELECT cloudinary_title AS img_title, cloudinary_url AS img_url FROM cloudinary_lookup ...
READ: SELECT imgur_title, delete_hash, fallback FROM imgur_lookup ...
DELETE: DELETE FROM imgur_lookup WHERE img_hash IN (SELECT img_hash FROM image_hash_lookup ...)
READ: SELECT cloudinary_title, rating_key, fallback FROM cloudinary_lookup ...
DELETE: DELETE FROM cloudinary_lookup WHERE img_hash IN (SELECT img_hash FROM image_hash_lookup ...)
READ: SELECT tvmaze_id FROM tvmaze_lookup WHERE rating_key = ?
READ: SELECT themoviedb_id FROM themoviedb_lookup WHERE rating_key = ?
READ: SELECT musicbrainz_id FROM musicbrainz_lookup WHERE rating_key = ?
DELETE: DELETE FROM themoviedb_lookup WHERE rating_key = ?
DELETE: DELETE FROM tvmaze_lookup WHERE rating_key = ?
DELETE: DELETE FROM musicbrainz_lookup WHERE rating_key = ?
DELETE: DELETE FROM %s_lookup
READ: SELECT rating_key, parent_rating_key, grandparent_rating_key, title, parent_title, grandparent_title, ... FROM session_history_metadata ...
READ: SELECT rating_key, parent_rating_key, grandparent_rating_key FROM session_history ...
WRITE: UPDATE session_history SET grandparent_rating_key = ? WHERE id IN (...)
WRITE: UPDATE session_history_metadata SET grandparent_rating_key = ? WHERE id IN (...)
WRITE: UPDATE session_history SET parent_rating_key = ? WHERE id IN (...)
WRITE: UPDATE session_history_metadata SET parent_rating_key = ? WHERE id IN (...)
WRITE: UPDATE session_history SET rating_key = ? WHERE id IN (...)
WRITE: UPDATE session_history_media_info SET rating_key = ? WHERE id IN (...)
WRITE: UPDATE session_history SET section_id = ? WHERE rating_key = ?
WRITE: UPDATE session_history_metadata SET rating_key = ?, parent_rating_key = ?, grandparent_rating_key = ? WHERE rating_key = ?
DELETE: DELETE FROM notify_log
DELETE: DELETE FROM newsletter_log
READ: SELECT machine_id FROM session_history WHERE user_id = ? ...
READ: SELECT * FROM (SELECT user_id, machine_id FROM session_history UNION SELECT user_id, machine_id FROM sessions_continued)
READ: SELECT * FROM recently_added WHERE rating_key = ?
NOTE: `where_timeframe`, `where_id`, `group_by`, and `sort_type` are interpolated into query strings (string formatting).
NOTE: `before`/`after` dates and `section_id`/`user_id` flow into SQL via string interpolation.
```

## plexpy/graphs.py
```
READ: SELECT sh.date_played ... FROM (SELECT ... FROM session_history ... GROUP BY date_played, {group_by}) AS sh JOIN session_history_metadata ...
READ: SELECT sh.daynumber ... FROM (SELECT ... FROM session_history ... GROUP BY daynumber, {group_by}) AS sh JOIN session_history_metadata ...
READ: SELECT sh.hourofday ... FROM (SELECT ... FROM session_history ... GROUP BY hourofday, {group_by}) AS sh JOIN session_history_metadata ...
READ: SELECT sh.datestring ... FROM (SELECT ... FROM session_history ... GROUP BY datestring, {group_by}) AS sh JOIN session_history_metadata ...
READ: SELECT u.user_id, u.username, ... FROM (SELECT * FROM session_history ... GROUP BY {group_by}) AS sh JOIN session_history_metadata ... JOIN users ...
READ: SELECT sh.platform ... FROM (SELECT * FROM session_history ... GROUP BY {group_by}) AS sh JOIN session_history_metadata ...
READ: SELECT sh.date_played, shmi.transcode_decision ... FROM (SELECT ... FROM session_history ... GROUP BY id) AS sh JOIN session_history_media_info ...
READ: SELECT shmi.video_full_resolution AS resolution ... FROM (SELECT * FROM session_history ... GROUP BY {group_by}) AS sh JOIN session_history_media_info ...
```

## plexpy/users.py
```
READ: SELECT thumb, custom_avatar_url FROM users WHERE user_id = ?
WRITE: UPDATE users SET is_active = 0 WHERE user_id NOT IN (?,...)
NOTE: `user_id NOT IN` placeholders are dynamically constructed with `format()`.
READ: SELECT users.id AS row_id, users.user_id, username, ... FROM users ...
READ: SELECT ... FROM session_history JOIN session_history_metadata ... (user stats)
WRITE: UPDATE users SET deleted_user = 1, keep_history = 0, do_notify = 0 WHERE user_id = ?
WRITE: UPDATE users SET deleted_user = 0, keep_history = 1, do_notify = 1 WHERE user_id = ?
WRITE: UPDATE users SET deleted_user = 0, keep_history = 1, do_notify = 1 WHERE username = ?
READ: SELECT user_id FROM users WHERE username = ?
READ: SELECT user_id, friendly_name FROM users WHERE deleted_user = 0 ...
READ: SELECT allow_guest, user_token, server_token FROM users WHERE user_id = ? AND deleted_user = 0
READ: SELECT filter_all, filter_movies, filter_tv, filter_music, filter_photos FROM users WHERE user_id = ?
UPSERT: UPDATE users ...; INSERT INTO users ...
UPSERT: UPDATE user_login ...; INSERT INTO user_login ...
READ: SELECT * FROM user_login WHERE jwt_token = ?
WRITE: UPDATE user_login SET jwt_token = NULL WHERE jwt_token = ?
WRITE: UPDATE user_login SET jwt_token = NULL WHERE id IN (?,...)
READ: SELECT * FROM user_login ... JOIN users ...
DELETE: DELETE FROM user_login; VACUUM
```

## plexpy/webauth.py
```
READ: SELECT timestamp, success FROM user_login WHERE ip_address = ? AND timestamp >= (SELECT CASE WHEN MAX(timestamp) IS NULL THEN 0 ELSE MAX(timestamp) END FROM user_login WHERE ip_address = ? AND success = 1) ORDER BY timestamp DESC
```

## plexpy/notification_handler.py
```
READ: SELECT * FROM image_hash_lookup WHERE img_hash = ?
UPSERT: upsert into image_hash_lookup (set_hash_image_info)
READ: SELECT imdb_id, tvmaze_id, tvmaze_url FROM tvmaze_lookup WHERE rating_key = ?
UPSERT: upsert into tvmaze_lookup (lookup_tvmaze_by_id)
READ: SELECT thetvdb_id, imdb_id, themoviedb_id, themoviedb_url FROM themoviedb_lookup WHERE rating_key = ?
READ: SELECT themoviedb_json FROM themoviedb_lookup WHERE rating_key = ?
UPSERT: upsert into themoviedb_lookup (lookup_themoviedb_by_id, get_themoviedb_info)
READ: SELECT musicbrainz_id, musicbrainz_url, musicbrainz_type FROM musicbrainz_lookup WHERE rating_key = ?
UPSERT: upsert into musicbrainz_lookup (lookup_musicbrainz_info)
READ: SELECT timestamp, notify_action, notifier_id FROM notify_log WHERE session_key = ? AND rating_key = ? AND user_id = ? ORDER BY id DESC
READ: SELECT id AS notifier_id, timestamp FROM notifiers LEFT OUTER JOIN (SELECT timestamp, notifier_id FROM notify_log WHERE ... AND notify_action = ?) AS t ON notifiers.id = t.notifier_id WHERE {notify_action} = 1 ...
UPSERT: UPDATE notify_log ...; INSERT INTO notify_log ...
READ: SELECT * FROM notify_log WHERE notify_action = ? AND tag = ?
```

## plexpy/notifiers.py
```
READ: SELECT notifiers.id, ... MAX(notify_log.timestamp) ... FROM notifiers LEFT OUTER JOIN notify_log ... GROUP BY notifiers.id
DELETE: DELETE FROM notifiers WHERE id = ?
READ: SELECT * FROM notifiers WHERE id = ?
UPSERT: UPDATE notifiers ...; INSERT INTO notifiers ...
READ: SELECT notifier_config FROM notifiers
READ: SELECT * FROM mobile_devices WHERE official = 1 AND onesignal_id IS NOT NULL AND onesignal_id != ''
```

## plexpy/mobile_app.py
```
READ: SELECT * FROM mobile_devices %s (dynamic WHERE clause string)
READ: SELECT * FROM mobile_devices WHERE id = ?
DELETE: DELETE FROM mobile_devices WHERE id = ?
DELETE: DELETE FROM mobile_devices WHERE device_id = ?
WRITE: UPDATE mobile_devices SET official = ?, platform = coalesce(platform, ?) WHERE device_id = ?
WRITE: UPDATE mobile_devices SET last_seen = ? WHERE device_token = ?
UPSERT: UPDATE mobile_devices ...; INSERT INTO mobile_devices ...
NOTE: `where` clause is concatenated into SQL.
```

## plexpy/plexwatch_import.py
```
READ: SELECT ratingKey from %s (dynamic table name)
READ: SELECT time AS started, stopped, ... FROM %s ORDER BY id (dynamic table name)
WRITE: INSERT OR IGNORE INTO users (user_id, username) SELECT user_id, user FROM session_history WHERE user_id != 1 GROUP BY user_id
```

## plexpy/plexivity_import.py
```
READ: SELECT xml from %s (dynamic table name)
READ: SELECT id AS id, time AS started, stopped, ... FROM %s ORDER BY id (dynamic table name)
WRITE: INSERT OR IGNORE INTO users (user_id, username) SELECT user_id, user FROM session_history WHERE user_id != 1 GROUP BY user_id
```

## plexpy/libraries.py
```
WRITE: UPDATE library_sections SET is_active = 0 WHERE server_id != ? OR section_id NOT IN (?,...)
READ: SELECT * FROM library_sections WHERE section_id = ? AND server_id = ?
READ: SELECT * FROM library_sections WHERE section_type = ? AND deleted_section = 0
READ: SELECT MAX(started) AS last_played, COUNT(DISTINCT ...) AS play_count, rating_key, parent_rating_key, grandparent_rating_key FROM session_history WHERE section_id = ? GROUP BY ...
READ: SELECT library_sections.id AS row_id, ... FROM library_sections LEFT OUTER JOIN session_history ...
READ: SELECT (SUM(stopped - started) - SUM(...paused_counter...)) AS total_time, COUNT(DISTINCT ...) AS total_plays FROM session_history ... WHERE section_id = ?
READ: SELECT (CASE WHEN users.friendly_name ...) ... FROM session_history JOIN session_history_metadata JOIN users WHERE section_id = ? GROUP BY users.user_id
READ: SELECT session_history.id, session_history.media_type, guid, ... FROM session_history_metadata JOIN session_history WHERE section_id = ? GROUP BY session_history.rating_key ORDER BY MAX(started) DESC LIMIT ?
READ: SELECT section_id, section_name, section_type, agent FROM library_sections WHERE deleted_section = 0
WRITE: UPDATE library_sections SET deleted_section = 1, keep_history = 0, do_notify = 0, do_notify_created = 0 WHERE server_id = ? AND section_id = ?
READ: SELECT server_id, section_id FROM library_sections WHERE id IN (?,...)
READ: SELECT * FROM library_sections WHERE section_id = ?
READ: SELECT * FROM library_sections WHERE section_name = ?
DELETE: DELETE FROM library_sections WHERE server_id != ?
```

## plexpy/newsletters.py
```
READ: SELECT newsletters.id, ... MAX(newsletter_log.timestamp) ... FROM newsletters LEFT OUTER JOIN newsletter_log ... GROUP BY newsletters.id
DELETE: DELETE FROM newsletters WHERE id = ?
READ: SELECT * FROM newsletters WHERE id = ?
UPSERT: UPDATE newsletters ...; INSERT INTO newsletters ...
READ: SELECT newsletter_config, email_config FROM newsletters
READ: SELECT EXISTS(SELECT uuid FROM newsletter_log WHERE uuid = ?) AS uuid_exists
```

## plexpy/newsletter_handler.py
```
UPSERT: UPDATE newsletter_log ...; INSERT INTO newsletter_log ...
READ: SELECT email_msg_id FROM newsletter_log WHERE newsletter_id = ? AND notify_action = ? AND success = 1 ORDER BY timestamp DESC LIMIT 1
READ: SELECT start_date, end_date, uuid, filename FROM newsletter_log WHERE uuid = ?
READ: SELECT start_date, end_date, uuid, filename FROM newsletter_log JOIN newsletters ON ... WHERE id_name = ? AND notify_action != 'test' ORDER BY timestamp DESC LIMIT 1
```

## plexpy/exporter.py
```
READ: SELECT timestamp, title, file_format, thumb_level, art_level, logo_level, individual_files, complete FROM exports WHERE id = ?
DELETE: DELETE FROM exports WHERE id = ?
WRITE: UPDATE exports SET complete = -1 WHERE complete = 0
```

## plexpy/plexwatch_import.py
```
READ: SELECT ratingKey FROM {table_name}
READ: SELECT time AS started, stopped, ... FROM {table_name} ORDER BY id
WRITE: INSERT OR IGNORE INTO users (user_id, username) SELECT user_id, user FROM session_history WHERE user_id != 1 GROUP BY user_id
```

## plexpy/plexivity_import.py
```
READ: SELECT xml FROM {table_name}
READ: SELECT id AS id, time AS started, stopped, ... FROM {table_name} ORDER BY id
WRITE: INSERT OR IGNORE INTO users (user_id, username) SELECT user_id, user FROM session_history WHERE user_id != 1 GROUP BY user_id
```

## plexpy/webserve.py
```
TXN: db.connection.execute('begin immediate')
WRITE: UPDATE users SET user_token = NULL, server_token = NULL
```

## api2.py (raw SQL entry point)
```
READ/WRITE: api_sql path accepts raw SQL submitted by client; exact statements are user-provided.
```
