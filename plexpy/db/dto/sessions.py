from typing import Optional
from pydantic import BaseModel, ConfigDict


class SessionDTO(BaseModel):
    id: int
    session_key: Optional[int] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    user_type: Optional[int] = None
    rating_key: Optional[int] = None
    parent_rating_key: Optional[int] = None
    grandparent_rating_key: Optional[int] = None
    media_type: Optional[str] = None
    title: Optional[str] = None
    parent_title: Optional[str] = None
    grandparent_title: Optional[str] = None
    thumb: Optional[str] = None
    art: Optional[str] = None
    duration: Optional[int] = None
    started: Optional[int] = None
    stopped: Optional[int] = None
    paused_counter: Optional[int] = None
    state: Optional[str] = None
    view_offset: Optional[int] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class SessionContinuedDTO(BaseModel):
    id: int
    session_key: Optional[int] = None
    reference_id: Optional[int] = None
    parent_id: Optional[int] = None
    started: Optional[int] = None
    stopped: Optional[int] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ExportDTO(BaseModel):
    id: int
    export_type: Optional[str] = None
    filepath: Optional[str] = None
    filename: Optional[str] = None
    mimetype: Optional[str] = None
    timestamp: Optional[int] = None
    user_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class MobileDeviceDTO(BaseModel):
    id: int
    device_id: Optional[str] = None
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    friendly_name: Optional[str] = None
    user_id: Optional[int] = None
    token: Optional[str] = None
    last_seen: Optional[int] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


__all__ = [
    'SessionDTO',
    'SessionContinuedDTO',
    'ExportDTO',
    'MobileDeviceDTO',
]
