from sqlalchemy import select

from app.core.config import settings
from app.core.logging import configure_logging, logger
from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models.entities import Organization, User, VoiceAgent


def seed() -> None:
    with SessionLocal() as db:
        existing = db.scalar(select(User).where(User.email == settings.default_admin_email.lower()))
        if existing:
            return
        org = Organization(name="Nova Demo", slug="nova-demo", timezone="UTC", currency="GBP")
        db.add(org)
        db.flush()
        user = User(
            organization_id=org.id,
            email=settings.default_admin_email.lower(),
            password_hash=hash_password(settings.default_admin_password),
            full_name="Nova Administrator",
            role="owner",
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.flush()
        db.add(
            VoiceAgent(
                organization_id=org.id,
                name="Nova Receptionist",
                description="General-purpose AI receptionist for demonstrations and first-response calls.",
                system_prompt=(
                    "You are Nova, a professional AI receptionist. Be concise, warm, and transparent that "
                    "you are an AI assistant. Confirm important names, phone numbers, dates, and times. "
                    "Never claim an action succeeded unless the function result confirms it. Respect opt-outs."
                ),
                greeting="Hello, this is Nova, the AI receptionist. How may I help you today?",
                tools=["search_knowledge", "create_task", "book_meeting", "lookup_contact"],
            )
        )
        db.commit()
        logger.info("bootstrap.complete", admin_email=settings.default_admin_email)


if __name__ == "__main__":
    configure_logging()
    seed()
