from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

kwargs = {"pool_pre_ping": True}
if not settings.database_url.startswith("sqlite"):
    kwargs.update(pool_size=10, max_overflow=20, pool_recycle=1800)

engine = create_engine(settings.database_url, **kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
