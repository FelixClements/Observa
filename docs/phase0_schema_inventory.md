<!-- Purpose: Capture Phase 0 schema inventory from dbcheck() as a baseline for migration. -->
# Phase 0 Schema Inventory

Source: `plexpy/__init__.py` `dbcheck()`.

Notes
- Column definitions mirror the raw SQLite DDL and ALTER TABLE additions.
- Defaults and UNIQUE constraints are recorded inline where present.
- `session_history_media_info.subtitle_forced` has no explicit type in DDL.

## Validation checklist
- All CREATE TABLE statements from `dbcheck()` captured.
- Index list matches `CREATE INDEX IF NOT EXISTS` block in `dbcheck()`.
- Temp-table rebuilds and data migrations recorded (session history, lookups, users, exports).
- Implicit relationships recorded (session_history ↔ metadata/media_info, users, libraries).

## Tables (CREATE TABLE)

### version_info
PK: none. Unique: `key`.
Columns:
```
key TEXT UNIQUE
value TEXT
```

### sessions
PK: `id INTEGER PRIMARY KEY AUTOINCREMENT`.
Columns:
```
id INTEGER PRIMARY KEY AUTOINCREMENT
session_key INTEGER
session_id TEXT
transcode_key TEXT
rating_key INTEGER
section_id INTEGER
media_type TEXT
started INTEGER
stopped INTEGER
paused_counter INTEGER DEFAULT 0
state TEXT
user_id INTEGER
user TEXT
friendly_name TEXT
ip_address TEXT
machine_id TEXT
bandwidth INTEGER
location TEXT
player TEXT
product TEXT
platform TEXT
title TEXT
parent_title TEXT
grandparent_title TEXT
original_title TEXT
full_title TEXT
media_index INTEGER
parent_media_index INTEGER
thumb TEXT
parent_thumb TEXT
grandparent_thumb TEXT
year INTEGER
parent_rating_key INTEGER
grandparent_rating_key INTEGER
originally_available_at TEXT
added_at INTEGER
guid TEXT
view_offset INTEGER DEFAULT 0
duration INTEGER
video_decision TEXT
audio_decision TEXT
transcode_decision TEXT
container TEXT
bitrate INTEGER
width INTEGER
height INTEGER
video_codec TEXT
video_bitrate INTEGER
video_resolution TEXT
video_width INTEGER
video_height INTEGER
video_framerate TEXT
video_scan_type TEXT
video_full_resolution TEXT
video_dynamic_range TEXT
aspect_ratio TEXT
audio_codec TEXT
audio_bitrate INTEGER
audio_channels INTEGER
audio_language TEXT
audio_language_code TEXT
subtitle_codec TEXT
subtitle_forced INTEGER
subtitle_language TEXT
stream_bitrate INTEGER
stream_video_resolution TEXT
quality_profile TEXT
stream_container_decision TEXT
stream_container TEXT
stream_video_decision TEXT
stream_video_codec TEXT
stream_video_bitrate INTEGER
stream_video_width INTEGER
stream_video_height INTEGER
stream_video_framerate TEXT
stream_video_scan_type TEXT
stream_video_full_resolution TEXT
stream_video_dynamic_range TEXT
stream_audio_decision TEXT
stream_audio_codec TEXT
stream_audio_bitrate INTEGER
stream_audio_channels INTEGER
stream_audio_language TEXT
stream_audio_language_code TEXT
subtitles INTEGER
stream_subtitle_decision TEXT
stream_subtitle_codec TEXT
stream_subtitle_forced INTEGER
stream_subtitle_language TEXT
transcode_protocol TEXT
transcode_container TEXT
transcode_video_codec TEXT
transcode_audio_codec TEXT
transcode_audio_channels INTEGER
transcode_width INTEGER
transcode_height INTEGER
transcode_hw_decoding INTEGER
transcode_hw_encoding INTEGER
optimized_version INTEGER
optimized_version_profile TEXT
optimized_version_title TEXT
synced_version INTEGER
synced_version_profile TEXT
live INTEGER
live_uuid TEXT
channel_call_sign TEXT
channel_id TEXT
channel_identifier TEXT
channel_title TEXT
channel_thumb TEXT
channel_vcn TEXT
secure INTEGER
relayed INTEGER
buffer_count INTEGER DEFAULT 0
buffer_last_triggered INTEGER
last_paused INTEGER
watched INTEGER DEFAULT 0
intro INTEGER DEFAULT 0
credits INTEGER DEFAULT 0
commercial INTEGER DEFAULT 0
marker INTEGER DEFAULT 0
initial_stream INTEGER DEFAULT 1
write_attempts INTEGER DEFAULT 0
raw_stream_info TEXT
rating_key_websocket TEXT
```

