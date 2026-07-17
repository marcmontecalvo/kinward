from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Sequence

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from kinward.application.conversation import Unmapped
from kinward.application.knowledge import (
    CONVERSATION_INFERENCE_SOURCE,
    MAX_EXTRACTED_OBSERVATIONS,
    CandidateObservation,
    Disposed,
    FactNotFound,
    NotConfirmed,
    NotPending,
    ProviderUnavailable,
    Suppressed,
    confirm_observation,
    correct_fact,
    delete_fact,
    expire_due_observations,
    extract_candidate_observations,
    list_confirmed_facts,
    list_pending_observations,
    propose_observation,
    reclassify_fact,
    reject_observation,
)
from kinward.llm.contracts import ModelMessage, ModelReply
from kinward.memory.contracts import KnowledgeFact
from kinward.memory.providers import NullKnowledgeStoreProvider
from kinward.persistence.models import Base, HouseholdRecord, KnowledgeFactRecord, PersonRecord


@dataclass
class FakeKnowledgeProvider:
    """Controllable fake of ``KnowledgeStoreProvider`` - real network I/O is covered

    separately by ``LlmWikiKnowledgeProvider``'s own tests; this exercises only the
    Kinward-side lifecycle logic in ``application/knowledge.py``.
    """

    name: str = "fake"
    retire_result: bool = True
    facts: dict[str, KnowledgeFact] = field(default_factory=dict)
    calls: list[tuple[str, dict[str, Any]]] = field(default_factory=list)
    _counter: int = 0

    async def propose_fact(self, **kwargs: Any) -> KnowledgeFact:
        self._counter += 1
        fact_id = f"fake-fact-{self._counter}"
        fact = KnowledgeFact(
            id=fact_id,
            subject=kwargs["subject"],
            predicate=kwargs["predicate"],
            value=kwargs["value"],
            status="proposed",
            privacy=kwargs["privacy"],
        )
        self.facts[fact_id] = fact
        self.calls.append(("propose_fact", kwargs))
        return fact

    async def confirm_fact(self, *, fact_id: str) -> KnowledgeFact | None:
        self.calls.append(("confirm_fact", {"fact_id": fact_id}))
        return self.facts.get(fact_id)

    async def search_facts(self, **kwargs: Any) -> list[KnowledgeFact]:
        return []

    async def revise_fact(
        self, *, fact_id: str, value: Any, provenance: Sequence[str], confidence: float
    ) -> KnowledgeFact | None:
        self.calls.append(("revise_fact", {"fact_id": fact_id, "value": value}))
        return self.facts.get(fact_id)

    async def retire_fact(self, *, fact_id: str) -> bool:
        self.calls.append(("retire_fact", {"fact_id": fact_id}))
        return self.retire_result

    async def reclassify_fact(self, *, fact_id: str, privacy: str) -> KnowledgeFact | None:
        self.calls.append(("reclassify_fact", {"fact_id": fact_id, "privacy": privacy}))
        return self.facts.get(fact_id)

    async def provenance(self, *, fact_id: str) -> list[str]:
        return []


async def _factory():  # type: ignore[no-untyped-def]
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)


async def _seed_person(session, *, household=None, ha_user_id: str = "ha-user-1"):  # type: ignore[no-untyped-def]
    if household is None:
        household = HouseholdRecord(name="Example House")
        session.add(household)
        await session.flush()
    person = PersonRecord(
        household_id=household.id,
        display_name="Example Adult",
        role="member",
        profile_kind="adult",
        ha_person_id=f"ha-person-{ha_user_id}",
        ha_user_id=ha_user_id,
    )
    session.add(person)
    await session.flush()
    return household, person


async def _propose(session, provider, household, person, **overrides):  # type: ignore[no-untyped-def]
    kwargs: dict[str, Any] = dict(
        household_id=household.id,
        owner_person_id=person.id,
        assistant_id=None,
        subject=person.display_name,
        predicate="likes",
        value="tea",
        privacy="personal",
        source_system="conversation-inference",
        source_version="v1",
        confidence=0.8,
    )
    kwargs.update(overrides)
    return await propose_observation(session, provider, **kwargs)


