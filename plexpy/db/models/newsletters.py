from typing import Optional

from sqlalchemy import Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from plexpy.db.models import Base, auto_pk


class Newsletter(Base):
    __tablename__ = 'newsletters'

    id: Mapped[int] = auto_pk()
    agent_id: Mapped[Optional[int]] = mapped_column(Integer)
    agent_name: Mapped[Optional[str]] = mapped_column(Text)
    agent_label: Mapped[Optional[str]] = mapped_column(Text)
    id_name: Mapped[str] = mapped_column(Text, nullable=False)
    friendly_name: Mapped[Optional[str]] = mapped_column(Text)
    newsletter_config: Mapped[Optional[str]] = mapped_column(Text)
    email_config: Mapped[Optional[str]] = mapped_column(Text)
    subject: Mapped[Optional[str]] = mapped_column(Text)
    body: Mapped[Optional[str]] = mapped_column(Text)
    message: Mapped[Optional[str]] = mapped_column(Text)
    cron: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'0 0 * * 0'"))
    active: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))


class NewsletterLog(Base):
    __tablename__ = 'newsletter_log'

    id: Mapped[int] = auto_pk()
    timestamp: Mapped[Optional[int]] = mapped_column(Integer)
    newsletter_id: Mapped[Optional[int]] = mapped_column(Integer)
    agent_id: Mapped[Optional[int]] = mapped_column(Integer)
    agent_name: Mapped[Optional[str]] = mapped_column(Text)
    notify_action: Mapped[Optional[str]] = mapped_column(Text)
    subject_text: Mapped[Optional[str]] = mapped_column(Text)
    body_text: Mapped[Optional[str]] = mapped_column(Text)
    message_text: Mapped[Optional[str]] = mapped_column(Text)
    start_date: Mapped[Optional[str]] = mapped_column(Text)
    end_date: Mapped[Optional[str]] = mapped_column(Text)
    start_time: Mapped[Optional[int]] = mapped_column(Integer)
    end_time: Mapped[Optional[int]] = mapped_column(Integer)
    uuid: Mapped[Optional[str]] = mapped_column(Text, unique=True)
    filename: Mapped[Optional[str]] = mapped_column(Text)
    email_msg_id: Mapped[Optional[str]] = mapped_column(Text)
    success: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
