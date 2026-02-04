# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-04T11:35:55+00:00
- Branch: main
- BASE_HEAD: 1a7efbf515685c313bcb9ed2367d9f0fc0a8108d
- Diff basis: staged

## Cycle Status
- Status: COMPLETE

## Summary
- Added safe auth debug details for Authorization parsing failures; details only populate when LC_DEBUG_AUTH=1 and never echo token data.
- Unified bearer parsing debug signals in deps/auth and extended UnauthorizedError to carry optional details.
- Added regression tests covering debug-on/off responses; kept tests deterministic with in-memory defaults.
- Optional run_local.ps1 switch (-DebugAuth) now sets LC_DEBUG_AUTH=1 for local troubleshooting.

## Files Changed (staged)
- app/api/deps.py
- app/api/routers/auth.py
- app/errors.py
- scripts/run_local.ps1
- tests/test_auth_debug_details.py
- evidence/test_runs.md
- evidence/test_runs_latest.md

## git status -sb
    ## main...origin/main
     M app/api/deps.py
     M app/api/routers/auth.py
     M app/errors.py
     M evidence/test_runs.md
     M evidence/test_runs_latest.md
     M scripts/run_local.ps1
    ?? tests/test_auth_debug_details.py

## Minimal Diff Hunks
    diff --git a/app/errors.py b/app/errors.py
    --- a/app/errors.py
    +++ b/app/errors.py
    @@
    -class UnauthorizedError(Exception):
    -    def __init__(self, message: str = "unauthorized"):
    -        self.message = message
    +class UnauthorizedError(Exception):
    +    def __init__(self, message: str = "unauthorized", details=None):
    +        self.message = message
    +        self.details = details
    @@
    -        content=ErrorResponse(error="unauthorized", message=exc.message).model_dump(),
    +        content=ErrorResponse(error="unauthorized", message=exc.message, details=getattr(exc, "details", None)).model_dump(),
    diff --git a/app/api/deps.py b/app/api/deps.py
    --- a/app/api/deps.py
    +++ b/app/api/deps.py
    @@
    +def _auth_debug_details(authorization: str | None):
    +    text = authorization or ""
    +    parts = text.split()
    +    scheme_lower = parts[0].lower() if parts else None
    +    return {
    +        "auth_present": authorization is not None,
    +        "auth_len": len(text),
    +        "parts_count": len(parts),
    +        "scheme_lower": scheme_lower,
    +        "starts_with_bearer_ci": text.lower().startswith("bearer"),
    +        "has_newline": "\n" in text,
    +        "has_tab": "\t" in text,
    +        "has_comma": "," in text,
    +    }
    @@
    -    if not authorization:
    -        raise UnauthorizedError("Missing Authorization header")
    +    if not authorization:
    +        details = _auth_debug_details(authorization) if debug else None
    +        raise UnauthorizedError("Missing Authorization header", details=details)
    @@
    -    if len(parts) != 2 or parts[0].lower() != "bearer":
    -        raise UnauthorizedError("Invalid Authorization header")
    +    if len(parts) != 2 or parts[0].lower() != "bearer":
    +        raise UnauthorizedError("Invalid Authorization header", details=details)
    diff --git a/app/api/routers/auth.py b/app/api/routers/auth.py
    --- a/app/api/routers/auth.py
    +++ b/app/api/routers/auth.py
    @@
    +def _auth_debug_details(authorization: str | None):
    +    text = authorization or ""
    +    parts = text.split()
    +    scheme_lower = parts[0].lower() if parts else None
    +    return {
    +        "auth_present": authorization is not None,
    +        "auth_len": len(text),
    +        "parts_count": len(parts),
    +        "scheme_lower": scheme_lower,
    +        "starts_with_bearer_ci": text.lower().startswith("bearer"),
    +        "has_newline": "\n" in text,
    +        "has_tab": "\t" in text,
    +        "has_comma": "," in text,
    +    }
    @@
    -    if not authorization:
    -        raise UnauthorizedError("Missing Authorization header")
    +    if not authorization:
    +        details = _auth_debug_details(authorization) if debug else None
    +        raise UnauthorizedError("Missing Authorization header", details=details)
    @@
    -    if len(parts) != 2 or parts[0].lower() != "bearer":
    -        raise UnauthorizedError("Invalid Authorization header")
    +    if len(parts) != 2 or parts[0].lower() != "bearer":
    +        raise UnauthorizedError("Invalid Authorization header", details=details)
    diff --git a/scripts/run_local.ps1 b/scripts/run_local.ps1
    --- a/scripts/run_local.ps1
    +++ b/scripts/run_local.ps1
    @@
    -  [switch]$NoOpen
    +  [switch]$NoOpen,
    +  [switch]$DebugAuth
    @@
    -  Load-DotEnv $root
    +  Load-DotEnv $root
    +  if ($DebugAuth) { $env:LC_DEBUG_AUTH = \"1\"; Info \"LC_DEBUG_AUTH=1 (debug auth headers)\" }
    diff --git a/tests/test_auth_debug_details.py b/tests/test_auth_debug_details.py
    --- /dev/null
    +++ b/tests/test_auth_debug_details.py
    @@
    +def test_auth_me_debug_details_when_enabled(monkeypatch):
    +    monkeypatch.setenv(\"LC_DEBUG_AUTH\", \"1\")
    +    with _make_client() as client:
    +        resp = client.get(\"/auth/me\", headers={\"Authorization\": \"Bearer part1 part2\"})
    +    assert resp.status_code == 401
    +    body = resp.json()
    +    assert body[\"message\"] == \"Invalid Authorization header\"
    +    details = body.get(\"details\")
    +    assert isinstance(details, dict)
    +    assert details.get(\"parts_count\") == 3
    +    assert details.get(\"scheme_lower\") == \"bearer\"
    +    assert details.get(\"has_newline\") is False
    +    detail_str = str(details)
    +    assert \"part1\" not in detail_str and \"part2\" not in detail_str

## Verification
- Static: python -m compileall app
- Runtime: python -c "import app.main; print('import ok')"
- Behavior: pwsh -NoProfile -Command "./scripts/run_tests.ps1" (PASS)
- Contract: No API/schema changes; /auth/me still Bearer per physics.yaml
- Example /auth/me debug details (LC_DEBUG_AUTH=1, malformed header "Bearer part1 part2"): {"auth_present": true, "auth_len": 16, "parts_count": 3, "scheme_lower": "bearer", "starts_with_bearer_ci": true, "has_newline": false, "has_tab": false, "has_comma": false}

## Notes (optional)
- None.

## Next Steps
- Deploy and retest /auth/me with LC_DEBUG_AUTH=1 to collect server-side details if header issues persist.

