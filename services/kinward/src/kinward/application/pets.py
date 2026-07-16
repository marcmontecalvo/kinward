from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kinward.persistence.models import PetRecord


@dataclass(frozen=True)
class PetNotFound:
    """No pet with that id in this household - fail closed."""


@dataclass(frozen=True)
class Deleted:
    pet_id: str


async def list_pets(session: AsyncSession, *, household_id: str) -> list[PetRecord]:
    pets = await session.scalars(
        select(PetRecord)
        .where(PetRecord.household_id == household_id)
        .order_by(PetRecord.display_name)
    )
    return list(pets)


async def create_pet(
    session: AsyncSession,
    *,
    household_id: str,
    display_name: str,
    species: str,
    shared_facts: list[str],
) -> PetRecord:
    pet = PetRecord(
        household_id=household_id,
        display_name=display_name.strip(),
        species=species.strip(),
        shared_facts=list(shared_facts),
    )
    session.add(pet)
    await session.flush()
    return pet


async def _find_pet(session: AsyncSession, *, household_id: str, pet_id: str) -> PetRecord | None:
    pet = await session.get(PetRecord, pet_id)
    if pet is None or pet.household_id != household_id:
        return None
    return pet


async def update_pet(
    session: AsyncSession,
    *,
    household_id: str,
    pet_id: str,
    display_name: str | None = None,
    species: str | None = None,
    shared_facts: list[str] | None = None,
) -> PetRecord | PetNotFound:
    pet = await _find_pet(session, household_id=household_id, pet_id=pet_id)
    if pet is None:
        return PetNotFound()
    if display_name is not None:
        pet.display_name = display_name.strip()
    if species is not None:
        pet.species = species.strip()
    if shared_facts is not None:
        pet.shared_facts = list(shared_facts)
    pet.record_version += 1
    await session.flush()
    return pet


async def delete_pet(
    session: AsyncSession, *, household_id: str, pet_id: str
) -> Deleted | PetNotFound:
    pet = await _find_pet(session, household_id=household_id, pet_id=pet_id)
    if pet is None:
        return PetNotFound()
    await session.delete(pet)
    await session.flush()
    return Deleted(pet_id=pet_id)
