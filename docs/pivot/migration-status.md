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
| Household domain contracts | `services/kinward/src/kinward/domain/models.py` | No persistence assumptions |
| Optional integration resilience | `services/kinward/src/kinward/integrations/base.py` | Secure TLS defaults, safe fallback, circuit breaker |
| Home Assistant seam | `services/kinward/src/kinward/integrations/home_assistant.py` | HA remains physical-state authority |
| Memory/knowledge seams | `services/kinward/src/kinward/integrations/memory.py` | Optional and non-blocking |
| Calendar/mail/voice contracts | `services/kinward/src/kinward/integrations/protocols.py` | Vendor-neutral protocols |
| Health capability reporting | `services/kinward/src/kinward/app.py` | Disabled optional peers are not startup failures |
| Modular UI card foundation | `apps/web/src/cards/registry.tsx` | Registry-driven first surface |
| Surface/layout schemas | `packages/schemas/src/index.ts` | Shared validation contracts |
| Public-safe Docker stack | `compose.yaml` | Single household with optional data profile |
| Validation workflow | `.github/workflows/ci.yml` | Backend and frontend gates |

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

## Rebuild rather than copy

These capabilities remain product requirements, but their legacy implementations are not clean enough to copy directly:

| Capability | Reason for rebuild |
|---|---|
| Persistence and baseline migration | Legacy schema contains tenant, support, entitlement, and routine history |
| Accounts and invitations | Must fit a simple single-household authentication model |
| Gmail and Google Calendar adapters | Credentials and account boundaries need a fresh public-safe design |
| Voice orchestration | Must align with surface handoff and future native Android boundaries |
| Activity and approvals persistence | Legacy ledger vocabulary is too platform-oriented |
| Progressive onboarding sessions | Old implementation is tied to the superseded onboarding journey |
| Layout editor | New registry/schema foundation should drive it |
| PWA notifications | Must be rebuilt without SaaS notification assumptions |

## Final-gate rule

A row moves from “rebuild” to “migrated and accepted” only when its Kinward implementation has focused tests, current documentation, and no legacy product assumptions or public-repository exposure.
