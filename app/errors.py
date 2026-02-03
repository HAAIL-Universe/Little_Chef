from fastapi.responses import JSONResponse
from fastapi import Request

from app.schemas import ErrorResponse


class UnauthorizedError(Exception):
    def __init__(self, message: str = "unauthorized"):
        self.message = message


class BadRequestError(Exception):
    def __init__(self, message: str = "bad request"):
        self.message = message


def unauthorized_handler(_request: Request, exc: UnauthorizedError):
    return JSONResponse(
        status_code=401,
        content=ErrorResponse(error="unauthorized", message=exc.message).model_dump(),
        headers={"WWW-Authenticate": "Bearer"},
    )


def bad_request_handler(_request: Request, exc: BadRequestError):
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(error="bad_request", message=exc.message).model_dump(),
    )
