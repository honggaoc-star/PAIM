# PAIM Prospective Physical Architecture & Persistence Plan

## Decision

Extend the current synchronous CPython modular monolith, SQLAlchemy Core ports, SQLite adapter,
Alembic lineage, server-rendered FastAPI browser, and one-process local operational shell. Add
prospective semantic-era modules and tables; do not rewrite the integrity kernel or reinterpret
legacy families.

This plan is physical design for later implementation review. It creates no schema or code.

## Module placement

| Module | Ownership | Reuse boundary |
|---|---|---|
| `integrity` | Record/Version IDs, immutable envelope, semantic-contract reference, exact context set, dual time, selector result, semantic transaction contract | Existing IDs, records, time, selection, command digest remain; new types cannot depend on SQLite/web |
| `responsibility` | Practical Role Relationship, Responsibility, Assignment Basis, resolution, delegation, reassignment | Reads Actor identity; never owns access or substantive authority |
| `case_work` | Derived-work query rules and durable Work, handoff packet, coordination state, result/return, stale context | Work links domain results; never creates them |
| `case_continuity` | Three-status Case contract, status events, continuity determinations, closure/reopen/supersession guards | Uses current Case/Configuration and unresolved-obligation ports; legacy lifecycle remains adapter-owned |
| `continuing_review` | Planned Review Point, Required Review Constraint, intersection, Review Episode, focused carry-forward | Uses Trigger/Reassessment and Decision ports without replacing them |
| `assessment` | Separate Value/Risk candidate finalization, Readiness, Adequacy, Reliance, candidate dispositions, quantitative claims | Existing Evidence/Applicability and analytical content remain sources; legacy Fitness/Selection is adapter-owned |
| `integration_decision` | Exact prospective relied-basis validation, Integration, Boundary, proposal, authorization, confirmation/successor | Extend current Increment-4 services; do not merge assessment or authority ownership |
| `practitioner_queries` | Home, Case, Task, current position, then/now access-filtered compositions | Produces immutable view models/source manifests only; no authoritative persistence |
| `legacy_adapters` | Explicit family/consumer adapters for v0.1 Role, lifecycle, Fitness/Selection, scheduled-like, Integration/Decision reads | No writes in target meaning; no fallback when adapter declaration is absent |

Use capability names rather than a new `increment8`-style dependency chain. Existing modules remain
unchanged until a consumer is explicitly cut over through application ports.

## Common prospective persistence

All new authoritative families continue to use the existing `records`, `record_versions`,
`version_relationships`, `status_events`, `idempotency_facts`, and `audit_facts` tables.

Add these common tables:

| Table | Key and required content | Constraints/indexes |
|---|---|---|
| `semantic_contracts` | stable contract ID, contract version, owning normative source/version, definition digest, introduced recorded time | unique `(contract_id, contract_version)` and definition digest; immutable; adoption state belongs to cutover history |
| `semantic_contract_families` | contract ID/version and each permitted authoritative family/fact kind | exact FK to contract; unique member; immutable |
| `semantic_contract_adapters` / `semantic_contract_successors` | named adapter ID/version, source/target contracts, bounded consumer/effect; and explicitly permitted successor transitions | exact contract FKs and unique versioned identities; catalog metadata only, never implicit fallback |
| `record_version_semantics` | `version_id`, semantic contract ID/version, exact context-set ID, producer command ID | PK/FK `version_id`; all FKs required for prospective Versions; immutable |
| `status_event_semantics` / `version_relationship_semantics` | event or relationship ID, semantic contract ID/version, exact context-set ID, producer command ID | one-to-one exact FK to owning common fact; required for prospective events/relationships; immutable |
| `exact_context_sets` | UUID identity, canonicalization version, SHA-256 canonical digest, member count | unique `(canonicalization_version, digest)`; immutable; internal ID not exposed before access |
| `exact_context_members` | context-set ID, controlled slot/kind, record ID and/or exact Version ID or typed literal, canonical value | composite uniqueness; check exactly one allowed member representation; indexed by referenced Version |
| `semantic_consumer_cutover_records` / `semantic_consumer_cutover_versions` | stable declaration identity, consumer ID, family, accepted semantic contract/version or named legacy adapter, activation/supersession recorded time, migration revision | append-preserving one/absence/conflict selection; operational compatibility metadata, never a domain selector |

Canonicalization is a pure, versioned algorithm. It normalizes controlled slot names and typed
literals, preserves exact Record/Version identity, sorts set members by canonical byte encoding,
rejects duplicate slots where the context schema is singular, and hashes UTF-8 canonical JSON.
Order-sensitive domain content is not represented as a set member. Hash equality is an integrity
check, not authorization, access, applicability, or semantic equivalence.

Legacy Versions/events/relationships have no corresponding semantic-metadata row. Absence means
legacy, not an implicit default contract.

## Family tables

Each family uses stable record and immutable Version tables with exact foreign keys to common
Versions and prospective semantic metadata. Names are proposed for migration design and may be
refined without changing semantics.

