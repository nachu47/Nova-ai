import json
from datetime import UTC,datetime

from fastapi import APIRouter,Depends,HTTPException,Query,Request
from sqlalchemy import func,select
from sqlalchemy.orm import Session

from app.api.deps import get_db,require_roles
from app.core.security import encrypt_secret, hash_password
from app.models.entities import APIKey,AuditLog,Call,Organization,SystemSetting,UsageRecord,User,VoiceAgent
from app.schemas.api import AdminUserUpdate,AgentOut,CallOut,Message,SystemSettingUpsert,UsageCreate,UserOut
from app.services.audit_service import write_audit

router=APIRouter(prefix="/admin",tags=["admin"])
AdminUser=Depends(require_roles("owner","admin","superadmin"))


@router.get("/users",response_model=list[UserOut])
def users(admin:User=AdminUser,db:Session=Depends(get_db)):return db.scalars(select(User).where(User.organization_id==admin.organization_id,User.deleted_at.is_(None)).order_by(User.created_at.desc())).all()


@router.patch("/users/{user_id}",response_model=UserOut)
def update_user(user_id:str,payload:AdminUserUpdate,request:Request,admin:User=AdminUser,db:Session=Depends(get_db)):
    user=db.scalar(select(User).where(User.id==user_id,User.organization_id==admin.organization_id,User.deleted_at.is_(None)))
    if not user:raise HTTPException(status_code=404,detail="User not found")
    if user.id==admin.id and payload.is_active is False:raise HTTPException(status_code=409,detail="You cannot deactivate your own account")
    changes=payload.model_dump(exclude_unset=True)
    if "role" in changes:
        new_role = changes["role"]
        if new_role not in {"owner","admin","member","viewer","superadmin"}:raise HTTPException(status_code=422,detail="Invalid role")
        if new_role == "superadmin" and admin.role != "superadmin":raise HTTPException(status_code=403,detail="Only a Super Admin can grant the superadmin role")
        if user.role == "superadmin" and admin.role != "superadmin":raise HTTPException(status_code=403,detail="Only a Super Admin can modify a superadmin account")
    for key,value in changes.items():setattr(user,key,value)
    write_audit(db,action="admin.user.update",entity_type="user",entity_id=user.id,organization_id=admin.organization_id,actor_id=admin.id,request=request,after=changes);db.commit();db.refresh(user);return user


@router.get("/calls")
def calls(page:int=Query(1,ge=1),page_size:int=Query(50,ge=1,le=200),admin:User=AdminUser,db:Session=Depends(get_db)):
    conditions=[Call.organization_id==admin.organization_id,Call.deleted_at.is_(None)];total=db.scalar(select(func.count(Call.id)).where(*conditions)) or 0;items=db.scalars(select(Call).where(*conditions).order_by(Call.created_at.desc()).offset((page-1)*page_size).limit(page_size)).all();return {"total":total,"items":[CallOut.model_validate(x).model_dump(mode="json") for x in items]}


@router.get("/agents",response_model=list[AgentOut])
def agents(admin:User=AdminUser,db:Session=Depends(get_db)):return db.scalars(select(VoiceAgent).where(VoiceAgent.organization_id==admin.organization_id,VoiceAgent.deleted_at.is_(None)).order_by(VoiceAgent.created_at.desc())).all()


@router.get("/api-keys")
def api_keys(admin:User=AdminUser,db:Session=Depends(get_db)):
    rows=db.execute(select(APIKey,User.email).join(User,User.id==APIKey.user_id).where(APIKey.organization_id==admin.organization_id,APIKey.deleted_at.is_(None)).order_by(APIKey.created_at.desc())).all();return [{"id":key.id,"name":key.name,"prefix":key.prefix,"owner_email":email,"scopes":key.scopes,"is_active":key.is_active,"last_used_at":key.last_used_at,"created_at":key.created_at} for key,email in rows]


