from __future__ import annotations

from fastapi import FastAPI, Response, status

from kinward.api.setup import router as setup_router
from kinward.config import Settings, get_settings
from kinward.health import HealthResponse, probe_health


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime = settings or get_settings()
    app = FastAPI(title="Kinward", version="0.1.0")
    app.include_router(setup_router)

    @app.get("/api/v1/health", response_model=HealthResponse, response_model_exclude_none=True)
    async def health(response: Response) -> HealthResponse:
        result = await probe_health(runtime)
        if result.status == "unhealthy":
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return result

    return app


app = create_app()
