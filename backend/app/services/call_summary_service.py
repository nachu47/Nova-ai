from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.entities import Call, CallSummary, Transcript
from app.services.openai_service import chat_json

SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "key_points": {"type": "array", "items": {"type": "string"}},
        "action_items": {"type": "array", "items": {"type": "string"}},
        "disposition": {"type": "string"},
        "sentiment": {"type": "string", "enum": ["positive", "neutral", "negative", "mixed"]},
        "structured_data": {"type": "object", "additionalProperties": True},
    },
    "required": ["summary", "key_points", "action_items", "disposition", "sentiment", "structured_data"],
    "additionalProperties": False,
}


def summarize_call(db: Session, call_id: str) -> CallSummary:
    call = db.get(Call, call_id)
    if not call:
        raise ValueError("Call not found")
    lines = db.scalars(select(Transcript).where(Transcript.call_id == call_id).order_by(Transcript.sequence)).all()
    transcript = "\n".join(f"{line.speaker}: {line.text}" for line in lines)
    result = chat_json(
        "Summarise the call accurately. Do not invent facts. Return the requested JSON schema.",
        transcript,
        "call_summary",
        SUMMARY_SCHEMA,
    )
    existing = db.scalar(select(CallSummary).where(CallSummary.call_id == call_id))
    if existing:
        for key, value in result.items():
            setattr(existing, key, value)
        summary = existing
    else:
        summary = CallSummary(call_id=call_id, **result)
        db.add(summary)
    call.sentiment = result["sentiment"]
    call.outcome = result["disposition"]
    db.commit()
    db.refresh(summary)
    return summary
