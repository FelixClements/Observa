from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, field_validator, ConfigDict


PLATFORM_NAME_OVERRIDES = {
    'Galaxy Note 10+': 'Samsung Galaxy Note 10+',
    'Galaxy S10': 'Samsung Galaxy S10',
    'Galaxy S10+': 'Samsung Galaxy S10+',
}


MOVIE_WATCHED_PERCENT = 90
TV_WATCHED_PERCENT = 85
MUSIC_WATCHED_PERCENT = 50


class SessionHistoryDTO(BaseModel):
    id: int
    reference_id: Optional[int] = None
    started: Optional[int] = None
    stopped: Optional[int] = None
    user_id: Optional[int] = None
    media_type: Optional[str] = None
    title: Optional[str] = None
    friendly_name: Optional[str] = None
    platform: Optional[str] = None

    @field_validator('platform', mode='before')
    @classmethod
    def normalize_platform(cls, v: Optional[str]) -> Optional[str]:
        if v in PLATFORM_NAME_OVERRIDES:
            return PLATFORM_NAME_OVERRIDES[v]
        return v

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class SessionHistoryMetadataDTO(BaseModel):
    id: int
    rating_key: Optional[int] = None
    parent_rating_key: Optional[int] = None
    grandparent_rating_key: Optional[int] = None
    title: Optional[str] = None
    parent_title: Optional[str] = None
    grandparent_title: Optional[str] = None
    full_title: Optional[str] = None
    media_type: Optional[str] = None
    year: Optional[int] = None
    duration: Optional[int] = None
    content_rating: Optional[str] = None
    summary: Optional[str] = None
    genres: Optional[str] = None
    studio: Optional[str] = None
    thumb: Optional[str] = None
    art: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class SessionHistoryMediaInfoDTO(BaseModel):
    id: int
    rating_key: Optional[int] = None
    video_decision: Optional[str] = None
    audio_decision: Optional[str] = None
    transcode_decision: Optional[str] = None
    duration: Optional[int] = None
    container: Optional[str] = None
    bitrate: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    video_codec: Optional[str] = None
    video_resolution: Optional[str] = None
    video_framerate: Optional[str] = None
    audio_codec: Optional[str] = None
    audio_channels: Optional[int] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class DataTableHistoryRowDTO(BaseModel):
    id: int
    reference_id: Optional[int] = None
    started: Optional[int] = None
    stopped: Optional[int] = None
    user_id: Optional[int] = None
    user: Optional[str] = None
    friendly_name: Optional[str] = None
    media_type: Optional[str] = None
    title: Optional[str] = None
    platform: Optional[str] = None
    watched_status: Optional[str] = None
    percent_complete: Optional[float] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


__all__ = [
    'SessionHistoryDTO',
    'SessionHistoryMetadataDTO',
    'SessionHistoryMediaInfoDTO',
    'DataTableHistoryRowDTO',
    'PLATFORM_NAME_OVERRIDES',
    'MOVIE_WATCHED_PERCENT',
    'TV_WATCHED_PERCENT',
    'MUSIC_WATCHED_PERCENT',
]
