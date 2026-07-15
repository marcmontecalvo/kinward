---
title: "Sprint Change Proposal: Exceptional UI Foundation"
status: approved
date: 2026-07-15
approvedBy: Marc
approvedAt: 2026-07-15
changeScope: moderate
reviewMode: incremental-visual
blocks:
  - Epic 2 implementation
---

# Sprint Change Proposal: Exceptional UI Foundation

## 1. Issue Summary

Epic 1 proved the card registry, layout resolver, privacy boundaries, five surface contexts, accessibility baseline, and deployment foundation. During visual review after Story 1.5, the product owner rejected the current UI elements and visual result as unsuitable for Kinward's long-term foundation.

The current frontend is deliberately small and replaceable, but presentation decisions remain distributed across global CSS and JSX: raw visual values, hard-coded visible presentation, a minimal shared card shell, no complete design-token taxonomy, no reusable primitive library, and insufficiently intentional differentiation among personal and shared surfaces.

This is both:

- a stakeholder requirement clarified by inspecting the implemented product; and
- an incomplete realization of the existing requirement for a calm, warm, restrained, polished visual foundation.

The triggering work is Epic 1 Stories 1.3–1.5. Their architectural contracts remain valid; their visual implementation is scaffolding rather than an accepted product foundation.

### Product-owner quality statement

Kinward's interface is the base of the household experience. It must feel magical, wonderful, coherent, trustworthy, and intentionally adapted to its surface. A merely functional or generic dashboard treatment is not acceptable.

## 2. Impact Analysis

### Epic impact

**Epic 1:** Add a final Story 1.6 before Epic 1 is accepted. Preserve Stories 1.1–1.5 and their backend, privacy, registry, layout, schema, and evidence contracts. Story 1.6 replaces and strengthens their presentation layer.

**Epic 2:** Do not begin implementation until Story 1.6 passes its final visual approval gate. Stories 2.1, 2.2, 2.4, 2.5, and 2.6 will consume the new shells, primitives, card renderers, status language, and composer rather than coupling live functionality to the rejected scaffolding.

**Epics 3–10:** No product capability becomes obsolete. All future web UI must consume the token and primitive system. Epic 8's Kinward Control remains a separate shell and navigation family but may share foundation tokens and primitives. Epic 10 generated views continue to use registered components only.

No new product epic is required and no completed backend work should be rolled back.

### Artifact impact

- **Product brief:** no product-goal change required; polished defaults and adaptive surfaces already support this correction.
- **PRD:** clarify the Milestone A frontend gate so architectural validity alone is insufficient; the accepted visual foundation must pass product-owner visual review and automated token enforcement.
- **UX specification:** expand the Visual Foundation into an implementable design-language, token, primitive, surface-differentiation, and visual-review contract.
- **Architecture:** extend AD-22 with frontend presentation ownership and enforceable token boundaries. No backend, API, privacy, or persistence architecture changes.
- **Epics:** add Story 1.6 and make it a prerequisite of Story 2.1.
- **Testing/CI:** add token-compliance linting and visual-regression evidence to the existing lint, browser, accessibility, and public-safety gates.

### Technical impact

Primary impact is confined to `apps/web`, its tests, and frontend tooling. Existing schemas, policy filtering, card registry identity, layout resolution precedence, backend APIs, and persistence remain authoritative.

Current UI areas in scope include the five assistant surfaces and setup. Future Kinward Control UI must adopt the same enforcement when introduced.

## 3. Recommended Approach

### Selected path: direct adjustment

Add Story 1.6, **Establish the Exceptional Kinward Visual Foundation**, after Story 1.5 and before Epic 2.

Do not roll back the card/layout/privacy foundation. Replace only the presentation architecture and visual implementation. This keeps the valuable Epic 1 contracts while preventing Epic 2 functionality from hardening rejected markup and styling.

### Effort and risk

- Estimated implementation: **10–20 focused agent-hours**, normally one or two working days including visual feedback.
- Technical risk: low to moderate.
- Product/aesthetic risk: moderate, controlled through early rendered checkpoints.
- Backend/privacy regression risk: low, controlled through the existing full suite.
- Expected result with visual checkpoints: approximately 75% great first accepted direction, 23% requiring ordinary visual revision, and 2% requiring major architectural rework.

### Review contract

The product owner reviews **visual output only**. The implementation agent owns source review, token compliance, accessibility, responsiveness, tests, and technical correctness.

```text
Direction gallery
      ↓ visual approval
Foundation slice: 3 surfaces × representative cards
      ↓ visual approval
Complete five-surface experience
      ↓ visual approval
Polish and edge-state gallery
      ↓ final visual approval
Epic 2 unblocked
```

Visual reviews use rendered browser views, comparison contact sheets, or directly inspectable local previews. They do not ask the product owner to review code, lint reports, implementation notes, or completion checklists.

## 4. Detailed Change Proposals

### 4.1 Epics — add Story 1.6

