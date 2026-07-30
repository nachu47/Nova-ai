from fastapi import APIRouter, HTTPException
from redis import Redis
from sqlalchemy import text

from app.core.config import settings
from app.database.session import SessionLocal

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
def live(): return {"status":"alive"}


@router.get("/ready")
def ready():
    checks = {"database": False, "redis": False}
    try:
        with SessionLocal() as db: db.execute(text("SELECT 1")); checks["database"] = True
        checks["redis"] = bool(Redis.from_url(settings.redis_url).ping())
    except Exception as exc:
        raise HTTPException(status_code=503, detail={"status":"not_ready", "checks":checks, "error":str(exc)}) from exc
    return {"status":"ready", "checks":checks, "voice_mode":settings.voice_provider_mode}
