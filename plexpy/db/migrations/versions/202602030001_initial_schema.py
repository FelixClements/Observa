"""Initial schema.

Revision ID: 202602030001
Revises:
Create Date: 2026-02-03 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = '202602030001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'version_info',
        sa.Column('key', sa.Text(), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('key', name='pk_version_info'),
    )

    op.create_table(
        'sessions',
        sa.Column('id', sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column('session_key', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.Text(), nullable=True),
        sa.Column('transcode_key', sa.Text(), nullable=True),
        sa.Column('rating_key', sa.Integer(), nullable=True),
        sa.Column('section_id', sa.Integer(), nullable=True),
        sa.Column('media_type', sa.Text(), nullable=True),
        sa.Column('started', sa.Integer(), nullable=True),
        sa.Column('stopped', sa.Integer(), nullable=True),
        sa.Column('paused_counter', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('state', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('user', sa.Text(), nullable=True),
        sa.Column('friendly_name', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.Text(), nullable=True),
        sa.Column('machine_id', sa.Text(), nullable=True),
        sa.Column('bandwidth', sa.Integer(), nullable=True),
        sa.Column('location', sa.Text(), nullable=True),
        sa.Column('player', sa.Text(), nullable=True),
        sa.Column('product', sa.Text(), nullable=True),
        sa.Column('platform', sa.Text(), nullable=True),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('parent_title', sa.Text(), nullable=True),
        sa.Column('grandparent_title', sa.Text(), nullable=True),
        sa.Column('original_title', sa.Text(), nullable=True),
        sa.Column('full_title', sa.Text(), nullable=True),
        sa.Column('media_index', sa.Integer(), nullable=True),
        sa.Column('parent_media_index', sa.Integer(), nullable=True),
        sa.Column('thumb', sa.Text(), nullable=True),
        sa.Column('parent_thumb', sa.Text(), nullable=True),
        sa.Column('grandparent_thumb', sa.Text(), nullable=True),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('parent_rating_key', sa.Integer(), nullable=True),
        sa.Column('grandparent_rating_key', sa.Integer(), nullable=True),
        sa.Column('originally_available_at', sa.Text(), nullable=True),
        sa.Column('added_at', sa.Integer(), nullable=True),
        sa.Column('guid', sa.Text(), nullable=True),
        sa.Column('view_offset', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('video_decision', sa.Text(), nullable=True),
        sa.Column('audio_decision', sa.Text(), nullable=True),
        sa.Column('transcode_decision', sa.Text(), nullable=True),
        sa.Column('container', sa.Text(), nullable=True),
        sa.Column('bitrate', sa.Integer(), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('video_codec', sa.Text(), nullable=True),
        sa.Column('video_bitrate', sa.Integer(), nullable=True),
        sa.Column('video_resolution', sa.Text(), nullable=True),
        sa.Column('video_width', sa.Integer(), nullable=True),
        sa.Column('video_height', sa.Integer(), nullable=True),
        sa.Column('video_framerate', sa.Text(), nullable=True),
        sa.Column('video_scan_type', sa.Text(), nullable=True),
        sa.Column('video_full_resolution', sa.Text(), nullable=True),
        sa.Column('video_dynamic_range', sa.Text(), nullable=True),
        sa.Column('aspect_ratio', sa.Text(), nullable=True),
        sa.Column('audio_codec', sa.Text(), nullable=True),
        sa.Column('audio_bitrate', sa.Integer(), nullable=True),
        sa.Column('audio_channels', sa.Integer(), nullable=True),
        sa.Column('audio_language', sa.Text(), nullable=True),
        sa.Column('audio_language_code', sa.Text(), nullable=True),
        sa.Column('subtitle_codec', sa.Text(), nullable=True),
        sa.Column('subtitle_forced', sa.Integer(), nullable=True),
        sa.Column('subtitle_language', sa.Text(), nullable=True),
        sa.Column('stream_bitrate', sa.Integer(), nullable=True),
        sa.Column('stream_video_resolution', sa.Text(), nullable=True),
        sa.Column('quality_profile', sa.Text(), nullable=True),
        sa.Column('stream_container_decision', sa.Text(), nullable=True),
        sa.Column('stream_container', sa.Text(), nullable=True),
        sa.Column('stream_video_decision', sa.Text(), nullable=True),
        sa.Column('stream_video_codec', sa.Text(), nullable=True),
        sa.Column('stream_video_bitrate', sa.Integer(), nullable=True),
        sa.Column('stream_video_width', sa.Integer(), nullable=True),
        sa.Column('stream_video_height', sa.Integer(), nullable=True),
        sa.Column('stream_video_framerate', sa.Text(), nullable=True),
        sa.Column('stream_video_scan_type', sa.Text(), nullable=True),
        sa.Column('stream_video_full_resolution', sa.Text(), nullable=True),
        sa.Column('stream_video_dynamic_range', sa.Text(), nullable=True),
        sa.Column('stream_audio_decision', sa.Text(), nullable=True),
        sa.Column('stream_audio_codec', sa.Text(), nullable=True),
        sa.Column('stream_audio_bitrate', sa.Integer(), nullable=True),
        sa.Column('stream_audio_channels', sa.Integer(), nullable=True),
        sa.Column('stream_audio_language', sa.Text(), nullable=True),
        sa.Column('stream_audio_language_code', sa.Text(), nullable=True),
        sa.Column('subtitles', sa.Integer(), nullable=True),
        sa.Column('stream_subtitle_decision', sa.Text(), nullable=True),
        sa.Column('stream_subtitle_codec', sa.Text(), nullable=True),
        sa.Column('stream_subtitle_forced', sa.Integer(), nullable=True),
        sa.Column('stream_subtitle_language', sa.Text(), nullable=True),
        sa.Column('transcode_protocol', sa.Text(), nullable=True),
        sa.Column('transcode_container', sa.Text(), nullable=True),
        sa.Column('transcode_video_codec', sa.Text(), nullable=True),
        sa.Column('transcode_audio_codec', sa.Text(), nullable=True),
        sa.Column('transcode_audio_channels', sa.Integer(), nullable=True),
        sa.Column('transcode_width', sa.Integer(), nullable=True),
        sa.Column('transcode_height', sa.Integer(), nullable=True),
        sa.Column('transcode_hw_decoding', sa.Integer(), nullable=True),
        sa.Column('transcode_hw_encoding', sa.Integer(), nullable=True),
        sa.Column('optimized_version', sa.Integer(), nullable=True),
        sa.Column('optimized_version_profile', sa.Text(), nullable=True),
        sa.Column('optimized_version_title', sa.Text(), nullable=True),
        sa.Column('synced_version', sa.Integer(), nullable=True),
        sa.Column('synced_version_profile', sa.Text(), nullable=True),
        sa.Column('live', sa.Integer(), nullable=True),
        sa.Column('live_uuid', sa.Text(), nullable=True),
        sa.Column('channel_call_sign', sa.Text(), nullable=True),
        sa.Column('channel_id', sa.Text(), nullable=True),
        sa.Column('channel_identifier', sa.Text(), nullable=True),
        sa.Column('channel_title', sa.Text(), nullable=True),
        sa.Column('channel_thumb', sa.Text(), nullable=True),
        sa.Column('channel_vcn', sa.Text(), nullable=True),
        sa.Column('secure', sa.Integer(), nullable=True),
        sa.Column('relayed', sa.Integer(), nullable=True),
        sa.Column('buffer_count', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('buffer_last_triggered', sa.Integer(), nullable=True),
        sa.Column('last_paused', sa.Integer(), nullable=True),
        sa.Column('watched', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('intro', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('credits', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('commercial', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('marker', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('initial_stream', sa.Integer(), server_default=sa.text('1'), nullable=True),
        sa.Column('write_attempts', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('raw_stream_info', sa.Text(), nullable=True),
        sa.Column('rating_key_websocket', sa.Text(), nullable=True),
        sa.UniqueConstraint('session_key', name='idx_sessions_session_key'),
        sa.PrimaryKeyConstraint('id', name='pk_sessions'),
    )

    op.create_table(
        'sessions_continued',
        sa.Column('id', sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('machine_id', sa.Text(), nullable=True),
        sa.Column('media_type', sa.Text(), nullable=True),
        sa.Column('stopped', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_sessions_continued'),
        sa.UniqueConstraint('user_id', 'machine_id', 'media_type', name='idx_sessions_continued'),
    )

    op.create_table(
        'session_history',
        sa.Column('id', sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('started', sa.Integer(), nullable=True),
        sa.Column('stopped', sa.Integer(), nullable=True),
        sa.Column('rating_key', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('user', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.Text(), nullable=True),
        sa.Column('paused_counter', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('player', sa.Text(), nullable=True),
        sa.Column('product', sa.Text(), nullable=True),
        sa.Column('product_version', sa.Text(), nullable=True),
        sa.Column('platform', sa.Text(), nullable=True),
        sa.Column('platform_version', sa.Text(), nullable=True),
        sa.Column('profile', sa.Text(), nullable=True),
        sa.Column('machine_id', sa.Text(), nullable=True),
        sa.Column('bandwidth', sa.Integer(), nullable=True),
        sa.Column('location', sa.Text(), nullable=True),
        sa.Column('quality_profile', sa.Text(), nullable=True),
        sa.Column('secure', sa.Integer(), nullable=True),
        sa.Column('relayed', sa.Integer(), nullable=True),
        sa.Column('parent_rating_key', sa.Integer(), nullable=True),
        sa.Column('grandparent_rating_key', sa.Integer(), nullable=True),
        sa.Column('media_type', sa.Text(), nullable=True),
        sa.Column('section_id', sa.Integer(), nullable=True),
        sa.Column('view_offset', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_session_history'),
    )
    op.create_index('idx_session_history_media_type', 'session_history', ['media_type'], unique=False)
    op.create_index('idx_session_history_media_type_stopped', 'session_history', ['media_type', 'stopped'], unique=False)
    op.create_index('idx_session_history_rating_key', 'session_history', ['rating_key'], unique=False)
    op.create_index('idx_session_history_parent_rating_key', 'session_history', ['parent_rating_key'], unique=False)
    op.create_index('idx_session_history_grandparent_rating_key', 'session_history', ['grandparent_rating_key'], unique=False)
    op.create_index('idx_session_history_user', 'session_history', ['user'], unique=False)
    op.create_index('idx_session_history_user_id', 'session_history', ['user_id'], unique=False)
    op.create_index('idx_session_history_user_id_stopped', 'session_history', ['user_id', 'stopped'], unique=False)
    op.create_index('idx_session_history_section_id', 'session_history', ['section_id'], unique=False)
    op.create_index('idx_session_history_section_id_stopped', 'session_history', ['section_id', 'stopped'], unique=False)
    op.create_index('idx_session_history_reference_id', 'session_history', ['reference_id'], unique=False)

    op.create_table(
        'session_history_media_info',
        sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('rating_key', sa.Integer(), nullable=True),
        sa.Column('video_decision', sa.Text(), nullable=True),
        sa.Column('audio_decision', sa.Text(), nullable=True),
        sa.Column('transcode_decision', sa.Text(), nullable=True),
        sa.Column('duration', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('container', sa.Text(), nullable=True),
        sa.Column('bitrate', sa.Integer(), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('video_bitrate', sa.Integer(), nullable=True),
        sa.Column('video_bit_depth', sa.Integer(), nullable=True),
        sa.Column('video_codec', sa.Text(), nullable=True),
        sa.Column('video_codec_level', sa.Text(), nullable=True),
        sa.Column('video_width', sa.Integer(), nullable=True),
        sa.Column('video_height', sa.Integer(), nullable=True),
        sa.Column('video_resolution', sa.Text(), nullable=True),
        sa.Column('video_framerate', sa.Text(), nullable=True),
        sa.Column('video_scan_type', sa.Text(), nullable=True),
        sa.Column('video_full_resolution', sa.Text(), nullable=True),
        sa.Column('video_dynamic_range', sa.Text(), nullable=True),
        sa.Column('aspect_ratio', sa.Text(), nullable=True),
        sa.Column('audio_bitrate', sa.Integer(), nullable=True),
        sa.Column('audio_codec', sa.Text(), nullable=True),
        sa.Column('audio_channels', sa.Integer(), nullable=True),
        sa.Column('audio_language', sa.Text(), nullable=True),
        sa.Column('audio_language_code', sa.Text(), nullable=True),
        sa.Column('subtitles', sa.Integer(), nullable=True),
        sa.Column('subtitle_codec', sa.Text(), nullable=True),
        sa.Column('subtitle_forced', sa.Integer(), nullable=True),
        sa.Column('subtitle_language', sa.Text(), nullable=True),
        sa.Column('transcode_protocol', sa.Text(), nullable=True),
        sa.Column('transcode_container', sa.Text(), nullable=True),
        sa.Column('transcode_video_codec', sa.Text(), nullable=True),
        sa.Column('transcode_audio_codec', sa.Text(), nullable=True),
        sa.Column('transcode_audio_channels', sa.Integer(), nullable=True),
        sa.Column('transcode_width', sa.Integer(), nullable=True),
        sa.Column('transcode_height', sa.Integer(), nullable=True),
        sa.Column('transcode_hw_requested', sa.Integer(), nullable=True),
        sa.Column('transcode_hw_full_pipeline', sa.Integer(), nullable=True),
        sa.Column('transcode_hw_decode', sa.Text(), nullable=True),
        sa.Column('transcode_hw_decode_title', sa.Text(), nullable=True),
        sa.Column('transcode_hw_decoding', sa.Integer(), nullable=True),
        sa.Column('transcode_hw_encode', sa.Text(), nullable=True),
        sa.Column('transcode_hw_encode_title', sa.Text(), nullable=True),
        sa.Column('transcode_hw_encoding', sa.Integer(), nullable=True),
        sa.Column('stream_container', sa.Text(), nullable=True),
        sa.Column('stream_container_decision', sa.Text(), nullable=True),
        sa.Column('stream_bitrate', sa.Integer(), nullable=True),
        sa.Column('stream_video_decision', sa.Text(), nullable=True),
        sa.Column('stream_video_bitrate', sa.Integer(), nullable=True),
        sa.Column('stream_video_codec', sa.Text(), nullable=True),
        sa.Column('stream_video_codec_level', sa.Text(), nullable=True),
        sa.Column('stream_video_bit_depth', sa.Integer(), nullable=True),
        sa.Column('stream_video_height', sa.Integer(), nullable=True),
        sa.Column('stream_video_width', sa.Integer(), nullable=True),
        sa.Column('stream_video_resolution', sa.Text(), nullable=True),
        sa.Column('stream_video_framerate', sa.Text(), nullable=True),
        sa.Column('stream_video_scan_type', sa.Text(), nullable=True),
        sa.Column('stream_video_full_resolution', sa.Text(), nullable=True),
        sa.Column('stream_video_dynamic_range', sa.Text(), nullable=True),
        sa.Column('stream_audio_decision', sa.Text(), nullable=True),
        sa.Column('stream_audio_codec', sa.Text(), nullable=True),
        sa.Column('stream_audio_bitrate', sa.Integer(), nullable=True),
        sa.Column('stream_audio_channels', sa.Integer(), nullable=True),
        sa.Column('stream_audio_language', sa.Text(), nullable=True),
        sa.Column('stream_audio_language_code', sa.Text(), nullable=True),
        sa.Column('stream_subtitle_decision', sa.Text(), nullable=True),
        sa.Column('stream_subtitle_codec', sa.Text(), nullable=True),
        sa.Column('stream_subtitle_container', sa.Text(), nullable=True),
        sa.Column('stream_subtitle_forced', sa.Integer(), nullable=True),
        sa.Column('stream_subtitle_language', sa.Text(), nullable=True),
        sa.Column('synced_version', sa.Integer(), nullable=True),
        sa.Column('synced_version_profile', sa.Text(), nullable=True),
        sa.Column('optimized_version', sa.Integer(), nullable=True),
        sa.Column('optimized_version_profile', sa.Text(), nullable=True),
        sa.Column('optimized_version_title', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_session_history_media_info'),
    )
    op.create_index(
        'idx_session_history_media_info_transcode_decision',
        'session_history_media_info',
        ['transcode_decision'],
        unique=False,
    )

    op.create_table(
        'session_history_metadata',
        sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('rating_key', sa.Integer(), nullable=True),
        sa.Column('parent_rating_key', sa.Integer(), nullable=True),
        sa.Column('grandparent_rating_key', sa.Integer(), nullable=True),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('parent_title', sa.Text(), nullable=True),
        sa.Column('grandparent_title', sa.Text(), nullable=True),
        sa.Column('original_title', sa.Text(), nullable=True),
        sa.Column('full_title', sa.Text(), nullable=True),
        sa.Column('media_index', sa.Integer(), nullable=True),
        sa.Column('parent_media_index', sa.Integer(), nullable=True),
        sa.Column('thumb', sa.Text(), nullable=True),
        sa.Column('parent_thumb', sa.Text(), nullable=True),
        sa.Column('grandparent_thumb', sa.Text(), nullable=True),
        sa.Column('art', sa.Text(), nullable=True),
        sa.Column('media_type', sa.Text(), nullable=True),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('originally_available_at', sa.Text(), nullable=True),
        sa.Column('added_at', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.Integer(), nullable=True),
        sa.Column('last_viewed_at', sa.Integer(), nullable=True),
        sa.Column('content_rating', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('tagline', sa.Text(), nullable=True),
        sa.Column('rating', sa.Text(), nullable=True),
        sa.Column('duration', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('guid', sa.Text(), nullable=True),
        sa.Column('directors', sa.Text(), nullable=True),
        sa.Column('writers', sa.Text(), nullable=True),
        sa.Column('actors', sa.Text(), nullable=True),
        sa.Column('genres', sa.Text(), nullable=True),
        sa.Column('studio', sa.Text(), nullable=True),
        sa.Column('labels', sa.Text(), nullable=True),
        sa.Column('live', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('channel_call_sign', sa.Text(), nullable=True),
        sa.Column('channel_id', sa.Text(), nullable=True),
        sa.Column('channel_identifier', sa.Text(), nullable=True),
        sa.Column('channel_title', sa.Text(), nullable=True),
        sa.Column('channel_thumb', sa.Text(), nullable=True),
        sa.Column('channel_vcn', sa.Text(), nullable=True),
        sa.Column('marker_credits_first', sa.Integer(), nullable=True),
        sa.Column('marker_credits_final', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_session_history_metadata'),
    )
    op.create_index(
        'idx_session_history_metadata_rating_key',
        'session_history_metadata',
        ['rating_key'],
        unique=False,
    )
    op.create_index(
        'idx_session_history_metadata_guid',
        'session_history_metadata',
        ['guid'],
        unique=False,
    )
    op.create_index(
        'idx_session_history_metadata_live',
        'session_history_metadata',
        ['live'],
        unique=False,
    )

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('username', sa.Text(), nullable=False),
        sa.Column('friendly_name', sa.Text(), nullable=True),
        sa.Column('thumb', sa.Text(), nullable=True),
        sa.Column('custom_avatar_url', sa.Text(), nullable=True),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('email', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Integer(), server_default=sa.text('1'), nullable=True),
        sa.Column('is_admin', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('is_home_user', sa.Integer(), nullable=True),
        sa.Column('is_allow_sync', sa.Integer(), nullable=True),
        sa.Column('is_restricted', sa.Integer(), nullable=True),
        sa.Column('do_notify', sa.Integer(), server_default=sa.text('1'), nullable=True),
        sa.Column('keep_history', sa.Integer(), server_default=sa.text('1'), nullable=True),
        sa.Column('deleted_user', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('allow_guest', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('user_token', sa.Text(), nullable=True),
        sa.Column('server_token', sa.Text(), nullable=True),
        sa.Column('shared_libraries', sa.Text(), nullable=True),
        sa.Column('filter_all', sa.Text(), nullable=True),
        sa.Column('filter_movies', sa.Text(), nullable=True),
        sa.Column('filter_tv', sa.Text(), nullable=True),
        sa.Column('filter_music', sa.Text(), nullable=True),
        sa.Column('filter_photos', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_users'),
        sa.UniqueConstraint('user_id', name='uq_users_user_id'),
    )

    op.create_table(
        'library_sections',
        sa.Column('id', sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column('server_id', sa.Text(), nullable=True),
        sa.Column('section_id', sa.Integer(), nullable=True),
        sa.Column('section_name', sa.Text(), nullable=True),
        sa.Column('section_type', sa.Text(), nullable=True),
        sa.Column('agent', sa.Text(), nullable=True),
        sa.Column('thumb', sa.Text(), nullable=True),
        sa.Column('custom_thumb_url', sa.Text(), nullable=True),
        sa.Column('art', sa.Text(), nullable=True),
        sa.Column('custom_art_url', sa.Text(), nullable=True),
        sa.Column('count', sa.Integer(), nullable=True),
        sa.Column('parent_count', sa.Integer(), nullable=True),
        sa.Column('child_count', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Integer(), server_default=sa.text('1'), nullable=True),
        sa.Column('do_notify', sa.Integer(), server_default=sa.text('1'), nullable=True),
        sa.Column('do_notify_created', sa.Integer(), server_default=sa.text('1'), nullable=True),
        sa.Column('keep_history', sa.Integer(), server_default=sa.text('1'), nullable=True),
        sa.Column('deleted_section', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_library_sections'),
        sa.UniqueConstraint('server_id', 'section_id', name='uq_library_sections_server_id'),
    )

    op.create_table(
        'user_login',
        sa.Column('id', sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column('timestamp', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('user', sa.Text(), nullable=True),
        sa.Column('user_group', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.Text(), nullable=True),
        sa.Column('host', sa.Text(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('success', sa.Integer(), server_default=sa.text('1'), nullable=True),
        sa.Column('expiry', sa.Text(), nullable=True),
        sa.Column('jwt_token', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_user_login'),
    )

    op.create_table(
        'notifiers',
        sa.Column('id', sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=True),
        sa.Column('agent_name', sa.Text(), nullable=True),
        sa.Column('agent_label', sa.Text(), nullable=True),
        sa.Column('friendly_name', sa.Text(), nullable=True),
        sa.Column('notifier_config', sa.Text(), nullable=True),
        sa.Column('on_play', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('on_stop', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('on_pause', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('on_resume', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('on_change', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('on_buffer', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('on_error', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('on_intro', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('on_credits', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('on_commercial', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('on_watched', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('on_created', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('on_extdown', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('on_intdown', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('on_extup', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('on_intup', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('on_pmsupdate', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('on_concurrent', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('on_newdevice', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('on_plexpyupdate', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('on_plexpydbcorrupt', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('on_tokenexpired', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('on_play_subject', sa.Text(), nullable=True),
        sa.Column('on_stop_subject', sa.Text(), nullable=True),
        sa.Column('on_pause_subject', sa.Text(), nullable=True),
        sa.Column('on_resume_subject', sa.Text(), nullable=True),
        sa.Column('on_change_subject', sa.Text(), nullable=True),
        sa.Column('on_buffer_subject', sa.Text(), nullable=True),
        sa.Column('on_error_subject', sa.Text(), nullable=True),
        sa.Column('on_intro_subject', sa.Text(), nullable=True),
        sa.Column('on_credits_subject', sa.Text(), nullable=True),
        sa.Column('on_commercial_subject', sa.Text(), nullable=True),
        sa.Column('on_watched_subject', sa.Text(), nullable=True),
        sa.Column('on_created_subject', sa.Text(), nullable=True),
        sa.Column('on_extdown_subject', sa.Text(), nullable=True),
        sa.Column('on_intdown_subject', sa.Text(), nullable=True),
        sa.Column('on_extup_subject', sa.Text(), nullable=True),
        sa.Column('on_intup_subject', sa.Text(), nullable=True),
        sa.Column('on_pmsupdate_subject', sa.Text(), nullable=True),
        sa.Column('on_concurrent_subject', sa.Text(), nullable=True),
        sa.Column('on_newdevice_subject', sa.Text(), nullable=True),
        sa.Column('on_plexpyupdate_subject', sa.Text(), nullable=True),
        sa.Column('on_plexpydbcorrupt_subject', sa.Text(), nullable=True),
        sa.Column('on_tokenexpired_subject', sa.Text(), nullable=True),
        sa.Column('on_play_body', sa.Text(), nullable=True),
        sa.Column('on_stop_body', sa.Text(), nullable=True),
        sa.Column('on_pause_body', sa.Text(), nullable=True),
        sa.Column('on_resume_body', sa.Text(), nullable=True),
        sa.Column('on_change_body', sa.Text(), nullable=True),
        sa.Column('on_buffer_body', sa.Text(), nullable=True),
        sa.Column('on_error_body', sa.Text(), nullable=True),
        sa.Column('on_intro_body', sa.Text(), nullable=True),
        sa.Column('on_credits_body', sa.Text(), nullable=True),
        sa.Column('on_commercial_body', sa.Text(), nullable=True),
        sa.Column('on_watched_body', sa.Text(), nullable=True),
        sa.Column('on_created_body', sa.Text(), nullable=True),
        sa.Column('on_extdown_body', sa.Text(), nullable=True),
        sa.Column('on_intdown_body', sa.Text(), nullable=True),
        sa.Column('on_extup_body', sa.Text(), nullable=True),
        sa.Column('on_intup_body', sa.Text(), nullable=True),
        sa.Column('on_pmsupdate_body', sa.Text(), nullable=True),
        sa.Column('on_concurrent_body', sa.Text(), nullable=True),
        sa.Column('on_newdevice_body', sa.Text(), nullable=True),
        sa.Column('on_plexpyupdate_body', sa.Text(), nullable=True),
        sa.Column('on_plexpydbcorrupt_body', sa.Text(), nullable=True),
        sa.Column('on_tokenexpired_body', sa.Text(), nullable=True),
        sa.Column('custom_conditions', sa.Text(), nullable=True),
        sa.Column('custom_conditions_logic', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_notifiers'),
    )

    op.create_table(
        'notify_log',
        sa.Column('id', sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column('timestamp', sa.Integer(), nullable=True),
        sa.Column('session_key', sa.Integer(), nullable=True),
        sa.Column('rating_key', sa.Integer(), nullable=True),
        sa.Column('parent_rating_key', sa.Integer(), nullable=True),
        sa.Column('grandparent_rating_key', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('user', sa.Text(), nullable=True),
        sa.Column('notifier_id', sa.Integer(), nullable=True),
        sa.Column('agent_id', sa.Integer(), nullable=True),
        sa.Column('agent_name', sa.Text(), nullable=True),
        sa.Column('notify_action', sa.Text(), nullable=True),
        sa.Column('subject_text', sa.Text(), nullable=True),
        sa.Column('body_text', sa.Text(), nullable=True),
        sa.Column('script_args', sa.Text(), nullable=True),
        sa.Column('poster_url', sa.Text(), nullable=True),
        sa.Column('success', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('tag', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_notify_log'),
    )

    op.create_table(
        'newsletters',
        sa.Column('id', sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=True),
        sa.Column('agent_name', sa.Text(), nullable=True),
        sa.Column('agent_label', sa.Text(), nullable=True),
        sa.Column('id_name', sa.Text(), nullable=False),
        sa.Column('friendly_name', sa.Text(), nullable=True),
        sa.Column('newsletter_config', sa.Text(), nullable=True),
        sa.Column('email_config', sa.Text(), nullable=True),
        sa.Column('subject', sa.Text(), nullable=True),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('cron', sa.Text(), server_default=sa.text("'0 0 * * 0'"), nullable=False),
        sa.Column('active', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_newsletters'),
    )

    op.create_table(
        'newsletter_log',
        sa.Column('id', sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column('timestamp', sa.Integer(), nullable=True),
        sa.Column('newsletter_id', sa.Integer(), nullable=True),
        sa.Column('agent_id', sa.Integer(), nullable=True),
        sa.Column('agent_name', sa.Text(), nullable=True),
        sa.Column('notify_action', sa.Text(), nullable=True),
        sa.Column('subject_text', sa.Text(), nullable=True),
        sa.Column('body_text', sa.Text(), nullable=True),
        sa.Column('message_text', sa.Text(), nullable=True),
        sa.Column('start_date', sa.Text(), nullable=True),
        sa.Column('end_date', sa.Text(), nullable=True),
        sa.Column('start_time', sa.Integer(), nullable=True),
        sa.Column('end_time', sa.Integer(), nullable=True),
        sa.Column('uuid', sa.Text(), nullable=True),
        sa.Column('filename', sa.Text(), nullable=True),
        sa.Column('email_msg_id', sa.Text(), nullable=True),
        sa.Column('success', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_newsletter_log'),
        sa.UniqueConstraint('uuid', name='uq_newsletter_log_uuid'),
    )

    op.create_table(
        'recently_added',
        sa.Column('id', sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column('added_at', sa.Integer(), nullable=True),
        sa.Column('pms_identifier', sa.Text(), nullable=True),
        sa.Column('section_id', sa.Integer(), nullable=True),
        sa.Column('rating_key', sa.Integer(), nullable=True),
        sa.Column('parent_rating_key', sa.Integer(), nullable=True),
        sa.Column('grandparent_rating_key', sa.Integer(), nullable=True),
        sa.Column('media_type', sa.Text(), nullable=True),
        sa.Column('media_info', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_recently_added'),
    )

    op.create_table(
        'mobile_devices',
        sa.Column('id', sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column('device_id', sa.Text(), nullable=False),
        sa.Column('device_token', sa.Text(), nullable=True),
        sa.Column('device_name', sa.Text(), nullable=True),
        sa.Column('platform', sa.Text(), nullable=True),
        sa.Column('version', sa.Text(), nullable=True),
        sa.Column('friendly_name', sa.Text(), nullable=True),
        sa.Column('onesignal_id', sa.Text(), nullable=True),
        sa.Column('last_seen', sa.Integer(), nullable=True),
        sa.Column('official', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_mobile_devices'),
        sa.UniqueConstraint('device_id', name='uq_mobile_devices_device_id'),
    )

    op.create_table(
        'tvmaze_lookup',
        sa.Column('id', sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column('rating_key', sa.Integer(), nullable=True),
        sa.Column('thetvdb_id', sa.Integer(), nullable=True),
        sa.Column('imdb_id', sa.Text(), nullable=True),
        sa.Column('tvmaze_id', sa.Integer(), nullable=True),
        sa.Column('tvmaze_url', sa.Text(), nullable=True),
        sa.Column('tvmaze_json', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_tvmaze_lookup'),
    )
    op.create_index('idx_tvmaze_lookup', 'tvmaze_lookup', ['rating_key'], unique=True)

    op.create_table(
        'themoviedb_lookup',
        sa.Column('id', sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column('rating_key', sa.Integer(), nullable=True),
        sa.Column('thetvdb_id', sa.Integer(), nullable=True),
        sa.Column('imdb_id', sa.Text(), nullable=True),
        sa.Column('themoviedb_id', sa.Integer(), nullable=True),
        sa.Column('themoviedb_url', sa.Text(), nullable=True),
        sa.Column('themoviedb_json', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_themoviedb_lookup'),
    )
    op.create_index('idx_themoviedb_lookup', 'themoviedb_lookup', ['rating_key'], unique=True)

    op.create_table(
        'musicbrainz_lookup',
        sa.Column('id', sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column('rating_key', sa.Integer(), nullable=True),
        sa.Column('musicbrainz_id', sa.Integer(), nullable=True),
        sa.Column('musicbrainz_url', sa.Text(), nullable=True),
        sa.Column('musicbrainz_type', sa.Text(), nullable=True),
        sa.Column('musicbrainz_json', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_musicbrainz_lookup'),
    )
    op.create_index('idx_musicbrainz_lookup', 'musicbrainz_lookup', ['rating_key'], unique=True)

    op.create_table(
        'image_hash_lookup',
        sa.Column('id', sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column('img_hash', sa.Text(), nullable=True),
        sa.Column('img', sa.Text(), nullable=True),
        sa.Column('rating_key', sa.Integer(), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('opacity', sa.Integer(), nullable=True),
        sa.Column('background', sa.Text(), nullable=True),
        sa.Column('blur', sa.Integer(), nullable=True),
        sa.Column('fallback', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_image_hash_lookup'),
        sa.UniqueConstraint('img_hash', name='uq_image_hash_lookup_img_hash'),
    )
    op.create_index('idx_image_hash_lookup', 'image_hash_lookup', ['img_hash'], unique=True)

    op.create_table(
        'imgur_lookup',
        sa.Column('id', sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column('img_hash', sa.Text(), nullable=True),
        sa.Column('imgur_title', sa.Text(), nullable=True),
        sa.Column('imgur_url', sa.Text(), nullable=True),
        sa.Column('delete_hash', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_imgur_lookup'),
    )
    op.create_index('idx_imgur_lookup', 'imgur_lookup', ['img_hash'], unique=True)

    op.create_table(
        'cloudinary_lookup',
        sa.Column('id', sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column('img_hash', sa.Text(), nullable=True),
        sa.Column('cloudinary_title', sa.Text(), nullable=True),
        sa.Column('cloudinary_url', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_cloudinary_lookup'),
    )
    op.create_index('idx_cloudinary_lookup', 'cloudinary_lookup', ['img_hash'], unique=True)

    op.create_table(
        'exports',
        sa.Column('id', sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column('timestamp', sa.Integer(), nullable=True),
        sa.Column('section_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('rating_key', sa.Integer(), nullable=True),
        sa.Column('media_type', sa.Text(), nullable=True),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('file_format', sa.Text(), nullable=True),
        sa.Column('metadata_level', sa.Integer(), nullable=True),
        sa.Column('media_info_level', sa.Integer(), nullable=True),
        sa.Column('thumb_level', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('art_level', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('logo_level', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('custom_fields', sa.Text(), nullable=True),
        sa.Column('individual_files', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('file_size', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('complete', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('exported_items', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('total_items', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_exports'),
    )


def downgrade() -> None:
    op.drop_table('exports')
    op.drop_index('idx_cloudinary_lookup', table_name='cloudinary_lookup')
    op.drop_table('cloudinary_lookup')
    op.drop_index('idx_imgur_lookup', table_name='imgur_lookup')
    op.drop_table('imgur_lookup')
    op.drop_index('idx_image_hash_lookup', table_name='image_hash_lookup')
    op.drop_table('image_hash_lookup')
    op.drop_index('idx_musicbrainz_lookup', table_name='musicbrainz_lookup')
    op.drop_table('musicbrainz_lookup')
    op.drop_index('idx_themoviedb_lookup', table_name='themoviedb_lookup')
    op.drop_table('themoviedb_lookup')
    op.drop_index('idx_tvmaze_lookup', table_name='tvmaze_lookup')
    op.drop_table('tvmaze_lookup')
    op.drop_table('mobile_devices')
    op.drop_table('recently_added')
    op.drop_table('newsletter_log')
    op.drop_table('newsletters')
    op.drop_table('notify_log')
    op.drop_table('notifiers')
    op.drop_table('user_login')
    op.drop_table('library_sections')
    op.drop_table('users')
    op.drop_index('idx_session_history_metadata_live', table_name='session_history_metadata')
    op.drop_index('idx_session_history_metadata_guid', table_name='session_history_metadata')
    op.drop_index('idx_session_history_metadata_rating_key', table_name='session_history_metadata')
    op.drop_table('session_history_metadata')
    op.drop_index(
        'idx_session_history_media_info_transcode_decision',
        table_name='session_history_media_info',
    )
    op.drop_table('session_history_media_info')
    op.drop_index('idx_session_history_reference_id', table_name='session_history')
    op.drop_index('idx_session_history_section_id_stopped', table_name='session_history')
    op.drop_index('idx_session_history_section_id', table_name='session_history')
    op.drop_index('idx_session_history_user_id_stopped', table_name='session_history')
    op.drop_index('idx_session_history_user_id', table_name='session_history')
    op.drop_index('idx_session_history_user', table_name='session_history')
    op.drop_index('idx_session_history_grandparent_rating_key', table_name='session_history')
    op.drop_index('idx_session_history_parent_rating_key', table_name='session_history')
    op.drop_index('idx_session_history_rating_key', table_name='session_history')
    op.drop_index('idx_session_history_media_type_stopped', table_name='session_history')
    op.drop_index('idx_session_history_media_type', table_name='session_history')
    op.drop_table('session_history')
    op.drop_table('sessions_continued')
    op.drop_table('sessions')
    op.drop_table('version_info')
