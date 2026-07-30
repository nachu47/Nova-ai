from datetime import UTC, datetime

import httpx
from sqlalchemy.orm import Session
from twilio.rest import Client

from app.core.config import settings
from app.models.entities import Notification
from app.services.email_service import send_email
from app.utils.network import validate_outbound_url


def deliver_notification(db: Session, notification: Notification) -> Notification:
    if notification.status == "sent":
        return notification
    try:
        if notification.channel == "email":
            message_id = send_email(notification.recipient, notification.subject or "Nova notification", notification.body)
        elif notification.channel in {"sms", "whatsapp"}:
            if not settings.twilio_account_sid or not settings.twilio_auth_token:
                raise RuntimeError("Twilio credentials are required for SMS and WhatsApp")
            client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
            from_number, to_number = settings.twilio_phone_number, notification.recipient
            if notification.channel == "whatsapp":
                from_number = from_number if from_number.startswith("whatsapp:") else f"whatsapp:{from_number}"
                to_number = to_number if to_number.startswith("whatsapp:") else f"whatsapp:{to_number}"
            message_id = client.messages.create(body=notification.body, from_=from_number, to=to_number).sid
        elif notification.channel == "push":
            target_url = validate_outbound_url(
                notification.recipient,
                require_https=settings.is_production,
                allow_private=not settings.is_production,
            )
            response = httpx.post(target_url, json={"title": notification.subject, "body": notification.body}, timeout=15)
            response.raise_for_status(); message_id = response.headers.get("x-request-id", "push")
        else:
            raise ValueError("Unsupported notification channel")
        notification.status, notification.provider_message_id = "sent", message_id
        notification.sent_at, notification.error = datetime.now(UTC), None
    except Exception as exc:
        notification.status, notification.error = "failed", str(exc)[:4000]
        db.commit()
        db.refresh(notification)
        raise
    db.commit()
    db.refresh(notification)
    return notification