async def test_propose_observation_creates_pending_with_fixed_expiry() -> None:
    factory = await _factory()
    async with factory() as session:
        household, person = await _seed_person(session)
        provider = FakeKnowledgeProvider()

        record = await _propose(session, provider, household, person)
        await session.commit()

        assert isinstance(record, KnowledgeFactRecord)
        assert record.knowledge_state == "pending"
        assert record.external_fact_id == "fake-fact-1"
        assert record.expires_at is not None
        assert record.created_at is not None
        assert (record.expires_at - record.created_at) == timedelta(days=30)


async def test_propose_observation_without_a_provider_fails_closed() -> None:
    factory = await _factory()
    async with factory() as session:
        household, person = await _seed_person(session)
        result = await _propose(session, NullKnowledgeStoreProvider(), household, person)
        assert isinstance(result, ProviderUnavailable)


async def test_list_pending_observations_is_scoped_to_the_owner() -> None:
    factory = await _factory()
    async with factory() as session:
        household, owner = await _seed_person(session, ha_user_id="ha-user-1")
        _, other = await _seed_person(session, household=household, ha_user_id="ha-user-2")
        provider = FakeKnowledgeProvider()
        await _propose(session, provider, household, owner)
        await _propose(session, provider, household, other, subject="Other Adult")
        await session.commit()

        own = await list_pending_observations(session, ha_user_id="ha-user-1")
        assert not isinstance(own, Unmapped)
        assert [record.owner_person_id for record in own] == [owner.id]


async def test_list_pending_observations_fails_closed_for_unmapped_user() -> None:
    factory = await _factory()
    async with factory() as session:
        await _seed_person(session)
        result = await list_pending_observations(session, ha_user_id="unknown")
        assert isinstance(result, Unmapped)


async def test_confirm_observation_moves_to_confirmed_and_confirms_the_provider_body() -> None:
    factory = await _factory()
    async with factory() as session:
        household, person = await _seed_person(session)
        provider = FakeKnowledgeProvider()
        pending = await _propose(session, provider, household, person)
        await session.commit()
        assert isinstance(pending, KnowledgeFactRecord)

        confirmed = await confirm_observation(
            session, provider, ha_user_id="ha-user-1", fact_id=pending.id
        )
        await session.commit()

        assert isinstance(confirmed, KnowledgeFactRecord)
        assert confirmed.knowledge_state == "confirmed"
        assert confirmed.expires_at is None
        assert confirmed.confirmed_at is not None
        assert ("confirm_fact", {"fact_id": "fake-fact-1"}) in provider.calls


async def test_confirm_observation_owned_by_someone_else_fails_closed() -> None:
    factory = await _factory()
    async with factory() as session:
        household, owner = await _seed_person(session, ha_user_id="ha-user-1")
        await _seed_person(session, household=household, ha_user_id="ha-user-2")
        provider = FakeKnowledgeProvider()
        pending = await _propose(session, provider, household, owner)
        await session.commit()
        assert isinstance(pending, KnowledgeFactRecord)

        result = await confirm_observation(
            session, provider, ha_user_id="ha-user-2", fact_id=pending.id
        )
        assert isinstance(result, FactNotFound)


async def test_confirm_only_applies_to_a_pending_observation() -> None:
    factory = await _factory()
    async with factory() as session:
        household, person = await _seed_person(session)
        provider = FakeKnowledgeProvider()
        pending = await _propose(session, provider, household, person)
        await session.commit()
        assert isinstance(pending, KnowledgeFactRecord)
        confirmed = await confirm_observation(
            session, provider, ha_user_id="ha-user-1", fact_id=pending.id
        )
        await session.commit()
        assert isinstance(confirmed, KnowledgeFactRecord)

        result = await confirm_observation(
            session, provider, ha_user_id="ha-user-1", fact_id=pending.id
        )
        assert isinstance(result, NotPending)


async def test_reject_observation_disposes_and_retires_the_provider_body() -> None:
    factory = await _factory()
    async with factory() as session:
        household, person = await _seed_person(session)
        provider = FakeKnowledgeProvider(retire_result=True)
        pending = await _propose(session, provider, household, person)
        await session.commit()
        assert isinstance(pending, KnowledgeFactRecord)

        result = await reject_observation(session, provider, ha_user_id="ha-user-1", fact_id=pending.id)
        await session.commit()

        assert isinstance(result, Disposed)
        refreshed = await session.get(KnowledgeFactRecord, pending.id)
        assert refreshed is not None
        assert refreshed.knowledge_state == "rejected"
        assert refreshed.deletion_status == "none"
        assert refreshed.disposed_at is not None


