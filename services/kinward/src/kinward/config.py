from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="KINWARD_", extra="ignore")

    environment: Literal["development", "test", "production"] = "development"
    database_url: str = "sqlite+aiosqlite:///./kinward.db"
    memory_backend: Literal["honcho", "none"] = "none"
    knowledge_backend: Literal["llm_wiki", "none"] = "none"
    honcho_url: str | None = None
    llm_wiki_url: str | None = None
    home_assistant_url: str | None = None
    home_assistant_token: str | None = Field(default=None, repr=False)

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
