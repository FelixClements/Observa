# This file is part of Observa.
#
#  Observa is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Observa is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Observa.  If not, see <http://www.gnu.org/licenses/>.

"""
Test factories for SessionHistory, SessionHistoryMediaInfo, and SessionHistoryMetadata models.
"""

import time

import factory
from factory import Faker as FactoryFaker

from plexpy.db.models.history import (
    SessionHistory,
    SessionHistoryMediaInfo,
    SessionHistoryMetadata,
)
from tests.factories.base import BaseFactory


class SessionHistoryFactory(BaseFactory):
    """Factory for creating SessionHistory model instances."""

    class Meta:
        model = SessionHistory

    id = factory.Sequence(lambda n: n + 1)
    reference_id = factory.Sequence(lambda n: n + 1)
    started = factory.LazyFunction(lambda: int(time.time()) - 3600)
    stopped = factory.LazyFunction(lambda: int(time.time()))
    rating_key = factory.Sequence(lambda n: n + 10000)
    user_id = factory.Sequence(lambda n: n + 1000)
    user = FactoryFaker('user_name')
    ip_address = FactoryFaker('ipv4')
    paused_counter = 0
    player = 'Plex Web'
    product = 'Plex Web'
    product_version = '4.115.0'
    platform = 'Windows'
    platform_version = '10'
    profile = 'PlexWeb'
    machine_id = FactoryFaker('uuid4')
    bandwidth = None
    location = 'lan'
    quality_profile = 'Original'
    secure = 1
    relayed = 0
    parent_rating_key = None
    grandparent_rating_key = None
    media_type = 'movie'
    section_id = factory.Sequence(lambda n: n + 1)
    view_offset = 0


class CompletedSessionHistoryFactory(SessionHistoryFactory):
    """Factory for creating completed session history instances."""

    stopped = factory.LazyFunction(lambda: int(time.time()))
    view_offset = factory.LazyFunction(lambda: 7200000)  # 2 hours in ms


class PartialSessionHistoryFactory(SessionHistoryFactory):
    """Factory for creating partial/watched session history instances."""

    view_offset = factory.LazyFunction(lambda: 3600000)  # 1 hour in ms (50% of 2hr movie)


class TVShowSessionHistoryFactory(SessionHistoryFactory):
    """Factory for creating TV show session history instances."""

    media_type = 'episode'
    parent_rating_key = factory.Sequence(lambda n: n + 5000)
    grandparent_rating_key = factory.Sequence(lambda n: n + 4000)


class MusicSessionHistoryFactory(SessionHistoryFactory):
    """Factory for creating music session history instances."""

    media_type = 'track'
    parent_rating_key = factory.Sequence(lambda n: n + 6000)
    grandparent_rating_key = factory.Sequence(lambda n: n + 7000)


class SessionHistoryMediaInfoFactory(BaseFactory):
    """Factory for creating SessionHistoryMediaInfo model instances."""

    class Meta:
        model = SessionHistoryMediaInfo

    id = factory.Sequence(lambda n: n + 1)
    rating_key = factory.Sequence(lambda n: n + 10000)
    video_decision = 'direct play'
    audio_decision = 'direct play'
    transcode_decision = 'direct play'
    duration = 0
    container = 'mkv'
    bitrate = 8000
    width = 1920
    height = 1080
    video_bitrate = 6000
    video_bit_depth = 8
    video_codec = 'h264'
    video_codec_level = '4.1'
    video_width = 1920
    video_height = 1080
    video_resolution = '1080p'
    video_framerate = '24p'
    video_scan_type = 'progressive'
    video_full_resolution = '1080p'
    video_dynamic_range = 'SDR'
    aspect_ratio = '1.78'
    audio_bitrate = 128
    audio_codec = 'aac'
    audio_channels = 6
    audio_language = 'eng'
    audio_language_code = 'en'
    subtitles = 0
    subtitle_codec = None
    subtitle_forced = 0
    subtitle_language = None
    transcode_protocol = 'http'
    transcode_container = 'mkv'
    transcode_video_codec = 'h264'
    transcode_audio_codec = 'aac'
    transcode_audio_channels = 6
    transcode_width = 1920
    transcode_height = 1080
    transcode_hw_requested = 0
    transcode_hw_full_pipeline = 0
    transcode_hw_decode = None
    transcode_hw_decode_title = None
    transcode_hw_decoding = 0
    transcode_hw_encode = None
    transcode_hw_encode_title = None
    transcode_hw_encoding = 0
    stream_container = 'mkv'
    stream_container_decision = 'direct play'
    stream_bitrate = 8000
    stream_video_decision = 'direct play'
    stream_video_bitrate = 6000
    stream_video_codec = 'h264'
    stream_video_codec_level = '4.1'
    stream_video_bit_depth = 8
    stream_video_height = 1080
    stream_video_width = 1920
    stream_video_resolution = '1080p'
    stream_video_framerate = '24p'
    stream_video_scan_type = 'progressive'
    stream_video_full_resolution = '1080p'
    stream_video_dynamic_range = 'SDR'
    stream_audio_decision = 'direct play'
    stream_audio_codec = 'aac'
    stream_audio_bitrate = 128
    stream_audio_channels = 6
    stream_audio_language = 'eng'
    stream_audio_language_code = 'en'
    stream_subtitle_decision = 'none'
    stream_subtitle_codec = None
    stream_subtitle_container = None
    stream_subtitle_forced = 0
    stream_subtitle_language = None
    synced_version = 0
    synced_version_profile = None
    optimized_version = 0
    optimized_version_profile = None
    optimized_version_title = None


