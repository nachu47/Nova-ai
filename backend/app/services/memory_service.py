from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Call, CallSummary, Contact


def build_conversation_memory(db: Session, call: Call, limit: int = 5) -> str:
    if not call.contact_id:
        return ""
    contact = db.get(Contact, call.contact_id)
    recent = db.execute(
        select(CallSummary.summary, Call.ended_at)
        .join(Call, Call.id == CallSummary.call_id)
        .where(
            Call.organization_id == call.organization_id,
            Call.contact_id == call.contact_id,
            Call.id != call.id,
            Call.deleted_at.is_(None),
        )
        .order_by(Call.ended_at.desc())
        .limit(limit)
    ).all()
    if not recent:
        return ""
    name = f"{contact.first_name} {contact.last_name}".strip() if contact else "this contact"
    lines = [f"Conversation memory for {name}. Use it only when relevant and do not expose internal notes:"]
    for summary, ended_at in reversed(recent):
        date = ended_at.date().isoformat() if ended_at else "unknown date"
        lines.append(f"- {date}: {summary}")
    return "\n".join(lines)