@router.post("/api-keys/{key_id}/deactivate",response_model=Message)
def deactivate_api_key(key_id:str,admin:User=AdminUser,db:Session=Depends(get_db)):
    key=db.scalar(select(APIKey).where(APIKey.id==key_id,APIKey.organization_id==admin.organization_id,APIKey.deleted_at.is_(None)))
    if not key:raise HTTPException(status_code=404,detail="API key not found")
    key.is_active=False;db.commit();return Message(message="API key deactivated")


@router.get("/usage")
def usage(metric:str|None=None,admin:User=AdminUser,db:Session=Depends(get_db)):
    conditions=[UsageRecord.organization_id==admin.organization_id]
    if metric:conditions.append(UsageRecord.metric==metric)
    rows=db.scalars(select(UsageRecord).where(*conditions).order_by(UsageRecord.period_start.desc()).limit(500)).all();return [{"id":x.id,"metric":x.metric,"quantity":float(x.quantity),"unit":x.unit,"unit_price":float(x.unit_price),"amount":float(x.amount),"period_start":x.period_start,"period_end":x.period_end,"call_id":x.call_id} for x in rows]


@router.post("/usage",status_code=201)
def create_usage(payload:UsageCreate,admin:User=AdminUser,db:Session=Depends(get_db)):
    if payload.organization_id!=admin.organization_id:raise HTTPException(status_code=403,detail="Cannot create usage for another organisation")
    record=UsageRecord(organization_id=payload.organization_id,user_id=payload.user_id,call_id=payload.call_id,metric=payload.metric,quantity=payload.quantity,unit=payload.unit,unit_price=payload.unit_price,amount=payload.quantity*payload.unit_price,period_start=payload.period_start,period_end=payload.period_end,metadata_json=payload.metadata);db.add(record);db.commit();db.refresh(record);return {"id":record.id,"amount":float(record.amount)}


@router.get("/settings")
def settings(admin:User=AdminUser,db:Session=Depends(get_db)):
    rows=db.scalars(select(SystemSetting).where(SystemSetting.organization_id==admin.organization_id).order_by(SystemSetting.key)).all();return [{"key":x.key,"value":{"masked":True} if x.is_secret else x.value,"is_secret":x.is_secret,"updated_at":x.updated_at} for x in rows]


@router.put("/settings/{key}")
def upsert_setting(key:str,payload:SystemSettingUpsert,request:Request,admin:User=AdminUser,db:Session=Depends(get_db)):
    if len(key)>120:raise HTTPException(status_code=422,detail="Setting key is too long")
    record=db.scalar(select(SystemSetting).where(SystemSetting.organization_id==admin.organization_id,SystemSetting.key==key));stored={"ciphertext":encrypt_secret(json.dumps(payload.value))} if payload.is_secret else payload.value
    if record:record.value=stored;record.is_secret=payload.is_secret;record.updated_by_id=admin.id
    else:record=SystemSetting(organization_id=admin.organization_id,key=key,value=stored,is_secret=payload.is_secret,updated_by_id=admin.id);db.add(record)
    write_audit(db,action="admin.setting.upsert",entity_type="system_setting",entity_id=record.id,organization_id=admin.organization_id,actor_id=admin.id,request=request,after={"key":key,"is_secret":payload.is_secret});db.commit();return {"key":key,"updated":True}


@router.get("/audit-logs")
def audit_logs(limit:int=Query(100,ge=1,le=500),admin:User=AdminUser,db:Session=Depends(get_db)):
    rows=db.scalars(select(AuditLog).where(AuditLog.organization_id==admin.organization_id).order_by(AuditLog.created_at.desc()).limit(limit)).all();return [{"id":x.id,"action":x.action,"entity_type":x.entity_type,"entity_id":x.entity_id,"actor_id":x.actor_id,"request_id":x.request_id,"created_at":x.created_at} for x in rows]


