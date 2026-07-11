from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol


class CalendarProvider(Protocol):
    async def events(self, *, person_id: str, start: datetime, end: datetime) -> list[dict[str, Any]]: ...

    async def propose_change(
        self,
        *,
        person_id: str,
        event_id: str,
        changes: dict[str, Any],
    ) -> dict[str, Any]: ...


class MailProvider(Protocol):
    async def important_messages(self, *, person_id: str, limit: int = 10) -> list[dict[str, Any]]: ...

    async def prepare_reply(
        self,
        *,
        person_id: str,
        message_id: str,
        instruction: str,
    ) -> dict[str, Any]: ...


class VoiceProvider(Protocol):
    async def transcribe(self, *, audio: bytes, content_type: str) -> str: ...

    async def synthesize(self, *, text: str, voice_id: str) -> bytes: ...


class NotificationProvider(Protocol):
    async def notify(
        self,
        *,
        person_id: str,
        title: str,
        body: str,
        actions: list[str] | None = None,
    ) -> bool: ...
