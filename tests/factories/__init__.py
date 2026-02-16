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
Test factories for Observa models.

This module provides factory-boy factories for creating test instances
of various database models.
"""

from tests.factories.base import BaseFactory, TimestampFactoryMixin
from tests.factories.user_factory import (
    AdminUserFactory,
    FailedLoginFactory,
    HomeUserFactory,
    InactiveUserFactory,
    RestrictedUserFactory,
    SuccessfulLoginFactory,
    UserFactory,
    UserLoginFactory,
)
from tests.factories.session_factory import (
    MovieSessionFactory,
    MusicSessionFactory,
    PlayingSessionFactory,
    PausedSessionFactory,
    SessionContinuedFactory,
    SessionFactory,
    StoppedSessionFactory,
    TVShowSessionFactory,
)
from tests.factories.history_factory import (
    CompletedSessionHistoryFactory,
    DirectPlayMediaInfoFactory,
    HDRMediaInfoFactory,
    LiveTVMetadataFactory,
    MovieMetadataFactory,
    MusicMetadataFactory,
    MusicSessionHistoryFactory,
    PartialSessionHistoryFactory,
    SessionHistoryFactory,
    SessionHistoryMediaInfoFactory,
    SessionHistoryMetadataFactory,
    TranscodedMediaInfoFactory,
    TVShowMetadataFactory,
    TVShowSessionHistoryFactory,
)
from tests.factories.notification_factory import (
    DiscordNotifierFactory,
    EmailNotifierFactory,
    ErrorNotificationFactory,
    FailedNotifyLogFactory,
    NotifyLogFactory,
    NotifierFactory,
    NotifierWithNotificationsFactory,
    PlayNotificationFactory,
    PauseNotificationFactory,
    PushbulletNotifierFactory,
    ResumeNotificationFactory,
    SlackNotifierFactory,
    StopNotificationFactory,
    TelegramNotifierFactory,
)

__all__ = [
    # Base
    'BaseFactory',
    'TimestampFactoryMixin',
    # User factories
    'UserFactory',
    'AdminUserFactory',
    'HomeUserFactory',
    'InactiveUserFactory',
    'RestrictedUserFactory',
    'UserLoginFactory',
    'FailedLoginFactory',
    'SuccessfulLoginFactory',
    # Session factories
    'SessionFactory',
    'PlayingSessionFactory',
    'PausedSessionFactory',
    'StoppedSessionFactory',
    'MovieSessionFactory',
    'TVShowSessionFactory',
    'MusicSessionFactory',
    'SessionContinuedFactory',
    # History factories
    'SessionHistoryFactory',
    'CompletedSessionHistoryFactory',
    'PartialSessionHistoryFactory',
    'TVShowSessionHistoryFactory',
    'MusicSessionHistoryFactory',
    'SessionHistoryMediaInfoFactory',
    'DirectPlayMediaInfoFactory',
    'TranscodedMediaInfoFactory',
    'HDRMediaInfoFactory',
    'SessionHistoryMetadataFactory',
    'MovieMetadataFactory',
    'TVShowMetadataFactory',
    'MusicMetadataFactory',
    'LiveTVMetadataFactory',
    # Notification factories
    'NotifierFactory',
    'EmailNotifierFactory',
    'PushbulletNotifierFactory',
    'TelegramNotifierFactory',
    'SlackNotifierFactory',
    'DiscordNotifierFactory',
    'NotifierWithNotificationsFactory',
    'NotifyLogFactory',
    'PlayNotificationFactory',
    'StopNotificationFactory',
    'PauseNotificationFactory',
    'ResumeNotificationFactory',
    'ErrorNotificationFactory',
    'FailedNotifyLogFactory',
]
