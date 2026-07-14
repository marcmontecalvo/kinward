---
baseline_commit: 2ec665967d0c26601d63e18d113d6f4d7f99d85e
---

# Story 1.1: Start a Healthy Core Deployment

Status: review

## Story

As a household operator,
I want Kinward's core stack to start from a clean checkout without optional providers,
so that I can operate a reliable private household deployment without infrastructure expertise.

## Acceptance Criteria

1. **Clean-checkout startup:** Given a clean checkout with the documented default configuration, when the operator runs the unmodified documented `docker compose up` command, then the migration runner, core web/API, worker, and default SQLite database start successfully, and the core stack reaches documented healthy states without manual database editing or additional setup commands.

2. **Single migration origin and startup ordering:** Given a clean empty database, when the one-shot migration runner executes, then it applies `001_initial_single_household` directly as the schema origin; it does not execute, copy, import, or depend on the retired legacy migration chain; API and worker readiness wait for successful migration completion; and neither API nor worker runs migrations during normal startup.

3. **Default and optional topology:** Given the default Compose configuration, when the service and profile inventory is inspected, then SQLite is selected; PostgreSQL, memory, knowledge, observability, and development services are opt-in only; Redis is neither started nor required; and absent optional services do not cause a core health failure.

4. **Truthful health without providers:** Given no model, memory, knowledge, calendar, or Home Assistant provider is configured, when health and locally available smoke checks run, then application, database, migration compatibility, bootstrap availability, worker/outbox readiness, and local health paths report healthy; provider-dependent capabilities separately report `degraded`, `unavailable`, or `intentionally-disabled`; and no unavailable provider data or capability is represented as current.

5. **Reproducible current dependencies:** Given the version policy in `_bmad-output/project-context.md`, when manifests and lockfiles are validated, then Node.js 24 LTS, pnpm 11, React 19, TypeScript 7 strict, compatible current Vite/Vitest and Zod 4, Python 3.14, FastAPI 0.139+, Pydantic 2, SQLAlchemy 2.0, Alembic 1, pytest 9, Ruff 0.15, and mypy 2 resolve reproducibly at supported patched releases; `pnpm-lock.yaml` and `services/kinward/uv.lock` are committed; and any temporary version hold records its blocker, affected validation, owner, review date, and exit criteria.

6. **Restart safety and Milestone A evidence:** Given the running clean-checkout stack, when containers or processes restart within documented recovery behavior, then committed schema state remains valid, startup creates no duplicate migration effects and requires no manual repair, and evidence captures exit behavior, restart behavior, health probes, service inventory, optional-provider absence, core smoke checks, and migration idempotency for the Milestone A gate.

7. **Selective salvage and repository safety:** Given retained deployment, backend, frontend, or integration infrastructure used by this story, when accepted, then useful behavior is documented, SaaS and multi-tenant assumptions are absent, the Kinward contract is explicit, focused checks pass, and only the smallest useful implementation is retained. Fixtures, examples, logs, configuration, and evidence use fictional or synthetic values and contain no secrets, private deployment identifiers, internal hosts, or private household data.

This story addresses `FR-001`, `FR-079`, `NFR-010`, `NFR-029`, `NFR-031` through `NFR-033`, `NFR-040`, and the deployment, migration, salvage, and public-repository-safety architecture constraints.

## Tasks / Subtasks

- [x] Align runtime manifests and produce reproducible lockfiles (AC: 5)
  - [x] Update `mise.toml`, root `package.json`, workspace manifests, and `services/kinward/pyproject.toml` to the authoritative compatibility policy in `_bmad-output/project-context.md`; do not preserve the architecture document's superseded fixed version table.
  - [x] Enable TypeScript strict mode requirements including `noUncheckedIndexedAccess` and `exactOptionalPropertyTypes` without weakening existing checks.
  - [x] Remove the legacy SQLAlchemy mypy plugin unless a specific typed-mapping gap is documented; native SQLAlchemy 2 mappings are the default.
  - [x] Generate and commit `pnpm-lock.yaml` and `services/kinward/uv.lock`; make local and container installs consume frozen locks.
  - [x] Record any unavoidable hold using the dependency-policy fields from project context rather than silently pinning an older major.

