# PAIM Local Computer Requirements Review

## Determination

The prospective Gates 1–6 model does not materially change PAIM's current computer class. It adds
relational metadata, immutable history, indexed dual-time queries, and read composition; it adds no
local AI model, bulk analytics engine, telemetry stream, document-content store, scheduler, or
background worker. The current single-workstation requirements therefore need no user-facing
change before implementation and measurement.

The values below are a **Gate-7 planning envelope**, not a benchmark, public support promise, or
organization-local deployment specification. Gate 8 must measure representative migrations,
writes, Home/Case/task reads, then/now reconstruction, database growth, backup, and browser use
before any release documentation changes.

## Current single-workstation/local envelope

| Resource | Minimum planning assumption | Recommended planning assumption | Basis and boundary |
|---|---|---|---|
| CPU | modern 64-bit 2-core processor | modern 64-bit 4-core processor | synchronous Python, SQLite, and server-rendered pages; no ML/numerical workload; more cores mainly help browser/OS and concurrent reads |
| RAM | 4 GB system RAM | 8 GB system RAM | one Python web/CLI process plus browser and OS; current one-worker model; no in-memory authoritative cache required |
| Free disk | 5 GB plus evidence/document storage | 10 GB plus evidence/document storage and at least two database-sized backup copies | application/dependencies are small; immutable Versions, audit, exports, and backups drive growth; large source documents should remain in governed external storage with PAIM provenance/reference |
| Runtime | organization-approved CPython `>=3.12,<3.13`; exact reference 3.12.13; pinned `uv` 0.12.5 | same locked runtime | unchanged accepted runtime; native components must satisfy local application-control policy |
| Browser | current standards-capable desktop browser with cookies and JavaScript; Chromium is the locked browser-test reference | current managed Chromium/Edge-class browser at normal desktop resolution | current server-rendered app uses loopback HTTP, server-side session and CSRF controls, HTML/CSS and bounded JS; product support remains evidence-driven |
| Database | local SQLite file on reliable local storage; one application writer | SSD-backed local storage, one web worker, short semantic writes | SQLite single-writer and `BEGIN IMMEDIATE` are current correctness boundaries, not multi-user scale claims |

Do not place the active SQLite database on an eventually consistent sync folder or shared network
filesystem. Evidence/document binaries are not assumed to be embedded in SQLite. If a later product
stores binaries, OCR, embeddings, or analytics results, it requires a separate resource and
security review.

## Workload assumptions for Gate-8 measurement

Use at least three proportional datasets rather than claim an untested maximum:

| Dataset | Planning shape | Purpose |
|---|---|---|
| Small | 25 Cases, 2 Configurations/Case, 2,000 authoritative Versions, 5,000 audit/relationship/event rows | everyday small-organization responsiveness |
| Medium | 250 Cases, 10,000 authoritative Versions, 50,000 supporting/audit rows | intended local small/medium-organization planning load |
| Stress | 1,000 Cases, 100,000 authoritative Versions, 500,000 supporting/audit rows | expose index/query/backup limits; not a support claim |

For each, measure database size, migration time, backup/restore time, single semantic-command latency,
Home/Case/task read latency, current-position and then/now latency, exact-context lookup,
quantitative comparison, and peak process memory. Include access-filtered low-visibility principals
to test non-disclosure plans rather than only administrator queries.

Suggested acceptance targets for local interactive design, subject to empirical confirmation, are:

- ordinary Case/task reads: p95 under 500 ms on recommended hardware;
- Home/current-position composition: p95 under 1 second for the medium dataset;
- then/now reconstruction: p95 under 2 seconds for one Case/Decision at medium scale;
- short semantic commands: p95 under 1 second excluding human time and external adapters; and
- backup and migration: bounded, progress-visible administrative operations with no active writes.

These are engineering targets, not semantic guarantees. Failure triggers indexing/query redesign,
not weakened access, history, selector, or atomicity rules.

## Growth drivers and controls

Primary growth comes from immutable record Versions, exact context members, relationships,
Responsibility/Work history, audit/idempotency, Review Episodes, quantitative claim context, and
backup copies. Read compositions are not persisted as master truth and therefore do not duplicate
the entire Case state. Exact context sets may be internally deduplicated by canonical digest, but
digest reuse creates no semantic or access inference.

Gate 8 should add indexes only from measured query plans and required selectors. It must verify
write overhead and never remove integrity constraints to improve speed. Routine `VACUUM`, WAL, page
size, journal, and durability tuning remain operational decisions requiring crash/recovery tests;
they are not assumed here.

## Quantitative, history, and composition impact

Typed Quantitative Claims add ordinary relational rows and bounded comparison reads; they do not
require statistical computation. Dual-time reconstruction adds indexed predicates and relationship
traversal. Home/Case/task views add application composition over access-filtered sources. These
features affect index design and row growth more than CPU/RAM class.

No universal score, cross-Case analytics, continuous observation, semantic matching, or local model
is included. Introducing any of those would invalidate this resource review.

## Future organization-controlled-local distinction

The current supported posture remains one loopback application process, one worker, one local
database, and no claim of concurrent CLI/web writing. A future organization-local multi-practitioner
deployment changes the resource and security model even if the domain modules remain reusable.

That later gate must benchmark concurrent readers/writers; choose and validate shared transactional
persistence; establish organization identity, shared sessions, TLS/network controls, backup,
monitoring, and recovery; and size CPU/RAM/storage from measured users, Cases, documents, and
retention. Current hardware figures must not be presented as server sizing.

## Documentation disposition

Do not change the public Quick Start or v0.1 release requirements in Gate 7. The redesign is not
implemented, and the current locked-runtime requirements remain correct. A future release issue may
publish measured minimum/recommended hardware only after Slice H validation and the applicable
deployment boundary are accepted.