**Location:** after Story 1.5 and before Epic 2.

**OLD:**

> Epic 1 ends when the five-surface mock-backed foundation passes functional, privacy, layout, responsive, accessibility, and evidence checks.

**NEW:**

> Epic 1 ends only after Story 1.6 establishes and visually approves the durable Kinward design system and all five surface experiences. Epic 2 cannot begin implementation before this gate passes.

#### Story 1.6: Establish the Exceptional Kinward Visual Foundation

As a household member,
I want every Kinward surface to feel beautiful, coherent, personal, and purpose-built,
So that the interface can sustain trust and delight as the household's daily assistant foundation.

##### Acceptance criteria

1. **Design language and tokens**
   - One documented token system owns color, typography, spacing, sizing, radii, borders, elevation, opacity, layering, motion, focus, targets, and supported responsive thresholds.
   - Primitive tokens are separated from semantic and surface-context tokens.
   - Assistant identity and surface modes may vary semantic tokens without bypassing accessibility or privacy semantics.
   - No application component or ordinary stylesheet introduces an unapproved raw visual value.

2. **Enforcement**
   - CI lint fails on raw colors, restricted numeric presentation values, unapproved arbitrary styles, or direct use of primitive values where a semantic token is required.
   - A small documented allowlist covers values that are structurally necessary, such as zero, inheritance, current color, percentages, screen-reader clipping, and data-driven layout coordinates.
   - Inline visual styling is forbidden outside an audited declarative-layout adapter.
   - New primitives, tokens, exceptions, and suppressions require an explicit inspectable declaration; silent lint bypasses fail CI.

3. **Reusable primitives**
   - The UI is composed from a small intentional primitive layer covering surface, layout, typography, panel/card frame, actions, status, navigation, composer, lists, assistant presence, privacy cues, and empty/unavailable states.
   - Primitives own presentation and accessibility mechanics; feature and card code owns semantics and intents.
   - Setup is migrated to the same applicable tokens and primitives.

4. **Thin registered-card renderers**
   - Each of the eight registered card types has one semantic renderer contract and remains policy-free.
   - Renderers compose primitives and contain no independent visual constants.
   - Every card receives an intentional treatment for personal mobile, personal tablet, personal desktop, shared kitchen, and shared living room.
   - The five treatments are visibly and structurally adapted, not recolored copies, while retaining shared semantics, state truthfulness, intent wiring, and accessibility.
   - Structural variants are introduced only where interaction capability, density, privacy, room, or viewing distance justifies them; forty unrelated renderer implementations are forbidden.

5. **Personal shells**
   - Mobile provides assistant presence, one dominant Now item, quiet briefing, Continue, persistent input, and minimal bottom navigation without reading as a dashboard grid.
   - Tablet supports touch-and-keyboard planning with a deliberate multi-column workspace.
   - Desktop provides persistent navigation, an adaptive canvas, topic/workspace continuity, and persistent input without being enlarged mobile.

6. **Shared-display shells**
   - Kitchen is glanceable, active, task-proximate, touch/voice compatible, and readable at room distance.
   - Living room is ambient, calm, distance-first, and clearly distinct from kitchen and personal surfaces.
   - Both remain household-safe by default, minimize navigation depth, and preserve unmistakable privacy/session cues.

7. **Visual quality**
   - The result expresses a coherent Kinward visual language: calm, warm, intelligent, personal, restrained, trustworthy, and quietly magical rather than generic, decorative, or dashboard-like.
   - Cards act as presentation primitives and do not become the product metaphor.
   - Assistant presence avoids a default humanoid avatar and uses purposeful, interruptible, reduced-motion-aware signals.
   - Available, empty, loading, degraded, unavailable, stale, error, approval, acting, submitted, unknown, completed, failed, and cancelled states remain visually and semantically distinguishable without color alone.

8. **Visual approval gates**
   - Gate A presents a compact visual-direction gallery rather than a completed application.
   - Gate B presents representative Now, Briefing, Approval, Assistant Input, and Presence experiences on personal mobile, personal desktop, and shared living room.
   - Gate C presents the complete eight-card set across all five surfaces.
   - Gate D presents final responsive, interaction, empty/degraded/error, text-scaling, reduced-motion, and forced-color evidence.
   - The product owner approves rendered visuals at each gate. Code review is not requested from the product owner.

9. **Regression and completion**
   - Existing card schema, layout validation, privacy filtering, forbidden-field absence, invalid-layout fallback, and surface-context tests remain green.
   - Automated checks cover token enforcement, primitive boundaries, responsive behavior, keyboard interaction, WCAG 2.2 AA, non-color states, 100%/200% text scale, touch targets, and shared-display distance requirements.
   - Stable visual-regression references cover all five default shells and a bounded representative state matrix; tests do not require an unmaintainable screenshot of every theoretical combination.
   - The public-repository safety review confirms all visual fixtures are obviously fictional and contain no household or deployment data.

