from __future__ import annotations

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from kinward.app import create_app
from kinward.application.integration_tokens import create_token, revoke_token
from kinward.config import Settings
from kinward.persistence.models import (
    AssistantRecord,
    Base,
    HouseholdRecord,
    IntegrationTokenRecord,
    PersonRecord,
    TopicTurnRecord,
)
from kinward.persistence.session import session_dependency


async def _client():  # type: ignore[no-untyped-def]
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_session():  # type: ignore[no-untyped-def]
        async with factory() as session:
            yield session

    app = create_app(Settings(environment="test"))
    app.dependency_overrides[session_dependency] = override_session
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")
    return client, factory


async def _seed_household(factory) -> None:  # type: ignore[no-untyped-def]
    async with factory() as session:
        household = HouseholdRecord(name="Example House")
        session.add(household)
        await session.flush()
        session.add_all(
            [
                PersonRecord(
                    household_id=household.id,
                    display_name="Example Adult",
                    role="admin",
                    profile_kind="adult",
                    ha_person_id="ha-person-admin",
                ),
                PersonRecord(
                    household_id=household.id,
                    display_name="Example Child",
                    role="member",
                    profile_kind="child",
                    classification="private-child",
                ),
            ]
        )
        await session.commit()


async def _seed_household_with_synced_admin(factory):  # type: ignore[no-untyped-def]
    """Seed a household with an admin whose HA login is synced, plus one child (no login)."""
    async with factory() as session:
        household = HouseholdRecord(name="Example House")
        session.add(household)
        await session.flush()
        admin = PersonRecord(
            household_id=household.id,
            display_name="Example Adult",
            role="admin",
            profile_kind="adult",
            ha_person_id="ha-person-admin",
            ha_user_id="ha-user-1",
        )
        child = PersonRecord(
            household_id=household.id,
            display_name="Example Child",
            role="member",
            profile_kind="child",
            classification="private-child",
        )
        session.add_all([admin, child])
        await session.commit()
        return admin.id, child.id


async def _issue_token(factory) -> str:  # type: ignore[no-untyped-def]
    async with factory() as session:
        _record, plaintext = await create_token(session, "Home Assistant")
        await session.commit()
    return plaintext


async def test_context_requires_a_bearer_token() -> None:
    client, _factory = await _client()
    async with client:
        response = await client.get("/api/v1/integration/context")
        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "invalid_integration_token"


async def test_context_rejects_unknown_or_malformed_tokens() -> None:
    client, _factory = await _client()
    async with client:
        response = await client.get(
            "/api/v1/integration/context", headers={"Authorization": "Bearer not-a-real-token"}
        )
        assert response.status_code == 401


async def test_context_and_summary_report_the_household() -> None:
    client, factory = await _client()
    async with client:
        await _seed_household(factory)
        token = await _issue_token(factory)
        headers = {"Authorization": f"Bearer {token}"}

        context = await client.get("/api/v1/integration/context", headers=headers)
        assert context.status_code == 200
        body = context.json()
        assert body["householdName"] == "Example House"
        assert body["contractVersion"] == "v1"
        household_id = body["householdId"]

        summary = await client.get("/api/v1/integration/summary", headers=headers)
        assert summary.status_code == 200
        summary_body = summary.json()
        assert summary_body["household"] == {"adultCount": 1, "childCount": 1}
        assert summary_body["briefing"] == {
            "state": "intentionally-disabled",
            "reason": "not-yet-implemented",
            "summary": None,
        }
        assert summary_body["attention"] == {
            "state": "intentionally-disabled",
            "reason": "not-yet-implemented",
            "count": None,
        }
        assert summary_body["nextEvent"] == {
            "state": "intentionally-disabled",
            "reason": "not-yet-implemented",
            "summary": None,
            "startsAt": None,
        }

        second_context = await client.get("/api/v1/integration/context", headers=headers)
        assert second_context.json()["householdId"] == household_id


