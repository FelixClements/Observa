from typing import Optional

from sqlalchemy import Integer, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from plexpy.db.models import Base, auto_pk


class LibrarySection(Base):
    __tablename__ = 'library_sections'
    __table_args__ = (
        UniqueConstraint('server_id', 'section_id'),
    )

    id: Mapped[int] = auto_pk()
    server_id: Mapped[Optional[str]] = mapped_column(Text)
    section_id: Mapped[Optional[int]] = mapped_column(Integer)
    section_name: Mapped[Optional[str]] = mapped_column(Text)
    section_type: Mapped[Optional[str]] = mapped_column(Text)
    agent: Mapped[Optional[str]] = mapped_column(Text)
    thumb: Mapped[Optional[str]] = mapped_column(Text)
    custom_thumb_url: Mapped[Optional[str]] = mapped_column(Text)
    art: Mapped[Optional[str]] = mapped_column(Text)
    custom_art_url: Mapped[Optional[str]] = mapped_column(Text)
    count: Mapped[Optional[int]] = mapped_column(Integer)
    parent_count: Mapped[Optional[int]] = mapped_column(Integer)
    child_count: Mapped[Optional[int]] = mapped_column(Integer)
    is_active: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('1'))
    do_notify: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('1'))
    do_notify_created: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('1'))
    keep_history: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('1'))
    deleted_section: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))


class RecentlyAdded(Base):
    __tablename__ = 'recently_added'

    id: Mapped[int] = auto_pk()
    added_at: Mapped[Optional[int]] = mapped_column(Integer)
    pms_identifier: Mapped[Optional[str]] = mapped_column(Text)
    section_id: Mapped[Optional[int]] = mapped_column(Integer)
    rating_key: Mapped[Optional[int]] = mapped_column(Integer)
    parent_rating_key: Mapped[Optional[int]] = mapped_column(Integer)
    grandparent_rating_key: Mapped[Optional[int]] = mapped_column(Integer)
    media_type: Mapped[Optional[str]] = mapped_column(Text)
    media_info: Mapped[Optional[str]] = mapped_column(Text)
