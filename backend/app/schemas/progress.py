from datetime import datetime

from pydantic import BaseModel


class ProgressUpdateRequest(BaseModel):
    session_id: str
    book_id: str
    chapter_index: int
    position_seconds: float


class ProgressResponse(BaseModel):
    session_id: str
    book_id: str
    chapter_index: int
    position_seconds: float
    updated_at: datetime


class BookmarkCreateRequest(BaseModel):
    session_id: str
    book_id: str
    chapter_index: int
    position_seconds: float
    note: str | None = None


class BookmarkResponse(BaseModel):
    id: int
    session_id: str
    book_id: str
    chapter_index: int
    position_seconds: float
    note: str | None = None
    created_at: datetime