@router.get("/platform")
def platform(admin:User=AdminUser,db:Session=Depends(get_db)):
    if admin.role == "superadmin":
        write_audit(db,action="SUPERADMIN_VIEW_PLATFORM",entity_type="platform",entity_id="global",organization_id=admin.organization_id,actor_id=admin.id,request=None,after=None)
        db.commit()
        today = datetime.now(UTC).date()
        today_dt = datetime(today.year, today.month, today.day, tzinfo=UTC)
        return {
            "organizations": db.scalar(select(func.count(Organization.id)).where(Organization.deleted_at.is_(None))) or 0,
            "users": db.scalar(select(func.count(User.id)).where(User.deleted_at.is_(None))) or 0,
            "voice_agents": db.scalar(select(func.count(VoiceAgent.id)).where(VoiceAgent.deleted_at.is_(None))) or 0,
            "calls": db.scalar(select(func.count(Call.id)).where(Call.deleted_at.is_(None))) or 0,
            "calls_today": db.scalar(select(func.count(Call.id)).where(Call.deleted_at.is_(None), Call.created_at >= today_dt)) or 0,
            "usage_revenue": float(db.scalar(select(func.coalesce(func.sum(UsageRecord.amount),0))) or 0),
            "active_organizations": 1,
            "platform_health": "operational"
        }
    return {"organizations":1,"users":db.scalar(select(func.count(User.id)).where(User.organization_id==admin.organization_id,User.deleted_at.is_(None))) or 0,"calls":db.scalar(select(func.count(Call.id)).where(Call.organization_id==admin.organization_id,Call.deleted_at.is_(None))) or 0,"usage_revenue":float(db.scalar(select(func.coalesce(func.sum(UsageRecord.amount),0)).where(UsageRecord.organization_id==admin.organization_id)) or 0)}


@router.get("/organizations")
def organizations(admin:User=AdminUser,db:Session=Depends(get_db)):
    if admin.role != "superadmin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    orgs = db.scalars(select(Organization).where(Organization.deleted_at.is_(None)).order_by(Organization.created_at.desc())).all()
    results = []
    for org in orgs:
        users_count = db.scalar(select(func.count(User.id)).where(User.organization_id==org.id, User.deleted_at.is_(None))) or 0
        agents_count = db.scalar(select(func.count(VoiceAgent.id)).where(VoiceAgent.organization_id==org.id, VoiceAgent.deleted_at.is_(None))) or 0
        calls_count = db.scalar(select(func.count(Call.id)).where(Call.organization_id==org.id, Call.deleted_at.is_(None))) or 0
        usage = db.scalar(select(func.coalesce(func.sum(UsageRecord.amount), 0)).where(UsageRecord.organization_id==org.id)) or 0
        owner = db.scalar(select(User).where(User.organization_id==org.id, User.deleted_at.is_(None)).order_by(User.created_at.asc()))
        results.append({
            "id": org.id,
            "name": org.name,
            "plan": org.plan,
            "owner_email": owner.email if owner else "N/A",
            "owner_name": owner.full_name if owner else "N/A",
            "owner_role": owner.role if owner else "N/A",
            "users": users_count,
            "voice_agents": agents_count,
            "calls": calls_count,
            "usage": float(usage),
            "created_at": org.created_at
        })
    return results

@router.post("/organizations")
def create_organization(payload:dict, admin:User=AdminUser, db:Session=Depends(get_db)):
    if admin.role != "superadmin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    name = payload.get("name", "").strip()
    plan = payload.get("plan", "starter")
    if not name:
        raise HTTPException(status_code=422, detail="Organization name is required")
    slug = name.lower().replace(" ", "-") + "-" + str(int(datetime.now(UTC).timestamp()))
    org = Organization(name=name, slug=slug, plan=plan)
    db.add(org)
    db.commit()
    db.refresh(org)
    write_audit(db, action="SUPERADMIN_CREATE_ORG", entity_type="organization", entity_id=org.id, organization_id=org.id, actor_id=admin.id, request=None, after={"name": name, "plan": plan})
    db.commit()
    return {"id": org.id, "name": org.name, "plan": org.plan}



