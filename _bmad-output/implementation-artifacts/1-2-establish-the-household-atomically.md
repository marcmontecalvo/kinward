---
baseline_commit: 2492dc8f6b337c83e51932732c174d30e705db07
---

# Story 1.2: Establish the Household Atomically

Status: review

## Story

As the initial household administrator,
I want to establish my household and its foundational profiles and assistants in one secure operation,
so that Kinward never presents a partial, duplicated, or ambiguously owned household as usable.

## Acceptance Criteria

1. A clean deployment exposes one fail-closed bootstrap path requiring a one-time setup authorization and explicit CSRF protection; no optional provider is required.
2. One application command atomically creates exactly one household, administrator profile and account binding, password verifier, administrator-owned primary assistant, ownerless household fallback assistant, and every selected adult, child, and pet profile. It creates no tenant/control-plane, entitlement, billing, support-access, specialist, routine, integration, room, device, schedule, notification, or layout object.
3. A pet has no account, assistant, private memory, credential, approval/delegation/action authority; only explicitly entered household-shared care or relationship facts may be stored.
4. Sequential and concurrent exact replays with the same idempotency identity return the prior committed result and create no duplicates; conflicting reuse fails without changing state.
5. Validation, policy, persistence, or transaction failure leaves no usable partial household, orphan binding/assistant/relationship, active setup authorization, activity, or outbox effect; the safe result says whether retry or reset/restore is required.
6. After commit, every bootstrap attempt is rejected, the setup capability is terminally invalidated, and status/health responses expose no verifier, private field, or reusable capability.
7. Passwords use the adopted Argon2id-equivalent mechanism and plaintext never reaches storage or logs. The mutation follows handler -> application service -> policy -> UoW -> domain/persistence -> classified activity/outbox.
8. Every created record declares household-local ownership/classification, version, backup/import eligibility, restore/quarantine disposition, and retention/deletion behavior. Keyboard-only completion uses ordinary household language and fictional fixtures.

Addresses `FR-001`, `FR-002`, `FR-011`, bootstrap `FR-091`, `NFR-002`, `NFR-007`, `NFR-025`, `NFR-027`, `NFR-030`, `NFR-032`, `NFR-040`, `UX-DR29`, `AD-01`, `AD-17`, `AD-19`, `AD-23`, and `AD-24`.

## Tasks / Subtasks

- [x] Define the framework-free bootstrap contract and invariants (AC: 1-8)
  - [x] Add typed bootstrap command/result, selected-profile and pet inputs, normalized request fingerprint, idempotency identity, safe error codes, and retryability.
  - [x] Model household/account/profile/assistant ownership and one-household invariants without `tenant_id`; UUID IDs and UTC timestamps only.
  - [x] Define explicit lifecycle metadata for every created type and reject specialist/additional assistant creation.
- [x] Add security and application seams (AC: 1, 4-7)
  - [x] Implement a random, expiring, hashed-at-rest, one-use setup capability; never return its verifier from status/health.
  - [x] Choose and document the AD-01-compliant password/CSRF mechanics; use secure server-side verification and privacy-safe errors.
  - [x] Replace route-owned persistence with a thin `/api/v1` handler dispatching one bootstrap application service through policy and one UoW.
- [x] Complete the pre-freeze `001_initial_single_household` model (AC: 2-7)
  - [x] Add account binding/verifier, setup capability, bootstrap idempotency/result, profile/pet/relationship, record-version/classification, and transactional activity/outbox state with database constraints enforcing the one-household and assistant cardinalities.
  - [x] Keep `001` as `down_revision = None`; do not add legacy migrations. Keep ORM metadata and Alembic identical.
  - [x] Make equal replay/concurrent execution database-safe on SQLite; preserve future PostgreSQL contract semantics without claiming parity.
- [x] Build the accessible setup experience (AC: 1-3, 5, 8)
  - [x] Collect household/admin/account/primary-assistant values plus optional adult, child, and pet profiles; explain errors and outcomes in household language.
  - [x] Require no integration or technical configuration and keep all examples obviously fictional.
- [x] Prove atomicity, secrecy, and recovery behavior (AC: 1-8)
  - [x] Test success graph, ownerless fallback, pet prohibitions, rollback at every stage, exact/conflicting replay, concurrent submissions, second-household denial, consumed/expired capability, CSRF denial, password non-disclosure, and sanitized logs/status.
  - [x] Run migration/model consistency and API contract tests plus `make lint`, `make typecheck`, `make test`, and `make build`.

## Dev Notes

### Current State and Required Changes

