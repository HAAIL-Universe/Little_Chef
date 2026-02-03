from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status

from app.api.deps import get_current_user
from app.schemas import (
    ErrorResponse,
    RecipeBook,
    RecipeBookListResponse,
    RecipeSearchRequest,
    RecipeSearchResponse,
    UserMe,
)
from app.services.recipe_service import get_recipe_service
from app.errors import BadRequestError

router = APIRouter(prefix="", tags=["Recipes"])


@router.get(
    "/recipes/books",
    response_model=RecipeBookListResponse,
    responses={"401": {"model": ErrorResponse}},
)
def list_books(current_user: UserMe = Depends(get_current_user)) -> RecipeBookListResponse:
    service = get_recipe_service()
    return service.list_books()


@router.post(
    "/recipes/books",
    status_code=status.HTTP_201_CREATED,
    response_model=RecipeBook,
    responses={"400": {"model": ErrorResponse}, "401": {"model": ErrorResponse}},
)
async def upload_book(
    title: str = Form(""),
    file: UploadFile = File(...),
    current_user: UserMe = Depends(get_current_user),
) -> RecipeBook:
    content = await file.read()
    if len(content) == 0:
        raise BadRequestError("empty file")
    service = get_recipe_service()
    return service.upload_book(title=title, filename=file.filename, content_type=file.content_type or "", data=content)


@router.get(
    "/recipes/books/{book_id}",
    response_model=RecipeBook,
    responses={"401": {"model": ErrorResponse}, "404": {"model": ErrorResponse}},
)
def get_book(book_id: str, current_user: UserMe = Depends(get_current_user)) -> RecipeBook:
    service = get_recipe_service()
    try:
        return service.get_book(book_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=ErrorResponse(error="not_found", message="book not found").model_dump())


@router.delete(
    "/recipes/books/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={"401": {"model": ErrorResponse}, "404": {"model": ErrorResponse}},
)
def delete_book(book_id: str, current_user: UserMe = Depends(get_current_user)) -> None:
    service = get_recipe_service()
    try:
        service.delete_book(book_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=ErrorResponse(error="not_found", message="book not found").model_dump())


def reset_recipes_for_tests() -> None:
    # Testing helper: clear recipe service cache/state
    from app.services.recipe_service import reset_recipe_service_cache

    reset_recipe_service_cache()


@router.post(
    "/recipes/search",
    response_model=RecipeSearchResponse,
    responses={"401": {"model": ErrorResponse}},
)
def search(request: RecipeSearchRequest, current_user: UserMe = Depends(get_current_user)) -> RecipeSearchResponse:
    service = get_recipe_service()
    return service.search(request)
