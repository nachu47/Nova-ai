from datetime import UTC,datetime

from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user,get_db,require_roles
from app.core.config import settings
from app.core.security import encrypt_secret,new_random_token
from app.models.entities import User,WebhookDelivery,WebhookEndpoint
from app.schemas.api import Message,WebhookCreate,WebhookOut
from app.services.webhook_service import enqueue_event
from app.utils.network import UnsafeOutboundURL, validate_outbound_url

router=APIRouter(prefix="/webhooks",tags=["webhooks"])


@router.get("",response_model=list[WebhookOut])
def list_endpoints(user:User=Depends(get_current_user),db:Session=Depends(get_db)):return db.scalars(select(WebhookEndpoint).where(WebhookEndpoint.organization_id==user.organization_id,WebhookEndpoint.deleted_at.is_(None)).order_by(WebhookEndpoint.created_at.desc())).all()


@router.post("",status_code=201)
def create_endpoint(payload:WebhookCreate,user:User=Depends(require_roles("owner","admin")),db:Session=Depends(get_db)):
    try:
        endpoint_url=validate_outbound_url(
            str(payload.url),
            require_https=settings.is_production,
            allow_private=not settings.is_production,
        )
    except UnsafeOutboundURL as exc:
        raise HTTPException(status_code=422,detail=str(exc)) from exc
    secret=new_random_token(32);endpoint=WebhookEndpoint(organization_id=user.organization_id,url=endpoint_url,description=payload.description,events=payload.events,secret_encrypted=encrypt_secret(secret));db.add(endpoint);db.commit();db.refresh(endpoint)
    return {"endpoint":WebhookOut.model_validate(endpoint).model_dump(mode="json"),"signing_secret":secret}


@router.post("/{endpoint_id}/test")
def test_endpoint(endpoint_id:str,user:User=Depends(require_roles("owner","admin")),db:Session=Depends(get_db)):
    endpoint=db.scalar(select(WebhookEndpoint).where(WebhookEndpoint.id==endpoint_id,WebhookEndpoint.organization_id==user.organization_id,WebhookEndpoint.deleted_at.is_(None)))
    if not endpoint:raise HTTPException(status_code=404,detail="Webhook endpoint not found")
    count=enqueue_event(db,user.organization_id,"webhook.test",{"message":"Nova webhook test","endpoint_id":endpoint.id});return {"queued":count}


@router.get("/{endpoint_id}/deliveries")
def deliveries(endpoint_id:str,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    endpoint=db.scalar(select(WebhookEndpoint).where(WebhookEndpoint.id==endpoint_id,WebhookEndpoint.organization_id==user.organization_id))
    if not endpoint:raise HTTPException(status_code=404,detail="Webhook endpoint not found")
    rows=db.scalars(select(WebhookDelivery).where(WebhookDelivery.endpoint_id==endpoint.id).order_by(WebhookDelivery.created_at.desc()).limit(100)).all()
    return [{"id":x.id,"event_type":x.event_type,"status":x.status,"attempts":x.attempts,"response_status":x.response_status,"created_at":x.created_at} for x in rows]


@router.delete("/{endpoint_id}",response_model=Message)
def delete_endpoint(endpoint_id:str,user:User=Depends(require_roles("owner","admin")),db:Session=Depends(get_db)):
    endpoint=db.scalar(select(WebhookEndpoint).where(WebhookEndpoint.id==endpoint_id,WebhookEndpoint.organization_id==user.organization_id,WebhookEndpoint.deleted_at.is_(None)))
    if not endpoint:raise HTTPException(status_code=404,detail="Webhook endpoint not found")
    endpoint.is_active=False;endpoint.deleted_at=datetime.now(UTC);db.commit();return Message(message="Webhook endpoint deleted")
