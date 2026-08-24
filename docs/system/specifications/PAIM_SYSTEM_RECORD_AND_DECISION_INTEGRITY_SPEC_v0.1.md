# PAIM System Record and Decision Integrity Specification v0.1

## Status

Implementation-independent cross-cutting system specification for authoritative-record history, current-record selection, Integrated Operating Boundary integrity, PAIM case transitions, decision authorization, and interim operating disposition during reassessment.

This specification resolves the blocking findings IRR-001 through IRR-005 and CON-001 in `PAIM_CODEX_IMPLEMENTATION_READINESS_REVIEW_v0.1.md`.

It also supplies the cross-cutting integrity rules needed by the accepted PAIM v0.1 resolution of IRR-007 and IRR-013/CON-002. The Managed Configuration, Case Lifecycle, and Roles/Accountability specifications remain the substantive owners of those scope, cardinality, role, and accountability semantics.

It governs the cross-cutting semantics defined here across the PAIM v0.1 system specification set. The affected specifications continue to govern the substantive content and human judgments of their record families. Where an earlier v0.1 specification is silent, optional, or inconsistent on a cross-cutting matter defined here, this specification controls. It does not replace the analytical or management semantics of those specifications.

This specification does not prescribe a database, event store, programming language, workflow engine, identity provider, signature technology, API, or user interface.

The Gate-1 common-integrity additions in Section 3A are prospective controlling machinery for
record families whose later owning specification explicitly adopts them. Existing v0.1 record
families and records retain their current contracts and meaning until their separately authorized
Gate 2–6 revisions are accepted. Section 3A does not itself create Responsibility, Case continuity,
Case Work, Review Timing, assessment adequacy/reliance, or quantitative Value/Risk semantics.

## 1. Purpose

PAIM requires a platform to preserve and enforce management history without inventing management behavior.

The system must be able to answer, deterministically and historically:

- Which exact record version was relied upon?
- Which record was authoritative for a scope and effective time?
- What changed, when, and why?
- What operating boundary was authorized?
- Which lifecycle transition occurred and which guards were satisfied?
- What legitimate authority authorized the decision?
- What governed operation while reassessment was pending?
- Did reassessment confirm the existing decision or create a traceable successor?

## 2. Scope and normative relationship

### 2.1 Authoritative record families

The common record-history contract applies to authoritative PAIM records, including:

- Case;
- Managed Configuration;
- governing Configuration designation/currentness relationship;
- Configuration materiality and same-identity/new-identity determination;
- Evidence;
- Evidence Applicability relationship;
- Authority;
- Authority Gap;
- Value Management Input;
- Risk Management Input;
- Integration;
- Integrated Operating Boundary Snapshot;
- Management Decision;
- Decision Authorization Basis;
- Intervention;
- Decision-to-Intervention Obligation Set and Obligation;
- Intervention Completion Result;
- Intervention Completion Acceptance;
- Prerequisite Evaluation Basis;
- Activation Authorization;
- Learning Item;
- Observation where represented as an authoritative record;
- Reassessment Trigger;
- Reassessment;
- Interim Operating Disposition;
- Role Assignment and delegation;
- accountable assignment/designation or explicitly governed accountable mechanism where represented separately;
- any durable confirmation, correction, amendment, or supersession record affecting the above.

The Management Register is a derived view and is not an independently mutable authoritative record. Its selection of current source records follows this specification.

### 2.2 Substantive specifications remain authoritative

This specification does not decide:

- whether evidence is sufficient;
- whether a configuration change is material;
- what Value or Risk concludes;
- what uncertainty is Accepted or Decision-Limiting;
- what management should decide;
- whether a narrative boundary clause is substantively appropriate;
- how an organization assigns authority.

It defines how those judgments are identified, authorized, versioned, related, selected, and preserved after accountable actors make them.

### 2.3 No silent fallback

When the required identity, version, scope, effective-time, or authority information is missing or conflicting, the system must represent the gap or conflict. It must not select a record because it is newest, most convenient, or most permissive unless an explicit PAIM rule or authorized organizational mechanism establishes that result.

## 3. Common authoritative-record history contract

### 3.1 Stable record identity

A **Record ID** identifies the continuing management subject across versions.

Examples:

- one Managed Configuration identity across configuration versions;
- one Value Input identity across refreshed versions where continuity is retained;
- one Intervention identity across revised versions where it remains the same intervention;
- one Role Assignment identity across traceable assignment versions.

A Record ID must not be reused for a different management subject.

### 3.2 Immutable version identity

Every durable content version has a distinct **Record Version ID**.

A version binds:

- Record ID;
- version identifier;
- record family/type;
- content;
- status at finalization where relevant;
- recorded time;
- effective time or interval;
- creator/source;
- predecessor version where applicable;
- reason for creation, correction, amendment, or supersession;
- relationships to exact versions of records relied upon where the substantive specification requires them.

Two different contents must not share one Record Version ID.

### 3.3 Draft mutation boundary

Draft content may be edited in place only while all of the following are true:

- the record version is explicitly `draft` or equivalent;
- it has not been frozen, finalized, authorized, issued, relied upon by an authorized decision, or made effective;
- no later authoritative record relies on that exact draft version as historical evidence;
- the edit remains attributable through draft audit history appropriate to the platform.

If a draft has already been cited by another finalized record, it must be finalized as cited or replaced by a new draft/version with an explicit relationship; the cited content must remain reconstructable.

### 3.4 Finalization boundary

Finalization occurs at the record-family event that makes content authoritative for its declared purpose.

Examples include:

- configuration version made current, proposed for formal decision, or preserved as the exact evaluated snapshot;
- evidence issued or accepted into the evidentiary record;
- Value or Risk Input frozen;
- Integration completed;
- Integrated Operating Boundary Snapshot completed for authorization;
- Management Decision authorized;
- Intervention plan finalized or completion result attested;
- Learning Item activated or result finalized;
- Reassessment completed;
- Role Assignment activated;
- Interim Operating Disposition authorized.

Finalized content is immutable. A status change after finalization does not reopen content for editing.

For a Value or Risk Input, analytical readiness is not finalization. The first valid lane-specific Acceptance/Selection semantic commit atomically finalizes/freezes the exact Input Version if necessary and records its first bounded selection. Later reuse records a new use-specific Acceptance/Selection Version and never refreezes or rewrites the Input Version.

### 3.5 Status events vs. content versions

A status event records a lifecycle fact about an existing version without changing its substantive content.

Examples:

- a current version becomes superseded;
- an assignment expires or is revoked;
- an intervention becomes blocked;
- a Learning Item becomes overdue;
- a decision is withdrawn prospectively;
- an Interim Operating Disposition expires.

A new content version is required when substantive content, scope, rationale, boundary, condition, conclusion, requirement, authority basis, or accountable judgment changes.

Status events must preserve:

- event identity;
- target Record Version ID;
- prior status;
- new status;
- recorded time;
- effective time;
- actor or authorized mechanism;
- basis/reason.

A platform may physically store status with the record, in an event stream, or otherwise, but it must reproduce the same status history and point-in-time result.

### 3.6 Recorded time and effective time

Every finalized version and status event must preserve:

- **recorded time** — when PAIM recorded the fact; and
- **effective time** or **effective interval** — when the content or status governs the management subject.

If effective time is not yet established, the version remains proposed/pending and must not be selected as effective current authority.

An effective interval is half-open for ordering purposes:

```text
[effective_from, effective_to)
```

An open end means the version remains effective until an explicit ending event or successor becomes effective.

Backdated recording must preserve both times and the reason. It must not rewrite what the system showed as recorded knowledge at an earlier time.

### 3.7 Correction

A correction repairs an error in a prior record while preserving the erroneous version.

A correction must:

- create a new Record Version ID or a separately immutable correction record;
- identify the corrected version;
- state the error and corrected content;
- preserve recorded and effective times;
- identify decisions or other finalized records potentially affected;
- trigger reassessment where the correction could change a current management judgment.

A correction does not silently replace the historical content used by an earlier decision.

### 3.8 Amendment

An amendment changes substantive content prospectively while retaining continuity of the same management subject.

An amendment:

- creates a new version;
- identifies its predecessor;
- states the changed content and reason;
- has its own authorization/finalization where required;
- becomes effective only under its declared effective time;
- does not mutate its predecessor.

For an authorized Management Decision, an “amendment” is an authorized successor Decision version. It is not an editable patch to the prior Decision version.

### 3.9 Supersession

Supersession establishes that a successor version or record governs prospectively for a declared scope.

Supersession must identify:

- predecessor;
- successor;
- scope of replacement;
- effective time;
- actor/authority or authorized mechanism;
- reason.

Supersession does not mean that prior evidence was false or that a prior decision was unauthorized for its historical period.

### 3.10 Withdrawal

Withdrawal ends prospective reliance on a record without erasing it.

Withdrawal must identify:

- record/version withdrawn;
- effective time;
- actor/authority;
- reason;
- current decisions or workflows affected;
- whether reassessment or replacement is required.

Withdrawal of an analytical input, authority, assignment, intervention, or decision relied upon by current operation must create an integrity condition and reassessment trigger where material. It does not rewrite the historical decision basis.

### 3.11 Current-record selection

“Current” is a derived result for a declared:

- record family;
- management subject/scope;
- configuration/version where applicable;
- decision or workflow purpose where applicable;
- effective time; and
- recorded-knowledge cutoff where a point-in-time reconstruction is requested.

The system selects an authoritative current record only when exactly one eligible finalized version:

1. matches the required identity and scope;
2. is effective at the requested effective time;
3. was recorded by the requested knowledge cutoff, if one is supplied;
4. has the required finalized/authorized state for the purpose;
5. is not prospectively withdrawn, expired, or superseded for that scope and time; and
6. satisfies any record-family guard, including exact configuration binding and authority applicability.

If no version qualifies, the result is explicitly absent/not established.

If more than one incompatible version qualifies, the result is **CURRENT RECORD CONFLICT — UNRESOLVED**. The platform must not choose by row order, creation time, version label, or convenience. An accountable resolution, correction, or supersession is required.

Multiple current records are permitted only when the substantive specification explicitly allows them in distinguishable, non-competing scopes. The scope distinction must be recorded.