- [x] Separate migration, API, and worker process roles (AC: 1, 2, 6)
  - [x] Replace the Dockerfile command that runs Alembic before Uvicorn with explicit API, migration, and worker entry points built from the same backend image.
  - [x] Configure one one-shot Compose migration service and gate API and worker startup on its successful completion.
  - [x] Ensure API and worker validate schema compatibility/readiness but never execute migrations during ordinary startup.
  - [x] Preserve `001_initial_single_household` as the sole root revision with `down_revision = None`; do not add or import a legacy revision chain.
  - [x] Amend the unreleased `001` only as needed for the minimum accepted Milestone A worker/outbox and single-household foundation. After the Milestone A evidence freeze, use forward-only migrations.
  - [x] Add a minimal durable SQL worker/outbox readiness path; do not introduce Redis, a process-local queue as durable truth, or external mutation behavior from later stories.

- [x] Build the default same-origin core topology (AC: 1, 3)
  - [x] Add the production web/ingress service needed to serve the built PWA and proxy `/api/v1` to the API on one origin.
  - [x] Keep SQLite on the default data volume and make PostgreSQL its own opt-in profile.
  - [x] Remove Redis from Compose and from every required dependency or readiness path.
  - [x] Keep model, memory, knowledge, calendar, Home Assistant, observability, and development services absent or opt-in; the default command must not need provider credentials.
  - [x] Use environment variables or secret mounts for secrets; do not bake values into images, defaults, examples, or source.

- [x] Implement truthful core and capability health contracts (AC: 4)
  - [x] Provide a versioned health endpoint under `/api/v1` with separate core component and optional capability status.
  - [x] Core health must verify application process, database reachability, current migration/schema compatibility, bootstrap availability, and worker/outbox readiness.
  - [x] Optional capabilities use only the canonical states `available`, `degraded`, `unavailable`, `intentionally-disabled`, `stale`, or `reauthorization-required`, with a safe actionable reason where applicable.
  - [x] Configuration alone must not report a provider `available`; only a successful bounded capability check may do so. An unconfigured provider is normally `intentionally-disabled`, not a core failure.
  - [x] Keep health output sanitized and bounded: no credentials, provider payloads, private identifiers, database URLs, internal hosts, or high-cardinality labels.
  - [x] Keep existing setup behavior working until Story 1.2 rewrites it; do not expand or claim bootstrap completion in this story.

- [x] Add deployment, migration, and restart verification (AC: 1-7)
  - [x] Add focused unit/integration tests for the health state model, schema compatibility, provider absence, and sanitized output.
  - [x] Add an automated clean-checkout Compose smoke test that builds, starts the unmodified default topology, waits for migration completion and service health, checks the web and API paths, and shuts down cleanly.
  - [x] Assert Compose's default service inventory excludes PostgreSQL, Redis, and optional providers; separately validate that the PostgreSQL profile is opt-in without advertising parity yet.
  - [x] Test migration failure prevents API/worker readiness, migration rerun is idempotent, and API/worker restarts do not execute Alembic or alter the schema.
  - [x] Restart API and worker against committed SQLite state and verify health recovers without duplicate effects or manual repair.
  - [x] Scan fixtures, logs, Compose output, generated evidence, and tracked configuration for secrets and deployment-specific private values.