### sessions_continued
PK: `id INTEGER PRIMARY KEY AUTOINCREMENT`.
Columns:
```
id INTEGER PRIMARY KEY AUTOINCREMENT
user_id INTEGER
machine_id TEXT
media_type TEXT
stopped INTEGER
```

### session_history
PK: `id INTEGER PRIMARY KEY AUTOINCREMENT`.
Columns:
```
id INTEGER PRIMARY KEY AUTOINCREMENT
reference_id INTEGER
started INTEGER
stopped INTEGER
rating_key INTEGER
user_id INTEGER
user TEXT
ip_address TEXT
paused_counter INTEGER DEFAULT 0
player TEXT
product TEXT
product_version TEXT
platform TEXT
platform_version TEXT
profile TEXT
machine_id TEXT
bandwidth INTEGER
location TEXT
quality_profile TEXT
secure INTEGER
relayed INTEGER
parent_rating_key INTEGER
grandparent_rating_key INTEGER
media_type TEXT
section_id INTEGER
view_offset INTEGER DEFAULT 0
```

### session_history_media_info
PK: `id INTEGER PRIMARY KEY`.
Columns:
```
id INTEGER PRIMARY KEY
rating_key INTEGER
video_decision TEXT
audio_decision TEXT
transcode_decision TEXT
duration INTEGER DEFAULT 0
container TEXT
bitrate INTEGER
width INTEGER
height INTEGER
video_bitrate INTEGER
video_bit_depth INTEGER
video_codec TEXT
video_codec_level TEXT
video_width INTEGER
video_height INTEGER
video_resolution TEXT
video_framerate TEXT
video_scan_type TEXT
video_full_resolution TEXT
video_dynamic_range TEXT
aspect_ratio TEXT
audio_bitrate INTEGER
audio_codec TEXT
audio_channels INTEGER
audio_language TEXT
audio_language_code TEXT
subtitles INTEGER
subtitle_codec TEXT
subtitle_forced
subtitle_language TEXT
transcode_protocol TEXT
transcode_container TEXT
transcode_video_codec TEXT
transcode_audio_codec TEXT
transcode_audio_channels INTEGER
transcode_width INTEGER
transcode_height INTEGER
transcode_hw_requested INTEGER
transcode_hw_full_pipeline INTEGER
transcode_hw_decode TEXT
transcode_hw_decode_title TEXT
transcode_hw_decoding INTEGER
transcode_hw_encode TEXT
transcode_hw_encode_title TEXT
transcode_hw_encoding INTEGER
stream_container TEXT
stream_container_decision TEXT
stream_bitrate INTEGER
stream_video_decision TEXT
stream_video_bitrate INTEGER
stream_video_codec TEXT
stream_video_codec_level TEXT
stream_video_bit_depth INTEGER
stream_video_height INTEGER
stream_video_width INTEGER
stream_video_resolution TEXT
stream_video_framerate TEXT
stream_video_scan_type TEXT
stream_video_full_resolution TEXT
stream_video_dynamic_range TEXT
stream_audio_decision TEXT
stream_audio_codec TEXT
stream_audio_bitrate INTEGER
stream_audio_channels INTEGER
stream_audio_language TEXT
stream_audio_language_code TEXT
stream_subtitle_decision TEXT
stream_subtitle_codec TEXT
stream_subtitle_container TEXT
stream_subtitle_forced INTEGER
stream_subtitle_language TEXT
synced_version INTEGER
synced_version_profile TEXT
optimized_version INTEGER
optimized_version_profile TEXT
optimized_version_title TEXT
```

