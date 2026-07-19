from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="KINWARD_", extra="ignore")

    environment: Literal["development", "test", "production"] = "development"
    database_url: str = Field(default="sqlite+aiosqlite:///./kinward.db", repr=False)
    model_provider: str = "none"
    memory_backend: Literal["honcho", "none"] = "none"
    knowledge_backend: Literal["llm_wiki", "none"] = "none"
    calendar_provider: str = "none"
    honcho_url: str | None = Field(default=None, repr=False)
    llm_wiki_url: str | None = Field(default=None, repr=False)
    home_assistant_url: str | None = Field(default=None, repr=False)
    home_assistant_token: str | None = Field(default=None, repr=False)
    worker_heartbeat_interval_seconds: float = Field(default=5.0, gt=0, allow_inf_nan=False)
    worker_stale_after_seconds: float = Field(default=30.0, gt=0, allow_inf_nan=False)
    setup_authorization: str | None = Field(default=None, repr=False)
    setup_authorization_ttl_seconds: int = Field(default=3600, ge=60, le=86400)

    # Epic 5 v1: direct Google/Microsoft account connections (off-script per product
    # owner - see api/accounts_setup.py). Each provider is only usable once its client
    # credentials, a reachable redirect base URL, and the token encryption key are all
    # configured; missing pieces degrade to "not configured" rather than blocking startup.
    google_client_id: str | None = Field(default=None, repr=False)
    google_client_secret: str | None = Field(default=None, repr=False)
    microsoft_client_id: str | None = Field(default=None, repr=False)
    microsoft_client_secret: str | None = Field(default=None, repr=False)
    microsoft_tenant: str = "common"
    oauth_redirect_base_url: str | None = Field(default=None, repr=False)
    account_token_encryption_key: str | None = Field(default=None, repr=False)
    accounts_setup_token: str | None = Field(default=None, repr=False)

    @field_validator("setup_authorization", mode="before")
    @classmethod
    def normalize_setup_authorization(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        if isinstance(value, str) and len(value) < 24:
            raise ValueError("setup authorization must contain at least 24 characters")
        return value

    @field_validator("accounts_setup_token", mode="before")
    @classmethod
    def normalize_accounts_setup_token(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        if isinstance(value, str) and len(value) < 24:
            raise ValueError("accounts setup token must contain at least 24 characters")
        return value

    @field_validator("account_token_encryption_key", mode="before")
    @classmethod
    def normalize_account_token_encryption_key(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        if isinstance(value, str):
            from cryptography.fernet import Fernet

            try:
                Fernet(value.encode())
            except (ValueError, TypeError) as exc:
                raise ValueError(
                    "account token encryption key must be a valid Fernet key "
                    "(generate one with `python -c \"from cryptography.fernet import "
                    'Fernet; print(Fernet.generate_key().decode())"`)'
                ) from exc
        return value

    @field_validator("oauth_redirect_base_url", mode="before")
    @classmethod
    def normalize_oauth_redirect_base_url(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        if isinstance(value, str):
            return value.rstrip("/")
        return value

    @model_validator(mode="after")
    def validate_worker_timing(self) -> Settings:
        if self.worker_stale_after_seconds <= self.worker_heartbeat_interval_seconds:
            raise ValueError("worker stale threshold must exceed the heartbeat interval")
        return self

    @property
    def memory_enabled(self) -> bool:
        return self.memory_backend == "honcho" and bool(self.honcho_url)

    @property
    def knowledge_enabled(self) -> bool:
        return self.knowledge_backend == "llm_wiki" and bool(self.llm_wiki_url)

    @property
    def home_assistant_enabled(self) -> bool:
        return bool(self.home_assistant_url and self.home_assistant_token)

    @property
    def google_oauth_enabled(self) -> bool:
        return bool(
            self.google_client_id
            and self.google_client_secret
            and self.oauth_redirect_base_url
            and self.account_token_encryption_key
        )

    @property
    def microsoft_oauth_enabled(self) -> bool:
        return bool(
            self.microsoft_client_id
            and self.microsoft_client_secret
            and self.oauth_redirect_base_url
            and self.account_token_encryption_key
        )

    @property
    def accounts_setup_enabled(self) -> bool:
        return bool(self.accounts_setup_token) and (
            self.google_oauth_enabled or self.microsoft_oauth_enabled
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
