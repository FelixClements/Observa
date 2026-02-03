from typing import Optional

from sqlalchemy import Index, Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from plexpy.db.models import Base, auto_pk, explicit_pk


class SessionHistory(Base):
    __tablename__ = 'session_history'
    __table_args__ = (
        Index('idx_session_history_media_type', 'media_type'),
        Index('idx_session_history_media_type_stopped', 'media_type', 'stopped'),
        Index('idx_session_history_rating_key', 'rating_key'),
        Index('idx_session_history_parent_rating_key', 'parent_rating_key'),
        Index('idx_session_history_grandparent_rating_key', 'grandparent_rating_key'),
        Index('idx_session_history_user', 'user'),
        Index('idx_session_history_user_id', 'user_id'),
        Index('idx_session_history_user_id_stopped', 'user_id', 'stopped'),
        Index('idx_session_history_section_id', 'section_id'),
        Index('idx_session_history_section_id_stopped', 'section_id', 'stopped'),
        Index('idx_session_history_reference_id', 'reference_id'),
    )

    id: Mapped[int] = auto_pk()
    reference_id: Mapped[Optional[int]] = mapped_column(Integer)
    started: Mapped[Optional[int]] = mapped_column(Integer)
    stopped: Mapped[Optional[int]] = mapped_column(Integer)
    rating_key: Mapped[Optional[int]] = mapped_column(Integer)
    user_id: Mapped[Optional[int]] = mapped_column(Integer)
    user: Mapped[Optional[str]] = mapped_column(Text)
    ip_address: Mapped[Optional[str]] = mapped_column(Text)
    paused_counter: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
    player: Mapped[Optional[str]] = mapped_column(Text)
    product: Mapped[Optional[str]] = mapped_column(Text)
    product_version: Mapped[Optional[str]] = mapped_column(Text)
    platform: Mapped[Optional[str]] = mapped_column(Text)
    platform_version: Mapped[Optional[str]] = mapped_column(Text)
    profile: Mapped[Optional[str]] = mapped_column(Text)
    machine_id: Mapped[Optional[str]] = mapped_column(Text)
    bandwidth: Mapped[Optional[int]] = mapped_column(Integer)
    location: Mapped[Optional[str]] = mapped_column(Text)
    quality_profile: Mapped[Optional[str]] = mapped_column(Text)
    secure: Mapped[Optional[int]] = mapped_column(Integer)
    relayed: Mapped[Optional[int]] = mapped_column(Integer)
    parent_rating_key: Mapped[Optional[int]] = mapped_column(Integer)
    grandparent_rating_key: Mapped[Optional[int]] = mapped_column(Integer)
    media_type: Mapped[Optional[str]] = mapped_column(Text)
    section_id: Mapped[Optional[int]] = mapped_column(Integer)
    view_offset: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))


