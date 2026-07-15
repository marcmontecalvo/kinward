# Migration Status

This document records the final-gate disposition of legacy Homefront subsystems.

## Migrated and accepted

| Subsystem | Kinward location | Notes |
|---|---|---|
| Product and UX direction | `_bmad-output/planning-artifacts/` | Renamed and rewritten for Kinward |
| Clean repository decision | `docs/adr/ADR-001-*` | New repository and selective salvage |
| Single-household architecture | `docs/architecture/README.md` | No control plane or tenancy |
| Assistant ownership invariants | `services/kinward/src/kinward/domain/assistant_ownership.py` | Personal owner and shared fallback rules |
| Child/owner permission guards | `services/kinward/src/kinward/domain/permissions.py` | Simplified household model |
| Household domain contracts | `services/kinward/src/kinward/domain/models.py` | Household-native vocabulary |
| Clean persistence baseline | `services/kinward/src/kinward/persistence/` | Household, people, assistants, layouts, approvals, activity, memory index |
| New migration history | `services/kinward/migrations/versions/001_initial_single_household.py` | Replaces the entire legacy chain |
| Atomic initial onboarding | `services/kinward/src/kinward/api/setup.py` | Creates household, first admin, and first personal assistant together |
| Optional integration resilience | `services/kinward/src/kinward/integrations/base.py` | Secure TLS defaults, safe fallback, circuit breaker |
| Home Assistant seam | `services/kinward/src/kinward/integrations/home_assistant.py` | HA remains physical-state authority |
| Memory/knowledge seams | `services/kinward/src/kinward/integrations/memory.py` | Optional and non-blocking |
| Calendar/mail/voice contracts | `services/kinward/src/kinward/integrations/protocols.py` | Vendor-neutral protocols |
| Health capability reporting | `services/kinward/src/kinward/app.py` | Disabled optional peers are not startup failures |
| Public-safe Docker stack | `compose.yaml` | Persistent SQLite default with optional data services |
| Validation workflow | `.github/workflows/ci.yml` | Backend gates |

## Explicitly retired

- `services/control-plane/`
- Multi-tenant and deployment-region identity
- Billing, package entitlement, and marketplace behavior
- Support-operator access and support grants
- Zitadel-specific stubs and SaaS provisioning
- Routine-centric frontend, onboarding, and tests
- Legacy database migration history
- SaaS production and cost-model documentation
- Any fixture or configuration containing real household or infrastructure data
- Standalone `apps/web` five-surface frontend, its `packages/schemas`/`packages/contracts` support packages, and the JS/pnpm toolchain that only served them — retired under the 2026-07-15 HA-native reset (`_bmad-output/implementation-artifacts/ha-native-reset-2026-07-15.md`) in favor of `custom_components/kinward` plus core-card HA dashboards. Salvage review found no code meeting the reset's preserve criteria (see the section below for the two concepts carried forward without code).

## Retired frontend: concepts carried forward without code

The standalone frontend's salvage review (2026-07-15) found no file meeting the reset's preserve criteria as code, but two concepts remain useful for HA-native work and should not be silently lost with the deleted files:

- **Privacy classification taxonomy** (was `apps/web/src/foundation/policy.ts`): the backend contract and HA integration must keep distinguishing `private-person` / `private-child` / `selected-share` / `household-shared` / `surface-ephemeral` / `system-operational` data, and the shared-surface identity states (`unknown` / `candidate` / `group` / `verified-selected` / `expired` / `authorization-loss`) that gate what a shared HA dashboard may ever render.
- **Accessibility test technique** (was `apps/web/e2e/foundation.spec.ts`): axe (`wcag2a`/`wcag2aa`/`wcag22aa`) plus explicit checks for focus visibility, `prefers-reduced-motion`, `forced-colors`, and a 48px minimum interactive target — worth reapplying if a custom dashboard strategy is ever built (deferred, epics.md Story 10.2).

## Rebuild rather than copy

These capabilities remain product requirements, but their legacy implementations are not clean enough to copy directly:

| Capability | Reason for rebuild |
|---|---|
| Accounts and invitations | Must fit a simple single-household authentication model |
| Gmail and Google Calendar adapters | Credentials and account boundaries need a fresh public-safe design |
| Voice orchestration | Must align with surface handoff and future native Android boundaries |
| Activity and approvals services | Persistence exists; service and UI behavior need household-language rebuilding |
| Progressive onboarding sessions | Old implementation is tied to the superseded onboarding journey |
| Layout editor | New registry/schema foundation should drive it |
| PWA notifications | Must be rebuilt without SaaS notification assumptions |

## Final-gate rule

A row moves from “rebuild” to “migrated and accepted” only when its Kinward implementation has focused tests, current documentation, and no legacy product assumptions or public-repository exposure.
