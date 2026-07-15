---
project_name: kinward
user_name: Marc
date: 2026-07-14
sections_completed:
  - technology_stack
existing_patterns_found: 8
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

- Node.js 24 LTS at the latest supported patch release, managed by mise.
- pnpm 11 workspaces, pinned through `packageManager` and Corepack with a committed frozen lockfile.
- React 19 at the latest patched compatible 19.x release.
- TypeScript 7 in strict mode with `noUncheckedIndexedAccess` and `exactOptionalPropertyTypes`.
- Use the current stable compatible Vite and Vitest majors, validated together with the React plugin, TypeScript, coverage tooling, and Playwright.
- Zod 4 at the latest patched compatible release.
- Python 3.14 at the latest patch release. Maintain Python 3.13 only as a tested fallback when a documented dependency incompatibility requires it.
- Use FastAPI 0.139 or newer compatible 0.x, Pydantic 2, pydantic-settings 2, SQLAlchemy 2.0, and Alembic 1 at their latest patched compatible releases.
- Use pytest 9, Ruff 0.15, mypy 2, and optional Pyright validation.
- Native SQLAlchemy 2 typed mappings are required. Use the legacy SQLAlchemy mypy plugin only for a documented typing gap.
- uv owns Python environments, dependency resolution, and locking.
- pnpm owns JavaScript workspaces and locking.
- mise owns runtimes and task execution.
- `make` may provide stable convenience entry points that delegate to mise.
- SQLite is the required default persistence engine.
- PostgreSQL 18 is an optional adapter and must not be advertised until the shared persistence, transaction, migration, backup, and concurrency contract suite passes.
- Docker Compose defines the single-household deployment topology.

### Dependency Currency and Compatibility

- Kinward uses supported, currently patched dependency releases.
- Apply security patches and compatible patch or minor updates promptly through automated dependency updates and the normal validation pipeline. These updates do not require a separate architecture decision.
- Evaluate new major releases when they become stable. Adopt them by default during greenfield or pre-release development unless automated compatibility tests demonstrate a concrete regression, unsupported dependency, data-migration risk, or deployment incompatibility.
- Every temporary version hold must record the specific blocker, affected validation, responsible owner, review date, and upgrade exit criteria.
- Architecture decisions govern behavioral contracts, security boundaries, persistence semantics, and externally observable compatibility. They do not permanently freeze implementation-library versions.
- Production builds require committed lockfiles, immutable container references or digests, and reproducible installation.
- Continuously check direct and transitive dependencies for known vulnerabilities, unsupported runtimes, malicious-package indicators, deprecated releases, and newer patched versions.
- Core principle: automatically consume safe updates, rigorously validate major changes, and require justification for staying old, not for staying current.
- This policy supersedes older fixed implementation-version tables in planning artifacts. Reconcile those tables and repository manifests before completing Story 1.1.

## Critical Implementation Rules

_Documented after discovery phase_