For PAIM v0.1 governing-Configuration selection is Case-scoped. Each Configuration identity has exactly one owning Case, and one Case has at most one governing Configuration at an effective time. The result is one exact governing Configuration version, explicit absence/not established, or explicit conflict. Proposed, experimental, alternative, and fallback purpose does not make a Configuration eligible as governing. Two same-Case, same-time governing candidates are incompatible; the platform must not treat them as a permitted set or select by recency, purpose, authorization date, or convenience. Independent concurrent governing Configurations use separately linked Cases.

Role-performer selection and accountability selection are distinct. Role resolution for one typed target/time may return multiple compatible performer assignments when the substantive role is additive. When a governed obligation requires accountability, selection returns exactly one eligible accountable Role Assignment or one explicitly governed accountable mechanism, explicit vacancy/not established, or explicit incompatible-accountability conflict. Broad and narrow assignments have no implicit precedence. Recency, breadth, specificity, directory hierarchy, and software permission must not select an accountability or authority winner; displacement requires explicit supersession, delegation, or a later accepted versioned policy.

Value Input and Risk Input acceptance/selection are separate authoritative relationship families. For one lane, exact Configuration Version, bounded use/purpose, effective time, and optional knowledge cutoff, selection returns one eligible accepted/frozen Input Version plus its exact Acceptance/Selection Version, `INPUT SELECTION NOT ESTABLISHED`, or `INPUT SELECTION CONFLICT — UNRESOLVED`. Zero eligible Acceptance/Selection Versions returns `INPUT SELECTION NOT ESTABLISHED` regardless of how many ready candidate Inputs exist; ready candidates remain preserved alternatives and do not create authoritative selection conflict merely by being ready. Conflict arises only from two or more incompatible co-current eligible Acceptance/Selection Versions for that same explicit selection context. Ready status, newest/latest time, owner, generic role, integrator participation, mutable flag, row order, or software permission cannot select a winner. Each later reuse requires a new use-specific acceptance and accountable material-Evidence fitness judgment.

Evidence Applicability is a first-class authoritative many-to-many relationship. For one exact Evidence Version, target identity/version, purpose/use, assessed scope, effective time, and optional knowledge cutoff, selection returns one eligible Applicability Version, `APPLICABILITY NOT ESTABLISHED`, or `EVIDENCE APPLICABILITY CONFLICT — UNRESOLVED`. Conflict is not a stored Applicability outcome. Recency, specificity, ownership, directory hierarchy, mutable current flag, row order, or permission cannot resolve it.

For one exact Decision Version, target Configuration Version, effective time, and optional knowledge cutoff, Decision-to-Intervention Obligation Set selection returns one eligible current set, explicit absence/not established, or explicit conflict. Only an explicit eligible set containing zero `REQUIRED_BEFORE_OPERATION` obligations yields `NOT_REQUIRED`; missing data never does.

For one exact Obligation, Completion Acceptance selection returns one eligible Acceptance, `ACCEPTANCE NOT ESTABLISHED`, or `COMPLETION ACCEPTANCE CONFLICT — UNRESOLVED`. Accountability resolves separately as one eligible Completion Acceptor assignment/mechanism, explicit vacancy, or explicit conflict for the exact Intervention/Decision/target-Configuration/owning-Case target set. No scope, time, ownership, role, directory, or permission fallback selects a winner.

For one exact Trigger identity/Version, Case/Decision/Configuration context, management question, effective time, and optional knowledge cutoff, Trigger Determination selection returns one eligible determination, `TRIGGER DETERMINATION NOT ESTABLISHED`, or `TRIGGER DETERMINATION CONFLICT — UNRESOLVED`. Exact command replay is identity/idempotency based; semantic similarity never deduplicates or selects.

For one exact Reassessment identity, current selection returns one eligible Reassessment Version with its immutable exact Trigger Set, explicit not established, or explicit conflict. Multiple open Reassessments in one Case are permitted only in distinguishable non-competing scope or through one eligible accountable compatibility/coordination determination. Shared or indeterminate scope is `REASSESSMENT OVERLAP CONFLICT — UNRESOLVED`; no recency, severity, hierarchy, breadth, or software-priority winner exists.

For one current eligible Trigger requiring reassessment, Trigger Coverage selection returns one compatible result from `REASSESSMENT_REQUIRED_UNASSIGNED`, `LINKED_ACTIVE`, `BLOCKED_CONFLICT`, `SATISFIED_BY_COMPLETED_REASSESSMENT`, or `DUPLICATE_DISPOSITIONED`; it must not return silent absence. Incompatible plurality is `TRIGGER COVERAGE CONFLICT — UNRESOLVED`.

### 3.12 Exact historical retrieval

Every finalized record must retain exact version references for the authoritative records it relied upon. In particular, an authorized Decision and its related Integration, Reassessment, and Interim Operating Disposition chain must collectively retain references sufficient to retrieve:

- Managed Configuration version;
- Value Input version;
- Value Input Acceptance/Selection version and material Evidence Applicability/lane-fitness basis;
- Risk Input version;
- Risk Input Acceptance/Selection version and material Evidence Applicability/lane-fitness basis;
- material Evidence and Evidence Applicability versions relied upon;
- Authority Records and Authority Gaps relied upon;
- Integrated Operating Boundary Snapshot;
- Decision Authorization Basis;
- relevant Role Assignments/delegations;
- accountable assignment/mechanism relationships and materiality or identity-continuity determinations relied upon;
- required Intervention and Learning relationships;
- exact Obligation Set/Obligation, Intervention, Completion Result, Completion Acceptance, replacement/reuse, Prerequisite Evaluation Basis, and Activation Authorization Versions relied upon for target activation;
- exact Trigger, Trigger Determination, Trigger-to-Reassessment Membership, Reassessment Trigger Set, grouping/compatibility, duplicate disposition, overlap/coordination, Trigger Coverage, Reassessment status/action, Interim Operating Disposition, and completion-basis Versions relied upon;
- predecessor/successor records.

Later correction, withdrawal, status change, or supersession must not change the historical reconstruction.

### 3.13 Accountable determination and relationship history

Every Configuration materiality or same-identity/new-identity determination must preserve:

- determination identity/version;
- exact Configuration identity/version or proposed change assessed;
- determination outcome and rationale;
- exact accountable Role Assignment version or explicitly governed accountable mechanism;
- effective time and recorded time;
- predecessor, correction, supersession, or withdrawal relationship where applicable; and
- affected Case, evidence, inputs, authority, controls, Decision, and routing references required by the substantive specification.

Every accountable assignment/designation or mechanism relied upon by a governed record or judgment must remain exactly reconstructable for the effective and recorded time at which it applied. Technical principal identity, software permission, edit access, or participation must not be substituted for the accountable relationship. Absence and incompatible plurality remain explicit historical outcomes.

## 3A. Prospective common integrity and semantic-era contract

### 3A.1 Adoption boundary and semantic contract identity

Every prospective authoritative Record Version, status event, relationship Version, or
determination that adopts this section must identify the exact semantic contract under which it was
created and must be interpreted. The logical identity contains:

- a stable **Semantic Contract ID** naming one owned contract/family;
- an immutable **Semantic Contract Version** naming the exact rules in force; and
- the owning specification/version or other accepted normative source.

Semantic contract identity is bound per immutable Version or event, not merely inferred from table,
deployment date, current software, Record ID, UI route, or latest specification. A stable Record may
span semantic contract Versions only when its owning substantive contract permits continuity and an
explicit cross-era successor relationship preserves the transition. Historical interpretation
always uses the contract bound to the historical fact.

A versioned semantic-contract catalog or equivalent must make each supported contract identity,
owner, interpretation source, allowed record families, compatibility adapters, and supported
successor transitions discoverable to authorized system operation. The catalog is integrity
metadata, not substantive authority and not a universal schema registry.

No contract or adapter may infer `newer semantic era wins`. Cross-era co-current facts may coexist.
The later owning substantive specification must define the exact eligibility, displacement,
compatibility, conflict, or coexistence rule for its scope. Without such a rule, incompatible
eligible facts return explicit conflict.

### 3A.2 Legacy interpretation and no silent fallback

Legacy v0.1 facts retain their original names, outcomes, scope, and semantics. In particular,
Fitness, Acceptance/Selection, Role Assignment, Case lifecycle, Trigger/Reassessment, and other
legacy records are not prospectively renamed or reinterpreted by a reader.

Where a legacy Version predates an explicit semantic-contract field, a catalog/adapter may map its
exact record family and supported persistence/specification revision to the original legacy
contract for interpretation. That immutable external mapping does not mutate the Version, assert
that the Version was created under the prospective envelope, or supply missing substantive facts.

An explicit bounded adapter may:

- read a named legacy contract through its original rules;
- produce a source-labelled compatibility representation for an authorized consumer; and
- retain the exact legacy Version and adapter contract/version as provenance.

An adapter does not create a prospective fact, fill a missing prospective field, establish
eligibility, or become write authority unless the later owning specification explicitly grants one
bounded effect. A failed prospective command or selector must not retry through legacy semantics,
another adapter, a UI label, or a permissive default. It returns the prospective failure unchanged.

### 3A.3 Prospective authoritative envelope

The common envelope is integrity vocabulary, not one giant mandatory record schema. An adopting
owning contract must use only the fields that carry meaning for its family and must define any
additional payload and guards. The envelope supports, as applicable:

- stable Record ID and immutable Record Version/event/relationship ID;
- record family/type and exact Semantic Contract ID/Version;
- owning Case ID where the family is Case-bound;
- immutable exact context set under Section 3A.4;
- effective time or half-open effective interval and recorded time;
- an explicit recorded-knowledge cutoff only where the owning contract makes it authoritative;
- attributable Actor or governed mechanism and the separately valid accountability/authority basis
  where required;
- typed predecessor, correction, amendment, supersession, withdrawal, cancellation, delegation, or
  other owning-contract relationship;
- exact source/provenance links;
- canonical payload representation/checksum where content equality, replay, transport, or audit
  requires it;
- access scope/policy reference; and
- family-owned eligibility metadata only where the owning contract defines its meaning.

Presence in the envelope does not establish the substantive validity of a payload, relationship,
Actor, source, or eligibility. Omitted inapplicable fields are not gaps. Missing required fields fail
the owning command without mutation.

### 3A.4 Exact context-set contract

An **Exact Context Set** binds a fact, judgment, action, query, or semantic transaction to the exact
basis it concerns. Every member contains:

- a controlled member role/purpose defined by the owning contract;
- record family/type;
- exact Record ID and Record Version ID; and
- semantic ordering information only when the owning contract declares order to carry meaning.