@router.get("/global-users")
def global_users(admin:User=AdminUser,db:Session=Depends(get_db)):
    if admin.role != "superadmin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    users = db.scalars(select(User).where(User.deleted_at.is_(None)).order_by(User.created_at.desc())).all()
    results = []
    for u in users:
        org = db.get(Organization, u.organization_id)
        u_dict = UserOut.model_validate(u).model_dump(mode="json")
        u_dict["organization_name"] = org.name if org else "Unknown"
        results.append(u_dict)
    return results

@router.post("/global-users", response_model=UserOut)
def create_global_user(payload:dict, admin:User=AdminUser, db:Session=Depends(get_db)):
    if admin.role != "superadmin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    email = payload.get("email", "").lower().strip()
    full_name = payload.get("full_name", "").strip()
    password = payload.get("password", "")
    role = payload.get("role", "member")
    org_id = payload.get("organization_id")
    
    if not email or not full_name or not password:
        raise HTTPException(status_code=422, detail="Email, full name, and password are required")
    if role not in {"owner", "admin", "member", "viewer", "superadmin"}:
        raise HTTPException(status_code=422, detail="Invalid role")
    
    if not org_id:
        org_id = admin.organization_id
        
    org = db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Selected organization not found")
        
    existing = db.scalar(select(User).where(User.organization_id == org_id, User.email == email, User.deleted_at.is_(None)))
    if existing:
        raise HTTPException(status_code=409, detail="User with this email already exists in this organization")
        
    user = User(
        organization_id=org_id,
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        role=role,
        is_active=True,
        is_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    write_audit(db, action="SUPERADMIN_CREATE_USER", entity_type="user", entity_id=user.id, organization_id=org_id, actor_id=admin.id, request=None, after={"email": email, "role": role})
    db.commit()
    return user

@router.patch("/global-users/{user_id}", response_model=UserOut)
def update_global_user(user_id:str, payload:dict, admin:User=AdminUser, db:Session=Depends(get_db)):
    if admin.role != "superadmin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    user = db.scalar(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if "is_active" in payload:
        user.is_active = bool(payload["is_active"])
    if "role" in payload:
        new_role = payload["role"]
        if new_role in {"owner", "admin", "member", "viewer", "superadmin"}:
            user.role = new_role
    if "full_name" in payload:
        user.full_name = payload["full_name"]
    db.commit()
    db.refresh(user)
    return user

@router.delete("/global-users/{user_id}")
def delete_global_user(user_id:str, admin:User=AdminUser, db:Session=Depends(get_db)):
    if admin.role != "superadmin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own superadmin account")
    user = db.scalar(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.deleted_at = func.now()
    write_audit(db, action="SUPERADMIN_DELETE_USER", entity_type="user", entity_id=user.id, organization_id=user.organization_id, actor_id=admin.id, request=None, after={"email": user.email})
    db.commit()
    return {"message": f"User '{user.full_name}' deleted successfully"}

@router.delete("/organizations/{org_id}")
def delete_organization(org_id:str, admin:User=AdminUser, db:Session=Depends(get_db)):
    if admin.role != "superadmin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    org = db.get(Organization, org_id)
    if not org or org.deleted_at:
        raise HTTPException(status_code=404, detail="Organization not found")
    org.deleted_at = func.now()
    write_audit(db, action="SUPERADMIN_DELETE_ORG", entity_type="organization", entity_id=org.id, organization_id=org.id, actor_id=admin.id, request=None, after={"name": org.name})
    db.commit()
    return {"message": f"Organization '{org.name}' deleted successfully"}



@router.get("/global-agents")
def global_agents(admin:User=AdminUser,db:Session=Depends(get_db)):
    if admin.role != "superadmin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    agents = db.scalars(select(VoiceAgent).where(VoiceAgent.deleted_at.is_(None)).order_by(VoiceAgent.created_at.desc())).all()
    results = []
    for a in agents:
        org = db.get(Organization, a.organization_id)
        a_dict = AgentOut.model_validate(a).model_dump(mode="json")
        a_dict["organization_name"] = org.name if org else "Unknown"
        results.append(a_dict)
    return results

@router.get("/global-calls")
def global_calls(page:int=Query(1,ge=1),page_size:int=Query(50,ge=1,le=200),admin:User=AdminUser,db:Session=Depends(get_db)):
    if admin.role != "superadmin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    total=db.scalar(select(func.count(Call.id)).where(Call.deleted_at.is_(None))) or 0
    items=db.scalars(select(Call).where(Call.deleted_at.is_(None)).order_by(Call.created_at.desc()).offset((page-1)*page_size).limit(page_size)).all()
    results = []
    for c in items:
        org = db.get(Organization, c.organization_id)
        c_dict = CallOut.model_validate(c).model_dump(mode="json")
        c_dict["organization_name"] = org.name if org else "Unknown"
        results.append(c_dict)
    return {"total":total,"items":results}

@router.post("/organizations/{org_id}/suspend")
def suspend_organization(org_id:str,admin:User=AdminUser,db:Session=Depends(get_db)):
    if admin.role != "superadmin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    org = db.get(Organization, org_id)
    if not org or org.deleted_at:
        raise HTTPException(status_code=404, detail="Organization not found")
    org.plan = "suspended"
    write_audit(db, action="SUPERADMIN_SUSPEND_ORG", entity_type="organization", entity_id=org.id, organization_id=org.id, actor_id=admin.id, request=None, after={"plan": "suspended"})
    db.commit()
    return {"message": f"Organization '{org.name}' suspended successfully"}

@router.post("/organizations/{org_id}/activate")
def activate_organization(org_id:str,admin:User=AdminUser,db:Session=Depends(get_db)):
    if admin.role != "superadmin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    org = db.get(Organization, org_id)
    if not org or org.deleted_at:
        raise HTTPException(status_code=404, detail="Organization not found")
    org.plan = "starter"
    write_audit(db, action="SUPERADMIN_ACTIVATE_ORG", entity_type="organization", entity_id=org.id, organization_id=org.id, actor_id=admin.id, request=None, after={"plan": "starter"})
    db.commit()
    return {"message": f"Organization '{org.name}' activated successfully"}

@router.patch("/organizations/{org_id}/plan")
def update_organization_plan(org_id:str,payload:dict,admin:User=AdminUser,db:Session=Depends(get_db)):
    if admin.role != "superadmin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    org = db.get(Organization, org_id)
    if not org or org.deleted_at:
        raise HTTPException(status_code=404, detail="Organization not found")
    if "plan" in payload:
        org.plan = payload["plan"]
    if "voice_credits_seconds" in payload:
        org.voice_credits_seconds = int(payload["voice_credits_seconds"])
    write_audit(db, action="SUPERADMIN_UPDATE_ORG_PLAN", entity_type="organization", entity_id=org.id, organization_id=org.id, actor_id=admin.id, request=None, after=payload)
    db.commit()
    return {"message": "Organization plan updated", "plan": org.plan, "voice_credits_seconds": org.voice_credits_seconds}

@router.get("/global-audit-logs")
def global_audit_logs(limit:int=Query(100,ge=1,le=500),admin:User=AdminUser,db:Session=Depends(get_db)):
    if admin.role != "superadmin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    logs = db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)).all()
    results = []
    for l in logs:
        actor = db.get(User, l.actor_id) if l.actor_id else None
        org = db.get(Organization, l.organization_id) if l.organization_id else None
        results.append({
            "id": l.id,
            "action": l.action,
            "entity_type": l.entity_type,
            "entity_id": l.entity_id,
            "actor_email": actor.email if actor else "System",
            "organization_name": org.name if org else "Global/Platform",
            "ip_address": l.ip_address,
            "created_at": l.created_at
        })
    return results

@router.get("/feature-flags")
def get_feature_flags(admin:User=AdminUser,db:Session=Depends(get_db)):
    if admin.role != "superadmin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    defaults = {
        "ff_openai_realtime": True,
        "ff_twilio_media_streams": True,
        "ff_inbound_calls": True,
        "ff_outbound_calls": True,
        "ff_rag_memory": True
    }
    settings = db.scalars(select(SystemSetting).where(SystemSetting.organization_id.is_(None))).all()
    stored = {s.key: s.value.get("enabled", True) if isinstance(s.value, dict) else s.value for s in settings if s.key.startswith("ff_")}
    defaults.update(stored)
    return defaults

