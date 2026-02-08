from typing import Optional
from pydantic import BaseModel, ConfigDict


class LibrarySectionDTO(BaseModel):
    section_id: int
    section_name: Optional[str] = None
    section_type: Optional[str] = None
    library_name: Optional[str] = None
    library_thumb: Optional[str] = None
    library_art: Optional[str] = None
    user_thumb: Optional[str] = None
    user_art: Optional[str] = None
    count: Optional[int] = None
    parent_count: Optional[int] = None
    child_count: Optional[int] = None
    last_accessed: Optional[int] = None
    date_created: Optional[int] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class RecentlyAddedDTO(BaseModel):
    id: int
    rating_key: Optional[int] = None
    parent_rating_key: Optional[int] = None
    grandparent_rating_key: Optional[int] = None
    title: Optional[str] = None
    parent_title: Optional[str] = None
    grandparent_title: Optional[str] = None
    full_title: Optional[str] = None
    media_type: Optional[str] = None
    section_id: Optional[int] = None
    thumb: Optional[str] = None
    parent_thumb: Optional[str] = None
    grandparent_thumb: Optional[str] = None
    art: Optional[str] = None
    duration: Optional[int] = None
    added_at: Optional[int] = None
    year: Optional[int] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


__all__ = [
    'LibrarySectionDTO',
    'RecentlyAddedDTO',
]
