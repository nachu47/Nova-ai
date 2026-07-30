from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decrypt_secret, encrypt_secret
from app.models.entities import Integration

PROVIDERS = {
    "google": {
        "authorize": "https://accounts.google.com/o/oauth2/v2/auth",
        "token": "https://oauth2.googleapis.com/token",
        "client_id": lambda: settings.oauth_google_client_id,
        "client_secret": lambda: settings.oauth_google_client_secret,
        "scopes": ["openid", "email", "profile", "https://www.googleapis.com/auth/calendar", "https://www.googleapis.com/auth/contacts.readonly", "https://www.googleapis.com/auth/gmail.send"],
    },
    "microsoft": {
        "authorize": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "client_id": lambda: settings.oauth_microsoft_client_id,
        "client_secret": lambda: settings.oauth_microsoft_client_secret,
        "scopes": ["openid", "email", "profile", "offline_access", "Calendars.ReadWrite", "Contacts.Read", "Mail.Send"],
    },
    "slack": {
        "authorize": "https://slack.com/oauth/v2/authorize",
        "token": "https://slack.com/api/oauth.v2.access",
        "client_id": lambda: settings.oauth_slack_client_id,
        "client_secret": lambda: settings.oauth_slack_client_secret,
        "scopes": ["chat:write", "channels:read", "users:read", "users:read.email"],
    },
    "hubspot": {
        "authorize": "https://app.hubspot.com/oauth/authorize",
        "token": "https://api.hubapi.com/oauth/v1/token",
        "client_id": lambda: settings.oauth_hubspot_client_id,
        "client_secret": lambda: settings.oauth_hubspot_client_secret,
        "scopes": ["crm.objects.contacts.read", "crm.objects.contacts.write", "crm.objects.companies.read", "crm.objects.deals.read"],
    },
    "salesforce": {
        "authorize": "https://login.salesforce.com/services/oauth2/authorize",
        "token": "https://login.salesforce.com/services/oauth2/token",
        "client_id": lambda: settings.oauth_salesforce_client_id,
        "client_secret": lambda: settings.oauth_salesforce_client_secret,
        "scopes": ["api", "refresh_token", "openid", "email"],
    },
}


def provider_config(provider: str) -> dict:
    if provider not in PROVIDERS:
        raise ValueError("Unsupported integration provider")
    config = PROVIDERS[provider]
    if not config["client_id"]() or not config["client_secret"]():
        raise ValueError(f"OAuth credentials are not configured for {provider}")
    return config


def authorization_url(provider: str, state: str, redirect_uri: str) -> str:
    config = provider_config(provider)
    query = {
        "client_id": config["client_id"](), "redirect_uri": redirect_uri, "response_type": "code",
        "scope": " ".join(config["scopes"]), "state": state, "access_type": "offline", "prompt": "consent",
    }
    return f"{config['authorize']}?{urlencode(query)}"


def exchange_code(provider: str, code: str, redirect_uri: str) -> dict:
    config = provider_config(provider)
    data = {"client_id": config["client_id"](), "client_secret": config["client_secret"](), "code": code, "redirect_uri": redirect_uri, "grant_type": "authorization_code"}
    with httpx.Client(timeout=30) as client:
        response = client.post(config["token"], data=data, headers={"Accept": "application/json"})
        response.raise_for_status()
        token = response.json()
    if "access_token" not in token:
        raise ValueError(token.get("error_description") or token.get("error") or "OAuth exchange failed")
    return token


def save_integration(db: Session, organization_id: str, user_id: str, provider: str, token: dict) -> Integration:
    account_email = token.get("email", "default")
    existing = db.scalar(select(Integration).where(Integration.organization_id == organization_id, Integration.provider == provider, Integration.account_email == account_email, Integration.deleted_at.is_(None)))
    values = {
        "encrypted_access_token": encrypt_secret(token["access_token"]),
        "encrypted_refresh_token": (
            encrypt_secret(token["refresh_token"])
            if token.get("refresh_token")
            else (existing.encrypted_refresh_token if existing else None)
        ),
        "token_expires_at": datetime.now(UTC) + timedelta(seconds=int(token.get("expires_in", 3600))),
        "scopes": str(token.get("scope", "")).split(),
        "config": {k: token[k] for k in ("instance_url", "team_id", "hub_id") if k in token},
        "is_active": True,
    }
    if existing:
        for key, value in values.items(): setattr(existing, key, value)
        integration = existing
    else:
        integration = Integration(organization_id=organization_id, user_id=user_id, provider=provider, account_email=account_email, **values)
        db.add(integration)
    db.commit(); db.refresh(integration)
    return integration



def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


def refresh_integration_token(db: Session, integration: Integration) -> str:
    """Return a valid access token, refreshing it before expiry when possible."""
    expiry = _aware(integration.token_expires_at)
    current = decrypt_secret(integration.encrypted_access_token)
    if not expiry or expiry > datetime.now(UTC) + timedelta(seconds=60):
        return current
    if not integration.encrypted_refresh_token:
        integration.is_active = False
        db.commit()
        raise ValueError("Integration access token expired and no refresh token is available")

    config = provider_config(integration.provider)
    payload = {
        "client_id": config["client_id"](),
        "client_secret": config["client_secret"](),
        "refresh_token": decrypt_secret(integration.encrypted_refresh_token),
        "grant_type": "refresh_token",
    }
    with httpx.Client(timeout=30) as client:
        response = client.post(config["token"], data=payload, headers={"Accept": "application/json"})
        response.raise_for_status()
        token = response.json()
    if "access_token" not in token:
        raise ValueError(token.get("error_description") or token.get("error") or "OAuth refresh failed")

    integration.encrypted_access_token = encrypt_secret(token["access_token"])
    if token.get("refresh_token"):
        integration.encrypted_refresh_token = encrypt_secret(token["refresh_token"])
    integration.token_expires_at = datetime.now(UTC) + timedelta(seconds=int(token.get("expires_in", 3600)))
    if token.get("scope"):
        integration.scopes = str(token["scope"]).split()
    if token.get("instance_url"):
        integration.config = {**(integration.config or {}), "instance_url": token["instance_url"]}
    db.commit()
    return token["access_token"]

def integration_request(db: Session, integration_id: str, method: str, url: str, json: dict | None = None) -> dict:
    integration = db.get(Integration, integration_id)
    if not integration or not integration.is_active or integration.deleted_at is not None:
        raise ValueError("Integration not found or inactive")
    token = refresh_integration_token(db, integration)
    with httpx.Client(timeout=30) as client:
        response = client.request(method, url, headers={"Authorization": f"Bearer {token}"}, json=json)
        response.raise_for_status()
        return response.json() if response.content else {"status": "ok"}