@router.put("/feature-flags/{key}")
def toggle_feature_flag(key:str,payload:dict,admin:User=AdminUser,db:Session=Depends(get_db)):
    if admin.role != "superadmin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    setting = db.scalar(select(SystemSetting).where(SystemSetting.organization_id.is_(None), SystemSetting.key == key))
    enabled = payload.get("enabled", True)
    if setting:
        setting.value = {"enabled": enabled}
    else:
        setting = SystemSetting(organization_id=None, key=key, value={"enabled": enabled}, is_secret=False, updated_by_id=admin.id)
        db.add(setting)
    write_audit(db, action="SUPERADMIN_TOGGLE_FEATURE_FLAG", entity_type="system_setting", entity_id=key, organization_id=None, actor_id=admin.id, request=None, after={"key": key, "enabled": enabled})
    db.commit()
    return {"key": key, "enabled": enabled}

@router.get("/announcements")
def get_announcements(admin:User=AdminUser,db:Session=Depends(get_db)):
    setting = db.scalar(select(SystemSetting).where(SystemSetting.organization_id.is_(None), SystemSetting.key == "global_announcements"))
    if not setting or not isinstance(setting.value, dict):
        return []
    return setting.value.get("items", [])

@router.post("/announcements")
def create_announcement(payload:dict,admin:User=AdminUser,db:Session=Depends(get_db)):
    if admin.role != "superadmin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    setting = db.scalar(select(SystemSetting).where(SystemSetting.organization_id.is_(None), SystemSetting.key == "global_announcements"))
    import uuid
    new_item = {
        "id": str(uuid.uuid4()),
        "title": payload.get("title", "Announcement"),
        "message": payload.get("message", ""),
        "level": payload.get("level", "info"),
        "created_at": datetime.now(UTC).isoformat()
    }
    if setting:
        items = setting.value.get("items", []) if isinstance(setting.value, dict) else []
        items.insert(0, new_item)
        setting.value = {"items": items}
    else:
        setting = SystemSetting(organization_id=None, key="global_announcements", value={"items": [new_item]}, is_secret=False, updated_by_id=admin.id)
        db.add(setting)
    write_audit(db, action="SUPERADMIN_CREATE_ANNOUNCEMENT", entity_type="announcement", entity_id=new_item["id"], organization_id=None, actor_id=admin.id, request=None, after=new_item)
    db.commit()
    return new_item

