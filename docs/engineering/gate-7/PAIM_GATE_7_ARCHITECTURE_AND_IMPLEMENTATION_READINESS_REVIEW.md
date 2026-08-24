# PAIM Gate-7 Architecture & Implementation Readiness Review

## Verdict

**PASS WITH BOUNDED CONDITIONS**

PAIM can implement the accepted prospective Gates 1–6 semantics in the existing synchronous
CPython modular monolith without making practitioners operate the engineering model and without
weakening exact authority, history, atomicity, access, or fail-closed behavior. No blocking
semantic contradiction or architectural impossibility was found.

The pass is bounded by the physical, migration, slice, test, and resource plans in this package.
It authorizes no code, schema, migration, consumer cutover, UI, deployment, Harborlight, or release
change. Gate 8 requires a separate issue and independent review.

## Review basis and method

The review traced the accepted Product Design Foundation, Practitioner Operating Model, Normative
Model Redesign, Gates 1–6 specifications, and Harborlight validation into the current repository:

- `src/paim/integrity/` — typed identity, immutable Versions, selection, dual time, and commands;
- `src/paim/domain/` and `src/paim/application/` — existing bounded domain services and ports;
- `src/paim/persistence/sqlite/` and Alembic revisions `0001`–`0008` — 135 existing tables,
  foreign keys, indexes, append-only triggers, and explicit transactions;
- `src/paim/operational/` — durable principal/Actor mapping, software access, health, backup,
  restore, intake, replay, and audit;
- `src/paim/application/practitioner/` and `src/paim/web/` — access-filtered Home/Case views,
  browser command adapters, loopback session security, and progressive practitioner expression;
- current unit, contract, integration, scenario, browser, migration, transaction, access, and
  practitioner-query tests; and
- current upgrade, recovery, local-operation, and release documentation.

The review is static and non-mutating. It does not claim runtime validation of prospective
families.

## Central architecture answer

The sound existing core is extensible:

1. finalized authoritative Versions and audit facts are immutable;
2. semantic writes already use one explicit SQLite transaction, expected-Version preconditions,
   idempotency scope/key/payload checks, and all-or-nothing audit;
3. selectors already return one, absence, or conflict for explicit effective and knowledge time;
4. domain/application ports keep SQLite and web concerns outside semantic modules;
5. durable principal-to-Actor mapping and access checks are distinct from Role accountability and
   substantive authority; and
6. practitioner reads already establish the rule that callers provide an access-filtered source
   population before composition.

The redesign must not be forced into current lifecycle, Role Assignment, Fitness, or
Acceptance/Selection meanings. The safe design adds prospective families and semantic metadata,
then uses explicit per-consumer adapters for legacy reads. Existing history remains legacy and is
never backfilled with invented target meaning.

## Current implementation gap map

Classifications apply to prospective semantics, not the continuing validity of v0.1 behavior.

