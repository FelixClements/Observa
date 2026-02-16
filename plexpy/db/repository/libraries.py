from typing import Optional

from sqlalchemy import select

from plexpy.db.models import LibrarySection, RecentlyAdded
from plexpy.db.repository.base import Repository, DataTableParams, DataTableResponse


class LibrariesRepository(Repository[LibrarySection]):
    model = LibrarySection

    # Searchable columns for datatable queries
    _SEARCHABLE_COLUMNS = [
        LibrarySection.section_name,
        LibrarySection.section_type,
        LibrarySection.agent,
    ]

    # Orderable columns for datatable queries
    _ORDERABLE_COLUMNS = {
        'id': LibrarySection.id,
        'server_id': LibrarySection.server_id,
        'section_id': LibrarySection.section_id,
        'section_name': LibrarySection.section_name,
        'section_type': LibrarySection.section_type,
        'agent': LibrarySection.agent,
        'thumb': LibrarySection.thumb,
        'custom_thumb_url': LibrarySection.custom_thumb_url,
        'art': LibrarySection.art,
        'custom_art_url': LibrarySection.custom_art_url,
        'count': LibrarySection.count,
        'parent_count': LibrarySection.parent_count,
        'child_count': LibrarySection.child_count,
        'is_active': LibrarySection.is_active,
        'do_notify': LibrarySection.do_notify,
        'do_notify_created': LibrarySection.do_notify_created,
        'keep_history': LibrarySection.keep_history,
        'deleted_section': LibrarySection.deleted_section,
    }

    def get_by_section_id(self, section_id: int, server_id: Optional[str] = None) -> Optional[LibrarySection]:
        stmt = select(LibrarySection).where(LibrarySection.section_id == section_id)
        if server_id is not None:
            stmt = stmt.where(LibrarySection.server_id == server_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_active(self):
        stmt = select(LibrarySection).where(LibrarySection.is_active == 1)
        return self.session.execute(stmt).scalars().all()

    def datatable_query(
        self,
        params: DataTableParams,
        searchable_columns: list = None,
        orderable_columns: dict = None,
        formatter=None,
        extra_filters: list = None,
    ) -> DataTableResponse:
        """
        Execute a datatable query with search, sort, and pagination.
        """
        return super().datatable_query(
            params=params,
            searchable_columns=searchable_columns or self._SEARCHABLE_COLUMNS,
            orderable_columns=orderable_columns or self._ORDERABLE_COLUMNS,
            formatter=formatter,
            extra_filters=extra_filters,
        )


class RecentlyAddedRepository(Repository[RecentlyAdded]):
    model = RecentlyAdded

    # Searchable columns for datatable queries
    _SEARCHABLE_COLUMNS = [
        RecentlyAdded.pms_identifier,
        RecentlyAdded.media_type,
    ]

    # Orderable columns for datatable queries
    _ORDERABLE_COLUMNS = {
        'id': RecentlyAdded.id,
        'added_at': RecentlyAdded.added_at,
        'pms_identifier': RecentlyAdded.pms_identifier,
        'section_id': RecentlyAdded.section_id,
        'rating_key': RecentlyAdded.rating_key,
        'parent_rating_key': RecentlyAdded.parent_rating_key,
        'grandparent_rating_key': RecentlyAdded.grandparent_rating_key,
        'media_type': RecentlyAdded.media_type,
    }

    def list_recent(self, limit: int = 100):
        stmt = select(RecentlyAdded).order_by(RecentlyAdded.added_at.desc()).limit(limit)
        return self.session.execute(stmt).scalars().all()

    def datatable_query(
        self,
        params: DataTableParams,
        searchable_columns: list = None,
        orderable_columns: dict = None,
        formatter=None,
        extra_filters: list = None,
    ) -> DataTableResponse:
        """
        Execute a datatable query with search, sort, and pagination.
        """
        return super().datatable_query(
            params=params,
            searchable_columns=searchable_columns or self._SEARCHABLE_COLUMNS,
            orderable_columns=orderable_columns or self._ORDERABLE_COLUMNS,
            formatter=formatter,
            extra_filters=extra_filters,
        )
