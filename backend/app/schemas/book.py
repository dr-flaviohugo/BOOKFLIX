from pydantic import BaseModel


class ChapterSummary(BaseModel):
    chapter_index: int
    title: str
    chunk_count: int


class BookCreateResponse(BaseModel):
    id: str
    title: str
    author: str | None = None
    chapters: int


class BookDetailResponse(BaseModel):
    id: str
    title: str
    author: str | None = None
    chapters: list[ChapterSummary]