| Prospective family or composition | Current support | Classification | Gate-8 disposition |
|---|---|---|---|
| Record/Version identity, immutable finalization, effective/recorded time, relationships, status events, audit | Generic integrity kernel, `records`, `record_versions`, relationship/event/audit tables, append-only triggers | **Reusable as-is** | Retain common kernel and ports; prospective families use it |
| Semantic-contract identity/version and family adoption metadata | No prospective contract registry or per-Version semantic metadata | **Requires new domain/persistence support** | Add immutable contract registry plus one-to-one Version metadata; no legacy backfill |
| Exact typed context sets and canonicalization | Exact foreign keys and family-specific context exist, but no common typed/canonical context-set identity | **Requires new domain/persistence support** | Add canonical immutable context-set/member tables and typed domain value; reject duplicate/noncanonical inputs |
| Practical-role relationship | Actor and legacy free-form Role Assignment exist | **Reusable with adapter/extension** | Add prospective practical-role family; expose legacy assignments only through bounded adapter |
| Responsibility and exact obligation signature | Legacy Role Assignment/accountability resolution uses role, target, compatibility key | **Requires new domain/persistence support** | Add controlled obligation kind, exact context, assignment, basis, delegation, and one/absence/conflict selector |
| Responsibility Assignment Basis | Some current records cite assignment Version or mechanism; no common prospective family | **Requires new domain/persistence support** | Add exact basis family/component and require it for every prospective assignment |
| Durable Case Work, handoff, result, return, stale handling | No durable prospective Work family; browser/task state is not authoritative Work | **Requires new domain/persistence support** | Add Work identity/Versions, context, state, result/return links, and no-retarget guards |
| Case Continuity Status/Event and Determination | Legacy multi-phase `CaseLifecycleState` and status events | **Legacy-only / must remain isolated** plus new support | Add three-status prospective family and determination; legacy phase adapter cannot emit target status |
| Managed Configuration identity/history/governing selection | Exact records, Versions, owning Case, designation, current selection | **Reusable with adapter/extension** | Retain existing family; bind prospective semantic metadata/context and continuity guards |
| Planned Review Point | No authoritative family | **Requires new domain/persistence support** | Add immutable Versioned point with exact Case/Decision/Configuration/purpose context |
| Required Review Constraint and intersection | Authority/Evidence and Boundary sources exist; no normalized constraint family/composer | **Requires new domain/persistence support** | Add constraint/source/Applicability family and pure intersection service |
| Review Episode | Trigger/Reassessment history exists; no target continuing-review episode | **Requires new domain/persistence support** | Add episode family linked to point/event, focused work, completion, Decision outcome, and next point |
| Value/Risk candidate/Input Version and legacy readiness/finalization | Analytical Inputs, Evidence links, lane Fitness, Acceptance/Selection, freeze, exact lane currentness | **Legacy-only / must remain isolated** plus reusable source data | Preserve exact v0.1 chain; prospective consumer adapter may read it only with declared mapping/result |
| Prospective Assessment Readiness Event | Finalization and legacy readiness concepts exist but no target attributed readiness family | **Requires new domain/persistence support** | Add separate event/fact committed with exact candidate finalization by Finish action |
| Assessment Adequacy Determination | Lane Fitness is different and cannot be reinterpreted | **Requires new domain/persistence support** | Add neutral three-outcome family with exact information/Applicability basis and selector |
| Assessment Reliance Designation | Acceptance/Selection is different and cannot be reinterpreted | **Requires new domain/persistence support** | Add exact reliance/candidate-disposition family; bounded legacy adapter remains explicit |
| Optional Quantitative Claim | JSON analytical content can carry numbers but lacks typed identity/context/comparison guards | **Requires new domain/persistence support** | Add related stable Record family; do not embed mutable/unversioned fields or create a score |
| Integration exact prospective relied basis | Current Integration binds exact accepted Value/Risk Inputs, fitness, use/purpose, and is revalidated | **Reusable with adapter/extension** | Add exact prospective chain links and reject mixed/undeclared semantic eras |
| Proposal, Boundary, Decision, Authorization Basis, Confirmation | Exact current families and authority guards exist | **Reusable with adapter/extension** | Extend commands to consume prospective Integration basis; never weaken separate authorization |
| Idempotency, stale-write detection, semantic transaction, audit | Existing application/store contracts and `BEGIN IMMEDIATE` write boundary | **Reusable as-is** with composed commands | Let one outer unit of work commit all intended facts; no nested semantic commits |
| Dual-time and historical reconstruction | Exact Version/effective/recorded selection and current practitioner source basis exist | **Reusable with adapter/extension** | Add contract/context filters and cross-era adapter provenance; preserve exact legacy reads |
| Home and Case read compositions | Existing practitioner models/services and web routes | **Reusable with adapter/extension** | Expand source families after access filtering; remain non-authoritative and source-traceable |
| Task composition | Current task-oriented browser pages carry some context; no general prospective Task query | **Requires new read support**, no new master record | Compose derived/durable Work and governing result context through a query port |
| Current management position | Partial Case/Decision workspace exists; no complete target composition | **Requires new read support**, not persistence | Compose exact current sources, absence, conflict, and attention on demand |
| Then-versus-now / Decision-time view | Underlying history exists; no complete practitioner composition | **Requires new read support** | Build access-filtered dual-time query with source manifest; persist no summary truth |
| First-class Observation, telemetry, automatic analytics, cross-Case authority | Explicitly excluded | **Not implemented by design** | Keep unavailable; typed observed claims do not create IRR-009 Observation semantics |

## Ten mandatory Harborlight criteria

