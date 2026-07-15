# Story 2.1: Enter a Private Personal Assistant Session

Status: ready-for-dev

## Story

As an account-bearing household member,
I want to authenticate into my own private personal assistant session,
so that only I can access my assistant, topics, memory boundary, and personal surface.

## Acceptance Criteria

1. Given an active account created during household bootstrap, when valid local credentials are submitted, then the server verifies the password with the adopted Argon2id-equivalent mechanism, creates an opaque high-entropy session whose verifier is stored server-side, sends its secret only in a `Secure`, `HttpOnly`, `SameSite` cookie, and binds the session to the existing account, person, issuance/expiry, security version, and revocation state.
2. Given a state-changing authenticated `/api/v1` request, the server validates the session and explicit CSRF protection before dispatch and derives identity and authority from server-side bindings, never client-supplied person, assistant, topic, or surface identifiers.
3. Given an authenticated active account without a deletion-pending overlay, the personal surface resolves exactly one primary assistant owned by that person; it cannot select or reassign another person's assistant, the ownerless household fallback remains separate, and additional/specialist assistants remain unavailable.
4. Unauthenticated, expired, revoked, non-active, deletion-pending, or invalid-CSRF requests fail before protected repository/provider access and disclose no private content, identifier, ownership hint, count, or existence signal; the client withholds or clears private state.
5. Administrator role alone never grants access to another adult's assistant, topic, conversation, memory reference, or personal integration. Denials contain only stable safe codes and opaque correlations.
6. A valid personal mobile or desktop session receives a server-derived immutable `AccessContext` containing actor, account/lifecycle state, owned assistant, validated surface and audience, requested capability, applicable policy versions, and opaque correlation ID. Every protected application, repository, and provider port requires it; authorization occurs before query construction and again before serialization.
7. Logout, expiry, revocation, account-state/security-version change, or deletion-pending entry invalidates old authority. Reuse fails closed, private browser state is removed, and a new valid session is required.
8. Authentication telemetry contains no password, session secret/verifier, private title/body, or unrestricted person identifier. Safe error codes and an opaque correlation reference remain diagnosable.
9. Account/person bindings and explicitly portable recovery material have protected backup treatment. Sessions, device trust, refresh artifacts, CSRF secrets, and pending authentication capabilities are excluded and invalid after restore.
10. Authenticated local personal-home queries complete within 500 ms p95 on the reference deployment; login, logout, errors, and the personal shell are keyboard-operable and use ordinary household language.

This story addresses `FR-009`, `FR-010`, `FR-028`, `FR-030`, `FR-031`, `FR-033`, `NFR-001`, `NFR-002`, `NFR-004`, `NFR-007`, `NFR-008`, `NFR-021`, `NFR-025`, `NFR-027`, `NFR-030`, `NFR-032`, `UX-DR6`, `UX-DR7`, `UX-DR26`, `UX-DR27`, and `AD-01`, `AD-05`, `AD-17`, `AD-21`, `AD-24`.

## Tasks / Subtasks

- [ ] Establish framework-free identity, session, and access contracts (AC: 1-7, 9)
  - [ ] Define account states exactly as `active`, `disabled`, `locked`, and `recovery-pending`; model `deletion-pending` as a separate overriding person lifecycle.
  - [ ] Define immutable `AccessContext`, authenticated principal, session lifecycle, CSRF validation, stable denial codes, and clock/random/credential-hasher ports under domain/application namespaces.
  - [ ] Keep mechanism details configurable, but document cookie name/path, SameSite policy, absolute/idle lifetime, rotation, CSRF pattern, Argon2id parameters, and local abuse limits chosen during implementation.
  - [ ] Ensure only `active` without deletion-pending has authority and that security-version changes revoke existing sessions atomically.
- [ ] Add account and session persistence through a forward migration (AC: 1, 7, 9)
  - [ ] Create account/binding and hashed session records with UUIDs, UTC timestamps, expiry, security version, revocation state, optimistic versioning, and database constraints.
  - [ ] Store only a keyed/hash verifier for the opaque session secret; never persist plaintext session or CSRF capabilities.
  - [ ] Add indexes supporting bounded verifier lookup and expiry/revocation cleanup without person-identifying telemetry.
  - [ ] Do not amend frozen `001_initial_single_household`; Story 1.1 evidence froze the baseline, so add a forward Alembic revision.
