from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user,get_db,org_record_or_404,require_roles
from app.models.entities import KnowledgeDocument,Prompt,User
from app.schemas.api import KnowledgeCreate,KnowledgeDocumentOut,KnowledgeSearch,Message,PromptCreate,PromptOut
from app.services.knowledge_service import content_hash,index_document,search_knowledge

router=APIRouter(prefix="/ai",tags=["ai and knowledge"])


@router.get("/prompts",response_model=list[PromptOut])
def prompts(user:User=Depends(get_current_user),db:Session=Depends(get_db)):return db.scalars(select(Prompt).where(Prompt.organization_id==user.organization_id,Prompt.deleted_at.is_(None)).order_by(Prompt.name,Prompt.version.desc())).all()


@router.post("/prompts",response_model=PromptOut,status_code=201)
def create_prompt(payload:PromptCreate,user:User=Depends(require_roles("owner","admin","member")),db:Session=Depends(get_db)):
    version=(db.scalar(select(func.max(Prompt.version)).where(Prompt.organization_id==user.organization_id,Prompt.name==payload.name)) or 0)+1
    prompt=Prompt(organization_id=user.organization_id,name=payload.name,version=version,content=payload.content,variables=payload.variables,created_by_id=user.id);db.add(prompt);db.commit();db.refresh(prompt);return prompt


@router.get("/knowledge",response_model=list[KnowledgeDocumentOut])
def documents(user:User=Depends(get_current_user),db:Session=Depends(get_db)):return db.scalars(select(KnowledgeDocument).where(KnowledgeDocument.organization_id==user.organization_id,KnowledgeDocument.deleted_at.is_(None)).order_by(KnowledgeDocument.created_at.desc())).all()


@router.post("/knowledge",response_model=KnowledgeDocumentOut,status_code=201)
def add_document(payload:KnowledgeCreate,user:User=Depends(require_roles("owner","admin","member")),db:Session=Depends(get_db)):
    digest=content_hash(payload.content);existing=db.scalar(select(KnowledgeDocument).where(KnowledgeDocument.organization_id==user.organization_id,KnowledgeDocument.content_hash==digest,KnowledgeDocument.deleted_at.is_(None)))
    if existing:raise HTTPException(status_code=409,detail="This document is already indexed")
    document=KnowledgeDocument(organization_id=user.organization_id,title=payload.title,source_type="text",source_url=payload.source_url,content_hash=digest,status="processing",metadata_json=payload.metadata,created_by_id=user.id);db.add(document);db.flush();index_document(db,document,payload.content);db.refresh(document);return document


@router.post("/knowledge/search")
def search(payload:KnowledgeSearch,user:User=Depends(get_current_user),db:Session=Depends(get_db)):return {"results":search_knowledge(db,user.organization_id,payload.query,payload.limit)}


@router.delete("/knowledge/{document_id}",response_model=Message)
def delete_document(document_id:str,user:User=Depends(require_roles("owner","admin")),db:Session=Depends(get_db)):
    document=org_record_or_404(db,KnowledgeDocument,document_id,user.organization_id);from datetime import UTC,datetime;document.deleted_at=datetime.now(UTC);db.commit();return Message(message="Knowledge document deleted")
