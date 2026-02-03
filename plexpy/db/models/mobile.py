from typing import Optional

from sqlalchemy import Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from plexpy.db.models import Base, auto_pk


class MobileDevice(Base):
    __tablename__ = 'mobile_devices'

    id: Mapped[int] = auto_pk()
    device_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    device_token: Mapped[Optional[str]] = mapped_column(Text)
    device_name: Mapped[Optional[str]] = mapped_column(Text)
    platform: Mapped[Optional[str]] = mapped_column(Text)
    version: Mapped[Optional[str]] = mapped_column(Text)
    friendly_name: Mapped[Optional[str]] = mapped_column(Text)
    onesignal_id: Mapped[Optional[str]] = mapped_column(Text)
    last_seen: Mapped[Optional[int]] = mapped_column(Integer)
    official: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
