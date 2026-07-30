import re
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.security import create_jwt, decode_jwt, hash_password, hash_token, new_random_token, verify_password
from app.models.entities import OneTimeToken, Organization, RefreshToken, User
from app.schemas.api import ForgotPasswordRequest, LoginRequest, Message, RegisterRequest, ResetPasswordRequest, TokenResponse, UserOut
from app.services.audit_service import write_audit
from app.services.email_service import send_email

router = APIRouter(prefix="/auth", tags=["authentication"])


def _slug(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "organisation"
    return f"{base}-{uuid.uuid4().hex[:6]}"


def _set_auth_cookies(response: Response, refresh: str, csrf: str) -> None:
    secure = settings.is_production
    response.set_cookie("nova_refresh", refresh, httponly=True, secure=secure, samesite="lax", max_age=settings.refresh_token_days*86400, path=f"{settings.api_prefix}/auth")
    response.set_cookie("nova_csrf", csrf, httponly=False, secure=secure, samesite="lax", max_age=settings.refresh_token_days*86400, path=f"{settings.api_prefix}/auth")


def _issue_tokens(
    db: Session,
    user: User,
    request: Request,
    response: Response,
    family_id: str | None = None,
    previous_record: RefreshToken | None = None,
) -> TokenResponse:
    access = create_jwt(user.id, "access", timedelta(minutes=settings.access_token_minutes), organization_id=user.organization_id, role=user.role)
    family = family_id or str(uuid.uuid4())
    refresh = create_jwt(user.id, "refresh", timedelta(days=settings.refresh_token_days), organization_id=user.organization_id, family_id=family)
    csrf = new_random_token(24)
    new_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh),
        family_id=family,
        expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    db.add(new_record)
    db.flush()
    if previous_record:
        previous_record.replaced_by_id = new_record.id
    _set_auth_cookies(response, refresh, csrf)
    return TokenResponse(access_token=access, expires_in=settings.access_token_minutes*60, csrf_token=csrf)


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == payload.email.lower())):
        raise HTTPException(status_code=409, detail="Email is already registered")
    org = Organization(name=payload.organization_name, slug=_slug(payload.organization_name), timezone=payload.timezone, currency="GBP")
    db.add(org); db.flush()
    user = User(organization_id=org.id, email=payload.email.lower(), password_hash=hash_password(payload.password), full_name=payload.full_name, role="owner", is_active=True, is_verified=False)
    db.add(user); db.flush()
    raw = new_random_token(); db.add(OneTimeToken(user_id=user.id, purpose="verify_email", token_hash=hash_token(raw), expires_at=datetime.now(UTC)+timedelta(hours=settings.verification_token_hours)))
    token = _issue_tokens(db, user, request, response)
    write_audit(db, action="auth.register", entity_type="user", entity_id=user.id, organization_id=org.id, actor_id=user.id, request=request)
    db.commit()
    send_email(user.email, "Verify your Nova account", f"Verify your email: {settings.frontend_url}/verify-email?token={raw}")
    return token


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower(), User.deleted_at.is_(None)))
    if not user or not verify_password(payload.password, user.password_hash) or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    user.last_login_at = datetime.now(UTC); token = _issue_tokens(db, user, request, response)
    write_audit(db, action="auth.login", entity_type="user", entity_id=user.id, organization_id=user.organization_id, actor_id=user.id, request=request); db.commit(); return token


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: Request, response: Response, x_csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"), db: Session = Depends(get_db)):
    raw = request.cookies.get("nova_refresh"); csrf_cookie = request.cookies.get("nova_csrf")
    if not raw or not csrf_cookie or not x_csrf_token or csrf_cookie != x_csrf_token: raise HTTPException(status_code=403, detail="CSRF validation failed")
    try: payload = decode_jwt(raw, "refresh")
    except jwt.InvalidTokenError as exc: raise HTTPException(status_code=401, detail="Invalid refresh token") from exc
    record = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw)))
    if not record:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    if record.revoked_at:
        # A rotated token was presented again: revoke the full family to contain token theft.
        now = datetime.now(UTC)
        family_tokens = db.scalars(
            select(RefreshToken).where(
                RefreshToken.family_id == record.family_id,
                RefreshToken.revoked_at.is_(None),
            )
        ).all()
        for family_token in family_tokens:
            family_token.revoked_at = now
        db.commit()
        raise HTTPException(status_code=401, detail="Refresh token reuse detected; session revoked")
    expiry = record.expires_at.replace(tzinfo=UTC) if record.expires_at.tzinfo is None else record.expires_at
    if expiry <= datetime.now(UTC):
        raise HTTPException(status_code=401, detail="Refresh token expired")
    user = db.get(User, payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User is inactive")
    record.revoked_at = datetime.now(UTC)
    token = _issue_tokens(
        db, user, request, response, family_id=record.family_id, previous_record=record
    )
    db.commit()
    return token


@router.post("/logout", response_model=Message)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    raw = request.cookies.get("nova_refresh")
    if raw:
        record = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw)))
        if record and not record.revoked_at: record.revoked_at = datetime.now(UTC); db.commit()
    response.delete_cookie("nova_refresh", path=f"{settings.api_prefix}/auth"); response.delete_cookie("nova_csrf", path=f"{settings.api_prefix}/auth")
    return Message(message="Logged out")


@router.get("/verify-email", response_model=Message)
def verify_email(token: str, db: Session = Depends(get_db)):
    record = db.scalar(select(OneTimeToken).where(OneTimeToken.token_hash == hash_token(token), OneTimeToken.purpose == "verify_email", OneTimeToken.used_at.is_(None)))
    if not record: raise HTTPException(status_code=400, detail="Invalid verification token")
    expiry = record.expires_at.replace(tzinfo=UTC) if record.expires_at.tzinfo is None else record.expires_at
    if expiry <= datetime.now(UTC): raise HTTPException(status_code=400, detail="Verification token expired")
    user = db.get(User, record.user_id); user.is_verified = True; record.used_at = datetime.now(UTC); db.commit(); return Message(message="Email verified")


@router.post("/forgot-password", response_model=Message)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower(), User.is_active.is_(True)))
    if user:
        raw = new_random_token(); db.add(OneTimeToken(user_id=user.id, purpose="reset_password", token_hash=hash_token(raw), expires_at=datetime.now(UTC)+timedelta(minutes=settings.reset_token_minutes))); db.commit()
        send_email(user.email, "Reset your Nova password", f"Reset your password: {settings.frontend_url}/reset-password?token={raw}")
    return Message(message="If the account exists, a reset email has been sent")


@router.post("/reset-password", response_model=Message)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    record = db.scalar(select(OneTimeToken).where(OneTimeToken.token_hash == hash_token(payload.token), OneTimeToken.purpose == "reset_password", OneTimeToken.used_at.is_(None)))
    if not record: raise HTTPException(status_code=400, detail="Invalid reset token")
    expiry = record.expires_at.replace(tzinfo=UTC) if record.expires_at.tzinfo is None else record.expires_at
    if expiry <= datetime.now(UTC): raise HTTPException(status_code=400, detail="Reset token expired")
    user = db.get(User, record.user_id); user.password_hash = hash_password(payload.password); record.used_at = datetime.now(UTC)
    for refresh_token in db.scalars(select(RefreshToken).where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))).all(): refresh_token.revoked_at = datetime.now(UTC)
    db.commit(); return Message(message="Password reset successfully")


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)): return user
