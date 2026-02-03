from typing import Optional

from sqlalchemy import Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from plexpy.db.models import Base, auto_pk


class Export(Base):
    __tablename__ = 'exports'

    id: Mapped[int] = auto_pk()
    timestamp: Mapped[Optional[int]] = mapped_column(Integer)
    section_id: Mapped[Optional[int]] = mapped_column(Integer)
    user_id: Mapped[Optional[int]] = mapped_column(Integer)
    rating_key: Mapped[Optional[int]] = mapped_column(Integer)
    media_type: Mapped[Optional[str]] = mapped_column(Text)
    title: Mapped[Optional[str]] = mapped_column(Text)
    file_format: Mapped[Optional[str]] = mapped_column(Text)
    metadata_level: Mapped[Optional[int]] = mapped_column(Integer)
    media_info_level: Mapped[Optional[int]] = mapped_column(Integer)
    thumb_level: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
    art_level: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
    logo_level: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
    custom_fields: Mapped[Optional[str]] = mapped_column(Text)
    individual_files: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
    file_size: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
    complete: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
    exported_items: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
    total_items: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
