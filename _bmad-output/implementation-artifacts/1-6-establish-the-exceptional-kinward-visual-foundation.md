---
baseline_commit: 2492dc8f6b337c83e51932732c174d30e705db07
course_correction: _bmad-output/planning-artifacts/sprint-change-proposal-2026-07-15.md
visual_review_mode: incremental-visual-only
---

# Story 1.6: Establish the Exceptional Kinward Visual Foundation

Status: ready-for-dev

## Story

As a household member,
I want every Kinward surface to feel beautiful, coherent, personal, and purpose-built,
so that the interface can sustain trust and delight as the household's daily assistant foundation.

## Acceptance Criteria

1. One versioned token system owns color, typography, spacing, sizing, radius, border, elevation, opacity, layering, motion, focus, targets, and supported responsive thresholds. Primitive, semantic, and surface-context tokens have explicit ownership; application presentation contains no unapproved raw visual values.
2. Local and CI lint rejects raw colors, restricted numeric visual values, arbitrary inline presentation, direct primitive-token use where semantic intent is required, and silent suppressions. A documented allowlist covers structural necessities; declarative grid placement flows through one audited layout-style adapter.
3. The assistant surfaces and setup experience compose a small reusable semantic primitive layer. Primitives own presentation and accessibility mechanics; features and cards own meaning, content structure, and typed intents.
4. All eight cards retain one thin semantic registered-renderer contract and receive intentional treatments for personal mobile, personal tablet, personal desktop, shared kitchen, and shared living room. Treatments adapt structure and hierarchy rather than acting as recolored copies or forty unrelated implementations.
5. Mobile is an intimate pocket presence with one dominant Now item, quiet briefing, Continue, persistent input, and minimal bottom navigation. Tablet is a deliberate touch-and-keyboard planning canvas. Desktop is a focused workspace with persistent navigation, continuity, adaptive canvas, and input. None reads as a generic dashboard or enlarged version of another surface.
6. Kitchen is active, glanceable, task-proximate, touch/voice compatible, and room-readable. Living room is ambient, quiet, distance-first, socially shared, and visually distinct. Both preserve household-safe defaults, minimal navigation, and unmistakable privacy/session cues.
7. The complete foundation feels calm, warm, intelligent, personal, restrained, trustworthy, and quietly magical. Cards remain presentation primitives rather than the product metaphor. Assistant presence is non-humanoid. Availability, progress, approval, uncertainty, completion, failure, cancellation, privacy, and degradation remain distinct without color alone.
8. Visual Gate A presents a compact direction gallery. Gate B presents representative Presence, Now, Briefing, Approval, and Assistant Input on mobile, desktop, and living room. Gate C presents all eight cards on all five surfaces. Gate D presents final responsive, interaction, empty/degraded/error, text-scale, reduced-motion, and forced-color polish. Marc reviews rendered visuals only and explicitly approves every gate.
9. Token enforcement, primitive boundaries, bounded visual regression, keyboard operation, WCAG 2.2 AA, non-color states, 100%/200% text scale, touch targets, and shared-display distance requirements pass. All Story 1.3–1.5 registry, layout, privacy, forbidden-field, fallback, responsive, accessibility, and public-safety evidence remains green. Epic 2 remains blocked until Gate D approval.

## Tasks / Subtasks

- [ ] Establish the visual-review workflow before broad implementation (AC: 7, 8)
  - [ ] Produce Gate A as a compact rendered comparison of 2–3 coherent art directions using obviously fictional content; show personal mobile, personal desktop, and shared living-room moments rather than isolated swatches.
  - [ ] Present only rendered images or a directly inspectable preview to Marc. Ask for visual reaction and selection; do not request source, lint, or implementation review.
  - [ ] Record the selected direction and specific visual feedback in this story's Dev Agent Record. Remove or production-disable any temporary review-only route before completion.