@router.delete("/announcements/{announcement_id}")
def delete_announcement(announcement_id:str,admin:User=AdminUser,db:Session=Depends(get_db)):
    if admin.role != "superadmin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    setting = db.scalar(select(SystemSetting).where(SystemSetting.organization_id.is_(None), SystemSetting.key == "global_announcements"))
    if setting and isinstance(setting.value, dict):
        items = [i for i in setting.value.get("items", []) if i.get("id") != announcement_id]
        setting.value = {"items": items}
        db.commit()
    return {"message": "Announcement deleted"}

@router.get("/revenue-analytics")
def get_revenue_analytics(admin:User=AdminUser,db:Session=Depends(get_db)):
    if admin.role != "superadmin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    total_revenue = float(db.scalar(select(func.coalesce(func.sum(UsageRecord.amount), 0))) or 0)
    total_records = db.scalar(select(func.count(UsageRecord.id))) or 0
    org_rankings = db.execute(
        select(Organization.name, func.coalesce(func.sum(UsageRecord.amount), 0).label("total"))
        .join(UsageRecord, UsageRecord.organization_id == Organization.id)
        .group_by(Organization.name)
        .order_by(func.sum(UsageRecord.amount).desc())
        .limit(10)
    ).all()
    return {
        "total_revenue": total_revenue,
        "total_usage_events": total_records,
        "top_organizations": [{"name": name, "total": float(total)} for name, total in org_rankings]
    }


