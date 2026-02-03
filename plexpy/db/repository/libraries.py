from typing import Optional

from sqlalchemy import select

from plexpy.db.models import LibrarySection, RecentlyAdded
from plexpy.db.repository.base import Repository


class LibrariesRepository(Repository[LibrarySection]):
    model = LibrarySection

    def get_by_section_id(self, section_id: int, server_id: Optional[str] = None) -> Optional[LibrarySection]:
        stmt = select(LibrarySection).where(LibrarySection.section_id == section_id)
        if server_id is not None:
            stmt = stmt.where(LibrarySection.server_id == server_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_active(self):
        stmt = select(LibrarySection).where(LibrarySection.is_active == 1)
        return self.session.execute(stmt).scalars().all()


class RecentlyAddedRepository(Repository[RecentlyAdded]):
    model = RecentlyAdded

    def list_recent(self, limit: int = 100):
        stmt = select(RecentlyAdded).order_by(RecentlyAdded.added_at.desc()).limit(limit)
        return self.session.execute(stmt).scalars().all()
