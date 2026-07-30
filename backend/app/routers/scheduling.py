from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, org_record_or_404, require_roles
from app.models.entities import Contact, Meeting, User, VoiceAgent
from app.schemas.api import AvailabilityRequest, MeetingCreate, MeetingOut, MeetingReschedule, Message

router=APIRouter(prefix="/scheduling",tags=["scheduling"])


@router.post("/availability")
def availability(payload:AvailabilityRequest,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    agent=org_record_or_404(db,VoiceAgent,payload.agent_id,user.organization_id)
    try: tz=ZoneInfo(payload.timezone)
    except ZoneInfoNotFoundError as exc: raise HTTPException(status_code=422,detail="Unknown timezone") from exc
    start=payload.date_from.astimezone(tz);end=payload.date_to.astimezone(tz);schedule=agent.schedule or {"days":[0,1,2,3,4],"start":"09:00","end":"17:00"}
    meetings=db.scalars(select(Meeting).where(Meeting.organization_id==user.organization_id,Meeting.agent_id==agent.id,Meeting.status=="scheduled",Meeting.deleted_at.is_(None),Meeting.start_at<end.astimezone(UTC),Meeting.end_at>start.astimezone(UTC))).all()
    duration=timedelta(minutes=payload.duration_minutes);slots=[];day=start.date()
    while day<=end.date() and len(slots)<200:
        if day.weekday() in schedule.get("days",[]):
            sh,sm=map(int,schedule.get("start","09:00").split(":"));eh,em=map(int,schedule.get("end","17:00").split(":"));cursor=datetime(day.year,day.month,day.day,sh,sm,tzinfo=tz);closing=datetime(day.year,day.month,day.day,eh,em,tzinfo=tz)
            while cursor+duration<=closing:
                slot_end=cursor+duration
                if cursor>=start and slot_end<=end and not any(m.start_at<slot_end.astimezone(UTC) and m.end_at>cursor.astimezone(UTC) for m in meetings):slots.append({"start_at":cursor.isoformat(),"end_at":slot_end.isoformat(),"timezone":payload.timezone})
                cursor+=duration
        day+=timedelta(days=1)
    return {"slots":slots}


@router.get("/meetings",response_model=list[MeetingOut])
def list_meetings(status:str|None=None,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    conditions=[Meeting.organization_id==user.organization_id,Meeting.deleted_at.is_(None)];
    if status:conditions.append(Meeting.status==status)
    return db.scalars(select(Meeting).where(*conditions).order_by(Meeting.start_at)).all()


@router.post("/meetings",response_model=MeetingOut,status_code=201)
def create_meeting(payload:MeetingCreate,user:User=Depends(require_roles("owner","admin","member")),db:Session=Depends(get_db)):
    if payload.contact_id:
        org_record_or_404(db,Contact,payload.contact_id,user.organization_id)
    if payload.agent_id:
        org_record_or_404(db,VoiceAgent,payload.agent_id,user.organization_id)
    conflict=db.scalar(select(Meeting).where(Meeting.organization_id==user.organization_id,Meeting.deleted_at.is_(None),Meeting.status=="scheduled",Meeting.start_at<payload.end_at,Meeting.end_at>payload.start_at))
    if conflict:raise HTTPException(status_code=409,detail={"message":"Time slot is unavailable","conflicting_meeting_id":conflict.id})
    meeting=Meeting(organization_id=user.organization_id,created_by_id=user.id,**payload.model_dump());db.add(meeting);db.commit();db.refresh(meeting);return meeting


@router.patch("/meetings/{meeting_id}/reschedule",response_model=MeetingOut)
def reschedule(meeting_id:str,payload:MeetingReschedule,user:User=Depends(require_roles("owner","admin","member")),db:Session=Depends(get_db)):
    meeting=org_record_or_404(db,Meeting,meeting_id,user.organization_id);conflict=db.scalar(select(Meeting).where(Meeting.organization_id==user.organization_id,Meeting.id!=meeting.id,Meeting.deleted_at.is_(None),Meeting.status=="scheduled",Meeting.start_at<payload.end_at,Meeting.end_at>payload.start_at))
    if conflict:raise HTTPException(status_code=409,detail="Time slot is unavailable")
    meeting.start_at=payload.start_at;meeting.end_at=payload.end_at;meeting.timezone=payload.timezone;db.commit();db.refresh(meeting);return meeting


@router.post("/meetings/{meeting_id}/cancel",response_model=Message)
def cancel(meeting_id:str,user:User=Depends(require_roles("owner","admin","member")),db:Session=Depends(get_db)):
    meeting=org_record_or_404(db,Meeting,meeting_id,user.organization_id);meeting.status="cancelled";db.commit();return Message(message="Meeting cancelled")
