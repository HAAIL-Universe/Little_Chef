"""Built-in recipe packs service — static catalogue + on-demand HF install."""

from __future__ import annotations

import re
from typing import List

from app.schemas import BuiltInPack, BuiltInPackListResponse, InstallPackResponse, UninstallPackResponse, RecipeBook, PackPreviewRecipe, PackPreviewResponse
from app.errors import BadRequestError

try:
    from datasets import load_dataset  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    load_dataset = None  # type: ignore[assignment]


# ── Static catalogue (curated from gossminn/wikibooks-cookbook categories) ─────
# pack_id must be stable; label/description are user-facing.
PACK_CATALOGUE: List[BuiltInPack] = [
    BuiltInPack(pack_id="soup", label="Soups", description="Hearty soups and broths from around the world", recipe_count=245),
    BuiltInPack(pack_id="cake", label="Cakes", description="Baking classics — sponges, cheesecakes, and more", recipe_count=131),
    BuiltInPack(pack_id="salad", label="Salads", description="Fresh salads and dressings", recipe_count=113),
    BuiltInPack(pack_id="bread", label="Breads", description="Loaves, rolls, flatbreads and doughs", recipe_count=130),
    BuiltInPack(pack_id="pasta", label="Pasta", description="Italian-inspired pasta dishes", recipe_count=90),
    BuiltInPack(pack_id="chicken", label="Chicken", description="Chicken mains and sides", recipe_count=142),
    BuiltInPack(pack_id="beef", label="Beef", description="Beef roasts, stews, and grills", recipe_count=45),
    BuiltInPack(pack_id="fish", label="Fish & Seafood", description="Fish, shellfish and seafood dishes", recipe_count=99),
    BuiltInPack(pack_id="vegetarian", label="Vegetarian", description="Meat-free mains and sides", recipe_count=29),
    BuiltInPack(pack_id="dessert", label="Desserts", description="Puddings, pies, and sweet treats", recipe_count=308),
    BuiltInPack(pack_id="indian", label="Indian", description="Curries, dals, and Indian classics", recipe_count=54),
    BuiltInPack(pack_id="mexican", label="Mexican", description="Tacos, burritos, salsas and more", recipe_count=6),
    BuiltInPack(pack_id="chinese", label="Chinese", description="Stir-fries, dumplings, and Chinese favourites", recipe_count=6),
    BuiltInPack(pack_id="sandwich", label="Sandwiches", description="Quick sandwiches and wraps", recipe_count=56),
    BuiltInPack(pack_id="breakfast", label="Breakfast", description="Morning meals and brunch ideas", recipe_count=40),
]

_PACK_BY_ID = {p.pack_id: p for p in PACK_CATALOGUE}

# Map pack_id → regex fragments that match HF category paths
_CATEGORY_PATTERNS = {
    "soup": r"soup",
    "cake": r"cake",
    "salad": r"salad",
    "bread": r"bread",
    "pasta": r"pasta",
    "chicken": r"chicken",
    "beef": r"beef",
    "fish": r"fish|seafood|shellfish",
    "vegetarian": r"vegetarian|vegan",
    "dessert": r"dessert|pudding|sweet",
    "indian": r"indian",
    "mexican": r"mexican",
    "chinese": r"chinese",
    "sandwich": r"sandwich|wrap",
    "breakfast": r"breakfast|brunch",
}


def _slugify(text: str, max_len: int = 80) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "_", s)
    return s[:max_len].strip("_") or "recipe"


def list_packs(installed_ids: list[str] | None = None) -> BuiltInPackListResponse:
    return BuiltInPackListResponse(packs=PACK_CATALOGUE, installed_pack_ids=installed_ids or [])


