# Data Retention and Record Lifecycle

Every durable database record class has an explicit, documented retention
disposition. The source of truth is
`services/kinward/src/kinward/domain/lifecycle.py`'s `BOOTSTRAP_RECORD_LIFECYCLES`
table; this document is its human-readable projection, not a second copy to keep
in sync by hand.

`TABLE_LIFECYCLE_KEYS` in the same module maps each persisted SQLAlchemy table
(`kinward.persistence.models`) to the lifecycle key(s) that classify it.
`tests/test_lifecycle.py` enforces that every table in `Base.metadata` is either
mapped here or listed as a tracked gap below - a new persisted table with no
lifecycle decision fails the test suite rather than shipping unclassified.

## Classified record classes

| Record class | Table | Classification | Backup eligible | Import eligible | Restore disposition | Deletion |
|---|---|---|---|---|---|---|
| household | `households` | household-shared | yes | yes | restore | delete with deployment reset |
| person | `people` (adult) | private-person | yes | yes | quarantine | delete with profile |
| child | `people` (child) | private-child | yes | yes | quarantine | delete with profile |
| pet | `pets` | household-shared | yes | yes | quarantine | delete with pet profile |
| relationship | `relationships` | household-shared | yes | yes | quarantine | delete with referenced profile |
| primary_assistant | `assistants` (owned) | private-person | yes | no | quarantine | delete with owner |
| fallback_assistant | `assistants` (household) | household-shared | yes | no | restore | delete with household |
| setup_capability | `setup_capabilities` | system-operational | no | no | regenerate | delete after terminal setup/reset |
| bootstrap_attempt | `bootstrap_attempts` | system-operational | yes | no | restore | retain with household audit history |
| activity | `activity` | system-operational | yes | no | restore | retain under operational policy |
| outbox | `outbox_messages` | system-operational | yes | no | restore | delete after delivery retention |
| surface_layout | `surface_layouts` | household-shared | yes | yes | quarantine | delete with surface assignment |
| layout_activation_attempt | `layout_activation_attempts` | system-operational | yes | no | restore | retain with layout audit history |

Field meanings:

- **Classification** - the privacy tier: `private-person`/`private-child` records
  belong to one person; `household-shared` records are visible household-wide;
  `system-operational` records carry no personal content.
- **Backup eligible** - included in a household backup at all.
- **Import eligible** - may be reintroduced by a restore/import into an
  existing, already-bootstrapped household (as opposed to only ever being
  produced fresh by that household's own bootstrap/setup flow).
- **Restore disposition** - what happens to the record when a backup is
  restored: `restore` (brought back as-is), `quarantine` (brought back but held
  for review before it takes effect - see AD-12), or `regenerate` (never
  restored verbatim; the system produces a fresh instance instead).
- **Deletion** - what removes the record and when.

`person` vs. `child` and `primary_assistant` vs. `fallback_assistant` are the
same table distinguished by a row field (`profile_kind`, `kind`), not by
table - see `TABLE_LIFECYCLE_KEYS`.

## Tracked gaps

These persisted tables have no lifecycle entry yet. Each is intentional and
reasoned, not silent drift - see `UNCLASSIFIED_TABLES` in `lifecycle.py`:

| Table | Why it's unclassified |
|---|---|
| `approvals` | Epic 6 approval/meaningful-action machinery - schema exists, zero call sites yet. Classify once that machinery lands. |
| `memory_index` | Pivot-era addition; retention not yet decided. |
| `worker_heartbeats` | Pivot-era addition; retention not yet decided. |
| `integration_tokens` | Pivot-era addition; retention not yet decided. |
| `topics` | Pivot-era addition; retention not yet decided. |
| `topic_turns` | Pivot-era addition; retention not yet decided. |

See `_bmad-output/planning-artifacts/epics.md` Story 9.4 for the broader
context: blocker-preservation checks for this taxonomy are blocked on Epic 6's
approval machinery, which has no call sites yet. Backup/restore-survival
verification is deferred to v2 alongside Stories 9.1-9.3 (backup/restore/import)
themselves, which have no implementation and are out of v1 scope. This
document and its enforcement test are the piece of Story 9.4 that doesn't
depend on either.
