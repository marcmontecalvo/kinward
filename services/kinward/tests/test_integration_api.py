from __future__ import annotations

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from kinward.app import create_app
from kinward.application.integration_tokens import create_token, revoke_token
from kinward.config import Settings
from kinward.persistence.models import (
    AccountRecord,
    AssistantRecord,
    Base,
    HouseholdRecord,
    IntegrationTokenRecord,
    PersonRecord,
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


async def _seed_household_with_account(factory):  # type: ignore[no-untyped-def]
    async with factory() as session:
        household = HouseholdRecord(name="Example House")
        session.add(household)
        await session.flush()
        admin = PersonRecord(
            household_id=household.id,
            display_name="Example Adult",
            role="admin",
            profile_kind="adult",
        )
        child = PersonRecord(
            household_id=household.id,
            display_name="Example Child",
            role="member",
            profile_kind="child",
            classification="private-child",
        )
        session.add_all([admin, child])
        await session.flush()
        session.add(
            AccountRecord(
                household_id=household.id,
                person_id=admin.id,
                email="adult@example.invalid",
                password_verifier="x",
            )
        )
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


async def test_people_lists_only_account_bearing_people() -> None:
    client, factory = await _client()
    async with client:
        admin_id, _child_id = await _seed_household_with_account(factory)
        token = await _issue_token(factory)

        response = await client.get(
            "/api/v1/integration/people", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json() == [{"id": admin_id, "displayName": "Example Adult"}]


async def test_ha_user_mappings_round_trip() -> None:
    client, factory = await _client()
    async with client:
        admin_id, _child_id = await _seed_household_with_account(factory)
        token = await _issue_token(factory)
        headers = {"Authorization": f"Bearer {token}"}

        empty = await client.get("/api/v1/integration/ha-user-mappings", headers=headers)
        assert empty.json() == []

        put_response = await client.put(
            "/api/v1/integration/ha-user-mappings",
            headers=headers,
            json=[{"haUserId": "ha-user-1", "personId": admin_id}],
        )
        assert put_response.status_code == 200
        assert put_response.json() == [{"haUserId": "ha-user-1", "personId": admin_id}]

        listed = await client.get("/api/v1/integration/ha-user-mappings", headers=headers)
        assert listed.json() == [{"haUserId": "ha-user-1", "personId": admin_id}]

        delete_response = await client.delete(
            "/api/v1/integration/ha-user-mappings/ha-user-1", headers=headers
        )
        assert delete_response.status_code == 204

        after_delete = await client.get("/api/v1/integration/ha-user-mappings", headers=headers)
        assert after_delete.json() == []


async def test_ha_user_mappings_rejects_a_non_account_bearing_person() -> None:
    client, factory = await _client()
    async with client:
        _admin_id, child_id = await _seed_household_with_account(factory)
        token = await _issue_token(factory)
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.put(
            "/api/v1/integration/ha-user-mappings",
            headers=headers,
            json=[{"haUserId": "ha-user-1", "personId": child_id}],
        )
        assert response.status_code == 422
        assert response.json()["detail"]["code"] == "person_not_account_bearing"

        after_failed_put = await client.get(
            "/api/v1/integration/ha-user-mappings", headers=headers
        )
        assert after_failed_put.json() == []


async def test_ha_user_mapping_endpoints_require_a_bearer_token() -> None:
    client, _factory = await _client()
    async with client:
        assert (await client.get("/api/v1/integration/people")).status_code == 401
        assert (await client.get("/api/v1/integration/ha-user-mappings")).status_code == 401
        assert (
            await client.put("/api/v1/integration/ha-user-mappings", json=[])
        ).status_code == 401
        assert (
            await client.delete("/api/v1/integration/ha-user-mappings/ha-user-1")
        ).status_code == 401
        assert (
            await client.post("/api/v1/integration/conversation", json={"haUserId": "x", "text": "hi"})
        ).status_code == 401


async def test_conversation_reports_unmapped_users_truthfully() -> None:
    client, factory = await _client()
    async with client:
        await _seed_household_with_account(factory)
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
        admin_id, _child_id = await _seed_household_with_account(factory)
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

        put_response = await client.put(
            "/api/v1/integration/ha-user-mappings",
            headers=headers,
            json=[{"haUserId": "ha-user-1", "personId": admin_id}],
        )
        assert put_response.status_code == 200

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
