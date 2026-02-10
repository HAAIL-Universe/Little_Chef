# Recipe Packs: Title Fix + Expandable Recipe Cards

> **Status of Phase A (below):** COMPLETE — all code changes applied, tests passing (156/156), dist rebuilt, staged and awaiting `AUTHORIZED` to commit. Stale DB data must be cleared manually after deploy (see Section 9).

## Context & Problem

This project is a FastAPI + vanilla TypeScript app called LittleChef. We recently added a "Recipe Packs" feature that downloads recipes from a HuggingFace dataset (`gossminn/wikibooks-cookbook`) and stores them in a Postgres `recipe_books` table.

**Two bugs/missing features need fixing:**

### Bug 1: Recipe titles are wrong
When installing a pack (e.g. "pasta"), recipe titles show ingredient lines like "¼ tsp salt", "8 eggs", or metadata like "Template:Nutritionsummary" instead of real recipe names like "Adult Macaroni and Cheese".

**Root cause:** In `app/services/builtin_packs_service.py` line 119, the code does:
```python
title = text_parts[0].strip() if text_parts else row.get("filename", "recipe")
```
This takes the first `text_lines` entry as the title, which is often an ingredient or template tag.

**The fix:** The HF dataset has a **`title`** field at `row["recipe_data"]["title"]` that contains the real recipe name. The variable called `infobox` in the code is actually `row["recipe_data"]` (the full dict), so `infobox.get("title")` gives the real title.

### Feature 2: Expandable recipe cards in "My Recipes" tab
Currently the "My Recipes" tab just shows a flat list of titles with `content_type` and `status` underneath (not useful). We want:
- Each recipe to be a clickable/expandable card
- Clicking a recipe title reveals the full recipe content (ingredients + instructions)
- The content is stored in the DB column `text_content` and in-memory repo's `_text_by_book` dict

---

## File-by-File Changes

### 1. `app/services/builtin_packs_service.py` — Fix title extraction

**Current code at line 119:**
```python
        title = text_parts[0].strip() if text_parts else row.get("filename", "recipe")
```

**Replace with:**
```python
        title = infobox.get("title", "") or (text_parts[0].strip() if text_parts else row.get("filename", "recipe"))
```

**Why this works:** The variable `infobox` is assigned on line 104 as `row.get("recipe_data", {})`. The HF dataset's `recipe_data` dict has these keys: `infobox`, `text_lines`, `title`, `url`. So `infobox.get("title")` gets the real recipe title like "Adult Macaroni and Cheese". The fallback to `text_parts[0]` handles any edge-case rows where `title` is missing.

Also update line 126 to use the proper title in the stored content:
```python
        content = f"# {title}\n\n{text_lines}\n"
```
This line is already correct — no change needed. Just confirming it uses the `title` variable which now has the right value.

**That's the only Python change for Bug 1. ONE line changed.**

### 2. `app/schemas.py` — Add `text_content` to RecipeBook

The `RecipeBook` schema currently does NOT include `text_content`. We need it for the expandable cards feature so the frontend can display the recipe body.

**Current code (lines 125-132):**
```python
class RecipeBook(BaseModel):
    book_id: str
    title: str = ""
    filename: str
    content_type: str
    status: RecipeBookStatus
    error_message: Optional[str] = None
    created_at: str
```

**Replace with:**
```python
class RecipeBook(BaseModel):
    book_id: str
    title: str = ""
    filename: str
    content_type: str
    status: RecipeBookStatus
    error_message: Optional[str] = None
    created_at: str
    text_content: Optional[str] = None
```

### 3. `app/repos/recipe_repo.py` — Return `text_content` from repos

#### 3a. In-memory `RecipeRepo.list_books()` (line 56-57)

The in-memory repo stores text in `self._text_by_book[book_id]`. We need to attach it to returned books.

**Current code (lines 56-57):**
```python
    def list_books(self) -> List[RecipeBook]:
        return list(self._books)
```

**Replace with:**
```python
    def list_books(self) -> List[RecipeBook]:
        result = []
        for b in self._books:
            clone = b.model_copy()
            clone.text_content = self._text_by_book.get(b.book_id)
            result.append(clone)
        return result
```

#### 3b. In-memory `RecipeRepo.get_book()` (lines 59-60)

**Current code:**
```python
    def get_book(self, book_id: str) -> Optional[RecipeBook]:
        return next((b for b in self._books if b.book_id == book_id), None)
```

