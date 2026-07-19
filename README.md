# Kinward

A private, single-household AI platform where each person has their own assistant, with personal memory, household coordination, smart-home integration, and adaptable experiences across personal and shared devices.

## Status

Kinward is the clean replacement for the legacy Homefront project after its pivot from a commercial multi-tenant SaaS design to a private, Docker-deployed system for one household.

Selective migration is underway. The repository now contains the authoritative product direction, a clean single-household backend foundation, optional integration adapters, Docker configuration, and validation gates. Legacy code is moved only after its useful behavior is separated from SaaS, routine, support-access, and tenant assumptions.

Kinward's own standalone frontend has been retired in favor of a Home Assistant-native application shell: Home Assistant owns dashboards, responsive rendering, and voice, and Kinward exposes household intelligence through the [`custom_components/kinward`](custom_components/kinward/README.md) integration. See [the HA-native reset](_bmad-output/implementation-artifacts/ha-native-reset-2026-07-15.md) and [migration status](docs/pivot/migration-status.md) for the final-gate disposition of each subsystem.

## Automated setup

The fastest path to a running household, on a host that already has Home Assistant elsewhere and
just needs Docker:

```bash
curl -fsSL https://raw.githubusercontent.com/marcmontecalvo/kinward/main/scripts/get-kinward.sh | bash
```

