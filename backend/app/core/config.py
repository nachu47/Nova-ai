from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    app_name: str = "Khair IT Solution"
    app_env: Literal["development", "test", "production"] = "development"
    api_prefix: str = "/api/v1"
    secret_key: str = "local-dev-secret-change-before-production-6d3b773598b24fdf"
    encryption_key: str = "gx2_yR_ywzViWFPN9AisjVRFN-ZUCIn04iIn8V3y8qQ="
    access_token_minutes: int = 15
    refresh_token_days: int = 30
    verification_token_hours: int = 24
    reset_token_minutes: int = 30

    database_url: str = "postgresql+psycopg://nova:nova_local_password@postgres:5432/nova"
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"

    public_base_url: str = "http://localhost"
    frontend_url: str = "http://localhost"
    cors_origins: list[str] | str = Field(default_factory=lambda: ["http://localhost"])
    default_admin_email: str = "admin@nova.example.com"
    default_admin_password: str = "NovaAdmin123!"

    email_mode: Literal["console", "smtp"] = "console"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@nova.example.com"

    voice_provider_mode: Literal["mock", "twilio"] = "mock"
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    twilio_validate_signatures: bool = True
    openai_api_key: str = ""
    openai_realtime_model: str = "gpt-realtime"
    openai_text_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    elevenlabs_api_key: str = ""

    oauth_google_client_id: str = ""
    oauth_google_client_secret: str = ""
    oauth_microsoft_client_id: str = ""
    oauth_microsoft_client_secret: str = ""
    oauth_slack_client_id: str = ""
    oauth_slack_client_secret: str = ""
    oauth_hubspot_client_id: str = ""
    oauth_hubspot_client_secret: str = ""
    oauth_salesforce_client_id: str = ""
    oauth_salesforce_client_secret: str = ""

    log_level: str = "INFO"
    rate_limit_per_minute: int = 120

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def validate_production_security(self):
        if self.app_env != "production":
            return self
        errors: list[str] = []
        if self.secret_key.startswith("local-dev-") or len(self.secret_key) < 32:
            errors.append("SECRET_KEY must be a unique production secret of at least 32 characters")
        if self.encryption_key == "gx2_yR_ywzViWFPN9AisjVRFN-ZUCIn04iIn8V3y8qQ=":
            errors.append("ENCRYPTION_KEY must be regenerated for production")
        if self.default_admin_password == "NovaAdmin123!":
            errors.append("DEFAULT_ADMIN_PASSWORD must be changed for production")
        if not self.public_base_url.startswith("https://") or not self.frontend_url.startswith("https://"):
            errors.append("PUBLIC_BASE_URL and FRONTEND_URL must use HTTPS in production")
        if "*" in self.cors_origins:
            errors.append("CORS_ORIGINS cannot contain a wildcard in production")
        if self.voice_provider_mode == "twilio":
            if not all([self.twilio_account_sid, self.twilio_auth_token, self.twilio_phone_number]):
                errors.append("Twilio credentials and phone number are required in Twilio mode")
            if not self.openai_api_key:
                errors.append("OPENAI_API_KEY is required for realtime AI calls")
        if errors:
            raise ValueError("; ".join(errors))
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
