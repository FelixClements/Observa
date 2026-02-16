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
Test factories for User and UserLogin models.
"""

import factory
from factory import Faker as FactoryFaker

from plexpy.db.models.users import User, UserLogin
from tests.factories.base import BaseFactory, TimestampFactoryMixin


class UserFactory(BaseFactory):
    """Factory for creating User model instances."""

    class Meta:
        model = User

    id = factory.Sequence(lambda n: n + 1)
    user_id = factory.Sequence(lambda n: n + 1000)
    username = FactoryFaker('user_name')
    friendly_name = FactoryFaker('first_name')
    thumb = FactoryFaker('image_url')
    custom_avatar_url = FactoryFaker('image_url')
    title = FactoryFaker('word')
    email = FactoryFaker('email')
    is_active = 1
    is_admin = 0
    is_home_user = factory.LazyAttribute(lambda o: 1 if o.username else 0)
    is_allow_sync = factory.LazyAttribute(lambda o: 1 if not o.is_restricted else 0)
    is_restricted = 0
    do_notify = 1
    keep_history = 1
    deleted_user = 0
    allow_guest = 0
    user_token = FactoryFaker('sha256')
    server_token = FactoryFaker('sha256')
    shared_libraries = factory.LazyAttribute(lambda o: ','.join(['1', '2', '3']))
    filter_all = None
    filter_tv = None
    filter_movies = None
    filter_music = None
    filter_photos = None


class AdminUserFactory(UserFactory):
    """Factory for creating admin User instances."""

    is_admin = 1
    username = FactoryFaker('user_name')
    email = FactoryFaker('company_email')


class HomeUserFactory(UserFactory):
    """Factory for creating home user instances."""

    is_home_user = 1
    allow_guest = 1


class InactiveUserFactory(UserFactory):
    """Factory for creating inactive/deleted user instances."""

    is_active = 0
    deleted_user = 1


class RestrictedUserFactory(UserFactory):
    """Factory for creating restricted user instances."""

    is_restricted = 1
    is_allow_sync = 0
    do_notify = 0


class UserLoginFactory(BaseFactory, TimestampFactoryMixin):
    """Factory for creating UserLogin model instances."""

    class Meta:
        model = UserLogin

    id = factory.Sequence(lambda n: n + 1)
    timestamp = factory.LazyAttribute(lambda o: o.timestamp)
    user_id = factory.LazyAttribute(lambda o: UserFactory().user_id)
    user = FactoryFaker('user_name')
    user_group = FactoryFaker('word')
    ip_address = FactoryFaker('ipv4')
    host = FactoryFaker('hostname')
    user_agent = FactoryFaker('user_agent')
    success = 1
    expiry = None
    jwt_token = FactoryFaker('sha256')


class FailedLoginFactory(UserLoginFactory):
    """Factory for creating failed login instances."""

    success = 0
    jwt_token = None


class SuccessfulLoginFactory(UserLoginFactory):
    """Factory for creating successful login instances."""

    success = 1
