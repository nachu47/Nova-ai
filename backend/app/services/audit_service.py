from datetime import UTC, datetime
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.entities import AuditLog


def write_audit(
    db: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    organization_id: str | None = None,
    actor_id: str | None = None,
    request: Request | None = None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
) -> None:
    db.add(
        AuditLog(
            organization_id=organization_id,
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
            request_id=getattr(request.state, "request_id", None) if request else None,
            before=before,
            after=after,
            created_at=datetime.now(UTC),
        )
    )
