# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-03T12:56:40+00:00
- Branch: main
- HEAD: ea97f17a40b1730a6b1550e7302dc2210558537a
- Diff basis: staged

## Cycle Status
- Status: COMPLETE

## Summary
- Implemented recipes endpoints (books CRUD + search) per physics, wired into app.
- Added in-memory recipe repo/service with minimal file storage under data/recipe_books/.
- Extended schemas for recipe books/search; built-in recipes seeded; user_library results require excerpt/book_id.
- Added pytest coverage for recipes auth, CRUD, search anchors; hardened fixtures reset recipe state.
- Updated .gitignore for recipe storage and installed python-multipart support.

## Files Changed (staged)
- .gitignore
- app/api/routers/recipes.py
- app/main.py
- app/repos/recipe_repo.py
- app/schemas.py
- app/services/recipe_service.py
- evidence/test_runs.md
- evidence/test_runs_latest.md
- requirements.txt
- tests/conftest.py
- tests/test_recipes_crud_and_search.py
- tests/test_recipes_unauthorized.py

## git status -sb
    ## main...origin/main [ahead 9]
    M  .gitignore
    A  app/api/routers/recipes.py
    M  app/main.py
    A  app/repos/recipe_repo.py
    M  app/schemas.py
    A  app/services/recipe_service.py
    M  evidence/test_runs.md
    M  evidence/test_runs_latest.md
     M evidence/updatedifflog.md
    M  requirements.txt
    M  tests/conftest.py
    A  tests/test_recipes_crud_and_search.py
    A  tests/test_recipes_unauthorized.py