async def test_reject_observation_marks_deletion_pending_when_the_provider_cannot_confirm_removal() -> None:
    factory = await _factory()
    async with factory() as session:
        household, person = await _seed_person(session)
        provider = FakeKnowledgeProvider(retire_result=False)
        pending = await _propose(session, provider, household, person)
        await session.commit()
        assert isinstance(pending, KnowledgeFactRecord)

        await reject_observation(session, provider, ha_user_id="ha-user-1", fact_id=pending.id)
        await session.commit()

        refreshed = await session.get(KnowledgeFactRecord, pending.id)
        assert refreshed is not None
        assert refreshed.knowledge_state == "rejected"
        assert refreshed.deletion_status == "deletion_pending"


async def test_rejecting_evidence_suppresses_a_later_identical_proposal() -> None:
    factory = await _factory()
    async with factory() as session:
        household, person = await _seed_person(session)
        provider = FakeKnowledgeProvider()
        pending = await _propose(session, provider, household, person)
        await session.commit()
        assert isinstance(pending, KnowledgeFactRecord)
        await reject_observation(session, provider, ha_user_id="ha-user-1", fact_id=pending.id)
        await session.commit()

        result = await _propose(session, provider, household, person)
        assert isinstance(result, Suppressed)


async def test_expire_due_observations_disposes_only_past_expiry() -> None:
    factory = await _factory()
    async with factory() as session:
        household, person = await _seed_person(session)
        provider = FakeKnowledgeProvider()
        due = await _propose(session, provider, household, person, predicate="likes")
        not_due = await _propose(session, provider, household, person, predicate="dislikes")
        await session.commit()
        assert isinstance(due, KnowledgeFactRecord)
        assert isinstance(not_due, KnowledgeFactRecord)
        due.expires_at = datetime.now(UTC) - timedelta(days=1)
        await session.commit()

        count = await expire_due_observations(session, provider)
        await session.commit()

        assert count == 1
        refreshed_due = await session.get(KnowledgeFactRecord, due.id)
        refreshed_not_due = await session.get(KnowledgeFactRecord, not_due.id)
        assert refreshed_due is not None and refreshed_due.knowledge_state == "expired"
        assert refreshed_not_due is not None and refreshed_not_due.knowledge_state == "pending"


async def test_disposing_a_fact_invalidates_its_dependents() -> None:
    """AD-25: rejection/deletion/expiry invalidates dependents - exercised directly since

    nothing yet populates ``depends_on`` in production (see application/knowledge.py).
    """
    factory = await _factory()
    async with factory() as session:
        household, person = await _seed_person(session)
        provider = FakeKnowledgeProvider()
        base = await _propose(session, provider, household, person, predicate="base")
        await session.commit()
        assert isinstance(base, KnowledgeFactRecord)
        dependent = await _propose(session, provider, household, person, predicate="derived")
        await session.commit()
        assert isinstance(dependent, KnowledgeFactRecord)
        await confirm_observation(session, provider, ha_user_id="ha-user-1", fact_id=dependent.id)
        dependent.depends_on = [base.id]
        await session.commit()

        await reject_observation(session, provider, ha_user_id="ha-user-1", fact_id=base.id)
        await session.commit()

        refreshed_dependent = await session.get(KnowledgeFactRecord, dependent.id)
        assert refreshed_dependent is not None
        assert refreshed_dependent.knowledge_state == "expired"


async def test_correct_fact_updates_the_value_and_revises_the_provider_body() -> None:
    factory = await _factory()
    async with factory() as session:
        household, person = await _seed_person(session)
        provider = FakeKnowledgeProvider()
        pending = await _propose(session, provider, household, person)
        await session.commit()
        assert isinstance(pending, KnowledgeFactRecord)
        confirmed = await confirm_observation(
            session, provider, ha_user_id="ha-user-1", fact_id=pending.id
        )
        await session.commit()
        assert isinstance(confirmed, KnowledgeFactRecord)

        corrected = await correct_fact(
            session,
            provider,
            ha_user_id="ha-user-1",
            fact_id=confirmed.id,
            value="green tea",
            confidence=0.95,
        )
        await session.commit()

        assert isinstance(corrected, KnowledgeFactRecord)
        assert corrected.value == "green tea"
        assert corrected.confidence == 0.95
        assert ("revise_fact", {"fact_id": "fake-fact-1", "value": "green tea"}) in provider.calls


