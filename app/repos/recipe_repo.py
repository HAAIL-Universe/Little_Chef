import os
from typing import List, Optional
from uuid import uuid4
from datetime import datetime, timezone

from app.schemas import RecipeBook, RecipeBookStatus


DATA_DIR = os.path.join(os.getcwd(), "data", "recipe_books")


class RecipeRepo:
    """
    In-memory recipe book registry with minimal file storage.
    PDF content is stored but not parsed; md/txt content stored for search excerpts.
    """

    def __init__(self) -> None:
        self._books: List[RecipeBook] = []
        self._text_by_book: dict[str, str] = {}

    def _ensure_dir(self) -> None:
        os.makedirs(DATA_DIR, exist_ok=True)

    def create_book(self, title: str, filename: str, content_type: str, data: bytes) -> RecipeBook:
        self._ensure_dir()
        book_id = str(uuid4())
        safe_name = filename.replace("/", "_").replace("\\", "_")
        path = os.path.join(DATA_DIR, f"{book_id}_{safe_name}")
        with open(path, "wb") as f:
            f.write(data)

        status = RecipeBookStatus.ready if content_type in ("text/markdown", "text/plain") else RecipeBookStatus.processing
        created_at = datetime.now(timezone.utc).isoformat()
        book = RecipeBook(
            book_id=book_id,
            title=title or "",
            filename=filename,
            content_type=content_type,
            status=status,
            error_message=None,
            created_at=created_at,
        )
        self._books.append(book)

        if status == RecipeBookStatus.ready:
            try:
                text = data.decode("utf-8", errors="ignore")
                self._text_by_book[book_id] = text
            except Exception:
                pass

        return book

    def list_books(self) -> List[RecipeBook]:
        return list(self._books)

    def get_book(self, book_id: str) -> Optional[RecipeBook]:
        return next((b for b in self._books if b.book_id == book_id), None)

    def delete_book(self, book_id: str) -> bool:
        before = len(self._books)
        self._books = [b for b in self._books if b.book_id != book_id]
        self._text_by_book.pop(book_id, None)
        return len(self._books) != before

    def clear(self) -> None:
        self._books = []
        self._text_by_book = {}

    def search_text(self, query: str, max_results: int) -> List[tuple[RecipeBook, str]]:
        hits: List[tuple[RecipeBook, str]] = []
        q = query.lower()
        for book in self._books:
            text = self._text_by_book.get(book.book_id, "")
            if not text:
                continue
            if q in text.lower():
                # grab short excerpt
                idx = text.lower().find(q)
                start = max(idx - 20, 0)
                end = min(idx + 80, len(text))
                excerpt = text[start:end].strip()
                hits.append((book, excerpt))
                if len(hits) >= max_results:
                    break
        return hits
