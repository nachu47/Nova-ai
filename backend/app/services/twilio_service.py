from datetime import timedelta
from html import escape

from twilio.rest import Client

from app.core.config import settings
from app.core.security import create_jwt
from app.models.entities import Call, VoiceAgent


from sqlalchemy.orm import Session
from app.services.settings_service import get_setting

def get_twilio_credentials(db: Session, organization_id: str) -> tuple[str | None, str | None, str | None]:
    sid = get_setting(db, organization_id, "twilio_account_sid")
    auth_val = get_setting(db, organization_id, "twilio_auth_token")
    auth = auth_val.get("secret") if isinstance(auth_val, dict) else auth_val
    phone = get_setting(db, organization_id, "twilio_phone_number")
    
    return (
        sid or settings.twilio_account_sid,
        auth or settings.twilio_auth_token,
        phone or settings.twilio_phone_number
    )


def stream_token(call: Call) -> str:
    return create_jwt(call.id, "voice_stream", timedelta(hours=2), organization_id=call.organization_id)


def twiml_for_call(call: Call, agent: VoiceAgent) -> str:
    public = settings.public_base_url.rstrip("/")
    ws_base = public.replace("https://", "wss://").replace("http://", "ws://")
    stream_url = f"{ws_base}/api/v1/voice/stream/{call.id}?token={stream_token(call)}"
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n<Response>\n'
        f'  <Connect><Stream url="{escape(stream_url)}" /></Connect>\n'
        '</Response>'
    )


def start_inbound_recording(db: Session, call: Call) -> str | None:
    if settings.voice_provider_mode != "twilio":
        return None
    account_sid, auth_token, _ = get_twilio_credentials(db, call.organization_id)
    if not account_sid or not auth_token:
        raise RuntimeError("Twilio credentials are required")
    public = settings.public_base_url.rstrip("/")
    client = Client(account_sid, auth_token)
    recording = client.calls(call.provider_call_sid).recordings.create(
        recording_channels="dual",
        recording_status_callback=f"{public}/api/v1/voice/twilio/recording/{call.id}",
        recording_status_callback_method="POST",
    )
    return recording.sid


def create_outbound_call(db: Session, call: Call) -> str:
    if settings.voice_provider_mode == "mock":
        return f"MOCK{call.id.replace('-', '')[:24]}"
    account_sid, auth_token, phone_number = get_twilio_credentials(db, call.organization_id)
    if not all([account_sid, auth_token, phone_number]):
        raise RuntimeError("Twilio credentials and phone number are required")
    
    # Override the call from_number to ensure it matches the org's phone number
    call.from_number = phone_number
    
    client = Client(account_sid, auth_token)
    public = settings.public_base_url.rstrip("/")
    result = client.calls.create(
        to=call.to_number, from_=phone_number,
        url=f"{public}/api/v1/voice/twilio/outbound/{call.id}",
        status_callback=f"{public}/api/v1/voice/twilio/status/{call.id}",
        status_callback_event=["initiated", "ringing", "answered", "completed"], status_callback_method="POST",
        record=True, recording_status_callback=f"{public}/api/v1/voice/twilio/recording/{call.id}",
    )
    return result.sid