### session_history_metadata
PK: `id INTEGER PRIMARY KEY`.
Columns:
```
id INTEGER PRIMARY KEY
rating_key INTEGER
parent_rating_key INTEGER
grandparent_rating_key INTEGER
title TEXT
parent_title TEXT
grandparent_title TEXT
original_title TEXT
full_title TEXT
media_index INTEGER
parent_media_index INTEGER
thumb TEXT
parent_thumb TEXT
grandparent_thumb TEXT
art TEXT
media_type TEXT
year INTEGER
originally_available_at TEXT
added_at INTEGER
updated_at INTEGER
last_viewed_at INTEGER
content_rating TEXT
summary TEXT
tagline TEXT
rating TEXT
duration INTEGER DEFAULT 0
guid TEXT
directors TEXT
writers TEXT
actors TEXT
genres TEXT
studio TEXT
labels TEXT
live INTEGER DEFAULT 0
channel_call_sign TEXT
channel_id TEXT
channel_identifier TEXT
channel_title TEXT
channel_thumb TEXT
channel_vcn TEXT
marker_credits_first INTEGER DEFAULT NULL
marker_credits_final INTEGER DEFAULT NULL
```

### users
PK: `id INTEGER PRIMARY KEY AUTOINCREMENT`. Unique: `user_id`.
Columns:
```
id INTEGER PRIMARY KEY AUTOINCREMENT
user_id INTEGER DEFAULT NULL UNIQUE
username TEXT NOT NULL
friendly_name TEXT
thumb TEXT
custom_avatar_url TEXT
title TEXT
email TEXT
is_active INTEGER DEFAULT 1
is_admin INTEGER DEFAULT 0
is_home_user INTEGER DEFAULT NULL
is_allow_sync INTEGER DEFAULT NULL
is_restricted INTEGER DEFAULT NULL
do_notify INTEGER DEFAULT 1
keep_history INTEGER DEFAULT 1
deleted_user INTEGER DEFAULT 0
allow_guest INTEGER DEFAULT 0
user_token TEXT
server_token TEXT
shared_libraries TEXT
filter_all TEXT
filter_movies TEXT
filter_tv TEXT
filter_music TEXT
filter_photos TEXT
```

### library_sections
PK: `id INTEGER PRIMARY KEY AUTOINCREMENT`. Unique: `(server_id, section_id)`.
Columns:
```
id INTEGER PRIMARY KEY AUTOINCREMENT
server_id TEXT
section_id INTEGER
section_name TEXT
section_type TEXT
agent TEXT
thumb TEXT
custom_thumb_url TEXT
art TEXT
custom_art_url TEXT
count INTEGER
parent_count INTEGER
child_count INTEGER
is_active INTEGER DEFAULT 1
do_notify INTEGER DEFAULT 1
do_notify_created INTEGER DEFAULT 1
keep_history INTEGER DEFAULT 1
deleted_section INTEGER DEFAULT 0
```

### user_login
PK: `id INTEGER PRIMARY KEY AUTOINCREMENT`.
Columns:
```
id INTEGER PRIMARY KEY AUTOINCREMENT
timestamp INTEGER
user_id INTEGER
user TEXT
user_group TEXT
ip_address TEXT
host TEXT
user_agent TEXT
success INTEGER DEFAULT 1
expiry TEXT
jwt_token TEXT
```