Membership is an unordered set by default. Storage, input, or display order has no meaning. When
order is substantive, the contract must define the ordered role and ordinal constraints; ordering
must not be inferred from timestamps or identifiers.

Exact duplicate members are invalid at commit rather than silently counted twice. Two Versions of
the same Record, incompatible typed roles, or contradictory members are rejected or returned as
explicit conflict unless the owning contract expressly permits them and defines their distinct
roles. The common layer does not decide Case/Configuration coherence; an adopting contract must
state those guards where required.

A persisted context set is immutable and canonically representable. Canonicalization must be
independent of storage/input order and include the member role, family, Record ID, Version ID, and
declared ordinal where applicable. If a checksum or independent Context Set ID is persisted, it is
computed from that canonical representation. The default is an embedded immutable component. A
separately identified Context Set Record is justified only when reuse, independent provenance,
authorization, or lifecycle/history is itself required by an accepted owning contract.

Access checks occur before a context set is composed, disclosed, or used to validate a command. An
inaccessible member cannot be used merely because a hidden relation exists. Ordinary output must
not leak its identity, count, type, conflict contribution, or existence. Authorized audit may expose
the exact set under its separate access basis.

Context membership never implies Applicability, responsibility, accountability, authority,
adequacy, reliance, materiality, priority, causality, comparability, or Decision. Those meanings
require their separately governed facts.

### 3A.5 Common selector framework

Every adopting record family that requires current selection must define in its owning contract:

1. the exact selection scope/key;
2. the eligibility predicate and required finalized/authorized state;
3. effective-time and optional recorded-knowledge-cutoff semantics;
4. permitted plurality or incompatibility conditions;
5. any authoritative precedence, supersession, delegation, or coordination relation;
6. stale, expired, withdrawn, cancelled, corrected, and superseded treatment; and
7. the family-specific meaning of vacancy/absence and conflict.

The common result shape is:

- exactly one eligible authoritative result where the contract requires one;
- explicit `NOT ESTABLISHED`/absence where none qualifies; or
- explicit `CONFLICT — UNRESOLVED` with all accessible incompatible candidates where more than one
  remains and no governing relation resolves them.

A contract that permits a set of compatible current facts must define their distinguishable scopes
and deterministic set result. The common layer never chooses by recency, record/version label,
specificity, breadth, strongest state, role hierarchy, semantic-contract version, display order,
row order, software permission, or convenience. A deterministic tie-break used only to render an
already determined set is not substantive selection.

### 3A.6 Non-authoritative read composition

A practitioner summary, current management position, attention view, participant view, derived work
view, or historical Case view is a **Read Composition** unless a later accepted contract explicitly
creates an authoritative Record. A read composition must:

- identify its query and composition-rule version;
- use exact visible source Versions and retain an authorized source manifest or equivalent trace;
- apply access and non-disclosure before selection, counting, grouping, conflict calculation, or
  labelling;
- preserve source absence, vacancy, conflict, uncertainty, and staleness rather than fabricate a
  favorable/current/completed state;
- support effective-time and recorded-knowledge-cutoff queries where its sources do;
- produce deterministic semantic output for identical visible source state, access context, query,
  and rule version; and
- be recomputable from authoritative sources.

Rendering, caching, export, notification, queue position, count, label, color, or generated summary
does not create completion, currentness, priority, responsibility, authority, or command basis. A
persisted cache or output manifest remains a non-authoritative projection and cannot be mutated back
into source truth. A downstream command must reconstruct and revalidate its own exact authoritative
context; a presentation label alone is never sufficient.

When access hides a source, the composition must not reveal that source through global counts,
blocker/conflict labels, participant lists, work queues, status wording, timing hints, or changed
output shape. Non-disclosing unavailable output must not falsely assert substantive absence where
the system cannot disclose that conclusion.

### 3A.7 Dual-time and historical reconstruction

Prospective concepts use the existing temporal discipline:

- **effective-at** asks which facts governed the subject at the requested effective time using the
  permitted knowledge basis; and
- **known-at** limits the source set to facts recorded by the requested cutoff.

Exact Decision-bound reconstruction starts with the exact Versions bound to the Decision, not a
current selector. A “best account now of then” may include a later-recorded correction effective at
that time, clearly labelled as later knowledge. A “what PAIM knew then” view excludes it. Neither
view rewrites the Decision's exact historical basis.

Cross-era reconstruction interprets every Version with its own bound Semantic Contract
ID/Version. A current adapter or contract must not reinterpret an earlier fact. Later quantitative
observations remain later knowledge and do not rewrite earlier estimates, targets, assessment
adequacy, reliance, or Decision basis. Later Responsibility, Work, Review, correction, or successor
facts likewise do not alter who was accountable or what was established at an earlier cutoff.

The common contract guarantees reconstruction only from authoritative data actually preserved and
linked under the owning contracts. It does not claim that PAIM knew unrecorded external facts or can
derive missing historical context.

### 3A.8 Semantic transaction and atomicity

A **Semantic Transaction** is the all-or-nothing commit boundary for one natural governed action
that may create multiple separate authoritative facts. It is not a workflow language. The adopting
command must bind:

- transaction/command identity and exact idempotency key;
- command Semantic Contract ID/Version;
- authenticated Actor and separately resolved accountability/authority where required;
- one exact canonical context/guard basis and its checksum where applicable;
- every intended fact, relationship, status event, and audit effect; and
- effective and recorded time rules.

All guards are evaluated against one consistent transaction basis. Every intended mutation commits
or none does. Stale context, absence, conflict, access denial, invalid authority/accountability, or
any write/audit failure leaves prior authoritative state unchanged and creates no partial domain
fact.

Exact replay with the same idempotency key, Actor, command contract, context checksum, and intent
returns the already committed outcome without duplicate mutation. Reuse of the key with different
identity, context, or intent fails explicitly. Concurrent incompatible attempts resolve
deterministically to one committed transaction plus explicit stale/conflict failure, or to no
commit; they never partially interleave.

Audit preserves a transaction-level relationship among outputs while retaining the separate
identity, contract, attribution, context, and history of every authoritative fact. Transaction
grouping must not collapse those facts into one substantive judgment.

### 3A.9 Migration, compatibility, and recovery

- Every v0.1.0 Record, Version, relationship, checksum, and audit fact remains immutable historical
  evidence under its original contract.
- Prospective writes use a new semantic contract only after the owning Gate 2–6 specification and
  implementation cutover are independently accepted.
- No bulk rename/rewrite, UI-state inference, numeric/prose parsing, or synthesized prospective fact
  is permitted merely for migration convenience.
- Every adapter is explicit, versioned, bounded to named source/consumer contracts, read-safe, and
  non-authoritative unless an owning specification grants a precise effect.
- Every supported prior persistence revision must have an explicit upgrade, compatibility,
  reconstruction, and recovery path before implementation ships.
- Upgrade, rollback, backup/restore, repair, or disaster recovery preserves semantic-contract
  identity and cannot reinterpret data according to the software version performing recovery.

Corrections or successors across eras preserve both Versions and an explicit typed relationship.
The owning later contract decides whether cross-era continuity is permitted and how eligibility is
resolved. The integrity layer supplies no era precedence and no silent fallback.

### 3A.10 Access and non-disclosure

Access is evaluated before exact-context construction, selector evaluation visible to the caller,
read composition, historical reconstruction, adapter output, or command use. A command cannot rely
on an inaccessible Record merely because the system knows a hidden relationship exists.

Conflict and absence output is access-contextual. Ordinary views must not reveal hidden identity,
fact, count, scope, role, timing, candidate plurality, or conflict contribution. This rule does not
authorize a false substantive statement; where neither disclosure nor a complete determination is
permitted, return a non-disclosing unavailable/insufficient-access result defined by the access
contract.

An authoritative mutation requiring a complete context or selector result must fail without
mutation when the Actor cannot access every contract-required source. It must not ignore hidden
facts, treat them as absent, or disclose which hidden fact prevented the action.

Cross-era adapters apply every applicable source and consumer restriction and use the stricter
result where they differ. Historical and technical/audit views expose additional detail only under
explicit authorization. Gate 1 does not redesign identity, authentication, sessions, software
permission, or deployment.

### 3A.11 Product-to-integrity discipline and later ownership

| Common concept | Practitioner/product need | Why common | Explicitly does not mean | Later substantive owner | Do not ordinarily expose |
|---|---|---|---|---|---|
| Semantic contract identity | Preserve what a fact meant when created | Every evolving authoritative family needs interpretation stability | newer era wins, migration, or new substantive fact | each Gate 2–6 owning specification | era keys, registry mechanics |
| Authoritative envelope | Give future facts consistent identity, time, attribution, provenance, and history vocabulary | These are shared integrity properties | every field is mandatory or payload is valid | each owning record family | envelope/schema machinery |
| Exact context set | Carry the precise basis across tasks, sessions, and commits | Multiple later concepts bind several exact Versions | Applicability, authority, responsibility, adequacy, materiality, causality, or Decision | each owning contract defines member roles/coherence | raw IDs and canonicalization |
| Selector framework | Show one current fact, explicit absence, or conflict without incidental winners | The outcome mechanics recur across families | a universal eligibility or precedence rule | each owning contract defines scope, eligibility, and relations | query algorithms and tie-break mechanics |
| Read composition | Provide current position, attention, work, and historical views without master-record sprawl | Access/traceability/non-authority rules are cross-cutting | source truth, command authority, priority, or completion | later read models and their source families | source manifests unless inspecting history |
| Dual-time reconstruction | Explain then-known versus now-known history | Every evolving family needs the same temporal discipline | knowledge of unrecorded facts or hindsight rewrite | each family supplies exact preserved sources | timestamp/query controls in ordinary work |
| Semantic transaction | Present one natural action while preserving several exact facts atomically | Atomicity/idempotency/audit are cross-cutting | workflow engine or merged substantive judgment | later command contracts define guards and outputs | transaction IDs and write choreography |

Gate 2 owns Responsibility kinds/assignment; Gate 3 owns Case continuity; Gate 4 owns Case Work;
Gate 5 owns Review Timing; and Gate 6 owns readiness, assessment adequacy, reliance, and quantitative
Value/Risk payloads. Until each gate is accepted, those semantics remain unresolved and current
v0.1 contracts remain controlling.

