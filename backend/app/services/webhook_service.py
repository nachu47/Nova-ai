import json
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decrypt_secret, sign_payload
from app.models.entities import WebhookDelivery, WebhookEndpoint
from app.core.config import settings
from app.utils.network import validate_outbound_url


def enqueue_event(db: Session, organization_id: str, event_type: str, payload: dict) -> int:
    endpoints = db.scalars(select(WebhookEndpoint).where(WebhookEndpoint.organization_id == organization_id, WebhookEndpoint.is_active.is_(True), WebhookEndpoint.deleted_at.is_(None))).all()
    count = 0
    for endpoint in endpoints:
        if event_type in endpoint.events or "*" in endpoint.events:
            delivery = WebhookDelivery(endpoint_id=endpoint.id, event_type=event_type, payload=payload)
            db.add(delivery); db.flush()
            from app.workers.tasks import deliver_webhook_task
            deliver_webhook_task.delay(delivery.id); count += 1
    db.commit(); return count


def deliver_webhook(db: Session, delivery_id: str) -> None:
    delivery = db.get(WebhookDelivery, delivery_id)
    if not delivery or delivery.status == "sent": return
    endpoint = db.get(WebhookEndpoint, delivery.endpoint_id)
    if not endpoint or not endpoint.is_active:
        delivery.status, delivery.response_body = "failed", "Endpoint inactive"; db.commit(); return
    body = json.dumps({"id": delivery.id, "type": delivery.event_type, "created_at": datetime.now(UTC).isoformat(), "data": delivery.payload}, separators=(",", ":")).encode()
    signature = sign_payload(decrypt_secret(endpoint.secret_encrypted), body); delivery.attempts += 1
    try:
        target_url = validate_outbound_url(
            endpoint.url,
            require_https=settings.is_production,
            allow_private=not settings.is_production,
        )
        response = httpx.post(target_url, content=body, headers={"Content-Type":"application/json", "X-Nova-Signature":f"sha256={signature}", "X-Nova-Event":delivery.event_type}, timeout=15)
        delivery.response_status, delivery.response_body = response.status_code, response.text[:4000]
        response.raise_for_status(); delivery.status = "sent"; endpoint.failure_count = 0; endpoint.last_delivery_at = datetime.now(UTC)
    except Exception as exc:
        endpoint.failure_count += 1; delivery.status = "failed" if delivery.attempts >= 6 else "pending"; delivery.response_body = str(exc)[:4000]
        delivery.next_attempt_at = datetime.now(UTC) + timedelta(minutes=2 ** min(delivery.attempts, 6))
        if delivery.attempts < 6:
            from app.workers.tasks import deliver_webhook_task
            deliver_webhook_task.apply_async(args=[delivery.id], countdown=2 ** delivery.attempts * 60)
    db.commit()