def preview_pack(pack_id: str, max_recipes: int = 500) -> PackPreviewResponse:
    """Return recipe titles within a pack without installing anything."""
    if pack_id not in _PACK_BY_ID:
        raise BadRequestError(f"Unknown pack_id: {pack_id}")

    if load_dataset is None:
        raise BadRequestError("Server missing 'datasets' package — cannot preview packs")

    pattern = re.compile(_CATEGORY_PATTERNS[pack_id], re.IGNORECASE)
    ds = load_dataset("gossminn/wikibooks-cookbook", split="main")

    recipes: list[PackPreviewRecipe] = []
    for row in ds:
        if len(recipes) >= max_recipes:
            break
        infobox = row.get("recipe_data", {}) if isinstance(row.get("recipe_data"), dict) else {}
        ib = infobox.get("infobox", {}) if isinstance(infobox.get("infobox"), dict) else {}
        category = ib.get("category", "") or row.get("category", "") or ""
        if not pattern.search(category):
            continue
        title = infobox.get("title", "") or "Untitled"
        text_lines = infobox.get("text_lines", []) or []
        text_parts = [tl.get("text", "") for tl in text_lines if isinstance(tl, dict) and tl.get("text")]
        # Extract first paragraph (section=None, line_type=p) as snippet
        snippet: str | None = None
        for tl in text_lines:
            if isinstance(tl, dict) and tl.get("line_type") == "p" and not tl.get("section"):
                txt = (tl.get("text", "") or "").strip()
                if txt and len(txt) > 10:
                    snippet = txt[:200] + ("…" if len(txt) > 200 else "")
                    break
        recipes.append(PackPreviewRecipe(title=title, has_content=bool(text_parts), snippet=snippet))

    return PackPreviewResponse(
        pack_id=pack_id,
        label=_PACK_BY_ID[pack_id].label,
        recipes=recipes,
        total_available=len(recipes),
    )


def install_pack(pack_id: str, max_recipes: int, repo, user_id: str | None = None, selected_titles: list[str] | None = None) -> InstallPackResponse:
    """Download recipes from HF matching pack_id's category and load into repo.

    For in-memory RecipeRepo: user_id is ignored (no per-user isolation).
    For DbRecipeRepo: user_id is required.
    """
    if pack_id not in _PACK_BY_ID:
        raise BadRequestError(f"Unknown pack_id: {pack_id}")

    # Idempotency: check if pack already installed
    from app.repos.recipe_repo import DbRecipeRepo
    is_db = isinstance(repo, DbRecipeRepo)
    if is_db:
        if repo.has_pack(user_id, pack_id):
            return InstallPackResponse(installed=0, books=[])
    else:
        if repo.has_pack(pack_id):
            return InstallPackResponse(installed=0, books=[])

    if load_dataset is None:
        raise BadRequestError("Server missing 'datasets' package — cannot install packs")

    pattern = re.compile(_CATEGORY_PATTERNS[pack_id], re.IGNORECASE)
    ds = load_dataset("gossminn/wikibooks-cookbook", split="main")

    books: List[RecipeBook] = []
    seen_slugs: set[str] = set()

    for row in ds:
        if len(books) >= max_recipes:
            break

        # Filter by category
        category = ""
        infobox = row.get("recipe_data", {}) if isinstance(row.get("recipe_data"), dict) else {}
        if isinstance(infobox, dict):
            ib = infobox.get("infobox", {}) if isinstance(infobox.get("infobox"), dict) else {}
            category = ib.get("category", "") or ""
        if not category:
            category = row.get("category", "") or ""
        if not pattern.search(category):
            continue

        # text_lines is a list of {line_type, section, text} dicts
        tl_objs = infobox.get("text_lines", []) if isinstance(infobox, dict) else []
        text_parts = [tl.get("text", "") for tl in tl_objs if isinstance(tl, dict) and tl.get("text")]
        if not text_parts:
            continue
        title = infobox.get("title", "") or (text_parts[0].strip() if text_parts else row.get("filename", "recipe"))

        # Cherry-pick filter: if selected_titles provided, skip unselected
        if selected_titles is not None and title not in selected_titles:
            continue

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

        if is_db:
            book = repo.create_pack_book(user_id, title, filename, content, pack_id)
        else:
            book = repo.create_pack_book(title, filename, content, pack_id)
        books.append(book)

    return InstallPackResponse(installed=len(books), books=books)


def uninstall_pack(pack_id: str, repo, user_id: str | None = None, selected_titles: list[str] | None = None) -> UninstallPackResponse:
    """Remove installed recipes belonging to a pack (all or selected titles)."""
    if pack_id not in _PACK_BY_ID:
        raise BadRequestError(f"Unknown pack_id: {pack_id}")

    from app.repos.recipe_repo import DbRecipeRepo
    is_db = isinstance(repo, DbRecipeRepo)
    if is_db:
        removed = repo.uninstall_pack(user_id, pack_id, selected_titles)
    else:
        removed = repo.uninstall_pack(pack_id, selected_titles)

    return UninstallPackResponse(removed=removed)
