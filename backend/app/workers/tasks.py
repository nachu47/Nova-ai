from app.database.session import SessionLocal
from app.models.entities import Notification
from app.services.call_summary_service import summarize_call
from app.services.notification_service import deliver_notification
from app.services.webhook_service import deliver_webhook
from app.workers.celery_app import celery_app


@celery_app.task(name="nova.summarize_call", autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def summarize_call_task(call_id: str) -> None:
    with SessionLocal() as db: summarize_call(db, call_id)


@celery_app.task(name="nova.deliver_webhook")
def deliver_webhook_task(delivery_id: str) -> None:
    with SessionLocal() as db: deliver_webhook(db, delivery_id)


@celery_app.task(name="nova.deliver_notification", autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def deliver_notification_task(notification_id: str) -> None:
    with SessionLocal() as db:
        notification = db.get(Notification, notification_id)
        if notification: deliver_notification(db, notification)
