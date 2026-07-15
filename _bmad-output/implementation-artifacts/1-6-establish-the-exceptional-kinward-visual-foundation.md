---
baseline_commit: 2492dc8f6b337c83e51932732c174d30e705db07
course_correction: _bmad-output/planning-artifacts/sprint-change-proposal-2026-07-15.md
visual_review_mode: incremental-visual-only
---

# Story 1.6: Establish the Exceptional Kinward Visual Foundation

Status: in-progress

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
7. The complete foundation feels calm, warm, intelligent, personal, restrained, trustworthy, and quietly magical. Cards remain presentation primitives rather than the product metaphor. Availability, progress, approval, uncertainty, completion, failure, cancellation, privacy, and degradation remain distinct without color alone.
8. Visual Gate A presents a compact direction gallery. Gate B presents representative Presence, Now, Briefing, Approval, and Assistant Input on mobile, desktop, and living room. Gate C presents all eight cards on all five surfaces. Gate D presents final responsive, interaction, empty/degraded/error, text-scale, reduced-motion, and forced-color polish. Marc reviews rendered visuals only and explicitly approves every gate.
9. Token enforcement, primitive boundaries, bounded visual regression, keyboard operation, WCAG 2.2 AA, non-color states, 100%/200% text scale, touch targets, and shared-display distance requirements pass. All Story 1.3–1.5 registry, layout, privacy, forbidden-field, fallback, responsive, accessibility, and public-safety evidence remains green. Epic 2 remains blocked until Gate D approval.

## Tasks / Subtasks

- [x] Establish the visual-review workflow before broad implementation (AC: 7, 8)
  - [x] Produce Gate A as a compact rendered comparison of 2–3 coherent art directions using obviously fictional content; show personal mobile, personal desktop, and shared living-room moments rather than isolated swatches.
  - [x] Present only rendered images or a directly inspectable preview to Marc. Ask for visual reaction and selection; do not request source, lint, or implementation review.
  - [x] Record the selected direction and specific visual feedback in this story's Dev Agent Record. Remove or production-disable any temporary review-only route before completion.
- [x] Build the governed token foundation (AC: 1, 2, 7)
  - [x] Create explicit primitive, semantic, component-when-necessary, and five-surface token layers under `apps/web/src/design-system/tokens/`; include descriptions/ownership and avoid aliases that conceal circular or meaningless indirection.
  - [x] Express application CSS entirely through semantic/custom-property references. Raw definitions belong only in designated token sources; setup, forced-colors, reduced-motion, focus, and responsive rules are included.
  - [x] Add Stylelint and a repository-owned token audit where built-in rules cannot express the boundary. Add ESLint AST restrictions for JSX `style` and presentation bypasses, with a file-scoped exception only for the audited layout-style adapter.
  - [x] Make suppression impossible without a named documented allowlist entry and negative tests proving representative forbidden values fail the guard.
  - [x] Wire token/style validation into `pnpm lint`, `mise lint`, and therefore `make lint`; commit compatible pinned dependencies through the existing lockfile.
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

### Gate A — round 1 (rejected)

- Presented three directions: Warm Hearth (warm cream/serif/terracotta ember-glow), Quiet Studio (cool neutral geometric sans, pulse-line presence), Ambient Glow (parchment-to-twilight shift, breathing violet glow).
- Marc's feedback: rejected all three outright ("I honestly don't like any of those"). No direction approved.
- Root cause per Marc: all three were tightly art-directed by me into the same structural skeleton with only font/color swapped — not genuinely different bets. Instruction for round 2: give much more open briefs, don't constrain structure/palette/type, let each model take its own direction, and run it across all available free OpenRouter models in parallel rather than a small hand-picked set.

### Gate A — round 2 (raw results, not yet reviewed by Marc)

- Ran a 19-model swarm (every suitable free-tier OpenRouter model) against one open brief: only non-humanoid presence, the three required moments (personal-mobile/personal-desktop/shared-living-room), fictional content, and a self-contained file were fixed — palette, typography, and layout structure were each model's own call.
- Marc asked to stop the run before it finished and see the raw results as-is. 10 of 19 tasks had completed and passed before the stop (4 failed outright: dolphin-mistral-24b-venice, llama-3.2-3b, hermes-3-405b, gpt-oss-20b; 3 were mid-retry; 2 were on their first attempt).
- Posted all 10 unedited results to the same Gate A review artifact, labeled by model, with factual notes (no direction chosen or recommended yet). Two stood out on a first look as genuinely distinct (Tencent Hy3's "quiet garden wall" breathing-ring concept, Nvidia Nemotron 3 Ultra's editorial card-density concept); one (Nemotron Nano 12B VL) came back broken/off-brief; a few others were only lightly styled.
- Awaiting Marc's actual direction pick before any further work proceeds.

### Gate A — round 3 (dark mode, raw results, not yet reviewed by Marc)

