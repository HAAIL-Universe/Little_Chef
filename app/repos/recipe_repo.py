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

    def __init__(self, data_dir: str | None = None) -> None:
        self._books: List[RecipeBook] = []
        self._text_by_book: dict[str, str] = {}
        self._data_dir = data_dir or DATA_DIR

    def _ensure_dir(self) -> None:
        os.makedirs(self._data_dir, exist_ok=True)

    def create_book(self, title: str, filename: str, content_type: str, data: bytes) -> RecipeBook:
        self._ensure_dir()
        book_id = str(uuid4())
        safe_name = filename.replace("/", "_").replace("\\", "_")
        path = os.path.join(self._data_dir, f"{book_id}_{safe_name}")
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
        result = []
        for b in self._books:
            clone = b.model_copy()
            clone.text_content = self._text_by_book.get(b.book_id)
            clone.pack_id = getattr(b, "_pack_id", None)
            result.append(clone)
        return result

    def get_book(self, book_id: str) -> Optional[RecipeBook]:
        b = next((b for b in self._books if b.book_id == book_id), None)
        if b:
            clone = b.model_copy()
            clone.text_content = self._text_by_book.get(b.book_id)
            clone.pack_id = getattr(b, "_pack_id", None)
            return clone
        return None

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

    def has_pack(self, pack_id: str) -> bool:
        return any(
            getattr(b, "_pack_id", None) == pack_id for b in self._books
        )

    def installed_pack_ids(self) -> List[str]:
        seen: set[str] = set()
        result: List[str] = []
        for b in self._books:
            pid = getattr(b, "_pack_id", None)
            if pid and pid not in seen:
                seen.add(pid)
                result.append(pid)
        return result

    def uninstall_pack(self, pack_id: str, selected_titles: list[str] | None = None) -> int:
        """Remove all (or selected) books belonging to a pack. Returns count removed."""
        before = len(self._books)
        kept: list[RecipeBook] = []
        for b in self._books:
            if getattr(b, "_pack_id", None) == pack_id:
                if selected_titles is None or b.title in selected_titles:
                    self._text_by_book.pop(b.book_id, None)
                    continue
            kept.append(b)
        self._books = kept
        return before - len(self._books)

    def create_pack_book(self, title: str, filename: str, text_content: str, pack_id: str) -> RecipeBook:
        """Create a book from a built-in pack (in-memory, no disk write)."""
        book_id = str(uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        book = RecipeBook(
            book_id=book_id,
            title=title,
            filename=filename,
            content_type="text/markdown",
            status=RecipeBookStatus.ready,
            error_message=None,
            created_at=created_at,
            text_content=text_content,
        )
        book._pack_id = pack_id  # type: ignore[attr-defined]
        self._books.append(book)
        self._text_by_book[book_id] = text_content
        clone = book.model_copy()
        clone.pack_id = pack_id
        return clone


class DbRecipeRepo:
    """DB-backed recipe book repository (matches inventory/prefs dual-repo pattern)."""

    def create_book(self, user_id: str, title: str, filename: str, content_type: str, data: bytes) -> RecipeBook:
        from app.db.conn import connect

        book_id = str(uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        status = "ready" if content_type in ("text/markdown", "text/plain") else "processing"
        text_content: Optional[str] = None
        if status == "ready":
            try:
                text_content = data.decode("utf-8", errors="ignore")
            except Exception:
                pass
        with connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO recipe_books (book_id, user_id, title, filename, content_type, status, text_content, source, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'upload', %s)
                """,
                (book_id, user_id, title or "", filename, content_type, status, text_content, created_at),
            )
            conn.commit()
        return RecipeBook(
            book_id=book_id, title=title or "", filename=filename,
            content_type=content_type, status=RecipeBookStatus(status),
            error_message=None, created_at=created_at,
        )

    def list_books(self, user_id: str) -> List[RecipeBook]:
        from app.db.conn import connect

        with connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT book_id, title, filename, content_type, status, error_message, created_at, text_content, pack_id FROM recipe_books WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,),
            )
            rows = cur.fetchall()
        return [
            RecipeBook(
                book_id=str(r[0]), title=r[1], filename=r[2], content_type=r[3],
                status=RecipeBookStatus(r[4]), error_message=r[5],
                created_at=r[6] if isinstance(r[6], str) else r[6].isoformat(),
                text_content=r[7],
                pack_id=r[8],
            )
            for r in rows
        ]

    def get_book(self, user_id: str, book_id: str) -> Optional[RecipeBook]:
        from app.db.conn import connect

        with connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT book_id, title, filename, content_type, status, error_message, created_at, text_content, pack_id FROM recipe_books WHERE user_id = %s AND book_id = %s",
                (user_id, book_id),
            )
            r = cur.fetchone()
        if not r:
            return None
        return RecipeBook(
            book_id=str(r[0]), title=r[1], filename=r[2], content_type=r[3],
            status=RecipeBookStatus(r[4]), error_message=r[5],
            created_at=r[6] if isinstance(r[6], str) else r[6].isoformat(),
            text_content=r[7],
            pack_id=r[8],
        )

    def delete_book(self, user_id: str, book_id: str) -> bool:
        from app.db.conn import connect

        with connect() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM recipe_books WHERE user_id = %s AND book_id = %s", (user_id, book_id))
            deleted = cur.rowcount > 0
            conn.commit()
        return deleted

    def clear(self) -> None:
        pass  # no-op for DB repo; use migrations

    def search_text(self, user_id: str, query: str, max_results: int) -> List[tuple[RecipeBook, str]]:
        from app.db.conn import connect

        with connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT book_id, title, filename, content_type, status, error_message, created_at, text_content
                FROM recipe_books
                WHERE user_id = %s AND text_content ILIKE %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (user_id, f"%{query}%", max_results),
            )
            rows = cur.fetchall()
        hits: List[tuple[RecipeBook, str]] = []
        q = query.lower()
        for r in rows:
            book = RecipeBook(
                book_id=str(r[0]), title=r[1], filename=r[2], content_type=r[3],
                status=RecipeBookStatus(r[4]), error_message=r[5],
                created_at=r[6] if isinstance(r[6], str) else r[6].isoformat(),
            )
            text = r[7] or ""
            idx = text.lower().find(q)
            start = max(idx - 20, 0) if idx >= 0 else 0
            end = min(idx + 80, len(text)) if idx >= 0 else 80
            excerpt = text[start:end].strip()
            hits.append((book, excerpt))
        return hits

    def has_pack(self, user_id: str, pack_id: str) -> bool:
        from app.db.conn import connect

        with connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM recipe_books WHERE user_id = %s AND pack_id = %s LIMIT 1",
                (user_id, pack_id),
            )
            return cur.fetchone() is not None

    def installed_pack_ids(self, user_id: str) -> List[str]:
        from app.db.conn import connect

        with connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT pack_id FROM recipe_books WHERE user_id = %s AND pack_id IS NOT NULL",
                (user_id,),
            )
            return [row[0] for row in cur.fetchall()]

    def uninstall_pack(self, user_id: str, pack_id: str, selected_titles: list[str] | None = None) -> int:
        """Remove all (or selected) books belonging to a pack. Returns count removed."""
        from app.db.conn import connect

        with connect() as conn, conn.cursor() as cur:
            if selected_titles is not None:
                if len(selected_titles) == 0:
                    return 0
                placeholders = ",".join(["%s"] * len(selected_titles))
                cur.execute(
                    f"DELETE FROM recipe_books WHERE user_id = %s AND pack_id = %s AND title IN ({placeholders})",
                    (user_id, pack_id, *selected_titles),
                )
            else:
                cur.execute(
                    "DELETE FROM recipe_books WHERE user_id = %s AND pack_id = %s",
                    (user_id, pack_id),
                )
            removed = cur.rowcount
            conn.commit()
        return removed

    def create_pack_book(self, user_id: str, title: str, filename: str, text_content: str, pack_id: str) -> RecipeBook:
        from app.db.conn import connect

        book_id = str(uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        with connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO recipe_books (book_id, user_id, title, filename, content_type, status, text_content, source, pack_id, created_at)
                VALUES (%s, %s, %s, %s, 'text/markdown', 'ready', %s, 'built_in_pack', %s, %s)
                """,
                (book_id, user_id, title, filename, text_content, pack_id, created_at),
            )
            conn.commit()
        return RecipeBook(
            book_id=book_id, title=title, filename=filename,
            content_type="text/markdown", status=RecipeBookStatus.ready,
            error_message=None, created_at=created_at,
            text_content=text_content,
            pack_id=pack_id,
        )


def get_recipe_repository():
    from app.db.conn import get_database_url

    if get_database_url():
        return DbRecipeRepo()
    return RecipeRepo()
