from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.application.authorization import resolve_person
from kinward.application.conversation import Unmapped
from kinward.persistence.models import AssistantRecord


@dataclass(frozen=True)
class AssistantNotFound:
    """The resolved person has no primary assistant to customize - fail closed."""


async def update_own_primary_assistant(
    session: AsyncSession,
    *,
    ha_user_id: str,
    name: str | None = None,
    personality: dict[str, Any] | None = None,
) -> AssistantRecord | AssistantNotFound | Unmapped:
    """Let an owner rename or set personality/interaction preferences on their own assistant.

    Preferences never alter authority, privacy, or action policy: this only ever
    touches the assistant's own ``name``/``personality`` fields, never anything on
    the owning ``PersonRecord`` (role, profile_kind, classification).
    """
    person = await resolve_person(session, ha_user_id=ha_user_id)
    if isinstance(person, Unmapped):
        return person
    assistant = await session.scalar(
        select(AssistantRecord).where(
            AssistantRecord.owner_person_id == person.id, AssistantRecord.kind == "primary"
        )
    )
    if assistant is None:
        return AssistantNotFound()
    if name is not None:
        assistant.name = name.strip()
    if personality is not None:
        assistant.personality = personality
    assistant.record_version += 1
    await session.flush()
    return assistant
