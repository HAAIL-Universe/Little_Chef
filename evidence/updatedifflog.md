# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-03T11:46:15+00:00
- Branch: main
- HEAD: 6b4b06c27821840d7fab1286ac375f62d564685b
- Diff basis: staged

## Cycle Status
- Status: COMPLETE

## Summary
- Phase 2 tests + run_tests.ps1
- Added pytest suite for health/auth/prefs/chat propose/confirm
- Ensured ErrorResponse shape is top-level and added test runner script

## Files Changed (staged)
- app/api/deps.py
- app/api/routers/auth.py
- app/api/routers/chat.py
- app/api/routers/prefs.py
- app/errors.py
- app/main.py
- app/repos/prefs_repo.py
- app/services/chat_service.py
- app/services/prefs_service.py
- app/services/proposal_store.py
- requirements.txt
- scripts/run_tests.ps1
- tests/conftest.py
- tests/test_auth_unauthorized_shape.py
- tests/test_chat_confirm_missing_proposal.py
- tests/test_chat_prefs_propose_confirm.py
- tests/test_health.py
- tests/test_prefs_defaults_and_upsert.py

## git status -sb
    ## main...origin/main
     M Contracts/builder_contract.md
    M  app/api/deps.py
    M  app/api/routers/auth.py
    M  app/api/routers/chat.py
    M  app/api/routers/prefs.py
    A  app/errors.py
    M  app/main.py
    M  app/repos/prefs_repo.py
    M  app/services/chat_service.py
    M  app/services/prefs_service.py
    M  app/services/proposal_store.py
    M  requirements.txt
    A  scripts/run_tests.ps1
    A  tests/conftest.py
    A  tests/test_auth_unauthorized_shape.py
    A  tests/test_chat_confirm_missing_proposal.py
    A  tests/test_chat_prefs_propose_confirm.py
    A  tests/test_health.py
    A  tests/test_prefs_defaults_and_upsert.py
    ?? Contracts/phases_0-6.md

