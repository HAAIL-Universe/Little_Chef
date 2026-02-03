from fastapi import FastAPI

from app.api.routers import health, auth


def create_app() -> FastAPI:
    app = FastAPI(title="Little Chef", version="0.1.0")
    app.include_router(health.router)
    app.include_router(auth.router)
    return app


app = create_app()

