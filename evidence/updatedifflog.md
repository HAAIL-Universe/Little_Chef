# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-10T09:00:25+00:00
- Branch: main
- HEAD: fa4b1c2d29e2728986e9bf341167dbd22730b082
- BASE_HEAD: 1476beaa84629f6647b323900b11839db296197f
- Diff basis: staged

## Cycle Status
- Status: COMPLETE

## Summary
- fix: use recipe_data.title for correct recipe titles (Bug 1)
- feat: expandable recipe cards in My Recipes tab with text_content (Feature 2)
- schema: add text_content Optional[str] to RecipeBook pydantic model
- repos: return text_content from list_books/get_book/create_pack_book in both in-memory and DB repos
- tests: update test_builtin_packs.py mock data to match real HF dataset structure
- frontend: replace loadMyRecipes() with expandable card UI + renderRecipeContent() helper + CSS

## Files Changed (staged)
- app/repos/recipe_repo.py
- app/schemas.py
- app/services/builtin_packs_service.py
- tests/test_builtin_packs.py
- web/dist/main.js
- web/dist/style.css
- web/src/main.ts
- web/src/style.css

## git status -sb
    ## main...origin/main [ahead 1]
     M .claude/settings.local.json
     M Contracts/physics.yaml
     M app/api/routers/recipes.py
    M  app/repos/recipe_repo.py
    M  app/schemas.py
    A  app/services/builtin_packs_service.py
     M app/services/recipe_service.py
     M evidence/test_runs.md
     M evidence/test_runs_latest.md
     M evidence/updatedifflog.md
     M requirements.txt
     M tests/conftest.py
    A  tests/test_builtin_packs.py
    M  web/dist/main.js
    M  web/dist/style.css
    M  web/src/main.ts
    M  web/src/style.css
    ?? db/migrations/0005_recipe_books.sql
    ?? evidence/instructions.md
    ?? nul
    ?? scripts/seed_wikibooks_cookbook.py
    ?? tests/test_recipe_books_isolation.py

