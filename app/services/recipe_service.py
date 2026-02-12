from __future__ import annotations

import re
from functools import lru_cache
from typing import List

from app.repos.recipe_repo import RecipeRepo, DbRecipeRepo, get_recipe_repository
from app.schemas import (
    IngredientLine,
    RecipeBook,
    RecipeBookListResponse,
    RecipeSearchRequest,
    RecipeSearchResponse,
    RecipeSearchResult,
)


BUILT_IN_RECIPES = [
    {"id": "builtin_1", "title": "Simple Tomato Pasta"},
    {"id": "builtin_2", "title": "Garlic Butter Chicken"},
    {"id": "builtin_3", "title": "Veggie Stir Fry"},
]

# ── Ingredient extraction from pack markdown ────────────────────────────
_VALID_UNITS = frozenset({
    "g", "ml", "count", "tin", "bag", "box", "jar", "bottle",
    "pack", "loaf", "slice", "piece", "can", "carton", "tub",
    "pot", "bunch", "bulb", "head",
})
_QTY_UNIT_RE = re.compile(
    r"^(\d+(?:[./]\d+)?)\s*"
    r"(g|ml|count|tin|bag|box|jar|bottle|pack|loaf|slice|piece|can|carton|tub|pot|bunch|bulb|head"
    r"|cups?|tbsp|tsp|oz|lbs?)\b\s+(.+)",
    re.IGNORECASE,
)
_UNIT_ALIAS = {"cup": "count", "cups": "count", "tbsp": "count", "tsp": "count", "oz": "g", "lb": "g", "lbs": "g"}


def extract_ingredients_from_markdown(text_content: str) -> list[IngredientLine]:
    """Parse ``## Ingredients`` section of pack markdown into IngredientLines.

    Returns an empty list when no ingredients section is found — callers should
    treat such recipes as ingredientless (Hardness #2).
    """
    if not text_content:
        return []
    lines = text_content.splitlines()
    in_ingredients = False
    results: list[IngredientLine] = []
    for raw in lines:
        stripped = raw.strip()
        if stripped.startswith("## "):
            section = stripped[3:].strip().lower()
            in_ingredients = section in ("ingredients", "ingredient")
            continue
        if stripped.startswith("# "):
            in_ingredients = False
            continue
        if not in_ingredients or not stripped:
            continue
        # Strip leading bullet / dash / number
        cleaned = re.sub(r"^[-*•]\s*", "", stripped)
        cleaned = re.sub(r"^\d+\.\s*", "", cleaned)
        cleaned = cleaned.strip()
        if not cleaned:
            continue
        m = _QTY_UNIT_RE.match(cleaned)
        if m:
            qty_str = m.group(1)
            qty = float(eval(qty_str)) if "/" in qty_str else float(qty_str)  # handle fractions like 1/2
            raw_unit = m.group(2).lower()
            unit = _UNIT_ALIAS.get(raw_unit, raw_unit)
            if unit not in _VALID_UNITS:
                unit = "count"
            name = m.group(3).strip().rstrip(",;.")
            results.append(IngredientLine(item_name=name, quantity=qty, unit=unit, optional=False))
        else:
            results.append(IngredientLine(item_name=cleaned.rstrip(",;."), quantity=1, unit="count", optional=False))
    return results


class RecipeService:
    def __init__(self, repo: RecipeRepo) -> None:
        self.repo = repo

    @property
    def _is_db(self) -> bool:
        return isinstance(self.repo, DbRecipeRepo)

    def upload_book(self, title: str, filename: str, content_type: str, data: bytes, user_id: str | None = None) -> RecipeBook:
        if self._is_db:
            return self.repo.create_book(user_id, title, filename, content_type, data)
        return self.repo.create_book(title, filename, content_type, data)

    def list_books(self, user_id: str | None = None) -> RecipeBookListResponse:
        if self._is_db:
            return RecipeBookListResponse(books=self.repo.list_books(user_id))
        return RecipeBookListResponse(books=self.repo.list_books())

    def get_book(self, book_id: str, user_id: str | None = None) -> RecipeBook:
        book = self.repo.get_book(user_id, book_id) if self._is_db else self.repo.get_book(book_id)
        if not book:
            raise KeyError("not found")
        return book

    def delete_book(self, book_id: str, user_id: str | None = None) -> None:
        removed = self.repo.delete_book(user_id, book_id) if self._is_db else self.repo.delete_book(book_id)
        if not removed:
            raise KeyError("not found")

    def installed_pack_ids(self, user_id: str | None = None) -> list[str]:
        if self._is_db:
            return self.repo.installed_pack_ids(user_id)
        return self.repo.installed_pack_ids()

    def search(self, request: RecipeSearchRequest, user_id: str | None = None) -> RecipeSearchResponse:
        results: List[RecipeSearchResult] = []

        # built-in simple contains search
        q = request.query.lower()
        for r in BUILT_IN_RECIPES:
            if q in r["title"].lower():
                results.append(
                    RecipeSearchResult(
                        title=r["title"],
                        source_type="built_in",
                        built_in_recipe_id=r["id"],
                        file_id=None,
                        book_id=None,
                        excerpt=None,
                    )
                )
                if len(results) >= request.max_results:
                    return RecipeSearchResponse(results=results)

        # user library search (only if excerpt available)
        remaining = request.max_results - len(results)
        if remaining > 0:
            hits = self.repo.search_text(user_id, request.query, remaining) if self._is_db else self.repo.search_text(request.query, remaining)
            for book, excerpt in hits:
                results.append(
                    RecipeSearchResult(
                        title=book.title or book.filename,
                        source_type="user_library",
                        built_in_recipe_id=None,
                        file_id=book.book_id,  # reusing book_id as file anchor
                        book_id=book.book_id,
                        excerpt=excerpt,
                    )
                )
                if len(results) >= request.max_results:
                    break

        return RecipeSearchResponse(results=results)


@lru_cache(maxsize=1)
def get_recipe_service() -> RecipeService:
    return RecipeService(get_recipe_repository())


def reset_recipe_service_cache():
    get_recipe_service.cache_clear()