### 4.2 UX specification — expand Visual Foundation

**OLD:**

> Kinward should feel calm, intelligent, personal, modern, restrained, and warm without becoming decorative.

**NEW:** retain that statement and add:

- a named design-token taxonomy and ownership rule;
- the reusable primitive inventory and semantic/presentation boundary;
- five explicit surface art-direction profiles;
- the rule that differentiation must follow context rather than arbitrary skins;
- representative anatomy for cards, navigation, composer, assistant presence, status, and privacy cues;
- the four visual approval gates from Story 1.6;
- visual anti-patterns: generic glass dashboard, undifferentiated card grid, enlarged-mobile desktop, wall-mounted personal dashboard, novelty motion, decorative status ambiguity, and one-off styling outside primitives.

Rationale: the current emotional adjectives are correct but insufficiently executable or reviewable.

### 4.3 Architecture — extend AD-22

**OLD:** registry-driven policy-filtered frontend with registered cards, validated layouts, and separate Assistant Experience/Kinward Control shells.

**NEW:** retain all existing AD-22 rules and add:

- token modules are the only source of visual constants;
- semantic primitives are the only ordinary application presentation boundary;
- surface variants consume explicit `SurfaceContext` rather than viewport guesses alone;
- feature/card renderers may choose semantic structure and intent but not independent visual values;
- declarative grid coordinates flow through one audited adapter;
- automated enforcement rejects raw values and unapproved bypasses;
- Kinward Control may share tokens/primitives but must use a separate shell, navigation family, and density profile.

Rationale: this makes the design foundation an enforceable architecture invariant instead of a styling convention.

### 4.4 PRD — strengthen the frontend-foundation gate

**OLD:** Milestone A validates surface, privacy, card, and layout architecture through automated or inspectable checks.

**NEW:** Milestone A additionally requires the Story 1.6 token, primitive, anti-hardcoding, visual-regression, and product-owner rendered-visual approval gates. Functional architecture alone cannot graduate rejected presentation into the product foundation.

This does not expand committed product capability or enable any deferred layout editor, voice, multimodal, or native scope.

## 5. Implementation Handoff

### Scope classification

**Moderate.** The product scope is unchanged, but the frontend foundation, Epic 1 exit gate, and Epic 2 dependency must be reorganized.

### Responsibilities

**Product owner**

- Reviews rendered visuals only at Gates A–D.
- Gives directional feedback in ordinary visual/product language.
- Approves or rejects each visual gate.

**Implementation agent**

- Produces visual alternatives and inspectable previews.
- Owns tokens, primitives, renderer/shell implementation, lint rules, tests, migration, documentation, and validation.
- Translates visual feedback into implementation without requesting source review.
- Does not declare Story 1.6 complete without final rendered-visual approval.

### Sequencing

1. Approve this Sprint Change Proposal.
2. Apply the approved edits to UX, architecture, PRD gate language, and epics.
3. Create the implementation-ready Story 1.6 artifact.
4. Run visual Gate A.
5. Implement and review Gates B–D incrementally.
6. Run full validation and public-safety review.
7. Mark Story 1.6 ready for review and unblock Epic 2.

### Definition of success

Success is not merely zero lint violations. It requires all of the following:

- the product owner considers the rendered foundation excellent enough to build the household experience upon;
- all current UI presentation is governed by tokens and reusable primitives;
- automated guards make raw visual-value regression difficult and visible;
- all five surfaces feel related but purpose-built;
- all eight card semantics remain thin, registered, safe, and truthful;
- existing privacy, layout, responsive, accessibility, and deployment gates remain green.

## 6. Checklist Disposition

| Checklist area | Status | Finding |
| --- | --- | --- |
| Trigger and evidence | Done | Post-Story 1.5 rendered UI was explicitly rejected by the product owner. |
| Current epic impact | Action needed | Add Story 1.6; do not accept Epic 1 visual foundation yet. |
| Future epic impact | Done | Epic 2 is blocked; later UI consumes the system without capability changes. |
| PRD impact | Action needed | Strengthen Milestone A visual and enforcement gate. |
| Architecture impact | Action needed | Extend AD-22 presentation ownership and enforcement. |
| UX impact | Action needed | Make visual language executable and visually reviewable. |
| Other artifacts | Action needed | Add CI lint and bounded visual-regression evidence. |
| Direct adjustment | Viable | Preserves valuable foundation and has bounded frontend scope. |
| Rollback | Not recommended | No architectural rollback is needed. |
| MVP review | Not required | Product capability and release scope remain unchanged. |
| Handoff | Ready after approval | Implementation agent executes; product owner reviews visuals only. |

## 7. Approval and Handoff Record

Marc approved this proposal on 2026-07-15. The change is routed to the implementation agent. The implementation agent owns all technical execution and verification; Marc reviews rendered visuals only at Gates A–D. Epic 2 remains blocked until Gate D is explicitly approved.
