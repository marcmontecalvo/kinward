# Kinward

A private, single-household AI platform where each person has their own assistant, with personal memory, household coordination, smart-home integration, and adaptable experiences across personal and shared devices.

## Status

Kinward is the clean replacement for the legacy Homefront project after its pivot from a commercial multi-tenant SaaS design to a private, Docker-deployed system for one household.

Selective migration is underway. The repository now contains the authoritative product direction, a clean single-household backend foundation, optional integration adapters, Docker configuration, and validation gates. Legacy code is moved only after its useful behavior is separated from SaaS, routine, support-access, and tenant assumptions.

Kinward's own standalone frontend has been retired in favor of a Home Assistant-native application shell: Home Assistant owns dashboards, responsive rendering, and voice, and Kinward exposes household intelligence through the [`custom_components/kinward`](custom_components/kinward/README.md) integration. See [the HA-native reset](_bmad-output/implementation-artifacts/ha-native-reset-2026-07-15.md) and [migration status](docs/pivot/migration-status.md) for the final-gate disposition of each subsystem.

## Product principles

- One private deployment serves one household.
- Each person has one or more personal AI assistants.
- Personal and assistant memory remain permission-bound.
- Shared assistants are limited household fallbacks, not collective private brains.
- Ordinary life is inferred from durable context rather than manually programmed routines.
- Native Android capabilities are deferred until a proven requirement needs them.
- Kinward Control remains separate from everyday assistant use.
- Home Assistant is the committed application shell: it owns dashboards, responsive rendering, mobile access, and voice. Kinward exposes household intelligence through a documented Home Assistant custom integration rather than a standalone frontend.

## Repository shape

```text
services/kinward/         Single-household backend
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

Run the API in a terminal:

```bash
make api
```

## Core deployment

A clean checkout needs no `.env` file and no provider credentials. Start the production-built
core exactly as follows:

```bash
docker compose up
```

Compose builds three default services:

- `migrate` applies the sole root revision, `001_initial_single_household`, then exits with status 0.
- `worker` records durable SQL heartbeat readiness and exposes no later-story action semantics.
- `api` serves the backend only after migration succeeds, published on <http://localhost:8000>.

SQLite data is retained in the project-scoped `kinward-data` volume. The API and worker never run
Alembic during normal startup. Both wait for the one-shot migration service and fail readiness when
the schema is incompatible. It is normal for `docker compose ps -a` to show `migrate` as exited (0).
The example environment file uses the same shared `/data/kinward.db` path, so copying it for local
development does not split migration, API, and worker state across container-local files.

The versioned health contract is available directly from the API:

```text
http://localhost:8000/api/v1/health
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
tests. Submit it to `POST http://localhost:8000/api/v1/setup/household` (directly, or through the
Home Assistant `config_flow` once `custom_components/kinward` exists) along with the household,
administrator, and any selected adult, child, or pet details; the endpoint creates the household,
administrator account, administrator-owned personal assistant, ownerless household fallback, and
those profiles in one transaction. It requires no provider or integration. Pets receive no
credentials, account, assistant, private memory, approval, delegation, or action authority; only
explicitly entered household-shared care facts are retained.

Setup uses an explicit CSRF token, Argon2id password verification, and an idempotency identity. The
authorization is stored only as a hash and becomes terminally unusable after commit. Remove the
environment variable and restart `api` after setup. `/api/v1/setup/status` reports only whether setup
is available or complete; it never returns a password verifier or reusable setup authorization.

Restart the long-running processes without rerunning the migration service:

```bash
docker compose restart api worker
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
safety, health, API reachability, and service inventory, then cleans up. OPS owns the
startup/restart/inventory evidence, BE owns migration/health/worker evidence, and QA owns evidence
completeness and public-repository safety.

The retained infrastructure contract is intentionally narrow: one backend image supplies explicit
migration, API, and worker roles; the versioned setup handler delegates through an application policy
and one transaction; the single-household SQL model remains authoritative; and optional adapters degrade without blocking
startup. No legacy tenant, entitlement, control-plane, support-access, or routine behavior is
carried into this deployment foundation.

## Home Assistant development

A pinned Home Assistant 2026.7.2 development instance is available under the `ha` compose profile. It
stays out of the default inventory (`docker compose up` never starts it) and is fully independent of
Kinward's own health: either can start, stop, or restart without the other.

```bash
docker compose --profile ha up --build
```

Home Assistant is published on <http://localhost:8123>. Its configuration persists in the
`kinward-homeassistant` volume. `custom_components/kinward` is bind-mounted read-only into the
container's `/config/custom_components/kinward`, so there is no manual copy/install step for local
development; restart the `homeassistant` service (or use Home Assistant's own reload) to pick up code
changes.

Reset Home Assistant's local state entirely:

```bash
docker compose --profile ha down --volumes
```

Once both `api` and `homeassistant` are healthy, generate a service token for the integration and use
it (with `http://api:8000` as the backend URL, from inside the Home Assistant container's network) in
the integration's config flow:

```bash
docker compose exec api python -m kinward.cli create-integration-token --name "Home Assistant"
```

The plaintext token is printed exactly once; it is stored only as a hash and can be revoked with
`python -m kinward.cli revoke-integration-token <id>`. See
[`custom_components/kinward/README.md`](custom_components/kinward/README.md) for installing the
integration, importing the dashboard, and the household trial runbook at
[`docs/ha-native/household-trial.md`](docs/ha-native/household-trial.md).

## License

Kinward is source-available under the PolyForm Noncommercial License 1.0.0. Personal, educational, research, hobby, and other qualifying noncommercial use is permitted. Commercial use requires a separate license from the copyright holder.
