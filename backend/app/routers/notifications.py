from datetime import UTC, datetime

from fastapi import APIRouter,Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user,get_db,require_roles
from app.models.entities import Notification,User
from app.schemas.api import NotificationCreate,NotificationOut
from app.workers.tasks import deliver_notification_task

router=APIRouter(prefix="/notifications",tags=["notifications"])


@router.get("",response_model=list[NotificationOut])
def list_notifications(user:User=Depends(get_current_user),db:Session=Depends(get_db)):return db.scalars(select(Notification).where(Notification.organization_id==user.organization_id).order_by(Notification.created_at.desc()).limit(200)).all()


@router.post("",response_model=NotificationOut,status_code=201)
def create_notification(payload:NotificationCreate,user:User=Depends(require_roles("owner","admin","member")),db:Session=Depends(get_db)):
    notification=Notification(organization_id=user.organization_id,**payload.model_dump())
    db.add(notification);db.commit();db.refresh(notification)
    scheduled_at=notification.scheduled_at
    if scheduled_at and scheduled_at.tzinfo is None:
        scheduled_at=scheduled_at.replace(tzinfo=UTC)
    if scheduled_at and scheduled_at>datetime.now(UTC):
        deliver_notification_task.apply_async(args=[notification.id],eta=scheduled_at)
    else:
        deliver_notification_task.delay(notification.id)
    return notification