**Replace with:**
```python
    def get_book(self, book_id: str) -> Optional[RecipeBook]:
        b = next((b for b in self._books if b.book_id == book_id), None)
        if b:
            clone = b.model_copy()
            clone.text_content = self._text_by_book.get(b.book_id)
            return clone
        return None
```

#### 3c. DB `DbRecipeRepo.list_books()` (lines 154-170)

**Current SQL on line 159:**
```python
            cur.execute(
                "SELECT book_id, title, filename, content_type, status, error_message, created_at FROM recipe_books WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,),
            )
```

**Replace with (add `text_content` to the SELECT):**
```python
            cur.execute(
                "SELECT book_id, title, filename, content_type, status, error_message, created_at, text_content FROM recipe_books WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,),
            )
```

**And update the RecipeBook construction (lines 163-170) to include `text_content`:**
```python
        return [
            RecipeBook(
                book_id=str(r[0]), title=r[1], filename=r[2], content_type=r[3],
                status=RecipeBookStatus(r[4]), error_message=r[5],
                created_at=r[6] if isinstance(r[6], str) else r[6].isoformat(),
                text_content=r[7],
            )
            for r in rows
        ]
```

#### 3d. DB `DbRecipeRepo.get_book()` (lines 172-187)

**Same pattern — update the SQL on line 177 to include `text_content`:**
```python
            cur.execute(
                "SELECT book_id, title, filename, content_type, status, error_message, created_at, text_content FROM recipe_books WHERE user_id = %s AND book_id = %s",
                (user_id, book_id),
            )
```

**And update the RecipeBook construction (lines 183-187):**
```python
        return RecipeBook(
            book_id=str(r[0]), title=r[1], filename=r[2], content_type=r[3],
            status=RecipeBookStatus(r[4]), error_message=r[5],
            created_at=r[6] if isinstance(r[6], str) else r[6].isoformat(),
            text_content=r[7],
        )
```

### 4. `app/repos/recipe_repo.py` — `create_pack_book` should set `text_content` on the returned book

#### 4a. In-memory `RecipeRepo.create_pack_book()` (lines 105-121)

After creating the book, set `text_content` on it before returning. **Current code creates book then sets `_pack_id` and appends to lists. Add `text_content` to the returned model.**

**Current (lines 109-121):**
```python
        book = RecipeBook(
            book_id=book_id,
            title=title,
            filename=filename,
            content_type="text/markdown",
            status=RecipeBookStatus.ready,
            error_message=None,
            created_at=created_at,
        )
        book._pack_id = pack_id  # type: ignore[attr-defined]
        self._books.append(book)
        self._text_by_book[book_id] = text_content
        return book
```

**Replace with:**
```python
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
        return book
```

#### 4b. DB `DbRecipeRepo.create_pack_book()` (lines 252-270)

**Current return (lines 266-270):**
```python
        return RecipeBook(
            book_id=book_id, title=title, filename=filename,
            content_type="text/markdown", status=RecipeBookStatus.ready,
            error_message=None, created_at=created_at,
        )
```

**Replace with:**
```python
        return RecipeBook(
            book_id=book_id, title=title, filename=filename,
            content_type="text/markdown", status=RecipeBookStatus.ready,
            error_message=None, created_at=created_at,
            text_content=text_content,
        )
```

### 5. `tests/test_builtin_packs.py` — Update mock data to match real dataset structure

The existing tests use mock rows with a top-level `title` field and `text` field. But the real dataset structure puts `title` inside `recipe_data`, and content comes from `recipe_data.text_lines` (list of dicts). The current mock data worked because the code had a fallback, but now we need `recipe_data.title` to be present.

**Current mock row format (line 50-63):**
```python
    fake_rows = [
        {
            "title": "Test Soup",
            "text": "Boil water. Add vegetables.",
            "recipe_data": {"infobox": {"category": "/wiki/Category:Soup_recipes"}},
            "category": "",
        },
        ...
    ]
```

**Replace ALL mock rows across the file with this format** (putting `title` and `text_lines` inside `recipe_data`):