async def test_correct_fact_only_applies_to_a_confirmed_fact() -> None:
    factory = await _factory()
    async with factory() as session:
        household, person = await _seed_person(session)
        provider = FakeKnowledgeProvider()
        pending = await _propose(session, provider, household, person)
        await session.commit()
        assert isinstance(pending, KnowledgeFactRecord)

        result = await correct_fact(
            session, provider, ha_user_id="ha-user-1", fact_id=pending.id, value="green tea"
        )
        assert isinstance(result, NotConfirmed)


async def test_reclassify_fact_updates_privacy_and_the_provider_body() -> None:
    factory = await _factory()
    async with factory() as session:
        household, person = await _seed_person(session)
        provider = FakeKnowledgeProvider()
        pending = await _propose(session, provider, household, person)
        await session.commit()
        assert isinstance(pending, KnowledgeFactRecord)
        confirmed = await confirm_observation(
            session, provider, ha_user_id="ha-user-1", fact_id=pending.id
        )
        await session.commit()
        assert isinstance(confirmed, KnowledgeFactRecord)
        assert confirmed.privacy == "personal"

        reclassified = await reclassify_fact(
            session,
            provider,
            ha_user_id="ha-user-1",
            fact_id=confirmed.id,
            privacy="household",
        )
        await session.commit()

        assert isinstance(reclassified, KnowledgeFactRecord)
        assert reclassified.privacy == "household"
        assert (
            "reclassify_fact",
            {"fact_id": "fake-fact-1", "privacy": "household"},
        ) in provider.calls


async def test_reclassify_fact_only_applies_to_a_confirmed_fact() -> None:
    factory = await _factory()
    async with factory() as session:
        household, person = await _seed_person(session)
        provider = FakeKnowledgeProvider()
        pending = await _propose(session, provider, household, person)
        await session.commit()
        assert isinstance(pending, KnowledgeFactRecord)

        result = await reclassify_fact(
            session, provider, ha_user_id="ha-user-1", fact_id=pending.id, privacy="household"
        )
        assert isinstance(result, NotConfirmed)


async def test_delete_fact_disposes_a_confirmed_fact() -> None:
    factory = await _factory()
    async with factory() as session:
        household, person = await _seed_person(session)
        provider = FakeKnowledgeProvider()
        pending = await _propose(session, provider, household, person)
        await session.commit()
        assert isinstance(pending, KnowledgeFactRecord)
        confirmed = await confirm_observation(
            session, provider, ha_user_id="ha-user-1", fact_id=pending.id
        )
        await session.commit()
        assert isinstance(confirmed, KnowledgeFactRecord)

        result = await delete_fact(session, provider, ha_user_id="ha-user-1", fact_id=confirmed.id)
        await session.commit()

        assert isinstance(result, Disposed)
        refreshed = await session.get(KnowledgeFactRecord, confirmed.id)
        assert refreshed is not None
        assert refreshed.knowledge_state == "deleted"


async def test_list_confirmed_facts_excludes_pending_and_other_owners() -> None:
    factory = await _factory()
    async with factory() as session:
        household, owner = await _seed_person(session, ha_user_id="ha-user-1")
        _, other = await _seed_person(session, household=household, ha_user_id="ha-user-2")
        provider = FakeKnowledgeProvider()
        own_pending = await _propose(session, provider, household, owner, predicate="pending")
        own_confirmed = await _propose(session, provider, household, owner, predicate="confirmed")
        other_confirmed = await _propose(session, provider, household, other, predicate="other")
        await session.commit()
        assert isinstance(own_pending, KnowledgeFactRecord)
        assert isinstance(own_confirmed, KnowledgeFactRecord)
        assert isinstance(other_confirmed, KnowledgeFactRecord)
        await confirm_observation(session, provider, ha_user_id="ha-user-1", fact_id=own_confirmed.id)
        await confirm_observation(session, provider, ha_user_id="ha-user-2", fact_id=other_confirmed.id)
        await session.commit()

        facts = await list_confirmed_facts(session, ha_user_id="ha-user-1")
        assert not isinstance(facts, Unmapped)
        assert [fact.id for fact in facts] == [own_confirmed.id]


