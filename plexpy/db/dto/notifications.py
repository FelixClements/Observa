from typing import Optional
from pydantic import BaseModel, ConfigDict


class NotifierDTO(BaseModel):
    id: int
    agent_id: Optional[int] = None
    agent_name: Optional[str] = None
    friendly_name: Optional[str] = None
    config: Optional[str] = None
    active: Optional[int] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class NotifyLogDTO(BaseModel):
    id: int
    notifier_id: Optional[int] = None
    timestamp: Optional[int] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    notify_action: Optional[str] = None
    success: Optional[int] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


__all__ = [
    'NotifierDTO',
    'NotifyLogDTO',
]
