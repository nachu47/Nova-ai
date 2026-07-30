from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, org_record_or_404, require_roles
from app.models.entities import User, VoiceAgent
from app.schemas.api import AgentCreate, AgentOut, AgentUpdate, Message
from app.services.audit_service import write_audit

router = APIRouter(prefix="/agents", tags=["voice agents"])


@router.get("", response_model=list[AgentOut])
def list_agents(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(select(VoiceAgent).where(VoiceAgent.organization_id == user.organization_id, VoiceAgent.deleted_at.is_(None)).order_by(VoiceAgent.created_at.desc())).all()


@router.post("", response_model=AgentOut, status_code=201)
def create_agent(payload: AgentCreate, request: Request, user: User = Depends(require_roles("owner", "admin", "member")), db: Session = Depends(get_db)):
    agent = VoiceAgent(organization_id=user.organization_id, **payload.model_dump()); db.add(agent); db.flush(); write_audit(db, action="agent.create", entity_type="voice_agent", entity_id=agent.id, organization_id=user.organization_id, actor_id=user.id, request=request); db.commit(); db.refresh(agent); return agent


@router.get("/{agent_id}", response_model=AgentOut)
def get_agent(agent_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)): return org_record_or_404(db, VoiceAgent, agent_id, user.organization_id)


@router.patch("/{agent_id}", response_model=AgentOut)
def update_agent(agent_id: str, payload: AgentUpdate, request: Request, user: User = Depends(require_roles("owner", "admin", "member")), db: Session = Depends(get_db)):
    agent = org_record_or_404(db, VoiceAgent, agent_id, user.organization_id); before = {k:getattr(agent,k) for k in payload.model_dump(exclude_unset=True)}
    for key, value in payload.model_dump(exclude_unset=True).items(): setattr(agent, key, value)
    write_audit(db, action="agent.update", entity_type="voice_agent", entity_id=agent.id, organization_id=user.organization_id, actor_id=user.id, request=request, before=before, after=payload.model_dump(exclude_unset=True)); db.commit(); db.refresh(agent); return agent


@router.delete("/{agent_id}", response_model=Message)
def delete_agent(agent_id: str, request: Request, user: User = Depends(require_roles("owner", "admin")), db: Session = Depends(get_db)):
    agent = org_record_or_404(db, VoiceAgent, agent_id, user.organization_id); agent.deleted_at = datetime.now(UTC); agent.is_active = False; write_audit(db, action="agent.delete", entity_type="voice_agent", entity_id=agent.id, organization_id=user.organization_id, actor_id=user.id, request=request); db.commit(); return Message(message="Agent deleted")
