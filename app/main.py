from fastapi import FastAPI

from app.api.routers import health, auth, prefs, chat, inventory
from app.errors import UnauthorizedError, unauthorized_handler, BadRequestError, bad_request_handler


def create_app() -> FastAPI:
    app = FastAPI(title="Little Chef", version="0.1.0")
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(prefs.router)
    app.include_router(chat.router)
    app.include_router(inventory.router)

    app.add_exception_handler(UnauthorizedError, unauthorized_handler)
    app.add_exception_handler(BadRequestError, bad_request_handler)
    return app


app = create_app()
