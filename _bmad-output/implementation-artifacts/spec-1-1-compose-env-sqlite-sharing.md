---
title: 'Repair Story 1.1 Compose SQLite sharing'
type: 'bugfix'
created: '2026-07-14'
status: 'done'
review_loop_iteration: 0
baseline_commit: '2ec665967d0c26601d63e18d113d6f4d7f99d85e'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/1-1-start-a-healthy-core-deployment.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Copying the repository's `.env.example` causes the migration, API, and worker containers to use separate container-local SQLite files. The migration succeeds, but the worker cannot find the migrated schema and continually restarts.

**Approach:** Make the example configuration use the shared `/data/kinward.db` volume path and extend the Compose smoke test to prove that an environment file copied from `.env.example` reaches a healthy core deployment.

## Boundaries & Constraints

**Always:** Preserve SQLite as the default, keep all backend roles on the same named volume, use synthetic configuration only, retain the migration-first startup contract, and preserve the clean-checkout no-`.env` path.

**Ask First:** Any change to the database engine, volume topology, service inventory, migration identity, or provider defaults.

**Never:** Run migrations from API or worker startup, weaken schema readiness, rely only on an environment override inside the smoke script, expose secrets, or discard existing uncommitted work.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Clean checkout | No `.env` file | Compose uses `/data/kinward.db`; migrate, worker, API, and web become ready | Smoke test fails with the service that did not become healthy |
| Documented environment setup | `.env` copied verbatim from `.env.example` | All backend containers resolve the shared `/data/kinward.db` path and become healthy | Regression test fails if the copied example overrides Compose with a private path |
| Migration failure | Injected non-zero migration command | API and worker remain gated | Smoke test verifies the migration exit and rejects running dependents |

</frozen-after-approval>

## Code Map

- `.env.example` -- Documented environment template currently overriding Compose with a container-private relative SQLite path.
- `compose.yaml` -- Defines the correct shared `/data/kinward.db` default and named volume mount.
- `scripts/compose-smoke.sh` -- Deployment regression suite currently suppressing `.env` and forcing the correct database URL.
- `README.md` -- Documents both copying `.env.example` for development and the default Compose startup contract.

## Tasks & Acceptance

**Execution:**
- [x] `.env.example` -- change the SQLite URL to `sqlite+aiosqlite:////data/kinward.db` so copied configuration preserves cross-container storage.
- [x] `scripts/compose-smoke.sh` -- add an isolated Compose run using a verbatim copied `.env.example`, verify healthy services and the shared migrated revision, and clean up its project/volume.
- [x] `README.md` and Story 1.1 record -- clarify the shared path and record the regression repair/evidence if needed.
- [x] Entire worktree -- run required quality and deployment gates and leave the validated worktree ready for the separately authorized publish workflow.

**Acceptance Criteria:**
- Given `.env.example` is copied to an environment file, when the default Compose topology starts, then migration, worker, API, and web become healthy using one persisted SQLite database at `/data/kinward.db`.
- Given no environment file, when the documented default Compose command starts, then the existing clean-checkout behavior remains healthy.
- Given all relevant gates pass, when publishing, then every current tracked and untracked worktree change is included in one commit and pushed to the configured remote without exposing private data.

## Spec Change Log

## Verification

**Commands:**
- `make lint` -- expected: all Python and TypeScript lint checks pass.
- `make typecheck` -- expected: all configured static type checks pass.
- `make test` -- expected: all automated tests pass.
- `make build` -- expected: backend and web production builds pass.
- `./scripts/compose-smoke.sh` -- expected: clean/default, copied-example, failure-gating, migration, health, restart, and cleanup checks pass.
- repository safety scan and `git diff --check` -- expected: no prohibited private values, secrets, or whitespace errors are introduced.

## Suggested Review Order

**Deployment topology**

- Start with the shared database and migration-gated service topology.
  [`compose.yaml:1`](../../compose.yaml#L1)

- Confirm the copied example preserves the same shared SQLite path.
  [`.env.example:1`](../../.env.example#L1)

**Health and worker contract**

- Review independent core health and optional-capability state assembly.
  [`health.py:84`](../../services/kinward/src/kinward/health.py#L84)

- Review durable heartbeat readiness without worker-owned migration behavior.
  [`worker.py:47`](../../services/kinward/src/kinward/worker.py#L47)

- Verify the single pre-freeze migration origin creates readiness tables.
  [`001_initial_single_household.py:107`](../../services/kinward/migrations/versions/001_initial_single_household.py#L107)

**Production web path**

- Review the same-origin ingress and bounded API proxy routes.
  [`nginx.conf:1`](../../apps/web/nginx.conf#L1)

- Review the production multi-stage web build.
  [`Dockerfile:1`](../../apps/web/Dockerfile#L1)

**Verification and reproducibility**

- Follow clean startup, failure gating, restart, and copied-example regression evidence.
  [`compose-smoke.sh:87`](../../scripts/compose-smoke.sh#L87)

- Confirm CI uses the declared Python, Node, pnpm, and frozen-lock policy.
  [`ci.yml:11`](../../.github/workflows/ci.yml#L11)

- Review operator expectations for startup, health, persistence, and shutdown.
  [`README.md:67`](../../README.md#L67)
