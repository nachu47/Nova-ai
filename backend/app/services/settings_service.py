from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decrypt_secret, encrypt_secret
from app.models.entities import SystemSetting

def get_setting(session: Session, organization_id: str, key: str) -> dict | None:
    stmt = select(SystemSetting).where(
        SystemSetting.organization_id == organization_id,
        SystemSetting.key == key
    )
    setting = session.scalar(stmt)
    
    if not setting:
        return None
        
    if setting.is_secret:
        encrypted_val = setting.value.get("secret")
        if encrypted_val:
            try:
                decrypted = decrypt_secret(encrypted_val)
                return {"secret": decrypted}
            except Exception:
                return setting.value
    return setting.value

def set_setting(
    session: Session, 
    organization_id: str, 
    key: str, 
    value: dict, 
    is_secret: bool = False,
    user_id: str | None = None
) -> SystemSetting:
    stmt = select(SystemSetting).where(
        SystemSetting.organization_id == organization_id,
        SystemSetting.key == key
    )
    setting = session.scalar(stmt)
    
    store_value = value
    if is_secret:
        raw_secret = value.get("secret")
        if raw_secret and raw_secret != "********":
            store_value = {"secret": encrypt_secret(raw_secret)}
        elif setting and raw_secret == "********":
            store_value = setting.value

    if setting:
        setting.value = store_value
        setting.is_secret = is_secret
        if user_id:
            setting.updated_by_id = user_id
    else:
        if is_secret and store_value.get("secret") == "********":
            raise ValueError("Cannot save masked secret value for a new setting.")
            
        setting = SystemSetting(
            organization_id=organization_id,
            key=key,
            value=store_value,
            is_secret=is_secret,
            updated_by_id=user_id
        )
        session.add(setting)
        
    session.commit()
    session.refresh(setting)
    return setting

def get_all_settings(session: Session, organization_id: str) -> dict[str, dict]:
    stmt = select(SystemSetting).where(SystemSetting.organization_id == organization_id)
    settings_records = session.scalars(stmt).all()
    
    out = {}
    for s in settings_records:
        if s.is_secret:
            out[s.key] = {"secret": "********"}
        else:
            out[s.key] = s.value
            
    return out
