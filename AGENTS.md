# Kinward Agent Instructions

## Product boundary

Kinward is a private, single-household AI assistant platform. It is not a SaaS control plane, a coding assistant, a morning-routine application, or a generic Home Assistant dashboard.

## Authoritative planning

Use only these current documents for product direction:

- `_bmad-output/planning-artifacts/product-brief-Kinward-Assistant-Experience.md`
- `_bmad-output/planning-artifacts/ux-design-specification-Kinward-Assistant-Experience.md`
- `docs/pivot/single-household-pivot-and-rebuild-plan.md`
- `docs/pivot/salvage-matrix.md`

Do not import legacy Homefront planning documents into this repository.

## Public repository safety

Never commit:

- Real household names, schedules, email addresses, memories, or location data.
- API keys, OAuth credentials, tokens, cookies, private keys, or passwords.
- Internal hostnames, LAN IP addresses, private domains, or deployment-specific URLs.
- Production `.env` files, databases, backups, logs, or support bundles.

Examples and fixtures must use obviously fictional values.

## Architecture rules

- One deployment serves one household.
- Optional integrations must degrade safely and must not block startup.
- Home Assistant remains the physical-state authority.
- Personal assistants have one owner; the shared fallback assistant has no personal owner.
- Personal and shared privacy boundaries are enforced before rendering or action.
- Web/PWA is first. Native Android remains deferred.
- UI surfaces use registered cards and declarative layouts.
- Everyday assistant UX stays separate from Kinward Control.

## Migration rule

Do not copy legacy Homefront files wholesale. For every retained subsystem:

1. Document the useful behavior.
2. Remove tenant, control-plane, entitlement, support-access, and routine assumptions.
3. Define a Kinward contract.
4. Move or rewrite the smallest useful implementation.
5. Add focused tests.
6. Pass the final public-repository safety review.

## Validation

Before considering work complete, run the relevant subset of:

```bash
make lint
make typecheck
make test
make build
```
