from pathlib import Path
import hashlib

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Book, Chapter, ChapterChunk
from app.db.session import get_db
from app.schemas.book import BookCreateResponse, BookDetailResponse, ChapterSummary
from app.services.chunk_service import estimate_duration_seconds, split_text_into_chunks
from app.services.epub_service import parse_epub

router = APIRouter(prefix="/api/v1/books", tags=["books"])


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


@router.post("/upload", response_model=BookCreateResponse)
async def upload_epub(file: UploadFile = File(...), db: Session = Depends(get_db)) -> BookCreateResponse:
    if not file.filename or not file.filename.lower().endswith(".epub"):
        raise HTTPException(status_code=400, detail="Envie um arquivo EPUB valido")

    storage_dir = Path("storage") / "epubs"
    storage_dir.mkdir(parents=True, exist_ok=True)
    file_path = storage_dir / file.filename

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Arquivo excede limite de 50MB")

    if file_path.exists():
        raise HTTPException(status_code=409, detail="Este arquivo EPUB ja existe na biblioteca")

    upload_hash = _sha256_bytes(content)
    for existing_file in storage_dir.glob("*.epub"):
        if existing_file.is_file() and _sha256_file(existing_file) == upload_hash:
            raise HTTPException(status_code=409, detail="Este EPUB ja foi enviado anteriormente")

    file_path.write_bytes(content)

    try:
        parsed = parse_epub(file_path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Falha ao processar EPUB: {exc}") from exc

    book = Book(title=parsed.title, author=parsed.author, original_file=str(file_path))
    db.add(book)
    db.flush()

    for idx, chapter_data in enumerate(parsed.chapters):
        chapter = Chapter(
            book_id=book.id,
            chapter_index=idx,
            title=chapter_data.title,
            text=chapter_data.text,
        )
        db.add(chapter)
        db.flush()

        chunks = split_text_into_chunks(chapter_data.text)
        for chunk_idx, chunk_text in enumerate(chunks):
            db.add(
                ChapterChunk(
                    chapter_id=chapter.id,
                    chunk_index=chunk_idx,
                    text=chunk_text,
                    estimated_duration_seconds=estimate_duration_seconds(chunk_text),
                )
            )

    db.commit()
    return BookCreateResponse(id=book.id, title=book.title, author=book.author, chapters=len(parsed.chapters))


@router.get("/{book_id}", response_model=BookDetailResponse)
def get_book(book_id: str, db: Session = Depends(get_db)) -> BookDetailResponse:
    stmt = select(Book).where(Book.id == book_id).options(selectinload(Book.chapters).selectinload(Chapter.chunks))
    book = db.scalar(stmt)
    if not book:
        raise HTTPException(status_code=404, detail="Livro nao encontrado")

    chapter_list = [
        ChapterSummary(
            chapter_index=chapter.chapter_index,
            title=chapter.title,
            chunk_count=len(chapter.chunks),
        )
        for chapter in sorted(book.chapters, key=lambda c: c.chapter_index)
    ]

    return BookDetailResponse(id=book.id, title=book.title, author=book.author, chapters=chapter_list)


@router.get("")
def list_books(db: Session = Depends(get_db)) -> list[BookCreateResponse]:
    books = db.scalars(select(Book).order_by(Book.created_at.desc())).all()
    return [
        BookCreateResponse(
            id=book.id,
            title=book.title,
            author=book.author,
            chapters=len(book.chapters),
        )
        for book in books
    ]


@router.delete("/{book_id}")
def delete_book(book_id: str, db: Session = Depends(get_db)) -> dict[str, str]:
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Livro nao encontrado")

    epub_path = Path(book.original_file)
    db.delete(book)
    db.commit()

    if epub_path.exists() and epub_path.is_file():
        epub_path.unlink()

    return {"detail": "Livro removido com sucesso"}
