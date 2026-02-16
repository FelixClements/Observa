from typing import Optional

from sqlalchemy import select

from plexpy.db.models import Session, SessionContinued
from plexpy.db.repository.base import Repository, DataTableParams, DataTableResponse


class SessionsRepository(Repository[Session]):
    model = Session

    # Searchable columns for datatable queries
    _SEARCHABLE_COLUMNS = [
        Session.session_id,
        Session.user,
        Session.friendly_name,
        Session.ip_address,
        Session.machine_id,
        Session.player,
        Session.product,
        Session.platform,
        Session.title,
        Session.parent_title,
        Session.grandparent_title,
        Session.full_title,
    ]

    # Orderable columns for datatable queries
    _ORDERABLE_COLUMNS = {
        'id': Session.id,
        'session_key': Session.session_key,
        'session_id': Session.session_id,
        'transcode_key': Session.transcode_key,
        'rating_key': Session.rating_key,
        'section_id': Session.section_id,
        'media_type': Session.media_type,
        'started': Session.started,
        'stopped': Session.stopped,
        'paused_counter': Session.paused_counter,
        'state': Session.state,
        'user_id': Session.user_id,
        'user': Session.user,
        'friendly_name': Session.friendly_name,
        'ip_address': Session.ip_address,
        'machine_id': Session.machine_id,
        'bandwidth': Session.bandwidth,
        'location': Session.location,
        'player': Session.player,
        'product': Session.product,
        'platform': Session.platform,
        'title': Session.title,
        'parent_title': Session.parent_title,
        'grandparent_title': Session.grandparent_title,
    }

    def get_by_session_key(self, session_key: int) -> Optional[Session]:
        stmt = select(Session).where(Session.session_key == session_key)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_session_id(self, session_id: str) -> Optional[Session]:
        stmt = select(Session).where(Session.session_id == session_id)
        return self.session.execute(stmt).scalar_one_or_none()

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


class SessionsContinuedRepository(Repository[SessionContinued]):
    model = SessionContinued

    def get_by_identity(self, user_id: int, machine_id: str, media_type: str) -> Optional[SessionContinued]:
        stmt = select(SessionContinued).where(
            SessionContinued.user_id == user_id,
            SessionContinued.machine_id == machine_id,
            SessionContinued.media_type == media_type,
        )
        return self.session.execute(stmt).scalar_one_or_none()