- Marc named Tencent Hy3 as his favorite from round 2 and asked for one more round: re-run only the models that returned genuinely formatted, on-brief work (excluding the 4 outright failures and the off-brief/broken Nemotron Nano 12B VL result), this time requiring a fully dark theme across all three moments.
- Re-ran 6 models (Hy3, Nemotron 3 Ultra, North Mini Code, Laguna M.1, Nemotron 3 Super, Laguna XS 2.1) with the same open brief plus a dark-mode requirement. Cohere's North Mini Code failed both attempts — it wrote its output to `/tmp/mockup.html` instead of its task directory both times, a path mistake rather than a design failure (logged in Ringer's MODEL-NOTES for future runs). The other 5 passed.
- Posted all 5 dark-mode results to the same Gate A review artifact. Hy3's dark variant looks like the strongest result across all three rounds (ember-accent presence line, in-character household thread, non-generic). Nemotron 3 Ultra is strong but has a privacy-labeling bug in its shared living-room moment. Laguna M.1 is solid and simpler. Nemotron 3 Super and Laguna XS 2.1 both drifted back toward generic dark-dashboard patterns. Notably, 3 of the 5 independently converged on a similar warm-ember/amber-on-near-black language.
- Awaiting Marc's direction pick before any further work proceeds.

### Gate A — APPROVED (2026-07-15)

- Marc's decision: a hybrid direction. Personal surfaces (mobile/tablet/desktop) use Claude's own "Kept Light" entry — warm bone/graphite palette, an organic "light pool" presence motif, a "windowsill" desktop layout. Shared surfaces (kitchen/living room, any ambient/open display) use Tencent Hy3's dark variant — near-black with a warm ember accent and the "quiet line" presence motif (a thin horizontal line with a traveling dot).
- Both winners avoided the round-1 cliché trap and read as genuinely distinctive rather than generic-AI-product default. This is the direction the token foundation and primitive layer should be built from.
- Deferred idea, explicitly out of scope for this story: personal AI assistant avatars (Tamagotchi-style, unique per user, not a fixed set of choices), plus room/voice-based access falling back to a generic "house avatar." This conflicts with the voice/multimodal exclusion in Dev Notes — noted for a future epic to explicitly resolve, not to be implemented here. Recorded in memory for continuity across sessions.

### Gate A — round 4 (light mode head-to-head, raw results, not yet reviewed by Marc)

