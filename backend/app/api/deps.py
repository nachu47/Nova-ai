from collections.abc import Generator
from datetime import UTC, datetime

import jwt
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_jwt, hash_token
from app.database.session import SessionLocal
from app.models.entities import APIKey, User

bearer = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _api_key_user(db: Session, raw_key: str) -> tuple[User, set[str]] | None:
    if "." not in raw_key:
        return None
    prefix = raw_key.split(".", 1)[0]
    record = db.scalar(
        select(APIKey).where(APIKey.prefix == prefix, APIKey.deleted_at.is_(None), APIKey.is_active.is_(True))
    )
    if not record or record.key_hash != hash_token(raw_key):
        return None
    if record.expires_at and record.expires_at <= datetime.now(UTC):
        return None
    record.last_used_at = datetime.now(UTC)
    user = db.get(User, record.user_id)
    db.commit()
    return (user, set(record.scopes or [])) if user else None


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> User:
    user: User | None = None
    if x_api_key:
        api_principal = _api_key_user(db, x_api_key)
        if api_principal:
            user, scopes = api_principal
            required_scope = "read" if request.method in {"GET", "HEAD", "OPTIONS"} else "write"
            if "*" not in scopes and required_scope not in scopes:
                raise HTTPException(status_code=403, detail=f"API key requires the {required_scope} scope")
            request.state.api_key_scopes = sorted(scopes)
    elif credentials:
        try:
            payload = decode_jwt(credentials.credentials, "access")
            user = db.get(User, payload["sub"])
        except (jwt.InvalidTokenError, KeyError):
            user = None
    if not user or not user.is_active or user.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication")
    request.state.user_id = user.id
    request.state.organization_id = user.organization_id
    return user


def require_roles(*roles: str):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dependency


def org_record_or_404(db: Session, model, record_id: str, organization_id: str):
    record = db.scalar(
        select(model).where(model.id == record_id, model.organization_id == organization_id, model.deleted_at.is_(None))
    )
    if not record:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return record
