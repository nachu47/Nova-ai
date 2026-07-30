from datetime import UTC, datetime, timedelta
from urllib.parse import urlparse

import jwt
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user,get_db
from app.core.config import settings
from app.core.security import create_jwt,decode_jwt
from app.models.entities import Integration,User
from app.schemas.api import Message
from app.services.integration_service import authorization_url,exchange_code,integration_request,save_integration

router=APIRouter(prefix="/integrations",tags=["integrations"])
ALLOWED_HOSTS={"google":{"www.googleapis.com","gmail.googleapis.com","people.googleapis.com"},"microsoft":{"graph.microsoft.com"},"slack":{"slack.com"},"hubspot":{"api.hubapi.com"},"salesforce":{"login.salesforce.com"}}


@router.get("")
def list_integrations(user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    rows=db.scalars(select(Integration).where(Integration.organization_id==user.organization_id,Integration.deleted_at.is_(None)).order_by(Integration.created_at.desc())).all()
    return [{"id":x.id,"provider":x.provider,"account_email":x.account_email,"scopes":x.scopes,"is_active":x.is_active,"token_expires_at":x.token_expires_at,"created_at":x.created_at} for x in rows]


@router.get("/{provider}/authorize")
def authorize(provider:str,user:User=Depends(get_current_user)):
    state=create_jwt(user.id,"oauth_state",timedelta(minutes=10),organization_id=user.organization_id,provider=provider)
    redirect=f"{settings.public_base_url.rstrip('/')}{settings.api_prefix}/integrations/{provider}/callback"
    try:return {"authorization_url":authorization_url(provider,state,redirect)}
    except ValueError as exc:raise HTTPException(status_code=409,detail=str(exc)) from exc


@router.get("/{provider}/callback")
def callback(provider:str,code:str,state:str,db:Session=Depends(get_db)):
    try:claims=decode_jwt(state,"oauth_state")
    except jwt.InvalidTokenError as exc:raise HTTPException(status_code=400,detail="Invalid OAuth state") from exc
    if claims.get("provider")!=provider:raise HTTPException(status_code=400,detail="OAuth provider mismatch")
    redirect=f"{settings.public_base_url.rstrip('/')}{settings.api_prefix}/integrations/{provider}/callback"
    try:
        token=exchange_code(provider,code,redirect)
        save_integration(db,claims["organization_id"],claims["sub"],provider,token)
    except Exception as exc:
        raise HTTPException(status_code=502,detail=f"OAuth connection failed: {exc}") from exc
    return RedirectResponse(
        url=f"{settings.frontend_url.rstrip('/')}/integrations?connected={provider}",
        status_code=302,
    )


@router.post("/{integration_id}/request")
def provider_request(integration_id:str,payload:dict=Body(...),user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    integration=db.scalar(select(Integration).where(Integration.id==integration_id,Integration.organization_id==user.organization_id,Integration.deleted_at.is_(None)))
    if not integration:raise HTTPException(status_code=404,detail="Integration not found")
    method=str(payload.get("method","GET")).upper();url=str(payload.get("url","")).strip();host=(urlparse(url).hostname or "").lower()
    allowed_hosts=set(ALLOWED_HOSTS.get(integration.provider,set()))
    if integration.provider=="salesforce" and integration.config.get("instance_url"):
        instance_host=(urlparse(integration.config["instance_url"]).hostname or "").lower()
        if instance_host:
            allowed_hosts.add(instance_host)
    if method not in {"GET","POST","PATCH","PUT","DELETE"} or host not in allowed_hosts:
        raise HTTPException(status_code=422,detail="The provider URL or HTTP method is not allowed")
    try:return integration_request(db,integration.id,method,url,payload.get("json"))
    except Exception as exc:raise HTTPException(status_code=502,detail=f"Provider request failed: {exc}") from exc


@router.delete("/{integration_id}",response_model=Message)
def disconnect(integration_id:str,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    integration=db.scalar(select(Integration).where(Integration.id==integration_id,Integration.organization_id==user.organization_id,Integration.deleted_at.is_(None)))
    if not integration:raise HTTPException(status_code=404,detail="Integration not found")
    integration.is_active=False;integration.deleted_at=datetime.now(UTC);db.commit();return Message(message="Integration disconnected")