### notifiers
PK: `id INTEGER PRIMARY KEY AUTOINCREMENT`.
Columns:
```
id INTEGER PRIMARY KEY AUTOINCREMENT
agent_id INTEGER
agent_name TEXT
agent_label TEXT
friendly_name TEXT
notifier_config TEXT
on_play INTEGER DEFAULT 0
on_stop INTEGER DEFAULT 0
on_pause INTEGER DEFAULT 0
on_resume INTEGER DEFAULT 0
on_change INTEGER DEFAULT 0
on_buffer INTEGER DEFAULT 0
on_error INTEGER DEFAULT 0
on_intro INTEGER DEFAULT 0
on_credits INTEGER DEFAULT 0
on_commercial INTEGER DEFAULT 0
on_watched INTEGER DEFAULT 0
on_created INTEGER DEFAULT 0
on_extdown INTEGER DEFAULT 0
on_intdown INTEGER DEFAULT 0
on_extup INTEGER DEFAULT 0
on_intup INTEGER DEFAULT 0
on_pmsupdate INTEGER DEFAULT 0
on_concurrent INTEGER DEFAULT 0
on_newdevice INTEGER DEFAULT 0
on_plexpyupdate INTEGER DEFAULT 0
on_plexpydbcorrupt INTEGER DEFAULT 0
on_tokenexpired INTEGER DEFAULT 0
on_play_subject TEXT
on_stop_subject TEXT
on_pause_subject TEXT
on_resume_subject TEXT
on_change_subject TEXT
on_buffer_subject TEXT
on_error_subject TEXT
on_intro_subject TEXT
on_credits_subject TEXT
on_commercial_subject TEXT
on_watched_subject TEXT
on_created_subject TEXT
on_extdown_subject TEXT
on_intdown_subject TEXT
on_extup_subject TEXT
on_intup_subject TEXT
on_pmsupdate_subject TEXT
on_concurrent_subject TEXT
on_newdevice_subject TEXT
on_plexpyupdate_subject TEXT
on_plexpydbcorrupt_subject TEXT
on_tokenexpired_subject TEXT
on_play_body TEXT
on_stop_body TEXT
on_pause_body TEXT
on_resume_body TEXT
on_change_body TEXT
on_buffer_body TEXT
on_error_body TEXT
on_intro_body TEXT
on_credits_body TEXT
on_commercial_body TEXT
on_watched_body TEXT
on_created_body TEXT
on_extdown_body TEXT
on_intdown_body TEXT
on_extup_body TEXT
on_intup_body TEXT
on_pmsupdate_body TEXT
on_concurrent_body TEXT
on_newdevice_body TEXT
on_plexpyupdate_body TEXT
on_plexpydbcorrupt_body TEXT
on_tokenexpired_body TEXT
custom_conditions TEXT
custom_conditions_logic TEXT
```

### notify_log
PK: `id INTEGER PRIMARY KEY AUTOINCREMENT`.
Columns:
```
id INTEGER PRIMARY KEY AUTOINCREMENT
timestamp INTEGER
session_key INTEGER
rating_key INTEGER
parent_rating_key INTEGER
grandparent_rating_key INTEGER
user_id INTEGER
user TEXT
notifier_id INTEGER
agent_id INTEGER
agent_name TEXT
notify_action TEXT
subject_text TEXT
body_text TEXT
script_args TEXT
success INTEGER DEFAULT 0
tag TEXT
```

### newsletters
PK: `id INTEGER PRIMARY KEY AUTOINCREMENT`.
Columns:
```
id INTEGER PRIMARY KEY AUTOINCREMENT
agent_id INTEGER
agent_name TEXT
agent_label TEXT
id_name TEXT NOT NULL
friendly_name TEXT
newsletter_config TEXT
email_config TEXT
subject TEXT
body TEXT
message TEXT
cron TEXT NOT NULL DEFAULT '0 0 * * 0'
active INTEGER DEFAULT 0
```

### newsletter_log
PK: `id INTEGER PRIMARY KEY AUTOINCREMENT`. Unique: `uuid`.
Columns:
```
id INTEGER PRIMARY KEY AUTOINCREMENT
timestamp INTEGER
newsletter_id INTEGER
agent_id INTEGER
agent_name TEXT
notify_action TEXT
subject_text TEXT
body_text TEXT
message_text TEXT
start_date TEXT
end_date TEXT
start_time INTEGER
end_time INTEGER
uuid TEXT UNIQUE
filename TEXT
email_msg_id TEXT
success INTEGER DEFAULT 0
```

### recently_added
PK: `id INTEGER PRIMARY KEY AUTOINCREMENT`.
Columns:
```
id INTEGER PRIMARY KEY AUTOINCREMENT
added_at INTEGER
pms_identifier TEXT
section_id INTEGER
rating_key INTEGER
parent_rating_key INTEGER
grandparent_rating_key INTEGER
media_type TEXT
media_info TEXT
```

### mobile_devices
PK: `id INTEGER PRIMARY KEY AUTOINCREMENT`. Unique: `device_id`.
Columns:
```
id INTEGER PRIMARY KEY AUTOINCREMENT
device_id TEXT NOT NULL UNIQUE
device_token TEXT
device_name TEXT
platform TEXT
version TEXT
friendly_name TEXT
onesignal_id TEXT
last_seen INTEGER
official INTEGER DEFAULT 0
```