## 4. Integrated Operating Boundary contract

### 4.1 Boundary Snapshot identity

Every boundary used by an authorized Decision must be a finalized, immutable **Integrated Operating Boundary Snapshot** with:

- Boundary Snapshot ID;
- Boundary Snapshot Version ID;
- Case ID;
- exact Managed Configuration ID/version;
- exact Integration ID/version;
- status;
- recorded time;
- effective interval;
- boundary owner/integrator;
- predecessor/successor boundary where applicable;
- structured clauses;
- narrative clauses/rationale;
- unresolved or indeterminate comparison items;
- Decision relationship(s) established by immutable Decision records after authorization.

The Boundary Snapshot may be embedded in an Integration or Decision implementation, but it remains separately identifiable and retrievable by the fields above. The Decision references the already-finalized Snapshot; establishing that relationship must not mutate the Snapshot.

### 4.2 Boundary clause identity

Each material boundary clause has a stable Clause ID within the Boundary Snapshot and identifies:

- clause type;
- permitted, excluded, required, limited, conditional, or indeterminate effect;
- configuration element or other target reference where available;
- exact control, authority, data, population, threshold, capacity, or operating-condition reference where the system is expected to test the clause;
- structured value/operator/unit where applicable and meaningful;
- narrative meaning and rationale;
- provenance from Value, Risk, authority, constraint, control dependency, or management judgment;
- verification mode;
- consequence of breach or inability to verify where defined.

### 4.3 Minimum structured boundary references

The Boundary Snapshot must structurally identify, when material to the decision:

- permitted activity/scope references;
- explicit exclusion references;
- required Control IDs/versions or exact control definitions;
- maximum or otherwise limited AI authority;
- required human authority, review, approval, override, or escalation condition;
- material Authority Record/Gap conditions;
- effective interval.

Threshold, capacity, information/data, population, provider/model, geography, and operating-condition clauses require structured references when PAIM expects the platform to compare, monitor, or test them. A narrative-only clause is permitted when its application inherently requires accountable human judgment, but it must be marked as such.

### 4.4 Verification modes

Each material clause is assigned one verification mode:

- **mechanically testable** — the system has structured evidence sufficient to evaluate the clause;
- **human determination required** — an accountable actor must determine and record whether the clause is satisfied;
- **external determination required** — an identified external authority/system provides the determination;
- **indeterminate** — current evidence does not support a determination.

The verification mode does not express confidence or a universal score.

### 4.5 Mechanical checks

The system may mechanically determine only what the structured clause and current evidence support, including:

- exact configuration/version match;
- presence of required control references and current control status where authoritative status exists;
- prohibited or permitted enumerated scope;
- typed AI/human authority limits;
- effective-period validity;
- threshold/capacity comparison where value, unit, and operator are defined;
- presence of required Authority Records or explicit Authority Gaps;
- existence of required human/external determinations.

Mechanical conformance does not authorize operation and does not replace substantive Value, Risk, authority, or management judgment.

### 4.6 Human determinations

A human determination must preserve:

- Boundary Snapshot and Clause ID;
- determination;
- actor and applicable role/authority;
- recorded/effective time;
- evidence considered;
- rationale;
- expiry or review condition where relevant.

The platform must not translate missing human determination into satisfaction.

### 4.7 Boundary comparison

Comparison occurs clause-by-clause against exact Boundary Snapshot versions.

Permitted overall outcomes are:

- **UNCHANGED** — no substantive clause changes;
- **NARROWED** — at least one permission/scope is reduced or one requirement is strengthened, and none is broadened;
- **BROADENED** — at least one permission/scope is expanded or one requirement is weakened;
- **MIXED** — some clauses narrow and others broaden;
- **INDETERMINATE** — evidence or mapping is insufficient to classify one or more material changes.

`MIXED` and `INDETERMINATE` require accountable review. They must not be treated as unchanged. A broadened or mixed boundary requires an authorized successor/amendment Decision and evidence/authority appropriate to the changed scope.

### 4.8 Boundary immutability and breach

An authorized Boundary Snapshot is immutable. Any substantive clause change creates a successor Boundary Snapshot and requires a successor/amendment Decision.

A breach may be mechanically detected or determined by an accountable human/external source. The breach record must reference the exact Boundary Snapshot and Clause ID(s). An indeterminate clause is not automatically a breach or compliance; it is a management-attention condition requiring the specified determination or reassessment.

## 5. Canonical PAIM case lifecycle transition contract

### 5.1 Single current lifecycle state

Each active Case has exactly one current lifecycle state at an effective time. Lifecycle state is distinct from AI operating state, configuration status, intervention status, reassessment status, and Interim Operating Disposition.

Every transition creates an immutable Lifecycle Transition Event containing:

- Transition Event ID;
- Case ID;
- source state;
- target state;
- recorded/effective time;
- actor and role or authorized mechanism;
- basis/trigger;
- guard results;
- exact subordinate record versions relied upon;
- rationale where human judgment is required.

### 5.2 Authorized transition actors

- The **Case Owner** or authorized case-workflow mechanism may advance or return workflow states after mandatory guards are satisfied.
- Only an established **Decision Authority** acting through a valid Decision Authorization Basis may create the authorized Decision that permits transition to `DECIDED`.
- Closure requires the closure authority identified by the Case specification and a valid authorization basis for the closure decision where closure changes operation or substantive management conditions.
- Supersession requires an identified successor and the authority/mechanism responsible for establishing the supersession.
- A system mechanism may detect guard satisfaction, raise a trigger, or propose a transition. It must not make a substantive materiality, authority, boundary, or management judgment unless an authorized organizational rule explicitly supplies that determination and is recorded as the basis.

### 5.3 Allowed transition table

No transition is allowed unless listed below.

| Source | Allowed target | Mandatory guard and basis |
|---|---|---|
| `OPEN` | `CONFIGURATION_DEFINED` | A Managed Configuration draft/finalized version sufficiently bounds the management object; Case Owner records the basis. |
| `OPEN` | `CLOSED` | Intake is withdrawn, duplicate, or no longer a management question; closure reason/authority and unresolved-item treatment are recorded. This is the only ordinary pre-analysis closure skip. |
| `OPEN` | `SUPERSEDED` | A named successor Case assumes the management question and the supersession relationship/authority are recorded. |
| `CONFIGURATION_DEFINED` | `EVIDENCE_ANALYSIS` | Exact configuration version exists and is sufficiently stable for evidence and analysis binding. |
| `CONFIGURATION_DEFINED` | `CLOSED` | Authorized withdrawal/retirement with closure requirements satisfied. |
| `CONFIGURATION_DEFINED` | `SUPERSEDED` | Named successor and supersession basis/authority recorded. |
| `EVIDENCE_ANALYSIS` | `CONFIGURATION_DEFINED` | Configuration is materially incomplete/changed; a new or revised configuration version is identified. |
| `EVIDENCE_ANALYSIS` | `READY_FOR_INTEGRATION` | All readiness guards in §5.4 are satisfied for exact versions. |
| `EVIDENCE_ANALYSIS` | `CLOSED` | Authorized withdrawal/retirement with closure requirements satisfied. |
| `EVIDENCE_ANALYSIS` | `SUPERSEDED` | Named successor and supersession basis/authority recorded. |
| `READY_FOR_INTEGRATION` | `EVIDENCE_ANALYSIS` | A selected input is withdrawn/refresh-required, configuration mismatch appears, or required evidence/authority treatment becomes incomplete. |
| `READY_FOR_INTEGRATION` | `DECISION_PENDING` | Integration has begun for the exact selected configuration and frozen inputs. |
| `READY_FOR_INTEGRATION` | `CLOSED` | Authorized withdrawal with closure requirements satisfied. |
| `READY_FOR_INTEGRATION` | `SUPERSEDED` | Named successor and supersession basis/authority recorded. |
| `DECISION_PENDING` | `READY_FOR_INTEGRATION` | Integration requires rework but selected inputs remain ready/current. |
| `DECISION_PENDING` | `EVIDENCE_ANALYSIS` | Input/configuration/evidence refresh is required. |
| `DECISION_PENDING` | `DECIDED` | Finalized Integration and Boundary Snapshot exist; an authorized Decision with valid Decision Authorization Basis is effective. |
| `DECISION_PENDING` | `CLOSED` | Proposed decision is withdrawn and closure requirements are satisfied; no unrecorded authorization is implied. |
| `DECISION_PENDING` | `SUPERSEDED` | Named successor and supersession basis/authority recorded. |
| `DECIDED` | `INTERVENTION_IN_PROGRESS` | The Decision identifies one or more interventions that are prerequisites or material implementation actions. |
| `DECIDED` | `OPERATING_OBSERVING` | Current target operation conforms to the exact authorized Decision/Configuration/Boundary; one exact Obligation Set yields `SATISFIED` or explicit `NOT_REQUIRED`; and valid Activation Authorization plus exact Prerequisite Evaluation Basis are retained. |
| `DECIDED` | `CLOSED` | Authorized Decision discontinues/retires the use or otherwise authorizes closure with no continuing observation requirement. |
| `DECIDED` | `SUPERSEDED` | The current or an authorized successor/amendment Decision establishes the named successor Case, effective transfer/end of operation under this Case, and preserved Decision/Case relationships. |
| `INTERVENTION_IN_PROGRESS` | `OPERATING_OBSERVING` | All required-before obligations are accepted complete or the explicit set is `NOT_REQUIRED`; target Configuration/Boundary alignment is confirmed; and valid Activation Authorization plus exact Prerequisite Evaluation Basis are retained. |
| `INTERVENTION_IN_PROGRESS` | `REASSESSMENT_DUE` | A prerequisite is blocked, failed, materially incomplete, changes the configuration, or creates another material trigger. |
| `INTERVENTION_IN_PROGRESS` | `CLOSED` | The current or an authorized successor/amendment Decision discontinues/retires the use and closure requirements are satisfied. An Interim Operating Disposition may suspend but cannot permanently discontinue or close. |
| `INTERVENTION_IN_PROGRESS` | `SUPERSEDED` | The current or an authorized successor/amendment Decision establishes the named successor, treatment of incomplete interventions, effective transfer/end of operation, and supersession authority. |
| `OPERATING_OBSERVING` | `REASSESSMENT_DUE` | A material trigger is recorded. |
| `OPERATING_OBSERVING` | `CLOSED` | Authorized closure/discontinuation and closure requirements are satisfied. |
| `OPERATING_OBSERVING` | `SUPERSEDED` | The current or an authorized successor/amendment Decision establishes the named successor, effective transfer/end of operation, and supersession authority. |
| `REASSESSMENT_DUE` | `REOPENED` | Reassessment is opened with trigger, owner, current Decision/configuration, and immediate operating disposition recorded or explicitly unnecessary. |
| `REASSESSMENT_DUE` | `OPERATING_OBSERVING` | An accountable materiality determination concludes the trigger is immaterial; the current Decision, Boundary Snapshot, conditions, and operating state remain unchanged; rationale is recorded. |
| `REOPENED` | `CONFIGURATION_DEFINED` | Configuration identity/version requires material work before analysis. |
| `REOPENED` | `EVIDENCE_ANALYSIS` | Configuration remains sufficiently defined but one or both analytical/evidence legs require refresh. |
| `REOPENED` | `READY_FOR_INTEGRATION` | Configuration and existing/current successor inputs satisfy all readiness guards without analytical refresh. This is the only allowed reopened-state analytical skip. |
| `REOPENED` | `INTERVENTION_IN_PROGRESS` | Completed Reassessment creates a Decision Confirmation leaving the authorized Decision/Boundary unchanged, but a non-substantive intervention within that Decision remains required. |
| `REOPENED` | `OPERATING_OBSERVING` | Completed Reassessment creates a Decision Confirmation leaving the authorized Decision, operating state, Boundary Snapshot, and substantive conditions unchanged; the exact Obligation Set yields `SATISFIED` or explicit `NOT_REQUIRED`; valid Activation Authorization and Prerequisite Evaluation Basis are retained; and any Interim Operating Disposition is ended or operation is aligned with it. |
| `REOPENED` | `CLOSED` | Completed reassessment produces an authorized successor/amendment Decision that discontinues/closes, or explicitly confirms closure is appropriate under an existing discontinuation Decision. |
| `REOPENED` | `SUPERSEDED` | Completed reassessment produces an authorized successor/amendment Decision establishing the named successor Case, effective transfer/end of operation, and supersession authority. |
| `CLOSED` | `REOPENED` | A new material trigger makes the same management object active again; reopening authority, current/new configuration, prior Decision relationship, and operation status are recorded. |
| `SUPERSEDED` | none | Terminal for active management. New work occurs in the named successor Case. |