### Responsibility and Work

- `case_practical_role_records`, `case_practical_role_versions`;
- `responsibility_records`, `responsibility_versions` with controlled obligation kind, exact
  context-set ID, Case, bounded purpose/use/scope discriminator, state, effective interval;
- `responsibility_assignment_records`, `responsibility_assignment_versions` with Actor or genuine
  mechanism, exact Responsibility Version, Assignment Basis Version, delegation/source, interval;
- `responsibility_assignment_basis_records`, `responsibility_assignment_basis_versions` with exact
  source/authority/provenance and limits;
- `case_work_records`, `case_work_versions` with exact context set, request, assignee, state,
  due/expected time only when justified, and return destination;
- `case_work_result_links` and `case_work_return_links` binding exact Work and governed-result
  Versions; and
- indexes for current Responsibility signature, assignment target/interval, assignee/open Work,
  source context, and result/return lookup.

The database enforces referential shape and immutable history. Domain selectors enforce one,
vacancy, or conflict under exact obligation/context/effective/known time. No uniqueness constraint
silently chooses a current assignment when incompatible candidates coexist.

### Continuing Case

- `case_continuity_status_records`, `case_continuity_status_versions` with only `OPEN`, `CLOSED`,
  and `SUPERSEDED`;
- `case_continuity_determination_records`, `case_continuity_determination_versions` with controlled
  kind/outcome, changed basis, exact predecessor/successor Case and Configuration context,
  Responsibility/authority basis, and rationale; and
- exact relationship rows for reopen/supersede/new-Case outcomes.

Closure and supersession are application semantic transactions that query all required guard
ports before appending facts. A database check cannot infer whether obligations are substantively
complete.

### Continuing review

- `planned_review_point_records`, `planned_review_point_versions`;
- `required_review_constraint_records`, `required_review_constraint_versions` with exact source
  Version, Applicability Version, scope, `BY`/`NOT_BEFORE`/`WINDOW`, timezone, interval, authority;
- `review_episode_records`, `review_episode_versions`;
- `review_episode_basis_links`, `review_episode_work_links`, and `review_episode_outcome_links`; and
- indexes by Case/current Decision/Configuration/purpose, due window, source, episode state, and
  effective/known time.

Constraint intersection is a pure read/domain service over every applicable current Version. It
returns a compatible exact window, absence, or explicit unresolved conflict and never stores a
winner.

### Assessment and quantitative claims

- `assessment_readiness_records`, `assessment_readiness_versions` (or event identity where the
  controlling implementation issue confirms event-only cardinality);
- `assessment_adequacy_records`, `assessment_adequacy_versions` with lane, exact candidate/readiness,
  bounded Decision use, exact information/Applicability basis, outcome, limitations, rationale,
  Actor/Responsibility, and dual time;
- `assessment_reliance_records`, `assessment_reliance_versions` with lane, candidate set, selected
  adequate chain, dispositions, use/purpose, Actor/Responsibility, and dual time;
- `quantitative_claim_records`, `quantitative_claim_versions`; and
- normalized `quantitative_claim_relationships` and optional structured context components for
  representation/range/distribution, unit, direction, scope/population, period,
  comparator/baseline, coverage, method/assumptions, uncertainty, source, and Applicability.

Quantitative Claim is a related stable Record family because claims may be reused by multiple
assessments/reviews, corrected, superseded, compared later, and reconstructed independently. The
family supports the six controlled claim types without requiring every optional context field.
Structured fields carry exact comparability; bounded narrative retains assumptions/limitations.
No calculated score or generic value column becomes a selector.

## Selector and query boundaries

Every authoritative family owns a typed selector port with explicit:

- semantic contract/version or explicit legacy adapter;
- exact context set and controlled family discriminator;
- effective-at and known-at;
- eligible status/disposition and predecessor/supersession rules; and
- access-independent domain outcome: found, not established, or unresolved conflict.

Application queries perform source access filtering before passing candidates into a composition.
Composition cannot query a global population and filter its result afterward. Hidden candidates
cannot alter visible counts, conflict labels, attention, or source manifests.

## Natural command and unit-of-work architecture

The browser/API adapter submits one command intent with:

- authenticated principal and resolved durable Actor;
- action kind and controlled semantic contract;
- server-reconstructed exact context-set identity;
- explicit expected Versions for every mutable current basis;
- idempotency scope/key and canonical payload digest;
- effective time and server recorded time; and
- practitioner inputs and confirmations only.

The application command loads every required source through ports, evaluates software access,
visibility, Responsibility, substantive authority, currentness, applicability, and family guards,
then opens one outer `semantic_transaction`. It repeats guard reads needed under the write lock,
appends every intended record/link/event/audit/idempotency fact, and commits once. Internal domain
functions never open nested transactions.

