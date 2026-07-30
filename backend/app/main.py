from contextlib import asynccontextmanager

from fastapi import FastAPI,Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.logging import configure_logging,logger
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_context import RequestContextMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.routers import admin,agents,ai,analytics,auth,calls,crm,health,integrations,notifications,scheduling,users,voice,webhooks


@asynccontextmanager
async def lifespan(app:FastAPI):
    configure_logging();logger.info("application.started",environment=settings.app_env,voice_mode=settings.voice_provider_mode);yield;logger.info("application.stopped")


app=FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Production-oriented multi-tenant AI voice calling, CRM, scheduling, RAG, integration and analytics API.",
    docs_url=f"{settings.api_prefix}/docs",
    redoc_url=f"{settings.api_prefix}/redoc",
    openapi_url=f"{settings.api_prefix}/openapi.json",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origins,allow_credentials=True,allow_methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"],allow_headers=["Authorization","Content-Type","X-CSRF-Token","X-API-Key","X-Request-ID"])
# app.add_middleware(SecurityHeadersMiddleware)
# app.add_middleware(RateLimitMiddleware)
# app.add_middleware(RequestContextMiddleware)

for router in [health.router,auth.router,users.router,agents.router,calls.router,voice.router,crm.router,scheduling.router,ai.router,integrations.router,webhooks.router,notifications.router,analytics.router,admin.router]:app.include_router(router,prefix=settings.api_prefix)


@app.get("/",include_in_schema=False)
def root():return {"name":settings.app_name,"version":"1.0.0","docs":f"{settings.api_prefix}/docs"}


@app.exception_handler(RequestValidationError)
async def validation_error(request:Request,exc:RequestValidationError):
    return ORJSONResponse(status_code=422,content={"detail":"Request validation failed","errors":exc.errors(),"request_id":getattr(request.state,"request_id",None)})


@app.exception_handler(SQLAlchemyError)
async def database_error(request:Request,exc:SQLAlchemyError):
    logger.exception("database.error",error=str(exc));return ORJSONResponse(status_code=500,content={"detail":"A database operation failed","request_id":getattr(request.state,"request_id",None)})

Instrumentator(excluded_handlers=["/metrics",f"{settings.api_prefix}/health/.*"]).instrument(app).expose(app,include_in_schema=False)
