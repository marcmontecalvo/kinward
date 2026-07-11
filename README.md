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

Or start the Docker runtime:

```bash
make up
```

## License

Kinward is source-available under the PolyForm Noncommercial License 1.0.0. Personal, educational, research, hobby, and other qualifying noncommercial use is permitted. Commercial use requires a separate license from the copyright holder.
