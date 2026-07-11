# Homefront → Kinward Salvage Matrix

This document controls what may be moved from the legacy Homefront repository. Nothing is copied merely because it exists.

| Subsystem | Initial disposition | Required review |
|---|---|---|
| Household people and roles | Refactor and move | Remove tenant and commercial-role assumptions |
| Personal assistants | Refactor and move | Rename contracts and verify multiple assistants per user |
| Per-user/per-assistant memory | Refactor and move | Verify ownership, privacy, deletion, and optional backends |
| Assistant personality | Refactor and move | Preserve interview/configuration behavior only |
| Calendar integration | Refactor and move | Remove SaaS credentials and tenant routing |
| Gmail/email integration | Refactor and move | Preserve household-scoped auth and privacy |
| Home Assistant integration | Refactor and move | Keep HA as physical-state authority |
| Voice STT/TTS seams | Evaluate | Retain protocol boundaries, not old UI assumptions |
| Permissions and approvals | Rewrite around one household | Remove entitlement and support-operator rules |
| Activity ledger | Refactor and move | Use plain household explanations |
| Rate limiting | Move | Reframe as local protection |
| Health and observability | Refactor and move | Local-only, optional observability profile |
| Honcho adapter | Refactor and move | Optional; backend must boot without it |
| LLM-Wiki adapter | Refactor and move | Optional; backend must boot without it |
| Database models | Selective rewrite | Start with a new baseline migration |
| API routing | Selective rewrite | Household terminology and new contracts |
| Existing web frontend | Retire | Salvage only proven generic primitives/tooling |
| Existing card/layout code | Audit | Keep only if genuinely declarative and decoupled |
| Control plane | Retire | Do not copy |
| Tenant identity | Retire | Do not copy |
| Billing/entitlements | Retire | Do not copy |
| Support access | Retire | Do not copy |
| Zitadel/OIDC stubs | Retire unless newly justified | Do not copy by default |
| SaaS deployment docs | Archive only | Do not add to Kinward |
| Routine-centric UI/docs/tests | Retire | Do not copy |
| Legacy migration chain | Retire | New `001_initial_single_household` baseline |

## Acceptance rule

A subsystem may move only after:

1. Its current behavior is documented.
2. SaaS and multi-tenant assumptions are identified.
3. Required contracts are defined in Kinward.
4. Tests are selected or rewritten around retained behavior.
5. The smallest useful implementation is migrated.
6. The implementation passes its own unit and integration checks.
