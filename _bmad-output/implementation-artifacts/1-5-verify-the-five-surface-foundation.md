---
baseline_commit: 2492dc8f6b337c83e51932732c174d30e705db07
---

# Story 1.5: Verify the Five-Surface Foundation

Status: review

## Story

As a household member,
I want Kinward's common assistant experience to adapt coherently across personal and shared surfaces,
so that the product foundation proves privacy, layout, accessibility, and viewing-context behavior before live capabilities expand.

## Acceptance Criteria

1. Personal mobile, tablet, desktop, shared kitchen, and shared living-room mocks render all eight common capabilities through the same card/layout registries with no hard-coded alternative tree.
2. Contexts visibly adapt to interaction, density, privacy, room, and distance. Tablet/desktop are not enlarged mobile; kitchen/living room are distinct; tablet remains mock-only.
3. Synthetic `private-person`, `private-child`, `selected-share`, `household-shared`, `surface-ephemeral`, and `system-operational` fixtures are filtered before response/render. Forbidden private/selected fields are absent, not CSS-hidden.
4. Unknown, candidate, group, expired, and simulated authorization-loss shared states receive only their exact permitted mock fields. Candidate is a neutral salutation with no identity/confidence/private-existence signal; downgrade clears disallowed rendered state.
5. Mobile/desktop retain hierarchy and essential function without horizontal loss; persistent text input, navigation, Now, Briefing, Continue and one dominant decision remain coherent.
6. The reference shared fixture covers Now, Briefing, Approval, House Status, unavailable capability, identity downgrade, and handoff at 100%/200% text scale with >=48x48 CSS px targets, >=8px inactive spacing, required room text sizes, WCAG 2.2 AA contrast, no clipping/overlap/loss, non-color status, and applicable keyboard/screen-reader semantics.
7. Reduced-motion, high-contrast, keyboard-only, and 1.5 m room-distance inspections pass with visible focus and plain non-color private-session/timeout cues.
8. With providers absent all contexts render from clearly identified mock adapters and truthfully show degraded/unavailable/intentionally-disabled states; mock data is never presented as live.
9. Automated/inspectable Milestone A evidence covers resolution, card presence, surface distinction, privacy-field absence, invalid-layout fallback, responsive/keyboard/accessibility behavior, uses fictional data, and does not claim Milestone B live completion.

Addresses `FR-035`, `FR-036`, `FR-040`, `FR-041`, `NFR-003`, `NFR-023-NFR-027`, `NFR-031`, `NFR-032`, `UX-DR1-UX-DR9`, `UX-DR11-UX-DR17`, `UX-DR20`, `UX-DR25-UX-DR29`, `AD-15`, `AD-21`, and `AD-22`.

## Tasks / Subtasks

- [x] Build one authoritative synthetic fixture/policy harness (AC: 1-4, 8)
  - [x] Define five complete surface contexts and all required data classes/shared identity states with obviously fictional values.
  - [x] Create mock adapters that apply deterministic policy before view-model serialization and expose byte/field-inspectable payloads; do not rely on renderer hiding.
  - [x] Add downgrade/uncertainty transitions that replace payloads and clear stale private DOM/state; do not persist private fixture content in shared browser storage/cache.
- [x] Integrate the five surface shells (AC: 1-5, 8)
  - [x] Render the same Story 1.3 registry through Story 1.4 resolution/defaults for every context.
  - [x] Implement distinct mobile/tablet/desktop/kitchen/living-room hierarchy, room defaults, density, interaction, and viewing-distance treatment.
  - [x] Keep Assistant Experience separate from Kinward Control and retain text-only input.
- [x] Add automated browser and contract verification (AC: 1-9)
  - [x] Add Playwright (or repository-standard equivalent) checks for registry identity, card presence, layout provenance, surface distinctions, forbidden-field absence, candidate exactness, downgrade clearing, invalid fallback, responsive behavior and provider absence.
  - [x] Add axe/semantic/keyboard/focus/reduced-motion/high-contrast tests and programmatic target size/spacing/contrast checks at 100% and 200% scaling.
  - [x] Inspect the fixed shared fixture at the documented 21.5-inch 1920x1080 Chromium-kiosk baseline from 1.5 m; record exact environment/version/hash if this evidence is used for a gate.
- [x] Package Milestone A evidence safely (AC: 9)
  - [x] Produce reproducible test reports/screenshots/manifests without machine-specific logs, credentials, private hosts, databases, or real household data.
  - [x] Label every result “mock-backed foundation”; explicitly list Milestone B live mobile/desktop/shared/auth/backend-privacy work as unproven.
  - [x] Run `make lint`, `make typecheck`, `make test`, and `make build` plus the browser suite.

