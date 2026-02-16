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
Base factory class with common patterns for Observa test factories.
"""

import factory
from factory import Faker as FactoryFaker


class BaseFactory(factory.Factory):
    """Base factory class providing common patterns for all model factories."""

    class Meta:
        abstract = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override to handle SQLAlchemy model creation if needed."""
        return model_class(*args, **kwargs)

    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        """Override to handle SQLAlchemy model building if needed."""
        return model_class(*args, **kwargs)


class TimestampFactoryMixin:
    """Mixin for adding timestamp generation."""

    @factory.lazy_attribute
    def timestamp(self):
        """Generate a current timestamp."""
        import time
        return int(time.time())


class NullableMixin:
    """Mixin to make fields nullable for testing optional relationships."""

    @classmethod
    def _meta_with_relations(cls):
        """Return a dict with nullable foreign keys."""
        return {}