- [ ] Build the governed token foundation (AC: 1, 2, 7)
  - [ ] Create explicit primitive, semantic, component-when-necessary, and five-surface token layers under `apps/web/src/design-system/tokens/`; include descriptions/ownership and avoid aliases that conceal circular or meaningless indirection.
  - [ ] Express application CSS entirely through semantic/custom-property references. Raw definitions belong only in designated token sources; setup, forced-colors, reduced-motion, focus, and responsive rules are included.
  - [ ] Add Stylelint and a repository-owned token audit where built-in rules cannot express the boundary. Add ESLint AST restrictions for JSX `style` and presentation bypasses, with a file-scoped exception only for the audited layout-style adapter.
  - [ ] Make suppression impossible without a named documented allowlist entry and negative tests proving representative forbidden values fail the guard.
  - [ ] Wire token/style validation into `pnpm lint`, `mise lint`, and therefore `make lint`; commit compatible pinned dependencies through the existing lockfile.
- [ ] Create the semantic primitive layer (AC: 3, 7)
  - [ ] Add focused primitives under `apps/web/src/design-system/primitives/` for surface/layout composition, typography, card frame, button/action, status, navigation, composer, list structures, assistant presence, privacy cue, and empty/unavailable presentation.
  - [ ] Keep primitives accessible by construction: semantic HTML, visible focus, disabled semantics, target size, non-color state cues, reduced-motion support, and forwarded labels/relationships.
  - [ ] Do not introduce a generic mega-component, arbitrary style props, unrestricted `className` escape hatches, a runtime CSS-in-JS dependency, or a duplicate card/layout registry.
  - [ ] Migrate `Setup.tsx` to applicable tokens/primitives without changing setup API behavior, validation, CSRF, accessibility, or retry semantics.
- [ ] Introduce surface shells and the audited layout adapter (AC: 2, 5, 6)
  - [ ] Split the monolithic `App` presentation into explicit personal-mobile, personal-tablet, personal-desktop, shared-kitchen, and shared-living-room shell compositions that consume the same resolved layout and policy-filtered views.
  - [ ] Keep surface selection driven by validated `SurfaceContext`; media queries handle physical reflow but never infer privacy, ownership, room, or authorization.
  - [ ] Move data-driven grid column/row/count/gap application into one small audited adapter. It may set only declared layout custom properties; it cannot accept general visual styles.
  - [ ] Preserve all `data-*` inspection hooks needed for provenance, fallback, privacy, interaction, viewing distance, and browser tests.
  - [ ] Preserve the exact shared-identity controls and downgrade-clearing test seam while visually integrating it as review scaffolding, not ordinary household navigation.
- [ ] Refactor cards into thin semantic renderers with five intentional treatments (AC: 3, 4, 7)
  - [ ] Preserve registration keys, versions, schemas, surface support, sizing contracts, capabilities, `resolveCard`, typed `CardIntent`, safe fallback behavior, and pre-render policy boundary.
  - [ ] Split card semantic renderers from registry mechanics. Compose primitives; do not put authorization, fixture selection, storage, API calls, raw style values, or layout policy into renderers.
  - [ ] Implement surface-aware composition through bounded named variants derived from `SurfaceContext`; do not fork forty independent renderers.
  - [ ] Make empty/loading/degraded/unavailable/stale/error and approval lifecycle states truthful, concise, visually distinct, and non-color-dependent.
- [ ] Run Gate B and converge the foundation slice (AC: 4–8)
  - [ ] Render Presence, Now, Briefing, Approval, and Assistant Input on personal mobile, personal desktop, and shared living room at their reference viewports.
  - [ ] Present a visual contact sheet or directly inspectable preview only. Incorporate Marc's feedback before migrating the remaining cards/surfaces.
  - [ ] Record approval and direction changes in the Dev Agent Record.
- [ ] Complete all five surfaces and run Gate C (AC: 4–8)
  - [ ] Complete all eight card treatments and mobile/tablet/desktop/kitchen/living-room shells using the selected language.
  - [ ] Demonstrate hierarchy, density, navigation, composer, privacy cues, and room-distance behavior through rendered full-surface views.
  - [ ] Do not advance to final polish without Marc's explicit rendered-visual approval.
