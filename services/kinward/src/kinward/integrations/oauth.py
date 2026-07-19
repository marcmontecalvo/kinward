from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OAuthTokens:
    access_token: str
    refresh_token: str | None
    expires_in: int


class OAuthExchangeError(RuntimeError):
    pass
