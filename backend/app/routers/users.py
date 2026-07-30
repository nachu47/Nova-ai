from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import basic_api_key, hash_token
from app.models.entities import APIKey, User
from app.schemas.api import APIKeyCreate, APIKeyCreated, APIKeyOut, Message, UserOut, UserUpdate
from app.services.audit_service import write_audit

router = APIRouter(prefix="/users", tags=["users"])


@router.patch("/me", response_model=UserOut)
def update_me(payload: UserUpdate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    for key, value in payload.model_dump(exclude_unset=True).items(): setattr(user, key, value)
    write_audit(db, action="user.update", entity_type="user", entity_id=user.id, organization_id=user.organization_id, actor_id=user.id, request=request); db.commit(); db.refresh(user); return user


@router.get("/api-keys", response_model=list[APIKeyOut])
def list_api_keys(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(select(APIKey).where(APIKey.user_id == user.id, APIKey.deleted_at.is_(None)).order_by(APIKey.created_at.desc())).all()


@router.post("/api-keys", response_model=APIKeyCreated, status_code=201)
def create_api_key(payload: APIKeyCreate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    prefix, raw = basic_api_key(); record = APIKey(organization_id=user.organization_id, user_id=user.id, name=payload.name, prefix=prefix, key_hash=hash_token(raw), scopes=payload.scopes, expires_at=payload.expires_at)
    db.add(record); db.flush(); write_audit(db, action="api_key.create", entity_type="api_key", entity_id=record.id, organization_id=user.organization_id, actor_id=user.id, request=request); db.commit(); db.refresh(record)
    return APIKeyCreated(**APIKeyOut.model_validate(record).model_dump(), key=raw)


@router.delete("/api-keys/{key_id}", response_model=Message)
def revoke_api_key(key_id: str, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = db.scalar(select(APIKey).where(APIKey.id == key_id, APIKey.user_id == user.id, APIKey.deleted_at.is_(None)))
    if not record: raise HTTPException(status_code=404, detail="API key not found")
    record.is_active = False; record.deleted_at = datetime.now(UTC); write_audit(db, action="api_key.revoke", entity_type="api_key", entity_id=record.id, organization_id=user.organization_id, actor_id=user.id, request=request); db.commit(); return Message(message="API key revoked")
