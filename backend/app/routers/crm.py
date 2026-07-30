from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, org_record_or_404, require_roles
from app.models.entities import Activity, Company, Contact, CRMNote, CRMTask, Deal, User
from app.schemas.api import CompanyCreate, CompanyOut, ContactCreate, ContactOut, ContactUpdate, DealCreate, DealOut, Message, NoteCreate, NoteOut, TaskCreate, TaskOut
from app.services.audit_service import write_audit

router = APIRouter(prefix="/crm", tags=["crm"])


def activity(db: Session, user: User, entity_type: str, entity_id: str, action: str, data: dict | None = None):
    db.add(Activity(organization_id=user.organization_id, actor_id=user.id, entity_type=entity_type, entity_id=entity_id, action=action, data=data or {}))


@router.get("/contacts")
def list_contacts(search: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conditions = [Contact.organization_id == user.organization_id, Contact.deleted_at.is_(None)]
    if search:
        q = f"%{search}%"; conditions.append(or_(Contact.first_name.ilike(q), Contact.last_name.ilike(q), Contact.email.ilike(q), Contact.phone.ilike(q)))
    total = db.scalar(select(func.count(Contact.id)).where(*conditions)) or 0
    items = db.scalars(select(Contact).where(*conditions).order_by(Contact.created_at.desc()).offset((page-1)*page_size).limit(page_size)).all()
    return {"total":total,"page":page,"page_size":page_size,"items":[ContactOut.model_validate(x).model_dump(mode="json") for x in items]}


@router.post("/contacts", response_model=ContactOut, status_code=201)
def create_contact(payload: ContactCreate, request: Request, user: User = Depends(require_roles("owner","admin","member")), db: Session = Depends(get_db)):
    if payload.email and db.scalar(select(Contact).where(Contact.organization_id == user.organization_id, Contact.email == payload.email.lower(), Contact.deleted_at.is_(None))): raise HTTPException(status_code=409, detail="Contact email already exists")
    contact = Contact(organization_id=user.organization_id, owner_id=user.id, **payload.model_dump()); db.add(contact); db.flush(); activity(db,user,"contact",contact.id,"created"); write_audit(db,action="contact.create",entity_type="contact",entity_id=contact.id,organization_id=user.organization_id,actor_id=user.id,request=request); db.commit(); db.refresh(contact)
    from app.services.webhook_service import enqueue_event
    enqueue_event(db, user.organization_id, "contact.created", {"contact_id": contact.id, "email": contact.email, "phone": contact.phone})
    return contact


@router.get("/contacts/{contact_id}", response_model=ContactOut)
def get_contact(contact_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)): return org_record_or_404(db, Contact, contact_id, user.organization_id)


@router.patch("/contacts/{contact_id}", response_model=ContactOut)
def update_contact(contact_id: str, payload: ContactUpdate, request: Request, user: User = Depends(require_roles("owner","admin","member")), db: Session = Depends(get_db)):
    contact = org_record_or_404(db, Contact, contact_id, user.organization_id); changes = payload.model_dump(exclude_unset=True)
    for k,v in changes.items(): setattr(contact,k,v)
    activity(db,user,"contact",contact.id,"updated",changes); write_audit(db,action="contact.update",entity_type="contact",entity_id=contact.id,organization_id=user.organization_id,actor_id=user.id,request=request,after=changes); db.commit(); db.refresh(contact); return contact


@router.delete("/contacts/{contact_id}", response_model=Message)
def delete_contact(contact_id: str, user: User = Depends(require_roles("owner","admin")), db: Session = Depends(get_db)):
    contact = org_record_or_404(db, Contact, contact_id, user.organization_id); contact.deleted_at=datetime.now(UTC); activity(db,user,"contact",contact.id,"deleted"); db.commit(); return Message(message="Contact deleted")


@router.get("/companies", response_model=list[CompanyOut])
def list_companies(user: User=Depends(get_current_user), db: Session=Depends(get_db)): return db.scalars(select(Company).where(Company.organization_id==user.organization_id,Company.deleted_at.is_(None)).order_by(Company.name)).all()


