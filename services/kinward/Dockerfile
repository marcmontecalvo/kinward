FROM ghcr.io/astral-sh/uv:0.11.28 AS uv
FROM python:3.14.4-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=uv /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
COPY src ./src

RUN uv sync --frozen --no-dev --no-editable

COPY alembic.ini ./
COPY migrations ./migrations

EXPOSE 8000

CMD ["uvicorn", "kinward.app:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