### 5.4 Mandatory readiness and decision guards

Before `READY_FOR_INTEGRATION`, the system must confirm exact-version presence and compatibility of:

- exactly one governing Managed Configuration for the Case/effective time, with proposed/experimental/alternative/fallback Configurations ineligible as substitutes;
- one selected frozen Value Input;
- one selected frozen Risk Input;
- matching configuration bindings;
- contributing boundaries and uncertainty;
- provenance;
- material established constraints;
- all material Authority Gaps, including Decision Authority Gap, explicitly represented;
- Decision Authority identified or explicitly unresolved.

Decision Authority may remain unresolved at `READY_FOR_INTEGRATION`, but must be resolved through a valid Decision Authorization Basis before `DECIDED`.

Before `DECIDED`, the system must confirm:

- completed Integration Record;
- finalized Boundary Snapshot;
- exact frozen input and configuration linkage;
- classified material uncertainty;
- established constraints and explicit Authority Gaps;
- Decision Authorization Basis valid for the Decision scope/effective time;
- decision does not exceed the Boundary Snapshot;
- required interventions and learning/reassessment relationships are identified.

### 5.5 Subordinate record effects

- Withdrawal, supersession, or refresh-required status of a selected input before authorization invalidates readiness and returns the Case to `EVIDENCE_ANALYSIS` or `READY_FOR_INTEGRATION` as the table permits.
- The same status change after authorization preserves the historical Decision basis and creates a reassessment trigger where material.
- Expiry, revocation, conflict, or scope failure of Decision Authority before authorization blocks `DECIDED`.
- The same authority change after authorization preserves historical validity and creates a reassessment trigger where it may affect current operation.
- A blocked, failed, cancelled, or materially partial prerequisite Intervention prevents the target configuration from becoming authorized operation and creates management attention/reassessment as specified.
- `COMPLETED` Intervention status, evidence presence, or Completion Acceptance alone never authorizes target operation.
- An incomplete `REQUIRED_AFTER_OPERATION` item does not block initial activation only under exact Decision permission; an incomplete `OPTIONAL` item does not block. Neither changes the Decision silently.
- Cancellation, failure, or inconclusive completion of a Learning Item does not silently resolve uncertainty or change a Decision.
- Supersession of a Decision changes current selection prospectively but never changes the historical record used for its effective period.

### 5.6 Coexisting operation and intervention

Case lifecycle state `INTERVENTION_IN_PROGRESS` describes the management workflow. It does not imply that all operation has stopped.

While intervention toward a target configuration is in progress:

- any continuing operation remains governed by the prior/current authorized Decision and Boundary Snapshot;
- the target configuration must not operate until all prerequisite interventions are accepted complete and an authorized Decision/Boundary permits it;
- a Decision or Interim Operating Disposition must explicitly authorize fallback, narrowed continuation, partial suspension, or full suspension;
- the system must display both the currently operating configuration/Decision and the target configuration/intervention state.

Target activation is one semantic transaction: guard evaluation, immutable Prerequisite Evaluation Basis, valid Activation Authorization, activation/operating event, and Lifecycle Transition Event must commit together or not at all. Failure leaves no partial authoritative activation state.

Activation authority is either an applicable Decision Authority acting explicitly or a genuine governed organizational activation mechanism explicitly pre-authorized in the exact Decision Authorization Basis with exact rule/version/scope/authority retained. A software checklist, technical rule, ownership, permission, or technical principal is never that mechanism by itself.

**Activation Authorization** is an authoritative record with stable identity and immutable Versions. It binds the exact Decision Version, target Configuration Version, operating-state value, Boundary Snapshot Version, Prerequisite Evaluation Basis Version, activation effective/recorded time, actor or genuine governed organizational mechanism, exact authority basis/rule Version, scope, limits, and predecessor/correction/supersession history. Its authority must be valid at activation effective time.

### 5.7 Coexisting operation and reassessment

Case states `REASSESSMENT_DUE` and `REOPENED` describe management workflow. Current operation is separately governed by:

1. the current authorized Decision and Boundary Snapshot; and
2. any current authorized Interim Operating Disposition.

Opening reassessment neither silently extends permission nor automatically suspends operation. The immediate operating effect must be explicit under §7.

### 5.8 Closure and reopening

Closure does not delete history and does not by itself revoke or create authority outside the closure Decision.

A closed Case may reopen only when continuity of the management object remains meaningful and the transition table guard is met. Reopening creates a new Reassessment/transition chain and never edits the closure record. A superseded Case is not reopened; work continues through its named successor.

## 6. Decision Authorization Basis

### 6.1 Required authorization record

Every authorized Decision version must have exactly one complete **Decision Authorization Basis** record or immutable authorization bundle identified as one logical record.

Minimum content:

- Authorization Basis ID/version;
- exact Decision ID/version;
- exact Decision Authority identity;
- exact active Role Assignment ID/version and/or committee/organizational authority mechanism;
- applicable Authority Record ID/version establishing the decision right, or an explicit reference to another legitimate organizational authority mechanism;
- delegation chain where used;
- authorized scope and limits;
- configuration, operating state, boundary, decision type, organizational unit, and other scope dimensions needed to demonstrate coverage;
- effective period of each relied-upon authority/assignment/delegation;
- authorization event identity, actor/mechanism, recorded time, and effective time;
- conditions, dissent, or exception where required;
- Authority Gaps considered, including any bounded-proceed determination;
- historical predecessor/successor where authorization is corrected or superseded.
- any pre-authorized activation mechanism, which must identify a genuine governed organizational authority mechanism and retain its exact rule/version, scope, authority source, limits, and effective period.

A software checklist, technical rule, workflow transition, Case Owner, Intervention Owner, administrator permission, or technical principal is not a governed organizational activation mechanism and cannot be recorded as one merely to automate release.

### 6.2 Authorization validity

At the Decision effective time, the system must be able to demonstrate that:

- the authority mechanism exists and is established/current;
- the Decision Authority identity is bound to it;
- every delegation link is active, in scope, and within its limits;
- the Decision scope does not exceed the authority scope;
- no required link is expired, revoked, superseded, or unresolved;
- committee/quorum or organization-specific mechanism requirements are satisfied where applicable;
- the authorization event binds the exact immutable Decision version and Boundary Snapshot.

If more than one incompatible authorization basis appears current, the result is **DECISION AUTHORIZATION CONFLICT — UNRESOLVED** and the Case cannot become `DECIDED`.

### 6.3 Decision Authority Gap

`DECISION AUTHORITY UNRESOLVED` is a required classification of the existing Authority Gap record family, not a separate informal flag or parallel gap system.

The Authority Gap must identify:

- the Decision or proposed Decision requiring authority;
- missing authority mechanism, Role Assignment, delegation, scope, or limit;
- whether analysis/integration may continue;
- whether any existing operation may continue under a prior valid Decision;
- owner for resolution;
- status and resolution linkage.

If authority to make the current proposed Decision is unresolved, the Case cannot become `DECIDED`.

### 6.4 Bounded-proceed determination

An Authority Gap concerning some broader, different, or external authority question may coexist with a narrower Decision only when:

- the narrower Decision has its own fully valid Decision Authorization Basis;
- that Decision Authority's scope explicitly covers making the bounded-proceed determination;
- the unresolved question and blocked broader/different Decision are identified;
- the exact narrower scope, Boundary clauses, operating state, rationale, conditions, and review trigger are recorded;
- the Decision does not claim to resolve the Authority Gap;
- the unresolved gap remains current and visible until resolved, superseded, or rendered immaterial through an authorized reframing.

No Case Owner, integrator, analyst, administrator, or Authority Gap owner may authorize bounded proceeding merely by recording `may proceed` unless separately established as the applicable Decision Authority.

If the Authority Gap concerns the authority to make even the narrower Decision, no bounded-proceed determination is available.

### 6.5 Historical preservation

Later expiry, revocation, delegation change, or Authority Gap resolution must not alter the historical Decision Authorization Basis. It may trigger reassessment of current operation and require a successor authorization/Decision.

## 7. Interim Operating Disposition during reassessment

