from dataclasses import dataclass
from pathlib import Path

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
    chapter_count = 0

    for item in book.get_items_of_type(ITEM_DOCUMENT):
        raw_html = item.get_content()
        soup = BeautifulSoup(raw_html, "html.parser")
        text = soup.get_text(" ", strip=True)
        if not text:
            continue

        chapter_count += 1
        heading = soup.find(["h1", "h2", "h3"])
        chapter_title = heading.get_text(strip=True) if heading else f"Capitulo {chapter_count}"
        chapters.append(ParsedChapter(title=chapter_title, text=text))

    if not chapters:
        raise ValueError("Nenhum conteudo textual encontrado no EPUB")

    return ParsedBook(title=title, author=author, chapters=chapters)
