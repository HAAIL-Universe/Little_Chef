from fastapi import FastAPI

from app.api.routers import health, auth, prefs, chat


def create_app() -> FastAPI:
    app = FastAPI(title="Little Chef", version="0.1.0")
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(prefs.router)
    app.include_router(chat.router)
    return app


app = create_app()
