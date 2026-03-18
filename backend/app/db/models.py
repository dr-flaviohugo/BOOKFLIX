from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Book(Base):
    __tablename__ = "books"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    title: Mapped[str] = mapped_column(String(300), index=True)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    original_file: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    chapters: Mapped[list["Chapter"]] = relationship(back_populates="book", cascade="all, delete-orphan")


class Chapter(Base):
    __tablename__ = "chapters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_id: Mapped[str] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), index=True)
    chapter_index: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(300))
    text: Mapped[str] = mapped_column(Text)

    book: Mapped[Book] = relationship(back_populates="chapters")
    chunks: Mapped[list["ChapterChunk"]] = relationship(back_populates="chapter", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("book_id", "chapter_index", name="uq_book_chapter_index"),)


class ChapterChunk(Base):
    __tablename__ = "chapter_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("chapters.id", ondelete="CASCADE"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, index=True)
    text: Mapped[str] = mapped_column(Text)
    estimated_duration_seconds: Mapped[float] = mapped_column(Float)
    audio_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    chapter: Mapped[Chapter] = relationship(back_populates="chunks")

    __table_args__ = (UniqueConstraint("chapter_id", "chunk_index", name="uq_chapter_chunk_index"),)


class UserProgress(Base):
    __tablename__ = "user_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(100), index=True)
    book_id: Mapped[str] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), index=True)
    chapter_index: Mapped[int] = mapped_column(Integer)
    position_seconds: Mapped[float] = mapped_column(Float)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint("session_id", "book_id", name="uq_session_book_progress"),)


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(100), index=True)
    book_id: Mapped[str] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), index=True)
    chapter_index: Mapped[int] = mapped_column(Integer)
    position_seconds: Mapped[float] = mapped_column(Float)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
