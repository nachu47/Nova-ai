from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from typing import Any

from app.api.deps import get_current_user, get_db
from app.models.entities import User
from app.services.settings_service import get_all_settings, set_setting

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("/")
def read_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all settings for the organization"""
    settings_dict = get_all_settings(db, current_user.organization_id)
    return settings_dict

@router.put("/{key}")
def update_setting(
    key: str,
    payload: Any = Body(...),
    is_secret: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a specific setting for the organization"""
    setting = set_setting(
        session=db,
        organization_id=current_user.organization_id,
        key=key,
        value=payload,
        is_secret=is_secret,
        user_id=current_user.id
    )
    
    # Return masked value if secret
    if setting.is_secret:
        return {"key": setting.key, "value": {"secret": "********"}, "is_secret": setting.is_secret}
    return {"key": setting.key, "value": setting.value, "is_secret": setting.is_secret}
