from pathlib import Path
import re
from typing import Iterator

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Chapter, ChapterChunk
from app.db.session import get_db
from app.services.cache_service import CacheService
from app.services.tts_service import TTSService, TTSUnavailableError

router = APIRouter(prefix="/api/v1/audio", tags=["audio"])
settings = get_settings()
cache_service = CacheService(settings.BOOKFLIX_REDIS_URL, settings.BOOKFLIX_CACHE_TTL_SECONDS)
tts_service = TTSService()


def _cache_key(book_id: str, chapter_index: int, chunk_index: int) -> str:
    return f"audio:{book_id}:{chapter_index}:{chunk_index}"


def _audio_mime(path: Path) -> str:
    return "audio/wav" if path.suffix.lower() == ".wav" else "audio/mpeg"


def _iter_file(path: Path, chunk_size: int = 64 * 1024) -> Iterator[bytes]:
    with path.open("rb") as file_obj:
        while True:
            data = file_obj.read(chunk_size)
            if not data:
                break
            yield data


def _build_audio_response(path: Path, request: Request) -> Response:
    mime = _audio_mime(path)
    range_header = request.headers.get("range")

    if not range_header:
        return FileResponse(path=path, media_type=mime)

    # If the browser sends an out-of-bounds range (e.g. stale offset),
    # return full content instead of bubbling up 416.
    match = re.match(r"^bytes=(\d+)-", range_header.strip())
    if not match:
        return FileResponse(path=path, media_type=mime)

    start = int(match.group(1))
    file_size = path.stat().st_size
    if start < file_size:
        return FileResponse(path=path, media_type=mime)

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(file_size),
    }
    return StreamingResponse(_iter_file(path), media_type=mime, headers=headers, status_code=200)


@router.get("/{book_id}/chapter/{chapter_index}/chunk/{chunk_index}")
async def stream_chunk(
    book_id: str,
    chapter_index: int,
    chunk_index: int,
    request: Request,
    db: Session = Depends(get_db),
) -> Response:
    chapter = db.scalar(
        select(Chapter).where(
            Chapter.book_id == book_id,
            Chapter.chapter_index == chapter_index,
        )
    )
    if not chapter:
        raise HTTPException(status_code=404, detail="Capitulo nao encontrado")

    chunk = db.scalar(
        select(ChapterChunk).where(
            ChapterChunk.chapter_id == chapter.id,
            ChapterChunk.chunk_index == chunk_index,
        )
    )
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk nao encontrado")

    key = _cache_key(book_id, chapter_index, chunk_index)
    cached_path = cache_service.get_audio_path(key)
    if cached_path and Path(cached_path).exists():
        return _build_audio_response(Path(cached_path), request)

    try:
        audio_path = await tts_service.synthesize_chunk(key, chunk.text)
    except TTSUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    chunk.audio_path = str(audio_path)
    db.commit()

    cache_service.set_audio_path(key, str(audio_path))
    return _build_audio_response(audio_path, request)


@router.get("/{book_id}/chapter/{chapter_index}/manifest")
def chapter_manifest(book_id: str, chapter_index: int, db: Session = Depends(get_db)) -> dict:
    chapter = db.scalar(
        select(Chapter).where(
            Chapter.book_id == book_id,
            Chapter.chapter_index == chapter_index,
        )
    )
    if not chapter:
        raise HTTPException(status_code=404, detail="Capitulo nao encontrado")

    chunks = db.scalars(select(ChapterChunk).where(ChapterChunk.chapter_id == chapter.id).order_by(ChapterChunk.chunk_index)).all()
    return {
        "book_id": book_id,
        "chapter_index": chapter_index,
        "chapter_title": chapter.title,
        "total_chunks": len(chunks),
        "chunks": [
            {
                "chunk_index": chunk.chunk_index,
                "estimated_duration_seconds": chunk.estimated_duration_seconds,
                "stream_url": f"/api/v1/audio/{book_id}/chapter/{chapter_index}/chunk/{chunk.chunk_index}",
            }
            for chunk in chunks
        ],
    }
