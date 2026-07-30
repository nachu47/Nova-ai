from datetime import timedelta
from html import escape

from twilio.rest import Client

from app.core.config import settings
from app.core.security import create_jwt
from app.models.entities import Call, VoiceAgent


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


def start_inbound_recording(provider_call_sid: str, call_id: str) -> str | None:
    if settings.voice_provider_mode != "twilio":
        return None
    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        raise RuntimeError("Twilio credentials are required")
    public = settings.public_base_url.rstrip("/")
    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    recording = client.calls(provider_call_sid).recordings.create(
        recording_channels="dual",
        recording_status_callback=f"{public}/api/v1/voice/twilio/recording/{call_id}",
        recording_status_callback_method="POST",
    )
    return recording.sid


def create_outbound_call(call: Call) -> str:
    if settings.voice_provider_mode == "mock":
        return f"MOCK{call.id.replace('-', '')[:24]}"
    if not all([settings.twilio_account_sid, settings.twilio_auth_token, settings.twilio_phone_number]):
        raise RuntimeError("Twilio credentials and phone number are required")
    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    public = settings.public_base_url.rstrip("/")
    result = client.calls.create(
        to=call.to_number, from_=settings.twilio_phone_number,
        url=f"{public}/api/v1/voice/twilio/outbound/{call.id}",
        status_callback=f"{public}/api/v1/voice/twilio/status/{call.id}",
        status_callback_event=["initiated", "ringing", "answered", "completed"], status_callback_method="POST",
        record=True, recording_status_callback=f"{public}/api/v1/voice/twilio/recording/{call.id}",
    )
    return result.sid