### 7.1 Record identity and purpose

An **Interim Operating Disposition** is an authoritative, time-bounded record governing operation while a material trigger is triaged or reassessment is incomplete.

It is not an amendment to the current Decision and must not silently become a permanent operating state.

Minimum content:

- Interim Disposition ID/version;
- Case ID;
- exact current Decision ID/version;
- exact current Boundary Snapshot ID/version;
- Reassessment Trigger and Reassessment IDs where available;
- exact operating configuration ID/version;
- authority basis satisfying §6 for the disposition;
- disposition type;
- permitted operating effect;
- interim Boundary Snapshot or exact restrictive clauses;
- rationale and evidence/trigger considered;
- recorded time;
- effective time;
- mandatory expiry time or review/resolution trigger;
- status;
- predecessor/successor disposition;
- final Reassessment outcome/Decision linkage when completed.

### 7.2 Permitted operating effect

An Interim Operating Disposition may:

- continue the current Decision unchanged for a stated short period;
- narrow scope or add restrictive conditions;
- invoke an already authorized fallback;
- partially suspend operation;
- fully suspend operation;
- require immediate remediation within the current Decision boundary.

It must not:

- broaden the Integrated Operating Boundary;
- authorize a stronger operating state;
- remove a required control;
- resolve an Authority Gap;
- permanently change a substantive Decision condition;
- authorize a different configuration beyond existing authority and evidence.

Any broadened, stronger, or substantively different operation requires an authorized successor/amendment Decision.

### 7.3 Authority and currentness

The disposition must be authorized by a Decision Authority or legitimate emergency/interim authority whose Authorization Basis covers the exact disposition scope and effective period.

The disposition is current only under the common selection rule in §3.11 and only while its expiry/review condition has not occurred.

If overlapping current dispositions exist, the platform must not choose the newest or most permissive. Operation must not exceed the intersection of the current Decision Boundary and every independently valid restrictive disposition while the conflict is escalated. If the intersection cannot be determined, operation is suspended for the affected scope pending an authorized determination.

### 7.4 Expiry and completion

Every disposition must end through:

- stated expiry;
- authorized withdrawal;
- authorized successor disposition;
- explicit Reassessment confirmation of the unchanged Decision; or
- an authorized successor/amendment Decision.

An expired disposition cannot silently continue. Expiry with reassessment incomplete creates management attention and requires a new authorized disposition or suspension for affected operation.

### 7.5 Completed Reassessment outcome invariant

Every completed Reassessment must produce exactly one of:

1. **Decision Confirmation** — an immutable confirmation record stating that the existing authorized Decision, operating state, Boundary Snapshot, and substantive conditions remain unchanged; or
2. **Authorized successor/amendment Decision** — a new immutable Decision version with its own Boundary Snapshot and Decision Authorization Basis.

The confirmation record must identify:

- Reassessment ID/version;
- unchanged Decision ID/version;
- evidence, authority, configuration, Value, Risk, control, uncertainty, and boundary reviews performed;
- rationale for confirmation;
- accountable Reassessment Owner/confirmer and any Decision Authority approval required by the current Decision or organizational authority mechanism;
- recorded/effective time;
- next triggers/learning.

A Decision Confirmation does not create new authority, extend the effective period of the existing Decision, broaden its Boundary, or cure an expired/withdrawn authorization basis. If continued operation requires any such change, an authorized successor/amendment Decision is required.

Immediately before completion, the platform prospectively revalidates the exact current Decision and governing Configuration, Reassessment Version and Trigger Set, Trigger Determinations/coverage, grouping/coordination and overlap, Reassessment Owner accountability/delegation/mechanism, and required Decision/confirmation authority at the completion effective time and knowledge cutoff.

Completion is one semantic transaction: the completed Reassessment Version/status, exactly one Confirmation or successor/amendment Decision path, disposition ending effects, Trigger coverage outcomes, and allowed lifecycle transition become authoritative together or not at all. Zero or both outcome paths, blocked/unresolved inputs, stale expected Versions, or unresolved overlap commits no partial completed state.

One concurrent Reassessment's unchanged-Decision Confirmation does not close another. If a successor/amendment Decision becomes effective, an open predecessor-bound Reassessment remains historical analysis but cannot complete as current. Prospective continuation requires explicit accountable coordination, a new/successor Reassessment identity bound to the current Decision/Configuration, exact Trigger carry-forward relationships, and explicit predecessor cancellation/supersession. Future-effective successors affect eligibility only from their effective time.

### 7.6 Resolution of “confirm with conditions”

“Confirm with conditions” is permitted without a successor Decision only when the changed item is operational implementation detail that does not change:

- selected operating state;
- Integrated Operating Boundary;
- permitted or excluded activity;
- required control;
- AI or human authority;
- material authority condition;
- substantive Decision condition/limit;
- configuration governed by the Decision.

If any of those changes, the result is an authorized successor/amendment Decision. The prior Decision remains immutable.

Changes to Intervention scheduling, ownership, or implementation method may be recorded without a successor Decision only when they remain within the existing Decision and Boundary and do not weaken a substantive condition. The rationale for treating the change as non-substantive must be recorded in the Reassessment.

## 8. Explicit cross-cutting invariants

The PAIM system must enforce or surface violation of the following invariants:

1. Every authoritative record has a stable Record ID, and every finalized content version has a distinct immutable Record Version ID.
2. Finalized, frozen, authorized, issued, or decision-relied-upon content is never edited in place.
3. Current selection is evaluated for explicit scope and time; absence and conflict remain explicit.
4. No two incompatible authoritative versions may silently govern the same subject, scope, and effective time.
5. Every finalized Integration binds exact selected frozen Value Input, Risk Input, and Managed Configuration versions.
6. Every authorized Decision binds exact Integration, Boundary Snapshot, configuration, frozen-input, authority, and authorization-basis versions.
7. Every authorized Decision remains exactly reconstructable after later corrections, amendments, withdrawals, or supersession.
8. A Decision never authorizes operation outside its Managed Configuration, Boundary Snapshot, established authority, or required-control conditions.
9. A material boundary change always creates a successor Boundary Snapshot and authorized successor/amendment Decision.
10. A Case becomes `DECIDED` only through a valid Decision Authorization Basis effective for the exact Decision scope.
11. `AUTHORITY UNRESOLVED` and `DECISION AUTHORITY UNRESOLVED` never imply permission.
12. Bounded proceeding is authorized only by an established Decision Authority whose own scope covers the narrower Decision and the bounded-proceed determination.
13. Opening reassessment never silently changes or extends operating permission.
14. Any interim operating change is governed by a time-bounded authorized Interim Operating Disposition or a successor/amendment Decision.
15. Every completed Reassessment produces either explicit unchanged-Decision confirmation or an authorized successor/amendment Decision.
16. A change to operating state, Integrated Operating Boundary, or substantive Decision condition never mutates the prior Decision.
17. Current operation during intervention or reassessment remains traceable to the exact Decision, Boundary Snapshot, configuration, and any Interim Operating Disposition that govern it.
18. The Management Register derives current facts under the same scope/time/current-selection rules and never overrides authoritative records.
19. Value and Risk Inputs remain separately attributable, immutable when frozen, and independently refreshable throughout integration and reassessment.
20. Every Configuration identity has exactly one owning Case, and every Case/effective time has at most one governing Configuration.
21. Governing-Configuration selection returns one exact version, explicit absence, or explicit conflict; a purpose-labeled alternative never satisfies governing currentness.
22. Independent concurrent governing Configurations use separately linked Cases in PAIM v0.1 rather than a plural governing set within one Case.
23. Multiple compatible role performers may coexist, but every obligation requiring accountability resolves to one accountable assignment/mechanism, explicit vacancy, or explicit conflict.
24. Broad and narrow Role Assignments have no implicit precedence; displacement requires an explicit history-preserving relationship or later accepted policy.
25. Configuration materiality and identity-continuity determinations preserve exact accountable provenance, rationale, effective/recorded time, and history.
26. Technical principal, PAIM actor, Role Assignment, accountability, software permission, and Decision Authority remain distinct; Decision Authority still requires the complete §6 Authorization Basis.
27. Analytical readiness is distinct from lane acceptance; only the first valid acceptance semantic commit may atomically freeze and select an unfrozen Input Version.
28. Every Integration use selects exactly one accepted/frozen Value Input and one accepted/frozen Risk Input, each with an exact use-specific Acceptance/Selection Version, or exposes absence/conflict independently by lane.
29. Reuse of a frozen Input requires a new use-specific acceptance/fitness judgment and never refreezes or rewrites the Input.
30. Each lane acceptance and each Evidence Applicability judgment resolves exact target-context accountability as one assignment/mechanism, vacancy, or conflict; unrelated-scope accountability is ineligible and broad/narrow assignments have no implicit precedence.
31. Evidence Applicability has stable identity, immutable Versions, exact Evidence/target Versions, assessed scope, outcome, rationale, assessor, accountable provenance, dual time, and preserved correction/supersession/withdrawal history.
32. Normative Applicability outcomes are `APPLICABLE`, `CONDITIONALLY_APPLICABLE`, `PARTIALLY_APPLICABLE`, `NOT_APPLICABLE`, and `INDETERMINATE`; `REFRESH REQUIRED` is status/attention and conflict is a derived selection result.
33. A new target identity/version requires a new Applicability judgment; prior applicability is provenance only and no universal expiry or silent carry-forward applies.
34. Later Input/Evidence/Applicability change never rewrites a historical Integration or Decision basis; it changes prospective eligibility or creates attention/reassessment where material.
35. Every authorized Decision has one exact versioned Intervention Obligation Set; requirement type is Decision/target-Configuration specific and is exactly `REQUIRED_BEFORE_OPERATION`, `REQUIRED_AFTER_OPERATION`, or `OPTIONAL`.
36. Intervention implementation status, Completion Result/evidence, Completion Acceptance, prerequisite satisfaction, and Activation Authorization are distinct; none silently creates another.
37. Every required-before obligation is satisfied only by exact `COMPLETED` work, an eligible exact all-`MET` Completion Result, and one eligible `ACCEPTED` Completion Acceptance.
38. Required-before aggregation is all-of and returns only `SATISFIED`, `NOT_REQUIRED`, `NOT_ESTABLISHED`, `INCOMPLETE`, `BLOCKED`, or `CONFLICT`, retaining all contributing diagnostics.
39. `NOT_REQUIRED` requires an explicit eligible Obligation Set containing zero required-before obligations; absence never means not required.
40. Completion Acceptor accountability resolves for exact Intervention/Decision/target-Configuration/owning-Case targets as one assignment/mechanism, vacancy, or conflict; ownership or software permission is not acceptance authority.
41. Fallback, remediation, replacement, and reuse operate only through exact history-preserving relationships and never avoid a successor Decision when substantive Decision/Boundary/Configuration/state conditions change.
42. Target activation retains an immutable exact Prerequisite Evaluation Basis and valid Activation Authorization; satisfied prerequisites alone never authorize operation.
43. A pre-authorized activation mechanism is valid only as a genuine governed organizational authority mechanism recorded in the exact Decision Authorization Basis with rule/version/scope/authority provenance; software logic never self-authorizes.
44. Activation guard evaluation, Prerequisite Evaluation Basis, Activation Authorization, operating event, and Lifecycle Transition Event commit atomically.
45. Every successor/amendment Decision has its own Obligation Set; prior completion reuse requires exact accountable continued-validity determination and never carries silently.
46. Later role, Evidence, Intervention, Acceptance, obligation, replacement, or Decision change never rewrites a historical activation basis; future eligibility remains prospective and fail-closed.
47. Every finalized Reassessment Version binds one complete immutable exact Trigger Set; membership changes create successor Reassessment and relationship Versions rather than mutation.
48. Trigger/Reassessment membership is many-to-many only through exact versioned relationships, distinguishable scope, and required accountable grouping/coordination.
49. Exact replay does not create another Trigger; source/content similarity never establishes duplicate identity, grouping, coverage, or a winner.
50. Every eligible Trigger requiring reassessment has one compatible explicit coverage result or explicit coverage conflict and never disappears from authoritative queries.
51. `CANCELLED` and `SUPERSEDED` Reassessment actions are accountable, prospective, history-preserving, and atomically preserve/disposition every unresolved Trigger; neither occurs automatically.
52. Reassessment merge/absorption does not exist in v0.1.
53. Concurrent Reassessments coexist only for mechanically disjoint scope or eligible accountable compatibility; shared/indeterminate scope is explicit overlap conflict.
54. Concurrent restrictive Interim Operating Dispositions use exact intersection or affected-scope suspension when indeterminate and never use operating-state rank, recency, severity, or permissiveness.
55. Reassessment completion prospectively revalidates current governance and commits exactly one outcome atomically; another completion or successor Decision never silently closes or rebases open work.
56. Trigger Determiner, Reassessment Owner, Reassessment Coordination Authority, and Decision Authority are distinct substantive functions; software permission, technical principal, ownership, or queue assignment never substitutes.
57. Later Trigger correction/withdrawal, role expiry/revocation, cancellation, supersession, or successor Decision does not rewrite historical knowledge-time or completed basis; prospective eligibility remains fail-closed.
58. Every Register Concern Entry is derived from the exact key of owning Case, applicable Configuration or permitted explicit absence context, concern kind, authoritative source family, and stable source Record ID; selected source Versions are basis, not entry identity.
59. Register categories, groups, aggregates, ordering, acknowledgements, dismissals, queues, reports, exports, and notifications never become authoritative source facts or transfer authority, applicability, satisfaction, outcome, ownership, or closure.
60. A stable Shared Dependency is established only by exact citation of the same dependency Record ID or one eligible Shared Dependency Equivalence Determination against one exact immutable Dependency Candidate Set Version.
61. A finalized Dependency Candidate Set Version has immutable exact typed membership. Membership change creates a successor Version and never rewrites a prior accountability target or determination basis.
62. Shared Dependency Equivalence selection returns one eligible determination, `SHARED DEPENDENCY EQUIVALENCE NOT ESTABLISHED`, or `SHARED DEPENDENCY EQUIVALENCE CONFLICT — UNRESOLVED`; names, similarity, majority, ownership, recency, and software permission never select a winner.
63. Cross-Case Shared Dependency grouping is descriptive only. Every constituent retains its independent Case/Configuration/source/authority/applicability/satisfaction/coverage/outcome/closure facts.
64. Exact exposure counts and sets are descriptive. Material concentration, when used, requires a separate eligible authoritative Concentration Determination or accepted governed mechanism; no universal score or threshold exists.
65. A Register output claimed as current proves its active rule Version and processed watermark through the relevant authoritative recorded-time high-water mark, or remains visibly stale/inconsistent and ineligible as command authority.
66. Historical Register reconstruction retains the exact source, Candidate Set, determination, rule, dual-time, high-water, watermark, constituent, filter, grouping, and ordering basis used at the time.

