from typing import Optional
from pydantic import BaseModel, field_validator, ConfigDict


class UserDTO(BaseModel):
    user_id: int
    username: Optional[str] = None
    friendly_name: Optional[str] = None
    email: Optional[str] = None
    thumb: Optional[str] = None
    is_active: Optional[int] = None
    deleted_user: Optional[int] = None
    last_seen: Optional[int] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class UserLoginDTO(BaseModel):
    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    token: Optional[str] = None
    ip: Optional[str] = None
    host: Optional[str] = None
    time: Optional[int] = None
    success: Optional[int] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


__all__ = [
    'UserDTO',
    'UserLoginDTO',
]