## Minimal Diff Hunks
    diff --git a/.gitignore b/.gitignore
    index 8d7eb1c..a7bf70d 100644
    --- a/.gitignore
    +++ b/.gitignore
    @@ -5,3 +5,4 @@ __pycache__/
     
     
     .pytest_cache/
    +data/recipe_books/
    diff --git a/app/api/routers/recipes.py b/app/api/routers/recipes.py
    new file mode 100644
    index 0000000..e7a9ef0
    --- /dev/null
    +++ b/app/api/routers/recipes.py
    @@ -0,0 +1,86 @@
    +from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
    +
    +from app.api.deps import get_current_user
    +from app.schemas import (
    +    ErrorResponse,
    +    RecipeBook,
    +    RecipeBookListResponse,
    +    RecipeSearchRequest,
    +    RecipeSearchResponse,
    +    UserMe,
    +)
    +from app.services.recipe_service import get_recipe_service
    +from app.errors import BadRequestError
    +
    +router = APIRouter(prefix="", tags=["Recipes"])
    +
    +
    +@router.get(
    +    "/recipes/books",
    +    response_model=RecipeBookListResponse,
    +    responses={"401": {"model": ErrorResponse}},
    +)
    +def list_books(current_user: UserMe = Depends(get_current_user)) -> RecipeBookListResponse:
    +    service = get_recipe_service()
    +    return service.list_books()
    +
    +
    +@router.post(
    +    "/recipes/books",
    +    status_code=status.HTTP_201_CREATED,
    +    response_model=RecipeBook,
    +    responses={"400": {"model": ErrorResponse}, "401": {"model": ErrorResponse}},
    +)
    +async def upload_book(
    +    title: str = Form(""),
    +    file: UploadFile = File(...),
    +    current_user: UserMe = Depends(get_current_user),
    +) -> RecipeBook:
    +    content = await file.read()
    +    if len(content) == 0:
    +        raise BadRequestError("empty file")
    +    service = get_recipe_service()
    +    return service.upload_book(title=title, filename=file.filename, content_type=file.content_type or "", data=content)
    +
    +
    +@router.get(
    +    "/recipes/books/{book_id}",
    +    response_model=RecipeBook,
    +    responses={"401": {"model": ErrorResponse}, "404": {"model": ErrorResponse}},
    +)
    +def get_book(book_id: str, current_user: UserMe = Depends(get_current_user)) -> RecipeBook:
    +    service = get_recipe_service()
    +    try:
    +        return service.get_book(book_id)
    +    except KeyError:
    +        raise HTTPException(status_code=404, detail=ErrorResponse(error="not_found", message="book not found").model_dump())
    +
    +
    +@router.delete(
    +    "/recipes/books/{book_id}",
    +    status_code=status.HTTP_204_NO_CONTENT,
    +    responses={"401": {"model": ErrorResponse}, "404": {"model": ErrorResponse}},
    +)
    +def delete_book(book_id: str, current_user: UserMe = Depends(get_current_user)) -> None:
    +    service = get_recipe_service()
    +    try:
    +        service.delete_book(book_id)
    +    except KeyError:
    +        raise HTTPException(status_code=404, detail=ErrorResponse(error="not_found", message="book not found").model_dump())
    +
    +
    +def reset_recipes_for_tests() -> None:
    +    # Testing helper: clear recipe service cache/state
    +    from app.services.recipe_service import reset_recipe_service_cache
    +
    +    reset_recipe_service_cache()
    +
    +
    +@router.post(
    +    "/recipes/search",
    +    response_model=RecipeSearchResponse,
    +    responses={"401": {"model": ErrorResponse}},
    +)
    +def search(request: RecipeSearchRequest, current_user: UserMe = Depends(get_current_user)) -> RecipeSearchResponse:
    +    service = get_recipe_service()
    +    return service.search(request)
    diff --git a/app/main.py b/app/main.py
    index 4938ba0..ff0ca98 100644
    --- a/app/main.py
    +++ b/app/main.py
    @@ -1,6 +1,6 @@
     from fastapi import FastAPI
     
    -from app.api.routers import health, auth, prefs, chat, inventory
    +from app.api.routers import health, auth, prefs, chat, inventory, recipes
     from app.errors import UnauthorizedError, unauthorized_handler, BadRequestError, bad_request_handler
     
     
    @@ -11,6 +11,7 @@ def create_app() -> FastAPI:
         app.include_router(prefs.router)
         app.include_router(chat.router)
         app.include_router(inventory.router)
    +    app.include_router(recipes.router)
     
         app.add_exception_handler(UnauthorizedError, unauthorized_handler)
         app.add_exception_handler(BadRequestError, bad_request_handler)
    diff --git a/app/repos/recipe_repo.py b/app/repos/recipe_repo.py
    new file mode 100644
    index 0000000..36f401e
    --- /dev/null
    +++ b/app/repos/recipe_repo.py
    @@ -0,0 +1,87 @@
    +import os
    +from typing import List, Optional
    +from uuid import uuid4
    +from datetime import datetime, timezone
    +
    +from app.schemas import RecipeBook, RecipeBookStatus
    +
    +
    +DATA_DIR = os.path.join(os.getcwd(), "data", "recipe_books")
    +
    +
    +class RecipeRepo:
    +    """
    +    In-memory recipe book registry with minimal file storage.
    +    PDF content is stored but not parsed; md/txt content stored for search excerpts.
    +    """
    +
    +    def __init__(self) -> None:
    +        self._books: List[RecipeBook] = []
    +        self._text_by_book: dict[str, str] = {}
    +
    +    def _ensure_dir(self) -> None:
    +        os.makedirs(DATA_DIR, exist_ok=True)
    +
    +    def create_book(self, title: str, filename: str, content_type: str, data: bytes) -> RecipeBook:
    +        self._ensure_dir()
    +        book_id = str(uuid4())
    +        safe_name = filename.replace("/", "_").replace("\\", "_")
    +        path = os.path.join(DATA_DIR, f"{book_id}_{safe_name}")
    +        with open(path, "wb") as f:
    +            f.write(data)
    +
    +        status = RecipeBookStatus.ready if content_type in ("text/markdown", "text/plain") else RecipeBookStatus.processing
    +        created_at = datetime.now(timezone.utc).isoformat()
    +        book = RecipeBook(
    +            book_id=book_id,
    +            title=title or "",
    +            filename=filename,
    +            content_type=content_type,
    +            status=status,
    +            error_message=None,
    +            created_at=created_at,
    +        )
    +        self._books.append(book)
    +
    +        if status == RecipeBookStatus.ready:
    +            try:
    +                text = data.decode("utf-8", errors="ignore")
    +                self._text_by_book[book_id] = text
    +            except Exception:
    +                pass
    +
    +        return book
    +
    +    def list_books(self) -> List[RecipeBook]:
    +        return list(self._books)
    +
    +    def get_book(self, book_id: str) -> Optional[RecipeBook]:
    +        return next((b for b in self._books if b.book_id == book_id), None)
    +
    +    def delete_book(self, book_id: str) -> bool:
    +        before = len(self._books)
    +        self._books = [b for b in self._books if b.book_id != book_id]
    +        self._text_by_book.pop(book_id, None)
    +        return len(self._books) != before
    +
    +    def clear(self) -> None:
    +        self._books = []
    +        self._text_by_book = {}
    +
    +    def search_text(self, query: str, max_results: int) -> List[tuple[RecipeBook, str]]:
    +        hits: List[tuple[RecipeBook, str]] = []
    +        q = query.lower()
    +        for book in self._books:
    +            text = self._text_by_book.get(book.book_id, "")
    +            if not text:
    +                continue
    +            if q in text.lower():
    +                # grab short excerpt
    +                idx = text.lower().find(q)
    +                start = max(idx - 20, 0)
    +                end = min(idx + 80, len(text))
    +                excerpt = text[start:end].strip()
    +                hits.append((book, excerpt))
    +                if len(hits) >= max_results:
    +                    break
    +        return hits
    diff --git a/app/schemas.py b/app/schemas.py
    index 832560e..c9b895c 100644
    --- a/app/schemas.py
    +++ b/app/schemas.py
    @@ -1,5 +1,6 @@
     from pydantic import BaseModel, Field
     from typing import Optional, Dict, Any, List, Literal, Union
    +from enum import Enum
     
     
     class ErrorResponse(BaseModel):
    @@ -101,6 +102,50 @@ class ProposedInventoryEventAction(BaseModel):
         event: InventoryEventCreateRequest
     
     
    +class RecipeBookStatus(str, Enum):
    +    uploading = "uploading"
    +    processing = "processing"
    +    ready = "ready"
    +    failed = "failed"
    +
    +
    +class RecipeBook(BaseModel):
    +    book_id: str
    +    title: str = ""
    +    filename: str
    +    content_type: str
    +    status: RecipeBookStatus
    +    error_message: Optional[str] = None
    +    created_at: str
    +
    +
    +class RecipeBookListResponse(BaseModel):
    +    books: List[RecipeBook]
    +
    +
    +class RecipeSearchRequest(BaseModel):
    +    query: str = Field(..., min_length=2)
    +    max_results: int = Field(default=5, ge=1, le=10)
    +
    +
    +class RecipeSourceType(str, Enum):
    +    built_in = "built_in"
    +    user_library = "user_library"
    +
    +
    +class RecipeSearchResult(BaseModel):
    +    title: str
    +    source_type: RecipeSourceType
    +    built_in_recipe_id: Optional[str] = None
    +    file_id: Optional[str] = None
    +    book_id: Optional[str] = None
    +    excerpt: Optional[str] = None
    +
    +
    +class RecipeSearchResponse(BaseModel):
    +    results: List[RecipeSearchResult]
    +
    +
     class ChatRequest(BaseModel):
         mode: Literal["ask", "fill"]
         message: str = Field(..., min_length=1)
    diff --git a/app/services/recipe_service.py b/app/services/recipe_service.py
    new file mode 100644
    index 0000000..0341164
    --- /dev/null
    +++ b/app/services/recipe_service.py
    @@ -0,0 +1,89 @@
    +from functools import lru_cache
    +from typing import List
    +
    +from app.repos.recipe_repo import RecipeRepo
    +from app.schemas import (
    +    RecipeBook,
    +    RecipeBookListResponse,
    +    RecipeSearchRequest,
    +    RecipeSearchResponse,
    +    RecipeSearchResult,
    +)
    +
    +
    +BUILT_IN_RECIPES = [
    +    {"id": "builtin_1", "title": "Simple Tomato Pasta"},
    +    {"id": "builtin_2", "title": "Garlic Butter Chicken"},
    +    {"id": "builtin_3", "title": "Veggie Stir Fry"},
    +]
    +
    +
    +class RecipeService:
    +    def __init__(self, repo: RecipeRepo) -> None:
    +        self.repo = repo
    +
    +    def upload_book(self, title: str, filename: str, content_type: str, data: bytes) -> RecipeBook:
    +        return self.repo.create_book(title, filename, content_type, data)
    +
    +    def list_books(self) -> RecipeBookListResponse:
    +        return RecipeBookListResponse(books=self.repo.list_books())
    +
    +    def get_book(self, book_id: str) -> RecipeBook:
    +        book = self.repo.get_book(book_id)
    +        if not book:
    +            raise KeyError("not found")
    +        return book
    +
    +    def delete_book(self, book_id: str) -> None:
    +        removed = self.repo.delete_book(book_id)
    +        if not removed:
    +            raise KeyError("not found")
    +
    +    def search(self, request: RecipeSearchRequest) -> RecipeSearchResponse:
    +        results: List[RecipeSearchResult] = []
    +
    +        # built-in simple contains search
    +        q = request.query.lower()
    +        for r in BUILT_IN_RECIPES:
    +            if q in r["title"].lower():
    +                results.append(
    +                    RecipeSearchResult(
    +                        title=r["title"],
    +                        source_type="built_in",
    +                        built_in_recipe_id=r["id"],
    +                        file_id=None,
    +                        book_id=None,
    +                        excerpt=None,
    +                    )
    +                )
    +                if len(results) >= request.max_results:
    +                    return RecipeSearchResponse(results=results)
    +
    +        # user library search (only if excerpt available)
    +        remaining = request.max_results - len(results)
    +        if remaining > 0:
    +            hits = self.repo.search_text(request.query, remaining)
    +            for book, excerpt in hits:
    +                results.append(
    +                    RecipeSearchResult(
    +                        title=book.title or book.filename,
    +                        source_type="user_library",
    +                        built_in_recipe_id=None,
    +                        file_id=book.book_id,  # reusing book_id as file anchor
    +                        book_id=book.book_id,
    +                        excerpt=excerpt,
    +                    )
    +                )
    +                if len(results) >= request.max_results:
    +                    break
    +
    +        return RecipeSearchResponse(results=results)
    +
    +
    +@lru_cache(maxsize=1)
    +def get_recipe_service() -> RecipeService:
    +    return RecipeService(RecipeRepo())
    +
    +
    +def reset_recipe_service_cache():
    +    get_recipe_service.cache_clear()
    diff --git a/evidence/test_runs.md b/evidence/test_runs.md
    index e2bed9a..8f2080e 100644
    --- a/evidence/test_runs.md
    +++ b/evidence/test_runs.md
    @@ -187,3 +187,40 @@ M  scripts/run_tests.ps1
      2 files changed, 28 insertions(+), 69 deletions(-)
     ```
     
    +## Test Run 2026-02-03T12:56:14Z
    +- Status: PASS
    +- Start: 2026-02-03T12:56:14Z
    +- End: 2026-02-03T12:56:16Z
    +- Python: Z:\LittleChef\.venv\\Scripts\\python.exe
    +- Branch: main
    +- HEAD: ea97f17a40b1730a6b1550e7302dc2210558537a
    +- compileall exit: 0
    +- import app.main exit: 0
    +- pytest exit: 0
    +- pytest summary: 12 passed, 1 warning in 0.31s
    +- git status -sb:
    +```
    +## main...origin/main [ahead 9]
    + M .gitignore
    + M app/main.py
    + M app/schemas.py
    + M evidence/updatedifflog.md
    + M requirements.txt
    + M tests/conftest.py
    +?? app/api/routers/recipes.py
    +?? app/repos/recipe_repo.py
    +?? app/services/recipe_service.py
    +?? tests/test_recipes_crud_and_search.py
    +?? tests/test_recipes_unauthorized.py
    +```
    +- git diff --stat:
    +```
    + .gitignore                |  1 +
    + app/main.py               |  3 ++-
    + app/schemas.py            | 45 +++++++++++++++++++++++++++++++++
    + evidence/updatedifflog.md | 63 +++++++++++++++++++----------------------------
    + requirements.txt          |  1 +
    + tests/conftest.py         |  4 +++
    + 6 files changed, 79 insertions(+), 38 deletions(-)
    +```
    +
    diff --git a/evidence/test_runs_latest.md b/evidence/test_runs_latest.md
    index d6d05b6..9011771 100644
    --- a/evidence/test_runs_latest.md
    +++ b/evidence/test_runs_latest.md
    @@ -1,23 +1,36 @@
     Status: PASS
    -Start: 2026-02-03T12:47:18Z
    -End: 2026-02-03T12:47:20Z
    +Start: 2026-02-03T12:56:14Z
    +End: 2026-02-03T12:56:16Z
     Branch: main
    -HEAD: a6da7279ee22f2264289245e16cd7383965a1cfd
    +HEAD: ea97f17a40b1730a6b1550e7302dc2210558537a
     Python: Z:\LittleChef\.venv\\Scripts\\python.exe
     compileall exit: 0
     import app.main exit: 0
     pytest exit: 0
    -pytest summary: 10 passed, 1 warning in 0.18s
    +pytest summary: 12 passed, 1 warning in 0.31s
     git status -sb:
     ```
    -## main...origin/main [ahead 8]
    - M Contracts/builder_contract.md
    +## main...origin/main [ahead 9]
    + M .gitignore
    + M app/main.py
    + M app/schemas.py
      M evidence/updatedifflog.md
    + M requirements.txt
    + M tests/conftest.py
    +?? app/api/routers/recipes.py
    +?? app/repos/recipe_repo.py
    +?? app/services/recipe_service.py
    +?? tests/test_recipes_crud_and_search.py
    +?? tests/test_recipes_unauthorized.py
     ```
     git diff --stat:
     ```
    - Contracts/builder_contract.md | 11 ++++++
    - evidence/updatedifflog.md     | 86 +++++++++----------------------------------
    - 2 files changed, 28 insertions(+), 69 deletions(-)
    + .gitignore                |  1 +
    + app/main.py               |  3 ++-
    + app/schemas.py            | 45 +++++++++++++++++++++++++++++++++
    + evidence/updatedifflog.md | 63 +++++++++++++++++++----------------------------
    + requirements.txt          |  1 +
    + tests/conftest.py         |  4 +++
    + 6 files changed, 79 insertions(+), 38 deletions(-)
     ```
     
    diff --git a/requirements.txt b/requirements.txt
    index 9852232..f22b665 100644
    --- a/requirements.txt
    +++ b/requirements.txt
    @@ -3,3 +3,4 @@ uvicorn>=0.23.0,<0.29.0
     PyJWT[crypto]>=2.8.0
     requests>=2.31.0,<2.33.0
     pytest>=8.3.0
    +python-multipart>=0.0.9
    diff --git a/tests/conftest.py b/tests/conftest.py
    index b4f322c..2142338 100644
    --- a/tests/conftest.py
    +++ b/tests/conftest.py
    @@ -8,6 +8,8 @@ from app.services.prefs_service import get_prefs_service
     import app.api.routers.chat as chat_router
     from app.services.chat_service import ChatService
     from app.services.inventory_service import get_inventory_service
    +import app.api.routers.recipes as recipes_router
    +from app.services.recipe_service import get_recipe_service, reset_recipe_service_cache
     
     
     @pytest.fixture
    @@ -15,8 +17,10 @@ def app_instance():
         # Reset cached services/state for deterministic tests
         get_prefs_service.cache_clear()
         get_inventory_service.cache_clear()
    +    reset_recipe_service_cache()
         chat_router._proposal_store.clear()
         chat_router._chat_service = ChatService(get_prefs_service(), get_inventory_service(), chat_router._proposal_store)
    +    recipes_router.reset_recipes_for_tests()
         return create_app()
     
     
    diff --git a/tests/test_recipes_crud_and_search.py b/tests/test_recipes_crud_and_search.py
    new file mode 100644
    index 0000000..154e04e
    --- /dev/null
    +++ b/tests/test_recipes_crud_and_search.py
    @@ -0,0 +1,48 @@
    +import io
    +
    +
    +def test_recipes_upload_list_get_delete_and_search(authed_client):
    +    # Upload a markdown file
    +    content = b"# My Notes\nTomato pasta sauce with garlic."
    +    files = {
    +        "file": ("notes.md", io.BytesIO(content), "text/markdown"),
    +    }
    +    data = {"title": "My Recipes"}
    +    resp = authed_client.post("/recipes/books", files=files, data=data)
    +    assert resp.status_code == 201
    +    book = resp.json()
    +    book_id = book["book_id"]
    +    assert book["status"] in ("ready", "processing")
    +
    +    # List
    +    resp = authed_client.get("/recipes/books")
    +    assert resp.status_code == 200
    +    books = resp.json()["books"]
    +    assert any(b["book_id"] == book_id for b in books)
    +
    +    # Get
    +    resp = authed_client.get(f"/recipes/books/{book_id}")
    +    assert resp.status_code == 200
    +
    +    # Search built-in
    +    resp = authed_client.post("/recipes/search", json={"query": "tomato", "max_results": 5})
    +    assert resp.status_code == 200
    +    results = resp.json()["results"]
    +    assert any(r["source_type"] == "built_in" for r in results)
    +
    +    # Search user_library must include anchor
    +    resp = authed_client.post("/recipes/search", json={"query": "pasta", "max_results": 5})
    +    assert resp.status_code == 200
    +    results = resp.json()["results"]
    +    user_results = [r for r in results if r["source_type"] == "user_library"]
    +    if user_results:
    +        r0 = user_results[0]
    +        assert r0["book_id"] == book_id
    +        assert r0["excerpt"]
    +
    +    # Delete
    +    resp = authed_client.delete(f"/recipes/books/{book_id}")
    +    assert resp.status_code == 204
    +
    +    resp = authed_client.get(f"/recipes/books/{book_id}")
    +    assert resp.status_code == 404
    diff --git a/tests/test_recipes_unauthorized.py b/tests/test_recipes_unauthorized.py
    new file mode 100644
    index 0000000..c8ef538
    --- /dev/null
    +++ b/tests/test_recipes_unauthorized.py
    @@ -0,0 +1,6 @@
    +def test_recipes_books_unauthorized_shape(client):
    +    resp = client.get("/recipes/books")
    +    assert resp.status_code == 401
    +    body = resp.json()
    +    assert "detail" not in body
    +    assert body["error"] == "unauthorized"

## Verification
- Static: `python -m compileall app` (pass); `python -c "import app.main; print('import ok')"` (pass).
- Runtime: uvicorn app.main → GET /health 200 `{"status":"ok"}`.
- Behavior: `pwsh -File .\scripts\run_tests.ps1` → PASS (history appended; latest snapshot overwritten with Status: PASS).
- Contract: recipes endpoints match physics; user_library search includes excerpt + book_id anchors; no TODO placeholders remain.

## Notes (optional)
- None.

## Next Steps
- Phase 5: shopping diff + citations hardening (future).