- [x] Update operator documentation and evidence ownership (AC: 1, 3, 4, 6, 7)
  - [x] Make `README.md` document the literal clean-checkout `docker compose up` path, health URL, expected default services, opt-in profiles, shutdown/restart behavior, and truthful no-provider states.
  - [x] Document retained infrastructure behavior and the Kinward-specific replacement contract; do not reference legacy Homefront documents as current implementation guidance.
  - [x] Store or generate reproducible Milestone A evidence through automated checks rather than committing machine-specific logs, databases, credentials, or private support bundles.
  - [x] Assign OPS ownership for startup/restart/service evidence, BE ownership for migration/health/worker evidence, and QA ownership for evidence completeness and the public-safety check.

## Dev Notes

### Implementation Boundaries

- This is the deployment foundation, not the household bootstrap implementation. Story 1.2 owns atomic household/profile/account/assistant creation and the secure one-time setup boundary.
- Stories 1.3 through 1.5 own the complete card set, layout resolver, and five-surface evidence. This story supplies a production-built web service and verifies it is reachable; it must not pre-implement those stories.
- Do not move all routes or hand-authored contracts in this story merely to make the repository look architecturally complete. Introduce the versioned health seam now; migrate feature routes in their owning stories.
- Do not claim PostgreSQL behavioral parity. It remains opt-in and unadvertised until the shared persistence/transaction suite passes.
- Do not implement provider calls, authentication, backup/restore, meaningful actions, or user-facing Kinward Control here.

### Current Repository State and Required Changes

| File / area | Current state | Story change | Preserve |
| --- | --- | --- | --- |
| `compose.yaml` | One `kinward` service runs API plus migrations; PostgreSQL and Redis share profile `data`; no web, worker, or one-shot migration service. | Split web/ingress, migration, API, and worker roles; default SQLite; standalone opt-in PostgreSQL; remove Redis. | Named SQLite persistence and optional-provider environment model where still useful. |
| `services/kinward/Dockerfile` | Python 3.12 image; installs without a lock; command runs Alembic then Uvicorn. | Build from the current Python line and frozen uv lock; expose separate role commands; no migration in API/worker startup. | One backend image reused by migration, API, and worker. |
| `services/kinward/src/kinward/app.py` | `/api/health` reports one aggregate `ok`; provider configuration is treated as availability; no database/schema/worker checks. | Add versioned, typed, truthful core/capability health with bounded checks and sanitized output. | App factory and no-provider startup. |
| `services/kinward/src/kinward/config.py` | Optional memory, knowledge, and Home Assistant settings default off. | Extend only for bounded health and role needs; secrets remain excluded from representations. | Optional integrations must remain optional. |
| `services/kinward/migrations/versions/001_initial_single_household.py` | Root revision exists and contains an initial partial schema. | Keep it the sole origin; amend only before evidence freeze for the minimum Story 1.1 foundation. | Root revision identity and no legacy dependency. |
| `services/kinward/src/kinward/persistence/models.py` | Native typed mappings exist but include a partial pre-freeze model. | Keep migration/model metadata consistent for introduced worker/outbox readiness state. | UUID strings, UTC creation times, typed SQLAlchemy mappings. |
| `package.json`, `mise.toml`, `services/kinward/pyproject.toml` | Older compatibility lines and broad ranges; no lockfiles. | Reconcile to project context, pin package manager/runtime lines, generate frozen locks. | pnpm workspaces, uv, mise, and Make convenience commands. |
| `README.md` | Requires `cp .env.example .env`, `make install`, and `make up`; does not prove literal default Compose startup. | Document the zero-extra-command runtime path and expected health/degraded states. | Concise private-household positioning and current-document links. |

### Architecture Compliance

- Use the hexagonal modular monolith. Deployment adapters and health adapters may depend inward; domain/application code must not depend on Docker, FastAPI, SQLAlchemy adapters, or provider SDKs.
- Exactly one household exists per deployment. Do not add `tenant_id`, tenant middleware, cross-household repository APIs, billing, entitlement, support-access, or control-plane configuration.
- SQLite is the required default. PostgreSQL is an adapter profile. Redis is prohibited as a required queue, cache, session, or coordination dependency.
- The migration runner is one-shot and completes before API/worker readiness. The API and worker must fail closed on incompatible schema rather than self-migrating.
- The web client and API are same-origin in production behind one ingress. Development may continue to use Vite proxying.
- Health separates core status from each optional capability and never treats absence as core failure.
- Structured operational output must be sanitized by construction. Do not log database URLs, environment dumps, tokens, provider payloads, or private values.

