import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path

from app.config.env import load_env
from app.api.routers import health, auth, prefs, chat, inventory, recipes, shopping, mealplan
from app.errors import (
    UnauthorizedError,
    unauthorized_handler,
    BadRequestError,
    bad_request_handler,
    NotFoundError,
    not_found_handler,
    ServiceUnavailableError,
    service_unavailable_handler,
)

logger = logging.getLogger("littlechef")


async def warm_hf_cache() -> None:
    """Pre-download HF dataset to local cache (runs in background thread)."""
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _sync_warm_cache)
        logger.info("HF recipe cache warmed successfully")
    except Exception as e:
        logger.warning(f"HF cache warming failed (non-fatal): {e}")


def _sync_warm_cache() -> None:
    from datasets import load_dataset  # type: ignore[import-untyped]
    load_dataset("gossminn/wikibooks-cookbook", split="train")


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(warm_hf_cache())
    yield


def create_app() -> FastAPI:
    load_env()
    app = FastAPI(title="Little Chef", version="0.1.0", lifespan=lifespan)
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(prefs.router)
    app.include_router(chat.router)
    app.include_router(inventory.router)
    app.include_router(recipes.router)
    app.include_router(shopping.router)
    app.include_router(mealplan.router)

    app.add_exception_handler(UnauthorizedError, unauthorized_handler)
    app.add_exception_handler(BadRequestError, bad_request_handler)
    app.add_exception_handler(NotFoundError, not_found_handler)
    app.add_exception_handler(ServiceUnavailableError, service_unavailable_handler)

    dist_dir = (Path(__file__).resolve().parent.parent / "web" / "dist").resolve()

    @app.get("/", include_in_schema=True)
    def ui_index():
        index_path = dist_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path, media_type="text/html")
        return JSONResponse(
            status_code=503,
            content={"error": "ui_not_built", "message": "UI build missing. Run npm --prefix web install && npm --prefix web run build."},
        )

    @app.get("/static/{path:path}", include_in_schema=True)
    def ui_static(path: str):
        target = (dist_dir / path).resolve()
        if not str(target).startswith(str(dist_dir)):
            raise HTTPException(status_code=404, detail="not found")
        if not target.exists():
            raise HTTPException(status_code=404, detail="not found")
        return FileResponse(target)

    return app


app = create_app()