class SessionHistoryMediaInfo(Base):
    __tablename__ = 'session_history_media_info'
    __table_args__ = (
        Index('idx_session_history_media_info_transcode_decision', 'transcode_decision'),
    )

    id: Mapped[int] = explicit_pk()
    rating_key: Mapped[Optional[int]] = mapped_column(Integer)
    video_decision: Mapped[Optional[str]] = mapped_column(Text)
    audio_decision: Mapped[Optional[str]] = mapped_column(Text)
    transcode_decision: Mapped[Optional[str]] = mapped_column(Text)
    duration: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
    container: Mapped[Optional[str]] = mapped_column(Text)
    bitrate: Mapped[Optional[int]] = mapped_column(Integer)
    width: Mapped[Optional[int]] = mapped_column(Integer)
    height: Mapped[Optional[int]] = mapped_column(Integer)
    video_bitrate: Mapped[Optional[int]] = mapped_column(Integer)
    video_bit_depth: Mapped[Optional[int]] = mapped_column(Integer)
    video_codec: Mapped[Optional[str]] = mapped_column(Text)
    video_codec_level: Mapped[Optional[str]] = mapped_column(Text)
    video_width: Mapped[Optional[int]] = mapped_column(Integer)
    video_height: Mapped[Optional[int]] = mapped_column(Integer)
    video_resolution: Mapped[Optional[str]] = mapped_column(Text)
    video_framerate: Mapped[Optional[str]] = mapped_column(Text)
    video_scan_type: Mapped[Optional[str]] = mapped_column(Text)
    video_full_resolution: Mapped[Optional[str]] = mapped_column(Text)
    video_dynamic_range: Mapped[Optional[str]] = mapped_column(Text)
    aspect_ratio: Mapped[Optional[str]] = mapped_column(Text)
    audio_bitrate: Mapped[Optional[int]] = mapped_column(Integer)
    audio_codec: Mapped[Optional[str]] = mapped_column(Text)
    audio_channels: Mapped[Optional[int]] = mapped_column(Integer)
    audio_language: Mapped[Optional[str]] = mapped_column(Text)
    audio_language_code: Mapped[Optional[str]] = mapped_column(Text)
    subtitles: Mapped[Optional[int]] = mapped_column(Integer)
    subtitle_codec: Mapped[Optional[str]] = mapped_column(Text)
    subtitle_forced: Mapped[Optional[int]] = mapped_column(Integer)
    subtitle_language: Mapped[Optional[str]] = mapped_column(Text)
    transcode_protocol: Mapped[Optional[str]] = mapped_column(Text)
    transcode_container: Mapped[Optional[str]] = mapped_column(Text)
    transcode_video_codec: Mapped[Optional[str]] = mapped_column(Text)
    transcode_audio_codec: Mapped[Optional[str]] = mapped_column(Text)
    transcode_audio_channels: Mapped[Optional[int]] = mapped_column(Integer)
    transcode_width: Mapped[Optional[int]] = mapped_column(Integer)
    transcode_height: Mapped[Optional[int]] = mapped_column(Integer)
    transcode_hw_requested: Mapped[Optional[int]] = mapped_column(Integer)
    transcode_hw_full_pipeline: Mapped[Optional[int]] = mapped_column(Integer)
    transcode_hw_decode: Mapped[Optional[str]] = mapped_column(Text)
    transcode_hw_decode_title: Mapped[Optional[str]] = mapped_column(Text)
    transcode_hw_decoding: Mapped[Optional[int]] = mapped_column(Integer)
    transcode_hw_encode: Mapped[Optional[str]] = mapped_column(Text)
    transcode_hw_encode_title: Mapped[Optional[str]] = mapped_column(Text)
    transcode_hw_encoding: Mapped[Optional[int]] = mapped_column(Integer)
    stream_container: Mapped[Optional[str]] = mapped_column(Text)
    stream_container_decision: Mapped[Optional[str]] = mapped_column(Text)
    stream_bitrate: Mapped[Optional[int]] = mapped_column(Integer)
    stream_video_decision: Mapped[Optional[str]] = mapped_column(Text)
    stream_video_bitrate: Mapped[Optional[int]] = mapped_column(Integer)
    stream_video_codec: Mapped[Optional[str]] = mapped_column(Text)
    stream_video_codec_level: Mapped[Optional[str]] = mapped_column(Text)
    stream_video_bit_depth: Mapped[Optional[int]] = mapped_column(Integer)
    stream_video_height: Mapped[Optional[int]] = mapped_column(Integer)
    stream_video_width: Mapped[Optional[int]] = mapped_column(Integer)
    stream_video_resolution: Mapped[Optional[str]] = mapped_column(Text)
    stream_video_framerate: Mapped[Optional[str]] = mapped_column(Text)
    stream_video_scan_type: Mapped[Optional[str]] = mapped_column(Text)
    stream_video_full_resolution: Mapped[Optional[str]] = mapped_column(Text)
    stream_video_dynamic_range: Mapped[Optional[str]] = mapped_column(Text)
    stream_audio_decision: Mapped[Optional[str]] = mapped_column(Text)
    stream_audio_codec: Mapped[Optional[str]] = mapped_column(Text)
    stream_audio_bitrate: Mapped[Optional[int]] = mapped_column(Integer)
    stream_audio_channels: Mapped[Optional[int]] = mapped_column(Integer)
    stream_audio_language: Mapped[Optional[str]] = mapped_column(Text)
    stream_audio_language_code: Mapped[Optional[str]] = mapped_column(Text)
    stream_subtitle_decision: Mapped[Optional[str]] = mapped_column(Text)
    stream_subtitle_codec: Mapped[Optional[str]] = mapped_column(Text)
    stream_subtitle_container: Mapped[Optional[str]] = mapped_column(Text)
    stream_subtitle_forced: Mapped[Optional[int]] = mapped_column(Integer)
    stream_subtitle_language: Mapped[Optional[str]] = mapped_column(Text)
    synced_version: Mapped[Optional[int]] = mapped_column(Integer)
    synced_version_profile: Mapped[Optional[str]] = mapped_column(Text)
    optimized_version: Mapped[Optional[int]] = mapped_column(Integer)
    optimized_version_profile: Mapped[Optional[str]] = mapped_column(Text)
    optimized_version_title: Mapped[Optional[str]] = mapped_column(Text)