```python
    fake_rows = [
        {
            "recipe_data": {
                "title": "Test Soup",
                "infobox": {"category": "/wiki/Category:Soup_recipes"},
                "text_lines": [
                    {"line_type": "p", "section": None, "text": "Boil water. Add vegetables."},
                ],
            },
            "filename": "recipes/test_soup.html",
        },
        {
            "recipe_data": {
                "title": "Another Soup",
                "infobox": {"category": "/wiki/Category:Soup_recipes"},
                "text_lines": [
                    {"line_type": "p", "section": None, "text": "Blend everything."},
                ],
            },
            "filename": "recipes/another_soup.html",
        },
    ]
```

Do this for ALL three test functions that create fake_rows:

1. **`test_install_pack_writes_books`** (lines 49-80): Update both rows as shown above. Keep the assertion `assert data["books"][0]["title"] == "Test Soup"` — it should still pass because `infobox.get("title")` will return "Test Soup".

2. **`test_install_pack_idempotent`** (lines 83-108): Update the single row:
```python
    fake_rows = [
        {
            "recipe_data": {
                "title": "Cake One",
                "infobox": {"category": "/wiki/Category:Cake_recipes"},
                "text_lines": [
                    {"line_type": "p", "section": None, "text": "Mix flour and sugar."},
                ],
            },
            "filename": "recipes/cake_one.html",
        },
    ]
```

3. **`test_install_pack_filters_by_category`** (lines 119-145): Update both rows:
```python
    fake_rows = [
        {
            "recipe_data": {
                "title": "Pasta Carbonara",
                "infobox": {"category": "/wiki/Category:Pasta_recipes"},
                "text_lines": [
                    {"line_type": "p", "section": None, "text": "Cook pasta. Add eggs."},
                ],
            },
            "filename": "recipes/pasta_carbonara.html",
        },
        {
            "recipe_data": {
                "title": "Chocolate Cake",
                "infobox": {"category": "/wiki/Category:Cake_recipes"},
                "text_lines": [
                    {"line_type": "p", "section": None, "text": "Not pasta."},
                ],
            },
            "filename": "recipes/chocolate_cake.html",
        },
    ]
```

### 6. `web/src/main.ts` — Expandable recipe cards in My Recipes tab

**Replace the entire `loadMyRecipes()` function** (lines 2125-2156) with this:

```typescript
async function loadMyRecipes() {
  const grid = document.getElementById("packs-grid");
  if (!grid) return;
  grid.innerHTML = "<p class='packs-loading'>Loading your recipes\u2026</p>";
  try {
    const resp = await doGet("/recipes/books");
    if (resp.status !== 200 || !resp.json?.books) {
      grid.innerHTML = "<p class='packs-loading'>Failed to load recipes.</p>";
      return;
    }
    const books = resp.json.books;
    if (books.length === 0) {
      grid.innerHTML = "<p class='packs-loading'>No recipes yet. Browse packs to install some!</p>";
      return;
    }
    grid.innerHTML = "";
    for (const book of books) {
      const card = document.createElement("div");
      card.className = "recipe-card";

      const header = document.createElement("div");
      header.className = "recipe-card-header";
      header.innerHTML = `
        <strong>${escapeHtml(book.title || book.filename)}</strong>
        <span class="recipe-card-toggle">&#x25BC;</span>
      `;
      card.appendChild(header);

      const body = document.createElement("div");
      body.className = "recipe-card-body";
      body.style.display = "none";

      if (book.text_content) {
        body.innerHTML = renderRecipeContent(book.text_content);
      } else {
        body.innerHTML = "<p class='recipe-card-empty'>No content available.</p>";
      }
      card.appendChild(body);

      header.addEventListener("click", () => {
        const isOpen = body.style.display !== "none";
        body.style.display = isOpen ? "none" : "block";
        const toggle = header.querySelector(".recipe-card-toggle");
        if (toggle) toggle.innerHTML = isOpen ? "&#x25BC;" : "&#x25B2;";
      });

      grid.appendChild(card);
    }
  } catch {
    grid.innerHTML = "<p class='packs-loading'>Failed to load recipes.</p>";
  }
}
```

**Add a new helper function `renderRecipeContent`** right after the `loadMyRecipes` function (before the `escapeHtml` function):

```typescript
function renderRecipeContent(text: string): string {
  const lines = text.split("\n");
  let html = "";
  let inSection = "";
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    if (trimmed.startsWith("# ")) {
      // Skip the title heading (already shown in header)
      continue;
    }
    if (trimmed.startsWith("## ") || trimmed.startsWith("### ")) {
      // Section heading
      if (inSection) html += "</ul>";
      inSection = trimmed.replace(/^#+\s*/, "");
      html += `<div class="recipe-section-title">${escapeHtml(inSection)}</div><ul>`;
      continue;
    }
    // Regular line — treat as list item
    html += `<li>${escapeHtml(trimmed)}</li>`;
  }
  if (inSection) html += "</ul>";
  if (!html) html = `<p class="recipe-card-empty">No content to display.</p>`;
  return html;
}
```