async def test_revoked_token_is_rejected() -> None:
    client, factory = await _client()
    async with client:
        await _seed_household(factory)
        token = await _issue_token(factory)
        async with factory() as session:
            record = await session.scalar(select(IntegrationTokenRecord))
            assert record is not None
            await revoke_token(session, record.id)
            await session.commit()

        response = await client.get(
            "/api/v1/integration/context", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401


async def test_no_household_reports_a_distinct_conflict() -> None:
    client, factory = await _client()
    async with client:
        token = await _issue_token(factory)

        response = await client.get(
            "/api/v1/integration/context", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "household_not_configured"


async def test_people_lists_every_synced_person() -> None:
    client, factory = await _client()
    async with client:
        admin_id, child_id = await _seed_household_with_synced_admin(factory)
        token = await _issue_token(factory)

        response = await client.get(
            "/api/v1/integration/people", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json() == sorted(
            [
                {"id": admin_id, "displayName": "Example Adult"},
                {"id": child_id, "displayName": "Example Child"},
            ],
            key=lambda item: item["displayName"],
        )


async def test_sync_people_creates_and_updates_by_ha_person_id() -> None:
    client, factory = await _client()
    async with client:
        await _seed_household(factory)
        token = await _issue_token(factory)
        headers = {"Authorization": f"Bearer {token}"}

        created = await client.put(
            "/api/v1/integration/people/sync",
            headers=headers,
            json=[{"haPersonId": "ha-person-lisa", "displayName": "Lisa"}],
        )
        assert created.status_code == 200
        body = created.json()
        assert len(body) == 1
        assert body[0]["haPersonId"] == "ha-person-lisa"
        assert body[0]["haUserId"] is None
        assert body[0]["role"] == "member"
        person_id = body[0]["id"]

        renamed = await client.put(
            "/api/v1/integration/people/sync",
            headers=headers,
            json=[{"haPersonId": "ha-person-lisa", "haUserId": "ha-user-lisa", "displayName": "Elisabeth"}],
        )
        assert renamed.status_code == 200
        renamed_body = renamed.json()
        assert renamed_body[0]["id"] == person_id
        assert renamed_body[0]["displayName"] == "Elisabeth"
        assert renamed_body[0]["haUserId"] == "ha-user-lisa"

        async with factory() as session:
            assistant = await session.scalar(
                select(AssistantRecord).where(AssistantRecord.owner_person_id == person_id)
            )
            assert assistant is not None and assistant.kind == "primary"


async def test_sync_derives_admin_role_from_is_admin_and_allows_multiple_admins() -> None:
    """Kinward has no admin designation of its own - HA's own admin flag is the whole rule."""
    client, factory = await _client()
    async with client:
        async with factory() as session:
            session.add(HouseholdRecord(name="Example House"))
            await session.commit()
        token = await _issue_token(factory)
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.put(
            "/api/v1/integration/people/sync",
            headers=headers,
            json=[
                {"haPersonId": "ha-person-1", "haUserId": "ha-user-1", "displayName": "Marc", "isAdmin": True},
                {"haPersonId": "ha-person-2", "haUserId": "ha-user-2", "displayName": "Lisa", "isAdmin": True},
                {"haPersonId": "ha-person-3", "displayName": "Kid", "isAdmin": False},
            ],
        )
        assert response.status_code == 200
        roles = {person["haPersonId"]: person["role"] for person in response.json()}
        assert roles == {"ha-person-1": "admin", "ha-person-2": "admin", "ha-person-3": "member"}

        demoted = await client.put(
            "/api/v1/integration/people/sync",
            headers=headers,
            json=[{"haPersonId": "ha-person-1", "haUserId": "ha-user-1", "displayName": "Marc", "isAdmin": False}],
        )
        assert demoted.status_code == 200
        assert demoted.json()[0]["role"] == "member"


async def test_integration_endpoints_require_a_bearer_token() -> None:
    client, _factory = await _client()
    async with client:
        assert (await client.get("/api/v1/integration/people")).status_code == 401
        assert (await client.put("/api/v1/integration/people/sync", json=[])).status_code == 401
        assert (
            await client.post("/api/v1/integration/conversation", json={"haUserId": "x", "text": "hi"})
        ).status_code == 401


async def test_conversation_reports_unmapped_users_truthfully() -> None:
    client, factory = await _client()
    async with client:
        await _seed_household_with_synced_admin(factory)
        token = await _issue_token(factory)

        response = await client.post(
            "/api/v1/integration/conversation",
            headers={"Authorization": f"Bearer {token}"},
            json={"haUserId": "unmapped-ha-user", "text": "hello"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["mapped"] is False
        assert body["outcome"] == "unmapped"
        assert body["conversationId"] is None


async def test_conversation_persists_and_continues_a_topic_for_a_mapped_user() -> None:
    client, factory = await _client()
    async with client:
        admin_id, _child_id = await _seed_household_with_synced_admin(factory)
        async with factory() as session:
            admin = await session.get(PersonRecord, admin_id)
            assert admin is not None
            session.add(
                AssistantRecord(
                    household_id=admin.household_id,
                    owner_person_id=admin_id,
                    name="Atlas",
                    kind="primary",
                )
            )
            await session.commit()
        token = await _issue_token(factory)
        headers = {"Authorization": f"Bearer {token}"}

        first = await client.post(
            "/api/v1/integration/conversation",
            headers=headers,
            json={"haUserId": "ha-user-1", "text": "hello"},
        )
        assert first.status_code == 200
        first_body = first.json()
        assert first_body["mapped"] is True
        assert first_body["outcome"] == "completed"
        assert first_body["conversationId"]

        second = await client.post(
            "/api/v1/integration/conversation",
            headers=headers,
            json={
                "haUserId": "ha-user-1",
                "text": "still there?",
                "conversationId": first_body["conversationId"],
            },
        )
        assert second.status_code == 200
        assert second.json()["conversationId"] == first_body["conversationId"]


async def test_cancel_turn_reports_already_terminal_for_a_real_turn() -> None:
    client, factory = await _client()
    async with client:
        admin_id, _child_id = await _seed_household_with_synced_admin(factory)
        async with factory() as session:
            admin = await session.get(PersonRecord, admin_id)
            assert admin is not None
            session.add(
                AssistantRecord(
                    household_id=admin.household_id,
                    owner_person_id=admin_id,
                    name="Atlas",
                    kind="primary",
                )
            )
            await session.commit()
        token = await _issue_token(factory)
        headers = {"Authorization": f"Bearer {token}"}

        conversation_response = await client.post(
            "/api/v1/integration/conversation",
            headers=headers,
            json={"haUserId": "ha-user-1", "text": "hello"},
        )
        topic_id = conversation_response.json()["conversationId"]

        async with factory() as session:
            turn = (
                await session.scalars(
                    select(TopicTurnRecord).where(TopicTurnRecord.topic_id == topic_id)
                )
            ).one()
            turn_id = turn.id

        cancel_response = await client.post(
            f"/api/v1/integration/conversation/turns/{turn_id}/cancel",
            headers=headers,
            json={"haUserId": "ha-user-1"},
        )
        assert cancel_response.status_code == 200
        body = cancel_response.json()
        assert body == {"turnId": turn_id, "outcome": "completed", "alreadyTerminal": True}


async def test_cancel_turn_not_found_is_indistinguishable_from_unmapped() -> None:
    client, factory = await _client()
    async with client:
        await _seed_household_with_synced_admin(factory)
        token = await _issue_token(factory)
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(
            "/api/v1/integration/conversation/turns/does-not-exist/cancel",
            headers=headers,
            json={"haUserId": "unmapped-ha-user"},
        )
        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "turn_not_found"


async def _mapped_headers_and_topic(client, factory):  # type: ignore[no-untyped-def]
    """Seed a synced admin, create one topic via /conversation, return (auth headers, topic_id)."""
    admin_id, _child_id = await _seed_household_with_synced_admin(factory)
    async with factory() as session:
        admin = await session.get(PersonRecord, admin_id)
        assert admin is not None
        session.add(
            AssistantRecord(
                household_id=admin.household_id, owner_person_id=admin_id, name="Atlas", kind="primary"
            )
        )
        await session.commit()
    token = await _issue_token(factory)
    headers = {"Authorization": f"Bearer {token}"}
    conversation_response = await client.post(
        "/api/v1/integration/conversation",
        headers=headers,
        json={"haUserId": "ha-user-1", "text": "hello"},
    )
    return headers, conversation_response.json()["conversationId"]


async def test_topics_list_and_detail() -> None:
    client, factory = await _client()
    async with client:
        headers, topic_id = await _mapped_headers_and_topic(client, factory)

        listing = await client.get(
            "/api/v1/integration/topics?haUserId=ha-user-1", headers=headers
        )
        assert listing.status_code == 200
        assert [topic["id"] for topic in listing.json()] == [topic_id]
        assert listing.json()[0]["state"] == "open"
        assert listing.json()[0]["title"] is None

        detail = await client.get(
            f"/api/v1/integration/topics/{topic_id}?haUserId=ha-user-1", headers=headers
        )
        assert detail.status_code == 200
        detail_body = detail.json()
        assert detail_body["id"] == topic_id
        assert len(detail_body["turns"]) == 1
        assert detail_body["turns"][0]["requestText"] == "hello"
        assert detail_body["turns"][0]["outcome"] == "completed"


async def test_topics_list_fails_closed_for_unmapped_ha_user() -> None:
    client, factory = await _client()
    async with client:
        headers, _topic_id = await _mapped_headers_and_topic(client, factory)

        response = await client.get(
            "/api/v1/integration/topics?haUserId=unmapped-ha-user", headers=headers
        )
        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "topic_not_found"


async def test_rename_archive_reopen_and_delete_a_topic() -> None:
    client, factory = await _client()
    async with client:
        headers, topic_id = await _mapped_headers_and_topic(client, factory)

        rename = await client.patch(
            f"/api/v1/integration/topics/{topic_id}",
            headers=headers,
            json={"haUserId": "ha-user-1", "title": "Weekend plans"},
        )
        assert rename.status_code == 200
        assert rename.json()["title"] == "Weekend plans"
        assert rename.json()["state"] == "open"

        archive = await client.patch(
            f"/api/v1/integration/topics/{topic_id}",
            headers=headers,
            json={"haUserId": "ha-user-1", "state": "archived"},
        )
        assert archive.status_code == 200
        assert archive.json()["state"] == "archived"
        assert archive.json()["title"] == "Weekend plans"

        reopen = await client.patch(
            f"/api/v1/integration/topics/{topic_id}",
            headers=headers,
            json={"haUserId": "ha-user-1", "state": "open"},
        )
        assert reopen.status_code == 200
        assert reopen.json()["state"] == "open"

        delete = await client.delete(
            f"/api/v1/integration/topics/{topic_id}?haUserId=ha-user-1", headers=headers
        )
        assert delete.status_code == 204

        after_delete = await client.get(
            f"/api/v1/integration/topics/{topic_id}?haUserId=ha-user-1", headers=headers
        )
        assert after_delete.status_code == 404


async def test_topic_endpoints_fail_closed_for_a_different_mapped_person() -> None:
    client, factory = await _client()
    async with client:
        headers, topic_id = await _mapped_headers_and_topic(client, factory)

        async with factory() as session:
            household = (await session.scalars(select(HouseholdRecord))).one()
            other_person = PersonRecord(
                household_id=household.id,
                display_name="Other Adult",
                role="member",
                profile_kind="adult",
                ha_person_id="ha-person-other",
                ha_user_id="ha-user-2",
            )
            session.add(other_person)
            await session.flush()
            session.add(
                AssistantRecord(
                    household_id=household.id,
                    owner_person_id=other_person.id,
                    name="Nova",
                    kind="primary",
                )
            )
            await session.commit()

        response = await client.patch(
            f"/api/v1/integration/topics/{topic_id}",
            headers=headers,
            json={"haUserId": "ha-user-2", "title": "not yours"},
        )
        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "topic_not_found"


async def test_pet_crud_requires_admin_and_round_trips() -> None:
    client, factory = await _client()
    async with client:
        admin_id, child_id = await _seed_household_with_synced_admin(factory)
        token = await _issue_token(factory)
        headers = {"Authorization": f"Bearer {token}"}

        forbidden = await client.post(
            "/api/v1/integration/pets",
            headers=headers,
            json={"haUserId": "not-mapped", "displayName": "Biscuit", "species": "Dog"},
        )
        assert forbidden.status_code == 403
        assert forbidden.json()["detail"]["code"] == "admin_required"

        created = await client.post(
            "/api/v1/integration/pets",
            headers=headers,
            json={
                "haUserId": "ha-user-1",
                "displayName": "Biscuit",
                "species": "Dog",
                "sharedFacts": ["Needs a walk every morning"],
            },
        )
        assert created.status_code == 201
        pet_id = created.json()["id"]
        assert created.json()["sharedFacts"] == ["Needs a walk every morning"]

        listed = await client.get("/api/v1/integration/pets", headers=headers)
        assert listed.status_code == 200
        assert [pet["displayName"] for pet in listed.json()] == ["Biscuit"]

        updated = await client.patch(
            f"/api/v1/integration/pets/{pet_id}",
            headers=headers,
            json={"haUserId": "ha-user-1", "species": "Golden Retriever"},
        )
        assert updated.status_code == 200
        assert updated.json()["species"] == "Golden Retriever"

        deleted = await client.delete(
            f"/api/v1/integration/pets/{pet_id}?haUserId=ha-user-1", headers=headers
        )
        assert deleted.status_code == 204

        after_delete = await client.get("/api/v1/integration/pets", headers=headers)
        assert after_delete.json() == []

        _ = child_id, admin_id


async def test_reclassify_person_requires_admin_and_updates_profile_kind() -> None:
    client, factory = await _client()
    async with client:
        admin_id, child_id = await _seed_household_with_synced_admin(factory)
        token = await _issue_token(factory)
        headers = {"Authorization": f"Bearer {token}"}

        forbidden = await client.patch(
            f"/api/v1/integration/people/{child_id}/reclassify",
            headers=headers,
            json={"haUserId": "not-mapped", "profileKind": "teen"},
        )
        assert forbidden.status_code == 403

        response = await client.patch(
            f"/api/v1/integration/people/{child_id}/reclassify",
            headers=headers,
            json={"haUserId": "ha-user-1", "profileKind": "teen"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["profileKind"] == "teen"
        assert body["classification"] == "private-person"

        missing = await client.patch(
            "/api/v1/integration/people/does-not-exist/reclassify",
            headers=headers,
            json={"haUserId": "ha-user-1", "profileKind": "adult"},
        )
        assert missing.status_code == 404
        assert missing.json()["detail"]["code"] == "person_not_found"

        _ = admin_id


async def test_delete_person_blocks_removing_the_sole_admin() -> None:
    client, factory = await _client()
    async with client:
        admin_id, child_id = await _seed_household_with_synced_admin(factory)
        token = await _issue_token(factory)
        headers = {"Authorization": f"Bearer {token}"}

        blocked = await client.delete(
            f"/api/v1/integration/people/{admin_id}?haUserId=ha-user-1", headers=headers
        )
        assert blocked.status_code == 409
        assert blocked.json()["detail"]["code"] == "household_requires_an_admin"

        allowed = await client.delete(
            f"/api/v1/integration/people/{child_id}?haUserId=ha-user-1", headers=headers
        )
        assert allowed.status_code == 204

        async with factory() as session:
            assert await session.get(PersonRecord, child_id) is None
            assert await session.get(PersonRecord, admin_id) is not None


async def test_owner_can_customize_their_own_assistant_via_api() -> None:
    client, factory = await _client()
    async with client:
        await _seed_household(factory)
        token = await _issue_token(factory)
        headers = {"Authorization": f"Bearer {token}"}

        synced = await client.put(
            "/api/v1/integration/people/sync",
            headers=headers,
            json=[{"haPersonId": "ha-person-marc", "haUserId": "ha-user-marc", "displayName": "Marc"}],
        )
        assert synced.status_code == 200

        response = await client.patch(
            "/api/v1/integration/assistants/primary",
            headers=headers,
            json={"haUserId": "ha-user-marc", "name": "Jarvis", "personality": {"tone": "warm"}},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "Jarvis"
        assert body["personality"] == {"tone": "warm"}

        unmapped = await client.patch(
            "/api/v1/integration/assistants/primary",
            headers=headers,
            json={"haUserId": "not-mapped", "name": "Nope"},
        )
        assert unmapped.status_code == 404
        assert unmapped.json()["detail"]["code"] == "assistant_not_found"