## Dev Notes

### Prerequisites and Current State

- Requires completed Story 1.3 card registrations and Story 1.4 resolver/defaults. If their contracts are not stable, finish them rather than introducing a test-only registry/layout path.
- Current `App.tsx` renders one generic responsive page, CSS only distinguishes <=760 and >=1400 widths, and no Playwright setup exists. Replace single-layout assumptions with surface fixtures; preserve useful tokens/primitives.
- Existing examples resemble plausible personal data. All new fixture names, schedules, rooms, topics, screenshots, and IDs must be unmistakably synthetic.
- Story 1.1 provides no-provider deployment and current toolchain. Reuse its health/capability vocabulary and production shell; do not make E2E depend on optional providers.

### Architecture and Scope Guardrails

- This is a mock-backed Milestone A proof, not live authentication, private shared-session authority, handoff redemption, assistant streaming, or backend provider integration.
- Passive/simulated identity never creates verified private authority. Mock shared-state policy must follow exact field allowlists and fail closed.
- Do not store shared private payloads in localStorage, IndexedDB, service-worker caches, screenshots, or error reports. Tests should inspect storage/cache where practical.
- The PRD places the fixed reference-display acceptance audit in Milestone C; Story 1.5 should build and exercise the fixture now, but must not overclaim a frozen Milestone C gate unless AD-15 environment evidence is actually frozen.
- No layout editor, voice, multimodal input, context targeting, emergency mode, specialist assistant, or live tablet claim.

### Testing and Evidence Ownership

- FE: five shells, responsive behavior, registry/layout provenance, browser automation.
- BE/security: review policy-filtered mock serialization and exact forbidden-field absence.
- QA: accessibility automation/manual distance inspection, evidence manifest, public-safety scan and no-live-claim review.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story 1.5: Verify the Five-Surface Foundation`]
- [Source: `_bmad-output/planning-artifacts/prd-Kinward-Assistant-Experience.md#4.1.1 Frontend-foundation gate (mock-backed)`]
- [Source: `_bmad-output/planning-artifacts/prd-Kinward-Assistant-Experience.md#15.4 Accessibility and usability`]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification-Kinward-Assistant-Experience.md#Experience by Surface`]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification-Kinward-Assistant-Experience.md#Initial Cross-Surface Vertical Slice`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md#AD-15 - Cross-database and cross-surface evidence gate`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/SOLUTION-DESIGN.md#Test strategy and release evidence`]
- [Source: `_bmad-output/implementation-artifacts/1-4-resolve-validated-layouts-safely.md#Dev Notes`]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- `make lint && make typecheck && make test && make build && make browser-test` (2026-07-15): all gates passed; 45 backend tests, 22 web unit/contract tests, and 21 runnable Chromium checks passed with one intentional mobile skip for the desktop-only fixed-reference audit.
- Fixed reference: Chromium 149.0.7827.55, Playwright 1.61.1, 1920×1080 CSS px, device scale 1; exact test hash is recorded in the evidence manifest.

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Added one policy-first fictional harness for all six required data classes and all shared identity uncertainty/downgrade states, with inspectable pre-render serialization.
- Added five distinct surface contexts and shells that consume the same eight-card registry and immutable layout resolver/defaults, with safe shared-surface fallbacks for every card.
- Proved candidate neutrality, exact selected sharing, authorization-loss DOM clearing, and empty shared local/session/IndexedDB/cache state.
- Added Chromium desktop/mobile automation for registry/layout provenance, responsive hierarchy, invalid fallback, provider absence, keyboard/focus, axe WCAG 2.2 A/AA, reduced motion, forced colors, 48px targets, 8px spacing, clipping/overlap, and 100%/200% scaling.
- Packaged reproducible fictional reports/screenshots/manifest guidance and explicitly listed all Milestone B live work and the Milestone C physical freeze as unproven.

### File List

- `Makefile`
- `apps/web/e2e/foundation.spec.ts`
- `apps/web/package.json`
- `apps/web/playwright.config.ts`
- `apps/web/src/App.tsx`
- `apps/web/src/foundation/policy.test.ts`
- `apps/web/src/foundation/policy.ts`
- `apps/web/src/styles.css`
- `apps/web/vite.config.ts`
- `docs/evidence/milestone-a-foundation/README.md`
- `docs/evidence/milestone-a-foundation/manifest.json`
- `mise.toml`
- `pnpm-lock.yaml`

## Change Log

- 2026-07-15: Implemented and verified the five-surface mock-backed Milestone A foundation; status moved to review.