### tvmaze_lookup
PK: `id INTEGER PRIMARY KEY AUTOINCREMENT`.
Columns:
```
id INTEGER PRIMARY KEY AUTOINCREMENT
rating_key INTEGER
thetvdb_id INTEGER
imdb_id TEXT
tvmaze_id INTEGER
tvmaze_url TEXT
tvmaze_json TEXT
```

### themoviedb_lookup
PK: `id INTEGER PRIMARY KEY AUTOINCREMENT`.
Columns:
```
id INTEGER PRIMARY KEY AUTOINCREMENT
rating_key INTEGER
thetvdb_id INTEGER
imdb_id TEXT
themoviedb_id INTEGER
themoviedb_url TEXT
themoviedb_json TEXT
```

### musicbrainz_lookup
PK: `id INTEGER PRIMARY KEY AUTOINCREMENT`.
Columns:
```
id INTEGER PRIMARY KEY AUTOINCREMENT
rating_key INTEGER
musicbrainz_id INTEGER
musicbrainz_url TEXT
musicbrainz_type TEXT
musicbrainz_json TEXT
```

### image_hash_lookup
PK: `id INTEGER PRIMARY KEY AUTOINCREMENT`. Unique: `img_hash`.
Columns:
```
id INTEGER PRIMARY KEY AUTOINCREMENT
img_hash TEXT UNIQUE
img TEXT
rating_key INTEGER
width INTEGER
height INTEGER
opacity INTEGER
background TEXT
blur INTEGER
fallback TEXT
```

### imgur_lookup
PK: `id INTEGER PRIMARY KEY AUTOINCREMENT`.
Columns:
```
id INTEGER PRIMARY KEY AUTOINCREMENT
img_hash TEXT
imgur_title TEXT
imgur_url TEXT
delete_hash TEXT
```

### cloudinary_lookup
PK: `id INTEGER PRIMARY KEY AUTOINCREMENT`.
Columns:
```
id INTEGER PRIMARY KEY AUTOINCREMENT
img_hash TEXT
cloudinary_title TEXT
cloudinary_url TEXT
```

### exports
PK: `id INTEGER PRIMARY KEY AUTOINCREMENT`.
Columns:
```
id INTEGER PRIMARY KEY AUTOINCREMENT
timestamp INTEGER
section_id INTEGER
user_id INTEGER
rating_key INTEGER
media_type TEXT
title TEXT
file_format TEXT
metadata_level INTEGER
media_info_level INTEGER
thumb_level INTEGER DEFAULT 0
art_level INTEGER DEFAULT 0
logo_level INTEGER DEFAULT 0
custom_fields TEXT
individual_files INTEGER DEFAULT 0
file_size INTEGER DEFAULT 0
complete INTEGER DEFAULT 0
exported_items INTEGER DEFAULT 0
total_items INTEGER DEFAULT 0
```

## Indexes (CREATE INDEX)

Session history:
```
idx_session_history_media_type ON session_history (media_type)
idx_session_history_media_type_stopped ON session_history (media_type, stopped ASC)
idx_session_history_rating_key ON session_history (rating_key)
idx_session_history_parent_rating_key ON session_history (parent_rating_key)
idx_session_history_grandparent_rating_key ON session_history (grandparent_rating_key)
idx_session_history_user ON session_history (user)
idx_session_history_user_id ON session_history (user_id)
idx_session_history_user_id_stopped ON session_history (user_id, stopped ASC)
idx_session_history_section_id ON session_history (section_id)
idx_session_history_section_id_stopped ON session_history (section_id, stopped ASC)
idx_session_history_reference_id ON session_history (reference_id ASC)
```

Session history metadata:
```
idx_session_history_metadata_rating_key ON session_history_metadata (rating_key)
idx_session_history_metadata_guid ON session_history_metadata (guid)
idx_session_history_metadata_live ON session_history_metadata (live)
```

Session history media info:
```
idx_session_history_media_info_transcode_decision ON session_history_media_info (transcode_decision)
```