- [ ] Implement authentication application commands and authorized personal query (AC: 1-8)
  - [ ] Add login, logout/revoke, current-session, and personal-session-context services using policy and unit-of-work boundaries.
  - [ ] Resolve the existing person's exactly-one active primary assistant server-side and reject missing, duplicate, cross-owner, fallback, specialist, or temporary matches as safe configuration failures.
  - [ ] Require `AccessContext` on every protected repository/provider method and scope reads before SQL execution; reauthorize fields immediately before Pydantic serialization.
  - [ ] Preserve transactional revocation behavior for future account/deletion transitions rather than embedding it only in routes.
- [ ] Add thin `/api/v1` authentication and personal-surface adapters (AC: 1-8, 10)
  - [ ] Add versioned Pydantic commands/responses and cookie operations; routes parse, dispatch, and serialize only.
  - [ ] Apply CSRF checks to every state-changing cookie-authenticated endpoint, including logout; return stable household-safe errors without existence hints.
  - [ ] Add same-origin web login and personal-shell gates for mobile and desktop; clear in-memory and persistent private state on denial/logout/expiry.
  - [ ] Generate TypeScript contracts from OpenAPI; do not extend the hand-authored `packages/contracts/src/index.ts` as a second wire authority.
- [ ] Define recovery, retention, and operational treatment (AC: 7-9)
  - [ ] Exclude reusable sessions, device trust, refresh/CSRF artifacts, and pending capabilities from backups and invalidate them after restore.
  - [ ] Retain account/person bindings only under the protected portable-recovery contract; do not introduce recovery delivery in this story.
  - [ ] Add bounded session cleanup and sanitized security-denial evidence without private payloads or high-cardinality labels.
- [ ] Verify privacy, security, accessibility, and performance (AC: 1-10)
  - [ ] Test valid/invalid credentials, replay, cookie flags, CSRF success/failure, expiry, logout, revocation, security-version changes, non-active states, deletion-pending, and concurrent revocation.
  - [ ] Test adult/admin/teen/child, personal/fallback/cross-owner assistant boundaries and byte/field absence for protected identifiers, records, counts, and provider calls.
  - [ ] Run generated-contract compilation, keyboard journeys, browser-storage inspection, local p95 evidence, SQLite tests, and the relevant PostgreSQL contract suite without advertising PostgreSQL prematurely.
  - [ ] Run `make lint`, `make typecheck`, `make test`, and `make build`; scan fixtures/logs/evidence for secrets and private deployment data.

## Dev Notes

### Prerequisite and Scope Boundaries

- Story 1.2 is a hard prerequisite: credentials must bind to the account and person created by its atomic bootstrap command. If that contract is not implemented/stable, implement or reconcile it first; do not bolt credentials onto the temporary direct-write setup route.
- This story establishes authentication, authorization context, and personal-shell gating. Story 2.2 owns request/SSE orchestration; Story 2.3 owns topics/conversations. Do not prebuild those flows beyond stable ports needed by this story.
- External OIDC, device trust, recovery delivery, invitations, additional assistants, specialists, voice/multimodal input, and live shared-display identity are out of scope.

### Current Repository State and Required Changes

