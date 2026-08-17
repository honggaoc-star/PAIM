# PAIM Increment 1 Technology Foundation Decision v0.1

## 1. Decision status and scope

**Status:** Proposed for independent review under PAIM Issue #11.

**Decision scope:** This artifact selects the minimum technology and engineering foundation needed for a later, separately authorized Increment 1A implementation of the PAIM common record-history and integrity kernel. It is design-only. It does not authorize or create application code, domain schemas, migrations, tests, APIs, user interfaces, infrastructure, or runtime bootstrap files.

The governing clean-main baseline is commit `df700df8529326846f12798d2bd195541b543cd2`.

The decision applies only to Increment 1. It does not select technology for later user interfaces, external integrations, distributed processing, production deployment, search, attachments, reporting, or analytical services.

## 2. Governing constraints

This decision is subordinate to:

- `AGENTS.md`;
- `PAIM_PLATFORM_ARCHITECTURE_v0.1.md`, especially §§6–7, 13, 18, 19, 22, and 23;
- `PAIM_IMPLEMENTATION_SEQUENCE_AND_P1_GATES_v0.1.md`, especially §§4.2, 8, 9, and 11; and
- `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, especially §§2–3, 8–10, and 12.

The selected foundation must preserve, rather than reinterpret:

- separate stable Record IDs and immutable Record Version IDs;
- mutable drafts only inside the permitted draft boundary and immutable finalized content;
- status events distinct from content versions;
- effective time distinct from recorded time, including `effective_at` and optional `known_at` reads;
- exact predecessor, correction, amendment, supersession, and withdrawal history;
- current selection returning exactly one eligible version, explicit absence, or explicit incompatible-current conflict;
- stale-precondition rejection and idempotent semantic writes;
- all-or-nothing semantic commit bundles;
- authenticated principal attribution distinct from PAIM actor attribution;
- authoritative history distinct from rebuildable projections and technical telemetry; and
- analytical independence between Value and Risk.

No storage convention, framework default, identifier order, row order, or “latest” query may become an undeclared semantic rule. Missing, conflicting, or deferred semantics remain explicit and non-permissive.

## 3. Decision criteria

Choices are evaluated in this order:

1. **Contract fidelity:** the mechanism must make immutable versions, append-preserving events, exact links, dual time, conflicts, and point-in-time reads directly testable.
2. **Atomicity:** a semantic write and its version, relationship, status, idempotency, and audit facts must commit or roll back together.
3. **Determinism:** identity, time, serialization, selection, and conflict behavior must not depend on process locale, database row order, or wall-clock timing in tests.
4. **Smallest adequate topology:** Increment 1A must run locally without a network service, container platform, or distributed transaction.
5. **Replaceability:** domain semantics must sit behind explicit persistence and clock/identity ports so a later database or deployment change does not rewrite the integrity contract.
6. **Cross-platform reproducibility:** supported development on Windows, Linux, and macOS with a committed environment lock.
7. **Operational legibility:** transactions, migrations, failures, idempotency outcomes, and audit attribution must be inspectable.
8. **P1 neutrality:** the foundation must not encode record-family cardinality, ownership, precedence, ranking, or workflow semantics reserved for later decisions.

Performance and horizontal scaling are secondary to correctness in Increment 1. Any optimization that obscures the authoritative semantics is rejected.

## 4. Alternatives considered

### 4.1 Language and runtime

| Alternative | Advantages | Reasons not selected for Increment 1 |
|---|---|---|
| CPython 3.14 | Concise domain-neutral kernel, mature SQL/testing ecosystem, timezone-aware standard types, and standard-library UUIDv7 | Selected; static discipline must be added through typing and tests. |
| TypeScript on Node.js | Strong developer tooling and useful type system | Transpilation/module/runtime choices and an asynchronous database layer add moving parts without benefiting a local integrity kernel. |
| C# on current .NET LTS | Strong static types, transaction support, and mature tooling | A larger SDK/project surface is not justified for the first local library and contract-test slice. |
| Java or Kotlin on a current LTS JVM | Strong typing, portability, and database tooling | Build/runtime weight and framework choice are disproportionate to Increment 1A. |

### 4.2 Dependency and environment management

| Alternative | Advantages | Reasons not selected |
|---|---|---|
| `uv` project with `pyproject.toml` and committed `uv.lock` | One tool for Python acquisition, dependency resolution, locking, environment synchronization, and command execution | Selected. |
| `pip` plus `venv` and requirements files | Standard-library familiarity and few concepts | Reproducible transitive locking and synchronized dev groups require additional conventions/tools. |
| Poetry or PDM | Integrated project and lock management | Adequate, but adds no needed capability over the smaller selected `uv` workflow. |
| Conda | Strong native/scientific environment management | Heavier than needed; Increment 1 has no native analytical stack. |

`uv` documents that project locking resolves dependencies into a lockfile, syncing installs from it, `--locked` fails when metadata and lock disagree, and upgrades are explicit. The later bootstrap issue must pin the exact CPython patch and `uv` tool version and commit the generated lock; this decision creates none of those files. See the official [uv locking and syncing documentation](https://docs.astral.sh/uv/concepts/projects/sync/).

### 4.3 Persistence and data access

| Alternative | Advantages | Reasons not selected for Increment 1A |
|---|---|---|
| SQLite plus SQLAlchemy 2.x Core and Alembic | Local ACID database, explicit SQL/transactions, no service, migration lineage, and a portable relational boundary | Selected. |
| PostgreSQL | Rich concurrency, constraints, temporal-query options, and production scaling | Requires an external service and operational setup before the semantic kernel needs them. It remains the leading future adapter candidate. |
| Dedicated event store | Append history is natural | Stream/version/projection infrastructure adds substantial complexity and does not remove the need for effective-time conflict queries. |
| Flat files or in-memory storage | Minimal startup cost | Cannot adequately prove durable atomic writes, concurrency preconditions, migrations, or indexed point-in-time reads. In-memory fakes remain useful only for pure tests. |
| Raw `sqlite3` throughout | Few dependencies and full SQL control | Couples the kernel to one driver and supplies no migration framework or reusable adapter contract. Driver SQL remains available behind the selected adapter when SQLite-specific transaction control is required. |
| SQLAlchemy ORM | Convenient object mapping and unit-of-work features | Identity maps and mutable entity conventions can obscure immutable-version and append-only behavior. SQLAlchemy Core keeps statements and transaction boundaries explicit. |

### 4.4 Identifiers, time, and tests

| Choice | Alternatives | Decision reason |
|---|---|---|
| UUIDv7 | UUIDv4, ULID, database integers | Standard RFC 9562 identity, application-side generation without coordination, sortable locality, and no third-party ID dependency under CPython 3.14. Semantic ordering never uses UUID order. |
| UTC integer microseconds | Database text timestamps, floating Unix time, local time, database-specific temporal types | Exact cross-platform representation at Python's native microsecond resolution; no locale, offset, or floating-point ambiguity. |
| `pytest` | `unittest`, behavior-specification frameworks | Concise assertions, fixtures, parametrization, temporary databases, and reusable adapter contract suites with little framework ceremony. |

Python 3.14 added standard-library UUID versions 6, 7, and 8; `uuid.uuid7()` follows RFC 9562. Python's aware `datetime` values and UTC singleton support an explicit UTC-only application convention. See the official [Python UUID documentation](https://docs.python.org/3.14/library/uuid.html) and [Python datetime documentation](https://docs.python.org/3.14/library/datetime.html).

### 4.5 Migration and engineering controls

| Choice | Alternatives | Decision reason |
|---|---|---|
| Alembic | Handwritten SQL runner, Flyway, Liquibase | It shares SQLAlchemy connection/metadata conventions, records an explicit revision graph, and stays inside the selected Python toolchain. Generated revisions still require human review. |
| Ruff | Black plus Flake8/isort, no formatter/linter | One fast development tool supplies deterministic formatting and a bounded lint surface with fewer overlapping configurations. |
| mypy strict checking | Pyright, runtime validation only | It is Python-native, runs locally/CI without an editor dependency, and makes port/value boundaries reviewable. Runtime validation remains authoritative. |

Handwritten SQL remains permitted inside reviewed Alembic revisions when it is clearer or safer than generated operations. A separate Java migration runtime is not justified for an embedded Increment 1A database. Ruff and mypy do not influence domain outcomes and can be replaced without migrating authoritative data.

## 5. Selected foundation

The Increment 1 foundation is:

- **Language/runtime:** CPython `3.14.x`. Increment 1 supports the Python 3.14 minor line only. At its clean-main checkpoint, the later Increment 1A bootstrap must pin the latest accepted released 3.14 patch available at that checkpoint and record the exact runtime pin with the locked environment. Subsequent patch upgrades require a bounded dependency change with the full test suite; minor-version upgrades require a new decision or amendment.
- **Project/environment manager:** `uv`, using one root `pyproject.toml`, a committed `uv.lock`, a repository-local `.venv`, and locked execution in CI/review. The later bootstrap issue pins the exact `uv` release used to create the lock.
- **Application shape:** a typed, synchronous Python package and modular monolith/library. No server or long-running process is selected.
- **Data access:** SQLAlchemy 2.x **Core**, not ORM, behind domain-neutral persistence ports. The bootstrap issue selects compatible exact versions through the lock.
- **Initial persistence adapter:** SQLite through the CPython driver, with foreign-key enforcement and explicit transactions.
- **Migration tool:** Alembic, with reviewed forward revisions. It is selected now but no migration environment or revision is created by this issue.
- **Tests:** `pytest`, with reusable parameterized hard-oracle and adapter contract suites. The official [pytest parametrization documentation](https://docs.pytest.org/en/stable/how-to/parametrize.html) supports running the same oracle over multiple inputs/adapters.
- **Static engineering controls:** Ruff for formatting/linting and mypy for strict static type checks. They are development-only controls; neither defines PAIM semantics.
- **Library style:** immutable/frozen value objects for finalized content and typed wrappers for semantically distinct identifiers. Runtime validation and database constraints remain required; Python typing is not an authorization or integrity mechanism.

Only the listed major/minor compatibility lines are architectural choices. Every exact third-party version and tool version must be resolved and committed in the Increment 1A lockfile. No unreviewed dependency upgrade is allowed during locked execution.

### 5.1 Local execution and development boundary

Increment 1A must run on a developer workstation or CI runner supporting the pinned CPython and `uv` versions on Windows, Linux, or macOS. Environment setup is a locked `uv sync`; project commands execute through `uv run --locked`. Tests use a fresh temporary SQLite database per test or isolated test scope. A developer database, if the later issue permits one, is repository-local, ignored by Git, disposable, and never an authoritative shared environment.

No container engine, database server, network listener, cloud account, message broker, identity provider, or external service is required. Configuration is limited to explicit local database location and safe test/runtime settings; secrets are not part of Increment 1A. The package exposes application services as an in-process library for tests and later adapters. It does not expose an HTTP API, CLI product surface, worker, scheduler, or UI.

## 6. Persistence and transaction model

### 6.1 Logical model

The adapter must support append-preserving storage for, at minimum:

- stable record identity;
- immutable content versions;
- status events that do not mutate version content;
- typed relationships among exact versions;
- effective intervals and recorded timestamps;
- idempotency command/outcome facts; and
- immutable audit facts.

This list is a capability contract, not a physical schema. Table names, columns, indexes, constraints, and migration revisions are explicitly deferred to the Increment 1A implementation contract.

Draft content may be updated only after the kernel proves the draft remains mutable under the governing contract. Finalization creates a durable immutable version. Later status changes append events; substantive changes create successor versions. Database constraints reinforce these rules but do not replace kernel validation.

### 6.2 Semantic commit

Each authoritative command executes through one synchronous application service and one database transaction:

1. establish authenticated principal, optional resolved PAIM actor, command identity, target, expected version/absence, and supplied effective time;
2. start an explicit SQLite write transaction using `BEGIN IMMEDIATE` for commands that may write;
3. re-read authoritative preconditions inside that transaction;
4. run mechanical invariant and currentness checks without consulting projections;
5. append the complete accepted version/status/relationship/idempotency/audit set;
6. commit once; or
7. roll back the entire set on validation failure, conflict, storage failure, or audit/idempotency failure.

`BEGIN IMMEDIATE` is chosen so writer contention is surfaced before application work is accepted, rather than during a deferred read-to-write upgrade. SQLite permits one writer at a time and keeps uncommitted writer changes invisible to other connections. See the official [SQLite transaction](https://www.sqlite.org/lang_transaction.html) and [SQLite isolation](https://www.sqlite.org/isolation.html) documentation.

SQLAlchemy Core supplies explicit connection and transaction scopes; it may use driver-level SQL at the adapter boundary to establish the required SQLite transaction mode. Autocommit is prohibited for semantic writes. Nested semantic commits are prohibited; internal composition shares the outer transaction. See the official [SQLAlchemy Core connection and transaction documentation](https://docs.sqlalchemy.org/en/20/core/connections.html).

### 6.3 Concurrency and reads

- Expected-current version or expected absence is mandatory whenever a command depends on current state.
- A stale expectation returns an explicit conflict and creates no partial authoritative facts.
- Uniqueness and overlap-supporting indexes/constraints provide a last line of defense, but the semantic result is computed by the kernel.
- Current selection queries always receive explicit scope, `effective_at`, and optional `known_at`; they never use implicit “now” below the application boundary.
- Selection returns one eligible version, explicit absence, or every incompatible eligible candidate with reasons. `ORDER BY ... LIMIT 1` is not a valid conflict policy.
- Point-in-time reads filter both effective validity and recorded-knowledge cutoff. Backdated facts remain visible to current knowledge while excluded from earlier `known_at` reconstruction.
- Exact-version historical reads bypass current selection and return preserved status and relationship history.

SQLite is adequate for the single-process/local Increment 1A proof. Its single-writer boundary is an accepted tradeoff, not a future production-topology commitment.

## 7. Identity, time, idempotency, and audit conventions

### 7.1 Identity

- Record ID and Record Version ID are separate nominal types and separate stored fields.
- Both use application-generated RFC 9562 UUIDv7 values from `uuid.uuid7()` and serialize as canonical lowercase hyphenated strings at boundaries.
- An ID is opaque after creation. UUID timestamp bits must never decide effective order, recorded order, currentness, succession, conflict, or authorization.
- Event, command, audit, and relationship identities also use UUIDv7 unless a later bounded decision establishes a stronger external interoperability requirement.
- Database-generated integer keys may exist only as private adapter optimizations; they cannot escape as authoritative PAIM identity.

### 7.2 Time

- Application values are timezone-aware UTC `datetime` instances. Naive datetime inputs and non-UTC persistence values are rejected or explicitly normalized at the boundary before validation.
- Persistence uses signed 64-bit integer microseconds since the Unix epoch. Floating timestamps are prohibited.
- External textual interchange uses RFC 3339 UTC with `Z` and six fractional digits.
- Effective intervals are half-open `[effective_from, effective_to)`; a null end means open-ended. An absent effective start means proposed/pending, not current.
- Every finalized version and status event stores recorded time independently from its effective time or interval.
- A `Clock` port supplies recorded time. Tests use a controlled clock; domain logic does not call the system clock directly.
- Equal timestamps are allowed. Deterministic history uses explicit predecessor/relationship facts and a transaction-local audit/event ordinal where needed, never identifier ordering.

### 7.3 Idempotency

Every semantic command carries a command scope and opaque idempotency key. Before command execution, the application computes a SHA-256 digest over a versioned canonical representation of the semantic command, including target, expected precondition, effective time, and payload. Canonicalization is an internal command contract, not a general PAIM record schema.

- First use stores the scope, key, digest, command identity, and complete outcome in the same transaction as the authoritative write.
- Same scope/key and same digest returns the original outcome, including original created IDs, without repeating validation side effects or inserts.
- Same scope/key and a different digest returns `IDEMPOTENCY KEY REUSE CONFLICT` and writes no authoritative change.
- Failed commands that create no authoritative facts may retain an attributable immutable failure outcome when the failure is deterministic; retryable storage failures are not recorded as completed outcomes.
- Idempotency facts do not expire automatically in Increment 1A.

### 7.4 Audit attribution

Every semantic attempt has a command context. Every committed authoritative change appends an audit fact in the same transaction containing:

- authenticated technical principal ID;
- resolved PAIM actor ID when established, or explicit unresolved/not-applicable state;
- operation and result;
- command, idempotency, correlation, and causation identities as applicable;
- target Record ID and exact Record Version IDs;
- expected and observed preconditions;
- effective and recorded time;
- rule/precondition outcomes and reason codes; and
- canonical request digest.

The system never infers that a principal is the accountable PAIM actor. Technical logs, traces, and metrics may repeat identifiers for diagnostics but are non-authoritative, replaceable, and must not be treated as PAIM Evidence or audit history.

## 8. Repository/module/test layout

The later Increment 1A bootstrap must use this source layout:

```text
src/
  paim/
    integrity/              # pure P0 identity, history, time, selection, outcomes
    application/            # command orchestration and semantic commit boundary
    persistence/
      ports.py              # domain-neutral repository/unit-of-work contracts
      sqlite/               # SQLite + SQLAlchemy Core adapter
    audit/                  # principal/actor context and authoritative audit contract
