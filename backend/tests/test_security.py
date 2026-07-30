def test_refresh_rotation_reuse_revokes_family(client):
    created = client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": "Secure Ltd",
            "full_name": "Security Owner",
            "email": "security@example.com",
            "password": "VeryStrongPass123!",
            "timezone": "UTC",
        },
    )
    assert created.status_code == 201
    old_refresh = client.cookies.get("nova_refresh")
    first_csrf = created.json()["csrf_token"]

    rotated = client.post("/api/v1/auth/refresh", headers={"X-CSRF-Token": first_csrf})
    assert rotated.status_code == 200
    new_refresh = client.cookies.get("nova_refresh")
    new_csrf = rotated.json()["csrf_token"]
    assert old_refresh != new_refresh

    client.cookies.set("nova_refresh", old_refresh, path="/api/v1/auth")
    replay = client.post("/api/v1/auth/refresh", headers={"X-CSRF-Token": new_csrf})
    assert replay.status_code == 401
    assert "reuse detected" in replay.json()["detail"].lower()

    client.cookies.set("nova_refresh", new_refresh, path="/api/v1/auth")
    revoked_family = client.post("/api/v1/auth/refresh", headers={"X-CSRF-Token": new_csrf})
    assert revoked_family.status_code == 401


def test_api_key_scopes_are_enforced(client, auth_headers):
    created = client.post(
        "/api/v1/users/api-keys",
        headers=auth_headers,
        json={"name": "Read-only automation", "scopes": ["read"]},
    )
    assert created.status_code == 201, created.text
    key = created.json()["key"]
    api_headers = {"X-API-Key": key}

    me = client.get("/api/v1/auth/me", headers=api_headers)
    assert me.status_code == 200

    denied = client.post(
        "/api/v1/agents",
        headers=api_headers,
        json={
            "name": "Blocked Agent",
            "system_prompt": "This request must be blocked because the API key is read only.",
        },
    )
    assert denied.status_code == 403
    assert "write scope" in denied.json()["detail"].lower()


def test_outbound_url_policy_blocks_private_targets():
    from app.utils.network import UnsafeOutboundURL, validate_outbound_url

    try:
        validate_outbound_url(
            "https://127.0.0.1/internal",
            require_https=True,
            allow_private=False,
        )
    except UnsafeOutboundURL:
        pass
    else:
        raise AssertionError("Private outbound addresses must be rejected")
