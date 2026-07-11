# Architecture Baseline

Kinward is a single-household Docker-deployed system.

## Initial runtime

- One household backend service.
- One responsive web/PWA client.
- PostgreSQL where durable relational storage is required.
- Redis only where it has a demonstrated runtime purpose.
- Optional Honcho memory adapter.
- Optional LLM-Wiki knowledge adapter.
- Optional local observability profile.
- Home Assistant integration for physical home state and action.

## Primary boundaries

- Household and people.
- Personal assistants.
- Memory and privacy.
- Topics and context.
- Integrations.
- Approvals and activity.
- Cards and layouts.
- Surface resolution.
- Identity and private handoff.

## Constraints

- No control plane.
- No multi-tenancy.
- No billing or commercial entitlement runtime.
- No support-operator access.
- No mandatory Home Assistant dependency.
- No mandatory external memory or knowledge backend.
- No native client requirement for the initial product.
