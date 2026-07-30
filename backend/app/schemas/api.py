from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from decimal import Decimal
from typing import Literal
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, field_validator, model_validator


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Message(BaseModel):
    message: str


class Pagination(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[Any]


class RegisterRequest(BaseModel):
    organization_name: str = Field(min_length=2, max_length=160)
    full_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    timezone: str = Field(default="UTC", max_length=64)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20)
    password: str = Field(min_length=12, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    csrf_token: str


class UserOut(ORMModel):
    id: str
    organization_id: str
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    is_verified: bool
    preferences: dict
    created_at: datetime


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=160)
    preferences: dict | None = None


class AdminUserUpdate(BaseModel):
    role: str | None = None
    is_active: bool | None = None
    is_verified: bool | None = None


class APIKeyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    scopes: list[Literal["read", "write", "*"]] = Field(default_factory=lambda: ["read"])
    expires_at: datetime | None = None


class APIKeyOut(ORMModel):
    id: str
    name: str
    prefix: str
    scopes: list
    is_active: bool
    expires_at: datetime | None
    last_used_at: datetime | None
    created_at: datetime


class APIKeyCreated(APIKeyOut):
    key: str


class AgentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=2000)
    system_prompt: str = Field(min_length=20, max_length=30000)
    greeting: str = Field(default="Hello, how may I help you today?", max_length=1000)
    voice: str = Field(default="marin", max_length=64)
    language: str = Field(default="en", max_length=16)
    provider: str = Field(default="openai", pattern="^(openai|elevenlabs)$")
    model: str = Field(default="gpt-realtime", max_length=80)
    temperature: float = Field(default=0.7, ge=0, le=1.5)
    max_call_seconds: int = Field(default=1800, ge=30, le=14400)
    silence_timeout_seconds: int = Field(default=15, ge=3, le=120)
    transfer_number: str | None = Field(default=None, max_length=32)
    tools: list[str] = Field(default_factory=lambda: ["search_knowledge", "create_task", "book_meeting"])
    schedule: dict = Field(default_factory=lambda: {"days": [0,1,2,3,4], "start": "09:00", "end": "17:00"})


class AgentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    system_prompt: str | None = Field(default=None, min_length=20, max_length=30000)
    greeting: str | None = Field(default=None, max_length=1000)
    voice: str | None = None
    language: str | None = None
    provider: str | None = Field(default=None, pattern="^(openai|elevenlabs)$")
    model: str | None = None
    temperature: float | None = Field(default=None, ge=0, le=1.5)
    max_call_seconds: int | None = Field(default=None, ge=30, le=14400)
    silence_timeout_seconds: int | None = Field(default=None, ge=3, le=120)
    transfer_number: str | None = None
    tools: list[str] | None = None
    schedule: dict | None = None
    is_active: bool | None = None


class AgentOut(ORMModel):
    id: str
    organization_id: str
    name: str
    description: str
    system_prompt: str
    greeting: str
    voice: str
    language: str
    provider: str
    model: str
    temperature: float
    max_call_seconds: int
    silence_timeout_seconds: int
    transfer_number: str | None
    tools: list
    schedule: dict
    is_active: bool
    created_at: datetime


class OutboundCallCreate(BaseModel):
    agent_id: str
    to_number: str = Field(min_length=7, max_length=32)
    contact_id: str | None = None
    context: dict = Field(default_factory=dict)
    revenue: Decimal = Field(default=Decimal("0"), ge=0)


class CallOut(ORMModel):
    id: str
    organization_id: str
    agent_id: str
    contact_id: str | None
    direction: str
    status: str
    from_number: str
    to_number: str
    provider: str
    provider_call_sid: str | None
    started_at: datetime | None
    answered_at: datetime | None
    ended_at: datetime | None
    duration_seconds: int
    recording_url: str | None
    cost: Decimal
    revenue: Decimal
    sentiment: str | None
    outcome: str | None
    context: dict
    created_at: datetime


class TranscriptOut(ORMModel):
    id: str
    call_id: str
    speaker: str
    text: str
    sequence: int
    created_at: datetime


class CallSummaryOut(ORMModel):
    id: str
    call_id: str
    summary: str
    key_points: list
    action_items: list
    disposition: str
    sentiment: str
    structured_data: dict


class CompanyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    domain: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=120)
    website: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=32)
    address: dict = Field(default_factory=dict)


class CompanyOut(ORMModel):
    id: str
    name: str
    domain: str | None
    industry: str | None
    website: str | None
    phone: str | None
    address: dict
    created_at: datetime


class ContactCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(default="", max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=32)
    company_id: str | None = None
    job_title: str | None = Field(default=None, max_length=120)
    timezone: str = Field(default="UTC", max_length=64)
    tags: list[str] = Field(default_factory=list)
    custom_fields: dict = Field(default_factory=dict)
    do_not_call: bool = False
    consent_recorded_at: datetime | None = None


class ContactUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    company_id: str | None = None
    job_title: str | None = None
    timezone: str | None = None
    tags: list[str] | None = None
    custom_fields: dict | None = None
    do_not_call: bool | None = None
    consent_recorded_at: datetime | None = None


class ContactOut(ORMModel):
    id: str
    company_id: str | None
    first_name: str
    last_name: str
    email: EmailStr | None
    phone: str | None
    job_title: str | None
    timezone: str
    tags: list
    custom_fields: dict
    do_not_call: bool
    consent_recorded_at: datetime | None
    created_at: datetime


class DealCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    company_id: str | None = None
    contact_id: str | None = None
    stage: str = "lead"
    value: Decimal = Field(default=Decimal("0"), ge=0)
    probability: int = Field(default=10, ge=0, le=100)
    expected_close_date: datetime | None = None


class DealOut(ORMModel):
    id: str
    name: str
    company_id: str | None
    contact_id: str | None
    stage: str
    value: Decimal
    probability: int
    expected_close_date: datetime | None
    created_at: datetime


class NoteCreate(BaseModel):
    body: str = Field(min_length=1, max_length=20000)
    contact_id: str | None = None
    company_id: str | None = None
    deal_id: str | None = None


class NoteOut(ORMModel):
    id: str
    body: str
    contact_id: str | None
    company_id: str | None
    deal_id: str | None
    created_at: datetime


class TaskCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str = Field(default="", max_length=10000)
    contact_id: str | None = None
    deal_id: str | None = None
    status: str = "open"
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")
    due_at: datetime | None = None
    assignee_id: str | None = None


class TaskOut(ORMModel):
    id: str
    title: str
    description: str
    status: str
    priority: str
    contact_id: str | None
    deal_id: str | None
    due_at: datetime | None
    assignee_id: str | None
    created_at: datetime


class MeetingCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str = Field(default="", max_length=10000)
    contact_id: str | None = None
    agent_id: str | None = None
    start_at: datetime
    end_at: datetime
    timezone: str = Field(default="UTC", max_length=64)
    location: str | None = Field(default=None, max_length=500)

    @field_validator("end_at")
    @classmethod
    def end_after_start(cls, value: datetime, info):
        start = info.data.get("start_at")
        if start and value <= start:
            raise ValueError("end_at must be after start_at")
        return value

    @model_validator(mode="after")
    def validate_timezone(self):
        if self.start_at.tzinfo is None or self.end_at.tzinfo is None:
            raise ValueError("start_at and end_at must include timezone offsets")
        try:
            ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Unknown timezone") from exc
        return self


class MeetingReschedule(BaseModel):
    start_at: datetime
    end_at: datetime
    timezone: str = Field(default="UTC", max_length=64)

    @model_validator(mode="after")
    def validate_window(self):
        if self.start_at.tzinfo is None or self.end_at.tzinfo is None:
            raise ValueError("start_at and end_at must include timezone offsets")
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be after start_at")
        try:
            ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Unknown timezone") from exc
        return self


class MeetingOut(ORMModel):
    id: str
    title: str
    description: str
    contact_id: str | None
    agent_id: str | None
    start_at: datetime
    end_at: datetime
    timezone: str
    status: str
    location: str | None
    external_event_id: str | None
    created_at: datetime


class AvailabilityRequest(BaseModel):
    agent_id: str
    date_from: datetime
    date_to: datetime
    duration_minutes: int = Field(default=30, ge=15, le=240)
    timezone: str = "UTC"

    @model_validator(mode="after")
    def validate_range(self):
        if self.date_from.tzinfo is None or self.date_to.tzinfo is None:
            raise ValueError("date_from and date_to must include timezone offsets")
        if self.date_to <= self.date_from:
            raise ValueError("date_to must be after date_from")
        try:
            ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Unknown timezone") from exc
        return self


class PromptCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    content: str = Field(min_length=20, max_length=30000)
    variables: list[str] = Field(default_factory=list)


class PromptOut(ORMModel):
    id: str
    name: str
    version: int
    content: str
    variables: list
    is_active: bool
    created_at: datetime


class KnowledgeCreate(BaseModel):
    title: str = Field(min_length=2, max_length=240)
    content: str = Field(min_length=10, max_length=1_000_000)
    source_url: str | None = Field(default=None, max_length=1000)
    metadata: dict = Field(default_factory=dict)


class KnowledgeDocumentOut(ORMModel):
    id: str
    title: str
    source_type: str
    source_url: str | None
    status: str
    metadata_json: dict
    created_at: datetime


class KnowledgeSearch(BaseModel):
    query: str = Field(min_length=2, max_length=2000)
    limit: int = Field(default=5, ge=1, le=20)


class WebhookCreate(BaseModel):
    url: HttpUrl
    description: str = Field(default="", max_length=240)
    events: list[str] = Field(min_length=1)


class WebhookOut(ORMModel):
    id: str
    url: str
    description: str
    events: list
    is_active: bool
    failure_count: int
    last_delivery_at: datetime | None
    created_at: datetime


class NotificationCreate(BaseModel):
    channel: str = Field(pattern="^(email|sms|whatsapp|push)$")
    recipient: str = Field(min_length=3, max_length=500)
    subject: str | None = Field(default=None, max_length=240)
    body: str = Field(min_length=1, max_length=20000)
    scheduled_at: datetime | None = None


class NotificationOut(ORMModel):
    id: str
    channel: str
    recipient: str
    subject: str | None
    body: str
    status: str
    provider_message_id: str | None
    error: str | None
    scheduled_at: datetime | None
    sent_at: datetime | None
    created_at: datetime


class SystemSettingUpsert(BaseModel):
    value: dict
    is_secret: bool = False


class UsageCreate(BaseModel):
    organization_id: str
    metric: str = Field(min_length=2, max_length=64)
    quantity: Decimal
    unit: str = Field(min_length=1, max_length=24)
    unit_price: Decimal = Decimal("0")
    period_start: datetime
    period_end: datetime
    user_id: str | None = None
    call_id: str | None = None
    metadata: dict = Field(default_factory=dict)