## Minimal Diff Hunks
    diff --git a/app/api/deps.py b/app/api/deps.py
    index 7c882f3..ad93ce3 100644
    --- a/app/api/deps.py
    +++ b/app/api/deps.py
    @@ -1,24 +1,17 @@
    -from fastapi import Header, HTTPException, status
    +from fastapi import Header
     
    -from app.schemas import ErrorResponse, UserMe
    +from app.schemas import UserMe
     from app.services.auth_service import get_auth_service
     from app.auth.jwt_verifier import JWTVerificationError, JWTConfigurationError
    +from app.errors import UnauthorizedError
     
     
     def _extract_bearer_token(authorization: str | None) -> str:
         if not authorization:
    -        raise HTTPException(
    -            status_code=status.HTTP_401_UNAUTHORIZED,
    -            detail=ErrorResponse(error="unauthorized", message="Missing Authorization header").model_dump(),
    -            headers={"WWW-Authenticate": "Bearer"},
    -        )
    +        raise UnauthorizedError("Missing Authorization header")
         parts = authorization.split()
         if len(parts) != 2 or parts[0].lower() != "bearer":
    -        raise HTTPException(
    -            status_code=status.HTTP_401_UNAUTHORIZED,
    -            detail=ErrorResponse(error="unauthorized", message="Invalid Authorization header").model_dump(),
    -            headers={"WWW-Authenticate": "Bearer"},
    -        )
    +        raise UnauthorizedError("Invalid Authorization header")
         return parts[1]
     
     
    @@ -30,9 +23,4 @@ def get_current_user(
         try:
             return service.resolve_user(token)
         except (JWTVerificationError, JWTConfigurationError) as exc:
    -        raise HTTPException(
    -            status_code=status.HTTP_401_UNAUTHORIZED,
    -            detail=ErrorResponse(error="unauthorized", message=str(exc)).model_dump(),
    -            headers={"WWW-Authenticate": "Bearer"},
    -        ) from exc
    -
    +        raise UnauthorizedError(str(exc)) from exc
    diff --git a/app/api/routers/auth.py b/app/api/routers/auth.py
    index ed24562..72b90a4 100644
    --- a/app/api/routers/auth.py
    +++ b/app/api/routers/auth.py
    @@ -1,26 +1,19 @@
    -from fastapi import APIRouter, Depends, Header, HTTPException, status
    +from fastapi import APIRouter, Header
     
     from app.schemas import UserMe, ErrorResponse
     from app.services.auth_service import get_auth_service
     from app.auth.jwt_verifier import JWTVerificationError, JWTConfigurationError
    +from app.errors import UnauthorizedError
     
     router = APIRouter(prefix="", tags=["Auth"])
     
     
     def _extract_bearer_token(authorization: str | None) -> str:
         if not authorization:
    -        raise HTTPException(
    -            status_code=status.HTTP_401_UNAUTHORIZED,
    -            detail=ErrorResponse(error="unauthorized", message="Missing Authorization header").model_dump(),
    -            headers={"WWW-Authenticate": "Bearer"},
    -        )
    +        raise UnauthorizedError("Missing Authorization header")
         parts = authorization.split()
         if len(parts) != 2 or parts[0].lower() != "bearer":
    -        raise HTTPException(
    -            status_code=status.HTTP_401_UNAUTHORIZED,
    -            detail=ErrorResponse(error="unauthorized", message="Invalid Authorization header").model_dump(),
    -            headers={"WWW-Authenticate": "Bearer"},
    -        )
    +        raise UnauthorizedError("Invalid Authorization header")
         return parts[1]
     
     
    @@ -37,9 +30,4 @@ def auth_me(
         try:
             return service.resolve_user(token)
         except (JWTVerificationError, JWTConfigurationError) as exc:
    -        raise HTTPException(
    -            status_code=status.HTTP_401_UNAUTHORIZED,
    -            detail=ErrorResponse(error="unauthorized", message=str(exc)).model_dump(),
    -            headers={"WWW-Authenticate": "Bearer"},
    -        ) from exc
    -
    +        raise UnauthorizedError(str(exc)) from exc
    diff --git a/app/api/routers/chat.py b/app/api/routers/chat.py
    index c18d001..804dbd0 100644
    --- a/app/api/routers/chat.py
    +++ b/app/api/routers/chat.py
    @@ -1,4 +1,4 @@
    -from fastapi import APIRouter, Depends, HTTPException, status
    +from fastapi import APIRouter, Depends
     
     from app.api.deps import get_current_user
     from app.schemas import (
    @@ -12,6 +12,7 @@ from app.schemas import (
     from app.services.chat_service import ChatService
     from app.services.prefs_service import get_prefs_service
     from app.services.proposal_store import ProposalStore
    +from app.errors import BadRequestError
     
     router = APIRouter(prefix="", tags=["Chat"])
     
    @@ -46,9 +47,14 @@ def chat_confirm(
     ) -> ConfirmProposalResponse:
         applied = _chat_service.confirm(current_user.user_id, request.proposal_id, request.confirm)
         if not applied and request.confirm:
    -        raise HTTPException(
    -            status_code=status.HTTP_400_BAD_REQUEST,
    -            detail=ErrorResponse(error="bad_request", message="proposal not found").model_dump(),
    -        )
    +        raise BadRequestError("proposal not found")
         return ConfirmProposalResponse(applied=applied, applied_event_ids=[])
     
    +
    +def reset_chat_state_for_tests() -> None:
    +    """
    +    Testing helper: clear proposal store and rebuild chat service with fresh prefs service.
    +    """
    +    global _chat_service
    +    _proposal_store.clear()
    +    _chat_service = ChatService(get_prefs_service(), _proposal_store)
    diff --git a/app/api/routers/prefs.py b/app/api/routers/prefs.py
    index 13e4b91..489ad64 100644
    --- a/app/api/routers/prefs.py
    +++ b/app/api/routers/prefs.py
    @@ -1,8 +1,9 @@
    -from fastapi import APIRouter, Depends, HTTPException, status
    +from fastapi import APIRouter, Depends
     
     from app.api.deps import get_current_user
     from app.schemas import UserPrefs, UserPrefsUpsertRequest, ErrorResponse, UserMe
     from app.services.prefs_service import get_prefs_service
    +from app.errors import BadRequestError
     
     router = APIRouter(prefix="", tags=["Prefs"], dependencies=[])
     
    @@ -32,8 +33,5 @@ def upsert_prefs(
         service = get_prefs_service()
         prefs = request.prefs
         if prefs.servings < 1 or prefs.meals_per_day < 1:
    -        raise HTTPException(
    -            status_code=status.HTTP_400_BAD_REQUEST,
    -            detail=ErrorResponse(error="bad_request", message="servings and meals_per_day must be >= 1").model_dump(),
    -        )
    +        raise BadRequestError("servings and meals_per_day must be >= 1")
         return service.upsert_prefs(current_user.user_id, prefs)
    diff --git a/app/errors.py b/app/errors.py
    new file mode 100644
    index 0000000..4dfa715
    --- /dev/null
    +++ b/app/errors.py
    @@ -0,0 +1,29 @@
    +from fastapi.responses import JSONResponse
    +from fastapi import Request
    +
    +from app.schemas import ErrorResponse
    +
    +
    +class UnauthorizedError(Exception):
    +    def __init__(self, message: str = "unauthorized"):
    +        self.message = message
    +
    +
    +class BadRequestError(Exception):
    +    def __init__(self, message: str = "bad request"):
    +        self.message = message
    +
    +
    +def unauthorized_handler(_request: Request, exc: UnauthorizedError):
    +    return JSONResponse(
    +        status_code=401,
    +        content=ErrorResponse(error="unauthorized", message=exc.message).model_dump(),
    +        headers={"WWW-Authenticate": "Bearer"},
    +    )
    +
    +
    +def bad_request_handler(_request: Request, exc: BadRequestError):
    +    return JSONResponse(
    +        status_code=400,
    +        content=ErrorResponse(error="bad_request", message=exc.message).model_dump(),
    +    )
    diff --git a/app/main.py b/app/main.py
    index f966306..ca0facf 100644
    --- a/app/main.py
    +++ b/app/main.py
    @@ -1,6 +1,7 @@
     from fastapi import FastAPI
     
     from app.api.routers import health, auth, prefs, chat
    +from app.errors import UnauthorizedError, unauthorized_handler, BadRequestError, bad_request_handler
     
     
     def create_app() -> FastAPI:
    @@ -9,6 +10,9 @@ def create_app() -> FastAPI:
         app.include_router(auth.router)
         app.include_router(prefs.router)
         app.include_router(chat.router)
    +
    +    app.add_exception_handler(UnauthorizedError, unauthorized_handler)
    +    app.add_exception_handler(BadRequestError, bad_request_handler)
         return app
     
     
    diff --git a/app/repos/prefs_repo.py b/app/repos/prefs_repo.py
    index d6d7b03..bdfd07b 100644
    --- a/app/repos/prefs_repo.py
    +++ b/app/repos/prefs_repo.py
    @@ -19,3 +19,5 @@ class PrefsRepository:
             self._prefs_by_user[user_id] = prefs
             return prefs
     
    +    def clear(self) -> None:
    +        self._prefs_by_user.clear()
    diff --git a/app/services/chat_service.py b/app/services/chat_service.py
    index cb3d995..f039bea 100644
    --- a/app/services/chat_service.py
    +++ b/app/services/chat_service.py
    @@ -133,10 +133,10 @@ class ChatService:
     
         def _extract_first_int(self, text: str, keywords: List[str]) -> int | None:
             for kw in keywords:
    -            if kw in text:
    -                match = re.search(r"(\d+)", text)
    -                if match:
    -                    return int(match.group(1))
    +            pattern = rf"{kw}[^0-9]*(\d+)"
    +            match = re.search(pattern, text)
    +            if match:
    +                return int(match.group(1))
             return None
     
         def _format_prefs(self, prefs: UserPrefs) -> str:
    diff --git a/app/services/prefs_service.py b/app/services/prefs_service.py
    index fa627ed..d05544c 100644
    --- a/app/services/prefs_service.py
    +++ b/app/services/prefs_service.py
    @@ -28,9 +28,11 @@ class PrefsService:
         def upsert_prefs(self, user_id: str, prefs: UserPrefs) -> UserPrefs:
             return self.repo.upsert_prefs(user_id, prefs)
     
    +    def clear(self) -> None:
    +        self.repo.clear()
    +
     
     @lru_cache(maxsize=1)
     def get_prefs_service() -> PrefsService:
         repo = PrefsRepository()
         return PrefsService(repo)
    -
    diff --git a/app/services/proposal_store.py b/app/services/proposal_store.py
    index e2c5735..32b760d 100644
    --- a/app/services/proposal_store.py
    +++ b/app/services/proposal_store.py
    @@ -47,3 +47,5 @@ class ProposalStore:
             for pid in expired:
                 bucket.pop(pid, None)
     
    +    def clear(self) -> None:
    +        self._data.clear()
    diff --git a/requirements.txt b/requirements.txt
    index 3e09b84..9852232 100644
    --- a/requirements.txt
    +++ b/requirements.txt
    @@ -2,3 +2,4 @@ fastapi>=0.110.0,<0.112.0
     uvicorn>=0.23.0,<0.29.0
     PyJWT[crypto]>=2.8.0
     requests>=2.31.0,<2.33.0
    +pytest>=8.3.0
    diff --git a/scripts/run_tests.ps1 b/scripts/run_tests.ps1
    new file mode 100644
    index 0000000..ac6b565
    --- /dev/null
    +++ b/scripts/run_tests.ps1
    @@ -0,0 +1,40 @@
    +param(
    +  [switch]$NoVenv
    +)
    +
    +Set-StrictMode -Version Latest
    +$ErrorActionPreference = "Stop"
    +
    +function Info($msg) { Write-Host "[run_tests] $msg" -ForegroundColor Cyan }
    +function Err($msg)  { Write-Host "[run_tests] $msg" -ForegroundColor Red }
    +
    +function Resolve-Python {
    +  if (-not $NoVenv) {
    +    $venvPy = Join-Path $PSScriptRoot "..\\..\\LittleChef\\.venv\\Scripts\\python.exe"
    +    $localVenv = Join-Path (Split-Path $PSScriptRoot -Parent) ".venv\\Scripts\\python.exe"
    +    foreach ($path in @($localVenv, $venvPy)) {
    +      if (Test-Path $path) { return $path }
    +    }
    +  }
    +  return "python"
    +}
    +
    +try {
    +  $root = Resolve-Path (Join-Path $PSScriptRoot "..")
    +  Set-Location $root
    +  $py = Resolve-Python
    +  Info "Python: $py"
    +
    +  & $py -m compileall app
    +  Info "compileall app: ok"
    +
    +  & $py -c "import app.main; print('import ok')"
    +  Info "import app.main: ok"
    +
    +  & $py -m pytest -q
    +  Info "pytest: ok"
    +}
    +catch {
    +  Err $_.Exception.Message
    +  exit 1
    +}
    diff --git a/tests/conftest.py b/tests/conftest.py
    new file mode 100644
    index 0000000..e647d02
    --- /dev/null
    +++ b/tests/conftest.py
    @@ -0,0 +1,34 @@
    +import pytest
    +from fastapi.testclient import TestClient
    +
    +from app.main import create_app
    +from app.api.deps import get_current_user
    +from app.schemas import UserMe
    +from app.services.prefs_service import get_prefs_service
    +import app.api.routers.chat as chat_router
    +from app.services.chat_service import ChatService
    +
    +
    +@pytest.fixture
    +def app_instance():
    +    # Reset cached services/state for deterministic tests
    +    get_prefs_service.cache_clear()
    +    chat_router._proposal_store.clear()
    +    chat_router._chat_service = ChatService(get_prefs_service(), chat_router._proposal_store)
    +    return create_app()
    +
    +
    +@pytest.fixture
    +def client(app_instance):
    +    with TestClient(app_instance) as c:
    +        yield c
    +
    +
    +@pytest.fixture
    +def authed_client(app_instance):
    +    app_instance.dependency_overrides[get_current_user] = lambda: UserMe(
    +        user_id="test-user", provider_subject="sub", email=None
    +    )
    +    with TestClient(app_instance) as c:
    +        yield c
    +    app_instance.dependency_overrides.clear()
    diff --git a/tests/test_auth_unauthorized_shape.py b/tests/test_auth_unauthorized_shape.py
    new file mode 100644
    index 0000000..0452ade
    --- /dev/null
    +++ b/tests/test_auth_unauthorized_shape.py
    @@ -0,0 +1,7 @@
    +def test_auth_me_unauthorized_shape(client):
    +    resp = client.get("/auth/me")
    +    assert resp.status_code == 401
    +    body = resp.json()
    +    assert "detail" not in body
    +    assert body["error"] == "unauthorized"
    +    assert "message" in body
    diff --git a/tests/test_chat_confirm_missing_proposal.py b/tests/test_chat_confirm_missing_proposal.py
    new file mode 100644
    index 0000000..b72c39a
    --- /dev/null
    +++ b/tests/test_chat_confirm_missing_proposal.py
    @@ -0,0 +1,9 @@
    +def test_chat_confirm_missing_proposal_returns_400(authed_client):
    +    resp = authed_client.post(
    +        "/chat/confirm",
    +        json={"proposal_id": "missing-id", "confirm": True},
    +    )
    +    assert resp.status_code == 400
    +    body = resp.json()
    +    assert "detail" not in body
    +    assert body["error"] == "bad_request"
    diff --git a/tests/test_chat_prefs_propose_confirm.py b/tests/test_chat_prefs_propose_confirm.py
    new file mode 100644
    index 0000000..0df4a63
    --- /dev/null
    +++ b/tests/test_chat_prefs_propose_confirm.py
    @@ -0,0 +1,31 @@
    +def test_chat_prefs_propose_confirm_flow(authed_client):
    +    # propose
    +    resp = authed_client.post(
    +        "/chat",
    +        json={"mode": "fill", "message": "set servings 4 meals per day 2"},
    +    )
    +    assert resp.status_code == 200
    +    body = resp.json()
    +    assert body["confirmation_required"] is True
    +    assert body["proposal_id"]
    +    assert body["proposed_actions"]
    +    action = body["proposed_actions"][0]
    +    assert action["action_type"] == "upsert_prefs"
    +    assert action["prefs"]["servings"] == 4
    +    assert action["prefs"]["meals_per_day"] == 2
    +
    +    # confirm
    +    proposal_id = body["proposal_id"]
    +    resp = authed_client.post(
    +        "/chat/confirm",
    +        json={"proposal_id": proposal_id, "confirm": True},
    +    )
    +    assert resp.status_code == 200
    +    assert resp.json()["applied"] is True
    +
    +    # prefs reflect change
    +    resp = authed_client.get("/prefs")
    +    assert resp.status_code == 200
    +    prefs = resp.json()
    +    assert prefs["servings"] == 4
    +    assert prefs["meals_per_day"] == 2
    diff --git a/tests/test_health.py b/tests/test_health.py
    new file mode 100644
    index 0000000..35bd6e0
    --- /dev/null
    +++ b/tests/test_health.py
    @@ -0,0 +1,4 @@
    +def test_health(client):
    +    resp = client.get("/health")
    +    assert resp.status_code == 200
    +    assert resp.json() == {"status": "ok"}
    diff --git a/tests/test_prefs_defaults_and_upsert.py b/tests/test_prefs_defaults_and_upsert.py
    new file mode 100644
    index 0000000..3a41a7d
    --- /dev/null
    +++ b/tests/test_prefs_defaults_and_upsert.py
    @@ -0,0 +1,32 @@
    +def test_prefs_defaults_and_upsert(authed_client):
    +    # defaults
    +    resp = authed_client.get("/prefs")
    +    assert resp.status_code == 200
    +    data = resp.json()
    +    assert data["servings"] >= 1
    +    assert data["meals_per_day"] >= 1
    +
    +    # update
    +    new_prefs = {
    +        "prefs": {
    +            "allergies": ["peanuts"],
    +            "dislikes": ["mushrooms"],
    +            "cuisine_likes": ["thai"],
    +            "servings": 3,
    +            "meals_per_day": 2,
    +            "notes": "spicy ok",
    +        }
    +    }
    +    resp = authed_client.put("/prefs", json=new_prefs)
    +    assert resp.status_code == 200
    +    updated = resp.json()
    +    assert updated["servings"] == 3
    +    assert updated["meals_per_day"] == 2
    +    assert updated["allergies"] == ["peanuts"]
    +
    +    # confirm persisted
    +    resp = authed_client.get("/prefs")
    +    assert resp.status_code == 200
    +    again = resp.json()
    +    assert again["servings"] == 3
    +    assert again["meals_per_day"] == 2

## Verification
- compileall app: pass
- import app.main: pass
- pytest -q: pass
- contract: ErrorResponse returned as top-level object for 401/400

## Notes (optional)
- TODO: blockers, risks, constraints.

## Next Steps
- Phase 3: inventory events + summary + low-stock + chat inventory actions

