# -*- coding: utf-8 -*-

# This file is part of Tautulli.
#
#  Tautulli is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Tautulli is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Tautulli.  If not, see <http://www.gnu.org/licenses/>.

"""
Integrations layer dependency injection helpers.

This module provides config dependency injection for the integrations layer,
following the pattern established in the services layer.
"""

from functools import lru_cache

from plexpy.config import core as config_module


@lru_cache(maxsize=1)
def _get_config():
    """Get config instance with caching for integrations layer."""
    return config_module.get_config()


def get_config():
    """Get the current config instance for integrations layer."""
    return _get_config()


def clear_config_cache():
    """Clear the config cache (useful for testing)."""
    _get_config.cache_clear()
