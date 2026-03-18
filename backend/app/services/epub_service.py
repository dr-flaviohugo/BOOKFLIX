from dataclasses import dataclass
from pathlib import Path
import re

from bs4 import BeautifulSoup
from ebooklib import ITEM_DOCUMENT, epub


@dataclass
class ParsedChapter:
    title: str
    text: str


@dataclass
class ParsedBook:
    title: str
    author: str | None
    chapters: list[ParsedChapter]


_INLINE_CHAPTER_HEADING = re.compile(
    r"(?<!\w)(PR\S*LOGO|EP\S*LOGO|CAP\S*TULO\s+\d{1,3}|CHAPTER\s+\d{1,3})(?!\w)"
)


def _iter_ordered_documents(book: epub.EpubBook):
    seen_names: set[str] = set()

    # Prefer spine order when available to keep reading sequence.
    for item_id, _ in book.spine:
        item = book.get_item_with_id(item_id)
        if not item or item.get_type() != ITEM_DOCUMENT:
            continue
        name = item.get_name()
        if name in seen_names:
            continue
        seen_names.add(name)
        yield item

    # Keep fallback for EPUBs with incomplete spine data.
    for item in book.get_items_of_type(ITEM_DOCUMENT):
        name = item.get_name()
        if name in seen_names:
            continue
        seen_names.add(name)
        yield item


def _split_document_into_chapters(soup: BeautifulSoup, chapter_start: int) -> list[ParsedChapter]:
    full_text = soup.get_text(" ", strip=True)
    if not full_text:
        return []

    markers = list(_INLINE_CHAPTER_HEADING.finditer(full_text))
    if not markers:
        return [ParsedChapter(title=f"Capitulo {chapter_start}", text=full_text)]

    chapters: list[ParsedChapter] = []

    # Preserve introductory text before the first heading when it is substantive.
    preface_text = full_text[: markers[0].start()].strip()
    if len(preface_text) > 300:
        chapters.append(ParsedChapter(title=f"Capitulo {chapter_start}", text=preface_text))

    for index, marker in enumerate(markers):
        end = markers[index + 1].start() if index + 1 < len(markers) else len(full_text)
        chapter_text = full_text[marker.start() : end].strip()
        if len(chapter_text) < 80:
            continue
        chapter_title = marker.group(1).strip()
        chapters.append(ParsedChapter(title=chapter_title, text=chapter_text))

    if not chapters:
        return [ParsedChapter(title=f"Capitulo {chapter_start}", text=full_text)]

    return chapters


def parse_epub(epub_path: Path) -> ParsedBook:
    book = epub.read_epub(str(epub_path))

    title = "Livro sem titulo"
    title_metadata = book.get_metadata("DC", "title")
    if title_metadata:
        title = title_metadata[0][0]

    author = None
    author_metadata = book.get_metadata("DC", "creator")
    if author_metadata:
        author = author_metadata[0][0]

    chapters: list[ParsedChapter] = []
    for item in _iter_ordered_documents(book):
        item_name = item.get_name().lower()
        # Skip EPUB navigation/toc resources that are not content chapters.
        if "nav" in item_name or "toc" in item_name:
            continue

        raw_html = item.get_content()
        soup = BeautifulSoup(raw_html, "html.parser")
        parsed_chapters = _split_document_into_chapters(soup, chapter_start=len(chapters) + 1)
        chapters.extend(parsed_chapters)

    if not chapters:
        raise ValueError("Nenhum conteudo textual encontrado no EPUB")

    return ParsedBook(title=title, author=author, chapters=chapters)