| Criterion | Architecture disposition | Result |
|---|---|---|
| Natural actions are command boundaries | Composed application commands own one outer semantic transaction and return ordinary outcomes | PASS |
| Home/Case/Task attention is non-authoritative | Query services compose access-filtered authoritative sources; no master current-position table | PASS |
| Exact context is carried automatically | Signed/opaque server-side task reference resolves a persisted exact context set; commit revalidates it | PASS WITH IMPLEMENTATION CONDITION |
| Fail-closed states are explainable | Domain failure codes map to ordinary explanation plus missing/conflicting source references after access filtering | PASS WITH IMPLEMENTATION CONDITION |
| One-person staffing is simple | One Actor may satisfy multiple separately resolved Responsibilities; combined command remains multi-fact | PASS |
| Detail uses progressive disclosure | Default view models exclude engineering identifiers; provenance/audit query remains separate | PASS |
| Continuing review is focused | New timing/episode families and exact carry-forward selector avoid cadence and copying | PASS WITH NEW SUPPORT |
| Quantitative claims avoid false precision | Related typed claim family preserves optional context and explicit comparison eligibility | PASS WITH NEW SUPPORT |
| Management history emerges from work | Every natural command emits exact facts, links, idempotency, attribution, and audit atomically | PASS |
| Gates 1–6 non-inference remains hard | Test matrix makes negative oracles mandatory across domain, persistence, application, read, and browser layers | PASS WITH TEST CONDITION |

## Bounded conditions

Gate 8 must satisfy all of these conditions:

1. **Add, do not reinterpret.** Prospective semantic metadata begins only with an explicitly cut-over
   family/consumer. No migration invents semantic-contract, Responsibility, continuity, adequacy,
   reliance, review, or quantitative meaning for legacy rows.
2. **No silent fallback.** A prospective command encountering missing, mixed, unsupported, stale,
   or conflicting semantic basis fails closed. A legacy adapter is selected explicitly and returns
   its exact source/provenance and limits.
3. **One outer transaction.** Natural combined actions commit every intended authoritative fact,
   relationship, status effect, idempotency fact, and audit record together or commit nothing.
4. **Access before composition.** Query adapters filter every source family before aggregation;
   hidden existence, counts, conflicts, and relationship shapes cannot affect visible output.
5. **Persistent continuity.** Handoff/task identity and exact context live in authoritative Work or
   server-reconstructable persisted facts, never only in a browser session or PowerShell variable.
6. **Typed quantitative claims are related Records.** Stable identity, reuse, correction,
   predecessor history, and multiple consumers require a related Versioned family, not an embedded
   unversioned JSON field.
7. **Current local limits remain explicit.** Loopback one-worker/single-writer support does not
   become a multi-practitioner deployment claim. Ports and command contracts must remain suitable
   for a future transactional adapter.
8. **Every slice carries hard oracles.** No slice merges until its migration, selector, replay,
   access, dual-time, zero-mutation, and non-inference exit tests pass.

## Security and concurrency determination

The proposal preserves five distinct layers: identity (authenticated principal resolved to a
durable PAIM Actor), software access, exact governed-context visibility,
Responsibility/accountability, and substantive authority. Browser session state may cache
authentication and CSRF only. It may not carry the sole identity of Work, source Version, exact
context, or pending semantic transaction.

Current SQLite `BEGIN IMMEDIATE`, expected-Version checks, idempotency facts, and one worker are
adequate for the bounded single-workstation implementation. They serialize writers rather than
solve organization-local concurrency. Future organization-local operation remains feasible because
commands use explicit expected Versions and idempotency identities behind persistence ports. Before
multi-process or network use, a separately reviewed deployment gate must add a shared identity
provider/session store, transactional database adapter or proven SQLite topology, cross-process
idempotency, and full access/concurrency adapter conformance.

## Conclusion

Gate 7 finds an implementable path with bounded additive change. The existing architecture should
be extended around its integrity, transaction, port, access, and practitioner-query seams. It must
not reuse legacy semantics by name similarity or expose new record machinery as practitioner work.
The accompanying plans are the required implementation-readiness baseline.

## Package

- [Prospective Physical Architecture & Persistence Plan](PAIM_PROSPECTIVE_PHYSICAL_ARCHITECTURE_AND_PERSISTENCE_PLAN.md)
- [Migration / Semantic-Era Cutover Plan](PAIM_MIGRATION_AND_SEMANTIC_ERA_CUTOVER_PLAN.md)
- [Implementation Slice Plan](PAIM_IMPLEMENTATION_SLICE_PLAN.md)
- [Gates 1–6 Conformance Test Matrix](PAIM_GATES_1_6_CONFORMANCE_TEST_MATRIX.md)
- [Local Computer Requirements Review](PAIM_LOCAL_COMPUTER_REQUIREMENTS_REVIEW.md)
