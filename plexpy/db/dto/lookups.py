from typing import Optional
from pydantic import BaseModel, ConfigDict


class CloudinaryLookupDTO(BaseModel):
    id: int
    public_id: Optional[str] = None
    version: Optional[int] = None
    format: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    bytes: Optional[int] = None
    timestamp: Optional[int] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ImgurLookupDTO(BaseModel):
    id: int
    imgur_id: Optional[str] = None
    link: Optional[str] = None
    deletehash: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    timestamp: Optional[int] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ImageHashLookupDTO(BaseModel):
    id: int
    img_hash: Optional[str] = None
    img: Optional[str] = None
    timestamp: Optional[int] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TheMovieDbLookupDTO(BaseModel):
    id: int
    rating_key: Optional[int] = None
    rating_key_type: Optional[str] = None
    ext: Optional[str] = None
    data: Optional[str] = None
    timestamp: Optional[int] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TvmazeLookupDTO(BaseModel):
    id: int
    rating_key: Optional[int] = None
    rating_key_type: Optional[str] = None
    ext: Optional[str] = None
    data: Optional[str] = None
    timestamp: Optional[int] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class MusicbrainzLookupDTO(BaseModel):
    id: int
    recording_id: Optional[str] = None
    data: Optional[str] = None
    timestamp: Optional[int] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


__all__ = [
    'CloudinaryLookupDTO',
    'ImgurLookupDTO',
    'ImageHashLookupDTO',
    'TheMovieDbLookupDTO',
    'TvmazeLookupDTO',
    'MusicbrainzLookupDTO',
]
