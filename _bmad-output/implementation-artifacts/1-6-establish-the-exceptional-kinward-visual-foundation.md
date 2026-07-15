---
baseline_commit: 2492dc8f6b337c83e51932732c174d30e705db07
status: superseded
superseded_on: 2026-07-15
superseded_by: _bmad-output/planning-artifacts/ha-native-pivot-2026-07-15.md
replacement_story: _bmad-output/planning-artifacts/epics.md#story-16-ship-the-first-core-card-kinward-dashboard
---

# Story 1.6: Establish the Exceptional Kinward Visual Foundation

## Status

**Cancelled as obsolete during the Home Assistant native pivot.**

Kinward no longer owns a standalone five-surface visual system. Home Assistant 2026.7.2 is the committed application shell for dashboards, responsive rendering, mobile access, and Assist voice interaction.

## Salvage disposition

The following completed work may be retained only after explicit review for independent value:

- backend privacy and policy filtering;
- accessible setup behavior unrelated to standalone rendering;
- general lint/test improvements that remain useful outside `apps/web`;
- public-safe fixtures and security tests that still exercise backend boundaries.

The following are no longer product requirements:

- Kinward design tokens and primitive library;
- five Kinward-owned surface shells;
- Kinward card renderers and layout resolver;
- visual approval Gates A–D;
- standalone responsive and PWA acceptance gates;
- Story 1.6 blocking Epic 2.

Do not continue incomplete subtasks from the former story. New implementation follows the revised HA-native `epics.md`, beginning with the pinned HA development profile, custom integration, safe entity set, core-card dashboard, and household trial.

## Historical note

This file is retained to prevent completed or partially completed frontend work from being mistaken for active requirements and to preserve the decision trail. Git history contains the original detailed story.