| Area | Current state | Required change | Preserve |
| --- | --- | --- | --- |
| `services/kinward/src/kinward/api/setup.py` | Unversioned `/api/setup`; direct SQL writes; person email but no account/password/session; only primary assistant is created. | Treat as migration input owned by Story 1.2. Consume its resulting account/binding contract; do not add login logic or more direct commits here. | Existing synthetic `.invalid` validation until bootstrap replaces it. |
| `services/kinward/src/kinward/app.py` | Registers setup and `/api/v1/health`; no auth middleware/dependency. | Register versioned auth/personal routers and reusable server-derived access dependency. | App factory and no-provider startup. |
| `persistence/models.py` and migration `001` | People/assistants exist; no account or session records; assistant ownership is weakly constrained. | Add forward migration and typed records; enforce account/binding/session and primary-owner invariants. | UUID strings, UTC timestamps, SQLAlchemy 2 typed mappings, one-household model. |
| `domain/assistant_ownership.py` | Pure owner-count helper only. | Reuse/strengthen invariant in domain/application policy; never rely on the helper alone for SQL query authorization. | Ownerless fallback and exactly-one personal owner semantics. |
| `apps/web/src/App.tsx` | Always renders fictional private-looking personal content; no auth gate. | Add login/session gate and policy-filtered personal shell; private data must never enter unauthenticated state. | Registered-card direction and persistent text input placeholder for Story 2.2. |
| `packages/contracts/src/index.ts` | Hand-authored, stale types expose specialist/temporary kinds and old health enums. | Replace relevant wire types through generated OpenAPI output. | `packages/schemas` remains card/layout/config authority only. |

### Architecture and Security Guardrails

- Maintain the hexagonal modular monolith: FastAPI, SQLAlchemy, password hashing, cookies, and cryptographic randomness are adapters behind inward ports. Routes do not own transactions or policy.
- `AccessContext` is constructed from validated server state, never request IDs. Validate before query/provider access and again before serialization; unauthorized resources are absent, not redacted-with-existence.
- Use secure random opaque session secrets with server-side hashed/keyed lookup. Never use readable bearer/JWT claims as authority. Cookie auth is same-origin behind the existing ingress.
- Do not introduce tenant IDs, global household queries, Redis sessions, provider-specific identity types, administrator override of adult privacy, or logs containing credentials/private identifiers.
- Use current locked project dependencies and the project-context currency policy. Add a maintained Argon2id-capable library only after compatibility/security review; record parameters and upgrade strategy rather than inventing custom cryptography.

### File Structure Guidance

- Expected additions: identity/auth domain and application modules, security ports/adapters, versioned API router and Pydantic models, access-policy tests, a forward Alembic revision, generated TS client output, and web auth/session modules.
- Expected updates: `app.py`, persistence model exports/session wiring, web route/app shell, manifests/locks, and focused tests. Avoid unrelated card/layout rewrites.
- Keep API schemas in backend Pydantic/OpenAPI. Do not put account/session domain types in `packages/schemas`.

### Testing and Evidence Ownership

- BE owns credential/session/CSRF, policy-order, persistence, backup-classification, and p95 API evidence. FE owns state clearing, keyboard flow, storage inspection, and personal-shell gating. QA owns cross-person matrices, byte/field absence, contract compilation, and public-safety evidence. OPS owns same-origin cookie/TLS deployment documentation.
- Security tests must assert that protected repositories/providers were not called after failed authentication, not merely that HTTP returned 401/403.

### Previous Story and Git Intelligence

- Story 1.1 established separate migration/API/worker roles, same-origin ingress, frozen locks, SQLite authority, truthful optional capability health, and the rule that API/worker never self-migrate. Reuse those deployment seams.
- Commit `2492dc8` froze `001_initial_single_household` through Milestone A evidence and retained `/api/setup` only as a narrow compatibility path. Use a forward migration and do not regress Compose smoke, health, worker/outbox readiness, or no-provider startup.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story 2.1: Enter a Private Personal Assistant Session`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md#AD-01 — Local account authentication`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md#AD-05 — AccessContext before query and before serialization`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/SOLUTION-DESIGN.md#AccessContext`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/SOLUTION-DESIGN.md#API and contract design`]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification-Kinward-Assistant-Experience.md#Personal Mobile`]
- [Source: `_bmad-output/project-context.md#Dependency Currency and Compatibility`]
- [Source: `_bmad-output/implementation-artifacts/1-1-start-a-healthy-core-deployment.md#Completion Notes List`]
- [Source: `AGENTS.md#Public repository safety`]

## Dev Agent Record

### Agent Model Used

OpenAI GPT-5

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.

### File List

