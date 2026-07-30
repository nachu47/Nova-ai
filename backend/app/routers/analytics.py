from datetime import UTC,datetime,timedelta

from fastapi import APIRouter,Depends,Query
from sqlalchemy import case,func,select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user,get_db
from app.models.entities import Call,Company,Contact,Organization,UsageRecord,User,VoiceAgent

router=APIRouter(prefix="/analytics",tags=["analytics"])


@router.get("/dashboard")
def dashboard(user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    org=db.get(Organization,user.organization_id);base=[Call.organization_id==user.organization_id,Call.deleted_at.is_(None)];total=db.scalar(select(func.count(Call.id)).where(*base)) or 0;completed=db.scalar(select(func.count(Call.id)).where(*base,Call.status=="completed")) or 0
    avg_duration=float(db.scalar(select(func.coalesce(func.avg(Call.duration_seconds),0)).where(*base)) or 0);revenue=float(db.scalar(select(func.coalesce(func.sum(Call.revenue),0)).where(*base)) or 0);cost=float(db.scalar(select(func.coalesce(func.sum(Call.cost),0)).where(*base)) or 0)
    recent=db.scalars(select(Call).where(*base).order_by(Call.created_at.desc()).limit(8)).all();agents=db.scalar(select(func.count(VoiceAgent.id)).where(VoiceAgent.organization_id==user.organization_id,VoiceAgent.deleted_at.is_(None))) or 0
    return {"total_calls":total,"completed_calls":completed,"success_rate":round(completed/total*100,1) if total else 0,"average_duration_seconds":round(avg_duration,1),"revenue":revenue,"cost":cost,"voice_credits_seconds":org.voice_credits_seconds if org else 0,"active_agents":agents,"recent_calls":[{"id":c.id,"direction":c.direction,"status":c.status,"to_number":c.to_number,"duration_seconds":c.duration_seconds,"created_at":c.created_at} for c in recent],"system_health":{"api":"healthy","database":"healthy","redis":"healthy"}}


@router.get("/timeseries")
def timeseries(days:int=Query(30,ge=7,le=365),user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    start=datetime.now(UTC)-timedelta(days=days-1);day=func.date(Call.created_at)
    rows=db.execute(select(day.label("day"),func.count(Call.id),func.coalesce(func.sum(Call.duration_seconds),0),func.coalesce(func.sum(Call.revenue),0)).where(Call.organization_id==user.organization_id,Call.deleted_at.is_(None),Call.created_at>=start).group_by(day).order_by(day)).all()
    mapped={str(r[0]):{"calls":r[1],"duration_seconds":r[2],"revenue":float(r[3])} for r in rows};result=[]
    for offset in range(days):
        d=(start+timedelta(days=offset)).date().isoformat();result.append({"date":d,**mapped.get(d,{"calls":0,"duration_seconds":0,"revenue":0})})
    return result


@router.get("/monthly")
def monthly(months:int=Query(12,ge=1,le=36),user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    start=datetime.now(UTC)-timedelta(days=months*31);month=func.date_trunc("month",Call.created_at)
    rows=db.execute(select(month.label("month"),func.count(Call.id),func.coalesce(func.avg(Call.duration_seconds),0),func.coalesce(func.sum(Call.revenue),0)).where(Call.organization_id==user.organization_id,Call.deleted_at.is_(None),Call.created_at>=start).group_by(month).order_by(month)).all()
    return [{"month":r[0],"calls":r[1],"average_duration":float(r[2]),"revenue":float(r[3])} for r in rows]


@router.get("/top-customers")
def top_customers(limit:int=Query(10,ge=1,le=100),user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    full_name=func.concat(Contact.first_name," ",Contact.last_name)
    rows=db.execute(select(Contact.id,full_name.label("name"),Contact.email,func.count(Call.id).label("calls"),func.coalesce(func.sum(Call.duration_seconds),0).label("duration"),func.coalesce(func.sum(Call.revenue),0).label("revenue")).join(Call,Call.contact_id==Contact.id).where(Contact.organization_id==user.organization_id,Contact.deleted_at.is_(None),Call.deleted_at.is_(None)).group_by(Contact.id,Contact.first_name,Contact.last_name,Contact.email).order_by(func.sum(Call.revenue).desc(),func.count(Call.id).desc()).limit(limit)).all()
    return [{"contact_id":r.id,"name":r.name.strip(),"email":r.email,"calls":r.calls,"duration_seconds":r.duration,"revenue":float(r.revenue)} for r in rows]
