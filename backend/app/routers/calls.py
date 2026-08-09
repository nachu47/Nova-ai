from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, org_record_or_404, require_roles
from app.core.config import settings
from app.models.entities import Call, CallSummary, Contact, Organization, Transcript, User, VoiceAgent
from app.schemas.api import CallOut, CallSummaryOut, Message, OutboundCallCreate, TranscriptOut
from app.services.audit_service import write_audit
from app.services.twilio_service import create_outbound_call

router = APIRouter(prefix="/calls", tags=["calls"])


@router.get("")
def list_calls(
    status: str | None = None, direction: str | None = None, agent_id: str | None = None,
    page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100),
    user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    conditions = [Call.organization_id == user.organization_id, Call.deleted_at.is_(None)]
    if status: conditions.append(Call.status == status)
    if direction: conditions.append(Call.direction == direction)
    if agent_id: conditions.append(Call.agent_id == agent_id)
    total = db.scalar(select(func.count(Call.id)).where(*conditions)) or 0
    items = db.scalars(select(Call).where(*conditions).order_by(Call.created_at.desc()).offset((page-1)*page_size).limit(page_size)).all()
    return {"total": total, "page": page, "page_size": page_size, "items": [CallOut.model_validate(item).model_dump(mode="json") for item in items]}


@router.post("/outbound", response_model=CallOut, status_code=201)
def outbound_call(payload: OutboundCallCreate, request: Request, user: User = Depends(require_roles("owner", "admin", "member")), db: Session = Depends(get_db)):
    agent = org_record_or_404(db, VoiceAgent, payload.agent_id, user.organization_id)
    if not agent.is_active: raise HTTPException(status_code=409, detail="Voice agent is inactive")
    organization = db.get(Organization, user.organization_id)
    if not organization or organization.voice_credits_seconds <= 0:
        raise HTTPException(status_code=402, detail="No voice credits remain for this organisation")
    contact = None
    if payload.contact_id:
        contact = org_record_or_404(db, Contact, payload.contact_id, user.organization_id)
        if contact.do_not_call: raise HTTPException(status_code=409, detail="Contact has opted out of calls")
    call = Call(
        organization_id=user.organization_id, agent_id=agent.id, contact_id=contact.id if contact else None,
        direction="outbound", status="queued", from_number=settings.twilio_phone_number or "+10000000000",
        to_number=payload.to_number, provider=settings.voice_provider_mode, context=payload.context, revenue=payload.revenue,
    )
    db.add(call); db.flush()
    try:
        call.provider_call_sid = create_outbound_call(db, call)
        if settings.voice_provider_mode == "mock": call.status = "ringing"
    except Exception as exc:
        call.status = "failed"; call.failure_reason = str(exc); db.commit(); raise HTTPException(status_code=502, detail=f"Voice provider rejected the call: {exc}") from exc
    write_audit(db, action="call.create", entity_type="call", entity_id=call.id, organization_id=user.organization_id, actor_id=user.id, request=request, after={"to_number":call.to_number,"agent_id":agent.id})
    db.commit(); db.refresh(call)
    from app.services.webhook_service import enqueue_event
    enqueue_event(db, user.organization_id, "call.created", {"call_id": call.id, "direction": call.direction, "status": call.status})
    return call


@router.get("/{call_id}", response_model=CallOut)
def get_call(call_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)): return org_record_or_404(db, Call, call_id, user.organization_id)


@router.get("/{call_id}/transcript", response_model=list[TranscriptOut])
def call_transcript(call_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    org_record_or_404(db, Call, call_id, user.organization_id)
    return db.scalars(select(Transcript).where(Transcript.call_id == call_id).order_by(Transcript.sequence)).all()


@router.get("/{call_id}/summary", response_model=CallSummaryOut)
def call_summary(call_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    org_record_or_404(db, Call, call_id, user.organization_id); summary = db.scalar(select(CallSummary).where(CallSummary.call_id == call_id))
    if not summary: raise HTTPException(status_code=404, detail="Call summary is not ready")
    return summary


@router.post("/{call_id}/simulate", response_model=CallOut)
def simulate_call(call_id: str, user: User = Depends(require_roles("owner", "admin", "member")), db: Session = Depends(get_db)):
    if settings.voice_provider_mode != "mock": raise HTTPException(status_code=404, detail="Simulation is available only in mock mode")
    call = org_record_or_404(db, Call, call_id, user.organization_id); now = datetime.now(UTC); call.status = "completed"; call.started_at = call.started_at or now; call.answered_at = call.answered_at or now; call.ended_at = now; call.duration_seconds = max(call.duration_seconds, 94); call.cost = 0
    if not db.scalar(select(Transcript).where(Transcript.call_id == call.id)):
        db.add_all([Transcript(call_id=call.id, speaker="assistant", text="Hello, this is Nova, the AI receptionist. How may I help you today?", sequence=1), Transcript(call_id=call.id, speaker="caller", text="I would like to arrange a product demonstration next week.", sequence=2), Transcript(call_id=call.id, speaker="assistant", text="Certainly. I have recorded the request for the team to follow up.", sequence=3)])
    db.commit()
    from app.services.usage_service import finalise_call_usage
    finalise_call_usage(db, call)
    from app.services.webhook_service import enqueue_event
    enqueue_event(db, user.organization_id, "call.completed", {"call_id": call.id, "duration_seconds": call.duration_seconds})
    from app.workers.tasks import summarize_call_task
    summarize_call_task.delay(call.id)
    db.refresh(call); return call


@router.delete("/{call_id}", response_model=Message)
def delete_call(call_id: str, request: Request, user: User = Depends(require_roles("owner", "admin")), db: Session = Depends(get_db)):
    call = org_record_or_404(db, Call, call_id, user.organization_id); call.deleted_at = datetime.now(UTC); write_audit(db, action="call.delete", entity_type="call", entity_id=call.id, organization_id=user.organization_id, actor_id=user.id, request=request); db.commit(); return Message(message="Call deleted")
