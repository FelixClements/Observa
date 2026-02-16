# -*- coding: utf-8 -*-

#  This file is part of Tautulli.
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
Lookup Repository

Provides data access for all lookup models (TVmaze, TMDB, Musicbrainz, etc.)
"""
from typing import Optional

from sqlalchemy import select

from plexpy.db.models import (
    TvmazeLookup,
    TheMovieDbLookup,
    MusicbrainzLookup,
    ImageHashLookup,
    ImgurLookup,
    CloudinaryLookup,
)
from plexpy.db.repository.async_base import AdvancedAsyncRepository


class TvmazeLookupRepository(AdvancedAsyncRepository[TvmazeLookup]):
    """Repository for TvmazeLookup model."""

    async def get_by_rating_key(
        self,
        rating_key: int,
    ) -> Optional[TvmazeLookup]:
        """Get TVmaze lookup by rating_key."""
        stmt = select(TvmazeLookup).where(TvmazeLookup.rating_key == rating_key)
        result = await self.execute_statement(stmt)
        return result.scalar_one_or_none()


class TheMovieDbLookupRepository(AdvancedAsyncRepository[TheMovieDbLookup]):
    """Repository for TheMovieDbLookup model."""

    async def get_by_rating_key(
        self,
        rating_key: int,
    ) -> Optional[TheMovieDbLookup]:
        """Get TMDB lookup by rating_key."""
        stmt = select(TheMovieDbLookup).where(
            TheMovieDbLookup.rating_key == rating_key
        )
        result = await self.execute_statement(stmt)
        return result.scalar_one_or_none()


class MusicbrainzLookupRepository(AdvancedAsyncRepository[MusicbrainzLookup]):
    """Repository for MusicbrainzLookup model."""

    async def get_by_rating_key(
        self,
        rating_key: int,
    ) -> Optional[MusicbrainzLookup]:
        """Get Musicbrainz lookup by rating_key."""
        stmt = select(MusicbrainzLookup).where(
            MusicbrainzLookup.rating_key == rating_key
        )
        result = await self.execute_statement(stmt)
        return result.scalar_one_or_none()


class ImageHashLookupRepository(AdvancedAsyncRepository[ImageHashLookup]):
    """Repository for ImageHashLookup model."""

    async def get_by_hash(self, img_hash: str) -> Optional[ImageHashLookup]:
        """Get image hash lookup by hash."""
        stmt = select(ImageHashLookup).where(ImageHashLookup.img_hash == img_hash)
        result = await self.execute_statement(stmt)
        return result.scalar_one_or_none()


class ImgurLookupRepository(AdvancedAsyncRepository[ImgurLookup]):
    """Repository for ImgurLookup model."""

    async def get_by_hash(self, img_hash: str) -> Optional[ImgurLookup]:
        """Get Imgur lookup by hash."""
        stmt = select(ImgurLookup).where(ImgurLookup.img_hash == img_hash)
        result = await self.execute_statement(stmt)
        return result.scalar_one_or_none()


class CloudinaryLookupRepository(AdvancedAsyncRepository[CloudinaryLookup]):
    """Repository for CloudinaryLookup model."""

    async def get_by_hash(self, img_hash: str) -> Optional[CloudinaryLookup]:
        """Get Cloudinary lookup by hash."""
        stmt = select(CloudinaryLookup).where(CloudinaryLookup.img_hash == img_hash)
        result = await self.execute_statement(stmt)
        return result.scalar_one_or_none()


__all__ = [
    'TvmazeLookupRepository',
    'TheMovieDbLookupRepository',
    'MusicbrainzLookupRepository',
    'ImageHashLookupRepository',
    'ImgurLookupRepository',
    'CloudinaryLookupRepository',
]
