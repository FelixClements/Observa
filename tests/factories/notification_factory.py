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
Test factories for Notifier and NotifyLog models.
"""

import factory
from factory import Faker as FactoryFaker

from plexpy.db.models.notifications import Notifier, NotifyLog
from tests.factories.base import BaseFactory, TimestampFactoryMixin


class NotifierFactory(BaseFactory):
    """Factory for creating Notifier model instances."""

    class Meta:
        model = Notifier

    id = factory.Sequence(lambda n: n + 1)
    agent_id = factory.Sequence(lambda n: n + 1)
    agent_name = 'email'
    agent_label = 'Email'
    friendly_name = FactoryFaker('word')
    notifier_config = '{}'
    on_play = 0
    on_stop = 0
    on_pause = 0
    on_resume = 0
    on_change = 0
    on_buffer = 0
    on_error = 0
    on_intro = 0
    on_credits = 0
    on_commercial = 0
    on_watched = 0
    on_created = 0
    on_extdown = 0
    on_intdown = 0
    on_extup = 0
    on_intup = 0
    on_pmsupdate = 0
    on_concurrent = 0
    on_newdevice = 0
    on_plexpyupdate = 0
    on_plexpydbcorrupt = 0
    on_tokenexpired = 0
    on_play_subject = None
    on_stop_subject = None
    on_pause_subject = None
    on_resume_subject = None
    on_change_subject = None
    on_buffer_subject = None
    on_error_subject = None
    on_intro_subject = None
    on_credits_subject = None
    on_commercial_subject = None
    on_watched_subject = None
    on_created_subject = None
    on_extdown_subject = None
    on_intdown_subject = None
    on_extup_subject = None
    on_intup_subject = None
    on_pmsupdate_subject = None
    on_concurrent_subject = None
    on_newdevice_subject = None
    on_plexpyupdate_subject = None
    on_plexpydbcorrupt_subject = None
    on_tokenexpired_subject = None
    on_play_body = None
    on_stop_body = None
    on_pause_body = None
    on_resume_body = None
    on_change_body = None
    on_buffer_body = None
    on_error_body = None
    on_intro_body = None
    on_credits_body = None
    on_commercial_body = None
    on_watched_body = None
    on_created_body = None
    on_extdown_body = None
    on_intdown_body = None
    on_extup_body = None
    on_intup_body = None
    on_pmsupdate_body = None
    on_concurrent_body = None
    on_newdevice_body = None
    on_plexpyupdate_body = None
    on_plexpydbcorrupt_body = None
    on_tokenexpired_body = None
    custom_conditions = None
    custom_conditions_logic = None


class EmailNotifierFactory(NotifierFactory):
    """Factory for creating email notifier instances."""

    agent_id = 1
    agent_name = 'email'
    agent_label = 'Email'


class PushbulletNotifierFactory(NotifierFactory):
    """Factory for creating Pushbullet notifier instances."""

    agent_id = 2
    agent_name = 'pushbullet'
    agent_label = 'Pushbullet'


class TelegramNotifierFactory(NotifierFactory):
    """Factory for creating Telegram notifier instances."""

    agent_id = 3
    agent_name = 'telegram'
    agent_label = 'Telegram'


class SlackNotifierFactory(NotifierFactory):
    """Factory for creating Slack notifier instances."""

    agent_id = 4
    agent_name = 'slack'
    agent_label = 'Slack'


class DiscordNotifierFactory(NotifierFactory):
    """Factory for creating Discord notifier instances."""

    agent_id = 5
    agent_name = 'discord'
    agent_label = 'Discord'


class NotifierWithNotificationsFactory(NotifierFactory):
    """Factory for creating notifier with playback notifications enabled."""

    on_play = 1
    on_stop = 1
    on_play_subject = 'Now Playing'
    on_play_body = '{title} is now playing'
    on_stop_subject = 'Playback Stopped'
    on_stop_body = '{title} has stopped'


class NotifyLogFactory(BaseFactory, TimestampFactoryMixin):
    """Factory for creating NotifyLog model instances."""

    class Meta:
        model = NotifyLog

    id = factory.Sequence(lambda n: n + 1)
    timestamp = factory.LazyAttribute(lambda o: o.timestamp)
    session_key = factory.Sequence(lambda n: n + 1)
    rating_key = factory.Sequence(lambda n: n + 10000)
    parent_rating_key = None
    grandparent_rating_key = None
    user_id = factory.Sequence(lambda n: n + 1000)
    user = FactoryFaker('user_name')
    notifier_id = factory.Sequence(lambda n: n + 1)
    agent_id = 1
    agent_name = 'email'
    notify_action = 'play'
    subject_text = FactoryFaker('sentence')
    body_text = FactoryFaker('paragraph')
    script_args = None
    poster_url = FactoryFaker('image_url')
    success = 1
    tag = None


class PlayNotificationFactory(NotifyLogFactory):
    """Factory for play notification instances."""

    notify_action = 'play'
    subject_text = 'Now Playing'
    body_text = factory.LazyAttribute(lambda o: f"{o.user} is watching something")


class StopNotificationFactory(NotifyLogFactory):
    """Factory for stop notification instances."""

    notify_action = 'stop'
    subject_text = 'Playback Stopped'
    body_text = factory.LazyAttribute(lambda o: f"{o.user} stopped watching")


class PauseNotificationFactory(NotifyLogFactory):
    """Factory for pause notification instances."""

    notify_action = 'pause'
    subject_text = 'Playback Paused'
    body_text = factory.LazyAttribute(lambda o: f"{o.user} paused playback")


class ResumeNotificationFactory(NotifyLogFactory):
    """Factory for resume notification instances."""

    notify_action = 'resume'
    subject_text = 'Playback Resumed'
    body_text = factory.LazyAttribute(lambda o: f"{o.user} resumed playback")


class ErrorNotificationFactory(NotifyLogFactory):
    """Factory for error notification instances."""

    notify_action = 'error'
    subject_text = 'Playback Error'
    body_text = 'An error occurred during playback'
    success = 0


class FailedNotifyLogFactory(NotifyLogFactory):
    """Factory for failed notification instances."""

    success = 0
    body_text = factory.LazyAttribute(lambda o: f"{o.body_text} (failed)")
