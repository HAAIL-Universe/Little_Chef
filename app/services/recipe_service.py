from functools import lru_cache
from typing import List

from app.repos.recipe_repo import RecipeRepo
from app.schemas import (
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


class RecipeService:
    def __init__(self, repo: RecipeRepo) -> None:
        self.repo = repo

    def upload_book(self, title: str, filename: str, content_type: str, data: bytes) -> RecipeBook:
        return self.repo.create_book(title, filename, content_type, data)

    def list_books(self) -> RecipeBookListResponse:
        return RecipeBookListResponse(books=self.repo.list_books())

    def get_book(self, book_id: str) -> RecipeBook:
        book = self.repo.get_book(book_id)
        if not book:
            raise KeyError("not found")
        return book

    def delete_book(self, book_id: str) -> None:
        removed = self.repo.delete_book(book_id)
        if not removed:
            raise KeyError("not found")

    def search(self, request: RecipeSearchRequest) -> RecipeSearchResponse:
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
            hits = self.repo.search_text(request.query, remaining)
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
    return RecipeService(RecipeRepo())


def reset_recipe_service_cache():
    get_recipe_service.cache_clear()