### Dependency and Language Requirements

- `_bmad-output/project-context.md` is authoritative and explicitly supersedes the older fixed stack table in the architecture documents. Reconciliation in this story is an intentional documented upgrade, not a silent change.
- As checked on 2026-07-14, Node 24.18.0 is the current Node 24 LTS patch, pnpm 11.13.0 is current, and TypeScript 7.0.2 is current. Resolve all remaining packages at implementation time through the package registries and commit the resulting lockfiles.
- TypeScript must remain strict with `noUncheckedIndexedAccess` and `exactOptionalPropertyTypes`; do not introduce `any`, and keep `unknown` at validated trust boundaries only.
- Python uses Pydantic at API/config boundaries and native SQLAlchemy 2 typed mappings. No ORM entity is an API response.
- Use UUID identities, UTC persisted timestamps, and fictional `.invalid` domains in public tests.

### File Structure Requirements

- Expected updates: `compose.yaml`, `services/kinward/Dockerfile`, `services/kinward/pyproject.toml`, `services/kinward/src/kinward/app.py`, `services/kinward/src/kinward/config.py`, `services/kinward/migrations/versions/001_initial_single_household.py`, `services/kinward/src/kinward/persistence/models.py`, root/workspace manifests, `mise.toml`, `Makefile`, and `README.md`.
- Expected additions may include a backend worker entry point, health contract/service modules, a production web Dockerfile and ingress configuration, Compose smoke-test tooling, `pnpm-lock.yaml`, and `services/kinward/uv.lock`.
- Keep framework-free decisions out of transport/config files. If health semantics become more than simple assembly, define a small application-facing health contract rather than embedding provider policy in the route.
- Do not add a second backend service or internal network boundary for a domain module.

### Testing Requirements

- Run `make lint`, `make typecheck`, `make test`, and `make build`.
- Validate `docker compose config` for the default and PostgreSQL profile inventories.
- Validate the literal clean-checkout default path with `docker compose up --build`, not only `make up` or preinstalled host dependencies.
- Test from an empty named volume and again after API/worker restarts. Capture the migration service's successful terminal state and prove it is not restarted as a daemon.
- Include failure injection for migration failure and unavailable optional providers.
- Assert exact health status categories and absence of sensitive fields, not only HTTP 200.
- Keep all evidence synthetic and repository-safe. Do not commit runtime databases, `.env`, logs, support bundles, credentials, LAN addresses, internal domains, or generated artifacts containing them.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story 1.1: Start a Healthy Core Deployment`]
- [Source: `_bmad-output/planning-artifacts/epics.md#Epic Execution Guardrails`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md#AD-06 - One local SQL authority with outbound provider ports`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md#AD-11 - Durable SQL jobs and outbox`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md#AD-17 - One household and one time model`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md#AD-18 - Hexagonal modular monolith`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md#AD-23 - Same-origin profile-based Compose deployment`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/SOLUTION-DESIGN.md#Container and deployment view`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/SOLUTION-DESIGN.md#Observability and operations`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/SOLUTION-DESIGN.md#Milestone A - foundation`]
- [Source: `_bmad-output/project-context.md#Technology Stack & Versions`]
- [Source: `_bmad-output/project-context.md#Dependency Currency and Compatibility`]
- [Source: `docs/pivot/single-household-pivot-and-rebuild-plan.md#Infrastructure simplification`]
- [Source: `docs/pivot/salvage-matrix.md#Acceptance rule`]
- [Source: `AGENTS.md#Public repository safety`]

## Dev Agent Record

### Agent Model Used

openai/gpt-5.6-sol

