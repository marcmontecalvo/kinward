from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.application.integration_tokens import verify_token
from kinward.persistence.models import IntegrationTokenRecord
from kinward.persistence.session import session_dependency

_bearer_scheme = HTTPBearer(auto_error=False)


def _invalid_token_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "invalid_integration_token", "retryable": False},
    )


async def require_integration_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> IntegrationTokenRecord:
    if credentials is None or not credentials.credentials:
        raise _invalid_token_error()
    record = await verify_token(session, credentials.credentials)
    if record is None:
        raise _invalid_token_error()
    await session.commit()
    return record