**IMPORTANT NOTE about the stored `text_content` format:** The content stored in the DB by `install_pack()` looks like this:
```
# Recipe Title

Template:Nutritionsummary
This dish was developed as...
¼ pound elbow macaroni
6 ounces heavy cream
...
Break the eggs...
Cook the pasta...
```

It is a flat concatenation of all `text_lines` text values joined with `\n`. It does NOT have `## Ingredients` / `## Procedure` section headers. The `section` metadata from `text_lines` is lost during storage. So the `renderRecipeContent` function will just show all lines as a list. If you want section headers, you'd need to change how `install_pack()` builds the content string — see the **Optional Enhancement** section below.

### 7. `web/src/style.css` — Add recipe card styles

**Add these styles at the very end of the file (after the `.packs-tab.active` rule on line 1029):**

```css
/* ── Recipe expandable cards ────────────────────────────────── */
.recipe-card {
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  overflow: hidden;
}

.recipe-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  cursor: pointer;
  transition: background 120ms ease;
}

.recipe-card-header:hover {
  background: rgba(255, 255, 255, 0.06);
}

.recipe-card-header strong {
  font-size: 14px;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recipe-card-toggle {
  font-size: 12px;
  opacity: 0.6;
  flex: 0 0 auto;
  margin-left: 8px;
}

.recipe-card-body {
  padding: 0 12px 12px;
  font-size: 13px;
  line-height: 1.5;
  max-height: 300px;
  overflow-y: auto;
}

.recipe-card-body ul {
  list-style: disc;
  margin: 0 0 8px 16px;
  padding: 0;
}

.recipe-card-body li {
  margin-bottom: 2px;
}

.recipe-section-title {
  font-weight: 700;
  font-size: 13px;
  margin-top: 8px;
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  opacity: 0.9;
}

.recipe-card-empty {
  opacity: 0.6;
  font-style: italic;
}
```

### 8. Optional Enhancement: Store sectioned content

If you want the stored `text_content` to have section headers (making the frontend rendering nicer), update the content-building block in `app/services/builtin_packs_service.py`.

**Current code (lines 113-126):**
```python
        # text_lines is a list of {line_type, section, text} dicts
        tl_objs = infobox.get("text_lines", []) if isinstance(infobox, dict) else []
        text_parts = [tl.get("text", "") for tl in tl_objs if isinstance(tl, dict) and tl.get("text")]
        text_lines = "\n".join(text_parts)
        if not text_lines.strip():
            continue
        title = infobox.get("title", "") or (text_parts[0].strip() if text_parts else row.get("filename", "recipe"))

        slug = _slugify(title)
        if slug in seen_slugs:
            slug = f"{slug}_{len(books)}"
        seen_slugs.add(slug)
        filename = f"{slug}.md"
        content = f"# {title}\n\n{text_lines}\n"
```

**Replace lines 113-126 with:**
```python
        # text_lines is a list of {line_type, section, text} dicts
        tl_objs = infobox.get("text_lines", []) if isinstance(infobox, dict) else []
        text_parts = [tl.get("text", "") for tl in tl_objs if isinstance(tl, dict) and tl.get("text")]
        if not text_parts:
            continue
        title = infobox.get("title", "") or (text_parts[0].strip() if text_parts else row.get("filename", "recipe"))

        # Build sectioned markdown content
        content_lines: list[str] = [f"# {title}", ""]
        current_section = ""
        for tl in tl_objs:
            if not isinstance(tl, dict):
                continue
            text = tl.get("text", "").strip()
            if not text:
                continue
            section = tl.get("section") or ""
            if section != current_section:
                current_section = section
                if section:
                    content_lines.append(f"\n## {section}\n")
            content_lines.append(text)
        content = "\n".join(content_lines) + "\n"

        slug = _slugify(title)
        if slug in seen_slugs:
            slug = f"{slug}_{len(books)}"
        seen_slugs.add(slug)
        filename = f"{slug}.md"
```

