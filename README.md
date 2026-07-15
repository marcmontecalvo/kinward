# Kinward

A private, single-household AI platform where each person has their own assistant, with personal memory, household coordination, smart-home integration, and adaptable experiences across personal and shared devices.

## Status

Kinward is the clean replacement for the legacy Homefront project after its pivot from a commercial multi-tenant SaaS design to a private, Docker-deployed system for one household.

Selective migration is underway. The repository now contains the authoritative product direction, a clean single-household backend foundation, optional integration adapters, shared contracts, a registry-driven web surface, Docker configuration, and validation gates. Legacy code is moved only after its useful behavior is separated from SaaS, routine, support-access, and tenant assumptions.

See [Migration Status](docs/pivot/migration-status.md) for the final-gate disposition of each subsystem.

## Product principles

- One private deployment serves one household.
- Each person has one or more personal AI assistants.
- Personal and assistant memory remain permission-bound.
- Shared assistants are limited household fallbacks, not collective private brains.
- Ordinary life is inferred from durable context rather than manually programmed routines.
- Web/PWA is the first client.
- Native Android capabilities are deferred until a proven requirement needs them.
- The interface is built from modular cards and declarative surface layouts.
- Kinward Control remains separate from everyday assistant use.
- Home Assistant is an integration and physical-state authority, not the user experience.

## Repository shape

```text
apps/web/                 Responsive web/PWA client
services/kinward/         Single-household backend
packages/contracts/       Shared API contracts
packages/schemas/         Runtime schemas and validation
packages/assistant-core/  Assistant domain primitives
packages/card-sdk/        Card registry contracts
packages/layout-sdk/      Surface and layout contracts
packages/integration-sdk/ Integration adapter contracts
infra/                    Docker and optional observability
docs/                     Current product and technical documentation
_bmad-output/             Authoritative BMAD planning artifacts
```

## Authoritative documents

- [Product brief](_bmad-output/planning-artifacts/product-brief-Kinward-Assistant-Experience.md)
- [Product requirements document](_bmad-output/planning-artifacts/prd-Kinward-Assistant-Experience.md)
- [UX specification](_bmad-output/planning-artifacts/ux-design-specification-Kinward-Assistant-Experience.md)
- [Pivot and rebuild plan](docs/pivot/single-household-pivot-and-rebuild-plan.md)
- [Salvage matrix](docs/pivot/salvage-matrix.md)
- [Migration status](docs/pivot/migration-status.md)

## Development

```bash
cp .env.example .env
make install
make test
make build
```

Run the API and web client in separate terminals:

```bash
make api
make web
```

## Core deployment

A clean checkout needs no `.env` file and no provider credentials. Start the production-built,
same-origin core exactly as follows:

```bash
docker compose up
```

Compose builds four default services:

- `migrate` applies the sole root revision, `001_initial_single_household`, then exits with status 0.
- `worker` records durable SQL heartbeat readiness and exposes no later-story action semantics.
- `api` serves the backend only after migration succeeds.
- `web` serves the built PWA on <http://localhost:8080> and proxies `/api/v1` to the API.

SQLite data is retained in the project-scoped `kinward-data` volume. The API and worker never run
Alembic during normal startup. Both wait for the one-shot migration service and fail readiness when
the schema is incompatible. It is normal for `docker compose ps -a` to show `migrate` as exited (0).
The example environment file uses the same shared `/data/kinward.db` path, so copying it for local
development does not split migration, API, and worker state across container-local files.

The versioned health contract is available through the same origin:

```text
http://localhost:8080/api/v1/health
```

It reports application, database, schema, bootstrap, and worker/outbox health independently.
Unconfigured model, memory, knowledge, calendar, and Home Assistant capabilities report
`intentionally-disabled`; this does not make the core unhealthy. A configured provider remains
`unavailable` until a bounded capability check succeeds. Health output contains only fixed status
and reason values, never provider payloads, credentials, database URLs, or private host values.

### Establish the household

Household setup is deliberately unavailable unless the operator supplies a random one-time setup
authorization. Generate it locally, keep it out of shell history and files, and supply it through a
secret-aware process environment when starting the clean deployment. For example, a POSIX shell can
hold the value without printing it:

```bash
read -rsp "One-time setup authorization: " KINWARD_SETUP_AUTHORIZATION
export KINWARD_SETUP_AUTHORIZATION
docker compose up
```

Use a randomly generated value of at least 24 characters; do not use the illustrative values from
tests. Visit <http://localhost:8080/setup> and enter the same value. The form creates the household,
administrator account, administrator-owned personal assistant, ownerless household fallback, and
any selected adult, child, or pet profiles in one transaction. It requires no provider or integration.
Pets receive no credentials, account, assistant, private memory, approval, delegation, or action
authority; only explicitly entered household-shared care facts are retained.

Setup uses an explicit CSRF token, Argon2id password verification, and an idempotency identity. The
authorization is stored only as a hash and becomes terminally unusable after commit. Remove the
environment variable and restart `api` after setup. `/api/v1/setup/status` reports only whether setup
is available or complete; it never returns a password verifier or reusable setup authorization.

Restart the long-running processes without rerunning the migration service:

```bash
docker compose restart api worker web
```

Stop containers while retaining SQLite data, or explicitly remove the project volumes:

```bash
docker compose down
docker compose down --volumes
```

PostgreSQL 18 is an independent, unadvertised adapter profile. It is absent from the default
inventory and does not replace SQLite automatically. Set `KINWARD_POSTGRES_PASSWORD` in the
operator environment or a secret-management wrapper before opting in:

```bash
docker compose --profile postgres up postgres
```

No Redis service or dependency exists. Model, memory, knowledge, calendar, Home Assistant,
observability, and development peers are also absent from the default topology.

Run the reproducible Milestone A deployment gate with `make smoke`. The script owns synthetic,
project-scoped containers and volumes, validates migration failure gating, idempotency, restart
safety, health, same-origin reachability, and service inventory, then cleans up. OPS owns the
startup/restart/inventory evidence, BE owns migration/health/worker evidence, and QA owns evidence
completeness and public-repository safety.

The retained infrastructure contract is intentionally narrow: one backend image supplies explicit
migration, API, and worker roles; the versioned setup handler delegates through an application policy
and one transaction; the single-household SQL model remains authoritative; and optional adapters degrade without blocking
startup. No legacy tenant, entitlement, control-plane, support-access, or routine behavior is
carried into this deployment foundation.

## License

Kinward is source-available under the PolyForm Noncommercial License 1.0.0. Personal, educational, research, hobby, and other qualifying noncommercial use is permitted. Commercial use requires a separate license from the copyright holder.