class SessionHistoryMetadata(Base):
    __tablename__ = 'session_history_metadata'
    __table_args__ = (
        Index('idx_session_history_metadata_rating_key', 'rating_key'),
        Index('idx_session_history_metadata_guid', 'guid'),
        Index('idx_session_history_metadata_live', 'live'),
    )

    id: Mapped[int] = explicit_pk()
    rating_key: Mapped[Optional[int]] = mapped_column(Integer)
    parent_rating_key: Mapped[Optional[int]] = mapped_column(Integer)
    grandparent_rating_key: Mapped[Optional[int]] = mapped_column(Integer)
    title: Mapped[Optional[str]] = mapped_column(Text)
    parent_title: Mapped[Optional[str]] = mapped_column(Text)
    grandparent_title: Mapped[Optional[str]] = mapped_column(Text)
    original_title: Mapped[Optional[str]] = mapped_column(Text)
    full_title: Mapped[Optional[str]] = mapped_column(Text)
    media_index: Mapped[Optional[int]] = mapped_column(Integer)
    parent_media_index: Mapped[Optional[int]] = mapped_column(Integer)
    thumb: Mapped[Optional[str]] = mapped_column(Text)
    parent_thumb: Mapped[Optional[str]] = mapped_column(Text)
    grandparent_thumb: Mapped[Optional[str]] = mapped_column(Text)
    art: Mapped[Optional[str]] = mapped_column(Text)
    media_type: Mapped[Optional[str]] = mapped_column(Text)
    year: Mapped[Optional[int]] = mapped_column(Integer)
    originally_available_at: Mapped[Optional[str]] = mapped_column(Text)
    added_at: Mapped[Optional[int]] = mapped_column(Integer)
    updated_at: Mapped[Optional[int]] = mapped_column(Integer)
    last_viewed_at: Mapped[Optional[int]] = mapped_column(Integer)
    content_rating: Mapped[Optional[str]] = mapped_column(Text)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    tagline: Mapped[Optional[str]] = mapped_column(Text)
    rating: Mapped[Optional[str]] = mapped_column(Text)
    duration: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
    guid: Mapped[Optional[str]] = mapped_column(Text)
    directors: Mapped[Optional[str]] = mapped_column(Text)
    writers: Mapped[Optional[str]] = mapped_column(Text)
    actors: Mapped[Optional[str]] = mapped_column(Text)
    genres: Mapped[Optional[str]] = mapped_column(Text)
    studio: Mapped[Optional[str]] = mapped_column(Text)
    labels: Mapped[Optional[str]] = mapped_column(Text)
    live: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
    channel_call_sign: Mapped[Optional[str]] = mapped_column(Text)
    channel_id: Mapped[Optional[str]] = mapped_column(Text)
    channel_identifier: Mapped[Optional[str]] = mapped_column(Text)
    channel_title: Mapped[Optional[str]] = mapped_column(Text)
    channel_thumb: Mapped[Optional[str]] = mapped_column(Text)
    channel_vcn: Mapped[Optional[str]] = mapped_column(Text)
    marker_credits_first: Mapped[Optional[int]] = mapped_column(Integer)
    marker_credits_final: Mapped[Optional[int]] = mapped_column(Integer)
