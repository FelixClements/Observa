from typing import Optional

from sqlalchemy import Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from plexpy.db.models import Base, auto_pk


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = auto_pk()
    user_id: Mapped[Optional[int]] = mapped_column(Integer, unique=True)
    username: Mapped[str] = mapped_column(Text, nullable=False)
    friendly_name: Mapped[Optional[str]] = mapped_column(Text)
    thumb: Mapped[Optional[str]] = mapped_column(Text)
    custom_avatar_url: Mapped[Optional[str]] = mapped_column(Text)
    title: Mapped[Optional[str]] = mapped_column(Text)
    email: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('1'))
    is_admin: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
    is_home_user: Mapped[Optional[int]] = mapped_column(Integer)
    is_allow_sync: Mapped[Optional[int]] = mapped_column(Integer)
    is_restricted: Mapped[Optional[int]] = mapped_column(Integer)
    do_notify: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('1'))
    keep_history: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('1'))
    deleted_user: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
    allow_guest: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
    user_token: Mapped[Optional[str]] = mapped_column(Text)
    server_token: Mapped[Optional[str]] = mapped_column(Text)
    shared_libraries: Mapped[Optional[str]] = mapped_column(Text)
    filter_all: Mapped[Optional[str]] = mapped_column(Text)
    filter_movies: Mapped[Optional[str]] = mapped_column(Text)
    filter_tv: Mapped[Optional[str]] = mapped_column(Text)
    filter_music: Mapped[Optional[str]] = mapped_column(Text)
    filter_photos: Mapped[Optional[str]] = mapped_column(Text)


class UserLogin(Base):
    __tablename__ = 'user_login'

    id: Mapped[int] = auto_pk()
    timestamp: Mapped[Optional[int]] = mapped_column(Integer)
    user_id: Mapped[Optional[int]] = mapped_column(Integer)
    user: Mapped[Optional[str]] = mapped_column(Text)
    user_group: Mapped[Optional[str]] = mapped_column(Text)
    ip_address: Mapped[Optional[str]] = mapped_column(Text)
    host: Mapped[Optional[str]] = mapped_column(Text)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    success: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('1'))
    expiry: Mapped[Optional[str]] = mapped_column(Text)
    jwt_token: Mapped[Optional[str]] = mapped_column(Text)