This produces content like:
```
# Adult Macaroni and Cheese

Template:Nutritionsummary
This dish was developed as...

## Ingredients

¼ pound elbow macaroni
6 ounces heavy cream
...

## Procedure

Preheat oven to 375°F...
Cook the macaroni...
```

**If you apply this optional enhancement**, the `renderRecipeContent()` function in the frontend will correctly detect `## Ingredients` and `## Procedure` section headers and render them nicely.

### 9. Clearing stale data (already-installed packs with bad titles)

Recipes already installed in the DB have wrong titles. You need to either:

**Option A (recommended):** Delete and reinstall. Run this SQL:
```sql
DELETE FROM recipe_books WHERE pack_id IS NOT NULL;
```
Then reinstall packs from the UI. They'll get correct titles.

**Option B:** If you don't want to re-download, run a one-time title fix (but this only fixes the `title` column, not the stored `text_content`).

### 10. Build step

After making all frontend changes, rebuild the bundle:

```bash
cd z:/LittleChef
npx esbuild web/src/main.ts --bundle --outfile=web/dist/main.js --format=esm --target=es2020
```

Then copy the CSS:
```bash
cp web/src/style.css web/dist/style.css
```

**IMPORTANT:** Both steps are required. The esbuild only bundles `.ts` files. The CSS is served directly from `web/dist/style.css` and must be manually copied.

---

## Verification Steps

### Step 1: Static check
```bash
cd z:/LittleChef
.venv/Scripts/python.exe -m py_compile app/services/builtin_packs_service.py
.venv/Scripts/python.exe -m py_compile app/schemas.py
.venv/Scripts/python.exe -m py_compile app/repos/recipe_repo.py
.venv/Scripts/python.exe -m py_compile app/services/recipe_service.py
.venv/Scripts/python.exe -m py_compile app/api/routers/recipes.py
```

All should succeed with no output.

### Step 2: Run tests
```bash
cd z:/LittleChef
.venv/Scripts/python.exe -m pytest tests/ -x -q
```

All ~140+ tests should pass. Pay special attention to:
- `tests/test_builtin_packs.py` — must pass with the updated mock data format
- `tests/test_recipe_books_isolation.py` — should still pass

### Step 3: Check the `text_content` field is in the response
After running the server and installing a pack, the `GET /recipes/books` response should now include `text_content` for each book. Verify in browser devtools Network tab.

---

## Summary of all files to modify

| File | What to change |
|---|---|
| `app/services/builtin_packs_service.py` | Line 119: use `infobox.get("title")` for title. Optional: build sectioned markdown content. |
| `app/schemas.py` | Add `text_content: Optional[str] = None` to `RecipeBook` class |
| `app/repos/recipe_repo.py` | Return `text_content` from `list_books()` and `get_book()` in both repo classes. Add `text_content` to `create_pack_book()` return values. |
| `tests/test_builtin_packs.py` | Update mock data to put `title` and `text_lines` inside `recipe_data` dict |
| `web/src/main.ts` | Replace `loadMyRecipes()` with expandable card version. Add `renderRecipeContent()` helper. |
| `web/src/style.css` | Add `.recipe-card`, `.recipe-card-header`, `.recipe-card-body`, etc. styles |
| `web/dist/main.js` | Rebuild with esbuild |
| `web/dist/style.css` | Copy from `web/src/style.css` |
| DB | Delete pack rows with bad titles so they reinstall cleanly |

## Environment Notes

- **Windows environment** — use `.venv/Scripts/python.exe` not `.venv/bin/python`
- **esbuild** is already installed: `npx esbuild` works from project root
- **CSS is NOT bundled** — must manually copy `web/src/style.css` to `web/dist/style.css`
- **`__pycache__` can be stale** — if Python changes don't seem to take effect, delete `__pycache__` dirs:
  ```bash
  Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
  ```
  (PowerShell) or just restart the server with `--reload` flag.
- Tests run with `DATABASE_URL=""` (in-memory repos), so DB-specific code paths are only tested via the in-memory repo unless you add specific DB tests.
- The `authed_client` test fixture creates a user with `user_id="test-user"`.

---
---

# Phase B: HF Cache Warming on Server Start + Cherry-Pick Recipe Browsing

> **Status:** NOT STARTED — This is the next phase after Phase A is committed.
> **Prerequisite:** Phase A (title fix + expandable cards) must be committed first.

## Goal

Eliminate all user-facing wait times when browsing recipe packs. The HuggingFace dataset (~15MB parquet) should be cached on the server at startup so that browsing, previewing, and installing recipes is instant.