- [ ] Add enforceable and bounded verification (AC: 2, 3, 9)
  - [ ] Add unit tests for token audit failures, primitive invariants, semantic renderer boundaries, and the audited layout adapter.
  - [ ] Add stable Playwright screenshots for the five default shells and a representative state matrix. Pin/freeze browser, fonts, animations, fixture time, and viewport inputs so diffs are meaningful.
  - [ ] Preserve and adapt the existing 22 web tests and 22 browser cases rather than deleting assertions that become inconvenient.
  - [ ] Retain axe WCAG 2.2 A/AA, keyboard/focus, 48px targets, inactive spacing, 100%/200% scale, overflow, reduced motion, forced colors, privacy clearing, storage emptiness, and invalid-layout fallback evidence.
- [ ] Run Gate D and close only after explicit visual approval (AC: 7–9)
  - [ ] Present final happy, empty, degraded, unavailable, error, approval-progress, privacy-loss, responsive, text-scale, reduced-motion, and forced-color rendered evidence without asking Marc to inspect code or reports.
  - [ ] Apply requested polish and repeat affected visual comparisons until explicitly approved.
  - [ ] Run `make lint`, `make typecheck`, `make test`, `make build`, `make browser-test`, `make smoke`, `git diff --check`, and the public-repository safety scan.
  - [ ] Do not mark the story complete or unblock Epic 2 without Gate D approval, even when every automated check passes.

## Dev Notes

### Non-negotiable review model

- Marc reviews visuals, not implementation. Commentary at Gates A–D should lead with rendered output and one focused visual question.
- Do not present token inventories, code diffs, lint output, test logs, or architecture prose as a substitute for a visual gate.
- Automated success cannot override visual rejection. Record feedback and iterate.

### Current implementation and preservation map

- `App.tsx` currently owns surface/identity query seams, policy payload selection, layout resolution, shell markup, navigation, identity controls, inline grid styles, renderer dispatch, and privacy cues. Split presentation while preserving the query/test seams and resolution flow.
- `cards/registry.tsx` currently mixes registry mechanics, `CardShell`, eight renderers, visible state copy, and intents. Preserve registry behavior and schemas; separate renderers and compose primitives.
- `styles.css` is one global raw-value stylesheet. Replace it with token and design-system layers; do not merely rename existing literals into tokens without revisiting visual decisions.
- `layouts/defaults.ts` owns declarative placements for all eight cards on all five surfaces. Preserve schema validity and default identities. Adjust placements when the selected art direction requires it, but keep all eight instances and deterministic resolver behavior.
- `foundation/policy.ts` and fixtures enforce pre-render privacy. Treat them as presentation inputs; do not move policy into shells or cards.
- `Setup.tsx` is a working accessible setup form. Reskin/recompose it without changing network, auth, CSRF, validation, or lifecycle behavior.
- `e2e/foundation.spec.ts` proves the Milestone A safety/accessibility contract. Update selectors intentionally and retain equivalent or stronger assertions.

### Token enforcement boundary

- “No hardcoding” means no unapproved raw **visual** values outside token definitions. Semantic HTML, user-facing copy, card type/version, layout coordinates, state enums, and interaction behavior remain explicit code.
- Token definitions may contain raw values. Application/component CSS must use semantic variables. Surface tokens may alias semantic decisions but cannot override privacy or state meaning.
- Allow structural constants only through a reviewed list. Expected examples: `0`, `100%`, `currentColor`, `inherit`, screen-reader clipping, and layout data converted to audited custom properties.
- CSS lint alone is insufficient because JSX can bypass it. Enforce both stylesheet values and TSX syntax/import boundaries.

### Architecture and scope guardrails

- Preserve AD-22: server-produced policy-filtered view models, registered cards only, validated layouts, deterministic precedence, last-valid fallback, separate everyday/control shells.
- No backend/API/schema/database work is expected unless a test exposes a genuine regression. Do not add authentication, streaming, live topics, provider integrations, layout editing, voice, multimodal input, or Kinward Control.
- Do not add a UI framework merely to accelerate styling. The current UI is small; own a focused Kinward primitive layer. A dependency requires a demonstrated need and lockfile update.
- Do not copy the legacy Homefront frontend or its visual system.
- All fixtures, screenshots, and review content must be obviously fictional and public-safe.

