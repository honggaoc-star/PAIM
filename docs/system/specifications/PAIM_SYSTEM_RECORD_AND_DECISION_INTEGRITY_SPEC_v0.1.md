# PAIM System Record and Decision Integrity Specification v0.1

## Status

Implementation-independent cross-cutting system specification for authoritative-record history, current-record selection, Integrated Operating Boundary integrity, PAIM case transitions, decision authorization, and interim operating disposition during reassessment.

This specification resolves the blocking findings IRR-001 through IRR-005 and CON-001 in `PAIM_CODEX_IMPLEMENTATION_READINESS_REVIEW_v0.1.md`.

It also supplies the cross-cutting integrity rules needed by the accepted PAIM v0.1 resolution of IRR-007 and IRR-013/CON-002. The Managed Configuration, Case Lifecycle, and Roles/Accountability specifications remain the substantive owners of those scope, cardinality, role, and accountability semantics.

It governs the cross-cutting semantics defined here across the PAIM v0.1 system specification set. The affected specifications continue to govern the substantive content and human judgments of their record families. Where an earlier v0.1 specification is silent, optional, or inconsistent on a cross-cutting matter defined here, this specification controls. It does not replace the analytical or management semantics of those specifications.

This specification does not prescribe a database, event store, programming language, workflow engine, identity provider, signature technology, API, or user interface.

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

Value Input and Risk Input acceptance/selection are separate authoritative relationship families. For one lane, exact Configuration Version, bounded use/purpose, effective time, and optional knowledge cutoff, selection returns one eligible accepted/frozen Input Version plus its exact Acceptance/Selection Version, `INPUT SELECTION NOT ESTABLISHED`, or `INPUT SELECTION CONFLICT — UNRESOLVED`. Ready status, newest/latest time, owner, generic role, integrator participation, mutable flag, row order, or software permission cannot select a winner. Each later reuse requires a new use-specific acceptance and accountable material-Evidence fitness judgment.

Evidence Applicability is a first-class authoritative many-to-many relationship. For one exact Evidence Version, target identity/version, purpose/use, assessed scope, effective time, and optional knowledge cutoff, selection returns one eligible Applicability Version, `APPLICABILITY NOT ESTABLISHED`, or `EVIDENCE APPLICABILITY CONFLICT — UNRESOLVED`. Conflict is not a stored Applicability outcome. Recency, specificity, ownership, directory hierarchy, mutable current flag, row order, or permission cannot resolve it.

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
| `DECIDED` | `OPERATING_OBSERVING` | Current operation already conforms to the authorized configuration/boundary and no prerequisite intervention remains incomplete. |
| `DECIDED` | `CLOSED` | Authorized Decision discontinues/retires the use or otherwise authorizes closure with no continuing observation requirement. |
| `DECIDED` | `SUPERSEDED` | The current or an authorized successor/amendment Decision establishes the named successor Case, effective transfer/end of operation under this Case, and preserved Decision/Case relationships. |
| `INTERVENTION_IN_PROGRESS` | `OPERATING_OBSERVING` | All interventions designated as prerequisites are accepted complete; target configuration and boundary alignment are confirmed. |
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
| `REOPENED` | `OPERATING_OBSERVING` | Completed Reassessment creates a Decision Confirmation leaving the authorized Decision, operating state, Boundary Snapshot, and substantive conditions unchanged; no prerequisite intervention remains incomplete; any Interim Operating Disposition is ended or operation is aligned with it. |
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
- Cancellation, failure, or inconclusive completion of a Learning Item does not silently resolve uncertainty or change a Decision.
- Supersession of a Decision changes current selection prospectively but never changes the historical record used for its effective period.

### 5.6 Coexisting operation and intervention

Case lifecycle state `INTERVENTION_IN_PROGRESS` describes the management workflow. It does not imply that all operation has stopped.

While intervention toward a target configuration is in progress:

- any continuing operation remains governed by the prior/current authorized Decision and Boundary Snapshot;
- the target configuration must not operate until all prerequisite interventions are accepted complete and an authorized Decision/Boundary permits it;
- a Decision or Interim Operating Disposition must explicitly authorize fallback, narrowed continuation, partial suspension, or full suspension;
- the system must display both the currently operating configuration/Decision and the target configuration/intervention state.

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
24. two ready Value candidates for one Configuration/use produce pre-acceptance selection conflict until an accountable acceptance records one selected Input and explicit dispositions/supersession for the competitors;
25. first acceptance freezes and selects atomically, while later reuse creates a new Acceptance/Selection Version against the same immutable Input Version;
26. withdrawal/rejection before Integration readiness makes the selected Input ineligible, while later change preserves historical reconstruction;
27. Evidence applicable to one Configuration Version does not silently transfer to another target/version;
28. conditional/partial Evidence cannot support a broader Input Boundary;
29. incompatible co-current Applicability judgments produce conflict, and an accountable successor resolves only prospectively while preserving predecessors;
30. `INDETERMINATE` Evidence is eligible or blocked only through an explicit exact lane-level fitness determination, never a global default;
31. unrelated-scope acceptance/Applicability accountability is rejected and broad/narrow competing assignments remain conflict absent explicit displacement.

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
- verify that materiality and identity-continuity determinations retain required accountable provenance and history.

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
- whether a trigger is immaterial under the current Decision;
- whether an implementation-detail change is non-substantive under §7.6;
- legitimacy and assignment of an accountable actor/mechanism;

Mechanical validity means the record is internally eligible for the next action. It does not mean the management judgment is substantively correct or authorized unless the required human/authority event also exists.

## 11. P1 dependencies intentionally not resolved here

This specification does not attempt to resolve all P1 findings from the implementation-readiness review.

The following remain for bounded later work unless another accepted specification already resolves them:

- whether Observation is a separate authoritative record;
- intervention prerequisite classification and completion-acceptance role details beyond the lifecycle guard;
- full trigger/reassessment concurrency and merge rules;
- Management Register aggregation and shared-dependency identity;
- canonical stronger/broader relations among organization-specific operating states.

These remain IRR-009, IRR-010, IRR-011, IRR-012, and IRR-014 respectively. The IRR-006/IRR-008 hardening does not define Observation persistence, Intervention completion acceptance, Trigger/Reassessment concurrency, Register aggregation/shared-dependency equivalence, or stronger/broader operating-state ranking.

Configuration ownership and v0.1 governing cardinality are resolved by the Managed Configuration and Case Lifecycle specifications: exactly one owning Case per Configuration identity and at most one governing Configuration per Case/effective time. Cross-Case sharing, dependency equivalence, and reuse beyond explicit relationships remain deferred with IRR-012.

General v0.1 Role Assignment overlap is resolved by the Roles/Accountability specification's no-implicit-precedence rule. A later accepted versioned organizational policy may define explicit displacement or combination behavior, but its absence never authorizes a specific-over-general, broad-over-narrow, newest, or software-permission fallback.

IRR-006 and IRR-008 are resolved for specification purposes by the Value/Risk Interface and Evidence/Authority contracts, with conforming lifecycle, role, Configuration, and Integration handoff rules. Their accepted semantics are summarized in §§3.4, 3.11–3.12, 8, and 10; this specification does not replace the substantive owner definitions.

If any unresolved P1 question prevents a required P0 integrity determination in a concrete case, the system records the gap/conflict and does not invent a permissive answer.

## 12. Platform boundary

Platform architecture may decide:

- how identities and versions are physically stored;
- whether status history uses events, immutable rows, or another append-preserving mechanism;
- how effective-time queries are implemented;
- how Boundary clauses are rendered or edited;
- how transition guards are presented;
- how authorization is signed or approved technically;
- how current conflicts and management attention are displayed;
- how audit/history views are implemented.

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

## 14. Repository placement

```text
docs/
└── system/
    └── specifications/
        └── PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md
```

## 15. Conclusion

This specification supplies the cross-cutting integrity rules required to translate PAIM's existing management semantics into one consistent platform architecture.

It preserves the governing distinctions:

> **human judgment determines substantive PAIM meaning; system integrity preserves exactly what was judged, by whom, under what authority, for which boundary and time, and what may govern next.**
