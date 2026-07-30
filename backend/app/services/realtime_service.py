import asyncio
import json
from datetime import UTC, datetime

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy import func, select
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed

from app.core.config import settings
from app.core.logging import logger
from app.database.session import SessionLocal
from app.models.entities import Call, CallEvent, Transcript, VoiceAgent
from app.services.memory_service import build_conversation_memory
from app.services.tool_service import TOOL_DEFINITIONS, execute_tool


def _record_transcript(call_id: str, speaker: str, text: str) -> None:
    text = text.strip()
    if not text:
        return
    with SessionLocal() as db:
        sequence = db.scalar(select(func.count(Transcript.id)).where(Transcript.call_id == call_id)) or 0
        db.add(Transcript(call_id=call_id, speaker=speaker, text=text, sequence=sequence + 1))
        db.commit()


def _record_event(call_id: str, event_type: str, payload: dict) -> None:
    with SessionLocal() as db:
        sequence = db.scalar(select(func.count(CallEvent.id)).where(CallEvent.call_id == call_id)) or 0
        db.add(CallEvent(call_id=call_id, event_type=event_type, sequence=sequence + 1, payload=payload))
        db.commit()


def _mark_stream_started(call_id: str, stream_sid: str | None) -> None:
    with SessionLocal() as db:
        call = db.get(Call, call_id)
        if call:
            call.stream_sid = stream_sid
            call.status = "in_progress"
            call.answered_at = call.answered_at or datetime.now(UTC)
            db.commit()


async def mock_voice_stream(websocket: WebSocket, call_id: str) -> None:
    stream_sid = None
    try:
        while True:
            event = await websocket.receive_json()
            event_type = event.get("event")
            if event_type == "start":
                stream_sid = event.get("start", {}).get("streamSid")
                _mark_stream_started(call_id, stream_sid)
            elif event_type == "stop":
                break
    except WebSocketDisconnect:
        logger.info("twilio.stream.disconnected", call_id=call_id)
    finally:
        _record_event(call_id, "stream.closed", {"stream_sid": stream_sid, "mode": "mock"})


async def bridge_twilio_openai(websocket: WebSocket, call_id: str) -> None:
    """Bridge Twilio bidirectional PCMU media to the OpenAI Realtime API."""
    if not settings.openai_api_key:
        await mock_voice_stream(websocket, call_id)
        return

    with SessionLocal() as db:
        call = db.get(Call, call_id)
        agent = db.get(VoiceAgent, call.agent_id) if call else None
        if not call or not agent:
            raise ValueError("Call or agent not found")
        memory = build_conversation_memory(db, call)
        instructions = agent.system_prompt + (f"\n\nConversation memory:\n{memory}" if memory else "")
        agent_data = {
            "voice": agent.voice,
            "greeting": agent.greeting,
            "tools": agent.tools,
            "organization_id": call.organization_id,
        }

    url = f"wss://api.openai.com/v1/realtime?model={settings.openai_realtime_model}"
    headers = {"Authorization": f"Bearer {settings.openai_api_key}"}

    async with connect(url, additional_headers=headers, max_size=8_000_000) as openai_ws:
        enabled_tools = [tool for tool in TOOL_DEFINITIONS if tool["name"] in agent_data["tools"]]
        await openai_ws.send(
            json.dumps(
                {
                    "type": "session.update",
                    "session": {
                        "type": "realtime",
                        "model": settings.openai_realtime_model,
                        "instructions": instructions,
                        "output_modalities": ["audio"],
                        "audio": {
                            "input": {
                                "format": {"type": "audio/pcmu"},
                                "transcription": {"model": "gpt-4o-mini-transcribe"},
                                "turn_detection": {
                                    "type": "server_vad",
                                    "threshold": 0.5,
                                    "prefix_padding_ms": 300,
                                    "silence_duration_ms": 650,
                                    "create_response": True,
                                    "interrupt_response": True,
                                },
                            },
                            "output": {
                                "format": {"type": "audio/pcmu"},
                                "voice": agent_data["voice"],
                            },
                        },
                        "tools": enabled_tools,
                        "tool_choice": "auto",
                    },
                }
            )
        )
        await openai_ws.send(
            json.dumps(
                {
                    "type": "response.create",
                    "response": {
                        "output_modalities": ["audio"],
                        "instructions": (
                            "Begin the call with this greeting naturally and exactly once: "
                            f"{agent_data['greeting']}"
                        ),
                    },
                }
            )
        )

        stream_sid: str | None = None

        async def from_twilio() -> None:
            nonlocal stream_sid
            try:
                while True:
                    message = await websocket.receive_json()
                    event_type = message.get("event")
                    if event_type == "start":
                        stream_sid = message.get("start", {}).get("streamSid")
                        _mark_stream_started(call_id, stream_sid)
                        _record_event(call_id, "stream.started", {"stream_sid": stream_sid})
                    elif event_type == "media":
                        payload = message.get("media", {}).get("payload")
                        if payload:
                            await openai_ws.send(
                                json.dumps({"type": "input_audio_buffer.append", "audio": payload})
                            )
                    elif event_type == "stop":
                        await openai_ws.close()
                        return
            except WebSocketDisconnect:
                await openai_ws.close()
            except ConnectionClosed:
                return

        async def to_twilio() -> None:
            try:
                async for raw in openai_ws:
                    event = json.loads(raw)
                    event_type = event.get("type", "")
                    if event_type in {"response.audio.delta", "response.output_audio.delta"} and stream_sid:
                        delta = event.get("delta", "")
                        if delta:
                            await websocket.send_json(
                                {
                                    "event": "media",
                                    "streamSid": stream_sid,
                                    "media": {"payload": delta},
                                }
                            )
                    elif event_type == "input_audio_buffer.speech_started" and stream_sid:
                        # Clear buffered Twilio playback immediately so callers can interrupt naturally.
                        await websocket.send_json({"event": "clear", "streamSid": stream_sid})
                    elif event_type == "conversation.item.input_audio_transcription.completed":
                        _record_transcript(call_id, "caller", event.get("transcript", ""))
                    elif event_type in {
                        "response.audio_transcript.done",
                        "response.output_audio_transcript.done",
                    }:
                        _record_transcript(call_id, "assistant", event.get("transcript", ""))
                    elif event_type == "response.function_call_arguments.done":
                        try:
                            arguments = json.loads(event.get("arguments") or "{}")
                        except json.JSONDecodeError:
                            arguments = {}
                        with SessionLocal() as db:
                            result = execute_tool(
                                db,
                                agent_data["organization_id"],
                                None,
                                event["name"],
                                arguments,
                            )
                        await openai_ws.send(
                            json.dumps(
                                {
                                    "type": "conversation.item.create",
                                    "item": {
                                        "type": "function_call_output",
                                        "call_id": event["call_id"],
                                        "output": json.dumps(result),
                                    },
                                }
                            )
                        )
                        await openai_ws.send(json.dumps({"type": "response.create"}))
                    elif event_type == "error":
                        logger.error("openai.realtime.error", call_id=call_id, error=event)
                        _record_event(call_id, "openai.error", event)
            except (ConnectionClosed, WebSocketDisconnect):
                return

        results = await asyncio.gather(from_twilio(), to_twilio(), return_exceptions=True)
        for result in results:
            if isinstance(result, Exception) and not isinstance(
                result, (ConnectionClosed, WebSocketDisconnect)
            ):
                logger.error("voice.bridge.error", call_id=call_id, error=str(result))
                _record_event(call_id, "bridge.error", {"error": str(result)})