## Minimal Diff Hunks
    diff --git a/app/repos/recipe_repo.py b/app/repos/recipe_repo.py
    index 36f401e..f644179 100644
    --- a/app/repos/recipe_repo.py
    +++ b/app/repos/recipe_repo.py
    @@ -15,18 +15,19 @@ class RecipeRepo:
         PDF content is stored but not parsed; md/txt content stored for search excerpts.
         """
     
    -    def __init__(self) -> None:
    +    def __init__(self, data_dir: str | None = None) -> None:
             self._books: List[RecipeBook] = []
             self._text_by_book: dict[str, str] = {}
    +        self._data_dir = data_dir or DATA_DIR
     
         def _ensure_dir(self) -> None:
    -        os.makedirs(DATA_DIR, exist_ok=True)
    +        os.makedirs(self._data_dir, exist_ok=True)
     
         def create_book(self, title: str, filename: str, content_type: str, data: bytes) -> RecipeBook:
             self._ensure_dir()
             book_id = str(uuid4())
             safe_name = filename.replace("/", "_").replace("\\", "_")
    -        path = os.path.join(DATA_DIR, f"{book_id}_{safe_name}")
    +        path = os.path.join(self._data_dir, f"{book_id}_{safe_name}")
             with open(path, "wb") as f:
                 f.write(data)
     
    @@ -53,10 +54,20 @@ class RecipeRepo:
             return book
     
         def list_books(self) -> List[RecipeBook]:
    -        return list(self._books)
    +        result = []
    +        for b in self._books:
    +            clone = b.model_copy()
    +            clone.text_content = self._text_by_book.get(b.book_id)
    +            result.append(clone)
    +        return result
     
         def get_book(self, book_id: str) -> Optional[RecipeBook]:
    -        return next((b for b in self._books if b.book_id == book_id), None)
    +        b = next((b for b in self._books if b.book_id == book_id), None)
    +        if b:
    +            clone = b.model_copy()
    +            clone.text_content = self._text_by_book.get(b.book_id)
    +            return clone
    +        return None
     
         def delete_book(self, book_id: str) -> bool:
             before = len(self._books)
    @@ -85,3 +96,197 @@ class RecipeRepo:
                     if len(hits) >= max_results:
                         break
             return hits
    +
    +    def has_pack(self, pack_id: str) -> bool:
    +        return any(
    +            getattr(b, "_pack_id", None) == pack_id for b in self._books
    +        )
    +
    +    def installed_pack_ids(self) -> List[str]:
    +        seen: set[str] = set()
    +        result: List[str] = []
    +        for b in self._books:
    +            pid = getattr(b, "_pack_id", None)
    +            if pid and pid not in seen:
    +                seen.add(pid)
    +                result.append(pid)
    +        return result
    +
    +    def create_pack_book(self, title: str, filename: str, text_content: str, pack_id: str) -> RecipeBook:
    +        """Create a book from a built-in pack (in-memory, no disk write)."""
    +        book_id = str(uuid4())
    +        created_at = datetime.now(timezone.utc).isoformat()
    +        book = RecipeBook(
    +            book_id=book_id,
    +            title=title,
    +            filename=filename,
    +            content_type="text/markdown",
    +            status=RecipeBookStatus.ready,
    +            error_message=None,
    +            created_at=created_at,
    +            text_content=text_content,
    +        )
    +        book._pack_id = pack_id  # type: ignore[attr-defined]
    +        self._books.append(book)
    +        self._text_by_book[book_id] = text_content
    +        return book
    +
    +
    +class DbRecipeRepo:
    +    """DB-backed recipe book repository (matches inventory/prefs dual-repo pattern)."""
    +
    +    def create_book(self, user_id: str, title: str, filename: str, content_type: str, data: bytes) -> RecipeBook:
    +        from app.db.conn import connect
    +
    +        book_id = str(uuid4())
    +        created_at = datetime.now(timezone.utc).isoformat()
    +        status = "ready" if content_type in ("text/markdown", "text/plain") else "processing"
    +        text_content: Optional[str] = None
    +        if status == "ready":
    +            try:
    +                text_content = data.decode("utf-8", errors="ignore")
    +            except Exception:
    +                pass
    +        with connect() as conn, conn.cursor() as cur:
    +            cur.execute(
    +                """
    +                INSERT INTO recipe_books (book_id, user_id, title, filename, content_type, status, text_content, source, created_at)
    +                VALUES (%s, %s, %s, %s, %s, %s, %s, 'upload', %s)
    +                """,
    +                (book_id, user_id, title or "", filename, content_type, status, text_content, created_at),
    +            )
    +            conn.commit()
    +        return RecipeBook(
    +            book_id=book_id, title=title or "", filename=filename,
    +            content_type=content_type, status=RecipeBookStatus(status),
    +            error_message=None, created_at=created_at,
    +        )
    +
    +    def list_books(self, user_id: str) -> List[RecipeBook]:
    +        from app.db.conn import connect
    +
    +        with connect() as conn, conn.cursor() as cur:
    +            cur.execute(
    +                "SELECT book_id, title, filename, content_type, status, error_message, created_at, text_content FROM recipe_books WHERE user_id = %s ORDER BY created_at DESC",
    +                (user_id,),
    +            )
    +            rows = cur.fetchall()
    +        return [
    +            RecipeBook(
    +                book_id=str(r[0]), title=r[1], filename=r[2], content_type=r[3],
    +                status=RecipeBookStatus(r[4]), error_message=r[5],
    +                created_at=r[6] if isinstance(r[6], str) else r[6].isoformat(),
    +                text_content=r[7],
    +            )
    +            for r in rows
    +        ]
    +
    +    def get_book(self, user_id: str, book_id: str) -> Optional[RecipeBook]:
    +        from app.db.conn import connect
    +
    +        with connect() as conn, conn.cursor() as cur:
    +            cur.execute(
    +                "SELECT book_id, title, filename, content_type, status, error_message, created_at, text_content FROM recipe_books WHERE user_id = %s AND book_id = %s",
    +                (user_id, book_id),
    +            )
    +            r = cur.fetchone()
    +        if not r:
    +            return None
    +        return RecipeBook(
    +            book_id=str(r[0]), title=r[1], filename=r[2], content_type=r[3],
    +            status=RecipeBookStatus(r[4]), error_message=r[5],
    +            created_at=r[6] if isinstance(r[6], str) else r[6].isoformat(),
    +            text_content=r[7],
    +        )
    +
    +    def delete_book(self, user_id: str, book_id: str) -> bool:
    +        from app.db.conn import connect
    +
    +        with connect() as conn, conn.cursor() as cur:
    +            cur.execute("DELETE FROM recipe_books WHERE user_id = %s AND book_id = %s", (user_id, book_id))
    +            deleted = cur.rowcount > 0
    +            conn.commit()
    +        return deleted
    +
    +    def clear(self) -> None:
    +        pass  # no-op for DB repo; use migrations
    +
    +    def search_text(self, user_id: str, query: str, max_results: int) -> List[tuple[RecipeBook, str]]:
    +        from app.db.conn import connect
    +
    +        with connect() as conn, conn.cursor() as cur:
    +            cur.execute(
    +                """
    +                SELECT book_id, title, filename, content_type, status, error_message, created_at, text_content
    +                FROM recipe_books
    +                WHERE user_id = %s AND text_content ILIKE %s
    +                ORDER BY created_at DESC
    +                LIMIT %s
    +                """,
    +                (user_id, f"%{query}%", max_results),
    +            )
    +            rows = cur.fetchall()
    +        hits: List[tuple[RecipeBook, str]] = []
    +        q = query.lower()
    +        for r in rows:
    +            book = RecipeBook(
    +                book_id=str(r[0]), title=r[1], filename=r[2], content_type=r[3],
    +                status=RecipeBookStatus(r[4]), error_message=r[5],
    +                created_at=r[6] if isinstance(r[6], str) else r[6].isoformat(),
    +            )
    +            text = r[7] or ""
    +            idx = text.lower().find(q)
    +            start = max(idx - 20, 0) if idx >= 0 else 0
    +            end = min(idx + 80, len(text)) if idx >= 0 else 80
    +            excerpt = text[start:end].strip()
    +            hits.append((book, excerpt))
    +        return hits
    +
    +    def has_pack(self, user_id: str, pack_id: str) -> bool:
    +        from app.db.conn import connect
    +
    +        with connect() as conn, conn.cursor() as cur:
    +            cur.execute(
    +                "SELECT 1 FROM recipe_books WHERE user_id = %s AND pack_id = %s LIMIT 1",
    +                (user_id, pack_id),
    +            )
    +            return cur.fetchone() is not None
    +
    +    def installed_pack_ids(self, user_id: str) -> List[str]:
    +        from app.db.conn import connect
    +
    +        with connect() as conn, conn.cursor() as cur:
    +            cur.execute(
    +                "SELECT DISTINCT pack_id FROM recipe_books WHERE user_id = %s AND pack_id IS NOT NULL",
    +                (user_id,),
    +            )
    +            return [row[0] for row in cur.fetchall()]
    +
    +    def create_pack_book(self, user_id: str, title: str, filename: str, text_content: str, pack_id: str) -> RecipeBook:
    +        from app.db.conn import connect
    +
    +        book_id = str(uuid4())
    +        created_at = datetime.now(timezone.utc).isoformat()
    +        with connect() as conn, conn.cursor() as cur:
    +            cur.execute(
    +                """
    +                INSERT INTO recipe_books (book_id, user_id, title, filename, content_type, status, text_content, source, pack_id, created_at)
    +                VALUES (%s, %s, %s, %s, 'text/markdown', 'ready', %s, 'built_in_pack', %s, %s)
    +                """,
    +                (book_id, user_id, title, filename, text_content, pack_id, created_at),
    +            )
    +            conn.commit()
    +        return RecipeBook(
    +            book_id=book_id, title=title, filename=filename,
    +            content_type="text/markdown", status=RecipeBookStatus.ready,
    +            error_message=None, created_at=created_at,
    +            text_content=text_content,
    +        )
    +
    +
    +def get_recipe_repository():
    +    from app.db.conn import get_database_url
    +
    +    if get_database_url():
    +        return DbRecipeRepo()
    +    return RecipeRepo()
    diff --git a/app/schemas.py b/app/schemas.py
    index 2b92664..5a84390 100644
    --- a/app/schemas.py
    +++ b/app/schemas.py
    @@ -130,12 +130,35 @@ class RecipeBook(BaseModel):
         status: RecipeBookStatus
         error_message: Optional[str] = None
         created_at: str
    +    text_content: Optional[str] = None
     
     
     class RecipeBookListResponse(BaseModel):
         books: List[RecipeBook]
     
     
    +class BuiltInPack(BaseModel):
    +    pack_id: str
    +    label: str
    +    description: str
    +    recipe_count: int
    +
    +
    +class BuiltInPackListResponse(BaseModel):
    +    packs: List[BuiltInPack]
    +    installed_pack_ids: List[str] = Field(default_factory=list)
    +
    +
    +class InstallPackRequest(BaseModel):
    +    pack_id: str
    +    max_recipes: int = Field(default=50, ge=1, le=200)
    +
    +
    +class InstallPackResponse(BaseModel):
    +    installed: int
    +    books: List[RecipeBook]
    +
    +
     class RecipeSearchRequest(BaseModel):
         query: str = Field(..., min_length=2)
         max_results: int = Field(default=5, ge=1, le=10)
    diff --git a/app/services/builtin_packs_service.py b/app/services/builtin_packs_service.py
    new file mode 100644
    index 0000000..f357be3
    --- /dev/null
    +++ b/app/services/builtin_packs_service.py
    @@ -0,0 +1,134 @@
    +"""Built-in recipe packs service ÔÇö static catalogue + on-demand HF install."""
    +
    +from __future__ import annotations
    +
    +import re
    +from typing import List
    +
    +from app.schemas import BuiltInPack, BuiltInPackListResponse, InstallPackResponse, RecipeBook
    +from app.errors import BadRequestError
    +
    +try:
    +    from datasets import load_dataset  # type: ignore[import-untyped]
    +except ImportError:  # pragma: no cover
    +    load_dataset = None  # type: ignore[assignment]
    +
    +
    +# ÔöÇÔöÇ Static catalogue (curated from gossminn/wikibooks-cookbook categories) ÔöÇÔöÇÔöÇÔöÇÔöÇ
    +# pack_id must be stable; label/description are user-facing.
    +PACK_CATALOGUE: List[BuiltInPack] = [
    +    BuiltInPack(pack_id="soup", label="Soups", description="Hearty soups and broths from around the world", recipe_count=120),
    +    BuiltInPack(pack_id="cake", label="Cakes", description="Baking classics ÔÇö sponges, cheesecakes, and more", recipe_count=90),
    +    BuiltInPack(pack_id="salad", label="Salads", description="Fresh salads and dressings", recipe_count=60),
    +    BuiltInPack(pack_id="bread", label="Breads", description="Loaves, rolls, flatbreads and doughs", recipe_count=50),
    +    BuiltInPack(pack_id="pasta", label="Pasta", description="Italian-inspired pasta dishes", recipe_count=40),
    +    BuiltInPack(pack_id="chicken", label="Chicken", description="Chicken mains and sides", recipe_count=50),
    +    BuiltInPack(pack_id="beef", label="Beef", description="Beef roasts, stews, and grills", recipe_count=40),
    +    BuiltInPack(pack_id="fish", label="Fish & Seafood", description="Fish, shellfish and seafood dishes", recipe_count=60),
    +    BuiltInPack(pack_id="vegetarian", label="Vegetarian", description="Meat-free mains and sides", recipe_count=80),
    +    BuiltInPack(pack_id="dessert", label="Desserts", description="Puddings, pies, and sweet treats", recipe_count=100),
    +    BuiltInPack(pack_id="indian", label="Indian", description="Curries, dals, and Indian classics", recipe_count=50),
    +    BuiltInPack(pack_id="mexican", label="Mexican", description="Tacos, burritos, salsas and more", recipe_count=30),
    +    BuiltInPack(pack_id="chinese", label="Chinese", description="Stir-fries, dumplings, and Chinese favourites", recipe_count=40),
    +    BuiltInPack(pack_id="sandwich", label="Sandwiches", description="Quick sandwiches and wraps", recipe_count=30),
    +    BuiltInPack(pack_id="breakfast", label="Breakfast", description="Morning meals and brunch ideas", recipe_count=40),
    +]
    +
    +_PACK_BY_ID = {p.pack_id: p for p in PACK_CATALOGUE}
    +
    +# Map pack_id ÔåÆ regex fragments that match HF category paths
    +_CATEGORY_PATTERNS = {
    +    "soup": r"soup",
    +    "cake": r"cake",
    +    "salad": r"salad",
    +    "bread": r"bread",
    +    "pasta": r"pasta",
    +    "chicken": r"chicken",
    +    "beef": r"beef",
    +    "fish": r"fish|seafood|shellfish",
    +    "vegetarian": r"vegetarian|vegan",
    +    "dessert": r"dessert|pudding|sweet",
    +    "indian": r"indian",
    +    "mexican": r"mexican",
    +    "chinese": r"chinese",
    +    "sandwich": r"sandwich|wrap",
    +    "breakfast": r"breakfast|brunch",
    +}
    +
    +
    +def _slugify(text: str, max_len: int = 80) -> str:
    +    s = text.lower().strip()
    +    s = re.sub(r"[^\w\s-]", "", s)
    +    s = re.sub(r"[\s_-]+", "_", s)
    +    return s[:max_len].strip("_") or "recipe"
    +
    +
    +def list_packs(installed_ids: list[str] | None = None) -> BuiltInPackListResponse:
    +    return BuiltInPackListResponse(packs=PACK_CATALOGUE, installed_pack_ids=installed_ids or [])
    +
    +
    +def install_pack(pack_id: str, max_recipes: int, repo, user_id: str | None = None) -> InstallPackResponse:
    +    """Download recipes from HF matching pack_id's category and load into repo.
    +
    +    For in-memory RecipeRepo: user_id is ignored (no per-user isolation).
    +    For DbRecipeRepo: user_id is required.
    +    """
    +    if pack_id not in _PACK_BY_ID:
    +        raise BadRequestError(f"Unknown pack_id: {pack_id}")
    +
    +    # Idempotency: check if pack already installed
    +    from app.repos.recipe_repo import DbRecipeRepo
    +    is_db = isinstance(repo, DbRecipeRepo)
    +    if is_db:
    +        if repo.has_pack(user_id, pack_id):
    +            return InstallPackResponse(installed=0, books=[])
    +    else:
    +        if repo.has_pack(pack_id):
    +            return InstallPackResponse(installed=0, books=[])
    +
    +    if load_dataset is None:
    +        raise BadRequestError("Server missing 'datasets' package ÔÇö cannot install packs")
    +
    +    pattern = re.compile(_CATEGORY_PATTERNS[pack_id], re.IGNORECASE)
    +    ds = load_dataset("gossminn/wikibooks-cookbook", split="main")
    +
    +    books: List[RecipeBook] = []
    +    seen_slugs: set[str] = set()
    +
    +    for row in ds:
    +        if len(books) >= max_recipes:
    +            break
    +
    +        # Filter by category
    +        category = ""
    +        infobox = row.get("recipe_data", {}) if isinstance(row.get("recipe_data"), dict) else {}
    +        if isinstance(infobox, dict):
    +            ib = infobox.get("infobox", {}) if isinstance(infobox.get("infobox"), dict) else {}
    +            category = ib.get("category", "") or ""
    +        if not category:
    +            category = row.get("category", "") or ""
    +        if not pattern.search(category):
    +            continue
    +
    +        # text_lines is a list of {line_type, section, text} dicts
    +        tl_objs = infobox.get("text_lines", []) if isinstance(infobox, dict) else []
    +        text_parts = [tl.get("text", "") for tl in tl_objs if isinstance(tl, dict) and tl.get("text")]
    +        text_lines = "\n".join(text_parts)
    +        if not text_lines.strip():
    +            continue
    +        title = infobox.get("title", "") or (text_parts[0].strip() if text_parts else row.get("filename", "recipe"))
    +
    +        slug = _slugify(title)
    +        if slug in seen_slugs:
    +            slug = f"{slug}_{len(books)}"
    +        seen_slugs.add(slug)
    +        filename = f"{slug}.md"
    +        content = f"# {title}\n\n{text_lines}\n"
    +
    +        if is_db:
    +            book = repo.create_pack_book(user_id, title, filename, content, pack_id)
    +        else:
    +            book = repo.create_pack_book(title, filename, content, pack_id)
    +        books.append(book)
    +
    +    return InstallPackResponse(installed=len(books), books=books)
    diff --git a/tests/test_builtin_packs.py b/tests/test_builtin_packs.py
    new file mode 100644
    index 0000000..7184501
    --- /dev/null
    +++ b/tests/test_builtin_packs.py
    @@ -0,0 +1,165 @@
    +"""Tests for /recipes/built-in-packs and /recipes/built-in-packs/install endpoints."""
    +
    +import pytest
    +from unittest.mock import patch, MagicMock
    +
    +# The service imports load_dataset at module level (with try/except fallback).
    +LOAD_DS_PATCH = "app.services.builtin_packs_service.load_dataset"
    +
    +
    +# ÔöÇÔöÇ catalogue listing ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
    +
    +def test_list_packs_returns_catalogue(authed_client):
    +    resp = authed_client.get("/recipes/built-in-packs")
    +    assert resp.status_code == 200
    +    data = resp.json()
    +    assert "packs" in data
    +    assert len(data["packs"]) > 0
    +    pack = data["packs"][0]
    +    assert "pack_id" in pack
    +    assert "label" in pack
    +    assert "description" in pack
    +    assert "recipe_count" in pack
    +
    +
    +def test_list_packs_requires_auth(client):
    +    resp = client.get("/recipes/built-in-packs")
    +    assert resp.status_code == 401
    +
    +
    +# ÔöÇÔöÇ install ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
    +
    +def test_install_pack_unknown_id_400(authed_client):
    +    resp = authed_client.post(
    +        "/recipes/built-in-packs/install",
    +        json={"pack_id": "nonexistent_pack_xyz"},
    +    )
    +    assert resp.status_code == 400
    +
    +
    +def _make_fake_dataset(rows):
    +    """Create a mock that behaves like a HF Dataset."""
    +    ds = MagicMock()
    +    ds.__len__ = lambda self: len(rows)
    +    ds.__iter__ = lambda self: iter(rows)
    +    ds.__getitem__ = lambda self, idx: rows[idx]
    +    return ds
    +
    +
    +def test_install_pack_writes_books(authed_client):
    +    fake_rows = [
    +        {
    +            "recipe_data": {
    +                "title": "Test Soup",
    +                "infobox": {"category": "/wiki/Category:Soup_recipes"},
    +                "text_lines": [
    +                    {"line_type": "p", "section": None, "text": "Boil water. Add vegetables."},
    +                ],
    +            },
    +            "filename": "recipes/test_soup.html",
    +        },
    +        {
    +            "recipe_data": {
    +                "title": "Another Soup",
    +                "infobox": {"category": "/wiki/Category:Soup_recipes"},
    +                "text_lines": [
    +                    {"line_type": "p", "section": None, "text": "Blend everything."},
    +                ],
    +            },
    +            "filename": "recipes/another_soup.html",
    +        },
    +    ]
    +    fake_ds = _make_fake_dataset(fake_rows)
    +
    +    with patch(LOAD_DS_PATCH, return_value=fake_ds):
    +        resp = authed_client.post(
    +            "/recipes/built-in-packs/install",
    +            json={"pack_id": "soup", "max_recipes": 10},
    +        )
    +    assert resp.status_code == 200
    +    data = resp.json()
    +    assert data["installed"] == 2
    +    assert len(data["books"]) == 2
    +    assert data["books"][0]["title"] == "Test Soup"
    +
    +    # Verify books are in the listing
    +    books_resp = authed_client.get("/recipes/books")
    +    assert books_resp.status_code == 200
    +    assert len(books_resp.json()["books"]) == 2
    +
    +
    +def test_install_pack_idempotent(authed_client):
    +    fake_rows = [
    +        {
    +            "recipe_data": {
    +                "title": "Cake One",
    +                "infobox": {"category": "/wiki/Category:Cake_recipes"},
    +                "text_lines": [
    +                    {"line_type": "p", "section": None, "text": "Mix flour and sugar."},
    +                ],
    +            },
    +            "filename": "recipes/cake_one.html",
    +        },
    +    ]
    +    fake_ds = _make_fake_dataset(fake_rows)
    +
    +    with patch(LOAD_DS_PATCH, return_value=fake_ds):
    +        resp1 = authed_client.post(
    +            "/recipes/built-in-packs/install",
    +            json={"pack_id": "cake"},
    +        )
    +        resp2 = authed_client.post(
    +            "/recipes/built-in-packs/install",
    +            json={"pack_id": "cake"},
    +        )
    +
    +    assert resp1.status_code == 200
    +    assert resp1.json()["installed"] == 1
    +    # Second install should be idempotent ÔÇö 0 new
    +    assert resp2.status_code == 200
    +    assert resp2.json()["installed"] == 0
    +
    +
    +def test_install_pack_requires_auth(client):
    +    resp = client.post(
    +        "/recipes/built-in-packs/install",
    +        json={"pack_id": "soup"},
    +    )
    +    assert resp.status_code == 401
    +
    +
    +def test_install_pack_filters_by_category(authed_client):
    +    """Install 'pasta' pack ÔÇö should skip rows whose category doesn't match."""
    +    fake_rows = [
    +        {
    +            "recipe_data": {
    +                "title": "Pasta Carbonara",
    +                "infobox": {"category": "/wiki/Category:Pasta_recipes"},
    +                "text_lines": [
    +                    {"line_type": "p", "section": None, "text": "Cook pasta. Add eggs."},
    +                ],
    +            },
    +            "filename": "recipes/pasta_carbonara.html",
    +        },
    +        {
    +            "recipe_data": {
    +                "title": "Chocolate Cake",
    +                "infobox": {"category": "/wiki/Category:Cake_recipes"},
    +                "text_lines": [
    +                    {"line_type": "p", "section": None, "text": "Not pasta."},
    +                ],
    +            },
    +            "filename": "recipes/chocolate_cake.html",
    +        },
    +    ]
    +    fake_ds = _make_fake_dataset(fake_rows)
    +
    +    with patch(LOAD_DS_PATCH, return_value=fake_ds):
    +        resp = authed_client.post(
    +            "/recipes/built-in-packs/install",
    +            json={"pack_id": "pasta"},
    +        )
    +    assert resp.status_code == 200
    +    data = resp.json()
    +    assert data["installed"] == 1
    +    assert data["books"][0]["title"] == "Pasta Carbonara"
    diff --git a/web/dist/main.js b/web/dist/main.js
    index 62a1e03..e234c4e 100644
    --- a/web/dist/main.js
    +++ b/web/dist/main.js
    @@ -1,2059 +1,2231 @@
    -import { formatProposalSummary, stripProposalPrefix } from "./proposalRenderer.js";
    -const state = {
    -    token: "",
    -    lastPlan: null,
    -    proposalId: null,
    -    proposedActions: [],
    -    chatReply: null,
    -    chatError: "",
    -    onboarded: null,
    -    inventoryOnboarded: null,
    +// web/src/proposalRenderer.ts
    +var parseNoteKeyValues = (note) => {
    +  const fields = {};
    +  note.split(";").forEach((piece) => {
    +    const trimmed = piece.trim();
    +    if (!trimmed) {
    +      return;
    +    }
    +    const equalsIndex = trimmed.indexOf("=");
    +    if (equalsIndex < 0) {
    +      return;
    +    }
    +    const key = trimmed.slice(0, equalsIndex).trim().toLowerCase();
    +    const value = trimmed.slice(equalsIndex + 1).trim();
    +    if (!key || !value) {
    +      return;
    +    }
    +    fields[key] = value;
    +  });
    +  return fields;
     };
    -const DEV_JWT_STORAGE_KEY = "lc_dev_jwt";
    -const DEV_JWT_EXP_KEY = "lc_dev_jwt_exp_utc_ms";
    -const DEV_JWT_DURATION_KEY = "lc_dev_jwt_duration_ms";
    -const DEV_JWT_DEFAULT_TTL_MS = 24 * 60 * 60 * 1000;
    -const DEV_JWT_DURATION_OPTIONS = [
    -    { value: DEV_JWT_DEFAULT_TTL_MS, label: "24 hours" },
    -    { value: 7 * DEV_JWT_DEFAULT_TTL_MS, label: "7 days" },
    +var formatUseByToken = (value) => {
    +  if (!value) {
    +    return null;
    +  }
    +  const digits = value.replace(/\D/g, "");
    +  if (!digits) {
    +    return null;
    +  }
    +  const dayNum = parseInt(digits, 10);
    +  if (Number.isNaN(dayNum) || dayNum < 1 || dayNum > 31) {
    +    return null;
    +  }
    +  const now = /* @__PURE__ */ new Date();
    +  const month = now.getMonth() + 1;
    +  const dayText = String(dayNum).padStart(2, "0");
    +  const monthText = String(month).padStart(2, "0");
    +  return `USE BY: ${dayText}/${monthText}`;
    +};
    +var formatInventoryAction = (action) => {
    +  const event = action.event;
    +  if (!event) {
    +    return `\u2022 Proposal: ${action.action_type}`;
    +  }
    +  const titleName = event.item_name.replace(/\b\w/g, (c) => c.toUpperCase());
    +  const components = [titleName];
    +  if (event.quantity !== void 0 && event.quantity !== null) {
    +    const unit = (event.unit || "").trim().toLowerCase();
    +    let qtyText = "";
    +    if (!unit || unit === "count") {
    +      qtyText = `${event.quantity}`;
    +    } else if (unit === "g" && typeof event.quantity === "number" && event.quantity >= 1e3 && event.quantity % 1e3 === 0) {
    +      qtyText = `${event.quantity / 1e3} kg`;
    +    } else if (unit === "ml" && typeof event.quantity === "number" && event.quantity >= 1e3 && event.quantity % 1e3 === 0) {
    +      qtyText = `${event.quantity / 1e3} L`;
    +    } else {
    +      qtyText = `${event.quantity} ${unit}`;
    +    }
    +    components.push(qtyText);
    +  }
    +  if (event.note) {
    +    const noteFields = parseNoteKeyValues(event.note);
    +    if (noteFields["date"]) {
    +      components.push(`(${noteFields["date"]})`);
    +    } else {
    +      const useByToken = formatUseByToken(noteFields["use_by"]);
    +      if (useByToken) {
    +        components.push(useByToken);
    +      }
    +    }
    +  }
    +  return `\u2022 ${components.join(" ")}`;
    +};
    +function formatProposalSummary(response) {
    +  if (!response || !response.confirmation_required) {
    +    return null;
    +  }
    +  const actions = response.proposed_actions ?? [];
    +  const details = [];
    +  actions.forEach((action) => {
    +    if (action.action_type === "upsert_prefs") {
    +      return;
    +    }
    +    details.push(formatInventoryAction(action));
    +  });
    +  if (!details.length) {
    +    return null;
    +  }
    +  const allInventory = actions.every((action) => action.action_type === "create_inventory_event");
    +  const hasPrefs = actions.some((action) => action.action_type === "upsert_prefs");
    +  let prefix = "Proposed update";
    +  if (allInventory) {
    +    prefix = "Proposed inventory update";
    +  } else if (hasPrefs) {
    +    prefix = "Proposed preferences";
    +  }
    +  return [prefix, "", ...details].join("\n");
    +}
    +function stripProposalPrefix(text) {
    +  if (!text) {
    +    return text;
    +  }
    +  const trimmed = text.trimStart();
    +  const prefixLength = text.length - trimmed.length;
    +  if (!trimmed.toLowerCase().startsWith("proposed ")) {
    +    return trimmed;
    +  }
    +  let rest = text.slice(prefixLength);
    +  const newlineIdx = rest.indexOf("\n");
    +  if (newlineIdx >= 0) {
    +    rest = rest.slice(newlineIdx + 1);
    +  } else {
    +    const periodIdx = rest.indexOf(".");
    +    if (periodIdx >= 0) {
    +      rest = rest.slice(periodIdx + 1);
    +    } else {
    +      rest = "";
    +    }
    +  }
    +  rest = rest.replace(/^\s*(\r?\n)*/, "");
    +  return rest.trimStart();
    +}
    +
    +// web/src/main.ts
    +var state = {
    +  token: "",
    +  lastPlan: null,
    +  proposalId: null,
    +  proposedActions: [],
    +  chatReply: null,
    +  chatError: "",
    +  onboarded: null,
    +  inventoryOnboarded: null
    +};
    +var DEV_JWT_STORAGE_KEY = "lc_dev_jwt";
    +var DEV_JWT_EXP_KEY = "lc_dev_jwt_exp_utc_ms";
    +var DEV_JWT_DURATION_KEY = "lc_dev_jwt_duration_ms";
    +var DEV_JWT_DEFAULT_TTL_MS = 24 * 60 * 60 * 1e3;
    +var DEV_JWT_DURATION_OPTIONS = [
    +  { value: DEV_JWT_DEFAULT_TTL_MS, label: "24 hours" },
    +  { value: 7 * DEV_JWT_DEFAULT_TTL_MS, label: "7 days" }
     ];
     function safeLocalStorage() {
    -    if (typeof window === "undefined")
    -        return null;
    -    try {
    -        return window.localStorage;
    -    }
    -    catch {
    -        return null;
    -    }
    +  if (typeof window === "undefined") return null;
    +  try {
    +    return window.localStorage;
    +  } catch {
    +    return null;
    +  }
     }
     function getRememberCheckbox() {
    -    return document.getElementById("dev-jwt-remember");
    +  return document.getElementById("dev-jwt-remember");
     }
     function getRememberDurationSelect() {
    -    return document.getElementById("dev-jwt-remember-duration");
    +  return document.getElementById("dev-jwt-remember-duration");
     }
     function saveRememberedJwt(token, ttlMs) {
    -    const storage = safeLocalStorage();
    -    if (!storage)
    -        return;
    -    storage.setItem(DEV_JWT_STORAGE_KEY, token);
    -    storage.setItem(DEV_JWT_EXP_KEY, (Date.now() + ttlMs).toString());
    -    storage.setItem(DEV_JWT_DURATION_KEY, ttlMs.toString());
    +  const storage = safeLocalStorage();
    +  if (!storage) return;
    +  storage.setItem(DEV_JWT_STORAGE_KEY, token);
    +  storage.setItem(DEV_JWT_EXP_KEY, (Date.now() + ttlMs).toString());
    +  storage.setItem(DEV_JWT_DURATION_KEY, ttlMs.toString());
     }
     function clearRememberedJwt() {
    -    const storage = safeLocalStorage();
    -    if (!storage)
    -        return;
    -    storage.removeItem(DEV_JWT_STORAGE_KEY);
    -    storage.removeItem(DEV_JWT_EXP_KEY);
    -    storage.removeItem(DEV_JWT_DURATION_KEY);
    +  const storage = safeLocalStorage();
    +  if (!storage) return;
    +  storage.removeItem(DEV_JWT_STORAGE_KEY);
    +  storage.removeItem(DEV_JWT_EXP_KEY);
    +  storage.removeItem(DEV_JWT_DURATION_KEY);
     }
     function loadRememberedJwt() {
    -    const storage = safeLocalStorage();
    -    if (!storage)
    -        return null;
    -    const token = storage.getItem(DEV_JWT_STORAGE_KEY);
    -    if (!token)
    -        return null;
    -    const expStr = storage.getItem(DEV_JWT_EXP_KEY);
    -    const durationStr = storage.getItem(DEV_JWT_DURATION_KEY);
    -    const expMs = Number(expStr);
    -    if (!expMs || expMs < Date.now()) {
    -        clearRememberedJwt();
    -        return null;
    -    }
    -    const durationMs = Number(durationStr);
    -    return {
    -        token,
    -        durationMs: Number.isFinite(durationMs) && durationMs > 0 ? durationMs : DEV_JWT_DEFAULT_TTL_MS,
    -    };
    -}
    -const PROPOSAL_CONFIRM_COMMANDS = new Set(["confirm"]);
    -const PROPOSAL_DENY_COMMANDS = new Set(["deny", "cancel"]);
    -const flowOptions = [
    -    { key: "general", label: "General", placeholder: "Ask or fill..." },
    -    { key: "inventory", label: "Inventory", placeholder: "Ask about inventory, stock, or adjustments..." },
    -    { key: "mealplan", label: "Meal Plan", placeholder: "Plan meals or ask for ideas..." },
    -    { key: "prefs", label: "Preferences", placeholder: "Update dislikes, allergies, or servings..." },
    +  const storage = safeLocalStorage();
    +  if (!storage) return null;
    +  const token = storage.getItem(DEV_JWT_STORAGE_KEY);
    +  if (!token) return null;
    +  const expStr = storage.getItem(DEV_JWT_EXP_KEY);
    +  const durationStr = storage.getItem(DEV_JWT_DURATION_KEY);
    +  const expMs = Number(expStr);
    +  if (!expMs || expMs < Date.now()) {
    +    clearRememberedJwt();
    +    return null;
    +  }
    +  const durationMs = Number(durationStr);
    +  return {
    +    token,
    +    durationMs: Number.isFinite(durationMs) && durationMs > 0 ? durationMs : DEV_JWT_DEFAULT_TTL_MS
    +  };
    +}
    +var PROPOSAL_CONFIRM_COMMANDS = /* @__PURE__ */ new Set(["confirm"]);
    +var PROPOSAL_DENY_COMMANDS = /* @__PURE__ */ new Set(["deny", "cancel"]);
    +var flowOptions = [
    +  { key: "general", label: "General", placeholder: "Ask or fill..." },
    +  { key: "inventory", label: "Inventory", placeholder: "Ask about inventory, stock, or adjustments..." },
    +  { key: "mealplan", label: "Meal Plan", placeholder: "Plan meals or ask for ideas..." },
    +  { key: "prefs", label: "Preferences", placeholder: "Update dislikes, allergies, or servings..." }
     ];
    -const duetState = {
    -    threadId: null,
    -    history: [],
    -    drawerOpen: false,
    -    drawerProgress: 0,
    +var duetState = {
    +  threadId: null,
    +  history: [],
    +  drawerOpen: false,
    +  drawerProgress: 0
     };
    -let lastServerMode = "ASK";
    +var lastServerMode = "ASK";
     function currentModeLower() {
    -    return (lastServerMode || "ASK").toLowerCase();
    -}
    -let historyOverlay = null;
    -let historyToggle = null;
    -let historyBadgeCount = 0;
    -let historyBadgeEl = null;
    -let proposalActionsContainer = null;
    -let proposalConfirmButton = null;
    -let proposalEditButton = null;
    -let proposalDenyButton = null;
    -const proposalDismissedIds = new Set();
    -let lastResponseRequiresConfirmation = false;
    -let userBubbleEllipsisActive = false;
    -let currentFlowKey = flowOptions[0].key;
    -let composerBusy = false;
    -let flowMenuContainer = null;
    -let flowMenuDropdown = null;
    -let flowMenuButton = null;
    -let flowMenuOpen = false;
    -let flowMenuListenersBound = false;
    -let devPanelVisible = false;
    -let inventoryOverlay = null;
    -let inventoryStatusEl = null;
    -let inventoryLowList = null;
    -let inventorySummaryList = null;
    -let inventoryLoading = false;
    -let inventoryHasLoaded = false;
    -let prefsOverlay = null;
    -let prefsOverlayStatusEl = null;
    -let prefsOverlaySummaryEl = null;
    -let prefsOverlayDetails = null;
    -let prefsOverlayLoading = false;
    -let prefsOverlayHasLoaded = false;
    -let onboardMenu = null;
    -const OVERLAY_ROOT_ID = "duet-overlay-root";
    -const OVERLAY_ROOT_Z_INDEX = 2147483640;
    -const ONBOARD_MENU_EDGE_MARGIN = 8;
    -const USER_BUBBLE_SENT_TEXT = "­ƒæì";
    -const USER_BUBBLE_DEFAULT_HINT = "Long-press this chat bubble to navigate > Preferences";
    -let userSystemHint = USER_BUBBLE_DEFAULT_HINT;
    -const HISTORY_BADGE_DISPLAY_MAX = 99;
    -const NORMAL_CHAT_FLOW_KEYS = new Set(["general", "inventory", "mealplan", "prefs"]);
    -let overlayRoot = null;
    -let onboardPressTimer = null;
    -let onboardPressStart = null;
    -let onboardPointerId = null;
    -let onboardMenuActive = false;
    -let onboardActiveItem = null;
    -let onboardIgnoreDocClickUntilMs = 0;
    -let onboardDragActive = false;
    -const COMPOSER_TRIPLE_TAP_WINDOW_MS = 450;
    -let composerVisible = false;
    -let stageTripleTapCount = 0;
    -let stageTripleTapResetTimer = null;
    +  return (lastServerMode || "ASK").toLowerCase();
    +}
    +var historyOverlay = null;
    +var historyToggle = null;
    +var historyBadgeCount = 0;
    +var historyBadgeEl = null;
    +var proposalActionsContainer = null;
    +var proposalConfirmButton = null;
    +var proposalEditButton = null;
    +var proposalDenyButton = null;
    +var proposalDismissedIds = /* @__PURE__ */ new Set();
    +var lastResponseRequiresConfirmation = false;
    +var userBubbleEllipsisActive = false;
    +var currentFlowKey = flowOptions[0].key;
    +var composerBusy = false;
    +var flowMenuContainer = null;
    +var flowMenuDropdown = null;
    +var flowMenuButton = null;
    +var flowMenuOpen = false;
    +var flowMenuListenersBound = false;
    +var recipePacksButton = null;
    +var packsModalOverlay = null;
    +var devPanelVisible = false;
    +var inventoryOverlay = null;
    +var inventoryStatusEl = null;
    +var inventoryLowList = null;
    +var inventorySummaryList = null;
    +var inventoryLoading = false;
    +var inventoryHasLoaded = false;
    +var prefsOverlay = null;
    +var prefsOverlayStatusEl = null;
    +var prefsOverlaySummaryEl = null;
    +var prefsOverlayDetails = null;
    +var prefsOverlayLoading = false;
    +var prefsOverlayHasLoaded = false;
    +var onboardMenu = null;
    +var OVERLAY_ROOT_ID = "duet-overlay-root";
    +var OVERLAY_ROOT_Z_INDEX = 2147483640;
    +var ONBOARD_MENU_EDGE_MARGIN = 8;
    +var USER_BUBBLE_SENT_TEXT = "\u{1F44D}";
    +var USER_BUBBLE_DEFAULT_HINT = "Long-press this chat bubble to navigate > Preferences";
    +var userSystemHint = USER_BUBBLE_DEFAULT_HINT;
    +var HISTORY_BADGE_DISPLAY_MAX = 99;
    +var NORMAL_CHAT_FLOW_KEYS = /* @__PURE__ */ new Set(["general", "inventory", "mealplan", "prefs"]);
    +var overlayRoot = null;
    +var onboardPressTimer = null;
    +var onboardPressStart = null;
    +var onboardPointerId = null;
    +var onboardMenuActive = false;
    +var onboardActiveItem = null;
    +var onboardIgnoreDocClickUntilMs = 0;
    +var onboardDragActive = false;
    +var COMPOSER_TRIPLE_TAP_WINDOW_MS = 450;
    +var composerVisible = false;
    +var stageTripleTapCount = 0;
    +var stageTripleTapResetTimer = null;
     function headers() {
    -    var _a;
    -    const h = { "Content-Type": "application/json" };
    -    const raw = (_a = state.token) === null || _a === void 0 ? void 0 : _a.trim();
    -    if (raw) {
    -        const tokenOnly = raw.replace(/^bearer\s+/i, "").replace(/\s+/g, "");
    -        if (tokenOnly) {
    -            h["Authorization"] = `Bearer ${tokenOnly}`;
    -        }
    +  const h = { "Content-Type": "application/json" };
    +  const raw = state.token?.trim();
    +  if (raw) {
    +    const tokenOnly = raw.replace(/^bearer\s+/i, "").replace(/\s+/g, "");
    +    if (tokenOnly) {
    +      h["Authorization"] = `Bearer ${tokenOnly}`;
         }
    -    return h;
    +  }
    +  return h;
     }
     function setModeFromResponse(json) {
    -    if (json && typeof json.mode === "string") {
    -        lastServerMode = json.mode.toUpperCase();
    -        updateThreadLabel();
    -    }
    +  if (json && typeof json.mode === "string") {
    +    lastServerMode = json.mode.toUpperCase();
    +    updateThreadLabel();
    +  }
     }
     function setText(id, value) {
    -    const el = document.getElementById(id);
    -    if (el)
    -        el.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
    -}
    -function hide(id) {
    -    var _a;
    -    (_a = document.getElementById(id)) === null || _a === void 0 ? void 0 : _a.classList.add("hidden");
    -}
    -function show(id) {
    -    var _a;
    -    (_a = document.getElementById(id)) === null || _a === void 0 ? void 0 : _a.classList.remove("hidden");
    +  const el = document.getElementById(id);
    +  if (el) el.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
     }
     function moveGroupIntoDevPanel(ids, panel, moved) {
    -    const scopes = ["section", "fieldset", ".panel", ".card", ".debug", "div"];
    -    let target = null;
    -    for (const id of ids) {
    -        const el = document.getElementById(id);
    -        if (!el)
    -            continue;
    -        for (const scope of scopes) {
    -            const candidate = el.closest(scope);
    -            if (!candidate)
    -                continue;
    -            const tag = candidate.tagName.toLowerCase();
    -            if (tag === "body" || tag === "main")
    -                continue;
    -            if (candidate.id === "duet-shell")
    -                continue;
    -            target = candidate;
    -            break;
    -        }
    -        if (target)
    -            break;
    -    }
    -    if (target) {
    -        if (!moved.has(target)) {
    -            moved.add(target);
    -            panel.appendChild(target);
    -        }
    -        return;
    -    }
    -    const wrapper = document.createElement("div");
    -    wrapper.className = "dev-panel-group";
    -    ids.forEach((id) => {
    -        const el = document.getElementById(id);
    -        if (el) {
    -            wrapper.appendChild(el);
    -        }
    -    });
    -    if (wrapper.childElementCount) {
    -        panel.appendChild(wrapper);
    +  const scopes = ["section", "fieldset", ".panel", ".card", ".debug", "div"];
    +  let target = null;
    +  for (const id of ids) {
    +    const el = document.getElementById(id);
    +    if (!el) continue;
    +    for (const scope of scopes) {
    +      const candidate = el.closest(scope);
    +      if (!candidate) continue;
    +      const tag = candidate.tagName.toLowerCase();
    +      if (tag === "body" || tag === "main") continue;
    +      if (candidate.id === "duet-shell") continue;
    +      target = candidate;
    +      break;
    +    }
    +    if (target) break;
    +  }
    +  if (target) {
    +    if (!moved.has(target)) {
    +      moved.add(target);
    +      panel.appendChild(target);
    +    }
    +    return;
    +  }
    +  const wrapper = document.createElement("div");
    +  wrapper.className = "dev-panel-group";
    +  ids.forEach((id) => {
    +    const el = document.getElementById(id);
    +    if (el) {
    +      wrapper.appendChild(el);
         }
    +  });
    +  if (wrapper.childElementCount) {
    +    panel.appendChild(wrapper);
    +  }
     }
     function setupDevPanel() {
    -    const shell = document.getElementById("duet-shell");
    -    const host = shell || document.querySelector("main.container");
    -    if (!host || document.getElementById("dev-panel"))
    -        return;
    -    const panel = document.createElement("details");
    -    panel.id = "dev-panel";
    -    panel.className = "dev-panel";
    -    panel.open = false;
    -    const summary = document.createElement("summary");
    -    summary.textContent = "Dev Panel";
    -    panel.appendChild(summary);
    -    const content = document.createElement("div");
    -    content.className = "dev-panel-content";
    -    panel.appendChild(content);
    -    panel.classList.add("hidden");
    -    host.appendChild(panel);
    -    const moved = new Set();
    -    const groups = [
    -        ["btn-auth", "jwt", "auth-out"],
    -        ["btn-chat", "chat-input", "chat-reply", "chat-error", "chat-proposal"],
    -        ["btn-prefs-get", "btn-prefs-put", "prefs-servings", "prefs-meals", "prefs-out"],
    -        ["btn-plan-gen", "plan-out"],
    -        ["btn-shopping", "shopping-out"],
    -    ];
    -    groups.forEach((ids) => moveGroupIntoDevPanel(ids, content, moved));
    -    ensureDevPanelRememberRow();
    +  const shell = document.getElementById("duet-shell");
    +  const host = shell || document.querySelector("main.container");
    +  if (!host || document.getElementById("dev-panel")) return;
    +  const panel = document.createElement("details");
    +  panel.id = "dev-panel";
    +  panel.className = "dev-panel";
    +  panel.open = false;
    +  const summary = document.createElement("summary");
    +  summary.textContent = "Dev Panel";
    +  panel.appendChild(summary);
    +  const content = document.createElement("div");
    +  content.className = "dev-panel-content";
    +  panel.appendChild(content);
    +  panel.classList.add("hidden");
    +  host.appendChild(panel);
    +  const moved = /* @__PURE__ */ new Set();
    +  const groups = [
    +    ["btn-auth", "jwt", "auth-out"],
    +    ["btn-chat", "chat-input", "chat-reply", "chat-error", "chat-proposal"],
    +    ["btn-prefs-get", "btn-prefs-put", "prefs-servings", "prefs-meals", "prefs-out"],
    +    ["btn-plan-gen", "plan-out"],
    +    ["btn-shopping", "shopping-out"]
    +  ];
    +  groups.forEach((ids) => moveGroupIntoDevPanel(ids, content, moved));
    +  ensureDevPanelRememberRow();
     }
     function ensureDevPanelRememberRow() {
    -    const card = document.querySelector("section.card.legacy-card");
    -    if (!card)
    -        return;
    -    if (getRememberCheckbox())
    -        return;
    -    const row = document.createElement("div");
    -    row.className = "dev-panel-remember-row";
    -    row.style.display = "flex";
    -    row.style.alignItems = "center";
    -    row.style.gap = "12px";
    -    row.style.marginTop = "8px";
    -    const checkboxLabel = document.createElement("label");
    -    checkboxLabel.className = "dev-panel-remember-label";
    -    checkboxLabel.style.display = "inline-flex";
    -    checkboxLabel.style.alignItems = "center";
    -    checkboxLabel.style.gap = "6px";
    -    const checkbox = document.createElement("input");
    -    checkbox.id = "dev-jwt-remember";
    -    checkbox.type = "checkbox";
    -    checkboxLabel.appendChild(checkbox);
    -    checkboxLabel.appendChild(document.createTextNode("Remember me"));
    -    const durationLabel = document.createElement("label");
    -    durationLabel.className = "dev-panel-remember-duration";
    -    durationLabel.style.display = "inline-flex";
    -    durationLabel.style.alignItems = "center";
    -    durationLabel.style.gap = "6px";
    -    durationLabel.textContent = "Duration:";
    -    const durationSelect = document.createElement("select");
    -    durationSelect.id = "dev-jwt-remember-duration";
    -    durationSelect.className = "dev-panel-remember-select";
    -    DEV_JWT_DURATION_OPTIONS.forEach((option) => {
    -        const opt = document.createElement("option");
    -        opt.value = option.value.toString();
    -        opt.textContent = option.label;
    -        durationSelect.appendChild(opt);
    -    });
    -    durationLabel.appendChild(durationSelect);
    -    row.appendChild(checkboxLabel);
    -    row.appendChild(durationLabel);
    -    const authOut = card.querySelector("#auth-out");
    -    if (authOut === null || authOut === void 0 ? void 0 : authOut.parentElement) {
    -        authOut.parentElement.insertBefore(row, authOut);
    -    }
    -    else {
    -        card.appendChild(row);
    -    }
    +  const card = document.querySelector("section.card.legacy-card");
    +  if (!card) return;
    +  if (getRememberCheckbox()) return;
    +  const row = document.createElement("div");
    +  row.className = "dev-panel-remember-row";
    +  row.style.display = "flex";
    +  row.style.alignItems = "center";
    +  row.style.gap = "12px";
    +  row.style.marginTop = "8px";
    +  const checkboxLabel = document.createElement("label");
    +  checkboxLabel.className = "dev-panel-remember-label";
    +  checkboxLabel.style.display = "inline-flex";
    +  checkboxLabel.style.alignItems = "center";
    +  checkboxLabel.style.gap = "6px";
    +  const checkbox = document.createElement("input");
    +  checkbox.id = "dev-jwt-remember";
    +  checkbox.type = "checkbox";
    +  checkboxLabel.appendChild(checkbox);
    +  checkboxLabel.appendChild(document.createTextNode("Remember me"));
    +  const durationLabel = document.createElement("label");
    +  durationLabel.className = "dev-panel-remember-duration";
    +  durationLabel.style.display = "inline-flex";
    +  durationLabel.style.alignItems = "center";
    +  durationLabel.style.gap = "6px";
    +  durationLabel.textContent = "Duration:";
    +  const durationSelect = document.createElement("select");
    +  durationSelect.id = "dev-jwt-remember-duration";
    +  durationSelect.className = "dev-panel-remember-select";
    +  DEV_JWT_DURATION_OPTIONS.forEach((option) => {
    +    const opt = document.createElement("option");
    +    opt.value = option.value.toString();
    +    opt.textContent = option.label;
    +    durationSelect.appendChild(opt);
    +  });
    +  durationLabel.appendChild(durationSelect);
    +  row.appendChild(checkboxLabel);
    +  row.appendChild(durationLabel);
    +  const authOut = card.querySelector("#auth-out");
    +  if (authOut?.parentElement) {
    +    authOut.parentElement.insertBefore(row, authOut);
    +  } else {
    +    card.appendChild(row);
    +  }
     }
     function applyRememberedJwtInput(jwtInput) {
    -    var _a, _b;
    -    ensureDevPanelRememberRow();
    -    const checkbox = getRememberCheckbox();
    -    const durationSelect = getRememberDurationSelect();
    -    if (durationSelect && !durationSelect.value) {
    -        durationSelect.value = DEV_JWT_DEFAULT_TTL_MS.toString();
    -    }
    -    const stored = loadRememberedJwt();
    -    if (stored) {
    -        if (jwtInput) {
    -            jwtInput.value = stored.token;
    -        }
    -        state.token = stored.token;
    -        if (checkbox) {
    -            checkbox.checked = true;
    -        }
    -        if (durationSelect) {
    -            const desired = stored.durationMs.toString();
    -            const has = Array.from(durationSelect.options).some((opt) => opt.value === desired);
    -            durationSelect.value = has ? desired : (_b = (_a = durationSelect.options[0]) === null || _a === void 0 ? void 0 : _a.value) !== null && _b !== void 0 ? _b : desired;
    -        }
    -    }
    -    else {
    -        if (checkbox) {
    -            checkbox.checked = false;
    -        }
    -        if (durationSelect) {
    -            durationSelect.value = DEV_JWT_DEFAULT_TTL_MS.toString();
    -        }
    -    }
    +  ensureDevPanelRememberRow();
    +  const checkbox = getRememberCheckbox();
    +  const durationSelect = getRememberDurationSelect();
    +  if (durationSelect && !durationSelect.value) {
    +    durationSelect.value = DEV_JWT_DEFAULT_TTL_MS.toString();
    +  }
    +  const stored = loadRememberedJwt();
    +  if (stored) {
    +    if (jwtInput) {
    +      jwtInput.value = stored.token;
    +    }
    +    state.token = stored.token;
    +    if (checkbox) {
    +      checkbox.checked = true;
    +    }
    +    if (durationSelect) {
    +      const desired = stored.durationMs.toString();
    +      const has = Array.from(durationSelect.options).some((opt) => opt.value === desired);
    +      durationSelect.value = has ? desired : durationSelect.options[0]?.value ?? desired;
    +    }
    +  } else {
    +    if (checkbox) {
    +      checkbox.checked = false;
    +    }
    +    if (durationSelect) {
    +      durationSelect.value = DEV_JWT_DEFAULT_TTL_MS.toString();
    +    }
    +  }
     }
     function renderProposal() {
    -    const container = document.getElementById("chat-proposal");
    -    const textEl = document.getElementById("chat-proposal-text");
    -    if (!container || !textEl)
    -        return;
    -    if (!state.proposalId || !state.proposedActions.length) {
    -        container.classList.add("hidden");
    -        textEl.textContent = "";
    -        updateProposalActionsVisibility();
    -        return;
    -    }
    -    const summaries = state.proposedActions.map((action) => {
    -        if (action.action_type === "upsert_prefs" && action.prefs) {
    -            return `Update prefs: servings ${action.prefs.servings}, ${action.prefs.plan_days} days, meals/day ${action.prefs.meals_per_day}`;
    -        }
    -        if (action.action_type === "create_inventory_event" && action.event) {
    -            const e = action.event;
    -            return `Inventory: ${e.event_type} ${e.quantity} ${e.unit} ${e.item_name}`;
    -        }
    -        return action.action_type || "proposal";
    -    });
    -    textEl.textContent = summaries.join(" | ");
    -    container.classList.remove("hidden");
    +  const container = document.getElementById("chat-proposal");
    +  const textEl = document.getElementById("chat-proposal-text");
    +  if (!container || !textEl) return;
    +  if (!state.proposalId || !state.proposedActions.length) {
    +    container.classList.add("hidden");
    +    textEl.textContent = "";
         updateProposalActionsVisibility();
    +    return;
    +  }
    +  const summaries = state.proposedActions.map((action) => {
    +    if (action.action_type === "upsert_prefs" && action.prefs) {
    +      return `Update prefs: servings ${action.prefs.servings}, ${action.prefs.plan_days} days, meals/day ${action.prefs.meals_per_day}`;
    +    }
    +    if (action.action_type === "create_inventory_event" && action.event) {
    +      const e = action.event;
    +      return `Inventory: ${e.event_type} ${e.quantity} ${e.unit} ${e.item_name}`;
    +    }
    +    return action.action_type || "proposal";
    +  });
    +  textEl.textContent = summaries.join(" | ");
    +  container.classList.remove("hidden");
    +  updateProposalActionsVisibility();
     }
     function clearProposal() {
    -    if (state.proposalId) {
    -        proposalDismissedIds.delete(state.proposalId);
    -    }
    -    lastResponseRequiresConfirmation = false;
    -    state.proposalId = null;
    -    state.proposedActions = [];
    -    renderProposal();
    +  if (state.proposalId) {
    +    proposalDismissedIds.delete(state.proposalId);
    +  }
    +  lastResponseRequiresConfirmation = false;
    +  state.proposalId = null;
    +  state.proposedActions = [];
    +  renderProposal();
     }
     function shouldShowProposalActions() {
    -    const proposalId = state.proposalId;
    -    if (!proposalId || !state.proposedActions.length)
    -        return false;
    -    if (!lastResponseRequiresConfirmation)
    -        return false;
    -    return !proposalDismissedIds.has(proposalId);
    +  const proposalId = state.proposalId;
    +  if (!proposalId || !state.proposedActions.length) return false;
    +  if (!lastResponseRequiresConfirmation) return false;
    +  return !proposalDismissedIds.has(proposalId);
     }
     function createProposalActionButton(id, icon, extraClass, label, handler) {
    -    const btn = document.createElement("button");
    -    btn.id = id;
    -    btn.type = "button";
    -    btn.className = `icon-btn proposal-action-btn ${extraClass}`;
    -    btn.setAttribute("aria-label", label);
    -    btn.setAttribute("data-testid", id);
    -    btn.textContent = icon;
    -    btn.addEventListener("click", handler);
    -    return btn;
    +  const btn = document.createElement("button");
    +  btn.id = id;
    +  btn.type = "button";
    +  btn.className = `icon-btn proposal-action-btn ${extraClass}`;
    +  btn.setAttribute("aria-label", label);
    +  btn.setAttribute("data-testid", id);
    +  btn.textContent = icon;
    +  btn.addEventListener("click", handler);
    +  return btn;
     }
     function ensureProposalActions() {
    -    if (!proposalActionsContainer || !proposalActionsContainer.isConnected) {
    -        const container = document.createElement("div");
    -        container.id = "proposal-actions";
    -        container.className = "proposal-actions";
    -        container.setAttribute("aria-hidden", "true");
    -        if (!proposalConfirmButton) {
    -            proposalConfirmButton = createProposalActionButton("proposal-confirm", "Ô£ö", "confirm", "Confirm proposal", () => handleProposalConfirm());
    -        }
    -        if (!proposalEditButton) {
    -            proposalEditButton = createProposalActionButton("proposal-edit", "Ô£Å", "edit", "Edit proposal", () => handleProposalEdit());
    -        }
    -        if (!proposalDenyButton) {
    -            proposalDenyButton = createProposalActionButton("proposal-deny", "Ô£û", "deny", "Deny proposal", () => handleProposalDeny());
    -        }
    -        container.append(proposalConfirmButton, proposalEditButton, proposalDenyButton);
    -        proposalActionsContainer = container;
    -    }
    -    if (!proposalActionsContainer) {
    -        return null;
    -    }
    -    const stage = document.querySelector(".duet-stage");
    -    const target = stage !== null && stage !== void 0 ? stage : document.body;
    -    if (proposalActionsContainer.parentElement !== target) {
    -        target.appendChild(proposalActionsContainer);
    -    }
    -    return proposalActionsContainer;
    +  if (!proposalActionsContainer || !proposalActionsContainer.isConnected) {
    +    const container = document.createElement("div");
    +    container.id = "proposal-actions";
    +    container.className = "proposal-actions";
    +    container.setAttribute("aria-hidden", "true");
    +    if (!proposalConfirmButton) {
    +      proposalConfirmButton = createProposalActionButton(
    +        "proposal-confirm",
    +        "\u2714",
    +        "confirm",
    +        "Confirm proposal",
    +        () => handleProposalConfirm()
    +      );
    +    }
    +    if (!proposalEditButton) {
    +      proposalEditButton = createProposalActionButton(
    +        "proposal-edit",
    +        "\u270F",
    +        "edit",
    +        "Edit proposal",
    +        () => handleProposalEdit()
    +      );
    +    }
    +    if (!proposalDenyButton) {
    +      proposalDenyButton = createProposalActionButton(
    +        "proposal-deny",
    +        "\u2716",
    +        "deny",
    +        "Deny proposal",
    +        () => handleProposalDeny()
    +      );
    +    }
    +    container.append(proposalConfirmButton, proposalEditButton, proposalDenyButton);
    +    proposalActionsContainer = container;
    +  }
    +  if (!proposalActionsContainer) {
    +    return null;
    +  }
    +  const stage = document.querySelector(".duet-stage");
    +  const target = stage ?? document.body;
    +  if (proposalActionsContainer.parentElement !== target) {
    +    target.appendChild(proposalActionsContainer);
    +  }
    +  return proposalActionsContainer;
     }
     function updateProposalActionsVisibility() {
    -    const container = ensureProposalActions();
    -    if (!container)
    -        return;
    -    const visible = shouldShowProposalActions();
    -    container.classList.toggle("visible", visible);
    -    container.setAttribute("aria-hidden", visible ? "false" : "true");
    -    [proposalConfirmButton, proposalEditButton, proposalDenyButton].forEach((btn) => {
    -        if (btn) {
    -            btn.disabled = !visible;
    -        }
    -    });
    +  const container = ensureProposalActions();
    +  if (!container) return;
    +  const visible = shouldShowProposalActions();
    +  container.classList.toggle("visible", visible);
    +  container.setAttribute("aria-hidden", visible ? "false" : "true");
    +  [proposalConfirmButton, proposalEditButton, proposalDenyButton].forEach((btn) => {
    +    if (btn) {
    +      btn.disabled = !visible;
    +    }
    +  });
     }
     function handleProposalConfirm() {
    -    if (!state.proposalId)
    -        return;
    -    void sendAsk("confirm");
    +  if (!state.proposalId) return;
    +  void sendAsk("confirm");
     }
     function handleProposalEdit() {
    -    showFloatingComposer();
    -    const input = document.getElementById("duet-input");
    -    if (input) {
    -        input.placeholder = "Type your changes (e.g. 'add milk allergy')ÔÇª";
    -        input.addEventListener("blur", () => { input.placeholder = ""; }, { once: true });
    -    }
    -    setDuetStatus("Send your changes to update the proposal.");
    +  showFloatingComposer();
    +  const input = document.getElementById("duet-input");
    +  if (input) {
    +    input.placeholder = "Type your changes (e.g. 'add milk allergy')\u2026";
    +    input.addEventListener("blur", () => {
    +      input.placeholder = "";
    +    }, { once: true });
    +  }
    +  setDuetStatus("Send your changes to update the proposal.");
     }
     function handleProposalDeny() {
    -    const proposalId = state.proposalId;
    -    if (proposalId) {
    -        proposalDismissedIds.add(proposalId);
    -        // Clear server-side pending proposal
    -        void submitProposalDecision(false);
    -    }
    -    lastResponseRequiresConfirmation = false;
    -    updateProposalActionsVisibility();
    -    setDuetStatus("Proposal dismissed.");
    +  const proposalId = state.proposalId;
    +  if (proposalId) {
    +    proposalDismissedIds.add(proposalId);
    +    void submitProposalDecision(false);
    +  }
    +  lastResponseRequiresConfirmation = false;
    +  updateProposalActionsVisibility();
    +  setDuetStatus("Proposal dismissed.");
     }
     function detectProposalCommand(message) {
    -    const normalized = message.trim().toLowerCase();
    -    if (!normalized)
    -        return null;
    -    if (PROPOSAL_CONFIRM_COMMANDS.has(normalized))
    -        return "confirm";
    -    if (PROPOSAL_DENY_COMMANDS.has(normalized))
    -        return "deny";
    -    return null;
    +  const normalized = message.trim().toLowerCase();
    +  if (!normalized) return null;
    +  if (PROPOSAL_CONFIRM_COMMANDS.has(normalized)) return "confirm";
    +  if (PROPOSAL_DENY_COMMANDS.has(normalized)) return "deny";
    +  return null;
     }
     async function submitProposalDecision(confirm, thinkingIndex) {
    -    var _a, _b, _c;
    -    if (!state.proposalId)
    -        return;
    -    setChatError("");
    -    setDuetStatus(confirm ? "Applying proposal confirmation..." : "Cancelling proposal...");
    -    setComposerBusy(true);
    -    try {
    -        const payload = {
    -            proposal_id: state.proposalId,
    -            confirm,
    -            thread_id: duetState.threadId,
    -        };
    -        const response = await doPost("/chat/confirm", payload);
    -        const success = response.status >= 200 && response.status < 300;
    -        const flowLabel = currentFlowKey === "inventory" ? "Inventory" : "Preferences";
    -        const assistantText = confirm
    -            ? success
    -                ? ((_a = response.json) === null || _a === void 0 ? void 0 : _a.applied)
    -                    ? `${flowLabel} confirmed.`
    -                    : `No pending ${flowLabel.toLowerCase()} added.`
    -                : "Confirmation failed."
    -            : success
    -                ? `${flowLabel} update cancelled.`
    -                : "Cancellation failed.";
    -        if (typeof thinkingIndex === "number") {
    -            updateHistory(thinkingIndex, assistantText);
    -        }
    -        else {
    -            addHistory("assistant", assistantText);
    -        }
    -        state.chatReply = response;
    -        setText("chat-reply", { status: response.status, json: response.json });
    -        setDuetStatus(success ? "Reply received." : "Confirmation failed.");
    -        if (success) {
    -            const confirmedPrefs = ((_b = response.json) === null || _b === void 0 ? void 0 : _b.applied) &&
    -                state.proposedActions.some((action) => action.action_type === "upsert_prefs");
    -            if (confirmedPrefs) {
    -                state.onboarded = true;
    -                ensureOnboardMenu();
    -                renderOnboardMenuButtons();
    -                updatePrefsOverlayVisibility();
    -                userSystemHint = "Long-press this chat bubble to navigate > Inventory";
    -                setUserBubbleEllipsis(false);
    -                setBubbleText(document.getElementById("duet-user-text"), userSystemHint);
    -            }
    -            const confirmedInventory = ((_c = response.json) === null || _c === void 0 ? void 0 : _c.applied) &&
    -                state.proposedActions.some((action) => action.action_type === "create_inventory_event");
    -            if (confirmedInventory) {
    -                state.inventoryOnboarded = true;
    -                ensureOnboardMenu();
    -                renderOnboardMenuButtons();
    -                updateInventoryOverlayVisibility();
    -                userSystemHint = "Long-press this chat bubble to finish onboarding > Meal Plan";
    -                setUserBubbleEllipsis(false);
    -                setBubbleText(document.getElementById("duet-user-text"), userSystemHint);
    -            }
    -            clearProposal();
    -        }
    -    }
    -    catch (err) {
    -        console.error(err);
    -        setChatError("Network error. Try again.");
    -        setDuetStatus("Confirmation failed.");
    -    }
    -    finally {
    -        setComposerBusy(false);
    +  if (!state.proposalId) return;
    +  setChatError("");
    +  setDuetStatus(confirm ? "Applying proposal confirmation..." : "Cancelling proposal...");
    +  setComposerBusy(true);
    +  try {
    +    const payload = {
    +      proposal_id: state.proposalId,
    +      confirm,
    +      thread_id: duetState.threadId
    +    };
    +    const response = await doPost("/chat/confirm", payload);
    +    const success = response.status >= 200 && response.status < 300;
    +    const flowLabel = currentFlowKey === "inventory" ? "Inventory" : "Preferences";
    +    const assistantText = confirm ? success ? response.json?.applied ? `${flowLabel} confirmed.` : `No pending ${flowLabel.toLowerCase()} added.` : "Confirmation failed." : success ? `${flowLabel} update cancelled.` : "Cancellation failed.";
    +    if (typeof thinkingIndex === "number") {
    +      updateHistory(thinkingIndex, assistantText);
    +    } else {
    +      addHistory("assistant", assistantText);
    +    }
    +    state.chatReply = response;
    +    setText("chat-reply", { status: response.status, json: response.json });
    +    setDuetStatus(success ? "Reply received." : "Confirmation failed.");
    +    if (success) {
    +      const confirmedPrefs = response.json?.applied && state.proposedActions.some((action) => action.action_type === "upsert_prefs");
    +      if (confirmedPrefs) {
    +        state.onboarded = true;
    +        ensureOnboardMenu();
    +        renderOnboardMenuButtons();
    +        updatePrefsOverlayVisibility();
    +        userSystemHint = "Long-press this chat bubble to navigate > Inventory";
    +        setUserBubbleEllipsis(false);
    +        setBubbleText(document.getElementById("duet-user-text"), userSystemHint);
    +      }
    +      const confirmedInventory = response.json?.applied && state.proposedActions.some((action) => action.action_type === "create_inventory_event");
    +      if (confirmedInventory) {
    +        state.inventoryOnboarded = true;
    +        ensureOnboardMenu();
    +        renderOnboardMenuButtons();
    +        updateInventoryOverlayVisibility();
    +        userSystemHint = "Long-press this chat bubble to finish onboarding > Meal Plan";
    +        setUserBubbleEllipsis(false);
    +        setBubbleText(document.getElementById("duet-user-text"), userSystemHint);
    +      }
    +      clearProposal();
         }
    +  } catch (err) {
    +    console.error(err);
    +    setChatError("Network error. Try again.");
    +    setDuetStatus("Confirmation failed.");
    +  } finally {
    +    setComposerBusy(false);
    +  }
     }
     function setChatError(msg) {
    -    state.chatError = msg;
    -    const el = document.getElementById("chat-error");
    -    if (el)
    -        el.textContent = msg;
    +  state.chatError = msg;
    +  const el = document.getElementById("chat-error");
    +  if (el) el.textContent = msg;
     }
     function setDuetStatus(msg, isError = false) {
    -    const el = document.getElementById("duet-status");
    -    if (!el)
    -        return;
    -    el.textContent = msg;
    -    el.classList.toggle("error", isError);
    +  const el = document.getElementById("duet-status");
    +  if (!el) return;
    +  el.textContent = msg;
    +  el.classList.toggle("error", isError);
     }
     function updateFlowStatusText() {
    -    var _a;
    -    const el = document.getElementById("duet-flow-chip");
    -    if (!el)
    -        return;
    -    const flow = (_a = flowOptions.find((f) => f.key === currentFlowKey)) !== null && _a !== void 0 ? _a : flowOptions[0];
    -    const label = flow.key === "general" ? "General" : flow.label;
    -    el.textContent = `[${label}]`;
    +  const el = document.getElementById("duet-flow-chip");
    +  if (!el) return;
    +  const flow = flowOptions.find((f) => f.key === currentFlowKey) ?? flowOptions[0];
    +  const label = flow.key === "general" ? "General" : flow.label;
    +  el.textContent = `[${label}]`;
     }
     function setComposerPlaceholder() {
    -    var _a;
    -    const input = document.getElementById("duet-input");
    -    if (!input)
    -        return;
    -    const flow = (_a = flowOptions.find((f) => f.key === currentFlowKey)) !== null && _a !== void 0 ? _a : flowOptions[0];
    -    input.placeholder = flow.placeholder;
    +  const input = document.getElementById("duet-input");
    +  if (!input) return;
    +  const flow = flowOptions.find((f) => f.key === currentFlowKey) ?? flowOptions[0];
    +  input.placeholder = flow.placeholder;
     }
     function flowDisplayLabel(key) {
    -    const flow = flowOptions.find((f) => f.key === key);
    -    if (!flow)
    -        return "Unknown";
    -    return flow.key === "general" ? "Home" : flow.label;
    +  const flow = flowOptions.find((f) => f.key === key);
    +  if (!flow) return "Unknown";
    +  return flow.key === "general" ? "Home" : flow.label;
     }
     function flowMenuCandidates() {
    -    if (currentFlowKey === "general") {
    -        return flowOptions.filter((f) => f.key !== "general");
    -    }
    -    return flowOptions.filter((f) => f.key !== currentFlowKey).map((f) => (f.key === "general" ? { ...f, label: "Home" } : f));
    +  if (currentFlowKey === "general") {
    +    return flowOptions.filter((f) => f.key !== "general");
    +  }
    +  return flowOptions.filter((f) => f.key !== currentFlowKey).map((f) => f.key === "general" ? { ...f, label: "Home" } : f);
     }
     function setFlowMenuOpen(open) {
    -    flowMenuOpen = open;
    -    if (flowMenuDropdown) {
    -        flowMenuDropdown.style.display = open ? "grid" : "none";
    -        flowMenuDropdown.classList.toggle("open", open);
    -        if (open) {
    -            positionFlowMenuDropdown();
    -        }
    +  flowMenuOpen = open;
    +  if (flowMenuDropdown) {
    +    flowMenuDropdown.style.display = open ? "grid" : "none";
    +    flowMenuDropdown.classList.toggle("open", open);
    +    if (open) {
    +      positionFlowMenuDropdown();
         }
    -    flowMenuButton === null || flowMenuButton === void 0 ? void 0 : flowMenuButton.setAttribute("aria-expanded", open ? "true" : "false");
    +  }
    +  flowMenuButton?.setAttribute("aria-expanded", open ? "true" : "false");
     }
     function renderFlowMenu() {
    -    const dropdown = flowMenuDropdown;
    -    const trigger = flowMenuButton;
    -    if (!dropdown || !trigger)
    -        return;
    -    dropdown.innerHTML = "";
    -    flowMenuCandidates().forEach((flow) => {
    -        const item = document.createElement("button");
    -        item.type = "button";
    -        item.className = "flow-menu-item";
    -        item.textContent = flow.key === "general" ? "Home" : flow.label;
    -        item.setAttribute("role", "menuitem");
    -        item.addEventListener("click", () => {
    -            selectFlow(flow.key);
    -            setFlowMenuOpen(false);
    -        });
    -        dropdown.appendChild(item);
    -    });
    -    const devItem = document.createElement("button");
    -    devItem.type = "button";
    -    devItem.className = "flow-menu-item";
    -    devItem.textContent = "Dev Panel";
    -    devItem.setAttribute("role", "menuitem");
    -    devItem.addEventListener("click", () => {
    -        toggleDevPanel();
    -        setFlowMenuOpen(false);
    +  const dropdown = flowMenuDropdown;
    +  const trigger = flowMenuButton;
    +  if (!dropdown || !trigger) return;
    +  dropdown.innerHTML = "";
    +  flowMenuCandidates().forEach((flow) => {
    +    const item = document.createElement("button");
    +    item.type = "button";
    +    item.className = "flow-menu-item";
    +    item.textContent = flow.key === "general" ? "Home" : flow.label;
    +    item.setAttribute("role", "menuitem");
    +    item.addEventListener("click", () => {
    +      selectFlow(flow.key);
    +      setFlowMenuOpen(false);
         });
    -    dropdown.appendChild(devItem);
    -    const currentLabel = flowDisplayLabel(currentFlowKey);
    -    trigger.textContent = "ÔÜÖ";
    -    trigger.setAttribute("aria-label", `Options (current: ${currentLabel})`);
    +    dropdown.appendChild(item);
    +  });
    +  const devItem = document.createElement("button");
    +  devItem.type = "button";
    +  devItem.className = "flow-menu-item";
    +  devItem.textContent = "Dev Panel";
    +  devItem.setAttribute("role", "menuitem");
    +  devItem.addEventListener("click", () => {
    +    toggleDevPanel();
    +    setFlowMenuOpen(false);
    +  });
    +  dropdown.appendChild(devItem);
    +  const currentLabel = flowDisplayLabel(currentFlowKey);
    +  trigger.textContent = "\u2699";
    +  trigger.setAttribute("aria-label", `Options (current: ${currentLabel})`);
     }
     function toggleDevPanel() {
    -    const panel = document.getElementById("dev-panel");
    -    if (!panel)
    -        return;
    -    devPanelVisible = !devPanelVisible;
    -    panel.classList.toggle("hidden", !devPanelVisible);
    -    panel.open = devPanelVisible;
    +  const panel = document.getElementById("dev-panel");
    +  if (!panel) return;
    +  devPanelVisible = !devPanelVisible;
    +  panel.classList.toggle("hidden", !devPanelVisible);
    +  panel.open = devPanelVisible;
     }
     function updateThreadLabel() {
    -    var _a;
    -    const label = document.getElementById("duet-thread-label");
    -    if (!label)
    -        return;
    -    label.textContent = `Thread: ${(_a = duetState.threadId) !== null && _a !== void 0 ? _a : "-"} | Mode: ${lastServerMode}`;
    +  const label = document.getElementById("duet-thread-label");
    +  if (!label) return;
    +  label.textContent = `Thread: ${duetState.threadId ?? "-"} | Mode: ${lastServerMode}`;
     }
     function syncHistoryUi() {
    -    const open = duetState.drawerOpen;
    -    document.body.classList.toggle("history-open", open);
    -    historyOverlay === null || historyOverlay === void 0 ? void 0 : historyOverlay.classList.toggle("open", open);
    -    historyOverlay === null || historyOverlay === void 0 ? void 0 : historyOverlay.setAttribute("aria-hidden", open ? "false" : "true");
    -    if (historyToggle) {
    -        historyToggle.setAttribute("aria-expanded", open ? "true" : "false");
    -        historyToggle.classList.toggle("active", open);
    -    }
    +  const open = duetState.drawerOpen;
    +  document.body.classList.toggle("history-open", open);
    +  historyOverlay?.classList.toggle("open", open);
    +  historyOverlay?.setAttribute("aria-hidden", open ? "false" : "true");
    +  if (historyToggle) {
    +    historyToggle.setAttribute("aria-expanded", open ? "true" : "false");
    +    historyToggle.classList.toggle("active", open);
    +  }
     }
     function renderDuetHistory() {
    -    const list = document.getElementById("duet-history-list");
    -    const empty = document.getElementById("duet-history-empty");
    -    if (!list || !empty)
    -        return;
    -    list.innerHTML = "";
    -    if (!duetState.history.length) {
    -        empty.classList.remove("hidden");
    -        return;
    -    }
    -    empty.classList.add("hidden");
    -    [...duetState.history]
    -        .slice()
    -        .reverse()
    -        .forEach((item) => {
    -        const li = document.createElement("li");
    -        li.className = item.role;
    -        li.textContent = item.text;
    -        list.appendChild(li);
    -    });
    +  const list = document.getElementById("duet-history-list");
    +  const empty = document.getElementById("duet-history-empty");
    +  if (!list || !empty) return;
    +  list.innerHTML = "";
    +  if (!duetState.history.length) {
    +    empty.classList.remove("hidden");
    +    return;
    +  }
    +  empty.classList.add("hidden");
    +  [...duetState.history].slice().reverse().forEach((item) => {
    +    const li = document.createElement("li");
    +    li.className = item.role;
    +    li.textContent = item.text;
    +    list.appendChild(li);
    +  });
     }
     function setBubbleText(element, text) {
    -    if (!element)
    -        return;
    -    element.innerHTML = "";
    -    if (!text)
    -        return;
    -    const parts = text.split("\n");
    -    parts.forEach((line, idx) => {
    -        element.append(document.createTextNode(line));
    -        if (idx < parts.length - 1) {
    -            element.append(document.createElement("br"));
    -        }
    -    });
    +  if (!element) return;
    +  element.innerHTML = "";
    +  if (!text) return;
    +  const parts = text.split("\n");
    +  parts.forEach((line, idx) => {
    +    element.append(document.createTextNode(line));
    +    if (idx < parts.length - 1) {
    +      element.append(document.createElement("br"));
    +    }
    +  });
     }
     function setUserBubbleLabel(isSystem) {
    -    const label = document.querySelector("#duet-user-bubble .bubble-label");
    -    if (label instanceof HTMLElement) {
    -        label.textContent = isSystem ? "System" : "You";
    -    }
    +  const label = document.querySelector("#duet-user-bubble .bubble-label");
    +  if (label instanceof HTMLElement) {
    +    label.textContent = isSystem ? "System" : "You";
    +  }
     }
     function updateDuetBubbles() {
    -    var _a, _b;
    -    const assistant = document.getElementById("duet-assistant-text");
    -    const user = document.getElementById("duet-user-text");
    -    const lastAssistant = [...duetState.history].reverse().find((h) => h.role === "assistant");
    -    const lastUser = [...duetState.history].reverse().find((h) => h.role === "user");
    -    const assistantFallback = "Welcome ÔÇö IÔÇÖm Little Chef.\n\nTo start onboarding, follow the instructions below.";
    -    setBubbleText(assistant, (_a = lastAssistant === null || lastAssistant === void 0 ? void 0 : lastAssistant.text) !== null && _a !== void 0 ? _a : assistantFallback);
    -    const showSentText = userBubbleEllipsisActive && isNormalChatFlow();
    -    const fallbackText = isNormalChatFlow() ? userSystemHint : (_b = lastUser === null || lastUser === void 0 ? void 0 : lastUser.text) !== null && _b !== void 0 ? _b : userSystemHint;
    -    setBubbleText(user, showSentText ? USER_BUBBLE_SENT_TEXT : fallbackText);
    -    const userBubble = document.getElementById("duet-user-bubble");
    -    if (userBubble) {
    -        userBubble.classList.toggle("sent-mode", showSentText);
    -    }
    -    setUserBubbleLabel(!showSentText);
    +  const assistant = document.getElementById("duet-assistant-text");
    +  const user = document.getElementById("duet-user-text");
    +  const lastAssistant = [...duetState.history].reverse().find((h) => h.role === "assistant");
    +  const lastUser = [...duetState.history].reverse().find((h) => h.role === "user");
    +  const assistantFallback = "Welcome \u2014 I\u2019m Little Chef.\n\nTo start onboarding, follow the instructions below.";
    +  setBubbleText(assistant, lastAssistant?.text ?? assistantFallback);
    +  const showSentText = userBubbleEllipsisActive && isNormalChatFlow();
    +  const fallbackText = isNormalChatFlow() ? userSystemHint : lastUser?.text ?? userSystemHint;
    +  setBubbleText(user, showSentText ? USER_BUBBLE_SENT_TEXT : fallbackText);
    +  const userBubble = document.getElementById("duet-user-bubble");
    +  if (userBubble) {
    +    userBubble.classList.toggle("sent-mode", showSentText);
    +  }
    +  setUserBubbleLabel(!showSentText);
     }
     function updateUserBubbleVisibility() {
    -    const userBubble = document.getElementById("duet-user-bubble");
    -    if (!userBubble)
    -        return;
    -    const hide = currentFlowKey === "inventory";
    -    userBubble.style.display = hide ? "none" : "";
    +  const userBubble = document.getElementById("duet-user-bubble");
    +  if (!userBubble) return;
    +  const hide = currentFlowKey === "inventory";
    +  userBubble.style.display = hide ? "none" : "";
     }
     function isNormalChatFlow() {
    -    return NORMAL_CHAT_FLOW_KEYS.has(currentFlowKey);
    +  return NORMAL_CHAT_FLOW_KEYS.has(currentFlowKey);
     }
     function setUserBubbleEllipsis(enabled) {
    -    if (userBubbleEllipsisActive === enabled) {
    -        return;
    -    }
    -    userBubbleEllipsisActive = enabled;
    -    if (!enabled) {
    -        updateDuetBubbles();
    -    }
    +  if (userBubbleEllipsisActive === enabled) {
    +    return;
    +  }
    +  userBubbleEllipsisActive = enabled;
    +  if (!enabled) {
    +    updateDuetBubbles();
    +  }
     }
     function applyDrawerProgress(progress, opts) {
    -    var _a;
    -    const history = document.getElementById("duet-history");
    -    const stage = document.querySelector(".duet-stage");
    -    const userBubble = document.getElementById("duet-user-bubble");
    -    if (!history || !stage || !userBubble)
    -        return;
    -    ensureHistoryClosedOffset(history);
    -    const clamped = Math.max(0, Math.min(1, progress));
    -    duetState.drawerProgress = clamped;
    -    history.style.setProperty("--drawer-progress", clamped.toString());
    -    const shouldShow = ((_a = opts === null || opts === void 0 ? void 0 : opts.dragging) !== null && _a !== void 0 ? _a : false) || clamped > 0;
    -    history.style.display = shouldShow ? "grid" : "none";
    -    history.style.pointerEvents = shouldShow ? "auto" : "none";
    -    history.classList.toggle("dragging", !!(opts === null || opts === void 0 ? void 0 : opts.dragging));
    -    stage.classList.toggle("history-open", shouldShow);
    -    if (opts === null || opts === void 0 ? void 0 : opts.commit) {
    -        duetState.drawerOpen = clamped > 0.35;
    -        history.classList.toggle("open", duetState.drawerOpen);
    -        syncHistoryUi();
    -        if (duetState.drawerOpen) {
    -            handleHistoryOpened();
    -        }
    -    }
    -    userBubble.style.transform = "";
    -}
    -function wireDuetDrag() {
    -    const userBubble = document.getElementById("duet-user-bubble");
    -    if (!userBubble)
    -        return;
    -    let dragging = false;
    -    let startY = 0;
    -    let pointerId = null;
    -    const endDrag = () => {
    -        if (!dragging)
    -            return;
    -        dragging = false;
    -        pointerId = null;
    -        const targetOpen = duetState.drawerProgress > 0.35;
    -        applyDrawerProgress(targetOpen ? 1 : 0, { commit: true });
    -    };
    -    userBubble.addEventListener("pointerdown", (ev) => {
    -        dragging = true;
    -        startY = ev.clientY;
    -        pointerId = ev.pointerId;
    -        userBubble.setPointerCapture(ev.pointerId);
    -        applyDrawerProgress(duetState.drawerProgress, { dragging: true });
    -    });
    -    userBubble.addEventListener("pointermove", (ev) => {
    -        if (!dragging || (pointerId !== null && ev.pointerId !== pointerId))
    -            return;
    -        const dy = startY - ev.clientY;
    -        const progress = dy <= 0 ? 0 : Math.min(dy / 120, 1);
    -        applyDrawerProgress(progress, { dragging: true });
    -    });
    -    const cancel = () => {
    -        if (!dragging)
    -            return;
    -        dragging = false;
    -        pointerId = null;
    -        applyDrawerProgress(duetState.drawerOpen ? 1 : 0, { commit: true });
    -    };
    -    userBubble.addEventListener("pointerup", endDrag);
    -    userBubble.addEventListener("pointercancel", cancel);
    -    userBubble.addEventListener("lostpointercapture", cancel);
    +  const history = document.getElementById("duet-history");
    +  const stage = document.querySelector(".duet-stage");
    +  const userBubble = document.getElementById("duet-user-bubble");
    +  if (!history || !stage || !userBubble) return;
    +  ensureHistoryClosedOffset(history);
    +  const clamped = Math.max(0, Math.min(1, progress));
    +  duetState.drawerProgress = clamped;
    +  history.style.setProperty("--drawer-progress", clamped.toString());
    +  const shouldShow = (opts?.dragging ?? false) || clamped > 0;
    +  history.style.display = shouldShow ? "grid" : "none";
    +  history.style.pointerEvents = shouldShow ? "auto" : "none";
    +  history.classList.toggle("dragging", !!opts?.dragging);
    +  stage.classList.toggle("history-open", shouldShow);
    +  if (opts?.commit) {
    +    duetState.drawerOpen = clamped > 0.35;
    +    history.classList.toggle("open", duetState.drawerOpen);
    +    syncHistoryUi();
    +    if (duetState.drawerOpen) {
    +      handleHistoryOpened();
    +    }
    +  }
    +  userBubble.style.transform = "";
     }
     function handleHistoryOpened() {
    -    resetHistoryBadge();
    -    setUserBubbleEllipsis(false);
    +  resetHistoryBadge();
    +  setUserBubbleEllipsis(false);
     }
     function setDrawerOpen(open) {
    -    applyDrawerProgress(open ? 1 : 0, { commit: true });
    +  applyDrawerProgress(open ? 1 : 0, { commit: true });
     }
     function ensureHistoryClosedOffset(historyEl) {
    -    var _a;
    -    const stage = document.querySelector(".duet-stage");
    -    const stageHeight = (_a = stage === null || stage === void 0 ? void 0 : stage.offsetHeight) !== null && _a !== void 0 ? _a : 0;
    -    const historyHeight = historyEl.offsetHeight || 0;
    -    const offset = Math.max(historyHeight, stageHeight) + 200; // larger buffer to force fully off-screen
    -    historyEl.style.setProperty("--history-closed-offset", `${offset}px`);
    +  const stage = document.querySelector(".duet-stage");
    +  const stageHeight = stage?.offsetHeight ?? 0;
    +  const historyHeight = historyEl.offsetHeight || 0;
    +  const offset = Math.max(historyHeight, stageHeight) + 200;
    +  historyEl.style.setProperty("--history-closed-offset", `${offset}px`);
     }
     function bindResizeForHistoryOffset() {
    -    const history = document.getElementById("duet-history");
    -    if (!history)
    -        return;
    -    const recalc = () => ensureHistoryClosedOffset(history);
    -    window.addEventListener("resize", recalc);
    -    recalc();
    +  const history = document.getElementById("duet-history");
    +  if (!history) return;
    +  const recalc = () => ensureHistoryClosedOffset(history);
    +  window.addEventListener("resize", recalc);
    +  recalc();
     }
     function elevateDuetBubbles() {
    -    const assistantBubble = document.getElementById("duet-assistant-bubble");
    -    const userBubble = document.getElementById("duet-user-bubble");
    -    if (assistantBubble) {
    -        assistantBubble.style.zIndex = "50";
    -    }
    -    if (userBubble) {
    -        userBubble.style.zIndex = "50";
    -    }
    +  const assistantBubble = document.getElementById("duet-assistant-bubble");
    +  const userBubble = document.getElementById("duet-user-bubble");
    +  if (assistantBubble) {
    +    assistantBubble.style.zIndex = "50";
    +  }
    +  if (userBubble) {
    +    userBubble.style.zIndex = "50";
    +  }
     }
     function startNewThread() {
    -    duetState.threadId = crypto.randomUUID();
    -    duetState.history = [];
    -    renderDuetHistory();
    -    updateDuetBubbles();
    -    updateThreadLabel();
    -    setDuetStatus("New thread created.");
    +  duetState.threadId = crypto.randomUUID();
    +  duetState.history = [];
    +  renderDuetHistory();
    +  updateDuetBubbles();
    +  updateThreadLabel();
    +  setDuetStatus("New thread created.");
     }
     function addHistory(role, text) {
    -    duetState.history.push({ role, text });
    -    renderDuetHistory();
    -    updateDuetBubbles();
    -    return duetState.history.length - 1;
    +  duetState.history.push({ role, text });
    +  renderDuetHistory();
    +  updateDuetBubbles();
    +  return duetState.history.length - 1;
     }
     function updateHistory(index, text) {
    -    if (index < 0 || index >= duetState.history.length)
    -        return;
    -    duetState.history[index] = { ...duetState.history[index], text };
    -    renderDuetHistory();
    -    updateDuetBubbles();
    +  if (index < 0 || index >= duetState.history.length) return;
    +  duetState.history[index] = { ...duetState.history[index], text };
    +  renderDuetHistory();
    +  updateDuetBubbles();
     }
     function setupHistoryDrawerUi() {
    -    const shell = document.getElementById("duet-shell");
    -    const stage = document.querySelector(".duet-stage");
    -    if (!shell || !stage)
    -        return;
    -    const historyPanel = document.getElementById("duet-history");
    -    const historyHeader = historyPanel === null || historyPanel === void 0 ? void 0 : historyPanel.querySelector(".history-header");
    -    if (historyHeader && !historyHeader.querySelector("#duet-new-thread")) {
    -        const newThreadBtn = document.createElement("button");
    -        newThreadBtn.id = "duet-new-thread";
    -        newThreadBtn.type = "button";
    -        newThreadBtn.className = "pill-btn";
    -        newThreadBtn.textContent = "New Thread";
    -        newThreadBtn.addEventListener("click", () => startNewThread());
    -        historyHeader.appendChild(newThreadBtn);
    -    }
    -    if (!historyOverlay) {
    -        historyOverlay = document.createElement("div");
    -        historyOverlay.className = "history-overlay";
    -        historyOverlay.setAttribute("aria-hidden", "true");
    -        historyOverlay.addEventListener("click", () => setDrawerOpen(false));
    -        historyOverlay.addEventListener("touchmove", (ev) => {
    -            ev.preventDefault();
    -        }, { passive: false });
    -        historyOverlay.addEventListener("wheel", (ev) => {
    -            ev.preventDefault();
    -        }, { passive: false });
    -        shell.appendChild(historyOverlay);
    -    }
    -    if (!historyToggle) {
    -        historyToggle = document.createElement("button");
    -        historyToggle.id = "duet-history-toggle";
    -        historyToggle.type = "button";
    -        historyToggle.className = "icon-btn history-toggle";
    -        historyToggle.setAttribute("aria-label", "Toggle history drawer");
    -        historyToggle.setAttribute("aria-controls", "duet-history");
    -        historyToggle.setAttribute("aria-expanded", "false");
    -        historyToggle.textContent = "­ƒòæ";
    -        historyToggle.addEventListener("click", () => setDrawerOpen(!duetState.drawerOpen));
    -        historyToggle.addEventListener("keydown", (ev) => {
    -            if (ev.key === "Enter" || ev.key === " ") {
    -                ev.preventDefault();
    -                setDrawerOpen(!duetState.drawerOpen);
    -            }
    -        });
    -        stage.appendChild(historyToggle);
    -    }
    -    resetHistoryBadge();
    +  const shell = document.getElementById("duet-shell");
    +  const stage = document.querySelector(".duet-stage");
    +  if (!shell || !stage) return;
    +  const historyPanel = document.getElementById("duet-history");
    +  const historyHeader = historyPanel?.querySelector(".history-header");
    +  if (historyHeader && !historyHeader.querySelector("#duet-new-thread")) {
    +    const newThreadBtn = document.createElement("button");
    +    newThreadBtn.id = "duet-new-thread";
    +    newThreadBtn.type = "button";
    +    newThreadBtn.className = "pill-btn";
    +    newThreadBtn.textContent = "New Thread";
    +    newThreadBtn.addEventListener("click", () => startNewThread());
    +    historyHeader.appendChild(newThreadBtn);
    +  }
    +  if (!historyOverlay) {
    +    historyOverlay = document.createElement("div");
    +    historyOverlay.className = "history-overlay";
    +    historyOverlay.setAttribute("aria-hidden", "true");
    +    historyOverlay.addEventListener("click", () => setDrawerOpen(false));
    +    historyOverlay.addEventListener(
    +      "touchmove",
    +      (ev) => {
    +        ev.preventDefault();
    +      },
    +      { passive: false }
    +    );
    +    historyOverlay.addEventListener(
    +      "wheel",
    +      (ev) => {
    +        ev.preventDefault();
    +      },
    +      { passive: false }
    +    );
    +    shell.appendChild(historyOverlay);
    +  }
    +  if (!historyToggle) {
    +    historyToggle = document.createElement("button");
    +    historyToggle.id = "duet-history-toggle";
    +    historyToggle.type = "button";
    +    historyToggle.className = "icon-btn history-toggle";
    +    historyToggle.setAttribute("aria-label", "Toggle history drawer");
    +    historyToggle.setAttribute("aria-controls", "duet-history");
    +    historyToggle.setAttribute("aria-expanded", "false");
    +    historyToggle.textContent = "\u{1F551}";
    +    historyToggle.addEventListener("click", () => setDrawerOpen(!duetState.drawerOpen));
    +    historyToggle.addEventListener("keydown", (ev) => {
    +      if (ev.key === "Enter" || ev.key === " ") {
    +        ev.preventDefault();
    +        setDrawerOpen(!duetState.drawerOpen);
    +      }
    +    });
    +    stage.appendChild(historyToggle);
    +  }
    +  if (!recipePacksButton) {
    +    recipePacksButton = document.createElement("button");
    +    recipePacksButton.id = "duet-recipe-packs";
    +    recipePacksButton.type = "button";
    +    recipePacksButton.className = "icon-btn recipe-packs-btn";
    +    recipePacksButton.setAttribute("aria-label", "Recipe packs");
    +    recipePacksButton.textContent = "\u{1F4D6}";
    +    recipePacksButton.addEventListener("click", () => openPacksModal());
    +    stage.appendChild(recipePacksButton);
    +  }
    +  resetHistoryBadge();
     }
     function ensureHistoryBadgeElement() {
    -    if (!historyToggle)
    -        return null;
    -    if (historyBadgeEl && historyBadgeEl.isConnected) {
    -        return historyBadgeEl;
    -    }
    -    const badge = document.createElement("span");
    -    badge.className = "history-badge";
    -    badge.setAttribute("aria-hidden", "true");
    -    historyToggle.appendChild(badge);
    -    historyBadgeEl = badge;
    -    return badge;
    +  if (!historyToggle) return null;
    +  if (historyBadgeEl && historyBadgeEl.isConnected) {
    +    return historyBadgeEl;
    +  }
    +  const badge = document.createElement("span");
    +  badge.className = "history-badge";
    +  badge.setAttribute("aria-hidden", "true");
    +  historyToggle.appendChild(badge);
    +  historyBadgeEl = badge;
    +  return badge;
     }
     function updateHistoryBadge() {
    -    const badge = ensureHistoryBadgeElement();
    -    if (!badge)
    -        return;
    -    if (historyBadgeCount > 0) {
    -        badge.textContent =
    -            historyBadgeCount > HISTORY_BADGE_DISPLAY_MAX
    -                ? `${HISTORY_BADGE_DISPLAY_MAX}+`
    -                : historyBadgeCount.toString();
    -        badge.classList.add("visible");
    -        badge.setAttribute("aria-hidden", "false");
    -    }
    -    else {
    -        badge.textContent = "";
    -        badge.classList.remove("visible");
    -        badge.setAttribute("aria-hidden", "true");
    -    }
    +  const badge = ensureHistoryBadgeElement();
    +  if (!badge) return;
    +  if (historyBadgeCount > 0) {
    +    badge.textContent = historyBadgeCount > HISTORY_BADGE_DISPLAY_MAX ? `${HISTORY_BADGE_DISPLAY_MAX}+` : historyBadgeCount.toString();
    +    badge.classList.add("visible");
    +    badge.setAttribute("aria-hidden", "false");
    +  } else {
    +    badge.textContent = "";
    +    badge.classList.remove("visible");
    +    badge.setAttribute("aria-hidden", "true");
    +  }
     }
     function incrementHistoryBadge() {
    -    historyBadgeCount = Math.max(0, historyBadgeCount + 1);
    -    updateHistoryBadge();
    +  historyBadgeCount = Math.max(0, historyBadgeCount + 1);
    +  updateHistoryBadge();
     }
     function resetHistoryBadge() {
    -    historyBadgeCount = 0;
    -    updateHistoryBadge();
    +  historyBadgeCount = 0;
    +  updateHistoryBadge();
     }
     function wireHistoryHotkeys() {
    -    document.addEventListener("keydown", (ev) => {
    -        if (ev.key === "Escape" && duetState.drawerOpen) {
    -            setDrawerOpen(false);
    -        }
    -    });
    +  document.addEventListener("keydown", (ev) => {
    +    if (ev.key === "Escape" && duetState.drawerOpen) {
    +      setDrawerOpen(false);
    +    }
    +  });
     }
     function formatQuantity(quantity, unit, approx) {
    -    const safe = Number.isFinite(quantity) ? quantity : 0;
    -    const rounded = Math.abs(safe) >= 10 ? safe.toFixed(1) : safe.toString();
    -    const trimmed = rounded.replace(/\.0+$/, "").replace(/(\.\d*[1-9])0+$/, "$1");
    -    const prefix = approx ? "~" : "";
    -    return `${prefix}${trimmed} ${unit}`;
    +  const safe = Number.isFinite(quantity) ? quantity : 0;
    +  const rounded = Math.abs(safe) >= 10 ? safe.toFixed(1) : safe.toString();
    +  const trimmed = rounded.replace(/\.0+$/, "").replace(/(\.\d*[1-9])0+$/, "$1");
    +  const prefix = approx ? "~" : "";
    +  return `${prefix}${trimmed} ${unit}`;
     }
     function setInventoryStatus(text) {
    -    if (inventoryStatusEl) {
    -        inventoryStatusEl.textContent = text;
    -    }
    +  if (inventoryStatusEl) {
    +    inventoryStatusEl.textContent = text;
    +  }
     }
     function markInventoryOnboarded(hasData) {
    -    const already = !!state.inventoryOnboarded;
    -    state.inventoryOnboarded = !!state.inventoryOnboarded || hasData;
    -    if (!already && state.inventoryOnboarded) {
    -        ensureOnboardMenu();
    -        renderOnboardMenuButtons();
    -        userSystemHint = "Long-press this chat bubble to finish onboarding > Meal Plan";
    -        setUserBubbleEllipsis(false);
    -        setBubbleText(document.getElementById("duet-user-text"), userSystemHint);
    -        updateInventoryOverlayVisibility();
    -    }
    +  const already = !!state.inventoryOnboarded;
    +  state.inventoryOnboarded = !!state.inventoryOnboarded || hasData;
    +  if (!already && state.inventoryOnboarded) {
    +    ensureOnboardMenu();
    +    renderOnboardMenuButtons();
    +    userSystemHint = "Long-press this chat bubble to finish onboarding > Meal Plan";
    +    setUserBubbleEllipsis(false);
    +    setBubbleText(document.getElementById("duet-user-text"), userSystemHint);
    +    updateInventoryOverlayVisibility();
    +  }
     }
     function renderInventoryLists(low, summary) {
    -    const lowList = inventoryLowList;
    -    if (lowList) {
    -        lowList.innerHTML = "";
    -        if (!low || !low.length) {
    -            const li = document.createElement("li");
    -            li.className = "inventory-empty";
    -            li.textContent = "No low stock items.";
    -            lowList.appendChild(li);
    -        }
    -        else {
    -            low.forEach((item) => {
    -                const li = document.createElement("li");
    -                const reason = item.reason ? ` - ${item.reason}` : "";
    -                li.textContent = `${item.item_name} - ${formatQuantity(item.quantity, item.unit)} (threshold ${item.threshold})${reason}`;
    -                lowList.appendChild(li);
    -            });
    -        }
    -    }
    -    const summaryList = inventorySummaryList;
    -    if (summaryList) {
    -        summaryList.innerHTML = "";
    -        if (!summary || !summary.length) {
    -            const li = document.createElement("li");
    -            li.className = "inventory-empty";
    -            li.textContent = "No items.";
    -            summaryList.appendChild(li);
    -        }
    -        else {
    -            summary.forEach((item) => {
    -                const li = document.createElement("li");
    -                li.textContent = `${item.item_name} - ${formatQuantity(item.quantity, item.unit, item.approx)}`;
    -                summaryList.appendChild(li);
    -            });
    -        }
    +  const lowList = inventoryLowList;
    +  if (lowList) {
    +    lowList.innerHTML = "";
    +    if (!low || !low.length) {
    +      const li = document.createElement("li");
    +      li.className = "inventory-empty";
    +      li.textContent = "No low stock items.";
    +      lowList.appendChild(li);
    +    } else {
    +      low.forEach((item) => {
    +        const li = document.createElement("li");
    +        const reason = item.reason ? ` - ${item.reason}` : "";
    +        li.textContent = `${item.item_name} - ${formatQuantity(item.quantity, item.unit)} (threshold ${item.threshold})${reason}`;
    +        lowList.appendChild(li);
    +      });
    +    }
    +  }
    +  const summaryList = inventorySummaryList;
    +  if (summaryList) {
    +    summaryList.innerHTML = "";
    +    if (!summary || !summary.length) {
    +      const li = document.createElement("li");
    +      li.className = "inventory-empty";
    +      li.textContent = "No items.";
    +      summaryList.appendChild(li);
    +    } else {
    +      summary.forEach((item) => {
    +        const li = document.createElement("li");
    +        li.textContent = `${item.item_name} - ${formatQuantity(item.quantity, item.unit, item.approx)}`;
    +        summaryList.appendChild(li);
    +      });
         }
    +  }
     }
     async function refreshInventoryOverlay(force = false) {
    -    var _a, _b;
    -    if (!inventoryOverlay)
    -        return;
    -    if (inventoryLoading && !force)
    -        return;
    -    inventoryLoading = true;
    -    setInventoryStatus("Loading...");
    -    try {
    -        const [summaryResp, lowResp] = await Promise.all([doGet("/inventory/summary"), doGet("/inventory/low-stock")]);
    -        if (summaryResp.status === 401 || lowResp.status === 401) {
    -            setInventoryStatus("Unauthorized (set token in Dev Panel)");
    -            renderInventoryLists([], []);
    -            inventoryHasLoaded = true;
    -            return;
    -        }
    -        const summaryItems = Array.isArray((_a = summaryResp.json) === null || _a === void 0 ? void 0 : _a.items) ? summaryResp.json.items : [];
    -        const lowItems = Array.isArray((_b = lowResp.json) === null || _b === void 0 ? void 0 : _b.items) ? lowResp.json.items : [];
    -        renderInventoryLists(lowItems, summaryItems);
    -        const hasAny = lowItems.length > 0 || summaryItems.length > 0;
    -        setInventoryStatus(hasAny ? "Read-only snapshot" : "No items yet.");
    -        markInventoryOnboarded(hasAny);
    -        inventoryHasLoaded = true;
    -    }
    -    catch (err) {
    -        setInventoryStatus("Network error. Try refresh.");
    -        renderInventoryLists([], []);
    -        console.error(err);
    -    }
    -    finally {
    -        inventoryLoading = false;
    -    }
    +  if (!inventoryOverlay) return;
    +  if (inventoryLoading && !force) return;
    +  inventoryLoading = true;
    +  setInventoryStatus("Loading...");
    +  try {
    +    const [summaryResp, lowResp] = await Promise.all([doGet("/inventory/summary"), doGet("/inventory/low-stock")]);
    +    if (summaryResp.status === 401 || lowResp.status === 401) {
    +      setInventoryStatus("Unauthorized (set token in Dev Panel)");
    +      renderInventoryLists([], []);
    +      inventoryHasLoaded = true;
    +      return;
    +    }
    +    const summaryItems = Array.isArray(summaryResp.json?.items) ? summaryResp.json.items : [];
    +    const lowItems = Array.isArray(lowResp.json?.items) ? lowResp.json.items : [];
    +    renderInventoryLists(lowItems, summaryItems);
    +    const hasAny = lowItems.length > 0 || summaryItems.length > 0;
    +    setInventoryStatus(hasAny ? "Read-only snapshot" : "No items yet.");
    +    markInventoryOnboarded(hasAny);
    +    inventoryHasLoaded = true;
    +  } catch (err) {
    +    setInventoryStatus("Network error. Try refresh.");
    +    renderInventoryLists([], []);
    +    console.error(err);
    +  } finally {
    +    inventoryLoading = false;
    +  }
     }
     function updateInventoryOverlayVisibility() {
    -    if (!inventoryOverlay)
    -        return;
    -    const wantsInventory = currentFlowKey === "inventory";
    -    const canShowInventory = !!state.inventoryOnboarded;
    -    const visible = wantsInventory && canShowInventory;
    -    inventoryOverlay.classList.toggle("hidden", !visible);
    -    inventoryOverlay.style.display = visible ? "flex" : "none";
    -    if (wantsInventory) {
    -        if (!canShowInventory) {
    -            refreshInventoryOverlay(true);
    -        }
    -        else if (visible && (!inventoryHasLoaded || !(inventoryLowList === null || inventoryLowList === void 0 ? void 0 : inventoryLowList.childElementCount))) {
    -            refreshInventoryOverlay();
    -        }
    -    }
    +  if (!inventoryOverlay) return;
    +  const wantsInventory = currentFlowKey === "inventory";
    +  const canShowInventory = !!state.inventoryOnboarded;
    +  const visible = wantsInventory && canShowInventory;
    +  inventoryOverlay.classList.toggle("hidden", !visible);
    +  inventoryOverlay.style.display = visible ? "flex" : "none";
    +  if (wantsInventory) {
    +    if (!canShowInventory) {
    +      refreshInventoryOverlay(true);
    +    } else if (visible && (!inventoryHasLoaded || !inventoryLowList?.childElementCount)) {
    +      refreshInventoryOverlay();
    +    }
    +  }
     }
     function setupInventoryGhostOverlay() {
    -    const shell = document.getElementById("duet-shell");
    -    const stage = shell === null || shell === void 0 ? void 0 : shell.querySelector(".duet-stage");
    -    if (!shell || !stage || document.getElementById("inventory-ghost"))
    -        return;
    -    const overlay = document.createElement("div");
    -    overlay.id = "inventory-ghost";
    -    overlay.className = "inventory-ghost hidden";
    -    overlay.style.display = "none";
    -    overlay.style.pointerEvents = "none";
    -    overlay.style.zIndex = "1";
    -    overlay.style.flexDirection = "column";
    -    overlay.style.justifyContent = "center";
    -    overlay.style.alignItems = "center";
    -    overlay.style.gap = "14px";
    -    overlay.style.inset = "10px";
    -    overlay.style.width = "calc(100% - 20px)";
    -    overlay.style.height = "calc(100% - 20px)";
    -    overlay.style.position = "absolute";
    -    const panel = document.createElement("div");
    -    panel.className = "prefs-overlay-content";
    -    panel.style.display = "grid";
    -    panel.style.pointerEvents = "auto";
    -    panel.style.gap = "12px";
    -    panel.style.width = "100%";
    -    panel.style.maxWidth = "520px";
    -    panel.style.margin = "0 auto";
    -    const header = document.createElement("div");
    -    header.className = "inventory-ghost-header";
    -    const title = document.createElement("span");
    -    title.textContent = "Inventory";
    -    const refresh = document.createElement("button");
    -    refresh.type = "button";
    -    refresh.className = "ghost-refresh";
    -    refresh.textContent = "Refresh";
    -    refresh.addEventListener("click", () => refreshInventoryOverlay(true));
    -    header.appendChild(title);
    -    header.appendChild(refresh);
    -    const status = document.createElement("div");
    -    status.id = "inventory-ghost-status";
    -    status.className = "inventory-ghost-status";
    -    status.textContent = "Select Inventory to load.";
    -    const lowSection = document.createElement("div");
    -    lowSection.className = "inventory-ghost-section";
    -    lowSection.style.width = "100%";
    -    const lowTitle = document.createElement("div");
    -    lowTitle.className = "inventory-ghost-title";
    -    lowTitle.textContent = "Low stock";
    -    const lowList = document.createElement("ul");
    -    lowList.id = "inventory-low-list";
    -    lowSection.appendChild(lowTitle);
    -    lowSection.appendChild(lowList);
    -    const summarySection = document.createElement("div");
    -    summarySection.className = "inventory-ghost-section";
    -    summarySection.style.width = "100%";
    -    const summaryTitle = document.createElement("div");
    -    summaryTitle.className = "inventory-ghost-title";
    -    summaryTitle.textContent = "In stock";
    -    const summaryList = document.createElement("ul");
    -    summaryList.id = "inventory-summary-list";
    -    summarySection.appendChild(summaryTitle);
    -    summarySection.appendChild(summaryList);
    -    panel.appendChild(header);
    -    panel.appendChild(status);
    -    panel.appendChild(lowSection);
    -    panel.appendChild(summarySection);
    -    overlay.appendChild(panel);
    -    stage.appendChild(overlay);
    -    inventoryOverlay = overlay;
    -    inventoryStatusEl = status;
    -    inventoryLowList = lowList;
    -    inventorySummaryList = summaryList;
    +  const shell = document.getElementById("duet-shell");
    +  const stage = shell?.querySelector(".duet-stage");
    +  if (!shell || !stage || document.getElementById("inventory-ghost")) return;
    +  const overlay = document.createElement("div");
    +  overlay.id = "inventory-ghost";
    +  overlay.className = "inventory-ghost hidden";
    +  overlay.style.display = "none";
    +  overlay.style.pointerEvents = "none";
    +  overlay.style.zIndex = "1";
    +  overlay.style.flexDirection = "column";
    +  overlay.style.justifyContent = "center";
    +  overlay.style.alignItems = "center";
    +  overlay.style.gap = "14px";
    +  overlay.style.inset = "10px";
    +  overlay.style.width = "calc(100% - 20px)";
    +  overlay.style.height = "calc(100% - 20px)";
    +  overlay.style.position = "absolute";
    +  const panel = document.createElement("div");
    +  panel.className = "prefs-overlay-content";
    +  panel.style.display = "grid";
    +  panel.style.pointerEvents = "auto";
    +  panel.style.gap = "12px";
    +  panel.style.width = "100%";
    +  panel.style.maxWidth = "520px";
    +  panel.style.margin = "0 auto";
    +  const header = document.createElement("div");
    +  header.className = "inventory-ghost-header";
    +  const title = document.createElement("span");
    +  title.textContent = "Inventory";
    +  const refresh = document.createElement("button");
    +  refresh.type = "button";
    +  refresh.className = "ghost-refresh";
    +  refresh.textContent = "Refresh";
    +  refresh.addEventListener("click", () => refreshInventoryOverlay(true));
    +  header.appendChild(title);
    +  header.appendChild(refresh);
    +  const status = document.createElement("div");
    +  status.id = "inventory-ghost-status";
    +  status.className = "inventory-ghost-status";
    +  status.textContent = "Select Inventory to load.";
    +  const lowSection = document.createElement("div");
    +  lowSection.className = "inventory-ghost-section";
    +  lowSection.style.width = "100%";
    +  const lowTitle = document.createElement("div");
    +  lowTitle.className = "inventory-ghost-title";
    +  lowTitle.textContent = "Low stock";
    +  const lowList = document.createElement("ul");
    +  lowList.id = "inventory-low-list";
    +  lowSection.appendChild(lowTitle);
    +  lowSection.appendChild(lowList);
    +  const summarySection = document.createElement("div");
    +  summarySection.className = "inventory-ghost-section";
    +  summarySection.style.width = "100%";
    +  const summaryTitle = document.createElement("div");
    +  summaryTitle.className = "inventory-ghost-title";
    +  summaryTitle.textContent = "In stock";
    +  const summaryList = document.createElement("ul");
    +  summaryList.id = "inventory-summary-list";
    +  summarySection.appendChild(summaryTitle);
    +  summarySection.appendChild(summaryList);
    +  panel.appendChild(header);
    +  panel.appendChild(status);
    +  panel.appendChild(lowSection);
    +  panel.appendChild(summarySection);
    +  overlay.appendChild(panel);
    +  stage.appendChild(overlay);
    +  inventoryOverlay = overlay;
    +  inventoryStatusEl = status;
    +  inventoryLowList = lowList;
    +  inventorySummaryList = summaryList;
     }
     function setPrefsOverlayStatus(text) {
    -    if (prefsOverlayStatusEl) {
    -        prefsOverlayStatusEl.textContent = text;
    -    }
    +  if (prefsOverlayStatusEl) {
    +    prefsOverlayStatusEl.textContent = text;
    +  }
     }
     function renderPrefsOverlay(prefs) {
    -    const details = prefsOverlayDetails;
    -    const summaryEl = prefsOverlaySummaryEl;
    -    if (!details || !summaryEl)
    -        return;
    -    details.innerHTML = "";
    -    if (!prefs) {
    -        summaryEl.textContent = "No preferences yet.";
    -        const empty = document.createElement("div");
    -        empty.className = "prefs-overlay-empty";
    -        empty.textContent = "No preferences saved yet.";
    -        details.appendChild(empty);
    -        return;
    -    }
    -    const servings = Number.isFinite(prefs.servings) ? prefs.servings : "ÔÇö";
    -    const meals = Number.isFinite(prefs.meals_per_day) ? prefs.meals_per_day : "ÔÇö";
    -    const days = Number.isFinite(prefs.plan_days) ? prefs.plan_days : "ÔÇö";
    -    summaryEl.textContent = `${servings} servings ┬À ${days} days ┬À ${meals} meals/day`;
    -    const sections = [
    -        { title: "Allergies", items: Array.isArray(prefs.allergies) ? prefs.allergies : [] },
    -        { title: "Dislikes", items: Array.isArray(prefs.dislikes) ? prefs.dislikes : [] },
    -        { title: "Likes", items: Array.isArray(prefs.cuisine_likes) ? prefs.cuisine_likes : [] },
    -    ];
    -    sections.forEach((section) => {
    -        const sectionEl = document.createElement("div");
    -        sectionEl.className = "prefs-overlay-section inventory-ghost-section";
    -        const titleEl = document.createElement("div");
    -        titleEl.className = "prefs-overlay-title inventory-ghost-title";
    -        titleEl.textContent = section.title;
    -        sectionEl.appendChild(titleEl);
    -        const list = document.createElement("ul");
    -        list.className = "prefs-overlay-list";
    -        if (!section.items.length) {
    -            const li = document.createElement("li");
    -            li.className = "inventory-empty";
    -            li.textContent = "None yet.";
    -            list.appendChild(li);
    -        }
    -        else {
    -            section.items.forEach((item) => {
    -                const li = document.createElement("li");
    -                li.textContent = item;
    -                list.appendChild(li);
    -            });
    -        }
    -        sectionEl.appendChild(list);
    -        details.appendChild(sectionEl);
    -    });
    -    if (prefs.notes) {
    -        const notesSection = document.createElement("div");
    -        notesSection.className = "prefs-overlay-section";
    -        const notesTitle = document.createElement("div");
    -        notesTitle.className = "prefs-overlay-title";
    -        notesTitle.textContent = "Notes";
    -        const notesBody = document.createElement("div");
    -        notesBody.className = "prefs-overlay-notes";
    -        notesBody.textContent = prefs.notes;
    -        notesSection.appendChild(notesTitle);
    -        notesSection.appendChild(notesBody);
    -        details.appendChild(notesSection);
    -    }
    +  const details = prefsOverlayDetails;
    +  const summaryEl = prefsOverlaySummaryEl;
    +  if (!details || !summaryEl) return;
    +  details.innerHTML = "";
    +  if (!prefs) {
    +    summaryEl.textContent = "No preferences yet.";
    +    const empty = document.createElement("div");
    +    empty.className = "prefs-overlay-empty";
    +    empty.textContent = "No preferences saved yet.";
    +    details.appendChild(empty);
    +    return;
    +  }
    +  const servings = Number.isFinite(prefs.servings) ? prefs.servings : "\u2014";
    +  const meals = Number.isFinite(prefs.meals_per_day) ? prefs.meals_per_day : "\u2014";
    +  const days = Number.isFinite(prefs.plan_days) ? prefs.plan_days : "\u2014";
    +  summaryEl.textContent = `${servings} servings \xB7 ${days} days \xB7 ${meals} meals/day`;
    +  const sections = [
    +    { title: "Allergies", items: Array.isArray(prefs.allergies) ? prefs.allergies : [] },
    +    { title: "Dislikes", items: Array.isArray(prefs.dislikes) ? prefs.dislikes : [] },
    +    { title: "Likes", items: Array.isArray(prefs.cuisine_likes) ? prefs.cuisine_likes : [] }
    +  ];
    +  sections.forEach((section) => {
    +    const sectionEl = document.createElement("div");
    +    sectionEl.className = "prefs-overlay-section inventory-ghost-section";
    +    const titleEl = document.createElement("div");
    +    titleEl.className = "prefs-overlay-title inventory-ghost-title";
    +    titleEl.textContent = section.title;
    +    sectionEl.appendChild(titleEl);
    +    const list = document.createElement("ul");
    +    list.className = "prefs-overlay-list";
    +    if (!section.items.length) {
    +      const li = document.createElement("li");
    +      li.className = "inventory-empty";
    +      li.textContent = "None yet.";
    +      list.appendChild(li);
    +    } else {
    +      section.items.forEach((item) => {
    +        const li = document.createElement("li");
    +        li.textContent = item;
    +        list.appendChild(li);
    +      });
    +    }
    +    sectionEl.appendChild(list);
    +    details.appendChild(sectionEl);
    +  });
    +  if (prefs.notes) {
    +    const notesSection = document.createElement("div");
    +    notesSection.className = "prefs-overlay-section";
    +    const notesTitle = document.createElement("div");
    +    notesTitle.className = "prefs-overlay-title";
    +    notesTitle.textContent = "Notes";
    +    const notesBody = document.createElement("div");
    +    notesBody.className = "prefs-overlay-notes";
    +    notesBody.textContent = prefs.notes;
    +    notesSection.appendChild(notesTitle);
    +    notesSection.appendChild(notesBody);
    +    details.appendChild(notesSection);
    +  }
     }
     async function refreshPrefsOverlay(force = false) {
    -    if (!prefsOverlay)
    -        return;
    -    if (prefsOverlayLoading && !force)
    -        return;
    -    prefsOverlayLoading = true;
    -    setPrefsOverlayStatus("Loading...");
    -    try {
    -        const resp = await doGet("/prefs");
    -        if (resp.status === 401) {
    -            setPrefsOverlayStatus("Unauthorized (set token in Dev Panel)");
    -            renderPrefsOverlay(null);
    -            prefsOverlayHasLoaded = true;
    -            return;
    -        }
    -        const payload = resp.json;
    -        const hasData = payload && typeof payload === "object" && payload !== null && (typeof payload.servings === "number" || Array.isArray(payload.allergies));
    -        renderPrefsOverlay(hasData ? payload : null);
    -        setPrefsOverlayStatus(hasData ? "Read-only snapshot" : "No preferences yet.");
    -        prefsOverlayHasLoaded = true;
    -    }
    -    catch (err) {
    -        setPrefsOverlayStatus("Network error. Try refresh.");
    -        renderPrefsOverlay(null);
    -        console.error(err);
    -    }
    -    finally {
    -        prefsOverlayLoading = false;
    -    }
    +  if (!prefsOverlay) return;
    +  if (prefsOverlayLoading && !force) return;
    +  prefsOverlayLoading = true;
    +  setPrefsOverlayStatus("Loading...");
    +  try {
    +    const resp = await doGet("/prefs");
    +    if (resp.status === 401) {
    +      setPrefsOverlayStatus("Unauthorized (set token in Dev Panel)");
    +      renderPrefsOverlay(null);
    +      prefsOverlayHasLoaded = true;
    +      return;
    +    }
    +    const payload = resp.json;
    +    const hasData = payload && typeof payload === "object" && payload !== null && (typeof payload.servings === "number" || Array.isArray(payload.allergies));
    +    renderPrefsOverlay(hasData ? payload : null);
    +    setPrefsOverlayStatus(hasData ? "Read-only snapshot" : "No preferences yet.");
    +    prefsOverlayHasLoaded = true;
    +  } catch (err) {
    +    setPrefsOverlayStatus("Network error. Try refresh.");
    +    renderPrefsOverlay(null);
    +    console.error(err);
    +  } finally {
    +    prefsOverlayLoading = false;
    +  }
     }
     function updatePrefsOverlayVisibility() {
    -    if (!prefsOverlay)
    -        return;
    -    const visible = currentFlowKey === "prefs" && !!state.onboarded;
    -    prefsOverlay.classList.toggle("hidden", !visible);
    -    prefsOverlay.style.display = visible ? "flex" : "none";
    -    if (visible && (!prefsOverlayHasLoaded || !(prefsOverlayDetails === null || prefsOverlayDetails === void 0 ? void 0 : prefsOverlayDetails.childElementCount))) {
    -        refreshPrefsOverlay();
    -    }
    +  if (!prefsOverlay) return;
    +  const visible = currentFlowKey === "prefs" && !!state.onboarded;
    +  prefsOverlay.classList.toggle("hidden", !visible);
    +  prefsOverlay.style.display = visible ? "flex" : "none";
    +  if (visible && (!prefsOverlayHasLoaded || !prefsOverlayDetails?.childElementCount)) {
    +    refreshPrefsOverlay();
    +  }
     }
     function setupPrefsOverlay() {
    -    const shell = document.getElementById("duet-shell");
    -    const stage = shell === null || shell === void 0 ? void 0 : shell.querySelector(".duet-stage");
    -    if (!shell || !stage || document.getElementById("prefs-ghost"))
    -        return;
    -    const overlay = document.createElement("div");
    -    overlay.id = "prefs-ghost";
    -    overlay.className = "inventory-ghost prefs-overlay hidden";
    -    overlay.style.display = "none";
    -    overlay.style.pointerEvents = "none";
    -    overlay.style.zIndex = "1";
    -    overlay.style.flexDirection = "column";
    -    overlay.style.justifyContent = "center";
    -    overlay.style.alignItems = "center";
    -    overlay.style.gap = "14px";
    -    overlay.style.position = "absolute";
    -    overlay.style.inset = "10px";
    -    overlay.style.width = "calc(100% - 20px)";
    -    overlay.style.height = "calc(100% - 20px)";
    -    const panel = document.createElement("div");
    -    panel.style.display = "grid";
    -    panel.style.pointerEvents = "auto";
    -    panel.style.gap = "12px";
    -    panel.style.width = "100%";
    -    panel.style.maxWidth = "520px";
    -    panel.style.margin = "0 auto";
    -    const header = document.createElement("div");
    -    header.className = "inventory-ghost-header";
    -    const title = document.createElement("span");
    -    title.textContent = "Preferences";
    -    const refresh = document.createElement("button");
    -    refresh.type = "button";
    -    refresh.className = "ghost-refresh";
    -    refresh.textContent = "Refresh";
    -    refresh.addEventListener("click", () => refreshPrefsOverlay(true));
    -    header.appendChild(title);
    -    header.appendChild(refresh);
    -    const status = document.createElement("div");
    -    status.id = "prefs-ghost-status";
    -    status.className = "inventory-ghost-status";
    -    status.textContent = "Select Preferences to load.";
    -    const summary = document.createElement("div");
    -    summary.id = "prefs-ghost-summary";
    -    summary.className = "prefs-ghost-summary";
    -    summary.textContent = "No preferences yet.";
    -    const details = document.createElement("div");
    -    details.className = "prefs-ghost-details";
    -    details.style.display = "grid";
    -    details.style.gap = "10px";
    -    details.style.width = "100%";
    -    panel.appendChild(header);
    -    panel.appendChild(status);
    -    panel.appendChild(summary);
    -    panel.appendChild(details);
    -    overlay.appendChild(panel);
    -    stage.appendChild(overlay);
    -    prefsOverlay = overlay;
    -    prefsOverlayStatusEl = status;
    -    prefsOverlaySummaryEl = summary;
    -    prefsOverlayDetails = details;
    +  const shell = document.getElementById("duet-shell");
    +  const stage = shell?.querySelector(".duet-stage");
    +  if (!shell || !stage || document.getElementById("prefs-ghost")) return;
    +  const overlay = document.createElement("div");
    +  overlay.id = "prefs-ghost";
    +  overlay.className = "inventory-ghost prefs-overlay hidden";
    +  overlay.style.display = "none";
    +  overlay.style.pointerEvents = "none";
    +  overlay.style.zIndex = "1";
    +  overlay.style.flexDirection = "column";
    +  overlay.style.justifyContent = "center";
    +  overlay.style.alignItems = "center";
    +  overlay.style.gap = "14px";
    +  overlay.style.position = "absolute";
    +  overlay.style.inset = "10px";
    +  overlay.style.width = "calc(100% - 20px)";
    +  overlay.style.height = "calc(100% - 20px)";
    +  const panel = document.createElement("div");
    +  panel.style.display = "grid";
    +  panel.style.pointerEvents = "auto";
    +  panel.style.gap = "12px";
    +  panel.style.width = "100%";
    +  panel.style.maxWidth = "520px";
    +  panel.style.margin = "0 auto";
    +  const header = document.createElement("div");
    +  header.className = "inventory-ghost-header";
    +  const title = document.createElement("span");
    +  title.textContent = "Preferences";
    +  const refresh = document.createElement("button");
    +  refresh.type = "button";
    +  refresh.className = "ghost-refresh";
    +  refresh.textContent = "Refresh";
    +  refresh.addEventListener("click", () => refreshPrefsOverlay(true));
    +  header.appendChild(title);
    +  header.appendChild(refresh);
    +  const status = document.createElement("div");
    +  status.id = "prefs-ghost-status";
    +  status.className = "inventory-ghost-status";
    +  status.textContent = "Select Preferences to load.";
    +  const summary = document.createElement("div");
    +  summary.id = "prefs-ghost-summary";
    +  summary.className = "prefs-ghost-summary";
    +  summary.textContent = "No preferences yet.";
    +  const details = document.createElement("div");
    +  details.className = "prefs-ghost-details";
    +  details.style.display = "grid";
    +  details.style.gap = "10px";
    +  details.style.width = "100%";
    +  panel.appendChild(header);
    +  panel.appendChild(status);
    +  panel.appendChild(summary);
    +  panel.appendChild(details);
    +  overlay.appendChild(panel);
    +  stage.appendChild(overlay);
    +  prefsOverlay = overlay;
    +  prefsOverlayStatusEl = status;
    +  prefsOverlaySummaryEl = summary;
    +  prefsOverlayDetails = details;
     }
     async function doGet(path) {
    -    const res = await fetch(path, { headers: headers() });
    -    return { status: res.status, json: await res.json().catch(() => null) };
    +  const res = await fetch(path, { headers: headers() });
    +  return { status: res.status, json: await res.json().catch(() => null) };
     }
     async function doPost(path, body) {
    -    const res = await fetch(path, { method: "POST", headers: headers(), body: JSON.stringify(body) });
    -    return { status: res.status, json: await res.json().catch(() => null) };
    -}
    -function shellOnlyDuetReply(userText) {
    -    var _a;
    -    const thread = (_a = duetState.threadId) !== null && _a !== void 0 ? _a : crypto.randomUUID();
    -    duetState.threadId = thread;
    -    updateThreadLabel();
    -    const replyText = "(Shell) Phase 7.1: backend wiring lands in Phase 7.4.";
    -    const resp = { status: 200, json: { reply_text: replyText, confirmation_required: false, thread_id: thread } };
    -    state.chatReply = resp;
    -    setText("chat-reply", resp);
    -    addHistory("assistant", replyText);
    -    renderDuetHistory();
    -    updateDuetBubbles();
    -    setDuetStatus("Shell-only: local echo shown; backend wiring arrives in Phase 7.4.");
    -    return resp;
    +  const res = await fetch(path, { method: "POST", headers: headers(), body: JSON.stringify(body) });
    +  return { status: res.status, json: await res.json().catch(() => null) };
     }
     async function sendAsk(message, opts) {
    -    var _a, _b;
    -    const ensureThread = () => {
    -        if (!duetState.threadId) {
    -            duetState.threadId = crypto.randomUUID();
    -            updateThreadLabel();
    -        }
    -        return duetState.threadId;
    -    };
    -    const normalizedMessage = message.trim();
    -    const flowLabel = opts === null || opts === void 0 ? void 0 : opts.flowLabel;
    -    const displayText = flowLabel ? `[${flowLabel}] ${normalizedMessage}` : normalizedMessage;
    -    const isNormalChat = isNormalChatFlow();
    -    if (isNormalChat) {
    -        setUserBubbleEllipsis(true);
    -        incrementHistoryBadge();
    -    }
    -    const userIndex = addHistory("user", displayText);
    -    const thinkingIndex = addHistory("assistant", "...");
    -    const command = state.proposalId ? detectProposalCommand(normalizedMessage) : null;
    -    if (command) {
    -        setDuetStatus(command === "confirm" ? "Applying proposal confirmation..." : "Cancelling proposal...");
    -        setComposerBusy(true);
    -        try {
    -            await submitProposalDecision(command === "confirm", thinkingIndex);
    -        }
    -        finally {
    -            setComposerBusy(false);
    -        }
    -        return { userIndex, thinkingIndex };
    -    }
    -    setDuetStatus("Contacting backend...");
    +  const ensureThread = () => {
    +    if (!duetState.threadId) {
    +      duetState.threadId = crypto.randomUUID();
    +      updateThreadLabel();
    +    }
    +    return duetState.threadId;
    +  };
    +  const normalizedMessage = message.trim();
    +  const flowLabel = opts?.flowLabel;
    +  const displayText = flowLabel ? `[${flowLabel}] ${normalizedMessage}` : normalizedMessage;
    +  const isNormalChat = isNormalChatFlow();
    +  if (isNormalChat) {
    +    setUserBubbleEllipsis(true);
    +    incrementHistoryBadge();
    +  }
    +  const userIndex = addHistory("user", displayText);
    +  const thinkingIndex = addHistory("assistant", "...");
    +  const command = state.proposalId ? detectProposalCommand(normalizedMessage) : null;
    +  if (command) {
    +    setDuetStatus(command === "confirm" ? "Applying proposal confirmation..." : "Cancelling proposal...");
         setComposerBusy(true);
         try {
    -        const threadId = ensureThread();
    -        const endpoint = currentFlowKey === "inventory" ? "/chat/inventory" : "/chat";
    -        const mode = currentFlowKey === "inventory" || currentFlowKey === "prefs" ? "fill" : currentModeLower();
    -        const res = await fetch(endpoint, {
    -            method: "POST",
    -            headers: headers(),
    -            body: JSON.stringify({
    -                mode,
    -                message,
    -                include_user_library: true,
    -                thread_id: threadId,
    -            }),
    -        });
    -        const json = await res.json().catch(() => null);
    -        if (!res.ok || !json || typeof json.reply_text !== "string") {
    -            throw new Error((json === null || json === void 0 ? void 0 : json.message) || `ASK failed (status ${res.status})`);
    -        }
    -        lastResponseRequiresConfirmation = !!json.confirmation_required;
    -        setModeFromResponse(json);
    -        const proposalSummary = formatProposalSummary(json);
    -        const replyText = json.reply_text;
    -        const replyBase = proposalSummary ? (_a = stripProposalPrefix(replyText)) !== null && _a !== void 0 ? _a : replyText : replyText;
    -        const assistantText = proposalSummary ? `${proposalSummary}\n\n${replyBase}` : replyBase;
    -        updateHistory(thinkingIndex, assistantText);
    -        state.proposalId = (_b = json.proposal_id) !== null && _b !== void 0 ? _b : null;
    -        state.proposedActions = Array.isArray(json.proposed_actions) ? json.proposed_actions : [];
    -        renderProposal();
    -        if (opts === null || opts === void 0 ? void 0 : opts.updateChatPanel) {
    -            setText("chat-reply", { status: res.status, json });
    -        }
    -        setDuetStatus("Reply received.");
    +      await submitProposalDecision(command === "confirm", thinkingIndex);
    +    } finally {
    +      setComposerBusy(false);
         }
    -    catch (err) {
    -        updateHistory(thinkingIndex, "Network error. Try again.");
    -        if (opts === null || opts === void 0 ? void 0 : opts.updateChatPanel) {
    -            setChatError("Network error. Try again.");
    -        }
    -        console.error(err);
    +    return { userIndex, thinkingIndex };
    +  }
    +  setDuetStatus("Contacting backend...");
    +  setComposerBusy(true);
    +  try {
    +    const threadId = ensureThread();
    +    const endpoint = currentFlowKey === "inventory" ? "/chat/inventory" : "/chat";
    +    const mode = currentFlowKey === "inventory" || currentFlowKey === "prefs" ? "fill" : currentModeLower();
    +    const res = await fetch(endpoint, {
    +      method: "POST",
    +      headers: headers(),
    +      body: JSON.stringify({
    +        mode,
    +        message,
    +        include_user_library: true,
    +        thread_id: threadId
    +      })
    +    });
    +    const json = await res.json().catch(() => null);
    +    if (!res.ok || !json || typeof json.reply_text !== "string") {
    +      throw new Error(json?.message || `ASK failed (status ${res.status})`);
    +    }
    +    lastResponseRequiresConfirmation = !!json.confirmation_required;
    +    setModeFromResponse(json);
    +    const proposalSummary = formatProposalSummary(json);
    +    const replyText = json.reply_text;
    +    const replyBase = proposalSummary ? stripProposalPrefix(replyText) ?? replyText : replyText;
    +    const assistantText = proposalSummary ? `${proposalSummary}
    +
    +${replyBase}` : replyBase;
    +    updateHistory(thinkingIndex, assistantText);
    +    state.proposalId = json.proposal_id ?? null;
    +    state.proposedActions = Array.isArray(json.proposed_actions) ? json.proposed_actions : [];
    +    renderProposal();
    +    if (opts?.updateChatPanel) {
    +      setText("chat-reply", { status: res.status, json });
         }
    -    finally {
    -        setComposerBusy(false);
    +    setDuetStatus("Reply received.");
    +  } catch (err) {
    +    updateHistory(thinkingIndex, "Network error. Try again.");
    +    if (opts?.updateChatPanel) {
    +      setChatError("Network error. Try again.");
         }
    -    return { userIndex, thinkingIndex };
    +    console.error(err);
    +  } finally {
    +    setComposerBusy(false);
    +  }
    +  return { userIndex, thinkingIndex };
     }
     function setComposerBusy(busy) {
    -    composerBusy = busy;
    -    const input = document.getElementById("duet-input");
    -    const sendBtn = document.getElementById("duet-send");
    -    if (sendBtn)
    -        sendBtn.disabled = busy || !!(input && input.value.trim().length === 0);
    -    if (input)
    -        input.readOnly = busy;
    +  composerBusy = busy;
    +  const input = document.getElementById("duet-input");
    +  const sendBtn = document.getElementById("duet-send");
    +  if (sendBtn) sendBtn.disabled = busy || !!(input && input.value.trim().length === 0);
    +  if (input) input.readOnly = busy;
     }
     async function silentGreetOnce() {
    -    var _a;
    -    if (!((_a = state.token) === null || _a === void 0 ? void 0 : _a.trim()))
    -        return;
    -    const key = "lc_silent_greet_done";
    -    if (sessionStorage.getItem(key) === "1")
    -        return;
    -    sessionStorage.setItem(key, "1");
    -    try {
    -        const greetMessage = state.onboarded === false ? "I'm new here" : "hello";
    -        const res = await doPost("/chat", {
    -            mode: "ask",
    -            message: greetMessage,
    -            include_user_library: true,
    -        });
    -        const json = res.json;
    -        if (res.status === 200 && json && typeof json.reply_text === "string") {
    -            setModeFromResponse(json);
    -            duetState.history.push({ role: "assistant", text: json.reply_text });
    -            renderDuetHistory();
    -            updateDuetBubbles();
    -        }
    -    }
    -    catch (_err) {
    -        // Silent failure by design
    +  if (!state.token?.trim()) return;
    +  const key = "lc_silent_greet_done";
    +  if (sessionStorage.getItem(key) === "1") return;
    +  sessionStorage.setItem(key, "1");
    +  try {
    +    const greetMessage = state.onboarded === false ? "I'm new here" : "hello";
    +    const res = await doPost("/chat", {
    +      mode: "ask",
    +      message: greetMessage,
    +      include_user_library: true
    +    });
    +    const json = res.json;
    +    if (res.status === 200 && json && typeof json.reply_text === "string") {
    +      setModeFromResponse(json);
    +      duetState.history.push({ role: "assistant", text: json.reply_text });
    +      renderDuetHistory();
    +      updateDuetBubbles();
         }
    +  } catch (_err) {
    +  }
     }
     function wire() {
    -    var _a, _b, _c, _d, _e, _f, _g, _h;
    -    enforceViewportLock();
    -    const jwtInput = document.getElementById("jwt");
    -    (_a = document.getElementById("btn-auth")) === null || _a === void 0 ? void 0 : _a.addEventListener("click", async () => {
    -        var _a, _b, _c;
    -        state.token = jwtInput.value.trim();
    -        const rememberCheckbox = getRememberCheckbox();
    -        const rememberSelect = getRememberDurationSelect();
    -        if (state.token && (rememberCheckbox === null || rememberCheckbox === void 0 ? void 0 : rememberCheckbox.checked)) {
    -            const desired = Number((_a = rememberSelect === null || rememberSelect === void 0 ? void 0 : rememberSelect.value) !== null && _a !== void 0 ? _a : DEV_JWT_DEFAULT_TTL_MS);
    -            const ttl = Number.isFinite(desired) && desired > 0 ? desired : DEV_JWT_DEFAULT_TTL_MS;
    -            saveRememberedJwt(state.token, ttl);
    -        }
    -        else {
    -            clearRememberedJwt();
    -        }
    -        clearProposal();
    -        const result = await doGet("/auth/me");
    -        setText("auth-out", result);
    -        state.onboarded = !!((_b = result.json) === null || _b === void 0 ? void 0 : _b.onboarded);
    -        state.inventoryOnboarded = !!((_c = result.json) === null || _c === void 0 ? void 0 : _c.inventory_onboarded);
    -        renderOnboardMenuButtons();
    -        updatePrefsOverlayVisibility();
    -        updateInventoryOverlayVisibility();
    -        await silentGreetOnce();
    -        inventoryHasLoaded = false;
    -        if (currentFlowKey === "inventory") {
    -            refreshInventoryOverlay(true);
    -        }
    -    });
    -    (_b = document.getElementById("btn-chat")) === null || _b === void 0 ? void 0 : _b.addEventListener("click", async () => {
    -        var _a;
    -        const msg = document.getElementById("chat-input").value;
    -        clearProposal();
    -        setChatError("");
    -        if (msg === null || msg === void 0 ? void 0 : msg.trim()) {
    -            const flow = (_a = flowOptions.find((f) => f.key === currentFlowKey)) !== null && _a !== void 0 ? _a : flowOptions[0];
    -            await sendAsk(msg.trim(), { flowLabel: flow.label, updateChatPanel: true });
    -        }
    -        else {
    -            setChatError("Enter a message to send.");
    -        }
    -    });
    -    (_c = document.getElementById("btn-prefs-get")) === null || _c === void 0 ? void 0 : _c.addEventListener("click", async () => {
    -        const resp = await doGet("/prefs");
    -        setText("prefs-out", resp);
    -    });
    -    (_d = document.getElementById("btn-prefs-put")) === null || _d === void 0 ? void 0 : _d.addEventListener("click", async () => {
    -        const servings = Number(document.getElementById("prefs-servings").value);
    -        const meals = Number(document.getElementById("prefs-meals").value);
    -        const resp = await fetch("/prefs", {
    -            method: "PUT",
    -            headers: headers(),
    -            body: JSON.stringify({ prefs: { servings, meals_per_day: meals } }),
    -        });
    -        const json = await resp.json().catch(() => null);
    -        setText("prefs-out", { status: resp.status, json });
    -    });
    -    (_e = document.getElementById("btn-plan-gen")) === null || _e === void 0 ? void 0 : _e.addEventListener("click", async () => {
    -        const resp = await doPost("/mealplan/generate", { days: 2, meals_per_day: 3 });
    -        state.lastPlan = resp.json;
    -        setText("plan-out", resp);
    -    });
    -    (_f = document.getElementById("btn-shopping")) === null || _f === void 0 ? void 0 : _f.addEventListener("click", async () => {
    -        if (!state.lastPlan) {
    -            setText("shopping-out", "No plan yet. Generate a plan first.");
    -            return;
    -        }
    -        const resp = await doPost("/shopping/diff", { plan: state.lastPlan });
    -        setText("shopping-out", resp);
    -    });
    -    (_g = document.getElementById("btn-confirm")) === null || _g === void 0 ? void 0 : _g.addEventListener("click", async () => {
    -        if (!state.proposalId)
    -            return;
    -        setChatError("");
    -        setChatError("Shell-only: confirmations land in Phase 7.4.");
    -        setDuetStatus("Shell-only: confirmations deferred to Phase 7.4.");
    -        setText("chat-reply", { status: 0, json: { message: "Shell-only confirmation stub (Phase 7.4 wires backend)" } });
    -        clearProposal();
    -    });
    -    (_h = document.getElementById("btn-cancel")) === null || _h === void 0 ? void 0 : _h.addEventListener("click", async () => {
    -        if (!state.proposalId)
    -            return;
    -        setChatError("");
    -        setChatError("Shell-only: decline stubbed until Phase 7.4.");
    -        setDuetStatus("Shell-only: confirmations deferred to Phase 7.4.");
    -        setText("chat-reply", { status: 0, json: { message: "Shell-only decline stub (Phase 7.4 wires backend)" } });
    -        clearProposal();
    -    });
    -    setupFlowChips();
    -    // setupDock();
    -    bindResizeForHistoryOffset();
    -    setupInventoryGhostOverlay();
    -    setupPrefsOverlay();
    -    setupDevPanel();
    -    applyRememberedJwtInput(jwtInput);
    -    wireDuetComposer();
    -    wireFloatingComposerTrigger(document.querySelector(".duet-stage"));
    -    setupHistoryDrawerUi();
    -    wireHistoryHotkeys();
    -    bindOnboardingLongPress();
    -    updateInventoryOverlayVisibility();
    +  enforceViewportLock();
    +  const jwtInput = document.getElementById("jwt");
    +  document.getElementById("btn-auth")?.addEventListener("click", async () => {
    +    state.token = jwtInput.value.trim();
    +    const rememberCheckbox = getRememberCheckbox();
    +    const rememberSelect = getRememberDurationSelect();
    +    if (state.token && rememberCheckbox?.checked) {
    +      const desired = Number(rememberSelect?.value ?? DEV_JWT_DEFAULT_TTL_MS);
    +      const ttl = Number.isFinite(desired) && desired > 0 ? desired : DEV_JWT_DEFAULT_TTL_MS;
    +      saveRememberedJwt(state.token, ttl);
    +    } else {
    +      clearRememberedJwt();
    +    }
    +    clearProposal();
    +    const result = await doGet("/auth/me");
    +    setText("auth-out", result);
    +    state.onboarded = !!result.json?.onboarded;
    +    state.inventoryOnboarded = !!result.json?.inventory_onboarded;
    +    renderOnboardMenuButtons();
         updatePrefsOverlayVisibility();
    -    applyDrawerProgress(duetState.drawerOpen ? 1 : 0, { commit: true });
    -    renderDuetHistory();
    -    updateDuetBubbles();
    -    updateThreadLabel();
    -    applyDrawerProgress(0, { commit: true });
    -    elevateDuetBubbles();
    -    updateFlowStatusText();
    +    updateInventoryOverlayVisibility();
    +    await silentGreetOnce();
    +    inventoryHasLoaded = false;
    +    if (currentFlowKey === "inventory") {
    +      refreshInventoryOverlay(true);
    +    }
    +  });
    +  document.getElementById("btn-chat")?.addEventListener("click", async () => {
    +    const msg = document.getElementById("chat-input").value;
    +    clearProposal();
    +    setChatError("");
    +    if (msg?.trim()) {
    +      const flow = flowOptions.find((f) => f.key === currentFlowKey) ?? flowOptions[0];
    +      await sendAsk(msg.trim(), { flowLabel: flow.label, updateChatPanel: true });
    +    } else {
    +      setChatError("Enter a message to send.");
    +    }
    +  });
    +  document.getElementById("btn-prefs-get")?.addEventListener("click", async () => {
    +    const resp = await doGet("/prefs");
    +    setText("prefs-out", resp);
    +  });
    +  document.getElementById("btn-prefs-put")?.addEventListener("click", async () => {
    +    const servings = Number(document.getElementById("prefs-servings").value);
    +    const meals = Number(document.getElementById("prefs-meals").value);
    +    const resp = await fetch("/prefs", {
    +      method: "PUT",
    +      headers: headers(),
    +      body: JSON.stringify({ prefs: { servings, meals_per_day: meals } })
    +    });
    +    const json = await resp.json().catch(() => null);
    +    setText("prefs-out", { status: resp.status, json });
    +  });
    +  document.getElementById("btn-plan-gen")?.addEventListener("click", async () => {
    +    const resp = await doPost("/mealplan/generate", { days: 2, meals_per_day: 3 });
    +    state.lastPlan = resp.json;
    +    setText("plan-out", resp);
    +  });
    +  document.getElementById("btn-shopping")?.addEventListener("click", async () => {
    +    if (!state.lastPlan) {
    +      setText("shopping-out", "No plan yet. Generate a plan first.");
    +      return;
    +    }
    +    const resp = await doPost("/shopping/diff", { plan: state.lastPlan });
    +    setText("shopping-out", resp);
    +  });
    +  document.getElementById("btn-confirm")?.addEventListener("click", async () => {
    +    if (!state.proposalId) return;
    +    setChatError("");
    +    setChatError("Shell-only: confirmations land in Phase 7.4.");
    +    setDuetStatus("Shell-only: confirmations deferred to Phase 7.4.");
    +    setText("chat-reply", { status: 0, json: { message: "Shell-only confirmation stub (Phase 7.4 wires backend)" } });
    +    clearProposal();
    +  });
    +  document.getElementById("btn-cancel")?.addEventListener("click", async () => {
    +    if (!state.proposalId) return;
    +    setChatError("");
    +    setChatError("Shell-only: decline stubbed until Phase 7.4.");
    +    setDuetStatus("Shell-only: confirmations deferred to Phase 7.4.");
    +    setText("chat-reply", { status: 0, json: { message: "Shell-only decline stub (Phase 7.4 wires backend)" } });
    +    clearProposal();
    +  });
    +  setupFlowChips();
    +  bindResizeForHistoryOffset();
    +  setupInventoryGhostOverlay();
    +  setupPrefsOverlay();
    +  setupDevPanel();
    +  applyRememberedJwtInput(jwtInput);
    +  wireDuetComposer();
    +  wireFloatingComposerTrigger(document.querySelector(".duet-stage"));
    +  setupHistoryDrawerUi();
    +  wireHistoryHotkeys();
    +  bindOnboardingLongPress();
    +  updateInventoryOverlayVisibility();
    +  updatePrefsOverlayVisibility();
    +  applyDrawerProgress(duetState.drawerOpen ? 1 : 0, { commit: true });
    +  renderDuetHistory();
    +  updateDuetBubbles();
    +  updateThreadLabel();
    +  applyDrawerProgress(0, { commit: true });
    +  elevateDuetBubbles();
    +  updateFlowStatusText();
     }
     document.addEventListener("DOMContentLoaded", wire);
     function wireDuetComposer() {
    -    const input = document.getElementById("duet-input");
    -    const sendBtn = document.getElementById("duet-send");
    -    const micBtn = document.getElementById("duet-mic");
    -    if (!input || !sendBtn)
    -        return;
    +  const input = document.getElementById("duet-input");
    +  const sendBtn = document.getElementById("duet-send");
    +  const micBtn = document.getElementById("duet-mic");
    +  if (!input || !sendBtn) return;
    +  hideFloatingComposer();
    +  const syncButtons = () => {
    +    sendBtn.disabled = composerBusy || input.value.trim().length === 0;
    +  };
    +  const send = () => {
    +    const text = input.value.trim();
    +    if (!text || composerBusy) return;
    +    setChatError("");
    +    const flow = flowOptions.find((f) => f.key === currentFlowKey) ?? flowOptions[0];
    +    setDuetStatus("Sending to backend...");
    +    syncButtons();
    +    const pendingCommand = state.proposalId ? detectProposalCommand(text) : null;
    +    if (!pendingCommand) {
    +      clearProposal();
    +    }
    +    sendAsk(text, { flowLabel: flow.label });
    +    input.value = "";
    +    syncButtons();
         hideFloatingComposer();
    -    const syncButtons = () => {
    -        sendBtn.disabled = composerBusy || input.value.trim().length === 0;
    -    };
    -    const send = () => {
    -        var _a;
    -        const text = input.value.trim();
    -        if (!text || composerBusy)
    -            return;
    -        setChatError("");
    -        const flow = (_a = flowOptions.find((f) => f.key === currentFlowKey)) !== null && _a !== void 0 ? _a : flowOptions[0];
    -        setDuetStatus("Sending to backend...");
    -        syncButtons();
    -        const pendingCommand = state.proposalId ? detectProposalCommand(text) : null;
    -        if (!pendingCommand) {
    -            clearProposal();
    -        }
    -        sendAsk(text, { flowLabel: flow.label });
    -        input.value = "";
    -        syncButtons();
    -        hideFloatingComposer();
    -    };
    -    input.addEventListener("input", syncButtons);
    -    sendBtn.addEventListener("click", send);
    -    input.addEventListener("keydown", (ev) => {
    -        if (ev.key === "Enter" && !ev.shiftKey) {
    -            ev.preventDefault();
    -            send();
    -        }
    -    });
    -    micBtn === null || micBtn === void 0 ? void 0 : micBtn.addEventListener("click", () => {
    -        setDuetStatus("Voice uses client-side transcription; mic will feed text here.", false);
    -        input.focus();
    -    });
    -    setComposerPlaceholder();
    +  };
    +  input.addEventListener("input", syncButtons);
    +  sendBtn.addEventListener("click", send);
    +  input.addEventListener("keydown", (ev) => {
    +    if (ev.key === "Enter" && !ev.shiftKey) {
    +      ev.preventDefault();
    +      send();
    +    }
    +  });
    +  micBtn?.addEventListener("click", () => {
    +    setDuetStatus("Voice uses client-side transcription; mic will feed text here.", false);
    +    input.focus();
    +  });
    +  setComposerPlaceholder();
     }
     function showFloatingComposer() {
    -    const composer = document.getElementById("duet-composer");
    -    if (!composer || composerVisible)
    -        return;
    -    composer.classList.add("visible");
    -    composer.setAttribute("aria-hidden", "false");
    -    composerVisible = true;
    -    syncFlowMenuVisibility();
    -    setFlowMenuOpen(false);
    -    const input = document.getElementById("duet-input");
    -    setComposerPlaceholder();
    -    window.requestAnimationFrame(() => input === null || input === void 0 ? void 0 : input.focus());
    +  const composer = document.getElementById("duet-composer");
    +  if (!composer || composerVisible) return;
    +  composer.classList.add("visible");
    +  composer.setAttribute("aria-hidden", "false");
    +  composerVisible = true;
    +  syncFlowMenuVisibility();
    +  setFlowMenuOpen(false);
    +  const input = document.getElementById("duet-input");
    +  setComposerPlaceholder();
    +  window.requestAnimationFrame(() => input?.focus());
     }
     function hideFloatingComposer() {
    -    const composer = document.getElementById("duet-composer");
    -    if (!composer)
    -        return;
    -    composer.classList.remove("visible");
    -    composer.setAttribute("aria-hidden", "true");
    -    composerVisible = false;
    -    syncFlowMenuVisibility();
    -    const input = document.getElementById("duet-input");
    -    input === null || input === void 0 ? void 0 : input.blur();
    +  const composer = document.getElementById("duet-composer");
    +  if (!composer) return;
    +  composer.classList.remove("visible");
    +  composer.setAttribute("aria-hidden", "true");
    +  composerVisible = false;
    +  syncFlowMenuVisibility();
    +  const input = document.getElementById("duet-input");
    +  input?.blur();
     }
     function wireFloatingComposerTrigger(stage) {
    -    if (!stage)
    -        return;
    -    stage.addEventListener("pointerdown", () => {
    -        stageTripleTapCount += 1;
    -        if (stageTripleTapResetTimer !== null) {
    -            window.clearTimeout(stageTripleTapResetTimer);
    -        }
    -        stageTripleTapResetTimer = window.setTimeout(() => {
    -            stageTripleTapCount = 0;
    -            stageTripleTapResetTimer = null;
    -        }, COMPOSER_TRIPLE_TAP_WINDOW_MS);
    -        if (stageTripleTapCount < 3) {
    -            return;
    -        }
    -        stageTripleTapCount = 0;
    -        if (stageTripleTapResetTimer !== null) {
    -            window.clearTimeout(stageTripleTapResetTimer);
    -            stageTripleTapResetTimer = null;
    -        }
    -        showFloatingComposer();
    -    });
    +  if (!stage) return;
    +  stage.addEventListener("pointerdown", () => {
    +    stageTripleTapCount += 1;
    +    if (stageTripleTapResetTimer !== null) {
    +      window.clearTimeout(stageTripleTapResetTimer);
    +    }
    +    stageTripleTapResetTimer = window.setTimeout(() => {
    +      stageTripleTapCount = 0;
    +      stageTripleTapResetTimer = null;
    +    }, COMPOSER_TRIPLE_TAP_WINDOW_MS);
    +    if (stageTripleTapCount < 3) {
    +      return;
    +    }
    +    stageTripleTapCount = 0;
    +    if (stageTripleTapResetTimer !== null) {
    +      window.clearTimeout(stageTripleTapResetTimer);
    +      stageTripleTapResetTimer = null;
    +    }
    +    showFloatingComposer();
    +  });
     }
     function syncFlowMenuVisibility() {
    -    if (!flowMenuContainer)
    -        return;
    -    const trigger = document.getElementById("flow-menu-trigger");
    -    if (composerVisible) {
    -        // Show trigger as a red Ô£ò close button instead of hiding it
    -        flowMenuContainer.classList.remove("hidden");
    -        if (trigger) {
    -            trigger.classList.add("close-mode");
    -            trigger.textContent = "Ô£ò";
    -            trigger.setAttribute("aria-label", "Close composer");
    -        }
    -        // Hide the dropdown while in close mode
    -        if (flowMenuDropdown) {
    -            flowMenuDropdown.style.display = "none";
    -            flowMenuDropdown.classList.remove("open");
    -        }
    +  if (!flowMenuContainer) return;
    +  const trigger = document.getElementById("flow-menu-trigger");
    +  if (composerVisible) {
    +    flowMenuContainer.classList.remove("hidden");
    +    if (trigger) {
    +      trigger.classList.add("close-mode");
    +      trigger.textContent = "\u2715";
    +      trigger.setAttribute("aria-label", "Close composer");
         }
    -    else {
    -        if (trigger) {
    -            trigger.classList.remove("close-mode");
    -            trigger.textContent = "ÔÜÖ";
    -            trigger.setAttribute("aria-label", `Options (current: ${flowDisplayLabel(currentFlowKey)})`);
    -        }
    +    if (flowMenuDropdown) {
    +      flowMenuDropdown.style.display = "none";
    +      flowMenuDropdown.classList.remove("open");
         }
    +  } else {
    +    if (trigger) {
    +      trigger.classList.remove("close-mode");
    +      trigger.textContent = "\u2699";
    +      trigger.setAttribute("aria-label", `Options (current: ${flowDisplayLabel(currentFlowKey)})`);
    +    }
    +  }
     }
     function setupFlowChips() {
    -    const shell = document.getElementById("duet-shell");
    -    const composer = document.getElementById("duet-composer");
    -    const stage = shell === null || shell === void 0 ? void 0 : shell.querySelector(".duet-stage");
    -    if (!shell || !composer)
    -        return;
    -    if (!flowMenuContainer) {
    -        flowMenuContainer = document.createElement("div");
    -        flowMenuContainer.id = "flow-chips";
    -        flowMenuContainer.className = "flow-menu";
    -    }
    -    else {
    -        flowMenuContainer.innerHTML = "";
    -        flowMenuContainer.className = "flow-menu";
    -    }
    -    const trigger = document.createElement("button");
    -    trigger.type = "button";
    -    trigger.id = "flow-menu-trigger";
    -    trigger.className = "flow-menu-toggle";
    -    trigger.setAttribute("aria-haspopup", "true");
    -    trigger.setAttribute("aria-expanded", "false");
    -    trigger.addEventListener("click", () => {
    -        if (composerVisible) {
    -            hideFloatingComposer();
    -            return;
    -        }
    -        setFlowMenuOpen(!flowMenuOpen);
    +  const shell = document.getElementById("duet-shell");
    +  const composer = document.getElementById("duet-composer");
    +  const stage = shell?.querySelector(".duet-stage");
    +  if (!shell || !composer) return;
    +  if (!flowMenuContainer) {
    +    flowMenuContainer = document.createElement("div");
    +    flowMenuContainer.id = "flow-chips";
    +    flowMenuContainer.className = "flow-menu";
    +  } else {
    +    flowMenuContainer.innerHTML = "";
    +    flowMenuContainer.className = "flow-menu";
    +  }
    +  const trigger = document.createElement("button");
    +  trigger.type = "button";
    +  trigger.id = "flow-menu-trigger";
    +  trigger.className = "flow-menu-toggle";
    +  trigger.setAttribute("aria-haspopup", "true");
    +  trigger.setAttribute("aria-expanded", "false");
    +  trigger.addEventListener("click", () => {
    +    if (composerVisible) {
    +      hideFloatingComposer();
    +      return;
    +    }
    +    setFlowMenuOpen(!flowMenuOpen);
    +  });
    +  const dropdown = document.createElement("div");
    +  dropdown.className = "flow-menu-dropdown";
    +  dropdown.setAttribute("role", "menu");
    +  dropdown.style.display = "none";
    +  dropdown.style.position = "absolute";
    +  dropdown.style.zIndex = "10";
    +  dropdown.style.top = "calc(100% + 6px)";
    +  flowMenuContainer.appendChild(trigger);
    +  flowMenuContainer.appendChild(dropdown);
    +  flowMenuButton = trigger;
    +  flowMenuDropdown = dropdown;
    +  setFlowMenuOpen(false);
    +  renderFlowMenu();
    +  const menuHost = stage ?? shell;
    +  if (flowMenuContainer && menuHost && flowMenuContainer.parentElement !== menuHost) {
    +    menuHost.appendChild(flowMenuContainer);
    +  }
    +  if (!flowMenuListenersBound) {
    +    document.addEventListener("click", (ev) => {
    +      if (!flowMenuOpen || !flowMenuContainer) return;
    +      if (ev.target instanceof Node && flowMenuContainer.contains(ev.target)) return;
    +      setFlowMenuOpen(false);
         });
    -    const dropdown = document.createElement("div");
    -    dropdown.className = "flow-menu-dropdown";
    -    dropdown.setAttribute("role", "menu");
    -    dropdown.style.display = "none";
    -    dropdown.style.position = "absolute";
    -    dropdown.style.zIndex = "10";
    -    dropdown.style.top = "calc(100% + 6px)";
    -    flowMenuContainer.appendChild(trigger);
    -    flowMenuContainer.appendChild(dropdown);
    -    flowMenuButton = trigger;
    -    flowMenuDropdown = dropdown;
    -    setFlowMenuOpen(false);
    -    renderFlowMenu();
    -    const menuHost = stage !== null && stage !== void 0 ? stage : shell;
    -    if (flowMenuContainer && menuHost && flowMenuContainer.parentElement !== menuHost) {
    -        menuHost.appendChild(flowMenuContainer);
    -    }
    -    if (!flowMenuListenersBound) {
    -        document.addEventListener("click", (ev) => {
    -            if (!flowMenuOpen || !flowMenuContainer)
    -                return;
    -            if (ev.target instanceof Node && flowMenuContainer.contains(ev.target))
    -                return;
    -            setFlowMenuOpen(false);
    -        });
    -        document.addEventListener("keydown", (ev) => {
    -            if (ev.key === "Escape" && flowMenuOpen) {
    -                setFlowMenuOpen(false);
    -            }
    -        });
    -        flowMenuListenersBound = true;
    -    }
    +    document.addEventListener("keydown", (ev) => {
    +      if (ev.key === "Escape" && flowMenuOpen) {
    +        setFlowMenuOpen(false);
    +      }
    +    });
    +    flowMenuListenersBound = true;
    +  }
     }
     function enforceViewportLock() {
    -    const html = document.documentElement;
    -    const body = document.body;
    -    const main = document.querySelector("main.container");
    -    const shell = document.getElementById("duet-shell");
    -    const stage = shell === null || shell === void 0 ? void 0 : shell.querySelector(".duet-stage");
    -    const composer = document.getElementById("duet-composer");
    -    const trigger = document.getElementById("flow-menu-trigger");
    -    const dock = document.getElementById("duet-dock");
    -    html.style.height = "100%";
    -    html.style.overscrollBehavior = "none";
    -    html.style.maxWidth = "100vw";
    -    html.style.overflow = "hidden";
    -    body.style.height = "100%";
    -    body.style.minHeight = "100dvh";
    -    body.style.maxWidth = "100vw";
    -    body.style.overflow = "hidden";
    -    body.style.overscrollBehavior = "none";
    -    if (main) {
    -        main.style.height = "100dvh";
    -        main.style.maxHeight = "100dvh";
    -        main.style.overflow = "hidden";
    -    }
    -    if (shell) {
    -        shell.style.display = "flex";
    -        shell.style.flexDirection = "column";
    -        shell.style.flex = "1 1 auto";
    -        shell.style.minHeight = "0";
    -        shell.style.height = "100%";
    -    }
    -    if (stage) {
    -        stage.style.flex = "1 1 auto";
    -        stage.style.minHeight = "0";
    -        stage.style.overflowY = "auto";
    -        stage.style.overscrollBehavior = "contain";
    -    }
    -    if (trigger) {
    -        trigger.style.flex = "0 0 auto";
    -    }
    -    if (composer) {
    -        composer.style.flex = "0 0 auto";
    -    }
    -    if (dock) {
    -        dock.style.display = "flex";
    -        dock.style.flexDirection = "column";
    -        dock.style.gap = "10px";
    -        dock.style.marginTop = "auto";
    -        dock.style.width = "100%";
    -    }
    +  const html = document.documentElement;
    +  const body = document.body;
    +  const main = document.querySelector("main.container");
    +  const shell = document.getElementById("duet-shell");
    +  const stage = shell?.querySelector(".duet-stage");
    +  const composer = document.getElementById("duet-composer");
    +  const trigger = document.getElementById("flow-menu-trigger");
    +  const dock = document.getElementById("duet-dock");
    +  html.style.height = "100%";
    +  html.style.overscrollBehavior = "none";
    +  html.style.maxWidth = "100vw";
    +  html.style.overflow = "hidden";
    +  body.style.height = "100%";
    +  body.style.minHeight = "100dvh";
    +  body.style.maxWidth = "100vw";
    +  body.style.overflow = "hidden";
    +  body.style.overscrollBehavior = "none";
    +  if (main) {
    +    main.style.height = "100dvh";
    +    main.style.maxHeight = "100dvh";
    +    main.style.overflow = "hidden";
    +  }
    +  if (shell) {
    +    shell.style.display = "flex";
    +    shell.style.flexDirection = "column";
    +    shell.style.flex = "1 1 auto";
    +    shell.style.minHeight = "0";
    +    shell.style.height = "100%";
    +  }
    +  if (stage) {
    +    stage.style.flex = "1 1 auto";
    +    stage.style.minHeight = "0";
    +    stage.style.overflowY = "auto";
    +    stage.style.overscrollBehavior = "contain";
    +  }
    +  if (trigger) {
    +    trigger.style.flex = "0 0 auto";
    +  }
    +  if (composer) {
    +    composer.style.flex = "0 0 auto";
    +  }
    +  if (dock) {
    +    dock.style.display = "flex";
    +    dock.style.flexDirection = "column";
    +    dock.style.gap = "10px";
    +    dock.style.marginTop = "auto";
    +    dock.style.width = "100%";
    +  }
     }
     function selectFlow(key) {
    -    if (!flowOptions.find((f) => f.key === key))
    -        return;
    -    currentFlowKey = key;
    -    renderFlowMenu();
    -    setFlowMenuOpen(false);
    -    setComposerPlaceholder();
    -    updateInventoryOverlayVisibility();
    -    updatePrefsOverlayVisibility();
    -    updateUserBubbleVisibility();
    -    if (currentFlowKey === "inventory") {
    -        refreshInventoryOverlay(true);
    -        if (!state.inventoryOnboarded) {
    -            addHistory("assistant", "Welcome to the inventory. This is where your cupboard, fridge, and freezer food will be displayed.\n\nFirst, you need to input the current stock you have.");
    -            userSystemHint = "Triple-tap to start chat and input inventory";
    -            setUserBubbleEllipsis(false);
    -        }
    -    }
    -    if (currentFlowKey === "prefs") {
    -        lastServerMode = "FILL";
    -        updateThreadLabel();
    -        refreshPrefsOverlay(true);
    -    }
    -    updateFlowStatusText();
    +  if (!flowOptions.find((f) => f.key === key)) return;
    +  currentFlowKey = key;
    +  renderFlowMenu();
    +  setFlowMenuOpen(false);
    +  setComposerPlaceholder();
    +  updateInventoryOverlayVisibility();
    +  updatePrefsOverlayVisibility();
    +  updateUserBubbleVisibility();
    +  if (currentFlowKey === "inventory") {
    +    refreshInventoryOverlay(true);
    +    if (!state.inventoryOnboarded) {
    +      addHistory(
    +        "assistant",
    +        "Welcome to the inventory. This is where your cupboard, fridge, and freezer food will be displayed.\n\nFirst, you need to input the current stock you have."
    +      );
    +      userSystemHint = "Triple-tap to start chat and input inventory";
    +      setUserBubbleEllipsis(false);
    +    }
    +  }
    +  if (currentFlowKey === "prefs") {
    +    lastServerMode = "FILL";
    +    updateThreadLabel();
    +    refreshPrefsOverlay(true);
    +  }
    +  if (currentFlowKey === "mealplan") {
    +    checkMealplanFirstVisit();
    +  }
    +  updateFlowStatusText();
     }
     function ensureOverlayRoot() {
    -    var _a;
    -    if (overlayRoot && overlayRoot.isConnected) {
    -        return overlayRoot;
    -    }
    -    const existing = document.getElementById(OVERLAY_ROOT_ID);
    -    if (existing) {
    -        overlayRoot = existing;
    -        return overlayRoot;
    -    }
    -    const rootHost = (_a = document.body) !== null && _a !== void 0 ? _a : document.documentElement;
    -    if (!rootHost) {
    -        throw new Error("Document root not found for overlay host");
    -    }
    -    const root = document.createElement("div");
    -    root.id = OVERLAY_ROOT_ID;
    -    root.style.position = "fixed";
    -    root.style.inset = "0";
    -    root.style.pointerEvents = "none";
    -    root.style.zIndex = OVERLAY_ROOT_Z_INDEX.toString();
    -    rootHost.appendChild(root);
    -    overlayRoot = root;
    +  if (overlayRoot && overlayRoot.isConnected) {
    +    return overlayRoot;
    +  }
    +  const existing = document.getElementById(OVERLAY_ROOT_ID);
    +  if (existing) {
    +    overlayRoot = existing;
         return overlayRoot;
    +  }
    +  const rootHost = document.body ?? document.documentElement;
    +  if (!rootHost) {
    +    throw new Error("Document root not found for overlay host");
    +  }
    +  const root = document.createElement("div");
    +  root.id = OVERLAY_ROOT_ID;
    +  root.style.position = "fixed";
    +  root.style.inset = "0";
    +  root.style.pointerEvents = "none";
    +  root.style.zIndex = OVERLAY_ROOT_Z_INDEX.toString();
    +  rootHost.appendChild(root);
    +  overlayRoot = root;
    +  return overlayRoot;
     }
     function ensureOnboardMenu() {
    -    const host = ensureOverlayRoot();
    -    if (!onboardMenu) {
    -        const menu = document.createElement("div");
    -        menu.id = "onboard-menu";
    -        menu.className = "flow-menu-dropdown";
    -        menu.style.position = "fixed";
    -        menu.style.display = "none";
    -        menu.style.zIndex = "999";
    -        host.appendChild(menu);
    -        onboardMenu = menu;
    -    }
    -    renderOnboardMenuButtons();
    -    return onboardMenu;
    +  const host = ensureOverlayRoot();
    +  if (!onboardMenu) {
    +    const menu = document.createElement("div");
    +    menu.id = "onboard-menu";
    +    menu.className = "flow-menu-dropdown";
    +    menu.style.position = "fixed";
    +    menu.style.display = "none";
    +    menu.style.zIndex = "999";
    +    host.appendChild(menu);
    +    onboardMenu = menu;
    +  }
    +  renderOnboardMenuButtons();
    +  return onboardMenu;
     }
     function renderOnboardMenuButtons() {
    -    if (!onboardMenu)
    -        return;
    -    onboardMenu.innerHTML = "";
    -    const prefsBtn = document.createElement("button");
    -    prefsBtn.type = "button";
    -    prefsBtn.className = "flow-menu-item";
    -    prefsBtn.textContent = "Preferences";
    -    prefsBtn.dataset.onboardItem = "start";
    -    prefsBtn.addEventListener("click", () => {
    -        hideOnboardMenu();
    -        startOnboarding();
    +  if (!onboardMenu) return;
    +  onboardMenu.innerHTML = "";
    +  const prefsBtn = document.createElement("button");
    +  prefsBtn.type = "button";
    +  prefsBtn.className = "flow-menu-item";
    +  prefsBtn.textContent = "Preferences";
    +  prefsBtn.dataset.onboardItem = "start";
    +  prefsBtn.addEventListener("click", () => {
    +    hideOnboardMenu();
    +    startOnboarding();
    +  });
    +  onboardMenu.appendChild(prefsBtn);
    +  if (state.onboarded) {
    +    const invBtn = document.createElement("button");
    +    invBtn.type = "button";
    +    invBtn.className = "flow-menu-item";
    +    invBtn.textContent = "Inventory";
    +    invBtn.dataset.onboardItem = "inventory";
    +    invBtn.addEventListener("click", () => {
    +      hideOnboardMenu();
    +      selectFlow("inventory");
         });
    -    onboardMenu.appendChild(prefsBtn);
    -    if (state.onboarded) {
    -        const invBtn = document.createElement("button");
    -        invBtn.type = "button";
    -        invBtn.className = "flow-menu-item";
    -        invBtn.textContent = "Inventory";
    -        invBtn.dataset.onboardItem = "inventory";
    -        invBtn.addEventListener("click", () => {
    -            hideOnboardMenu();
    -            selectFlow("inventory");
    -        });
    -        onboardMenu.appendChild(invBtn);
    -    }
    -    if (state.inventoryOnboarded) {
    -        const planBtn = document.createElement("button");
    -        planBtn.type = "button";
    -        planBtn.className = "flow-menu-item";
    -        planBtn.textContent = "Meal Plan";
    -        planBtn.dataset.onboardItem = "mealplan";
    -        planBtn.addEventListener("click", () => {
    -            hideOnboardMenu();
    -            selectFlow("mealplan");
    -        });
    -        onboardMenu.appendChild(planBtn);
    -    }
    +    onboardMenu.appendChild(invBtn);
    +  }
    +  if (state.inventoryOnboarded) {
    +    const planBtn = document.createElement("button");
    +    planBtn.type = "button";
    +    planBtn.className = "flow-menu-item";
    +    planBtn.textContent = "Meal Plan";
    +    planBtn.dataset.onboardItem = "mealplan";
    +    planBtn.addEventListener("click", () => {
    +      hideOnboardMenu();
    +      selectFlow("mealplan");
    +    });
    +    onboardMenu.appendChild(planBtn);
    +  }
     }
     function clampNumber(value, min, max) {
    -    if (max < min) {
    -        return min;
    -    }
    -    return Math.min(Math.max(value, min), max);
    +  if (max < min) {
    +    return min;
    +  }
    +  return Math.min(Math.max(value, min), max);
    +}
    +var mealplanNudged = false;
    +async function checkMealplanFirstVisit() {
    +  if (mealplanNudged) return;
    +  try {
    +    const resp = await doGet("/recipes/books");
    +    if (resp.status === 200 && resp.json?.books?.length === 0) {
    +      mealplanNudged = true;
    +      addHistory(
    +        "assistant",
    +        "Welcome to the Meal Plan! You don't have any recipes yet.\n\nTap the \u{1F4D6} button to browse and install a built-in recipe pack."
    +      );
    +      renderDuetHistory();
    +      updateDuetBubbles();
    +    } else {
    +      mealplanNudged = true;
    +    }
    +  } catch {
    +  }
    +}
    +function openPacksModal() {
    +  if (packsModalOverlay && packsModalOverlay.isConnected) {
    +    packsModalOverlay.style.display = "";
    +    packsModalOverlay.classList.add("open");
    +    const browseTab2 = packsModalOverlay.querySelector('[data-tab="browse"]');
    +    const myTab2 = packsModalOverlay.querySelector('[data-tab="my"]');
    +    browseTab2?.classList.add("active");
    +    myTab2?.classList.remove("active");
    +    loadPacksCatalogue();
    +    return;
    +  }
    +  const overlay = document.createElement("div");
    +  overlay.className = "packs-modal-overlay";
    +  overlay.addEventListener("click", (ev) => {
    +    if (ev.target === overlay) closePacksModal();
    +  });
    +  const panel = document.createElement("div");
    +  panel.className = "packs-modal";
    +  const header = document.createElement("div");
    +  header.className = "packs-modal-header";
    +  const title = document.createElement("h2");
    +  title.textContent = "Recipe Packs";
    +  const closeBtn = document.createElement("button");
    +  closeBtn.type = "button";
    +  closeBtn.className = "icon-btn packs-close-btn";
    +  closeBtn.textContent = "\u2715";
    +  closeBtn.addEventListener("click", () => closePacksModal());
    +  header.appendChild(title);
    +  header.appendChild(closeBtn);
    +  panel.appendChild(header);
    +  const tabBar = document.createElement("div");
    +  tabBar.className = "packs-tab-bar";
    +  const browseTab = document.createElement("button");
    +  browseTab.type = "button";
    +  browseTab.className = "packs-tab active";
    +  browseTab.textContent = "Browse";
    +  browseTab.setAttribute("data-tab", "browse");
    +  const myTab = document.createElement("button");
    +  myTab.type = "button";
    +  myTab.className = "packs-tab";
    +  myTab.textContent = "My Recipes";
    +  myTab.setAttribute("data-tab", "my");
    +  tabBar.appendChild(browseTab);
    +  tabBar.appendChild(myTab);
    +  panel.appendChild(tabBar);
    +  browseTab.addEventListener("click", () => {
    +    browseTab.classList.add("active");
    +    myTab.classList.remove("active");
    +    loadPacksCatalogue();
    +  });
    +  myTab.addEventListener("click", () => {
    +    myTab.classList.add("active");
    +    browseTab.classList.remove("active");
    +    loadMyRecipes();
    +  });
    +  const grid = document.createElement("div");
    +  grid.className = "packs-grid";
    +  grid.id = "packs-grid";
    +  const loading = document.createElement("p");
    +  loading.className = "packs-loading";
    +  loading.textContent = "Loading packs\u2026";
    +  grid.appendChild(loading);
    +  panel.appendChild(grid);
    +  overlay.appendChild(panel);
    +  document.body.appendChild(overlay);
    +  packsModalOverlay = overlay;
    +  requestAnimationFrame(() => overlay.classList.add("open"));
    +  loadPacksCatalogue();
    +}
    +function closePacksModal() {
    +  if (packsModalOverlay) {
    +    packsModalOverlay.classList.remove("open");
    +    setTimeout(() => {
    +      if (packsModalOverlay) packsModalOverlay.style.display = "none";
    +    }, 200);
    +  }
    +}
    +async function loadPacksCatalogue() {
    +  const grid = document.getElementById("packs-grid");
    +  if (!grid) return;
    +  grid.innerHTML = "<p class='packs-loading'>Loading packs\u2026</p>";
    +  try {
    +    const resp = await doGet("/recipes/built-in-packs");
    +    if (resp.status !== 200 || !resp.json?.packs) {
    +      grid.innerHTML = "<p class='packs-loading'>Failed to load packs.</p>";
    +      return;
    +    }
    +    const installedIds = new Set(resp.json.installed_pack_ids ?? []);
    +    grid.innerHTML = "";
    +    for (const pack of resp.json.packs) {
    +      const card = document.createElement("div");
    +      card.className = "pack-card";
    +      card.innerHTML = `
    +        <div class="pack-card-info">
    +          <strong>${escapeHtml(pack.label)}</strong>
    +          <span class="pack-card-desc">${escapeHtml(pack.description)}</span>
    +          <span class="pack-card-count">~${pack.recipe_count} recipes</span>
    +        </div>
    +      `;
    +      const btn = document.createElement("button");
    +      btn.type = "button";
    +      btn.className = "pack-install-btn";
    +      if (installedIds.has(pack.pack_id)) {
    +        btn.textContent = "Installed \u2713";
    +        btn.classList.add("installed");
    +        btn.disabled = true;
    +      } else {
    +        btn.textContent = "Install";
    +        btn.addEventListener("click", () => installPack(pack.pack_id, btn));
    +      }
    +      card.appendChild(btn);
    +      grid.appendChild(card);
    +    }
    +  } catch {
    +    grid.innerHTML = "<p class='packs-loading'>Failed to load packs.</p>";
    +  }
    +}
    +async function loadMyRecipes() {
    +  const grid = document.getElementById("packs-grid");
    +  if (!grid) return;
    +  grid.innerHTML = "<p class='packs-loading'>Loading your recipes\u2026</p>";
    +  try {
    +    const resp = await doGet("/recipes/books");
    +    if (resp.status !== 200 || !resp.json?.books) {
    +      grid.innerHTML = "<p class='packs-loading'>Failed to load recipes.</p>";
    +      return;
    +    }
    +    const books = resp.json.books;
    +    if (books.length === 0) {
    +      grid.innerHTML = "<p class='packs-loading'>No recipes yet. Browse packs to install some!</p>";
    +      return;
    +    }
    +    grid.innerHTML = "";
    +    for (const book of books) {
    +      const card = document.createElement("div");
    +      card.className = "recipe-card";
    +      const header = document.createElement("div");
    +      header.className = "recipe-card-header";
    +      header.innerHTML = `
    +        <strong>${escapeHtml(book.title || book.filename)}</strong>
    +        <span class="recipe-card-toggle">&#x25BC;</span>
    +      `;
    +      card.appendChild(header);
    +      const body = document.createElement("div");
    +      body.className = "recipe-card-body";
    +      body.style.display = "none";
    +      if (book.text_content) {
    +        body.innerHTML = renderRecipeContent(book.text_content);
    +      } else {
    +        body.innerHTML = "<p class='recipe-card-empty'>No content available.</p>";
    +      }
    +      card.appendChild(body);
    +      header.addEventListener("click", () => {
    +        const isOpen = body.style.display !== "none";
    +        body.style.display = isOpen ? "none" : "block";
    +        const toggle = header.querySelector(".recipe-card-toggle");
    +        if (toggle) toggle.innerHTML = isOpen ? "&#x25BC;" : "&#x25B2;";
    +      });
    +      grid.appendChild(card);
    +    }
    +  } catch {
    +    grid.innerHTML = "<p class='packs-loading'>Failed to load recipes.</p>";
    +  }
    +}
    +function renderRecipeContent(text) {
    +  const lines = text.split("\n");
    +  let html = "";
    +  let inSection = "";
    +  for (const line of lines) {
    +    const trimmed = line.trim();
    +    if (!trimmed) continue;
    +    if (trimmed.startsWith("# ")) {
    +      continue;
    +    }
    +    if (trimmed.startsWith("## ") || trimmed.startsWith("### ")) {
    +      if (inSection) html += "</ul>";
    +      inSection = trimmed.replace(/^#+\s*/, "");
    +      html += `<div class="recipe-section-title">${escapeHtml(inSection)}</div><ul>`;
    +      continue;
    +    }
    +    html += `<li>${escapeHtml(trimmed)}</li>`;
    +  }
    +  if (inSection) html += "</ul>";
    +  if (!html) html = `<p class="recipe-card-empty">No content to display.</p>`;
    +  return html;
    +}
    +function escapeHtml(text) {
    +  const d = document.createElement("div");
    +  d.textContent = text;
    +  return d.innerHTML;
    +}
    +async function installPack(packId, btn) {
    +  btn.disabled = true;
    +  btn.textContent = "Installing\u2026";
    +  try {
    +    const resp = await doPost("/recipes/built-in-packs/install", { pack_id: packId });
    +    if (resp.status === 200 && resp.json) {
    +      if (resp.json.installed > 0) {
    +        btn.textContent = `Installed \u2713 (${resp.json.installed})`;
    +        btn.classList.add("installed");
    +      } else {
    +        btn.textContent = "Already installed";
    +        btn.classList.add("installed");
    +      }
    +    } else {
    +      btn.textContent = "Error";
    +      btn.disabled = false;
    +    }
    +  } catch {
    +    btn.textContent = "Error";
    +    btn.disabled = false;
    +  }
     }
     function hideOnboardMenu() {
    -    if (onboardMenu) {
    -        onboardMenu.style.display = "none";
    -        onboardMenu.style.visibility = "hidden";
    -        onboardMenu.classList.remove("open");
    -    }
    -    onboardMenuActive = false;
    -    if (onboardActiveItem) {
    -        onboardActiveItem.classList.remove("active");
    -        onboardActiveItem.style.outline = "";
    -    }
    -    onboardActiveItem = null;
    +  if (onboardMenu) {
    +    onboardMenu.style.display = "none";
    +    onboardMenu.style.visibility = "hidden";
    +    onboardMenu.classList.remove("open");
    +  }
    +  onboardMenuActive = false;
    +  if (onboardActiveItem) {
    +    onboardActiveItem.classList.remove("active");
    +    onboardActiveItem.style.outline = "";
    +  }
    +  onboardActiveItem = null;
     }
     function showOnboardMenu(x, y) {
    -    const menu = ensureOnboardMenu();
    -    // Rebuild menu contents immediately before showing to ensure button visibility
    -    // reflects the latest `state.inventoryOnboarded` value (prevents race in E2E).
    -    renderOnboardMenuButtons();
    -    menu.style.display = "grid";
    -    menu.classList.add("open");
    -    menu.style.visibility = "hidden";
    -    menu.style.left = "0px";
    -    menu.style.top = "0px";
    -    const rect = menu.getBoundingClientRect();
    -    const width = rect.width || menu.offsetWidth || 0;
    -    const height = rect.height || menu.offsetHeight || 0;
    -    const viewportWidth = window.innerWidth;
    -    const viewportHeight = window.innerHeight;
    -    const offset = ONBOARD_MENU_EDGE_MARGIN;
    -    const maxLeft = Math.max(offset, viewportWidth - width - offset);
    -    const maxTop = Math.max(offset, viewportHeight - height - offset);
    -    const desiredLeft = clampNumber(x - width - offset, offset, maxLeft);
    -    const desiredTop = clampNumber(y - height - offset, offset, maxTop);
    -    menu.style.left = `${desiredLeft}px`;
    -    menu.style.top = `${desiredTop}px`;
    -    menu.style.visibility = "visible";
    -    onboardMenuActive = true;
    -    onboardIgnoreDocClickUntilMs = Date.now() + 800;
    -    onboardDragActive = true;
    +  const menu = ensureOnboardMenu();
    +  renderOnboardMenuButtons();
    +  menu.style.display = "grid";
    +  menu.classList.add("open");
    +  menu.style.visibility = "hidden";
    +  menu.style.left = "0px";
    +  menu.style.top = "0px";
    +  const rect = menu.getBoundingClientRect();
    +  const width = rect.width || menu.offsetWidth || 0;
    +  const height = rect.height || menu.offsetHeight || 0;
    +  const viewportWidth = window.innerWidth;
    +  const viewportHeight = window.innerHeight;
    +  const offset = ONBOARD_MENU_EDGE_MARGIN;
    +  const maxLeft = Math.max(offset, viewportWidth - width - offset);
    +  const maxTop = Math.max(offset, viewportHeight - height - offset);
    +  const desiredLeft = clampNumber(x - width - offset, offset, maxLeft);
    +  const desiredTop = clampNumber(y - height - offset, offset, maxTop);
    +  menu.style.left = `${desiredLeft}px`;
    +  menu.style.top = `${desiredTop}px`;
    +  menu.style.visibility = "visible";
    +  onboardMenuActive = true;
    +  onboardIgnoreDocClickUntilMs = Date.now() + 800;
    +  onboardDragActive = true;
     }
     function startOnboarding() {
    -    selectFlow("prefs");
    -    const assistantText = "To get started, letÔÇÖs set your preferences (allergies, likes/dislikes, servings, days).";
    -    const userText = "Answer in one messageÔÇª";
    -    const assistant = document.getElementById("duet-assistant-text");
    -    const user = document.getElementById("duet-user-text");
    -    if (assistant)
    -        assistant.textContent = assistantText;
    -    if (user)
    -        user.textContent = userText;
    -    setUserBubbleLabel(true);
    -}
    -function setupDock() {
    -    // Dock layout is temporarily disabled; keep the legacy logic here in case we re-enable it later.
    -    /*
    -    const shell = document.getElementById("duet-shell");
    -    const composer = document.getElementById("duet-composer");
    -    if (!shell || !composer) return;
    -    let dock = document.getElementById("duet-dock") as HTMLDivElement | null;
    -    if (!dock) {
    -      dock = document.createElement("div");
    -      dock.id = "duet-dock";
    -      dock.className = "duet-dock";
    -      shell.appendChild(dock);
    -    }
    -    if (flowMenuContainer && flowMenuContainer.parentElement !== dock) {
    -      dock.appendChild(flowMenuContainer);
    -    }
    -    if (composer.parentElement !== dock) {
    -      dock.appendChild(composer);
    -    }
    -    enforceViewportLock();
    -    */
    +  selectFlow("prefs");
    +  const assistantText = "To get started, let\u2019s set your preferences (allergies, likes/dislikes, servings, days).";
    +  const userText = "Answer in one message\u2026";
    +  const assistant = document.getElementById("duet-assistant-text");
    +  const user = document.getElementById("duet-user-text");
    +  if (assistant) assistant.textContent = assistantText;
    +  if (user) user.textContent = userText;
    +  setUserBubbleLabel(true);
     }
     function bindOnboardingLongPress() {
    -    const userBubble = document.getElementById("duet-user-bubble");
    -    if (!userBubble)
    -        return;
    -    const clearTimer = () => {
    -        if (onboardPressTimer !== null) {
    -            window.clearTimeout(onboardPressTimer);
    -            onboardPressTimer = null;
    -        }
    -    };
    -    const cancel = (opts) => {
    -        var _a;
    -        clearTimer();
    -        onboardPressStart = null;
    -        onboardPointerId = null;
    -        if ((_a = opts === null || opts === void 0 ? void 0 : opts.hideMenu) !== null && _a !== void 0 ? _a : true) {
    -            hideOnboardMenu();
    -        }
    -    };
    -    userBubble.addEventListener("pointerdown", (ev) => {
    -        onboardPressStart = { x: ev.clientX, y: ev.clientY };
    -        clearTimer();
    -        onboardPointerId = ev.pointerId;
    -        onboardPressTimer = window.setTimeout(() => {
    -            showOnboardMenu(ev.clientX, ev.clientY);
    -            onboardPressTimer = null;
    -            onboardPressStart = null;
    -            try {
    -                userBubble.setPointerCapture(ev.pointerId);
    -            }
    -            catch (_err) {
    -                // ignore if capture not supported
    -            }
    -        }, 500);
    -    });
    -    userBubble.addEventListener("pointermove", (ev) => {
    -        if (onboardMenuActive) {
    -            const el = document.elementFromPoint(ev.clientX, ev.clientY);
    -            const item = el === null || el === void 0 ? void 0 : el.closest("[data-onboard-item]");
    -            if (item !== onboardActiveItem) {
    -                if (onboardActiveItem) {
    -                    onboardActiveItem.classList.remove("active");
    -                    onboardActiveItem.style.outline = "";
    -                }
    -                onboardActiveItem = item;
    -                if (onboardActiveItem) {
    -                    onboardActiveItem.classList.add("active");
    -                    onboardActiveItem.style.outline = "2px solid #7df";
    -                }
    -            }
    -            return;
    -        }
    -        if (!onboardPressStart || onboardPressTimer === null)
    -            return;
    -        const dx = Math.abs(ev.clientX - onboardPressStart.x);
    -        const dy = Math.abs(ev.clientY - onboardPressStart.y);
    -        if (dx > 6 || dy > 6) {
    -            cancel();
    -        }
    -    });
    -    userBubble.addEventListener("pointerup", (ev) => {
    -        if (onboardMenuActive) {
    -            const startHovered = (onboardActiveItem === null || onboardActiveItem === void 0 ? void 0 : onboardActiveItem.dataset.onboardItem) === "start";
    -            if (startHovered) {
    -                startOnboarding();
    -                hideOnboardMenu();
    -            }
    -            onboardDragActive = false;
    -            cancel({ hideMenu: false });
    -            return;
    -        }
    -        cancel();
    -    });
    -    userBubble.addEventListener("pointercancel", () => cancel());
    -    userBubble.addEventListener("lostpointercapture", () => {
    -        if (onboardMenuActive) {
    -            cancel({ hideMenu: false });
    +  const userBubble = document.getElementById("duet-user-bubble");
    +  if (!userBubble) return;
    +  const clearTimer = () => {
    +    if (onboardPressTimer !== null) {
    +      window.clearTimeout(onboardPressTimer);
    +      onboardPressTimer = null;
    +    }
    +  };
    +  const cancel = (opts) => {
    +    clearTimer();
    +    onboardPressStart = null;
    +    onboardPointerId = null;
    +    if (opts?.hideMenu ?? true) {
    +      hideOnboardMenu();
    +    }
    +  };
    +  userBubble.addEventListener("pointerdown", (ev) => {
    +    onboardPressStart = { x: ev.clientX, y: ev.clientY };
    +    clearTimer();
    +    onboardPointerId = ev.pointerId;
    +    onboardPressTimer = window.setTimeout(() => {
    +      showOnboardMenu(ev.clientX, ev.clientY);
    +      onboardPressTimer = null;
    +      onboardPressStart = null;
    +      try {
    +        userBubble.setPointerCapture(ev.pointerId);
    +      } catch (_err) {
    +      }
    +    }, 500);
    +  });
    +  userBubble.addEventListener("pointermove", (ev) => {
    +    if (onboardMenuActive) {
    +      const el = document.elementFromPoint(ev.clientX, ev.clientY);
    +      const item = el?.closest("[data-onboard-item]");
    +      if (item !== onboardActiveItem) {
    +        if (onboardActiveItem) {
    +          onboardActiveItem.classList.remove("active");
    +          onboardActiveItem.style.outline = "";
             }
    -        else {
    -            cancel();
    +        onboardActiveItem = item;
    +        if (onboardActiveItem) {
    +          onboardActiveItem.classList.add("active");
    +          onboardActiveItem.style.outline = "2px solid #7df";
             }
    -    });
    -    document.addEventListener("click", (ev) => {
    -        if (!onboardMenu || onboardMenu.style.display === "none")
    -            return;
    -        if (Date.now() < onboardIgnoreDocClickUntilMs)
    -            return;
    -        if (onboardDragActive)
    -            return;
    -        if (ev.target instanceof Node && onboardMenu.contains(ev.target))
    -            return;
    +      }
    +      return;
    +    }
    +    if (!onboardPressStart || onboardPressTimer === null) return;
    +    const dx = Math.abs(ev.clientX - onboardPressStart.x);
    +    const dy = Math.abs(ev.clientY - onboardPressStart.y);
    +    if (dx > 6 || dy > 6) {
    +      cancel();
    +    }
    +  });
    +  userBubble.addEventListener("pointerup", (ev) => {
    +    if (onboardMenuActive) {
    +      const startHovered = onboardActiveItem?.dataset.onboardItem === "start";
    +      if (startHovered) {
    +        startOnboarding();
             hideOnboardMenu();
    -    });
    +      }
    +      onboardDragActive = false;
    +      cancel({ hideMenu: false });
    +      return;
    +    }
    +    cancel();
    +  });
    +  userBubble.addEventListener("pointercancel", () => cancel());
    +  userBubble.addEventListener("lostpointercapture", () => {
    +    if (onboardMenuActive) {
    +      cancel({ hideMenu: false });
    +    } else {
    +      cancel();
    +    }
    +  });
    +  document.addEventListener("click", (ev) => {
    +    if (!onboardMenu || onboardMenu.style.display === "none") return;
    +    if (Date.now() < onboardIgnoreDocClickUntilMs) return;
    +    if (onboardDragActive) return;
    +    if (ev.target instanceof Node && onboardMenu.contains(ev.target)) return;
    +    hideOnboardMenu();
    +  });
     }
     function positionFlowMenuDropdown() {
    -    const dropdown = flowMenuDropdown;
    -    const trigger = flowMenuButton;
    -    if (!dropdown || !trigger)
    -        return;
    -    const prevDisplay = dropdown.style.display;
    -    const prevVisibility = dropdown.style.visibility;
    -    dropdown.style.visibility = "hidden";
    -    dropdown.style.display = "grid";
    -    const dropdownHeight = dropdown.getBoundingClientRect().height || dropdown.offsetHeight || 0;
    -    const triggerRect = trigger.getBoundingClientRect();
    -    const viewportHeight = window.innerHeight;
    -    const spaceBelow = viewportHeight - triggerRect.bottom;
    -    const spaceAbove = triggerRect.top;
    -    dropdown.style.top = "";
    -    dropdown.style.bottom = "";
    -    dropdown.style.left = "";
    -    dropdown.style.right = "-4px";
    -    if (spaceBelow >= dropdownHeight + 8) {
    -        dropdown.style.top = `${trigger.offsetHeight + 6}px`;
    -    }
    -    else if (spaceAbove >= dropdownHeight + 8) {
    -        dropdown.style.bottom = `${trigger.offsetHeight + 6}px`;
    -    }
    -    else if (spaceBelow >= spaceAbove) {
    -        dropdown.style.top = `${Math.max(6, spaceBelow - 2)}px`;
    -    }
    -    else {
    -        dropdown.style.bottom = `${Math.max(6, spaceAbove - 2)}px`;
    -    }
    -    dropdown.style.display = prevDisplay;
    -    dropdown.style.visibility = prevVisibility;
    +  const dropdown = flowMenuDropdown;
    +  const trigger = flowMenuButton;
    +  if (!dropdown || !trigger) return;
    +  const prevDisplay = dropdown.style.display;
    +  const prevVisibility = dropdown.style.visibility;
    +  dropdown.style.visibility = "hidden";
    +  dropdown.style.display = "grid";
    +  const dropdownHeight = dropdown.getBoundingClientRect().height || dropdown.offsetHeight || 0;
    +  const triggerRect = trigger.getBoundingClientRect();
    +  const viewportHeight = window.innerHeight;
    +  const spaceBelow = viewportHeight - triggerRect.bottom;
    +  const spaceAbove = triggerRect.top;
    +  dropdown.style.top = "";
    +  dropdown.style.bottom = "";
    +  dropdown.style.left = "";
    +  dropdown.style.right = "-4px";
    +  if (spaceBelow >= dropdownHeight + 8) {
    +    dropdown.style.top = `${trigger.offsetHeight + 6}px`;
    +  } else if (spaceAbove >= dropdownHeight + 8) {
    +    dropdown.style.bottom = `${trigger.offsetHeight + 6}px`;
    +  } else if (spaceBelow >= spaceAbove) {
    +    dropdown.style.top = `${Math.max(6, spaceBelow - 2)}px`;
    +  } else {
    +    dropdown.style.bottom = `${Math.max(6, spaceAbove - 2)}px`;
    +  }
    +  dropdown.style.display = prevDisplay;
    +  dropdown.style.visibility = prevVisibility;
     }
    diff --git a/web/dist/style.css b/web/dist/style.css
    index 74a38ec..615022f 100644
    --- a/web/dist/style.css
    +++ b/web/dist/style.css
    @@ -847,3 +847,252 @@ pre {
         padding: 10px;
       }
     }
    +
    +/* ÔöÇÔöÇ Recipe packs button ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ */
    +.recipe-packs-btn {
    +  position: absolute;
    +  top: 148px;
    +  right: 16px;
    +  z-index: 50;
    +  display: inline-flex;
    +  align-items: center;
    +  justify-content: center;
    +  overflow: visible;
    +  box-shadow: var(--shadow);
    +}
    +
    +/* ÔöÇÔöÇ Recipe packs modal ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ */
    +.packs-modal-overlay {
    +  position: fixed;
    +  inset: 0;
    +  background: rgba(5, 12, 20, 0.55);
    +  backdrop-filter: blur(6px);
    +  -webkit-backdrop-filter: blur(6px);
    +  opacity: 0;
    +  pointer-events: none;
    +  transition: opacity 180ms ease;
    +  z-index: 9999;
    +  display: flex;
    +  align-items: center;
    +  justify-content: center;
    +}
    +
    +.packs-modal-overlay.open {
    +  opacity: 1;
    +  pointer-events: auto;
    +}
    +
    +.packs-modal {
    +  width: 92%;
    +  max-width: 480px;
    +  max-height: 80vh;
    +  overflow-y: auto;
    +  border-radius: 16px;
    +  background: linear-gradient(145deg, rgba(255, 255, 255, 0.06), rgba(127, 164, 255, 0.10));
    +  border: 1px solid rgba(255, 255, 255, 0.10);
    +  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.45);
    +  backdrop-filter: blur(14px);
    +  -webkit-backdrop-filter: blur(14px);
    +  padding: 18px;
    +  color: var(--text);
    +}
    +
    +.packs-modal-header {
    +  display: flex;
    +  align-items: center;
    +  justify-content: space-between;
    +  margin-bottom: 14px;
    +}
    +
    +.packs-modal-header h2 {
    +  font-size: 18px;
    +  font-weight: 700;
    +  margin: 0;
    +}
    +
    +.packs-close-btn {
    +  width: 32px;
    +  height: 32px;
    +  font-size: 16px;
    +  border-radius: 8px;
    +}
    +
    +.packs-grid {
    +  display: flex;
    +  flex-direction: column;
    +  gap: 10px;
    +}
    +
    +.packs-loading {
    +  text-align: center;
    +  opacity: 0.7;
    +  font-size: 14px;
    +}
    +
    +.pack-card {
    +  display: flex;
    +  align-items: center;
    +  justify-content: space-between;
    +  gap: 10px;
    +  padding: 10px 12px;
    +  border-radius: 10px;
    +  background: rgba(255, 255, 255, 0.05);
    +  border: 1px solid rgba(255, 255, 255, 0.08);
    +}
    +
    +.pack-card-info {
    +  display: flex;
    +  flex-direction: column;
    +  gap: 2px;
    +  min-width: 0;
    +  flex: 1;
    +}
    +
    +.pack-card-info strong {
    +  font-size: 14px;
    +}
    +
    +.pack-card-desc {
    +  font-size: 12px;
    +  opacity: 0.75;
    +  white-space: nowrap;
    +  overflow: hidden;
    +  text-overflow: ellipsis;
    +}
    +
    +.pack-card-count {
    +  font-size: 11px;
    +  opacity: 0.55;
    +}
    +
    +.pack-install-btn {
    +  flex: 0 0 auto;
    +  padding: 6px 14px;
    +  border-radius: 8px;
    +  background: linear-gradient(135deg, var(--accent), var(--accent-2));
    +  color: #051225;
    +  font-weight: 700;
    +  font-size: 13px;
    +  border: none;
    +  cursor: pointer;
    +  white-space: nowrap;
    +  transition: opacity 120ms ease;
    +}
    +
    +.pack-install-btn:hover {
    +  opacity: 0.85;
    +}
    +
    +.pack-install-btn:disabled {
    +  opacity: 0.6;
    +  cursor: default;
    +}
    +
    +.pack-install-btn.installed {
    +  background: rgba(255, 255, 255, 0.08);
    +  color: var(--text);
    +  opacity: 0.7;
    +}
    +
    +/* ÔöÇÔöÇ Packs modal tabs ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ */
    +.packs-tab-bar {
    +  display: flex;
    +  gap: 0;
    +  margin-bottom: 14px;
    +  border-radius: 10px;
    +  overflow: hidden;
    +  border: 1px solid rgba(255, 255, 255, 0.12);
    +}
    +
    +.packs-tab {
    +  flex: 1;
    +  padding: 8px 0;
    +  border: none;
    +  border-radius: 0;
    +  background: rgba(255, 255, 255, 0.04);
    +  color: var(--text);
    +  font-weight: 600;
    +  font-size: 13px;
    +  cursor: pointer;
    +  transition: background 120ms ease;
    +  margin: 0;
    +}
    +
    +.packs-tab:hover {
    +  background: rgba(255, 255, 255, 0.08);
    +}
    +
    +.packs-tab.active {
    +  background: linear-gradient(135deg, var(--accent), var(--accent-2));
    +  color: #051225;
    +}
    +
    +/* ÔöÇÔöÇ Recipe expandable cards ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ */
    +.recipe-card {
    +  border-radius: 10px;
    +  background: rgba(255, 255, 255, 0.05);
    +  border: 1px solid rgba(255, 255, 255, 0.08);
    +  overflow: hidden;
    +}
    +
    +.recipe-card-header {
    +  display: flex;
    +  align-items: center;
    +  justify-content: space-between;
    +  padding: 10px 12px;
    +  cursor: pointer;
    +  transition: background 120ms ease;
    +}
    +
    +.recipe-card-header:hover {
    +  background: rgba(255, 255, 255, 0.06);
    +}
    +
    +.recipe-card-header strong {
    +  font-size: 14px;
    +  flex: 1;
    +  min-width: 0;
    +  overflow: hidden;
    +  text-overflow: ellipsis;
    +  white-space: nowrap;
    +}
    +
    +.recipe-card-toggle {
    +  font-size: 12px;
    +  opacity: 0.6;
    +  flex: 0 0 auto;
    +  margin-left: 8px;
    +}
    +
    +.recipe-card-body {
    +  padding: 0 12px 12px;
    +  font-size: 13px;
    +  line-height: 1.5;
    +  max-height: 300px;
    +  overflow-y: auto;
    +}
    +
    +.recipe-card-body ul {
    +  list-style: disc;
    +  margin: 0 0 8px 16px;
    +  padding: 0;
    +}
    +
    +.recipe-card-body li {
    +  margin-bottom: 2px;
    +}
    +
    +.recipe-section-title {
    +  font-weight: 700;
    +  font-size: 13px;
    +  margin-top: 8px;
    +  margin-bottom: 4px;
    +  text-transform: uppercase;
    +  letter-spacing: 0.04em;
    +  opacity: 0.9;
    +}
    +
    +.recipe-card-empty {
    +  opacity: 0.6;
    +  font-style: italic;
    +}
    diff --git a/web/src/main.ts b/web/src/main.ts
    index cc5720b..3719637 100644
    --- a/web/src/main.ts
    +++ b/web/src/main.ts
    @@ -118,6 +118,8 @@ let flowMenuDropdown: HTMLDivElement | null = null;
     let flowMenuButton: HTMLButtonElement | null = null;
     let flowMenuOpen = false;
     let flowMenuListenersBound = false;
    +let recipePacksButton: HTMLButtonElement | null = null;
    +let packsModalOverlay: HTMLDivElement | null = null;
     let devPanelVisible = false;
     let inventoryOverlay: HTMLDivElement | null = null;
     let inventoryStatusEl: HTMLElement | null = null;
    @@ -938,6 +940,17 @@ function setupHistoryDrawerUi() {
         });
         stage.appendChild(historyToggle);
       }
    +
    +  if (!recipePacksButton) {
    +    recipePacksButton = document.createElement("button");
    +    recipePacksButton.id = "duet-recipe-packs";
    +    recipePacksButton.type = "button";
    +    recipePacksButton.className = "icon-btn recipe-packs-btn";
    +    recipePacksButton.setAttribute("aria-label", "Recipe packs");
    +    recipePacksButton.textContent = "­ƒôû";
    +    recipePacksButton.addEventListener("click", () => openPacksModal());
    +    stage.appendChild(recipePacksButton);
    +  }
       resetHistoryBadge();
     }
     
    @@ -1866,6 +1879,9 @@ function selectFlow(key: string) {
         updateThreadLabel();
         refreshPrefsOverlay(true);
       }
    +  if (currentFlowKey === "mealplan") {
    +    checkMealplanFirstVisit();
    +  }
       updateFlowStatusText();
     }
     
    @@ -1955,6 +1971,265 @@ function clampNumber(value: number, min: number, max: number): number {
       return Math.min(Math.max(value, min), max);
     }
     
    +// ÔöÇÔöÇ Recipe packs modal ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
    +let mealplanNudged = false;
    +
    +async function checkMealplanFirstVisit() {
    +  if (mealplanNudged) return;
    +  try {
    +    const resp = await doGet("/recipes/books");
    +    if (resp.status === 200 && resp.json?.books?.length === 0) {
    +      mealplanNudged = true;
    +      addHistory(
    +        "assistant",
    +        "Welcome to the Meal Plan! You don't have any recipes yet.\n\nTap the ­ƒôû button to browse and install a built-in recipe pack."
    +      );
    +      renderDuetHistory();
    +      updateDuetBubbles();
    +    } else {
    +      mealplanNudged = true;
    +    }
    +  } catch {
    +    // network error ÔÇö skip nudge silently
    +  }
    +}
    +
    +function openPacksModal() {
    +  if (packsModalOverlay && packsModalOverlay.isConnected) {
    +    packsModalOverlay.style.display = "";
    +    packsModalOverlay.classList.add("open");
    +    // Reset to Browse tab on reopen
    +    const browseTab = packsModalOverlay.querySelector('[data-tab="browse"]') as HTMLElement | null;
    +    const myTab = packsModalOverlay.querySelector('[data-tab="my"]') as HTMLElement | null;
    +    browseTab?.classList.add("active");
    +    myTab?.classList.remove("active");
    +    loadPacksCatalogue();
    +    return;
    +  }
    +  const overlay = document.createElement("div");
    +  overlay.className = "packs-modal-overlay";
    +  overlay.addEventListener("click", (ev) => {
    +    if (ev.target === overlay) closePacksModal();
    +  });
    +
    +  const panel = document.createElement("div");
    +  panel.className = "packs-modal";
    +
    +  const header = document.createElement("div");
    +  header.className = "packs-modal-header";
    +  const title = document.createElement("h2");
    +  title.textContent = "Recipe Packs";
    +  const closeBtn = document.createElement("button");
    +  closeBtn.type = "button";
    +  closeBtn.className = "icon-btn packs-close-btn";
    +  closeBtn.textContent = "Ô£ò";
    +  closeBtn.addEventListener("click", () => closePacksModal());
    +  header.appendChild(title);
    +  header.appendChild(closeBtn);
    +  panel.appendChild(header);
    +
    +  const tabBar = document.createElement("div");
    +  tabBar.className = "packs-tab-bar";
    +  const browseTab = document.createElement("button");
    +  browseTab.type = "button";
    +  browseTab.className = "packs-tab active";
    +  browseTab.textContent = "Browse";
    +  browseTab.setAttribute("data-tab", "browse");
    +  const myTab = document.createElement("button");
    +  myTab.type = "button";
    +  myTab.className = "packs-tab";
    +  myTab.textContent = "My Recipes";
    +  myTab.setAttribute("data-tab", "my");
    +  tabBar.appendChild(browseTab);
    +  tabBar.appendChild(myTab);
    +  panel.appendChild(tabBar);
    +
    +  browseTab.addEventListener("click", () => {
    +    browseTab.classList.add("active");
    +    myTab.classList.remove("active");
    +    loadPacksCatalogue();
    +  });
    +  myTab.addEventListener("click", () => {
    +    myTab.classList.add("active");
    +    browseTab.classList.remove("active");
    +    loadMyRecipes();
    +  });
    +
    +  const grid = document.createElement("div");
    +  grid.className = "packs-grid";
    +  grid.id = "packs-grid";
    +  const loading = document.createElement("p");
    +  loading.className = "packs-loading";
    +  loading.textContent = "Loading packsÔÇª";
    +  grid.appendChild(loading);
    +  panel.appendChild(grid);
    +
    +  overlay.appendChild(panel);
    +  document.body.appendChild(overlay);
    +  packsModalOverlay = overlay;
    +
    +  requestAnimationFrame(() => overlay.classList.add("open"));
    +  loadPacksCatalogue();
    +}
    +
    +function closePacksModal() {
    +  if (packsModalOverlay) {
    +    packsModalOverlay.classList.remove("open");
    +    setTimeout(() => {
    +      if (packsModalOverlay) packsModalOverlay.style.display = "none";
    +    }, 200);
    +  }
    +}
    +
    +async function loadPacksCatalogue() {
    +  const grid = document.getElementById("packs-grid");
    +  if (!grid) return;
    +  grid.innerHTML = "<p class='packs-loading'>Loading packsÔÇª</p>";
    +  try {
    +    const resp = await doGet("/recipes/built-in-packs");
    +    if (resp.status !== 200 || !resp.json?.packs) {
    +      grid.innerHTML = "<p class='packs-loading'>Failed to load packs.</p>";
    +      return;
    +    }
    +    const installedIds = new Set<string>(resp.json.installed_pack_ids ?? []);
    +    grid.innerHTML = "";
    +    for (const pack of resp.json.packs) {
    +      const card = document.createElement("div");
    +      card.className = "pack-card";
    +      card.innerHTML = `
    +        <div class="pack-card-info">
    +          <strong>${escapeHtml(pack.label)}</strong>
    +          <span class="pack-card-desc">${escapeHtml(pack.description)}</span>
    +          <span class="pack-card-count">~${pack.recipe_count} recipes</span>
    +        </div>
    +      `;
    +      const btn = document.createElement("button");
    +      btn.type = "button";
    +      btn.className = "pack-install-btn";
    +      if (installedIds.has(pack.pack_id)) {
    +        btn.textContent = "Installed \u2713";
    +        btn.classList.add("installed");
    +        btn.disabled = true;
    +      } else {
    +        btn.textContent = "Install";
    +        btn.addEventListener("click", () => installPack(pack.pack_id, btn));
    +      }
    +      card.appendChild(btn);
    +      grid.appendChild(card);
    +    }
    +  } catch {
    +    grid.innerHTML = "<p class='packs-loading'>Failed to load packs.</p>";
    +  }
    +}
    +
    +async function loadMyRecipes() {
    +  const grid = document.getElementById("packs-grid");
    +  if (!grid) return;
    +  grid.innerHTML = "<p class='packs-loading'>Loading your recipes\u2026</p>";
    +  try {
    +    const resp = await doGet("/recipes/books");
    +    if (resp.status !== 200 || !resp.json?.books) {
    +      grid.innerHTML = "<p class='packs-loading'>Failed to load recipes.</p>";
    +      return;
    +    }
    +    const books = resp.json.books;
    +    if (books.length === 0) {
    +      grid.innerHTML = "<p class='packs-loading'>No recipes yet. Browse packs to install some!</p>";
    +      return;
    +    }
    +    grid.innerHTML = "";
    +    for (const book of books) {
    +      const card = document.createElement("div");
    +      card.className = "recipe-card";
    +
    +      const header = document.createElement("div");
    +      header.className = "recipe-card-header";
    +      header.innerHTML = `
    +        <strong>${escapeHtml(book.title || book.filename)}</strong>
    +        <span class="recipe-card-toggle">&#x25BC;</span>
    +      `;
    +      card.appendChild(header);
    +
    +      const body = document.createElement("div");
    +      body.className = "recipe-card-body";
    +      body.style.display = "none";
    +
    +      if (book.text_content) {
    +        body.innerHTML = renderRecipeContent(book.text_content);
    +      } else {
    +        body.innerHTML = "<p class='recipe-card-empty'>No content available.</p>";
    +      }
    +      card.appendChild(body);
    +
    +      header.addEventListener("click", () => {
    +        const isOpen = body.style.display !== "none";
    +        body.style.display = isOpen ? "none" : "block";
    +        const toggle = header.querySelector(".recipe-card-toggle");
    +        if (toggle) toggle.innerHTML = isOpen ? "&#x25BC;" : "&#x25B2;";
    +      });
    +
    +      grid.appendChild(card);
    +    }
    +  } catch {
    +    grid.innerHTML = "<p class='packs-loading'>Failed to load recipes.</p>";
    +  }
    +}
    +
    +function renderRecipeContent(text: string): string {
    +  const lines = text.split("\n");
    +  let html = "";
    +  let inSection = "";
    +  for (const line of lines) {
    +    const trimmed = line.trim();
    +    if (!trimmed) continue;
    +    if (trimmed.startsWith("# ")) {
    +      // Skip the title heading (already shown in header)
    +      continue;
    +    }
    +    if (trimmed.startsWith("## ") || trimmed.startsWith("### ")) {
    +      // Section heading
    +      if (inSection) html += "</ul>";
    +      inSection = trimmed.replace(/^#+\s*/, "");
    +      html += `<div class="recipe-section-title">${escapeHtml(inSection)}</div><ul>`;
    +      continue;
    +    }
    +    // Regular line ÔÇö treat as list item
    +    html += `<li>${escapeHtml(trimmed)}</li>`;
    +  }
    +  if (inSection) html += "</ul>";
    +  if (!html) html = `<p class="recipe-card-empty">No content to display.</p>`;
    +  return html;
    +}
    +
    +function escapeHtml(text: string): string {
    +  const d = document.createElement("div");
    +  d.textContent = text;
    +  return d.innerHTML;
    +}
    +
    +async function installPack(packId: string, btn: HTMLButtonElement) {
    +  btn.disabled = true;
    +  btn.textContent = "InstallingÔÇª";
    +  try {
    +    const resp = await doPost("/recipes/built-in-packs/install", { pack_id: packId });
    +    if (resp.status === 200 && resp.json) {
    +      if (resp.json.installed > 0) {
    +        btn.textContent = `Installed Ô£ô (${resp.json.installed})`;
    +        btn.classList.add("installed");
    +      } else {
    +        btn.textContent = "Already installed";
    +        btn.classList.add("installed");
    +      }
    +    } else {
    +      btn.textContent = "Error";
    +      btn.disabled = false;
    +    }
    +  } catch {
    +    btn.textContent = "Error";
    +    btn.disabled = false;
    +  }
    +}
    +
     function hideOnboardMenu() {
       if (onboardMenu) {
         onboardMenu.style.display = "none";
    diff --git a/web/src/style.css b/web/src/style.css
    index 74a38ec..615022f 100644
    --- a/web/src/style.css
    +++ b/web/src/style.css
    @@ -847,3 +847,252 @@ pre {
         padding: 10px;
       }
     }
    +
    +/* ÔöÇÔöÇ Recipe packs button ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ */
    +.recipe-packs-btn {
    +  position: absolute;
    +  top: 148px;
    +  right: 16px;
    +  z-index: 50;
    +  display: inline-flex;
    +  align-items: center;
    +  justify-content: center;
    +  overflow: visible;
    +  box-shadow: var(--shadow);
    +}
    +
    +/* ÔöÇÔöÇ Recipe packs modal ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ */
    +.packs-modal-overlay {
    +  position: fixed;
    +  inset: 0;
    +  background: rgba(5, 12, 20, 0.55);
    +  backdrop-filter: blur(6px);
    +  -webkit-backdrop-filter: blur(6px);
    +  opacity: 0;
    +  pointer-events: none;
    +  transition: opacity 180ms ease;
    +  z-index: 9999;
    +  display: flex;
    +  align-items: center;
    +  justify-content: center;
    +}
    +
    +.packs-modal-overlay.open {
    +  opacity: 1;
    +  pointer-events: auto;
    +}
    +
    +.packs-modal {
    +  width: 92%;
    +  max-width: 480px;
    +  max-height: 80vh;
    +  overflow-y: auto;
    +  border-radius: 16px;
    +  background: linear-gradient(145deg, rgba(255, 255, 255, 0.06), rgba(127, 164, 255, 0.10));
    +  border: 1px solid rgba(255, 255, 255, 0.10);
    +  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.45);
    +  backdrop-filter: blur(14px);
    +  -webkit-backdrop-filter: blur(14px);
    +  padding: 18px;
    +  color: var(--text);
    +}
    +
    +.packs-modal-header {
    +  display: flex;
    +  align-items: center;
    +  justify-content: space-between;
    +  margin-bottom: 14px;
    +}
    +
    +.packs-modal-header h2 {
    +  font-size: 18px;
    +  font-weight: 700;
    +  margin: 0;
    +}
    +
    +.packs-close-btn {
    +  width: 32px;
    +  height: 32px;
    +  font-size: 16px;
    +  border-radius: 8px;
    +}
    +
    +.packs-grid {
    +  display: flex;
    +  flex-direction: column;
    +  gap: 10px;
    +}
    +
    +.packs-loading {
    +  text-align: center;
    +  opacity: 0.7;
    +  font-size: 14px;
    +}
    +
    +.pack-card {
    +  display: flex;
    +  align-items: center;
    +  justify-content: space-between;
    +  gap: 10px;
    +  padding: 10px 12px;
    +  border-radius: 10px;
    +  background: rgba(255, 255, 255, 0.05);
    +  border: 1px solid rgba(255, 255, 255, 0.08);
    +}
    +
    +.pack-card-info {
    +  display: flex;
    +  flex-direction: column;
    +  gap: 2px;
    +  min-width: 0;
    +  flex: 1;
    +}
    +
    +.pack-card-info strong {
    +  font-size: 14px;
    +}
    +
    +.pack-card-desc {
    +  font-size: 12px;
    +  opacity: 0.75;
    +  white-space: nowrap;
    +  overflow: hidden;
    +  text-overflow: ellipsis;
    +}
    +
    +.pack-card-count {
    +  font-size: 11px;
    +  opacity: 0.55;
    +}
    +
    +.pack-install-btn {
    +  flex: 0 0 auto;
    +  padding: 6px 14px;
    +  border-radius: 8px;
    +  background: linear-gradient(135deg, var(--accent), var(--accent-2));
    +  color: #051225;
    +  font-weight: 700;
    +  font-size: 13px;
    +  border: none;
    +  cursor: pointer;
    +  white-space: nowrap;
    +  transition: opacity 120ms ease;
    +}
    +
    +.pack-install-btn:hover {
    +  opacity: 0.85;
    +}
    +
    +.pack-install-btn:disabled {
    +  opacity: 0.6;
    +  cursor: default;
    +}
    +
    +.pack-install-btn.installed {
    +  background: rgba(255, 255, 255, 0.08);
    +  color: var(--text);
    +  opacity: 0.7;
    +}
    +
    +/* ÔöÇÔöÇ Packs modal tabs ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ */
    +.packs-tab-bar {
    +  display: flex;
    +  gap: 0;
    +  margin-bottom: 14px;
    +  border-radius: 10px;
    +  overflow: hidden;
    +  border: 1px solid rgba(255, 255, 255, 0.12);
    +}
    +
    +.packs-tab {
    +  flex: 1;
    +  padding: 8px 0;
    +  border: none;
    +  border-radius: 0;
    +  background: rgba(255, 255, 255, 0.04);
    +  color: var(--text);
    +  font-weight: 600;
    +  font-size: 13px;
    +  cursor: pointer;
    +  transition: background 120ms ease;
    +  margin: 0;
    +}
    +
    +.packs-tab:hover {
    +  background: rgba(255, 255, 255, 0.08);
    +}
    +
    +.packs-tab.active {
    +  background: linear-gradient(135deg, var(--accent), var(--accent-2));
    +  color: #051225;
    +}
    +
    +/* ÔöÇÔöÇ Recipe expandable cards ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ */
    +.recipe-card {
    +  border-radius: 10px;
    +  background: rgba(255, 255, 255, 0.05);
    +  border: 1px solid rgba(255, 255, 255, 0.08);
    +  overflow: hidden;
    +}
    +
    +.recipe-card-header {
    +  display: flex;
    +  align-items: center;
    +  justify-content: space-between;
    +  padding: 10px 12px;
    +  cursor: pointer;
    +  transition: background 120ms ease;
    +}
    +
    +.recipe-card-header:hover {
    +  background: rgba(255, 255, 255, 0.06);
    +}
    +
    +.recipe-card-header strong {
    +  font-size: 14px;
    +  flex: 1;
    +  min-width: 0;
    +  overflow: hidden;
    +  text-overflow: ellipsis;
    +  white-space: nowrap;
    +}
    +
    +.recipe-card-toggle {
    +  font-size: 12px;
    +  opacity: 0.6;
    +  flex: 0 0 auto;
    +  margin-left: 8px;
    +}
    +
    +.recipe-card-body {
    +  padding: 0 12px 12px;
    +  font-size: 13px;
    +  line-height: 1.5;
    +  max-height: 300px;
    +  overflow-y: auto;
    +}
    +
    +.recipe-card-body ul {
    +  list-style: disc;
    +  margin: 0 0 8px 16px;
    +  padding: 0;
    +}
    +
    +.recipe-card-body li {
    +  margin-bottom: 2px;
    +}
    +
    +.recipe-section-title {
    +  font-weight: 700;
    +  font-size: 13px;
    +  margin-top: 8px;
    +  margin-bottom: 4px;
    +  text-transform: uppercase;
    +  letter-spacing: 0.04em;
    +  opacity: 0.9;
    +}
    +
    +.recipe-card-empty {
    +  opacity: 0.6;
    +  font-style: italic;
    +}

## Verification
- Static: py_compile passed for builtin_packs_service.py, schemas.py, recipe_repo.py
- Build: esbuild web/dist/main.js rebuilt (77.7kb, 34ms)
- Build: CSS copied web/src/style.css -> web/dist/style.css
- Behavior: pytest 156 passed, 0 failed (6.63s)
- Contract: minimal diffs, no boundary violations, no new routes

## Notes (optional)
- Operator Step (Manual): To clear stale DB pack rows with wrong titles, run:
  ```sql
  DELETE FROM recipe_books WHERE pack_id IS NOT NULL;
  ```
  Then reinstall packs from the UI. Only execute with explicit Julius authorization.
- Optional Enhancement (sectioned content) WAS applied: install_pack() now preserves section metadata as ## headings in stored markdown.

## Next Steps
- Julius: say AUTHORIZED to commit
- After commit: run DELETE SQL above in production DB, then reinstall packs for correct titles

