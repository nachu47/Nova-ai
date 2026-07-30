import json
from datetime import UTC,datetime

from fastapi import APIRouter,Depends,HTTPException,Query,Request
from sqlalchemy import func,select
from sqlalchemy.orm import Session

from app.api.deps import get_db,require_roles
from app.core.security import encrypt_secret
from app.models.entities import APIKey,AuditLog,Call,Organization,SystemSetting,UsageRecord,User,VoiceAgent
from app.schemas.api import AdminUserUpdate,AgentOut,CallOut,Message,SystemSettingUpsert,UsageCreate,UserOut
from app.services.audit_service import write_audit

router=APIRouter(prefix="/admin",tags=["admin"])
AdminUser=Depends(require_roles("owner","admin"))


@router.get("/users",response_model=list[UserOut])
def users(admin:User=AdminUser,db:Session=Depends(get_db)):return db.scalars(select(User).where(User.organization_id==admin.organization_id,User.deleted_at.is_(None)).order_by(User.created_at.desc())).all()


@router.patch("/users/{user_id}",response_model=UserOut)
def update_user(user_id:str,payload:AdminUserUpdate,request:Request,admin:User=AdminUser,db:Session=Depends(get_db)):
    user=db.scalar(select(User).where(User.id==user_id,User.organization_id==admin.organization_id,User.deleted_at.is_(None)))
    if not user:raise HTTPException(status_code=404,detail="User not found")
    if user.id==admin.id and payload.is_active is False:raise HTTPException(status_code=409,detail="You cannot deactivate your own account")
    changes=payload.model_dump(exclude_unset=True)
    if "role" in changes and changes["role"] not in {"owner","admin","member","viewer"}:raise HTTPException(status_code=422,detail="Invalid role")
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
    return {"organisations":1,"users":db.scalar(select(func.count(User.id)).where(User.organization_id==admin.organization_id,User.deleted_at.is_(None))) or 0,"calls":db.scalar(select(func.count(Call.id)).where(Call.organization_id==admin.organization_id,Call.deleted_at.is_(None))) or 0,"usage_revenue":float(db.scalar(select(func.coalesce(func.sum(UsageRecord.amount),0)).where(UsageRecord.organization_id==admin.organization_id)) or 0)}
