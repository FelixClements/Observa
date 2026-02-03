from sqlalchemy import DateTime, Identity, Integer, MetaData
from sqlalchemy.orm import DeclarativeBase, mapped_column


NAMING_CONVENTION = {
    'ix': 'ix_%(table_name)s_%(column_0_name)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'ck': 'ck_%(table_name)s_%(constraint_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s',
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def auto_pk():
    return mapped_column(Integer, Identity(always=False), primary_key=True)


def explicit_pk():
    return mapped_column(Integer, primary_key=True, autoincrement=False)


UTCDateTime = DateTime(timezone=True)


from plexpy.db.models.common import VersionInfo
from plexpy.db.models.exports import Export
from plexpy.db.models.history import SessionHistory, SessionHistoryMediaInfo, SessionHistoryMetadata
from plexpy.db.models.libraries import LibrarySection, RecentlyAdded
from plexpy.db.models.lookups import (
    CloudinaryLookup,
    ImageHashLookup,
    ImgurLookup,
    MusicbrainzLookup,
    TheMovieDbLookup,
    TvmazeLookup,
)
from plexpy.db.models.mobile import MobileDevice
from plexpy.db.models.newsletters import Newsletter, NewsletterLog
from plexpy.db.models.notifications import Notifier, NotifyLog
from plexpy.db.models.sessions import Session, SessionContinued
from plexpy.db.models.users import User, UserLogin


__all__ = [
    'Base',
    'UTCDateTime',
    'auto_pk',
    'explicit_pk',
    'CloudinaryLookup',
    'Export',
    'ImageHashLookup',
    'ImgurLookup',
    'LibrarySection',
    'MobileDevice',
    'MusicbrainzLookup',
    'Newsletter',
    'NewsletterLog',
    'Notifier',
    'NotifyLog',
    'RecentlyAdded',
    'Session',
    'SessionContinued',
    'SessionHistory',
    'SessionHistoryMediaInfo',
    'SessionHistoryMetadata',
    'TheMovieDbLookup',
    'TvmazeLookup',
    'User',
    'UserLogin',
    'VersionInfo',
]
