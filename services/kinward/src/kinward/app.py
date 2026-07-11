from __future__ import annotations

from fastapi import FastAPI

from kinward.api.setup import router as setup_router
from kinward.config import Settings, get_settings


def _capability(enabled: bool, disabled_detail: str) -> dict[str, str]:
    if enabled:
        return {"state": "available"}
    return {"state": "disabled", "detail": disabled_detail}


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime = settings or get_settings()
    app = FastAPI(title="Kinward", version="0.1.0")
    app.include_router(setup_router)

    @app.get("/api/health")
    def health() -> dict[str, object]:
        capabilities = {
            "memory": _capability(
                runtime.memory_enabled,
                "No memory backend is configured; core household features remain available.",
            ),
            "knowledge": _capability(
                runtime.knowledge_enabled,
                "No knowledge backend is configured; contextual knowledge is unavailable.",
            ),
            "homeAssistant": _capability(
                runtime.home_assistant_enabled,
                "Home Assistant is not configured; physical-home control is unavailable.",
            ),
        }
        return {
            "status": "ok",
            "service": "kinward",
            "capabilities": capabilities,
        }

    return app


app = create_app()
