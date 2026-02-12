from fastapi import APIRouter, Depends, UploadFile, File, Form, status

from app.api.deps import get_current_user
from app.schemas import (
    ErrorResponse,
    RecipeBook,
    RecipeBookListResponse,
    RecipePasteRequest,
    RecipePhotoResponse,
    RecipeSearchRequest,
    RecipeSearchResponse,
    BuiltInPackListResponse,
    InstallPackRequest,
    InstallPackResponse,
    PackPreviewResponse,
    UninstallPackRequest,
    UninstallPackResponse,
    UserMe,
    RecipeBookStatus,
)
from app.services.recipe_service import get_recipe_service
from app.errors import BadRequestError, NotFoundError

router = APIRouter(prefix="", tags=["Recipes"])


@router.get(
    "/recipes/books",
    response_model=RecipeBookListResponse,
    responses={"401": {"model": ErrorResponse}},
)
def list_books(current_user: UserMe = Depends(get_current_user)) -> RecipeBookListResponse:
    service = get_recipe_service()
    return service.list_books(user_id=current_user.user_id)


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
    return service.upload_book(title=title, filename=file.filename, content_type=file.content_type or "", data=content, user_id=current_user.user_id)


@router.post(
    "/recipes/paste",
    status_code=status.HTTP_201_CREATED,
    response_model=RecipeBook,
    responses={"400": {"model": ErrorResponse}, "401": {"model": ErrorResponse}},
)
def paste_recipe(
    request: RecipePasteRequest,
    current_user: UserMe = Depends(get_current_user),
) -> RecipeBook:
    """Create a recipe book from pasted text content."""
    service = get_recipe_service()
    return service.paste_text(
        title=request.title,
        text_content=request.text_content,
        user_id=current_user.user_id,
    )


@router.post(
    "/recipes/photo",
    status_code=status.HTTP_201_CREATED,
    response_model=RecipePhotoResponse,
    responses={"400": {"model": ErrorResponse}, "401": {"model": ErrorResponse}},
)
async def upload_recipe_photo(
    file: UploadFile = File(...),
    current_user: UserMe = Depends(get_current_user),
) -> RecipePhotoResponse:
    """Upload a photo of a recipe for OCR processing (placeholder).

    OCR extraction is not yet implemented — the photo is stored and
    the recipe is marked as 'processing' for future expansion.
    """
    content = await file.read()
    if len(content) == 0:
        raise BadRequestError("empty file")
    service = get_recipe_service()
    book = service.upload_book(
        title="",
        filename=file.filename or "photo.jpg",
        content_type=file.content_type or "image/jpeg",
        data=content,
        user_id=current_user.user_id,
    )
    return RecipePhotoResponse(
        book_id=book.book_id,
        status=RecipeBookStatus.processing,
        message="Photo received. OCR processing is not yet available — recipe will remain in 'processing' status.",
    )


@router.get(
    "/recipes/books/{book_id}",
    response_model=RecipeBook,
    responses={"401": {"model": ErrorResponse}, "404": {"model": ErrorResponse}},
)
def get_book(book_id: str, current_user: UserMe = Depends(get_current_user)) -> RecipeBook:
    service = get_recipe_service()
    try:
        return service.get_book(book_id, user_id=current_user.user_id)
    except KeyError:
        raise NotFoundError("book not found")


@router.delete(
    "/recipes/books/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={"401": {"model": ErrorResponse}, "404": {"model": ErrorResponse}},
)
def delete_book(book_id: str, current_user: UserMe = Depends(get_current_user)) -> None:
    service = get_recipe_service()
    try:
        service.delete_book(book_id, user_id=current_user.user_id)
    except KeyError:
        raise NotFoundError("book not found")


@router.get(
    "/recipes/built-in-packs",
    response_model=BuiltInPackListResponse,
    responses={"401": {"model": ErrorResponse}},
)
def list_builtin_packs(current_user: UserMe = Depends(get_current_user)) -> BuiltInPackListResponse:
    from app.services.builtin_packs_service import list_packs

    service = get_recipe_service()
    installed = service.installed_pack_ids(user_id=current_user.user_id)
    return list_packs(installed_ids=installed)


@router.get(
    "/recipes/built-in-packs/{pack_id}/preview",
    response_model=PackPreviewResponse,
    responses={"400": {"model": ErrorResponse}, "401": {"model": ErrorResponse}},
)
def preview_builtin_pack(
    pack_id: str,
    max_recipes: int = 50,
    current_user: UserMe = Depends(get_current_user),
) -> PackPreviewResponse:
    from app.services.builtin_packs_service import preview_pack

    return preview_pack(pack_id, max_recipes)


@router.post(
    "/recipes/built-in-packs/install",
    response_model=InstallPackResponse,
    responses={"400": {"model": ErrorResponse}, "401": {"model": ErrorResponse}},
)
def install_builtin_pack(
    request: InstallPackRequest,
    current_user: UserMe = Depends(get_current_user),
) -> InstallPackResponse:
    from app.services.builtin_packs_service import install_pack

    service = get_recipe_service()
    return install_pack(
        pack_id=request.pack_id,
        max_recipes=request.max_recipes,
        repo=service.repo,
        user_id=current_user.user_id,
        selected_titles=request.selected_titles,
    )


@router.post(
    "/recipes/built-in-packs/uninstall",
    response_model=UninstallPackResponse,
    responses={"400": {"model": ErrorResponse}, "401": {"model": ErrorResponse}},
)
def uninstall_builtin_pack(
    request: UninstallPackRequest,
    current_user: UserMe = Depends(get_current_user),
) -> UninstallPackResponse:
    from app.services.builtin_packs_service import uninstall_pack

    service = get_recipe_service()
    return uninstall_pack(
        pack_id=request.pack_id,
        repo=service.repo,
        user_id=current_user.user_id,
        selected_titles=request.selected_titles,
    )


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
    return service.search(request, user_id=current_user.user_id)