Lookup tables:
```
idx_tvmaze_lookup ON tvmaze_lookup (rating_key) UNIQUE
idx_themoviedb_lookup ON themoviedb_lookup (rating_key) UNIQUE
idx_musicbrainz_lookup ON musicbrainz_lookup (rating_key) UNIQUE
idx_image_hash_lookup ON image_hash_lookup (img_hash) UNIQUE
idx_cloudinary_lookup ON cloudinary_lookup (img_hash) UNIQUE
idx_imgur_lookup ON imgur_lookup (img_hash) UNIQUE
idx_sessions_continued ON sessions_continued (user_id, machine_id, media_type) UNIQUE
```

## Implicit relationships

`session_history` to `session_history_metadata` and `session_history_media_info`:
```
session_history.id == session_history_metadata.id
session_history.id == session_history_media_info.id
```

Rating key associations:
```
session_history.rating_key == session_history_metadata.rating_key
session_history_media_info.rating_key == session_history_metadata.rating_key
```

User/library associations:
```
session_history.user_id == users.user_id
session_history.section_id == library_sections.section_id
```

## Data migrations and rebuilds (dbcheck)

`session_history`
```
UPDATE session_history SET reference_id = (CASE ...)
UPDATE session_history SET platform = 'Windows' WHERE platform = 'windows'
UPDATE session_history SET platform = 'macOS' WHERE platform = 'macos'
UPDATE session_history SET section_id = (SELECT section_id FROM session_history_metadata ...)
```

`session_history_media_info`
```
UPDATE session_history_media_info SET transcode_decision = (CASE ...)
UPDATE session_history_media_info SET video_resolution = REPLACE(...)
UPDATE session_history_media_info SET subtitle_codec = '' WHERE subtitle_codec IS NULL
UPDATE session_history_media_info SET stream_container = '' WHERE stream_container IS NULL
UPDATE session_history_media_info SET stream_video_codec = '' WHERE stream_video_codec IS NULL
UPDATE session_history_media_info SET stream_audio_codec = '' WHERE stream_audio_codec IS NULL
UPDATE session_history_media_info SET stream_subtitle_codec = '' WHERE stream_subtitle_codec IS NULL
UPDATE session_history_media_info SET video_scan_type = 'progressive' WHERE video_scan_type IS NULL
UPDATE session_history_media_info SET video_full_resolution = (CASE ...)
UPDATE session_history_media_info SET stream_video_dynamic_range = 'SDR' WHERE ...
```

`users`
```
UPDATE users SET friendly_name = NULL WHERE friendly_name = username
INSERT INTO users (user_id, username) VALUES (0, 'Local')
```

`notify_log`
```
UPDATE notify_log SET success = 1
```

`library_sections`
```
DELETE FROM library_sections WHERE server_id = ''
```

`exports`
```
UPDATE exports SET thumb_level = 9 WHERE include_thumb = 1
UPDATE exports SET art_level = 9 WHERE include_art = 1
```

Lookup table dedupe
```
DELETE FROM tvmaze_lookup WHERE id NOT IN (SELECT MIN(id) FROM tvmaze_lookup GROUP BY rating_key)
DELETE FROM themoviedb_lookup WHERE id NOT IN (SELECT MIN(id) FROM themoviedb_lookup GROUP BY rating_key)
DELETE FROM musicbrainz_lookup WHERE id NOT IN (SELECT MIN(id) FROM musicbrainz_lookup GROUP BY rating_key)
DELETE FROM image_hash_lookup WHERE id NOT IN (SELECT MIN(id) FROM image_hash_lookup GROUP BY img_hash)
DELETE FROM cloudinary_lookup WHERE id NOT IN (SELECT MIN(id) FROM cloudinary_lookup GROUP BY img_hash)
DELETE FROM imgur_lookup WHERE id NOT IN (SELECT MIN(id) FROM imgur_lookup GROUP BY img_hash)
```

Rebuilds via temp tables
```
session_history_metadata_temp (rebuild with section_id migration)
notify_log_temp (rebuild notify_log)
newsletters_temp (rebuild newsletters for cron default)
library_sections_temp (rebuild to adjust unique constraint)
users_temp (rebuild to drop username unique constraint)
```

## Temp tables used in migrations

See "Rebuilds via temp tables" in the data migrations section above.