This installs Docker if it is missing (via Docker's own `get-docker.sh`), clones this repository,
and hands off to an interactive wizard that:

- lets you pick which optional peers to install alongside Kinward - [Honcho](https://github.com/plastic-labs/honcho)
  (conversational memory) and [LLM-Wiki](https://github.com/marcmontecalvo/llm_wiki) (curated
  household knowledge) are both selected by default, along with their own prerequisites (Postgres
  with pgvector, Redis); a Home Assistant dev/test container is offered but off by default, since
  most households already run HA elsewhere;
- pulls published images and starts everything with `docker compose` - no local build, no vendored
  source checkouts for Kinward, Honcho, or LLM-Wiki;
- mints a Home Assistant integration token and prints the exact next steps to add
  `custom_components/kinward` to your existing Home Assistant instance.

Household setup itself happens from inside that integration's own setup step in Home Assistant
(Settings -> Devices & Services -> Add Integration -> Kinward): it creates the household using Home
Assistant's own Home Name (Settings -> System -> General), gated by a one-time setup authorization
the wizard prints. This keeps the household's name and the home it manages from ever drifting apart.

Already have the repository checked out? Run the wizard directly instead:

```bash
make setup
# or: bash scripts/kinward-setup.sh --non-interactive --with-honcho --with-llm-wiki
```

Everything below this section documents what the wizard automates, for manual setups, CI, and
debugging.

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

Compose pulls the published `ghcr.io/marcmontecalvo/kinward` image (set `KINWARD_IMAGE` to pin a
different tag, or run `docker compose up --build` to build from `services/kinward` instead) for
three default services:

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

The normal path is the Kinward integration's own setup step in Home Assistant (Settings -> Devices
& Services -> Add Integration -> Kinward): once it sees a backend with no household yet, it asks for
the one-time setup authorization `scripts/kinward-setup.sh` prints (see "Automated setup" above) and
creates the household using Home Assistant's own Home Name (Settings -> System -> General). What
follows is the manual/scripted equivalent - useful for automating outside Home Assistant, or for a
household name that should differ from HA's Home Name.

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
tests. Submit it to `POST http://localhost:8000/api/v1/setup/household` along with the household name,
fallback assistant name, and any selected pet details; the endpoint creates the household and an
ownerless household fallback assistant in one transaction. It requires no provider or integration.
Pets receive no credentials, account, assistant, private memory, approval, delegation, or action
authority; only explicitly entered household-shared care facts are retained.

Kinward has no identity system of its own: people are not created by this call at all. Once
`custom_components/kinward` is connected to this household, Home Assistant's own `person.*` entities
become the only source of Kinward people - the integration syncs them on every poll. A person with no
linked Home Assistant login (e.g. a child) is simply a `person.*` entity with no `user_id` attribute;
nothing Kinward-specific is required to represent them.

Kinward has no administrator designation step either: whoever is a Home Assistant administrator is a
Kinward administrator, full stop. Every sync pass reads each synced person's linked HA user's admin
flag and reconciles their Kinward role to match - promoting or demoting automatically as HA admin
membership changes. Any number of people can hold the role at once. This is a coarse household-role
distinction only; it does not by itself grant access to another adult's private data, which remains
governed separately by privacy classification (see epics.md Story 3.3). Finer-grained permissions
(e.g. a non-admin "manager" role) may be built later if the household actually needs them.

Setup uses an explicit CSRF token and an idempotency identity. The authorization is stored only as a
hash and becomes terminally unusable after commit - a household, once created, permanently blocks any
further bootstrap attempt regardless of whether the environment variable is still set, so removing it
afterward is optional hardening rather than a required step. `/api/v1/setup/status` reports only
whether setup is available or complete; it never returns a reusable setup authorization.

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

No Redis, memory, knowledge, calendar, Home Assistant, or observability service exists in the
default topology. Model, memory, and knowledge peers are opt-in adapter profiles like PostgreSQL:

```bash
docker compose -f compose.yaml -f compose.honcho.yaml --profile honcho up
docker compose -f compose.yaml -f compose.llmwiki.yaml --profile llm-wiki up
```

Both pull published images (`ghcr.io/plastic-labs/honcho`, `ghcr.io/marcmontecalvo/llm_wiki`) rather
than building from source, so no vendored checkout is needed; `scripts/kinward-setup.sh` (see
"Automated setup" above) handles generating their secrets and pointing Kinward's provider settings at
them. Doing this by hand means: set `KINWARD_HONCHO_POSTGRES_PASSWORD` and one of
`KINWARD_HONCHO_LLM_OPENAI_API_KEY`/`KINWARD_HONCHO_LLM_ANTHROPIC_API_KEY`/`KINWARD_HONCHO_LLM_GEMINI_API_KEY`
for Honcho (it will not start without one) and `KINWARD_LLM_WIKI_UI_PASSWORD` for LLM-Wiki, then set
`memoryBackend`/`honchoUrl`
and `knowledgeBackend`/`llmWikiUrl` via `PATCH /api/v1/integration/settings/providers` (or the
Kinward integration's Options flow in Home Assistant) once they're healthy.

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

### Connect Google/Microsoft calendar accounts

Off-script by product decision: this is the one Kinward-owned webpage in the system (everywhere
else, Home Assistant's own core cards are the UI). Connecting an account requires a real browser
redirect to Google's or Microsoft's consent screen and back, which no Lovelace card or
`kinward.*` service call can do, so it is served directly by the `api` container at
`{KINWARD_OAUTH_REDIRECT_BASE_URL}/setup/accounts`.

Both providers are entirely optional and independently gated - a household with neither configured
sees no change. To enable one:

1. Register an OAuth app with the provider and add
   `{KINWARD_OAUTH_REDIRECT_BASE_URL}/api/v1/setup/accounts/{google|microsoft}/callback` as an
   allowed redirect URI:
   - Google: [Google Cloud Console](https://console.cloud.google.com/apis/credentials) → OAuth
     client ID (Web application), with the Calendar API enabled.
   - Microsoft: [Azure App registrations](https://portal.azure.com) → new registration, with a
     `Calendars.Read`/`offline_access`/`User.Read` delegated permission grant.
2. Set `KINWARD_GOOGLE_CLIENT_ID`/`KINWARD_GOOGLE_CLIENT_SECRET` and/or
   `KINWARD_MICROSOFT_CLIENT_ID`/`KINWARD_MICROSOFT_CLIENT_SECRET`, plus
   `KINWARD_OAUTH_REDIRECT_BASE_URL` (the externally reachable URL Kinward itself is served at, no
   trailing slash).
3. Generate and set `KINWARD_ACCOUNT_TOKEN_ENCRYPTION_KEY` (stored tokens are Fernet-encrypted at
   rest, distinct from any HA or setup secret):
   ```bash
   python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
4. Generate and set `KINWARD_ACCOUNTS_SETUP_TOKEN` (a long-lived shared secret, at least 24
   characters - unlike `KINWARD_SETUP_AUTHORIZATION` this one is not single-use and is not removed
   after use; it gates the setup page itself).
5. Restart `api`, then visit `{KINWARD_OAUTH_REDIRECT_BASE_URL}/setup/accounts`, enter the setup
   token, and connect an account per household member.

Once connected, an account's events flow through the exact same detection/attention/briefing
pipeline Epic 5's Home Assistant calendars already use (`sensor.kinward_attention`, the Briefings
Card) - no separate surface. `sensor.kinward_connected_accounts` reports connection status
(including when a token needs reauthorization) and carries the setup page's URL as an attribute, so
it's discoverable from Home Assistant without leaving it. Disconnecting removes the stored
credentials immediately (best-effort revoked with the provider for Google) and stops that
account's events from syncing on the next pass.

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
