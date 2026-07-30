import os
from collections.abc import Generator
from pathlib import Path

os.environ["APP_ENV"]="test"
os.environ["DATABASE_URL"]="sqlite:///./nova_test.db"
os.environ["REDIS_URL"]="redis://127.0.0.1:6399/15"
os.environ["CELERY_BROKER_URL"]="memory://"
os.environ["CELERY_RESULT_BACKEND"]="cache+memory://"
os.environ["SECRET_KEY"]="test-secret-that-is-long-enough-for-tests"
os.environ["ENCRYPTION_KEY"]="gx2_yR_ywzViWFPN9AisjVRFN-ZUCIn04iIn8V3y8qQ="
os.environ["VOICE_PROVIDER_MODE"]="mock"
os.environ["EMAIL_MODE"]="console"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.database.base import Base
from app.main import app
from app.models import entities  # noqa: F401

engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool)
TestingSession=sessionmaker(bind=engine,autoflush=False,autocommit=False,expire_on_commit=False)


def override_db() -> Generator:
    db=TestingSession()
    try:yield db
    finally:db.close()

app.dependency_overrides[get_db]=override_db


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine);Base.metadata.create_all(bind=engine);yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:yield test_client


@pytest.fixture
def auth_headers(client:TestClient):
    response=client.post("/api/v1/auth/register",json={"organization_name":"Acme Ltd","full_name":"Ada Admin","email":"ada@example.com","password":"StrongPassword123!","timezone":"Europe/London"})
    assert response.status_code==201,response.text
    return {"Authorization":f"Bearer {response.json()['access_token']}"}