- Marc asked for one more round: light mode only from Hy3 and Nemotron 3 Ultra (round 3's two standouts), explicitly not required to follow the dark direction — plus one entry from Claude directly ("one from each of you").
- Hy3 (light) extended its own "quiet line" presence idea from the dark round into a cooler, sage-tinted light palette rather than color-inverting it — kept its own throughline while genuinely adapting to light mode.
- Nemotron 3 Ultra (light) had good typographic instincts but shipped with real layout bugs: an uncontained/off-center mobile card leaving a large dead void, and a stray vertical divider line bisecting the desktop moment.
- Claude's own entry ("Kept Light"): warm bone/graphite palette avoiding the cream+terracotta cliché, an organic soft-edged "light pool" presence motif (sunlight pooling on a counter, drifting almost imperceptibly) instead of another circle/orb/line, and a "windowsill" desktop layout (a narrow column of small ambient household notes) instead of a sidebar-nav.
- Awaiting Marc's direction pick before any further work proceeds.

### Governed token foundation (built from the approved direction)

- Built a four-layer token system (primitive → semantic → component → surface) under `apps/web/src/design-system/tokens/`, encoding both approved palettes verbatim from their Gate-A source: Claude's "Kept Light" (bone/graphite/clay/moss) and Hy3's "ember at midnight" (charcoal/parchment/ember/sage). Theme selection rides on the surface shell's existing `data-privacy` attribute (personal → light, household-shared → dark) rather than introducing a separate toggle, so the visual language and the privacy architecture can't drift out of sync.
- Retokenized `styles.css` in place (same selectors/classes the existing 22 web tests and 22 browser cases depend on — App.tsx/registry.tsx structure is unchanged apart from the layout adapter below); zero raw visual literals remain outside the token layer, enforced by a repository-owned audit (`token-audit.ts` + `token-audit.test.ts`), Stylelint (`color-no-hex`, `function-disallowed-list`), and an ESLint `no-restricted-syntax` rule banning JSX `style` props everywhere except the one audited file. Every allowed raw value (0, 100%, currentColor, sr-only clip rect, etc.) is a named, documented entry in `allowlist.ts` — there is no inline-disable escape hatch.
- Pulled forward the minimal audited layout-style adapter (`surfaces/layoutStyleAdapter.tsx`) from the next task, since the new ESLint rule's file-scoped exception is meaningless without it: it's the only place allowed to set inline styles, and only for six declared layout custom properties (grid columns/gap/column-start/column-span/row-start/row-span), never general visual styles.
- All four validation layers wired into `apps/web/package.json`'s `lint` script (`tsc --noEmit && eslint . && stylelint ... && vitest run src/design-system`), which flows into `mise run lint` → `make lint` unchanged.
- **Tooling finding:** `typescript-eslint` (current: 8.64) caps its `typescript` peer range below 6.1 and crashes at import time against this project's pinned TypeScript 7.0.2 — a real ecosystem gap, not a config mistake (confirmed via `npm view typescript-eslint peerDependencies`). Used `@babel/eslint-parser` + `@babel/preset-typescript` instead: syntax-only parsing with no dependency on the `typescript` package's compiler API, sufficient since the one active rule is a pure AST check needing no type information. Revisit if typescript-eslint ships TS7 support.
- **Real bug found by the axe accessibility test, not a test artifact:** `:root`/`body` originally set `color`/`font-family` via `var(--kw-color-text-primary)`/`var(--kw-font-body)`. Since `body` sits above the `data-privacy`-scoped `<main>` shell, those regular CSS properties locked in the *personal*-theme resolved value at body's own position in the tree; descendants then inherited that already-resolved computed color rather than re-reading the custom property fresh at the shell boundary — so household-shared surfaces rendered light-theme ink text on a dark-theme background (contrast ratio 1.17, caught by `reference shared fixture ... contrast` axe test). Fixed by re-declaring `color`/`font-family`/`background` on `.shell` itself, the element that actually carries `data-privacy`. Custom properties don't have this problem (they do re-resolve per descendant); only regular properties assigned via `var()` do.
- Verified end-to-end: `make lint`, `make test` (45 backend + 32 web), `make build`, and the full Playwright suite (21/22 passing, 1 intentional viewport-specific skip, same as Story 1.5's baseline) all green.

### File List

- `apps/web/package.json` — added eslint/stylelint/postcss/babel/@types-node devDependencies; `lint` script now runs typecheck + eslint + stylelint + token-audit tests.
- `apps/web/tsconfig.json` — added `"node"` to `types` (needed for the token-audit test's fs/path/url imports).
- `apps/web/eslint.config.js` — new. Babel-parser-based flat config; bans JSX `style` props outside the layout adapter.
- `apps/web/stylelint.config.js` — new. Narrow config: `color-no-hex` + `function-disallowed-list`, with an override for the tokens directory.
- `apps/web/src/design-system/tokens/primitive.css` — new. Raw palette/type/spacing/radius/motion primitives for both approved directions.
- `apps/web/src/design-system/tokens/semantic.css` — new. Theme-switched (by `data-privacy`) semantic tokens; reduced-motion and forced-colors overrides.
- `apps/web/src/design-system/tokens/component.css` — new. Presence-motif shape tokens (light-pool blob vs. quiet-line) and card-frame/composer aliases.
- `apps/web/src/design-system/tokens/surface.css` — new. Per-surface-class density/scale overrides for all five surfaces.
- `apps/web/src/design-system/tokens/index.css` — new. Single import entry point, layer order enforced.
- `apps/web/src/design-system/tokens/tokens.ts` — new. Documented registry of every legal `--kw-*` custom property.
- `apps/web/src/design-system/tokens/allowlist.ts` — new. Named allowlist of permitted raw structural values, the layout adapter's path, and its declared custom-property names.
- `apps/web/src/design-system/token-audit.ts` — new. Repository-owned audit: flags raw colors/lengths outside the token layer, primitive-token misuse outside `tokens/`, and undeclared `var()` references.
- `apps/web/src/design-system/token-audit.test.ts` — new. Negative fixtures for representative forbidden values plus a real-repository scan asserting zero violations.
- `apps/web/src/surfaces/layoutStyleAdapter.tsx` — new. The one audited file allowed to set inline styles (six declared layout custom properties only).
- `apps/web/src/styles.css` — retokenized in place; no raw visual literals remain; fixed the color/font-family inheritance bug at `.shell`.
- `apps/web/src/App.tsx` — grid container/instance divs replaced with `LayoutGrid`/`LayoutItem` from the audited adapter; no other structural change.
- `apps/web/src/cards/registry.test.tsx` — updated the accessibility-guarantee assertion to check the token system (where those guarantees now actually live) instead of a hardcoded `48px`/`forced-colors` string match in one file.
- `pnpm-lock.yaml` — updated for new devDependencies.

## Change Log

- 2026-07-15: Approved course correction applied; Story 1.6 created and set ready for development.
- 2026-07-15: Gate A approved — hybrid direction: Claude's "Kept Light" for personal surfaces, Tencent Hy3's dark "quiet line" for shared surfaces. Proceeding to the governed token foundation.
- 2026-07-15: Governed token foundation complete — four-layer token system, Stylelint/ESLint/token-audit enforcement wired into `make lint`, layout-style adapter pulled forward, and a real dark-surface text-contrast inheritance bug found and fixed. `make lint`/`make test`/`make build`/browser suite all green.
