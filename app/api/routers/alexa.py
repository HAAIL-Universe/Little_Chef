"""Alexa skill webhook endpoint.

POST /alexa/webhook — receives Alexa skill requests and returns
Alexa-compatible JSON responses.  Authentication uses the same
JWT middleware as the rest of the API.
"""

from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.schemas import UserMe
from app.services.alexa_service import AlexaService

router = APIRouter(prefix="", tags=["Alexa"])

_alexa_service: AlexaService | None = None


def _get_alexa_service() -> AlexaService:
    global _alexa_service
    if _alexa_service is None:
        from app.api.routers.chat import _chat_service
        _alexa_service = AlexaService(
            chef_agent=_chat_service.chef_agent,
            inventory_service=_chat_service.inventory_service,
        )
    return _alexa_service


@router.post("/alexa/webhook")
def alexa_webhook(
    body: dict[str, Any],
    current_user: UserMe = Depends(get_current_user),
) -> dict[str, Any]:
    service = _get_alexa_service()
    return service.handle_request(body, current_user)


def reset_alexa_for_tests() -> None:
    """Testing helper: rebuild Alexa service."""
    global _alexa_service
    _alexa_service = None
