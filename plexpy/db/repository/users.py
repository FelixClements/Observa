from typing import Optional

from sqlalchemy import select

from plexpy.db.models import User, UserLogin
from plexpy.db.repository.base import Repository, DataTableParams, DataTableResponse


class UsersRepository(Repository[User]):
    model = User

    # Searchable columns for datatable queries
    _SEARCHABLE_COLUMNS = [
        User.username,
        User.friendly_name,
        User.email,
        User.title,
    ]

    # Orderable columns for datatable queries
    _ORDERABLE_COLUMNS = {
        'id': User.id,
        'user_id': User.user_id,
        'username': User.username,
        'friendly_name': User.friendly_name,
        'thumb': User.thumb,
        'custom_avatar_url': User.custom_avatar_url,
        'title': User.title,
        'email': User.email,
        'is_active': User.is_active,
        'is_admin': User.is_admin,
        'is_home_user': User.is_home_user,
        'is_allow_sync': User.is_allow_sync,
        'is_restricted': User.is_restricted,
        'do_notify': User.do_notify,
        'keep_history': User.keep_history,
        'deleted_user': User.deleted_user,
        'allow_guest': User.allow_guest,
    }

    def get_by_user_id(self, user_id: int) -> Optional[User]:
        stmt = select(User).where(User.user_id == user_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_username(self, username: str) -> Optional[User]:
        stmt = select(User).where(User.username == username)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_active(self):
        stmt = select(User).where(User.is_active == 1)
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


class UserLoginRepository(Repository[UserLogin]):
    model = UserLogin

    # Searchable columns for datatable queries
    _SEARCHABLE_COLUMNS = [
        UserLogin.user,
        UserLogin.user_group,
        UserLogin.ip_address,
        UserLogin.host,
        UserLogin.user_agent,
    ]

    # Orderable columns for datatable queries
    _ORDERABLE_COLUMNS = {
        'id': UserLogin.id,
        'timestamp': UserLogin.timestamp,
        'user_id': UserLogin.user_id,
        'user': UserLogin.user,
        'user_group': UserLogin.user_group,
        'ip_address': UserLogin.ip_address,
        'host': UserLogin.host,
        'user_agent': UserLogin.user_agent,
        'success': UserLogin.success,
    }

    def list_recent(self, limit: int = 100):
        stmt = select(UserLogin).order_by(UserLogin.timestamp.desc()).limit(limit)
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