tests/
  unit/                     # pure hard-oracle functions and value objects
  contract/                 # reusable persistence/clock/identity adapter contracts
  integration/              # SQLite transactions, idempotency, history, point-in-time reads
  scenarios/                # longitudinal cross-behavior regression scenarios
migrations/                 # Alembic environment and revisions, when separately authorized
```

Rules for this layout:

- `integrity` has no dependency on SQLAlchemy, SQLite, Alembic, environment variables, or wall-clock access.
- `application` depends on integrity contracts and persistence/audit ports, not on SQLite implementation details.
- the SQLite adapter depends inward on ports; no domain module imports it directly;
- tests may import package internals only through the seam being tested; adapter contract tests must be reusable by a future PostgreSQL adapter;
- no `case`, `configuration`, `roles`, `evidence`, `value`, `risk`, `integration`, `boundary`, `decision`, `intervention`, `reassessment`, `register`, API, UI, worker, or external-adapter module is created in Increment 1A; and
- an empty placeholder package for a deferred module is also prohibited because it can imply unaccepted ownership or dependencies.

The minimum hard-oracle layers are:

1. **Pure unit oracles:** stable/version identity distinction, immutable finalized values, status-vs-content classification, half-open interval behavior, and current selection of one/absence/conflict.
2. **Persistence contract oracles:** append preservation, exact-version retrieval, relationship history, recorded/effective filters, and adapter-neutral outcomes.
3. **SQLite integration oracles:** all-or-nothing commits, rollback, stale preconditions, duplicate delivery, payload mismatch, writer contention, audit attribution, and known-at reconstruction.
4. **Longitudinal scenario oracles:** backdated correction, supersession/withdrawal, overlapping incompatible candidates, and exact historical reconstruction after later changes.

Property-based testing may be added later through a bounded dependency change if interval/state-space coverage demonstrates a need. It is not required to bootstrap Increment 1A.

## 9. Increment 1A implementation boundary

This decision makes the following eligible for a later, separately issued code-bearing Increment 1A issue:

- repository/runtime bootstrap for the selected tools;
- domain-neutral stable Record ID and immutable Record Version ID types;
- the draft/finalization boundary;
- status events distinct from content versions;
- recorded and effective time, including half-open intervals;
- pure current selection returning one version, explicit absence, or explicit conflict;
- correction, amendment, supersession, and withdrawal relationship primitives without family workflows;
- exact history and point-in-time query ports;
- principal-versus-PAIM-actor attribution seam;
- one SQLite persistence adapter and semantic transaction boundary;
- idempotency and append-only audit foundation; and
- executable hard-oracle tests for only those behaviors.

Increment 1A must begin from a separately named clean-main commit, restate these inclusions and exclusions, define physical schemas and migration acceptance criteria in that issue, and end at a draft PR. This artifact does not open Increment 1A automatically.

## 10. Deferred decisions and P1 exclusions

The following platform decisions remain deferred because Increment 1A does not need them:

- HTTP/API style, serialization contract beyond the internal conventions above, authentication provider, credential mechanism, approval/signature technology, and authorization UI;
- web/UI framework, workflow engine, background jobs, notification delivery, report/export stack, search, cache, projections, document/blob storage, and external adapters;
- container images, orchestration, cloud provider, production database, backup service, observability vendor, scaling topology, multi-tenancy, and data partitioning;
- SQLite journal-mode and durability tuning beyond correctness-preserving test defaults; and
- production retention, encryption, disaster recovery, and service-level targets.

All nine P1 findings remain unavailable or explicitly unresolved:

| P1 | Increment 1 exclusion |
|---|---|
| IRR-006 | No selection, freeze, acceptance, or reuse rule among competing Value or Risk Inputs. |
| IRR-007 | No Case–Configuration cardinality, multiple-current Configuration behavior, or materiality/identity authority. |
| IRR-008 | No authoritative Evidence Applicability design, reuse/current-use selection, or automated applicability. |
| IRR-009 | No first-class Observation persistence or Observation conversion/monitoring semantics. |
| IRR-010 | No Intervention prerequisite aggregation, completion acceptance, or target-operation transition. |
| IRR-011 | No Trigger deduplication/merge, concurrent Reassessment coordination, or cross-Reassessment closure. |
| IRR-012 | No Register population/aggregation, shared-dependency equivalence, or concentration analytics. |
| IRR-013 / CON-002 | No general Role Assignment scope precedence, conflict resolution, or permission derivation. |
| IRR-014 | No stronger/broader operating-state ranking, automatic comparison, or state-derived escalation. |

The generic kernel may carry opaque family/scope values supplied by future modules, but it may not enumerate these domain families, interpret scope cardinality, select defaults, or authorize behavior. A deferred question encountered by a generic operation returns explicit unsupported/unresolved behavior.

## 11. Risks/tradeoffs and reversal strategy

| Risk or tradeoff | Control now | Reversal/extension strategy |
|---|---|---|
| Python permits runtime mutation and weaker static guarantees than C#/Java | Frozen values, strict mypy, narrow ports, runtime validation, database constraints, and hard-oracle tests | Preserve serialized contracts and port suites if a later kernel component is replaced. |
| SQLite permits one writer and has database-specific transaction controls | Keep semantic transactions short; surface busy/stale conflicts; test contention; do not claim production scale | Add a PostgreSQL adapter behind the same ports and run the full adapter/semantic suite before cutover. |
| SQLAlchemy Core adds a dependency and does not erase dialect differences | Keep SQL in one adapter; use Core rather than ORM; isolate driver SQL | Replace the adapter without changing integrity/application modules. |
| UUIDv7 exposes approximate creation-time bits and may tempt ordering shortcuts | Treat IDs as opaque and prohibit semantic ordering by UUID | UUID syntax can change only at a boundary; explicit times and relationships remain authoritative. |
| Integer microseconds may not match a future database's native precision | Define one canonical precision and conversion checks | A future adapter may use a native UTC type if round-trip and ordering contract tests prove equivalence. |
| A modular monolith may later need distributed scaling | Retain inward ports, transaction boundary, and authoritative/projection separation | Extract only after demonstrating equivalent semantic commit, idempotency, currentness, audit, and recovery. |
| Forward migrations can make rollback difficult | Review migration scripts, back up before destructive production changes, and test upgrades | Prefer forward repair; use restore-and-replay when a downgrade cannot preserve authoritative history. |

Migration policy is a linear, reviewed Alembic revision history at first. Each deployed database records its applied revision; application startup/commands reject an incompatible schema revision. Autogenerated diffs are review input, never accepted authority. Revisions are forward-oriented and preserve authoritative data. Downgrade is supplied only when demonstrably non-destructive; otherwise recovery uses a verified backup and a forward corrective revision. An Alembic revision is infrastructure metadata and must never be confused with a PAIM Record Version ID. Alembic's official [tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html) documents its revision environment and version locations.

No domain schema, migration revision, or database file is defined by this decision.

## 12. Acceptance criteria

This decision is acceptable only if independent review confirms all of the following:

1. It selects CPython 3.14.x, `uv`, SQLAlchemy 2.x Core, SQLite, Alembic, pytest, Ruff, and mypy for Increment 1 only, with the exact released Python patch pinned at the Increment 1A clean-main checkpoint.
2. It selects one locked, cross-platform local environment and requires exact dependency/tool pins at the later bootstrap step.
3. It defines a domain-neutral package, adapter, migration, and four-layer test layout without creating any files from that layout.
4. It explains how immutable versions, append-preserving status/history, dual time, explicit conflict, and point-in-time reads are supported without defining a physical domain schema.
5. Record ID and Record Version ID are separate opaque UUIDv7 identities, and no semantic ordering relies on them.
6. UTC-aware application time, integer-microsecond persistence, RFC 3339 interchange, injected clock, and half-open intervals are explicit.
7. A semantic command commits authoritative, relationship, idempotency, and audit facts atomically or creates no partial authoritative change.
8. Same-key/same-payload replay returns the original outcome; key reuse with a different payload is an explicit conflict.
9. The test layers provide direct hard oracles for immutability, status/content distinction, time, one/absence/conflict, history, transactions, idempotency, and audit attribution.
10. Alembic is selected with a forward, reviewed, data-preserving migration policy, while all physical schemas and migrations remain deferred.
11. Local execution requires no external service, container, API, UI, or infrastructure.
12. Principal and PAIM actor remain distinct, attributable audit facts are authoritative, and technical telemetry remains non-authoritative.
13. All nine P1 findings and every record-family workflow are explicitly excluded, and no follow-on implementation is authorized.
14. The repository diff for Issue #11 contains exactly this one decision artifact and no system specification modification.

## 13. Final decision summary

PAIM Increment 1 will use a typed synchronous CPython 3.14.x modular kernel, with the exact accepted released patch pinned at the Increment 1A clean-main checkpoint and the environment reproducibly locked with `uv`. SQLAlchemy 2.x Core will isolate explicit persistence ports; SQLite will provide the first local ACID adapter; Alembic will govern later reviewed migrations; and pytest will prove pure, adapter, transactional, and longitudinal hard oracles. Ruff and mypy provide development-time consistency and static checks.

Record and version identities use distinct opaque UUIDv7 values. Time is explicit UTC with separate recorded/effective dimensions and integer-microsecond persistence. Each accepted command uses one transaction to preserve version, status, relationship, idempotency, and audit facts all-or-nothing. The architecture remains a local modular monolith until a later need proves that another topology can preserve the same observable semantics.

This foundation is intentionally smaller than a PAIM platform. It authorizes no code by itself, decides no physical domain schema, implements no record-family workflow, and leaves every P1 dependency blocked. The next step, only when separately issued by ChatGPT through GitHub, is a bounded Increment 1A implementation contract and draft PR.
