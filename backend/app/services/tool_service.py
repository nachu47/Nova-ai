from datetime import datetime
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.entities import CRMTask, Contact, Meeting, User
from app.services.knowledge_service import search_knowledge

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "name": "search_knowledge",
        "description": "Search the organisation knowledge base for accurate information.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
    },
    {
        "type": "function",
        "name": "lookup_contact",
        "description": "Find a CRM contact by email, phone, or name.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
    },
    {
        "type": "function",
        "name": "create_task",
        "description": "Create a CRM follow-up task after the caller agrees or requests follow-up.",
        "parameters": {
            "type": "object",
            "properties": {"title": {"type": "string"}, "description": {"type": "string"}, "due_at": {"type": ["string", "null"]}},
            "required": ["title", "description", "due_at"],
        },
    },
    {
        "type": "function",
        "name": "book_meeting",
        "description": "Book a meeting after confirming the exact date, time, timezone, and duration.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"}, "start_at": {"type": "string"}, "end_at": {"type": "string"},
                "timezone": {"type": "string"}, "contact_id": {"type": ["string", "null"]},
            },
            "required": ["title", "start_at", "end_at", "timezone", "contact_id"],
        },
    },
]


def execute_tool(db: Session, organization_id: str, user_id: str | None, name: str, arguments: dict[str, Any]) -> dict:
    if name == "search_knowledge":
        return {"results": search_knowledge(db, organization_id, arguments["query"], 4)}
    if name == "lookup_contact":
        query = f"%{arguments['query']}%"
        contacts = db.scalars(
            select(Contact).where(
                Contact.organization_id == organization_id,
                Contact.deleted_at.is_(None),
                or_(Contact.email.ilike(query), Contact.phone.ilike(query), Contact.first_name.ilike(query), Contact.last_name.ilike(query)),
            ).limit(5)
        ).all()
        return {"contacts": [{"id": c.id, "name": f"{c.first_name} {c.last_name}".strip(), "email": c.email, "phone": c.phone} for c in contacts]}
    if name == "create_task":
        task = CRMTask(
            organization_id=organization_id, title=arguments["title"], description=arguments.get("description", ""),
            due_at=datetime.fromisoformat(arguments["due_at"].replace("Z", "+00:00")) if arguments.get("due_at") else None,
            created_by_id=user_id or db.scalar(
                select(User.id).where(
                    User.organization_id == organization_id,
                    User.is_active.is_(True),
                    User.deleted_at.is_(None),
                ).order_by(User.created_at).limit(1)
            ),
        )
        if not task.created_by_id:
            return {"error": "No active user is available to own the task"}
        db.add(task); db.commit(); return {"status": "created", "task_id": task.id}
    if name == "book_meeting":
        start = datetime.fromisoformat(arguments["start_at"].replace("Z", "+00:00")); end = datetime.fromisoformat(arguments["end_at"].replace("Z", "+00:00"))
        if start.tzinfo is None or end.tzinfo is None or end <= start:
            return {"error": "Meeting times must include offsets and end after start"}
        contact_id = arguments.get("contact_id")
        if contact_id:
            contact = db.get(Contact, contact_id)
            if not contact or contact.organization_id != organization_id or contact.deleted_at is not None:
                return {"error": "Contact not found"}
        conflict = db.scalar(select(Meeting).where(Meeting.organization_id == organization_id, Meeting.deleted_at.is_(None), Meeting.status == "scheduled", Meeting.start_at < end, Meeting.end_at > start))
        if conflict:
            return {"error": "The requested time is no longer available", "conflicting_meeting_id": conflict.id}
        meeting = Meeting(
            organization_id=organization_id, title=arguments["title"], start_at=start, end_at=end,
            timezone=arguments["timezone"], contact_id=contact_id, created_by_id=user_id,
        )
        db.add(meeting); db.commit(); return {"status": "booked", "meeting_id": meeting.id}
    return {"error": f"Unknown tool: {name}"}