@dataclass
class FakeExtractionModel:
    """Fake ``ModelProvider`` that hands back a canned extraction reply and records the call."""

    reply_text: str
    name: str = "fake"
    calls: list[tuple[str, tuple[ModelMessage, ...]]] = field(default_factory=list)

    async def generate_reply(self, *, system_prompt: str, messages: Sequence[ModelMessage]) -> ModelReply:
        self.calls.append((system_prompt, tuple(messages)))
        return ModelReply(content=self.reply_text)


async def test_extract_candidate_observations_parses_a_well_formed_reply() -> None:
    model = FakeExtractionModel(
        reply_text=(
            '{"observations": [{"subject": "Example Adult", "predicate": "likes", '
            '"value": "tea", "privacy": "personal", "confidence": 0.8}]}'
        )
    )

    candidates = await extract_candidate_observations(
        model, person_display_name="Example Adult", message_text="I really like tea."
    )

    assert candidates == [
        CandidateObservation(
            subject="Example Adult", predicate="likes", value="tea", privacy="personal", confidence=0.8
        )
    ]
    assert len(model.calls) == 1
    system_prompt, messages = model.calls[0]
    assert "Example Adult" in system_prompt
    assert messages == (ModelMessage(role="user", content="I really like tea."),)


async def test_extract_candidate_observations_ignores_a_non_json_reply() -> None:
    model = FakeExtractionModel(reply_text="Sure, I can help with that!")

    candidates = await extract_candidate_observations(
        model, person_display_name="Example Adult", message_text="hello"
    )

    assert candidates == []


async def test_extract_candidate_observations_drops_entries_with_invalid_privacy_or_missing_fields() -> None:
    # At most MAX_EXTRACTED_OBSERVATIONS items, so the cap doesn't shadow the filtering this
    # test is actually exercising (see test_..._caps_the_number_of_candidates for that).
    model = FakeExtractionModel(
        reply_text=(
            '{"observations": ['
            '{"subject": "Example Adult", "predicate": "likes", "value": "tea", "privacy": "public"},'
            '{"subject": "Example Adult", "predicate": "likes", "value": "coffee"},'
            '{"subject": "Example Adult", "predicate": "likes", "value": "cocoa", "privacy": "household", '
            '"confidence": 5}'
            "]}"
        )
    )

    candidates = await extract_candidate_observations(
        model, person_display_name="Example Adult", message_text="various drinks"
    )

    assert candidates == [
        CandidateObservation(
            subject="Example Adult", predicate="likes", value="cocoa", privacy="household", confidence=1.0
        )
    ]


async def test_extract_candidate_observations_caps_the_number_of_candidates() -> None:
    items = ",".join(
        f'{{"subject": "Example Adult", "predicate": "likes", "value": "item-{i}", "privacy": "personal"}}'
        for i in range(MAX_EXTRACTED_OBSERVATIONS + 5)
    )
    model = FakeExtractionModel(reply_text=f'{{"observations": [{items}]}}')

    candidates = await extract_candidate_observations(
        model, person_display_name="Example Adult", message_text="lots of preferences"
    )

    assert len(candidates) == MAX_EXTRACTED_OBSERVATIONS


async def test_proposing_an_extracted_observation_uses_the_conversation_inference_source() -> None:
    factory = await _factory()
    async with factory() as session:
        household, person = await _seed_person(session)
        provider = FakeKnowledgeProvider()

        record = await propose_observation(
            session,
            provider,
            household_id=household.id,
            owner_person_id=person.id,
            assistant_id=None,
            subject=person.display_name,
            predicate="likes",
            value="tea",
            privacy="personal",
            source_system=CONVERSATION_INFERENCE_SOURCE,
            confidence=0.8,
        )

        assert isinstance(record, KnowledgeFactRecord)
        assert record.source_system == "conversation-inference"
