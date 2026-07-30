from datetime import UTC, datetime

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.orm import Session
from twilio.request_validator import RequestValidator

from app.api.deps import get_db
from app.core.config import settings
from app.core.security import decode_jwt
from app.database.session import SessionLocal
from app.models.entities import Call, Contact, VoiceAgent
from app.services.realtime_service import bridge_twilio_openai
from app.services.twilio_service import start_inbound_recording, twiml_for_call

router = APIRouter(prefix="/voice", tags=["voice provider webhooks"])


async def _validate_twilio(request: Request, form: dict) -> None:
    if settings.voice_provider_mode != "twilio" or not settings.twilio_validate_signatures: return
    signature = request.headers.get("X-Twilio-Signature", "")
    url = f"{settings.public_base_url.rstrip('/')}{request.url.path}"
    if request.url.query: url += f"?{request.url.query}"
    if not RequestValidator(settings.twilio_auth_token).validate(url, form, signature): raise HTTPException(status_code=403, detail="Invalid Twilio signature")


@router.post("/twilio/inbound/{agent_id}")
async def inbound(agent_id: str, request: Request, db: Session = Depends(get_db)):
    form = dict(await request.form()); await _validate_twilio(request, form)
    agent = db.get(VoiceAgent, agent_id)
    if not agent or not agent.is_active or agent.deleted_at is not None: raise HTTPException(status_code=404, detail="Voice agent not found")
    from_number, to_number, sid = str(form.get("From", "unknown")), str(form.get("To", "unknown")), str(form.get("CallSid", "")) or None
    contact = db.scalar(select(Contact).where(Contact.organization_id == agent.organization_id, Contact.phone == from_number, Contact.deleted_at.is_(None)))
    call = db.scalar(select(Call).where(Call.provider == "twilio", Call.provider_call_sid == sid)) if sid else None
    if not call:
        call = Call(organization_id=agent.organization_id, agent_id=agent.id, contact_id=contact.id if contact else None, direction="inbound", status="ringing", from_number=from_number, to_number=to_number, provider="twilio", provider_call_sid=sid, started_at=datetime.now(UTC))
        db.add(call); db.commit(); db.refresh(call)
        if sid and settings.voice_provider_mode == "twilio":
            try:
                call.recording_sid = start_inbound_recording(sid, call.id)
                db.commit()
            except Exception as exc:
                call.failure_reason = f"Recording startup failed: {exc}"[:4000]
                db.commit()
    return Response(twiml_for_call(call, agent), media_type="application/xml")


@router.post("/twilio/outbound/{call_id}")
async def outbound_twiml(call_id: str, request: Request, db: Session = Depends(get_db)):
    form = dict(await request.form()); await _validate_twilio(request, form)
    call = db.get(Call, call_id); agent = db.get(VoiceAgent, call.agent_id) if call else None
    if not call or not agent: raise HTTPException(status_code=404, detail="Call not found")
    return Response(twiml_for_call(call, agent), media_type="application/xml")


@router.post("/twilio/status/{call_id}")
async def status_callback(call_id: str, request: Request, db: Session = Depends(get_db)):
    form = dict(await request.form()); await _validate_twilio(request, form)
    call = db.get(Call, call_id)
    if not call: raise HTTPException(status_code=404, detail="Call not found")
    mapping = {"initiated":"queued", "queued":"queued", "ringing":"ringing", "in-progress":"in_progress", "completed":"completed", "busy":"busy", "failed":"failed", "no-answer":"no_answer", "canceled":"cancelled"}
    terminal = {"completed", "failed", "busy", "no_answer", "cancelled"}
    was_terminal = call.status in terminal
    call.status = mapping.get(str(form.get("CallStatus", "")), call.status)
    call.provider_call_sid = str(form.get("CallSid") or call.provider_call_sid)
    now = datetime.now(UTC)
    if call.status == "in_progress": call.answered_at = call.answered_at or now; call.started_at = call.started_at or now
    if call.status in terminal:
        call.ended_at = call.ended_at or now
        call.duration_seconds = int(form.get("CallDuration") or call.duration_seconds or 0)
        db.commit()
        if not was_terminal:
            from app.services.usage_service import finalise_call_usage
            finalise_call_usage(db, call)
            from app.services.webhook_service import enqueue_event
            enqueue_event(db, call.organization_id, "call.completed", {"call_id": call.id, "status": call.status, "duration_seconds": call.duration_seconds})
            from app.workers.tasks import summarize_call_task
            summarize_call_task.delay(call.id)
        return {"status":"accepted"}
    db.commit(); return {"status":"accepted"}


@router.post("/twilio/recording/{call_id}")
async def recording_callback(call_id: str, request: Request, db: Session = Depends(get_db)):
    form = dict(await request.form()); await _validate_twilio(request, form)
    call = db.get(Call, call_id)
    if not call: raise HTTPException(status_code=404, detail="Call not found")
    call.recording_sid = str(form.get("RecordingSid") or ""); call.recording_url = str(form.get("RecordingUrl") or ""); db.commit(); return {"status":"accepted"}


@router.websocket("/stream/{call_id}")
async def media_stream(websocket: WebSocket, call_id: str, token: str):
    try:
        payload = decode_jwt(token, "voice_stream")
        if payload.get("sub") != call_id: raise jwt.InvalidTokenError("Call mismatch")
        with SessionLocal() as db:
            call = db.get(Call, call_id)
            if not call or call.organization_id != payload.get("organization_id"): raise jwt.InvalidTokenError("Organisation mismatch")
    except jwt.InvalidTokenError as e:
        import logging
        logging.error(f"WebSocket auth failed: {e}")
        await websocket.close(code=4401); return
    await websocket.accept()
    bridge_failed = False
    try:
        await bridge_twilio_openai(websocket, call_id)
    except WebSocketDisconnect:
        pass
    except Exception:
        bridge_failed = True
        try:
            await websocket.close(code=1011)
        except RuntimeError:
            pass
    finally:
        with SessionLocal() as db:
            call = db.get(Call, call_id)
            terminal = {"completed", "failed", "busy", "no_answer", "cancelled"}
            if call and call.status not in terminal:
                now = datetime.now(UTC)
                call.ended_at = now
                call.status = "failed" if bridge_failed else "completed"
                started = call.answered_at or call.started_at
                if started:
                    if started.tzinfo is None:
                        started = started.replace(tzinfo=UTC)
                    call.duration_seconds = max(call.duration_seconds, int((now - started).total_seconds()))
                db.commit()
                from app.services.usage_service import finalise_call_usage
                from app.services.webhook_service import enqueue_event
                from app.workers.tasks import summarize_call_task

                finalise_call_usage(db, call)
                enqueue_event(
                    db,
                    call.organization_id,
                    "call.completed",
                    {
                        "call_id": call.id,
                        "status": call.status,
                        "duration_seconds": call.duration_seconds,
                    },
                )
                summarize_call_task.delay(call.id)
