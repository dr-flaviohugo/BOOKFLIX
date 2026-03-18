from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Bookmark, UserProgress
from app.db.session import get_db
from app.schemas.progress import BookmarkCreateRequest, BookmarkResponse, ProgressResponse, ProgressUpdateRequest

router = APIRouter(prefix="/api/v1", tags=["progress"])


@router.post("/progress", response_model=ProgressResponse)
def save_progress(payload: ProgressUpdateRequest, db: Session = Depends(get_db)) -> ProgressResponse:
    progress = db.scalar(
        select(UserProgress).where(
            UserProgress.session_id == payload.session_id,
            UserProgress.book_id == payload.book_id,
        )
    )

    if not progress:
        progress = UserProgress(
            session_id=payload.session_id,
            book_id=payload.book_id,
            chapter_index=payload.chapter_index,
            position_seconds=payload.position_seconds,
        )
        db.add(progress)
    else:
        progress.chapter_index = payload.chapter_index
        progress.position_seconds = payload.position_seconds

    db.commit()
    db.refresh(progress)

    return ProgressResponse(
        session_id=progress.session_id,
        book_id=progress.book_id,
        chapter_index=progress.chapter_index,
        position_seconds=progress.position_seconds,
        updated_at=progress.updated_at,
    )


@router.get("/progress/{session_id}/{book_id}", response_model=ProgressResponse)
def get_progress(session_id: str, book_id: str, db: Session = Depends(get_db)) -> ProgressResponse:
    progress = db.scalar(
        select(UserProgress).where(
            UserProgress.session_id == session_id,
            UserProgress.book_id == book_id,
        )
    )
    if not progress:
        raise HTTPException(status_code=404, detail="Progresso nao encontrado")

    return ProgressResponse(
        session_id=progress.session_id,
        book_id=progress.book_id,
        chapter_index=progress.chapter_index,
        position_seconds=progress.position_seconds,
        updated_at=progress.updated_at,
    )


@router.post("/bookmarks", response_model=BookmarkResponse)
def add_bookmark(payload: BookmarkCreateRequest, db: Session = Depends(get_db)) -> BookmarkResponse:
    bookmark = Bookmark(
        session_id=payload.session_id,
        book_id=payload.book_id,
        chapter_index=payload.chapter_index,
        position_seconds=payload.position_seconds,
        note=payload.note,
    )
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)
    return BookmarkResponse(
        id=bookmark.id,
        session_id=bookmark.session_id,
        book_id=bookmark.book_id,
        chapter_index=bookmark.chapter_index,
        position_seconds=bookmark.position_seconds,
        note=bookmark.note,
        created_at=bookmark.created_at,
    )


@router.get("/bookmarks/{session_id}/{book_id}", response_model=list[BookmarkResponse])
def list_bookmarks(session_id: str, book_id: str, db: Session = Depends(get_db)) -> list[BookmarkResponse]:
    rows = db.scalars(
        select(Bookmark)
        .where(Bookmark.session_id == session_id, Bookmark.book_id == book_id)
        .order_by(Bookmark.created_at.desc())
    ).all()

    return [
        BookmarkResponse(
            id=row.id,
            session_id=row.session_id,
            book_id=row.book_id,
            chapter_index=row.chapter_index,
            position_seconds=row.position_seconds,
            note=row.note,
            created_at=row.created_at,
        )
        for row in rows
    ]