Additionally, allow users to **preview recipe titles within a pack** before installing, and **cherry-pick individual recipes** rather than bulk-installing entire packs.

## Background & Rationale

- The `datasets` library from HuggingFace caches downloaded data on disk after the first `load_dataset()` call. Subsequent calls read from the local cache (~instant).
- Currently, the first user to install any pack triggers the download, causing a noticeable wait.
- By warming the cache at server startup, no user ever sees that delay.
- This is a **server-side cache only** — no user data is written, no DB changes, fully compliant with confirm-before-write.

---

## Phase B.1: Cache Warming on Server Startup

### What to do
Add a background task to `app/main.py` that calls `load_dataset("gossminn/wikibooks-cookbook")` at startup. This pre-populates the HuggingFace disk cache so all subsequent dataset operations are instant.

### File: `app/main.py`

Add a `lifespan` or `startup` event handler:

```python
import asyncio
import logging

logger = logging.getLogger("littlechef")

async def warm_hf_cache():
    """Pre-download HF dataset to local cache (runs in background thread)."""
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _sync_warm_cache)
        logger.info("HF recipe cache warmed successfully")
    except Exception as e:
        logger.warning(f"HF cache warming failed (non-fatal): {e}")

def _sync_warm_cache():
    from datasets import load_dataset
    load_dataset("gossminn/wikibooks-cookbook", split="train")
```

Then in the app startup:
```python
@app.on_event("startup")
async def on_startup():
    asyncio.create_task(warm_hf_cache())
```

Or if using the newer `lifespan` pattern:
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(warm_hf_cache())
    yield

app = FastAPI(lifespan=lifespan)
```

### Key design decisions
- **Non-blocking:** Uses `run_in_executor` so the synchronous `load_dataset` call doesn't block the event loop. Server starts accepting requests immediately.
- **Non-fatal:** If the download fails (network issue, HF outage), the server still starts. Users just get the old behavior (download-on-first-install).
- **No DB writes:** This only populates the HF disk cache. Confirm-before-write is respected.
- **Idempotent:** If the cache is already warm (server restart, not first deploy), the call returns instantly from disk.

### Tests
- No new test needed for the cache warming itself (it's a fire-and-forget background task).
- Existing tests are unaffected (they mock `load_dataset`).
- Optional: add a test that verifies the startup handler doesn't crash when `datasets` is unavailable (graceful degradation).

### Physics compliance
- No new endpoints. No physics update needed.

---

## Phase B.2: Pack Preview Endpoint (Browse Titles Before Installing)

### What to do
Add a new endpoint that returns recipe titles within a pack **without installing anything**. This lets the UI show an expandable list of recipe names under each pack card in the Browse tab.

### New endpoint

```
GET /recipes/built-in-packs/{pack_id}/preview?max_recipes=50
```

**Response:**
```json
{
  "pack_id": "pasta",
  "label": "Pasta",
  "recipes": [
    { "title": "Adult Macaroni and Cheese", "has_content": true },
    { "title": "Spaghetti and Sausages", "has_content": true }
  ],
  "total_available": 42
}
```

### Physics update required
Add to `Contracts/physics.yaml`:
- New path: `/recipes/built-in-packs/{pack_id}/preview`
- New schema: `PackPreviewResponse` with `pack_id`, `label`, `recipes` (list of `{title: str, has_content: bool}`), `total_available`
- Method: GET, auth required

### Backend implementation

**File: `app/services/builtin_packs_service.py`**

Add a `preview_pack()` function:
```python
def preview_pack(pack_id: str, max_recipes: int = 50) -> PackPreviewResponse:
    pack = PACK_CATALOGUE.get(pack_id)
    if not pack:
        raise ValueError(f"Unknown pack: {pack_id}")

    ds = load_dataset("gossminn/wikibooks-cookbook", split="train")
    pattern = re.compile(pack["category_pattern"], re.IGNORECASE)

    recipes = []
    for row in ds:
        if len(recipes) >= max_recipes:
            break
        infobox = row.get("recipe_data", {}) if isinstance(row.get("recipe_data"), dict) else {}
        # category filter (same logic as install_pack)
        ib = infobox.get("infobox", {}) if isinstance(infobox.get("infobox"), dict) else {}
        category = ib.get("category", "") or row.get("category", "") or ""
        if not pattern.search(category):
            continue
        title = infobox.get("title", "") or "Untitled"
        text_parts = [tl.get("text", "") for tl in infobox.get("text_lines", []) if isinstance(tl, dict) and tl.get("text")]
        recipes.append({"title": title, "has_content": bool(text_parts)})

    return PackPreviewResponse(pack_id=pack_id, label=pack["label"], recipes=recipes, total_available=len(recipes))
