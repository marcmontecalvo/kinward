from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