### Tooling guidance

- Use the current React 19.2, TypeScript 7 strict, Vite 8, Vitest 4, Playwright 1.61, and pnpm 11 workspace. Do not downgrade or replace the build stack.
- Stylelint's current rules can reject raw colors and property/value patterns; use a small project-owned audit for semantic-token and exception rules that cannot be expressed reliably with configuration alone.
- ESLint `no-restricted-syntax` accepts AST selectors and can prohibit JSX style attributes outside the audited adapter. Keep the rule narrow and test it against failing fixtures.
- Playwright `toHaveScreenshot()` is appropriate for stable comparisons, but baselines must run in a frozen environment because browser/OS/font rendering changes pixels.
- The DTCG 2025.10 format is a stable interoperability reference. Do not introduce a token build pipeline solely for theoretical portability; CSS custom properties plus typed/documented source data are sufficient unless Gate A reveals a real cross-tool need.

### Expected file organization

```text
apps/web/
  eslint.config.*
  stylelint.config.*
  src/
    design-system/
      tokens/
      primitives/
      token-audit.test.*
    surfaces/
      personal-mobile/
      personal-tablet/
      personal-desktop/
      shared-kitchen/
      shared-living-room/
      ResolvedSurface.*
      layoutStyleAdapter.*
    cards/
      registry.*
      renderers/
    App.tsx
    Setup.tsx
  e2e/
    foundation.spec.ts
    visual-foundation.spec.ts
```

Exact filenames may be simplified, but preserve these ownership boundaries. Avoid one file per trivial wrapper and avoid recreating a monolithic `styles.css`.

### Testing strategy

- Unit: registry invariants, render semantics, primitive a11y contracts, layout adapter allowlist, token graph/alias resolution, forbidden-value negative fixtures.
- Browser functional: existing five surfaces, eight registered cards, provenance, fallback, identity downgrade, storage absence, responsive hierarchy, keyboard/focus, scale, targets, contrast, forced colors, reduced motion.
- Browser visual: five default shell baselines plus bounded representative states. Use stable fictional data and deterministic time; mask only genuinely nondeterministic browser artifacts, never product content.
- Manual/product: Gates A–D through rendered previews. Gate approval is a required input, not inferred from silence.

### Previous-story intelligence

- Story 1.5 finished with 45 backend tests, 22 web tests, and 21 passing Chromium checks plus one intentional viewport-specific skip.
- Its evidence manifest binds the browser version and test-source hash; update provenance truthfully when visual tests change.
- Shared safe fallbacks were required so every surface could render all eight cards without leaking private existence. Preserve that invariant.
- Candidate identity must remain neutral, and authorization loss must remove forbidden DOM and browser state—not visually hide it.

### References

- [Source: `_bmad-output/planning-artifacts/sprint-change-proposal-2026-07-15.md`]
- [Source: `_bmad-output/planning-artifacts/epics.md#Story 1.6: Establish the Exceptional Kinward Visual Foundation`]
- [Source: `_bmad-output/planning-artifacts/prd-Kinward-Assistant-Experience.md#4.1.1 Frontend-foundation gate (mock-backed)`]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification-Kinward-Assistant-Experience.md#Visual Foundation`]
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-kinward-2026-07-14/ARCHITECTURE-SPINE.md#AD-22 — Registry-driven policy-filtered frontend`]
- [Source: `_bmad-output/implementation-artifacts/1-5-verify-the-five-surface-foundation.md`]
- [Stylelint rules](https://stylelint.io/user-guide/rules/)
- [ESLint `no-restricted-syntax`](https://eslint.org/docs/latest/rules/no-restricted-syntax)
- [Playwright visual comparisons](https://playwright.dev/docs/test-snapshots)
- [Design Tokens Format Module 2025.10](https://www.designtokens.org/tr/2025.10/format/)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Product owner review mode is incremental and visual-only; Story 1.6 blocks Epic 2 until final visual approval.

### File List

## Change Log

- 2026-07-15: Approved course correction applied; Story 1.6 created and set ready for development.