- `services/kinward/src/kinward/api/setup.py` is unversioned, performs count/check/insert/commit directly, has no setup capability, account/password, CSRF, fallback assistant, selected profiles, idempotency, activity, or outbox. Replace this behavior; do not layer more direct writes onto it. Preserve only useful validation and safe “already configured” language.
- `PersonRecord`, `AssistantRecord`, and `001_initial_single_household` are partial pre-freeze models. Current uniqueness does not safely enforce concurrent one-household bootstrap or exactly one primary assistant. Database constraints plus the application policy must enforce invariants.
- Existing `validate_owner_count` is reusable framework-free logic, but it is not sufficient persistence enforcement. Extend domain rules rather than importing ORM/FastAPI inward.
- Story 1.1 established one-shot migrations, SQL outbox readiness, truthful health, same-origin deployment, and current dependency policy. Preserve those seams and do not regress clean `docker compose up` without providers.

### Architecture and Scope Guardrails

- One deployable backend, one household, one transaction. Routes parse/dispatch only; no ORM entities as API responses.
- Bootstrap is not ordinary login/session/invitation or ongoing profile management. Create the first account binding and secure bootstrap boundary only; Epic 2 owns normal authenticated sessions and Epic 3 owns later membership lifecycle.
- Primary assistant has exactly one owner. Fallback is household-owned with no personal owner and no private-memory query path. Pets never acquire person authority.
- Amend the unreleased baseline only before the Milestone A evidence freeze; otherwise use a forward migration and document why.
- Provider absence must remain harmless. No model call is allowed in setup.
- Public evidence must contain no real household names, emails, schedules, credentials, hosts, or deployment URLs.

### Testing and Evidence Ownership

- BE: domain/application/UoW, security, persistence/concurrency, API and migration evidence.
- FE: accessible keyboard setup flow and safe error rendering.
- QA: rollback injection, replay/concurrency, secrecy/public-safety scan, clean no-provider flow.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story 1.2: Establish the Household Atomically`]
- [Source: `_bmad-output/planning-artifacts/prd-Kinward-Assistant-Experience.md#UJ-1: Administrator establishes a household`]
- [Source: `_bmad-output/planning-artifacts/prd-Kinward-Assistant-Experience.md#13.1 Household, accounts, and onboarding`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md#AD-01 - Local account authentication`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md#AD-19 - Application commands are the only mutation path`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md#AD-24 - One primary assistant per person and one fallback`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/SOLUTION-DESIGN.md#Authentication and security`]
- [Source: `_bmad-output/implementation-artifacts/1-1-start-a-healthy-core-deployment.md#Dev Notes`]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- `make lint && make typecheck && make test && make build` (2026-07-14): all gates passed; 34 backend tests and 3 web tests passed.
- Focused persistence-stage fault matrix: setup tests passed across four flush stages and commit failure.

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Added the versioned, fail-closed setup API with explicit CSRF, one-time hashed authorization, Argon2id verification, normalized idempotency, and sanitized retry/reset outcomes.
- Added an application policy and SQLAlchemy unit-of-work path that atomically creates the complete permitted graph and nothing from later epics.
- Completed the pre-freeze root migration and ORM parity with singleton household, personal-owner, and single-fallback constraints plus lifecycle metadata.
- Added the keyboard-accessible same-origin setup experience for repeated optional adult, child, and pet profiles using fictional examples and explicit pet restrictions.
- Proved exact and conflicting replay, SQLite concurrency, terminal/expired authorization, second-household denial, password secrecy, and rollback at each persistence stage.

### File List

- `.env.example`
- `README.md`
- `apps/web/nginx.conf`
- `apps/web/src/Setup.test.tsx`
- `apps/web/src/Setup.tsx`
- `apps/web/src/main.tsx`
- `apps/web/src/styles.css`
- `compose.yaml`
- `services/kinward/migrations/versions/001_initial_single_household.py`
- `services/kinward/pyproject.toml`
- `services/kinward/src/kinward/api/setup.py`
- `services/kinward/src/kinward/app.py`
- `services/kinward/src/kinward/application/__init__.py`
- `services/kinward/src/kinward/application/bootstrap.py`
- `services/kinward/src/kinward/config.py`
- `services/kinward/src/kinward/domain/lifecycle.py`
- `services/kinward/src/kinward/persistence/models.py`
- `services/kinward/tests/test_config.py`
- `services/kinward/tests/test_lifecycle.py`
- `services/kinward/tests/test_migrations.py`
- `services/kinward/tests/test_setup_api.py`
- `services/kinward/uv.lock`
- `scripts/compose-smoke.sh`

## Change Log

- 2026-07-14: Implemented and verified atomic single-household establishment; status moved to review.