### 8.1 Shared Dependency authoritative record contract

The following authoritative families support IRR-012 without making the Management Register authoritative:

#### Shared Dependency

A **Shared Dependency** has a stable Record ID across its immutable Versions. Each Version retains dependency kind/type, declared scope/purpose, organizational context where applicable, effective/recorded time, provenance, and predecessor/correction/supersession/withdrawal history. It is a portfolio dependency identity only; it creates no cross-Case authority, ownership, applicability, satisfaction, coverage, outcome, or closure.

#### Dependency Candidate Set

`DEPENDENCY_CANDIDATE_SET` is a first-class authoritative typed target, not a string or computed query. Each finalized Version retains:

- stable Candidate Set ID and immutable Candidate Set Version ID;
- exact typed candidate source Record IDs and, where equivalence depends on exact state/content, exact Version IDs;
- dependency kind/type for every candidate;
- declared equivalence scope and purpose;
- owning organizational context required for accountability resolution without creating Case authority transfer;
- effective time and recorded time;
- provenance and rationale for establishment;
- predecessor, correction, supersession, and withdrawal history; and
- deterministic canonical membership checksum or equivalent integrity basis.

Finalized membership is immutable. Adding, removing, or rebinding any candidate creates a successor Candidate Set Version. A Role Assignment, delegation, mechanism, or determination cites the exact Candidate Set Version. Historical resolution never recomputes membership from current source facts, a projection, search, UI selection, or query result.

#### Shared Dependency Equivalence Determination

An Equivalence Determination has stable Record ID and immutable Version ID and retains exact Candidate Set Version, exact stable Shared Dependency ID where the outcome is `EQUIVALENT`, dependency kind, exact outcome (`EQUIVALENT`, `NOT_EQUIVALENT`, or `INDETERMINATE`) and scope, rationale, exact accountable actor and Shared Dependency Determiner assignment or governed-mechanism/delegation basis, effective/recorded time, and complete correction/supersession/withdrawal history. Only `EQUIVALENT` establishes grouping for its exact scope. `NOT_EQUIVALENT` preserves distinct candidates, and `INDETERMINATE` establishes no group.

For exact Candidate Set Version, dependency kind, scope, effective time, and optional knowledge cutoff, current selection returns exactly:

- one eligible Equivalence Determination;
- `SHARED DEPENDENCY EQUIVALENCE NOT ESTABLISHED`; or
- `SHARED DEPENDENCY EQUIVALENCE CONFLICT — UNRESOLVED` with every incompatible candidate and reason.

An outcome may be scope-limited. Incompatible co-current outcomes block authoritative combined grouping but leave all source identities and constituent concern entries independently visible. No newest, majority, name, normalization, similarity, owner, hierarchy, or software-permission winner exists.

#### Concentration Determination

If PAIM records a substantive `MATERIAL CONCENTRATION` or equivalent classification, it uses a separate stable/versioned authoritative Concentration Determination. Each Version retains exact Shared Dependency ID/Version, exact constituent/source input manifest, classification/outcome, rationale, Shared Dependency Determiner actor and assignment/mechanism/delegation basis, effective/recorded time, and history. Current selection returns one eligible determination, `CONCENTRATION DETERMINATION NOT ESTABLISHED`, or `CONCENTRATION DETERMINATION CONFLICT — UNRESOLVED` with every candidate/reason. Absence of this determination leaves exact descriptive exposure counts/sets available but creates no materiality, risk, severity, priority, or authority meaning.

#### Projection and reconstruction integrity

Register population and aggregation are deterministic for declared scope, `effective_at`, optional `known_at`, and exact projection/population/aggregation rule Version. A materialized projection additionally retains calculation time, relevant source recorded-time high-water mark, processed watermark, and consistency state. It is current only when the watermark proves processing through that high-water mark under the active rule Version.

A historical Register view/export manifest retains requested scope/access context; effective/knowledge time; all rule IDs/Versions; every selected source Record/Version and absent/conflict candidates; Shared Dependency and exact Candidate Set/Equivalence/Concentration Versions; constituent concern keys and group membership; calculation time; high-water mark; watermark/inconsistency; and filter/group/order basis. Later correction, rule change, equivalence change, supersession, or rebuild never rewrites a prior manifest.

## 9. Integrity behavior and test candidates

The system should support tests demonstrating that:

