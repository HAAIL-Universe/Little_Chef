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
)


def create_app() -> FastAPI:
    load_env()
    app = FastAPI(title="Little Chef", version="0.1.0")
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