@router.post("/companies", response_model=CompanyOut, status_code=201)
def create_company(payload: CompanyCreate, user: User=Depends(require_roles("owner","admin","member")), db: Session=Depends(get_db)):
    company=Company(organization_id=user.organization_id,owner_id=user.id,**payload.model_dump());db.add(company);db.flush();activity(db,user,"company",company.id,"created");db.commit();db.refresh(company);return company


@router.get("/deals", response_model=list[DealOut])
def list_deals(stage: str|None=None,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    conditions=[Deal.organization_id==user.organization_id,Deal.deleted_at.is_(None)];
    if stage: conditions.append(Deal.stage==stage)
    return db.scalars(select(Deal).where(*conditions).order_by(Deal.created_at.desc())).all()


@router.post("/deals",response_model=DealOut,status_code=201)
def create_deal(payload:DealCreate,user:User=Depends(require_roles("owner","admin","member")),db:Session=Depends(get_db)):
    deal=Deal(organization_id=user.organization_id,owner_id=user.id,**payload.model_dump());db.add(deal);db.flush();activity(db,user,"deal",deal.id,"created");db.commit();db.refresh(deal);return deal


@router.patch("/deals/{deal_id}/stage",response_model=DealOut)
def update_deal_stage(deal_id:str,stage:str,user:User=Depends(require_roles("owner","admin","member")),db:Session=Depends(get_db)):
    if stage not in {"lead","qualified","proposal","negotiation","won","lost"}:raise HTTPException(status_code=422,detail="Invalid deal stage")
    deal=org_record_or_404(db,Deal,deal_id,user.organization_id);deal.stage=stage;activity(db,user,"deal",deal.id,"stage_changed",{"stage":stage});db.commit();db.refresh(deal);return deal


@router.get("/notes",response_model=list[NoteOut])
def list_notes(contact_id:str|None=None,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    conditions=[CRMNote.organization_id==user.organization_id,CRMNote.deleted_at.is_(None)];
    if contact_id:conditions.append(CRMNote.contact_id==contact_id)
    return db.scalars(select(CRMNote).where(*conditions).order_by(CRMNote.created_at.desc())).all()


@router.post("/notes",response_model=NoteOut,status_code=201)
def create_note(payload:NoteCreate,user:User=Depends(require_roles("owner","admin","member")),db:Session=Depends(get_db)):
    note=CRMNote(organization_id=user.organization_id,created_by_id=user.id,**payload.model_dump());db.add(note);db.flush();activity(db,user,"note",note.id,"created");db.commit();db.refresh(note);return note


@router.get("/tasks",response_model=list[TaskOut])
def list_tasks(status:str|None=None,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    conditions=[CRMTask.organization_id==user.organization_id,CRMTask.deleted_at.is_(None)];
    if status:conditions.append(CRMTask.status==status)
    return db.scalars(select(CRMTask).where(*conditions).order_by(CRMTask.due_at.asc().nullslast(),CRMTask.created_at.desc())).all()


@router.post("/tasks",response_model=TaskOut,status_code=201)
def create_task(payload:TaskCreate,user:User=Depends(require_roles("owner","admin","member")),db:Session=Depends(get_db)):
    task=CRMTask(organization_id=user.organization_id,created_by_id=user.id,assignee_id=payload.assignee_id or user.id,**payload.model_dump(exclude={"assignee_id"}));db.add(task);db.flush();activity(db,user,"task",task.id,"created");db.commit();db.refresh(task);return task


@router.patch("/tasks/{task_id}/status",response_model=TaskOut)
def update_task_status(task_id:str,status:str,user:User=Depends(require_roles("owner","admin","member")),db:Session=Depends(get_db)):
    if status not in {"open","in_progress","done","cancelled"}:raise HTTPException(status_code=422,detail="Invalid task status")
    task=org_record_or_404(db,CRMTask,task_id,user.organization_id);task.status=status;activity(db,user,"task",task.id,"status_changed",{"status":status});db.commit();db.refresh(task);return task


@router.get("/timeline/{entity_type}/{entity_id}")
def timeline(entity_type:str,entity_id:str,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    return db.scalars(select(Activity).where(Activity.organization_id==user.organization_id,Activity.entity_type==entity_type,Activity.entity_id==entity_id).order_by(Activity.created_at.desc()).limit(200)).all()