| Natural action | Intended facts in one transaction | Fail-closed result and read response |
|---|---|---|
| Create/open proposed Case | Case, initial Configuration/context, prospective `OPEN` continuity fact, relationships, audit | Any invalid context/authority creates nothing; return Case orientation |
| Finish Value assessment | finalized exact Value candidate plus attributed Readiness fact | stale/missing information or Responsibility creates nothing; return review attention |
| Finish Risk assessment | finalized exact Risk candidate plus attributed Readiness fact | same, independently by Risk lane |
| Assign Responsibility | exact assignment plus Assignment Basis and history links | unauthorized, stale, incompatible, or conflicting basis creates nothing; return found/vacancy/conflict |
| Perform governed result + return | owning domain result, Work result link, Work state/return facts | any domain/Work/context guard failure creates neither result nor completion; return destination task |
| Complete Value review | one Adequacy Determination plus one Reliance Designation only when combined-action guards hold | different Actors, multiple candidates, stale candidate, missing basis, or conflict creates neither; return lane position |
| Complete Risk review | same independent Risk facts | same independent failure behavior |
| Integrate Value/Risk | Integration bound to one exact prospective relied chain per lane | absent/conflicting/stale/mixed-era chain creates nothing; return exact limitations/readiness |
| Propose Decision | proposal plus exact Integration/Boundary/basis links | stale chain or changed Boundary creates nothing; return proposal-awaiting-authority |
| Authorize Decision | authorized successor Version and Authorization Basis/relationships | access, Responsibility, authority, scope/time, or currentness failure creates nothing |
| Confirm unchanged Decision | Confirmation linked to exact current Decision/review basis | changed position or missing authority creates nothing; return current position |
| Authorize successor Decision | successor Decision, Boundary/Basis as required, predecessor relation | predecessor remains unchanged on any failure |
| Establish/change next review point | new point Version plus predecessor/cancellation/supersession facts | constraint/Responsibility/authority conflict creates nothing; return planned/required timing |
| Begin continuing review | Review Episode, exact point/event source link, initial scope | date arrival alone cannot create it; return focused review task |
| Complete continuing review | episode outcome plus exact Confirmation or successor link; optional separately valid next point | zero/both Decision paths or invalid next point rolls back all intended combined facts |
| Close/reopen/supersede Case | Continuity Determination, status Version, exact relationships | unmet obligations, invalid successor, stale context, or missing authority creates nothing |

No adapter may add a separate practitioner click for readiness, Versioning, freeze, selection,
Work/result linkage, or transaction construction.

## Idempotency and replay

Use one stable client intent ID generated when a confirmation surface is rendered and retained in a
server-verifiable form. The idempotency scope includes command family and authenticated principal;
the canonical digest includes semantic contract, exact context set, expected Versions, and
practitioner payload. Exact replay returns the original outcome. Same key with any different digest
is rejected. Restart safety comes from persisted idempotency and context, not session memory.

## Read composition architecture

`PractitionerQueryService` remains an application read boundary and expands into typed composition
ports:

| View | Source boundary | Required result |
|---|---|---|
| Home — What needs me? | visible current Responsibilities, durable/derived Work, due review attention, explicit vacancies/conflicts relevant to Actor | unranked attention with source manifest; no inferred assignment/priority |
| Case — What is happening here? | visible Case/Configuration, current Value/Risk, Decision/Boundary, Work, review, unresolved information/authority | current management position with absence/conflict and exact source basis |
| Task — Help me accomplish this work | one exact Responsibility/Work/governed-result context and permitted action consequences | minimum context, ordinary question, authority boundary, return path |
| Current management position | exact current sources selected independently by owning families | derived immutable view only; never a master status/record |
| Then versus now | Decision-bound effective/known cutoff plus separately current visible sources | two source manifests; later facts cannot enter earlier side |

View models contain source-basis references for provenance but templates default to practitioner
language. Engineering detail is an explicitly authorized expansion. Caching, if later introduced,
is keyed by principal/access epoch, query context, semantic contracts, effective/known cutoff, and
source watermark; stale or uncertain cache state is visibly ineligible for commands.

## Access and non-disclosure

1. Authenticate principal and resolve current Actor from durable operational records.
2. Determine permitted Case/Configuration/source population for each family.
3. Fetch or reject exact source Versions without revealing hidden existence.
4. Compose only the filtered set.
5. Evaluate command permission separately from Responsibility and substantive authority.
6. Revalidate all layers inside the command boundary before commit.

Error codes are stable internal categories. The practitioner explanation names only visible facts,
the legitimate missing/conflicting requirement, consequence, and next action. Counts, timing,
relationships, and conflict existence from hidden sources are not disclosed.

## Legacy boundary

Legacy adapters are read-only translators with a declared consumer, accepted legacy source family,
exact result type, limits, and source manifest. They never:

- write prospective facts;
- equate Role Assignment with Responsibility;
- equate lifecycle phase with continuity status;
- equate Fitness with adequacy or Acceptance/Selection with reliance;
- manufacture exact context or semantic metadata;
- combine legacy and prospective candidates in one selector without an accepted compatibility rule;
  or
- activate automatically because prospective data is absent.

An unsupported or ambiguous legacy source returns not established or explicit conflict. It never
falls through to a convenient current row.