### Debug Log References

- 2026-07-14 host verification: `make lint`, `make typecheck`, `make test` (24 Python tests and 2 web tests), and `make build` passed.
- 2026-07-14 operator verification: `./scripts/compose-smoke.sh` passed, verifying image builds, default and PostgreSQL-profile inventories, injected migration failure gating, one-shot `001_initial_single_household`, healthy web/API/worker with absent providers intentionally disabled, migration idempotency, API/worker restart recovery, persisted revision stability, and cleanup.
- 2026-07-14 regression verification: corrected `.env.example` to retain the shared `/data/kinward.db` Compose path and extended the smoke suite to start a healthy isolated stack from a verbatim copied example environment file.
- 2026-07-14 final checks: `docker compose config` and `git diff --check` passed.

### Completion Notes List

- No `sprint-status.yaml` exists, so no sprint-status entry was updated.
- Implemented the migration/API/worker role split, same-origin production web ingress, default SQLite topology, opt-in PostgreSQL profile, SQL outbox/worker heartbeat seam, sanitized versioned health contract, and focused deployment checks.
- Preserved the existing `/api/setup` routes through a narrow ingress proxy; Story 1.2 behavior was not expanded.
- Fixed TypeScript 7 exact-optional prop forwarding, Vite asset declarations, declaration-package source roots, Corepack-backed pnpm execution on Node 24, and `.invalid` synthetic setup-email validation required by repository-safe fixtures.
- Removed redundant API/worker build targets for the shared backend tag while retaining one backend image for all three process roles and clean-checkout build ownership on the migration service.
- All required host gates and the operator-run Compose smoke passed on 2026-07-14; every task is complete and the story is ready for review.

### File List

- `.env.example`
- `Makefile`
- `README.md`
- `_bmad-output/implementation-artifacts/1-1-start-a-healthy-core-deployment.md`
- `apps/web/Dockerfile`
- `apps/web/nginx.conf`
- `apps/web/package.json`
- `apps/web/src/App.tsx`
- `apps/web/src/cards/registry.tsx`
- `apps/web/tsconfig.json`
- `compose.yaml`
- `mise.toml`
- `package.json`
- `pnpm-lock.yaml`
- `packages/contracts/package.json`
- `packages/contracts/tsconfig.json`
- `packages/schemas/package.json`
- `packages/schemas/tsconfig.json`
- `scripts/compose-smoke.sh`
- `services/kinward/Dockerfile`
- `services/kinward/migrations/versions/001_initial_single_household.py`
- `services/kinward/pyproject.toml`
- `services/kinward/src/kinward/api/setup.py`
- `services/kinward/src/kinward/app.py`
- `services/kinward/src/kinward/config.py`
- `services/kinward/src/kinward/health.py`
- `services/kinward/src/kinward/integrations/base.py`
- `services/kinward/src/kinward/persistence/models.py`
- `services/kinward/src/kinward/worker.py`
- `services/kinward/tests/test_health.py`
- `services/kinward/tests/test_integrations.py`
- `services/kinward/tests/test_migrations.py`
- `services/kinward/tests/test_persistence.py`
- `services/kinward/tests/test_worker.py`
- `services/kinward/uv.lock`

### Change Log

- 2026-07-14: Implemented the Story 1.1 core deployment foundation and verification tooling; retained in-progress status because lock generation and required runtime validation are environment-blocked.
- 2026-07-14: Continued TypeScript 7 and current-dependency repair, generated and checked frozen lockfiles, and passed all daemon-free gates; retained in-progress status because ordinary asyncio/SQLite tests and Docker smoke remain sandbox-blocked.
- 2026-07-14: Consolidated backend Compose build ownership after the Ringer smoke stopped during shared-image export; retained in-progress status pending the required post-repair runtime smoke rerun.
- 2026-07-14: Finalized the story record after host quality gates and the full operator Compose smoke passed; marked all tasks complete and moved the story to review.
