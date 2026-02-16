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
Test factories for Session and SessionContinued models.
"""

import time

import factory
from factory import Faker as FactoryFaker

from plexpy.db.models.sessions import Session, SessionContinued
from tests.factories.base import BaseFactory, TimestampFactoryMixin


class SessionFactory(BaseFactory):
    """Factory for creating Session model instances."""

    class Meta:
        model = Session

    id = factory.Sequence(lambda n: n + 1)
    session_key = factory.Sequence(lambda n: n + 1)
    session_id = FactoryFaker('uuid4')
    transcode_key = FactoryFaker('uuid4')
    rating_key = factory.Sequence(lambda n: n + 10000)
    section_id = factory.Sequence(lambda n: n + 1)
    media_type = 'movie'
    started = factory.LazyFunction(lambda: int(time.time()))
    stopped = None
    paused_counter = 0
    state = 'playing'
    user_id = factory.Sequence(lambda n: n + 1000)
    user = FactoryFaker('user_name')
    friendly_name = FactoryFaker('first_name')
    ip_address = FactoryFaker('ipv4')
    machine_id = FactoryFaker('uuid4')
    bandwidth = None
    location = 'lan'
    player = 'Plex Web'
    product = 'Plex Web'
    platform = 'Windows'
    title = FactoryFaker('catch_phrase')
    parent_title = None
    grandparent_title = None
    original_title = None
    full_title = FactoryFaker('catch_phrase')
    media_index = 1
    parent_media_index = None
    thumb = FactoryFaker('image_url')
    parent_thumb = None
    grandparent_thumb = None
    year = FactoryFaker('year')
    parent_rating_key = None
    grandparent_rating_key = None
    originally_available_at = FactoryFaker('date')
    added_at = factory.LazyFunction(lambda: int(time.time()))
    guid = FactoryFaker('uuid4')
    view_offset = 0
    duration = factory.LazyFunction(lambda: 7200000)  # 2 hours in ms
    video_decision = 'direct play'
    audio_decision = 'direct play'
    transcode_decision = 'direct play'
    container = 'mkv'
    bitrate = 8000
    width = 1920
    height = 1080
    video_codec = 'h264'
    video_bitrate = 6000
    video_resolution = '1080p'
    video_width = 1920
    video_height = 1080
    video_framerate = '24p'
    video_scan_type = 'progressive'
    video_full_resolution = '1080p'
    video_dynamic_range = 'SDR'
    aspect_ratio = '1.78'
    audio_codec = 'aac'
    audio_bitrate = 128
    audio_channels = 6
    audio_language = 'eng'
    audio_language_code = 'en'
    subtitle_codec = None
    subtitle_forced = 0
    subtitle_language = None
    stream_bitrate = 8000
    stream_video_resolution = '1080p'
    quality_profile = 'Original'
    stream_container_decision = 'direct play'
    stream_container = 'mkv'
    stream_video_decision = 'direct play'
    stream_video_codec = 'h264'
    stream_video_bitrate = 6000
    stream_video_width = 1920
    stream_video_height = 1080
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
    subtitles = 0
    stream_subtitle_decision = 'none'
    stream_subtitle_codec = None
    stream_subtitle_forced = 0
    stream_subtitle_language = None
    transcode_protocol = 'http'
    transcode_container = 'mkv'
    transcode_video_codec = 'h264'
    transcode_audio_codec = 'aac'
    transcode_audio_channels = 6
    transcode_width = 1920
    transcode_height = 1080
    transcode_hw_decoding = 0
    transcode_hw_encoding = 0
    optimized_version = 0
    optimized_version_profile = None
    optimized_version_title = None
    synced_version = 0
    synced_version_profile = None
    live = 0
    live_uuid = None
    channel_call_sign = None
    channel_id = None
    channel_identifier = None
    channel_title = None
    channel_thumb = None
    channel_vcn = None
    secure = 1
    relayed = 0
    buffer_count = 0
    buffer_last_triggered = None
    last_paused = None
    watched = 0
    intro = 0
    credits = 0
    commercial = 0
    marker = 0
    initial_stream = 1
    write_attempts = 0
    raw_stream_info = None
    rating_key_websocket = None


class PlayingSessionFactory(SessionFactory):
    """Factory for creating active playing session instances."""

    state = 'playing'
    stopped = None


class PausedSessionFactory(SessionFactory):
    """Factory for creating paused session instances."""

    state = 'paused'
    paused_counter = factory.LazyFunction(lambda: 30000)  # 30 seconds


class StoppedSessionFactory(SessionFactory):
    """Factory for creating stopped session instances."""

    state = 'stopped'
    stopped = factory.LazyFunction(lambda: int(time.time()))


class MovieSessionFactory(SessionFactory):
    """Factory for creating movie session instances."""

    media_type = 'movie'
    title = FactoryFaker('catch_phrase')
    full_title = factory.LazyAttribute(lambda o: o.title)
    year = FactoryFaker('year')


class TVShowSessionFactory(SessionFactory):
    """Factory for creating TV show session instances."""

    media_type = 'episode'
    title = FactoryFaker('sentence', nb_words=3)
    parent_title = FactoryFaker('catch_phrase')
    grandparent_title = FactoryFaker('company')
    full_title = factory.LazyAttribute(lambda o: f"{o.parent_title} - {o.title}")
    parent_rating_key = factory.Sequence(lambda n: n + 5000)
    grandparent_rating_key = factory.Sequence(lambda n: n + 4000)


class MusicSessionFactory(SessionFactory):
    """Factory for creating music session instances."""

    media_type = 'track'
    title = FactoryFaker('sentence', nb_words=3)
    parent_title = FactoryFaker('word')
    grandparent_title = FactoryFaker('name')
    full_title = factory.LazyAttribute(lambda o: f"{o.grandparent_title} - {o.title}")
    parent_rating_key = factory.Sequence(lambda n: n + 6000)
    grandparent_rating_key = factory.Sequence(lambda n: n + 7000)
    duration = factory.LazyFunction(lambda: 210000)  # 3.5 minutes


class SessionContinuedFactory(BaseFactory, TimestampFactoryMixin):
    """Factory for creating SessionContinued model instances."""

    class Meta:
        model = SessionContinued

    id = factory.Sequence(lambda n: n + 1)
    user_id = factory.Sequence(lambda n: n + 1000)
    machine_id = FactoryFaker('uuid4')
    media_type = 'movie'
    stopped = factory.LazyAttribute(lambda o: o.timestamp)
