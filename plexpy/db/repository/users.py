from typing import Optional

from sqlalchemy import select

from plexpy.db.models import User, UserLogin
from plexpy.db.repository.base import Repository


class UsersRepository(Repository[User]):
    model = User

    def get_by_user_id(self, user_id: int) -> Optional[User]:
        stmt = select(User).where(User.user_id == user_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_username(self, username: str) -> Optional[User]:
        stmt = select(User).where(User.username == username)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_active(self):
        stmt = select(User).where(User.is_active == 1)
        return self.session.execute(stmt).scalars().all()


class UserLoginRepository(Repository[UserLogin]):
    model = UserLogin

    def list_recent(self, limit: int = 100):
        stmt = select(UserLogin).order_by(UserLogin.timestamp.desc()).limit(limit)
        return self.session.execute(stmt).scalars().all()
