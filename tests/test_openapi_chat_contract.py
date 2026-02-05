import json
from typing import Dict, Any

import pytest

from app.main import app


EXPECT_CHAT_CONFIRM = True
EXPECT_REQ_FIELDS = {"mode", "message", "include_user_library"}
EXPECT_RESP_FIELDS = {"reply_text", "confirmation_required"}


def resolve_schema(schema: Dict[str, Any], components: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve $ref and allOf for simple object schemas."""
    if "$ref" in schema:
        ref = schema["$ref"]
        name = ref.split("/")[-1]
        return resolve_schema(components["schemas"][name], components)

    # Copy to avoid mutating input
    result: Dict[str, Any] = {}
    # Handle allOf by deep-merging properties/required
    if "allOf" in schema:
        merged_props: Dict[str, Any] = {}
        merged_required = []
        for part in schema["allOf"]:
            resolved = resolve_schema(part, components)
            merged_props.update(resolved.get("properties", {}))
            merged_required.extend(resolved.get("required", []))
        result["type"] = "object"
        if merged_props:
            result["properties"] = merged_props
        if merged_required:
            # preserve order but unique
            seen = set()
            dedup = []
            for r in merged_required:
                if r not in seen:
                    seen.add(r)
                    dedup.append(r)
            result["required"] = dedup
        return result

    # Shallow copy remaining keys
    result.update(schema)
    return result


def test_chat_openapi_contract():
    oas = app.openapi()
    paths = oas.get("paths", {})
    assert "/chat" in paths, "Chat path missing in OpenAPI"
    chat_post = paths["/chat"].get("post")
    assert chat_post, "POST /chat missing"

    components = oas.get("components", {})

    # Resolve request schema
    req_schema = (
        chat_post["requestBody"]["content"]["application/json"]["schema"]
    )
    resolved_req = resolve_schema(req_schema, components)
    actual_req_fields = set(resolved_req.get("properties", {}).keys())
    assert EXPECT_REQ_FIELDS.issubset(
        actual_req_fields
    ), f"Missing expected request fields: {EXPECT_REQ_FIELDS - actual_req_fields}"

    # Resolve response schema
    resp_schema = (
        chat_post["responses"]["200"]["content"]["application/json"]["schema"]
    )
    resolved_resp = resolve_schema(resp_schema, components)
    actual_resp_fields = set(resolved_resp.get("properties", {}).keys())
    assert EXPECT_RESP_FIELDS.issubset(
        actual_resp_fields
    ), f"Missing expected response fields: {EXPECT_RESP_FIELDS - actual_resp_fields}"

    has_confirm = "/chat/confirm" in paths
    assert has_confirm is EXPECT_CHAT_CONFIRM, f"/chat/confirm presence drift: {has_confirm}"


if __name__ == "__main__":
    # Useful for ad-hoc debugging
    print(json.dumps(app.openapi()["paths"]["/chat"], indent=2))