```

**File: `app/schemas.py`**

Add:
```python
class PackPreviewRecipe(BaseModel):
    title: str
    has_content: bool

class PackPreviewResponse(BaseModel):
    pack_id: str
    label: str
    recipes: List[PackPreviewRecipe]
    total_available: int
```

**File: `app/api/routers/recipes.py`**

Add the route (HTTP-only, calls service):
```python
@router.get("/built-in-packs/{pack_id}/preview")
async def preview_pack(pack_id: str, max_recipes: int = 50, user=Depends(get_current_user)):
    try:
        return builtin_packs_service.preview_pack(pack_id, max_recipes)
    except ValueError:
        raise HTTPException(400, detail="Unknown pack_id")
```

### Frontend: Expandable pack preview in Browse tab

**File: `web/src/main.ts`**

Update the Browse tab's pack cards. Currently each pack card has a title + "Install" button. Change to:
1. Pack card header is clickable (like the recipe cards in My Recipes)
2. Clicking it calls `GET /recipes/built-in-packs/{pack_id}/preview`
3. Expands to show a list of recipe titles with checkboxes
4. "Install Selected" button at the bottom of the expanded card
5. Or keep the existing "Install All" as a quick action

### Tests
- `test_preview_pack_returns_titles` — mock `load_dataset`, verify response contains expected titles
- `test_preview_pack_unknown_400` — unknown pack_id returns 400
- `test_preview_pack_requires_auth` — no token returns 401

---

## Phase B.3: Selective Install (Cherry-Pick Recipes)

### What to do
Extend the existing install endpoint to accept an optional list of selected recipe titles. If provided, only those recipes are installed. If omitted, behavior is unchanged (install all matching).

### Physics update required
Add optional field to `InstallPackRequest`:
```yaml
selected_titles:
  type: array
  items:
    type: string
  description: Optional list of recipe titles to install. If omitted, all matching recipes are installed.
```

### Backend implementation

**File: `app/schemas.py`**

Update `InstallPackRequest`:
```python
class InstallPackRequest(BaseModel):
    pack_id: str
    max_recipes: int = 25
    selected_titles: Optional[List[str]] = None  # NEW — cherry-pick mode
```

**File: `app/services/builtin_packs_service.py`**

In `install_pack()`, after the category filter and title extraction, add:
```python
        if selected_titles is not None and title not in selected_titles:
            continue
```

This is a one-line filter addition. If `selected_titles` is None (default), all recipes pass through. If it's a list, only matching titles are installed.

### Frontend
- The "Install Selected" button from Phase B.2 sends `{ pack_id, selected_titles: [...checked titles...] }`
- The existing "Install All" button sends `{ pack_id }` (no `selected_titles` — installs all)

### Tests
- `test_install_pack_selected_titles` — mock data with 3 recipes, select 1 by title, verify only 1 installed
- `test_install_pack_selected_titles_empty_list` — empty list installs nothing (0 recipes)

---

## Implementation Order

| Step | Phase | Effort | Dependencies |
|------|-------|--------|-------------|
| 1 | B.1 — Cache warming on startup | ~15 min | None (can do immediately after Phase A commit) |
| 2 | B.2 — Preview endpoint + physics | ~45 min | B.1 (cache must be warm for fast previews) |
| 3 | B.2 — Frontend expandable pack browse | ~30 min | B.2 backend |
| 4 | B.3 — Selective install (backend) | ~15 min | B.2 (needs preview to know titles) |
| 5 | B.3 — Frontend checkboxes + install selected | ~30 min | B.3 backend + B.2 frontend |

Total estimated: ~2.5 hours of builder time.

## Contract checklist before starting
- [ ] Update `Contracts/physics.yaml` with preview endpoint + selective install schema changes
- [ ] Update `Contracts/blueprint.md` if recipe browsing/selection is considered a new feature scope
- [ ] Get Julius approval on physics diff before writing code
- [ ] Follow builder contract: evidence bundle → minimal diffs → test gate → diff log gate → authorization gate