class DirectPlayMediaInfoFactory(SessionHistoryMediaInfoFactory):
    """Factory for direct play media info."""

    video_decision = 'direct play'
    audio_decision = 'direct play'
    transcode_decision = 'direct play'


class TranscodedMediaInfoFactory(SessionHistoryMediaInfoFactory):
    """Factory for transcoded media info."""

    video_decision = 'transcode'
    audio_decision = 'transcode'
    transcode_decision = 'transcode'
    container = 'mkv'
    transcode_container = 'mpegts'
    transcode_video_codec = 'h264'
    transcode_audio_codec = 'aac'


class HDRMediaInfoFactory(SessionHistoryMediaInfoFactory):
    """Factory for HDR media info."""

    video_dynamic_range = 'HDR'
    video_bit_depth = 10
    video_codec = 'hevc'


class SessionHistoryMetadataFactory(BaseFactory):
    """Factory for creating SessionHistoryMetadata model instances."""

    class Meta:
        model = SessionHistoryMetadata

    id = factory.Sequence(lambda n: n + 1)
    rating_key = factory.Sequence(lambda n: n + 10000)
    parent_rating_key = None
    grandparent_rating_key = None
    title = FactoryFaker('catch_phrase')
    parent_title = None
    grandparent_title = None
    original_title = None
    full_title = factory.LazyAttribute(lambda o: o.title)
    media_index = 1
    parent_media_index = None
    thumb = FactoryFaker('image_url')
    parent_thumb = None
    grandparent_thumb = None
    art = FactoryFaker('image_url')
    media_type = 'movie'
    year = FactoryFaker('year')
    originally_available_at = FactoryFaker('date')
    added_at = factory.LazyFunction(lambda: int(time.time()) - 86400 * 30)
    updated_at = factory.LazyFunction(lambda: int(time.time()) - 86400)
    last_viewed_at = factory.LazyFunction(lambda: int(time.time()) - 3600)
    content_rating = 'R'
    summary = FactoryFaker('paragraph')
    tagline = FactoryFaker('sentence')
    rating = factory.LazyAttribute(lambda o: f"{round(8.5, 1)}")
    duration = factory.LazyFunction(lambda: 7200000)
    guid = FactoryFaker('uuid4')
    directors = FactoryFaker('name')
    writers = FactoryFaker('name')
    actors = FactoryFaker('name')
    genres = 'Action, Drama'
    studio = FactoryFaker('company')
    labels = None
    live = 0
    channel_call_sign = None
    channel_id = None
    channel_identifier = None
    channel_title = None
    channel_thumb = None
    channel_vcn = None
    marker_credits_first = 0
    marker_credits_final = 0


class MovieMetadataFactory(SessionHistoryMetadataFactory):
    """Factory for movie metadata."""

    media_type = 'movie'
    title = FactoryFaker('catch_phrase')
    full_title = factory.LazyAttribute(lambda o: o.title)


class TVShowMetadataFactory(SessionHistoryMetadataFactory):
    """Factory for TV show episode metadata."""

    media_type = 'episode'
    title = FactoryFaker('sentence', nb_words=3)
    parent_title = FactoryFaker('catch_phrase')
    grandparent_title = FactoryFaker('company')
    full_title = factory.LazyAttribute(lambda o: f"{o.parent_title} - {o.title}")
    parent_rating_key = factory.Sequence(lambda n: n + 5000)
    grandparent_rating_key = factory.Sequence(lambda n: n + 4000)
    parent_thumb = FactoryFaker('image_url')
    grandparent_thumb = FactoryFaker('image_url')


class MusicMetadataFactory(SessionHistoryMetadataFactory):
    """Factory for music track metadata."""

    media_type = 'track'
    title = FactoryFaker('sentence', nb_words=3)
    parent_title = FactoryFaker('word')
    grandparent_title = FactoryFaker('name')
    full_title = factory.LazyAttribute(lambda o: f"{o.grandparent_title} - {o.title}")
    parent_rating_key = factory.Sequence(lambda n: n + 6000)
    grandparent_rating_key = factory.Sequence(lambda n: n + 7000)
    duration = factory.LazyFunction(lambda: 210000)


class LiveTVMetadataFactory(SessionHistoryMetadataFactory):
    """Factory for live TV metadata."""

    media_type = 'live'
    live = 1
    title = FactoryFaker('sentence')
    channel_call_sign = FactoryFaker('bothify', text='???#')
    channel_title = FactoryFaker('company')
