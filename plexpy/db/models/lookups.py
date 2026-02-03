from typing import Optional

from sqlalchemy import Index, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from plexpy.db.models import Base, auto_pk


class TvmazeLookup(Base):
    __tablename__ = 'tvmaze_lookup'
    __table_args__ = (
        Index('idx_tvmaze_lookup', 'rating_key', unique=True),
    )

    id: Mapped[int] = auto_pk()
    rating_key: Mapped[Optional[int]] = mapped_column(Integer)
    thetvdb_id: Mapped[Optional[int]] = mapped_column(Integer)
    imdb_id: Mapped[Optional[str]] = mapped_column(Text)
    tvmaze_id: Mapped[Optional[int]] = mapped_column(Integer)
    tvmaze_url: Mapped[Optional[str]] = mapped_column(Text)
    tvmaze_json: Mapped[Optional[str]] = mapped_column(Text)


class TheMovieDbLookup(Base):
    __tablename__ = 'themoviedb_lookup'
    __table_args__ = (
        Index('idx_themoviedb_lookup', 'rating_key', unique=True),
    )

    id: Mapped[int] = auto_pk()
    rating_key: Mapped[Optional[int]] = mapped_column(Integer)
    thetvdb_id: Mapped[Optional[int]] = mapped_column(Integer)
    imdb_id: Mapped[Optional[str]] = mapped_column(Text)
    themoviedb_id: Mapped[Optional[int]] = mapped_column(Integer)
    themoviedb_url: Mapped[Optional[str]] = mapped_column(Text)
    themoviedb_json: Mapped[Optional[str]] = mapped_column(Text)


class MusicbrainzLookup(Base):
    __tablename__ = 'musicbrainz_lookup'
    __table_args__ = (
        Index('idx_musicbrainz_lookup', 'rating_key', unique=True),
    )

    id: Mapped[int] = auto_pk()
    rating_key: Mapped[Optional[int]] = mapped_column(Integer)
    musicbrainz_id: Mapped[Optional[int]] = mapped_column(Integer)
    musicbrainz_url: Mapped[Optional[str]] = mapped_column(Text)
    musicbrainz_type: Mapped[Optional[str]] = mapped_column(Text)
    musicbrainz_json: Mapped[Optional[str]] = mapped_column(Text)


class ImageHashLookup(Base):
    __tablename__ = 'image_hash_lookup'
    __table_args__ = (
        Index('idx_image_hash_lookup', 'img_hash', unique=True),
    )

    id: Mapped[int] = auto_pk()
    img_hash: Mapped[Optional[str]] = mapped_column(Text, unique=True)
    img: Mapped[Optional[str]] = mapped_column(Text)
    rating_key: Mapped[Optional[int]] = mapped_column(Integer)
    width: Mapped[Optional[int]] = mapped_column(Integer)
    height: Mapped[Optional[int]] = mapped_column(Integer)
    opacity: Mapped[Optional[int]] = mapped_column(Integer)
    background: Mapped[Optional[str]] = mapped_column(Text)
    blur: Mapped[Optional[int]] = mapped_column(Integer)
    fallback: Mapped[Optional[str]] = mapped_column(Text)


class ImgurLookup(Base):
    __tablename__ = 'imgur_lookup'
    __table_args__ = (
        Index('idx_imgur_lookup', 'img_hash', unique=True),
    )

    id: Mapped[int] = auto_pk()
    img_hash: Mapped[Optional[str]] = mapped_column(Text)
    imgur_title: Mapped[Optional[str]] = mapped_column(Text)
    imgur_url: Mapped[Optional[str]] = mapped_column(Text)
    delete_hash: Mapped[Optional[str]] = mapped_column(Text)


class CloudinaryLookup(Base):
    __tablename__ = 'cloudinary_lookup'
    __table_args__ = (
        Index('idx_cloudinary_lookup', 'img_hash', unique=True),
    )

    id: Mapped[int] = auto_pk()
    img_hash: Mapped[Optional[str]] = mapped_column(Text)
    cloudinary_title: Mapped[Optional[str]] = mapped_column(Text)
    cloudinary_url: Mapped[Optional[str]] = mapped_column(Text)
