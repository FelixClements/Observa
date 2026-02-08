from typing import Optional
from pydantic import BaseModel, ConfigDict


class NewsletterDTO(BaseModel):
    id: int
    uuid: Optional[str] = None
    newsletter_id: Optional[int] = None
    user_id: Optional[int] = None
    friendly_name: Optional[str] = None
    filename: Optional[str] = None
    file_path: Optional[str] = None
    mime_type: Optional[str] = None
    timestamp: Optional[int] = None
    event_type: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class NewsletterLogDTO(BaseModel):
    id: int
    newsletter_id: Optional[int] = None
    uuid: Optional[str] = None
    timestamp: Optional[int] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    notifier_id: Optional[int] = None
    notify_action: Optional[str] = None
    success: Optional[int] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


__all__ = [
    'NewsletterDTO',
    'NewsletterLogDTO',
]
