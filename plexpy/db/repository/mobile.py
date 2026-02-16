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
Mobile Device Repository

Provides data access for MobileDevice model.
"""
from typing import Optional

from sqlalchemy import select

from plexpy.db.models import MobileDevice
from plexpy.db.repository.async_base import AdvancedAsyncRepository


class MobileDeviceRepository(AdvancedAsyncRepository[MobileDevice]):
    """Repository for MobileDevice model."""

    async def get_by_device_id(self, device_id: str) -> Optional[MobileDevice]:
        """Get mobile device by device_id."""
        stmt = select(MobileDevice).where(MobileDevice.device_id == device_id)
        result = await self.execute_statement(stmt)
        return result.scalar_one_or_none()

    async def get_by_onesignal_id(
        self,
        onesignal_id: str,
    ) -> Optional[MobileDevice]:
        """Get mobile device by OneSignal ID."""
        stmt = select(MobileDevice).where(MobileDevice.onesignal_id == onesignal_id)
        result = await self.execute_statement(stmt)
        return result.scalar_one_or_none()

    async def list_official(self) -> list[MobileDevice]:
        """List official mobile devices."""
        stmt = select(MobileDevice).where(MobileDevice.official == 1)
        result = await self.execute_statement(stmt)
        return list(result.scalars().all())


__all__ = [
    'MobileDeviceRepository',
]