1. two incompatible effective current versions produce `CURRENT RECORD CONFLICT — UNRESOLVED` rather than latest-record selection;
2. a correction preserves the original decision reconstruction and triggers reassessment when material;
3. a Boundary Snapshot with a missing required control fails the mechanical integrity check without producing a substantive decision automatically;
4. narrative human-determination clauses remain unresolved until an accountable determination is recorded;
5. a broadened or mixed boundary comparison cannot reuse the prior Decision authorization;
6. every attempted case transition outside §5.3 is rejected or visibly invalid;
7. withdrawal of a selected input before authorization returns the Case to an allowed earlier state;
8. withdrawal of the same historical input after authorization leaves the prior Decision intact and raises reassessment where material;
9. an expired or out-of-scope delegation cannot authorize a Decision;
10. a Decision Authority Gap blocks `DECIDED` but does not block analysis/integration unless another guard does;
11. a narrower Decision with another unresolved Authority Gap preserves the gap and exact blocked broader decision;
12. an Interim Operating Disposition can narrow or suspend but cannot broaden operation;
13. an expired disposition does not continue silently;
14. “confirm with conditions” changing a boundary clause requires a successor Decision;
15. a completed Reassessment cannot have both no confirmation and no successor Decision;
16. operation during intervention remains bound to the prior/current Decision until target prerequisites are accepted complete;
17. historical reconstruction returns the exact configuration, inputs, boundary, authority, roles, and rationale originally used;
18. two governing Configurations for one Case/effective time produce conflict rather than a plural current set or latest-record winner;
19. proposed, experimental, alternative, and fallback Configurations do not satisfy a governing-Configuration guard;
20. multiple compatible role performers coexist without creating implicit co-accountability;
21. accountability vacancy and incompatible plurality return explicit absence/conflict, and broad/narrow overlap has no implicit winner;
22. a materiality or identity-continuity determination without exact accountable provenance is ineligible for guarded use;
23. a Decision Authority role label or software permission without the complete §6 Authorization Basis cannot authorize a Decision.
24. two ready Value candidates with no eligible Acceptance/Selection Version return `INPUT SELECTION NOT ESTABLISHED`; two incompatible co-current eligible Acceptance/Selection Versions for the same explicit context return `INPUT SELECTION CONFLICT — UNRESOLVED`; one accountable eligible acceptance with explicit competitor dispositions returns the one accepted/frozen Input and exact Acceptance/Selection Version;
25. first acceptance freezes and selects atomically, while later reuse creates a new Acceptance/Selection Version against the same immutable Input Version;
26. withdrawal/rejection before Integration readiness makes the selected Input ineligible, while later change preserves historical reconstruction;
27. Evidence applicable to one Configuration Version does not silently transfer to another target/version;
28. conditional/partial Evidence cannot support a broader Input Boundary;
29. incompatible co-current Applicability judgments produce conflict, and an accountable successor resolves only prospectively while preserving predecessors;
30. `INDETERMINATE` Evidence is eligible or blocked only through an explicit exact lane-level fitness determination, never a global default;
31. unrelated-scope acceptance/Applicability accountability is rejected and broad/narrow competing assignments remain conflict absent explicit displacement.
32. evidence with no Completion Acceptance leaves a required-before obligation unsatisfied;
33. two required-before obligations with one incomplete block activation under all-of aggregation;
34. incompatible Acceptances or replacements produce explicit conflict;
35. owner self-acceptance is ineligible without a separately established Completion Acceptor relationship, while the same actor may qualify when both exact relationships exist;
36. explicit zero-required-before set yields `NOT_REQUIRED`, while missing Obligation Set yields `NOT_ESTABLISHED`;
37. required-after and optional incompletion do not block initial activation under their exact normative conditions;
38. partial, failed, or cancelled required-before work does not satisfy;
39. wrong-Decision or wrong-Configuration completion is ineligible and prior accepted completion does not silently carry to a successor Decision;
40. Completion Acceptance alone does not authorize activation;
41. a software checklist or incompletely governed pre-authorization mechanism cannot activate, while one genuine exact pre-authorized organizational mechanism plus all guards is eligible; and
42. later acceptor-role expiry does not rewrite historical Acceptance, while withdrawn/superseded Acceptance cannot support future activation.

## 10. Human judgment and mechanical integrity boundary

The system may mechanically:

- validate identity/version references;
- apply effective-time and current-selection rules;
- detect overlap/conflict;
- enforce allowed lifecycle transitions and required record presence;
- compare structured boundary clauses;
- validate authority-chain scope/time/link completeness;
- enforce immutability and successor relationships;
- detect missing confirmation/successor outcomes;
- select governing Configuration and accountability outcomes as one, absence, or conflict under the accepted scope rules;
- select each analytical lane and Evidence Applicability as one, absence, or conflict for exact scope/purpose/time;
- validate exact Input Acceptance/Selection, Evidence Applicability, material-Evidence reference, and lane-level fitness record completeness;
- validate typed Role Assignment targets and explicit supersession/delegation relationships;
- verify that materiality and identity-continuity determinations retain required accountable provenance and history;
- select exact Obligation Sets, Completion Acceptances, and Completion Acceptor accountability as one, absence, or conflict;
- derive per-obligation and aggregate prerequisite results using the normative staged all-of rule;
- validate exact Prerequisite Evaluation Basis and Activation Authorization completeness; and
- execute a genuinely governed, pre-authorized organizational activation mechanism only when its exact rule/version/scope/authority and every guard are established;
- validate immutable Dependency Candidate Set membership/checksum and exact typed candidate references;
- select Shared Dependency Equivalence and Concentration Determinations as one, absence, or conflict for exact target/scope/time;
- derive exact descriptive Register counts/sets from a retained constituent manifest; and
- validate projection watermark against the relevant authoritative recorded-time high-water mark and active rule Version.

The system must leave to accountable human or established organizational authority:

- substantive configuration materiality and same-identity/new-identity outcomes;
- evidence applicability where not mechanically established;
- lane-level material-Evidence fitness and treatment of `INDETERMINATE` for a bounded analytical use;
- substantive Value/Risk Input acceptance under the eligible accountable assignment/mechanism;
- Value and Risk conclusions;
- uncertainty classification;
- narrative boundary interpretation;
- whether a human-determination clause is satisfied;
- management judgment among alternatives;
- legitimacy of organizational authority sources;
- authorization of Decisions and Interim Operating Dispositions;
- Trigger materiality/Determination;
- semantic Trigger grouping, identity-level duplicate disposition, Reassessment compatibility/coordination, cancellation, supersession, and Trigger coverage transfer;
- whether an implementation-detail change is non-substantive under §7.6;
- legitimacy and assignment of an accountable actor/mechanism;
- substantive Completion Acceptance;
- whether continued-validity/reuse criteria remain satisfied for a successor Decision; and
- explicit target activation unless a genuine governed organizational mechanism was already authorized for that exact determination;
- establishment of Shared Dependency equivalence beyond exact identity; and
- substantive concentration classification or cross-Case prioritization.

Mechanical validity means the record is internally eligible for the next action. It does not mean the management judgment is substantively correct or authorized unless the required human/authority event also exists.

## 11. P1 dependencies intentionally not resolved here

This specification does not attempt to resolve all P1 findings from the implementation-readiness review.

The following remain for bounded later work unless another accepted specification already resolves them:

- whether Observation is a separate authoritative record;
- canonical stronger/broader relations among organization-specific operating states.

These remaining items are IRR-009 and IRR-014 respectively. IRR-012 Management Register semantics are normatively hardened by §§8.1 and the Management Register, Roles/Accountability, Managed Configuration, analytical, Decision, Intervention/Learning, Reassessment, Behavioral Validation, Platform Architecture, and sequencing contracts, subject to independent Increment 7 gate-closure re-review. This hardening does not define Observation persistence or stronger/broader operating-state ranking.

Configuration ownership and v0.1 governing cardinality remain unchanged: exactly one owning Case per Configuration identity and at most one governing Configuration per Case/effective time. Accepted Shared Dependency identity permits descriptive cross-Case grouping only under §§8.1 and never creates joint Configuration ownership or cross-Case authority/reuse.

General v0.1 Role Assignment overlap is resolved by the Roles/Accountability specification's no-implicit-precedence rule. A later accepted versioned organizational policy may define explicit displacement or combination behavior, but its absence never authorizes a specific-over-general, broad-over-narrow, newest, or software-permission fallback.

IRR-006 and IRR-008 are resolved for specification purposes by the Value/Risk Interface and Evidence/Authority contracts, with conforming lifecycle, role, Configuration, and Integration handoff rules. Their accepted semantics are summarized in §§3.4, 3.11–3.12, 8, and 10; this specification does not replace the substantive owner definitions.

If any unresolved P1 question prevents a required P0 integrity determination in a concrete case, the system records the gap/conflict and does not invent a permissive answer.

The accepted Normative Model Redesign Gates 2–6 are also intentionally unresolved here as stated
in Section 3A.11. Gate 1 provides reusable integrity vocabulary only; it does not pre-decide those
substantive contracts.

## 12. Platform boundary

Platform architecture may decide:

- how identities and versions are physically stored;
- whether status history uses events, immutable rows, or another append-preserving mechanism;
- how effective-time queries are implemented;
- how Boundary clauses are rendered or edited;
- how transition guards are presented;
- how authorization is signed or approved technically;
- how current conflicts and management attention are displayed;
- how audit/history views are implemented;
- physical representation of the semantic-contract catalog and conditional envelope;
- whether an adopting exact context set is embedded or, where later authorized, independently
  identified;
- transaction/isolation mechanisms that provide the specified all-or-nothing behavior; and
- caching/materialization of non-authoritative read compositions.

Platform architecture may not change the observable semantics in this specification.

## 13. Resolution traceability

| Finding | Resolution in this specification |
|---|---|
| IRR-001 | §§3 and 8: stable identity, immutable versions, draft/finalization boundary, status events, time, correction/amendment/supersession/withdrawal, current selection, exact retrieval, invariants |
| IRR-002 | §4 and §8: immutable hybrid Boundary Snapshot, structured and narrative clauses, verification modes, comparison, breach, invariants |
| IRR-003 | §5 and §8: complete allowed transition table, guards, actors/mechanisms, subordinate effects, concurrent operation/intervention/reassessment, closure/reopening |
| IRR-004 | §6 and §8: Decision Authorization Basis, scope/time validity, Decision Authority Gap as Authority Gap classification, bounded-proceed authority, historical preservation |
| IRR-005 / CON-001 | §7 and §8: Interim Operating Disposition, permitted effects, authority/currentness/expiry, completed-Reassessment outcome invariant, successor rule for changed conditions |
| IRR-007 | §§2.1, 3.11–3.13, 5.4, and 8–10: one owning Case, one/absence/conflict governing Configuration selection, orthogonal non-governing purpose, linked-Case concurrency, accountable materiality/identity history |
| IRR-013 / CON-002 | §§2.1, 3.11–3.13, 6, and 8–10: typed/conditional scope conformance, compatible plural performers, one/absence/conflict accountability, no implicit scope precedence, and unchanged Decision Authorization Basis |
| Issue #129 / Normative Redesign Gate 1 | §3A: prospective semantic-contract identity, conditional envelope, exact context sets, family-owned selection, non-authoritative read composition, dual-time reconstruction, semantic transactions, compatibility, access, and later-gate boundaries |

## 14. Repository placement

```text
docs/
└── system/
    └── specifications/
        └── PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md
```

## 15. Conclusion

This specification supplies the cross-cutting integrity rules required to translate PAIM's existing
management semantics into one consistent platform architecture and the prospective common machinery
needed for explicitly adopted later semantic contracts without reinterpreting v0.1 history.

It preserves the governing distinctions:

> **human judgment determines substantive PAIM meaning; system integrity preserves exactly what was judged, by whom, under what authority, for which boundary and time, and what may govern next.**
