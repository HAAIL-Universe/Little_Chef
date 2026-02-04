from fastapi.responses import JSONResponse
from fastapi import Request

from app.schemas import ErrorResponse


class UnauthorizedError(Exception):
    def __init__(self, message: str = "unauthorized", details=None):
        self.message = message
        self.details = details

class ServiceUnavailableError(Exception):
    def __init__(self, message: str = "service unavailable", details=None):
        self.message = message
        self.details = details


class BadRequestError(Exception):
    def __init__(self, message: str = "bad request"):
        self.message = message


class NotFoundError(Exception):
    def __init__(self, message: str = "not found"):
        self.message = message


def unauthorized_handler(_request: Request, exc: UnauthorizedError):
    return JSONResponse(
        status_code=401,
        content=ErrorResponse(error="unauthorized", message=exc.message, details=getattr(exc, "details", None)).model_dump(),
        headers={"WWW-Authenticate": "Bearer"},
    )

def service_unavailable_handler(_request: Request, exc: ServiceUnavailableError):
    return JSONResponse(
        status_code=503,
        content=ErrorResponse(error="service_unavailable", message=exc.message, details=getattr(exc, "details", None)).model_dump(),
    )


def bad_request_handler(_request: Request, exc: BadRequestError):
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(error="bad_request", message=exc.message).model_dump(),
    )


def not_found_handler(_request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(error="not_found", message=exc.message).model_dump(),
    )
