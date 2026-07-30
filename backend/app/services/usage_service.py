from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Call, Organization, UsageRecord


def finalise_call_usage(db: Session, call: Call) -> UsageRecord:
    existing = db.scalar(
        select(UsageRecord).where(
            UsageRecord.call_id == call.id,
            UsageRecord.metric == "voice_seconds",
        )
    )
    if existing:
        return existing
    seconds = max(0, int(call.duration_seconds or 0))
    org = db.get(Organization, call.organization_id)
    if org:
        org.voice_credits_seconds = max(0, org.voice_credits_seconds - seconds)
    ended = call.ended_at or datetime.now(UTC)
    started = call.started_at or call.answered_at or ended
    record = UsageRecord(
        organization_id=call.organization_id,
        call_id=call.id,
        metric="voice_seconds",
        quantity=Decimal(seconds),
        unit="second",
        unit_price=(Decimal(call.cost or 0) / Decimal(seconds)) if seconds else Decimal("0"),
        amount=Decimal(call.cost or 0),
        period_start=started,
        period_end=ended,
        metadata_json={"provider": call.provider, "direction": call.direction},
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
