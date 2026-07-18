from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.persistence.models import ActivityRecord, AssistantRecord, PersonRecord


@dataclass(frozen=True)
class SyncedPerson:
    ha_person_id: str
    ha_user_id: str | None
    display_name: str
    is_admin: bool = False


def _assistant_name_for(display_name: str) -> str:
    return f"{display_name}'s Assistant"


def _role_for(is_admin: bool) -> str:
    return "admin" if is_admin else "member"


async def sync_people(
    session: AsyncSession, *, household_id: str, people: list[SyncedPerson]
) -> list[PersonRecord]:
    """Create-or-update every synced HA person, keyed on the durable ``ha_person_id``.

    Kinward has no admin designation step of its own: whoever is an HA administrator
    is a Kinward administrator, and every synced pass reconciles ``role`` to match
    current HA admin membership - promoting or demoting as that changes, and
    supporting any number of simultaneous admins. A person missing from ``people``
    (deleted in HA) is left untouched here - no deletion, no field clearing - real
    removal is Epic 9's territory, not an unrelated sync pass's side effect.
    """
    synced: list[PersonRecord] = []
    for item in people:
        record = await session.scalar(
            select(PersonRecord).where(PersonRecord.ha_person_id == item.ha_person_id)
        )
        role = _role_for(item.is_admin)
        if record is None:
            record = PersonRecord(
                household_id=household_id,
                display_name=item.display_name,
                role=role,
                profile_kind="adult",
                ha_person_id=item.ha_person_id,
                ha_user_id=item.ha_user_id,
            )
            session.add(record)
            await session.flush()
            session.add(
                AssistantRecord(
                    household_id=household_id,
                    owner_person_id=record.id,
                    name=_assistant_name_for(item.display_name),
                    kind="primary",
                    # Epic 3 Story 3.5: only a genuinely new assistant opts into the interview -
                    # see migration 014's note on why the column default stays "completed".
                    interview_state="not_started",
                )
            )
            session.add(
                ActivityRecord(
                    household_id=household_id,
                    person_id=record.id,
                    summary="Person synced from Home Assistant",
                    outcome="completed",
                    detail={"ha_person_id": item.ha_person_id, "role": role},
                )
            )
        else:
            if record.role != role:
                session.add(
                    ActivityRecord(
                        household_id=household_id,
                        person_id=record.id,
                        summary="Household role changed to match Home Assistant admin status",
                        outcome="completed",
                        detail={"ha_person_id": item.ha_person_id, "from_role": record.role, "to_role": role},
                    )
                )
            record.display_name = item.display_name
            record.ha_user_id = item.ha_user_id
            record.role = role
            record.record_version += 1
        synced.append(record)
    await session.flush()
    return synced
