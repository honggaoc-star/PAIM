# PAIM Case Lifecycle Specification v0.1

## Status

Implementation-independent system specification for the lifecycle of a Practical AI Management (PAIM) case.

This specification derives from:

- `PAIM_SYSTEM_ARCHITECTURE_v0.1.md`
- `PAIM_SYSTEM_COMPLETION_BASELINE_GAP_MAP_v0.1.md`
- `PAIM_MINIMUM_MANAGEMENT_CASE_v0.3.md`
- `PAIM_PRACTITIONER_PLAYBOOK_v0.2.md`

It defines **what lifecycle behavior the PAIM system must support**. It does not prescribe software implementation.

**Normative cross-cutting contracts:** `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`
governs authoritative record identity/version/currentness, semantic-era interpretation, Decision
Authorization Basis, operation during intervention/reassessment, and Interim Operating Disposition.
`PAIM_RESPONSIBILITY_AND_CASE_WORK_SPEC_v0.1.md` governs exact Responsibility and Work context.
§3A of this specification governs prospective continuing-Case status and continuity determinations.
The v0.1 phase states and Transition Events in §3 and §§4–25 retain their original meaning before
cutover and remain immutable historical facts after cutover; §3A is the prospective contract.

## 1. Purpose

A PAIM case is the durable management container for an AI-related decision.

The lifecycle must allow management to:

- open a case for a real decision;
- define the AI-enabled configuration;
- assemble relevant evidence and authority;
- obtain Value and Risk inputs;
- perform Decision Integration;
- make and authorize a judgment;
- implement intervention;
- observe operation and generate learning;
- reassess when conditions change;
- preserve prior decisions and configuration history;
- close or supersede the case without destroying its record.

## 2. Lifecycle Principles

### 2.1 A case is decision-centered

A case exists because management must decide something about a bounded AI-enabled configuration.

It is not merely an AI inventory entry, risk record, project record, or document folder.

### 2.2 Lifecycle state is not operating state

The system must distinguish:

**Case lifecycle state** — where the management case is in its workflow.

from:

**AI operating state** — experiment, bounded continuation, targeted scale, institutionalized use, controlled transition, suspended, discontinued, or another management state.

A case may be `OPERATING / OBSERVING` while the AI operating state is `bounded continuation`.

### 2.3 History is non-destructive

A later decision must not silently overwrite an earlier decision.

Reassessment creates a successor decision or successor case state with explicit linkage.

### 2.4 Material configuration change matters

If the managed configuration changes materially, the system must determine whether:

- the existing case can be reopened with a new configuration version; or
- a successor/new case is required.

Prior evidence must not automatically transfer.

The materiality and same-identity/new-identity determinations must identify one accountable Role Assignment or one explicitly governed accountable mechanism for the exact Configuration scope/version, together with rationale, effective time, recorded time, and preserved history. Edit access, workflow participation, or Case ownership alone must not be used to infer that accountability.

### 2.5 Evidence maturity controls readiness

A case should not advance to Decision Integration merely because documents exist.

The required Value/Risk inputs, authority state, and configuration definition must be sufficiently complete for the decision being made.

### 2.6 Unresolved authority is explicit

Missing governing authority does not necessarily block every bounded decision.

The case must record:

- `AUTHORITY UNRESOLVED`;
- decision affected;
- authority/evidence needed;
- whether the current bounded decision can proceed.

## 3. Canonical Lifecycle States

The minimum lifecycle is:

```text
OPEN
  |
  v
CONFIGURATION_DEFINED
  |
  v
EVIDENCE_ANALYSIS
  |
  v
READY_FOR_INTEGRATION
  |
  v
DECISION_PENDING
  |
  v
DECIDED
  |
  v
INTERVENTION_IN_PROGRESS
  |
  v
OPERATING_OBSERVING
  |
  +-----------> REASSESSMENT_DUE
  |                    |
  |                    v
  |                REOPENED
  |                    |
  +<-------------------+
  |
  v
CLOSED / SUPERSEDED
```

Cases may use only the source-to-target transitions and explicit skips defined in `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, §5.3. A platform may compress presentation or complete adjacent transitions at the same recorded time, but it must preserve a distinct valid Transition Event and every mandatory guard for each transition.

## 3A. Prospective continuing-Case and continuity contract

### 3A.1 Adoption and legacy boundary

This section is the controlling substantive contract for prospective Case continuity. It adopts the
Gate-1 common envelope, Semantic Contract ID/Version, exact typed context set, family-owned
selection, dual-time reconstruction, semantic transaction, compatibility, and access rules.

There is no global cutover. A Case uses this contract only after a separately accepted
implementation/migration contract declares the exact supported Semantic Contract Version, Case or
population, effective/knowledge boundary, initialization rule, legacy adapter, rollback behavior,
and cross-era selection. Before cutover, the canonical v0.1 phase model in §§3–25 and Integrity §5
continues to control runtime behavior.

After cutover, the three-status continuity contract controls Case-level continuity. Legacy
`CONFIGURATION_DEFINED`, `EVIDENCE_ANALYSIS`, `READY_FOR_INTEGRATION`, `DECISION_PENDING`,
`DECIDED`, `INTERVENTION_IN_PROGRESS`, `OPERATING_OBSERVING`, `REASSESSMENT_DUE`, and `REOPENED`
events remain exact historical phase facts but are not prospective Case continuity statuses. A
failed prospective command never retries as a legacy transition, and no legacy event is rewritten,
relabeled, or selected merely because its era is older or newer.

### 3A.2 Durable Case identity

A Case is one bounded continuing management subject:

- one materially coherent AI-related business use or management question;
- its exact Managed Configuration lineage;
- independent Value and Risk histories;
- authorized Decisions, Boundaries, and operating relationships;
- actions/Interventions, outcomes, information, Learning, Triggers, and Reassessments; and
- the organizational need to preserve continuity among those facts.

The Case is neither an AI inventory entry nor a universal workflow container. Provider, model,
product, title, owner, organizational unit, source information, technical deployment, or semantic
similarity alone does not establish identity. One system may support several Cases, and one Case
may contain multiple AI and non-AI components within its bounded subject.

### 3A.3 Continuity status vocabulary and selector

The only prospective Case continuity statuses are:

- `OPEN`: the same bounded management subject remains eligible for continuing PAIM management;
- `CLOSED`: an accountable determination establishes that there is no current operation and no
  remaining required PAIM management obligation under this Case identity; and
- `SUPERSEDED`: one named successor Case prospectively carries the management subject, and the
  predecessor is terminal for new Work or substantive Case acts.

`OPEN` does not mean active Work, active operation, approval, readiness, undecided status, or a
missing Decision. There is no universal `ACTIVE` or `COMPLETED` Case status. `REOPENED` is an
explicit continuity event/determination that appends a new `OPEN` status; it is not a long-lived
status.

For one exact Case, effective time, and knowledge cutoff, continuity selection returns exactly one
eligible status Version or explicit `CASE CONTINUITY STATUS CONFLICT — UNRESOLVED`. A Case must have
one eligible status after initialization. Recency, storage order, legacy phase, subordinate state,
operation, Work, title, or UI presentation cannot choose or derive a status.

### 3A.4 Case continuity status/event minimum record

Every prospective status change preserves:

- exact Case ID and immutable continuity Status/Event Version ID;
- this exact Semantic Contract ID/Version;
- prior and new continuity status;
- exact Case Continuity Determination Version and changed-basis context where required;
- exact responsible Actor or governed mechanism and eligible Responsibility Version;
- separately valid authority/assignment basis required for the act;
- rationale and reason;
- effective time, recorded time, and knowledge cutoff used by the command;
- exact predecessor/successor status relationship; and
- successor Case relationship when status is `SUPERSEDED`.

Initial Case creation under this contract appends `OPEN`; it does not create any subordinate
Decision, Configuration, Work, operation, or review fact.

### 3A.5 Case Continuity Determination

A Case Continuity Determination is a stable authoritative Record with immutable Versions. It
preserves:

- Determination ID and Version ID and Semantic Contract ID/Version;
- controlled determination kind;
- exact source Case and current continuity Status Version;
- candidate same-Case, changed-Configuration, or successor-Case context as applicable;
- an immutable typed context set containing every exact changed source/basis Version;
- controlled outcome;
- rationale and identified material continuity/discontinuity factors;
- responsible Actor or genuine governed mechanism;
- exact `DETERMINE_CASE_CONTINUITY` Responsibility Version and assignment/authority basis;
- effective time, recorded time, and knowledge cutoff;
- predecessor/correction/supersession/withdrawal history; and
- exact successor Case relationship where required.

The controlled kinds and outcomes are:

| Determination kind | Permitted outcomes | Required additional context |
|---|---|---|
| `SAME_OR_NEW_CASE` | `SAME_CASE`, `NEW_CASE_REQUIRED` | exact changed basis, candidate business use/question and Configuration context |
| `CASE_CLOSURE` | `CLOSE`, `REMAIN_OPEN` | exact closure-guard manifest and final Decision/operation relationship |
| `CASE_REOPENING` | `REOPEN_SAME_CASE`, `REMAIN_CLOSED`, `NEW_CASE_REQUIRED` | exact prior closure Version and new management need/source |
| `CASE_SUPERSESSION` | `SUPERSEDE_WITH_SUCCESSOR`, `DO_NOT_SUPERSEDE` | exact named successor Case and relationship basis |

Absence, vacancy, inaccessible basis, or conflict blocks the requested routing/status command.
Similarity, provider/model equality, shared information, title, ownership, recency, majority,
configuration version number, or software inference cannot produce an outcome.

### 3A.6 Same Case versus new Case

The same Case is appropriate when the bounded management subject remains materially coherent and
the new activity is reconsideration, changed information, changed operating conditions, a successor
Configuration within the same use, or a later Decision about that same use.

A new Case is required when independent interpretation is materially necessary, including a
materially different business purpose/management question, use/population/workflow with no
defensible continuity, concurrent independently governed Configuration, information that cannot
reasonably carry across the claimed subject, or a successor requiring independent Responsibilities,
authority, Decisions, and review.

A purely structural correction whose identity effect is already fixed by its owning contract need
not invent a continuity judgment. Whenever material coherence is not mechanically established by
an exact accepted rule, `SAME_OR_NEW_CASE` requires the accountable determination above. A new Case
receives a new stable Case ID and its own `OPEN` status. Any predecessor/successor or related-Case
relationship is explicit and does not transfer authority, Responsibility, access, applicability,
Decision effect, closure, or subordinate state.

### 3A.7 Configuration continuity within a Case

A successor Configuration Version or new Configuration identity may remain within the same Case
only when the exact Configuration change contract and, where required, a `SAME_CASE` continuity
determination establish that the bounded management subject remains coherent. Materially different
business use requires a new Case even when provider, model, technical system, or information is
shared.

Every historical Evidence Applicability, Value/Risk Input and selection, Integration, Boundary,
Decision, Responsibility, Work, Intervention, Trigger/Reassessment, and Learning fact remains bound
to its original exact Case and Configuration Version. A successor Configuration creates no silent
carry-forward, retarget, currentness, applicability, satisfaction, or authority. Each owning
contract must revalidate any prospective reuse.

### 3A.8 Closure guards

Stopping or discontinuing AI-enabled use is a Decision/operating result and does not automatically
close the Case. A `CLOSE` determination and `OPEN -> CLOSED` status transaction may commit only when
the exact effective-time/knowledge-time guard manifest establishes all of the following:

1. the exact current Case status is `OPEN` and no conflicting status exists;
2. no current operation continues under an authorized Decision/Configuration for this identity;
3. required Intervention, retirement, data/control disposition, Completion Acceptance, or other
   action obligation is completed, explicitly transferred through a valid owning contract, or not
   required;
4. required Learning/outcome-evidence obligations are completed or validly disposed;
5. no Trigger requiring Reassessment lacks exact completed coverage, and no active/conflicting
   Reassessment or Interim Operating Disposition requires management;
6. required Authority, contractual, retention, or existing review obligation is completed or
   validly disposed without inventing Gate-5 timing semantics;
7. no required durable Work remains `READY` or `WAITING`, and no Responsibility vacancy/conflict
   blocks a required obligation;
8. the final Decision/operation, governing Configuration, unresolved-item treatment, retention,
   and any successor relationship are exact; and
9. the responsible Actor/mechanism, `DETERMINE_CASE_CONTINUITY` Responsibility, assignment/authority
   basis, access, expected Versions, and command replay basis are valid.

Closure deletes nothing, changes no prior effective interval outside the status event, terminates no
external authority by inference, and does not declare every subordinate item successful. A failed
guard yields `REMAIN_OPEN`/blocked explanation as the owning command permits and commits no `CLOSED`
status or partial disposition.

### 3A.9 Reopening and supersession

A `CLOSED` Case may return to `OPEN` only through `CASE_REOPENING` with outcome
`REOPEN_SAME_CASE`, exact prior closure, a new exact management need, and a valid continuity
Responsibility/basis. The closure remains historical. Reopening creates no Work, Configuration,
Decision, Trigger, or review result; each required subordinate fact follows its own command.

If the new need is a materially different subject, outcome is `NEW_CASE_REQUIRED` and the old Case
remains `CLOSED`. A `SUPERSEDED` Case never reopens. `CASE_SUPERSESSION` requires one exact named
successor Case and atomically appends the predecessor `SUPERSEDED` status plus Case relationship.
From its effective time, the predecessor rejects new Responsibility, Work, Configuration,
Decision, Intervention, Learning, Trigger/Reassessment, or other substantive writes except
explicitly authorized correction, audit, retention, or historical relationship operations.

### 3A.10 Concurrent subordinate states and current position

An `OPEN` Case may simultaneously have operation under an exact Decision, in-progress or waiting
Interventions, Learning, Value refresh, Risk refresh, information work, Trigger/Reassessment, and
other exact Work. Their independent statuses coexist and cannot collide because they are not Case
continuity phases. Completion or change in one does not move, complete, hide, or waive another.

`Current management position` is an access-filtered Gate-1 read composition, not an authoritative
master record or status. It may compose the current Case status, governing Configuration,
Decision/Boundary/operation, independent Value/Risk positions, Responsibilities/Work, actions,
Learning, Triggers/Reassessments, unresolved information/authority/uncertainty, and exact existing
attention conditions. It retains source Versions, rule Version, effective/known-at basis, access
context, and watermark. Cache, label, order, count, notification, or view state creates no
continuity, priority, authority, or closure.

### 3A.11 Responsibility and Work interaction

Gate-2/4 Responsibility and Work remain bound to their original exact Case and Configuration
context. Prospective Case continuity uses controlled obligation kind
`DETERMINE_CASE_CONTINUITY`, with a discriminator for `SAME_OR_NEW_CASE`, `CASE_CLOSURE`,
`CASE_REOPENING`, or `CASE_SUPERSESSION`, and the exact determination context above.

Case or Configuration change triggers review/commit revalidation under the Work contract. A stale
Responsibility or Work Item cannot retarget to a successor Case/Configuration, satisfy a closure
guard, or commit a result. It remains historical and may be explicitly cancelled/superseded; any
replacement receives a new or linked successor identity and exact context. Case Coordinator
practical role, access, ownership, operation, or software permission does not establish continuity
Responsibility or authority.

Continuity Responsibility establishes who is accountable to perform the exact determination; it
does not choose the outcome or supply any separate organizational authority required to close,
reopen, supersede, transfer, or end operation. The command retains both bases where both are
required.

### 3A.12 Historical reconstruction

Every authorized Decision remains reconstructable from its exact bound Configuration, Integration,
Value/Risk Inputs and selections, Boundary, Authority/Gap, Decision Authorization Basis, and other
explicit sources. Case reconstruction supports:

1. the exact Decision-bound basis;
2. state effective at a requested time using knowledge now available;
3. state actually known by the requested cutoff; and
4. later facts labelled as later knowledge.

Successor Configuration, Decision, Case status, correction, closure, reopening, supersession,
Responsibility, Work, action, information, or Learning never rewrites the earlier basis or enters a
known-at view before its recorded time. Historical legacy phase and prospective continuity facts
retain their source contract labels; there is no cross-era `newer wins` rule.

### 3A.13 Access, atomicity, and zero mutation

Access/non-disclosure is checked before status/determination selection, changed-basis composition,
closure-guard composition, same/new routing, command review/commit, current-position composition,
and historical reconstruction. Hidden Cases, sources, candidates, obligations, conflicts, counts,
or successor identities do not leak through explanations, output shape, ordering, or timing.

Continuity determination plus status/relationship facts declared by one natural command form one
Gate-1 semantic transaction. Every expected Version, Responsibility, assignment/authority, access,
guard, context, and replay check passes and all intended facts commit, or zero facts commit. Exact
replay returns the original identities without duplicates. A changed context, determination,
successor, status, or intended-fact set is not replay.

### 3A.14 Explicit exclusions

Gate 5 now owns planned/required review timing through the Reassessment specification, §38A; this
continuity section does not redefine it. It does not define scheduler behavior, assessment
adequacy, reliance, quantitative Value/Risk, first-class Observation, generic workflow, UI,
notifications, persistence, schema, migration, deployment, analytics, or Harborlight mutation.
Gate 6 now owns the prospective analytical meanings; this continuity section does not redefine
them.

### 3A.15 Gate-5 continuing-review interaction

Only an `OPEN` prospective Case may initiate a new Planned Review Point, time-driven review
Trigger, Review Episode, or review-related Work. `CLOSED` and `SUPERSEDED` Cases reject those new
substantive facts under the existing atomic/access rules. Reopening creates none automatically.

An existing applicable required-review obligation participates in the §3A.8 closure guard and
must be completed or validly disposed under its exact source contract. A planned point, elapsed
date, derived attention, or missed planned review is not by itself a closure obligation or
violation. Neither arrival nor Review Episode completion moves the Case status, closes subordinate
work, or changes the current Decision. All point, constraint, Trigger, Work, and episode facts
remain bound to their original exact Case/Decision/Configuration context and never retarget across
continuity change.

### 3A.16 Gate-6 analytical readiness composition

For a prospective Gate-6-adopted consumer, **ready for Integration** is an access-filtered
composition, not a Case status, lifecycle phase, shared Value/Risk result, or practitioner action.
For the exact governing Configuration and bounded decision use, it requires independently one
eligible current Value and one eligible current Risk Assessment/Input, Readiness Event, `ADEQUATE`
Determination, and Reliance Designation, plus every owning information/Applicability/currentness
guard required by the Value/Risk and Integration specifications. Absence or conflict in either lane
keeps the composition not ready and reveals no inaccessible basis.

Legacy `READY_FOR_INTEGRATION` phase events and readiness guards remain exact under their original
semantic era. PAIM never converts the prospective composition into a phase, maps a legacy phase to
new adequacy/reliance facts, or lets `OPEN` imply readiness. Case/Configuration continuity change
causes prospective revalidation; it does not retarget an Assessment, Responsibility, Work,
Adequacy Determination, or Reliance Designation. `CLOSED`/`SUPERSEDED` behavior remains governed by
Gate 3.

### 3A.17 Pre-Case initiation authority

A prospective Case may be opened from a minimal practitioner request only through one exact,
current **Case-initiation authority** Version that already exists before the Case. This source is
an externally grounded organizational mandate, not a Case-specific authority fabricated in
anticipation of a generated Case identity. It preserves the authorized Actor, bounded
organizational/local scope, permitted act `CREATE_OPEN_CASE`, any allowed management-use
constraints, authoritative provenance, effective and recorded time, immutable succession or
withdrawal history, and its exact Semantic Contract/context.

The natural Case-initiation command validates software create access and exactly one eligible
Case-initiation authority, then generates the Case and initial context identities internally. In
one semantic transaction it appends the Case, initial governing Configuration and designation,
`OPEN` continuity fact, and only the minimum `DETERMINE_CASE_CONTINUITY` Responsibility,
Assignment Basis, and Responsibility Assignment needed to coordinate the new Case. The resulting
Assignment Basis binds the exact pre-Case mandate while its Case, context, obligation signature,
and Actor are made exact inside that same transaction. A practitioner supplies no generated IDs,
context digest, Assignment Basis, predecessor, or transaction member.

The resulting initial Assignment Basis and Responsibility Assignment remain subject to the
canonical Responsibility validation contract. The pre-Case mandate is an allowed authority-source
family only for this exact initial obligation; it does not bypass Actor, owning-Case, exact-context,
obligation-signature, authority-source, Assignment-Basis, or assignment-coherence validation. Any
malformed initial responsibility plan rejects the complete Case-initiation transaction with zero
semantic mutation.

Case-initiation authority grants no later Value, Risk, adequacy, reliance, Integration, Decision,
review, closure, reopening, supersession, or other substantive authority. Those bases remain
just-in-time and independently governed. Login, practical role, Case coordination, authorship,
software create permission, Decision authority, or assessment authority cannot substitute for the
initiation mandate. Absent, plural, stale, withdrawn, inaccessible, Actor-mismatched, or
out-of-scope initiation authority rejects the natural command with zero semantic mutation. Exact
replay returns the original identities; changed management-use or other material payload is an
idempotency conflict.

## 4. State: OPEN

### Meaning

A management issue has been admitted into PAIM but the managed configuration may not yet be sufficiently defined.

### Minimum entry information

- Case ID
- Case title
- reason/trigger
- provisional management question
- case owner
- date opened
- known decision authority or authority gap
- related prior case/configuration if known

### Permitted activity

- refine management question;
- identify stakeholders;
- gather initial evidence;
- identify configuration elements;
- identify required analytical contributors;
- identify obvious authority gaps.

### Exit condition

Advance when the management object is sufficiently bounded to create a Managed Configuration Record.

### Prohibited interpretation

`OPEN` does not imply approval, experimentation permission, or acceptable risk.

## 5. State: CONFIGURATION_DEFINED

### Meaning

The AI-enabled system of work being evaluated has been explicitly bounded.

For PAIM v0.1, the state refers to the Case's one governing Configuration at the relevant effective time. Governing-Configuration selection must return exactly one eligible finalized Configuration, explicit absence/not established, or explicit conflict. A proposed, experimental, alternative, or fallback Configuration does not satisfy this state merely because it exists.

### Required elements

As relevant:

- AI capability/system;
- activity/process;
- users/affected parties;
- information/data;
- AI authority;
- human authority;
- controls;
- escalation/review;
- provider/model;
- operating conditions;
- dependencies;
- exclusions;
- configuration version.

### Exit condition

Advance when the configuration is sufficiently stable for evidence and analytical findings to be meaningfully bound to it.

If no governing Configuration is established, or if more than one Configuration claims to govern the Case at the same effective time, guarded progression is blocked until the absence or conflict is resolved through an accountable history-preserving action.

### Reversion condition

If configuration definition proves materially incomplete or changes during analysis, remain in or return to this state with a new configuration version.

## 6. State: EVIDENCE_ANALYSIS

### Meaning

Evidence, governing authority, Value analysis, and Risk analysis are being developed or refreshed.

### Required system behavior

The case must be able to associate evidence with:

- configuration version;
- source/provenance;
- analytical finding;
- authority status;
- date/context where material.

### Possible analytical statuses

Value and Risk may independently be:

- not started;
- in progress;
- ready;
- frozen;
- accepted/selected for a bounded use;
- refresh required;
- superseded.

`ready` is analytical readiness; `frozen` is immutable Input finalization; and `accepted/selected` is established only by an exact use-specific lane Acceptance/Selection Version. None implies either of the others.

### Exit condition

Advance only when each analytical lane has exactly one eligible selected/frozen Input Version and exact lane-specific Acceptance/Selection Version for the same governing Configuration Version and bounded Integration path/use. Input-selection absence, conflict, or ineligibility blocks advancement.

## 7. State: READY_FOR_INTEGRATION

### Meaning

The case has the minimum contributing material required for PAIM Decision Integration.

### Minimum readiness conditions

- exactly one governing Managed Configuration Record exists for the Case and effective time;
- exactly one eligible selected/frozen Value Management Input Version and Value Acceptance/Selection Version exist for this bounded use;
- exactly one eligible selected/frozen Risk Management Input Version and Risk Acceptance/Selection Version exist for this bounded use;
- both Inputs and acceptances refer to the exact governing Configuration Version;
- contributing boundaries are explicit;
- uncertainty is represented;
- provenance exists;
- material Evidence has exact current-context Evidence Applicability and accountable lane-level fitness treatment;
- material established constraints are recorded;
- material authority gaps are explicit;
- decision authority is identified or its absence is explicit.

A proposed, experimental, alternative, or fallback Configuration is not substituted for the governing Configuration. Governing-Configuration absence or conflict fails readiness; the platform must not select an alternative by recency, purpose, or convenience.

For either analytical lane, selection returns one eligible result, explicit `INPUT SELECTION NOT ESTABLISHED`, or explicit `INPUT SELECTION CONFLICT — UNRESOLVED`. Ready status, newest/latest date, owner, generic role, integrator participation, software permission, or row order cannot select or accept an Input.

Evidence Applicability absence, unresolved conflict, `NOT_APPLICABLE`, or unresolved material `REFRESH REQUIRED` blocks when required to support an Input's Finding, Boundary, or Implication. Conditional/partial Evidence cannot support beyond its recorded scope. `INDETERMINATE` requires the separate exact accountable lane-level fitness determination; there is no global allow/block default.

### Readiness does not mean

- Value and Risk agree;
- uncertainty is resolved;
- all authority gaps are closed;
- the final decision is obvious.

### Exit condition

Integration begins.

## 8. State: DECISION_PENDING

### Meaning

PAIM integration has been performed or is being finalized, but the accountable management decision has not yet been authorized.

### Required integration content

- constraints;
- authority gaps;
- Control Dependencies;
- Accepted and Decision-Limiting Uncertainty;
- Integrated Operating Boundary;
- alternatives;
- interaction analysis;
- proposed management judgment;
- rationale.

### Permitted outcomes

The proposed decision may include continuation, constraint, redesign, experiment, targeted scale, institutionalization, suspension, discontinuation, or another bounded state.

### Exit condition

An authorized Management Decision Record is created.

## 9. State: DECIDED

### Meaning

An accountable management judgment exists.

### Required decision content

- decision/action;
- selected AI operating state;
- Integrated Operating Boundary;
- rationale;
- Value evidence relied upon;
- Risk evidence relied upon;
- constraints/authority;
- Accepted Uncertainty;
- Decision-Limiting Uncertainty;
- conditions/limits;
- decision authority;
- decision date;
- required intervention.

### System requirement

The decision record becomes historical evidence and must not be silently rewritten.

Corrections or amendments must remain traceable.

### Exit possibilities

- intervention required → `INTERVENTION_IN_PROGRESS`;
- no material implementation action required, the exact Obligation Set explicitly yields `NOT_REQUIRED`, operation is aligned, and §11.1 activation guard passes → `OPERATING_OBSERVING`;
- decision is discontinue/close with no continuing observation requirement → `CLOSED`;
- decision supersedes another case → linked supersession.

## 10. State: INTERVENTION_IN_PROGRESS

### Meaning

The management judgment requires operational change that has not yet been fully implemented.

### Required intervention information

- action;
- owner;
- target/effective configuration;
- controls retained/changed;
- prohibited activities;
- fallback/escalation/remediation;
- implementation status;
- completion criteria.

The exact Decision-to-Intervention Obligation Set/Obligation Versions, requirement types, Completion Results, Completion Acceptances, and replacement/reuse relationships are governed by the Intervention and Learning specification. `COMPLETED` implementation status is not accepted completion.

### Possible statuses

Use the exact Intervention implementation-status vocabulary in the Intervention and Learning specification: `PROPOSED`, `PLANNED`, `IN_PROGRESS`, `BLOCKED`, `PARTIALLY_COMPLETED`, `COMPLETED`, `FAILED`, `CANCELLED`, and `SUPERSEDED`. Acceptance outcome and prerequisite result are separate.

### System behavior

The system should surface material overdue, blocked, or failed interventions.

### Exit condition

The target Configuration may exit to `OPERATING_OBSERVING` only through the exact activation guard in §11.1. Another authorized successor/amendment Decision may instead supersede or change the Intervention obligation package prospectively while preserving history.

## 11. State: OPERATING_OBSERVING

### Meaning

The AI-enabled configuration is operating under the current PAIM decision and boundary.

### Required system behavior

Maintain visibility into:

- current configuration;
- current operating state;
- current Integrated Operating Boundary;
- active controls;
- unresolved authority;
- Accepted Uncertainty;
- Decision-Limiting Uncertainty;
- learning items;
- observation signals;
- reassessment triggers.

### Important rule

Operation under a decision is not permanent approval.

### 11.1 Exact target-operation activation guard

An exact target Configuration may enter `OPERATING_OBSERVING` only when all of the following are established for the activation effective time and knowledge cutoff:

1. exactly one eligible authorized Decision governs the target activation context;
2. its exact target Configuration Version and finalized Boundary Snapshot match;
3. one exact current Decision-to-Intervention Obligation Set is established without conflict;
4. the aggregate `REQUIRED_BEFORE_OPERATION` result is `SATISFIED` or explicit `NOT_REQUIRED`;
5. every satisfied obligation has the exact current Completion Result and one eligible Completion Acceptance;
6. no blocking current obligation, Acceptance, replacement, Decision, Configuration, or Boundary conflict exists;
7. the target Configuration aligns with the Decision, Boundary, required controls/prohibitions, and accepted completion basis;
8. no effective successor/amendment Decision has changed or superseded the prerequisites;
9. `REQUIRED_AFTER_OPERATION` and `OPTIONAL` obligations are treated exactly under the Intervention specification and are not silently promoted or waived;
10. an explicit Activation Authorization binds the exact Decision, target Configuration, operating state, Boundary, effective time, and immutable Prerequisite Evaluation Basis; and
11. the Lifecycle Transition Event retains exact guard results, source versions, actor/mechanism, authority provenance, rationale, effective time, recorded time, and knowledge context.

Satisfied prerequisites alone never authorize operation. Activation authority is either the applicable Decision Authority acting explicitly or a genuine governed organizational activation mechanism explicitly pre-authorized in the exact Decision Authorization Basis, with exact rule/version/scope/authority retained. A software/technical rule, completed checklist, Case Owner, Intervention Owner, administrator permission, or technical principal alone cannot accept completion or authorize activation. A Case Owner or authorized workflow mechanism may record the transition only after every guard and Activation Authorization is established.

## 12. State: REASSESSMENT_DUE

### Meaning

A condition has occurred that requires management to determine whether the current decision remains valid.

### Trigger families

- incident/material error;
- Value deterioration or improvement;
- Risk change;
- control failure/change;
- provider/model change;
- scope expansion;
- autonomy/authority change;
- information/data change;
- operating-condition change;
- capacity change;
- authority resolution/change;
- completed learning experiment;
- scheduled reassessment;
- proposed stronger operating state.

### Required system behavior

Record:

- exact authoritative Trigger identity/Version, source provenance, and current Trigger Determination;
- date;
- affected configuration/decision;
- reason reassessment is required;
- whether operation may continue pending reassessment;
- required analytical refresh; and
- the current Trigger Coverage result, including explicit unassigned or conflict rather than reliance on a queue.

One Case lifecycle state may coexist with multiple Trigger and Reassessment identities. `REASSESSMENT_DUE` does not imply one Trigger ↔ one Reassessment, does not group Triggers, and does not select a Reassessment winner. Every eligible Trigger requiring reassessment remains subject to the no-lost-trigger coverage invariant in `PAIM_REASSESSMENT_SPEC_v0.1.md`, §38.5.

### Exit condition

The Case moves to `REOPENED` when at least one eligible current Trigger requires reassessment. It may return to `OPERATING_OBSERVING` without Reassessment only when every applicable current Trigger has one eligible non-reassessment Trigger Determination, no determination/coverage conflict remains, and the exact accountable rationale is retained. One immaterial Trigger does not clear another requiring, unassigned, or conflicting Trigger.

## 13. State: REOPENED

### Meaning

A prior decision is under active reconsideration.

### Reassessment questions

- Is the one governing Managed Configuration for the Case/effective time still the same, absent, or conflicting?
- Is a new configuration version required?
- Which evidence remains applicable?
- Which Value/Risk inputs require refresh?
- Has authority changed?
- Has uncertainty changed classification?
- Is the Integrated Operating Boundary still supportable?
- Does the operating state need to change?

### Possible routing

```text
REOPENED
   |
   +--> CONFIGURATION_DEFINED
   +--> EVIDENCE_ANALYSIS
   +--> READY_FOR_INTEGRATION
   +--> INTERVENTION_IN_PROGRESS / OPERATING_OBSERVING
        only after completed reassessment confirms the
        existing Decision unchanged
```

The route depends on what changed. The confirmation routes require the immutable Decision Confirmation and guards defined in `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, §§5.3 and 7.5. A substantive Decision, boundary, condition, configuration, or operating-state change proceeds through integration and an authorized successor/amendment Decision instead.

### Historical requirement

The prior decision remains intact as a historical record.

Multiple open Reassessments may coexist while the Case is `REOPENED` only under the exact non-overlap/eligible-coordination contract in `PAIM_REASSESSMENT_SPEC_v0.1.md`, §38.3. The single Case lifecycle state does not collapse their separate Reassessment statuses, Trigger Sets, scopes, owners, analyses, Interim Operating Dispositions, or outcomes.

One Reassessment completing, being cancelled, or being superseded does not automatically close another Reassessment or move the Case out of `REOPENED`. A transition from `REOPENED` that depends on Reassessment completion requires all affected eligible Triggers to have compatible current coverage, no unresolved overlap/coverage/current-governance conflict, and the exact completed outcome basis required by the Integrity specification. Remaining active, unassigned, or conflicting work keeps the applicable management condition visible.

## 14. State: CLOSED

### Meaning

The case no longer requires active PAIM management under its current identity.

Possible reasons:

- AI use discontinued;
- decision completed with no continuing management requirement;
- issue withdrawn;
- case merged into/superseded by another case;
- configuration retired.

### Required closure information

- closure reason;
- closure authority;
- date;
- final configuration/decision status;
- unresolved items, if any;
- successor case/configuration, if any;
- record-retention status.

Closure must not delete history.

## 15. State: SUPERSEDED

### Meaning

Another case, configuration, or decision has explicitly replaced the current one.

### Required linkage

- superseding case/record;
- reason;
- effective date;
- authority;
- relationship of prior evidence to successor.

`SUPERSEDED` is terminal for active management but remains part of history.

## 16. Transition Rules

The rules below state substantive lifecycle invariants. The exhaustive allowed-transition table, transition actors/mechanisms, required Transition Event, subordinate-record effects, and closure/reopening behavior are governed by `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, §5. A transition not listed there is invalid.

### 16.1 No silent forward transition

Each transition must have an identifiable basis.

### 16.2 No evidence-free integration

A case cannot be `READY_FOR_INTEGRATION` without exactly one eligible selected/frozen Value Input and Acceptance/Selection Version and exactly one eligible selected/frozen Risk Input and Acceptance/Selection Version for the same governing Configuration Version and bounded use. Required material-Evidence Applicability/fitness guards must also pass.

### 16.3 No unauthorized decision

A case cannot become `DECIDED` without an identified decision authority or explicitly defined authorization mechanism.

### 16.4 No silent configuration substitution

A material configuration change requires explicit version/change handling.

### 16.5 No silent closure of uncertainty

Uncertainty remains until evidence supports a change in status/classification.

### 16.6 No silent authority resolution

`AUTHORITY UNRESOLVED` may change only when governing authority/evidence is obtained or the decision is reframed so the unresolved authority is no longer material.

### 16.7 No silent Reassessment coordination or closure

Trigger grouping, Reassessment coexistence, duplicate disposition, overlap resolution, cancellation, supersession, and Trigger coverage transfer require their exact accountable records. A new Decision, Configuration, Trigger, Reassessment row, timestamp, severity, queue position, or status never groups, closes, cancels, or supersedes another Reassessment automatically.

Before a Reassessment-dependent lifecycle transition, the platform prospectively revalidates the exact current Decision/Configuration, Trigger coverage, overlap/coordination, accountability, authority, and outcome at effective time and optional knowledge cutoff. A predecessor-bound Reassessment cannot complete as current after a successor Decision becomes effective; continuing work uses the explicit successor-Reassessment and Trigger carry-forward contract.

## 17. Case Trigger Model

A new case or reassessment may be triggered by:

### Initiation triggers

- proposed new AI use;
- proposed pilot/experiment;
- proposed internalization or outsourcing change;
- proposed automation/autonomy increase.

### Evidence triggers

- completed experiment;
- realized Value evidence;
- new Risk evidence;
- new control-effectiveness evidence.

### Change triggers

- model/provider change;
- workflow change;
- data/information change;
- control change;
- user/customer population change;
- material volume/capacity change.

### Management triggers

- proposed scale;
- proposed institutionalization;
- proposed scope expansion;
- proposed suspension/discontinuation.

### Adverse triggers

- incident;
- material error;
- control failure;
- boundary breach.

### Authority triggers

- new policy;
- contract change;
- regulatory/legal change;
- previously unresolved authority resolved.

## 18. Reopen vs. New Case Decision

Use **reopen** when:

- the management object remains substantially the same;
- the prior decision is being reassessed;
- continuity of history is important.

Use a **new/successor case** when:

- the configuration is materially different;
- the management question is materially different;
- evidence cannot reasonably transfer;
- the prior case should remain independently interpretable.

PAIM v0.1 also uses separately linked Cases when independent Configurations must govern concurrently. Each Configuration identity has exactly one owning Case, and each linked Case independently resolves one governing Configuration, explicit absence, or explicit conflict for an effective time. A second governing Configuration must not be added to one Case as a concurrency shortcut.

The Managed Configuration specification should define the material-change test in greater detail.

The reopen/new-Case and same-identity/new-identity judgments require the explicit accountable assignment/mechanism and determination history defined by the Managed Configuration and Roles specifications. Vacancy or incompatible accountability conflict blocks routing that depends on the unresolved judgment.

## 19. Case Relationships

The lifecycle must support explicit relationships such as:

- predecessor / successor;
- reopened from;
- supersedes / superseded by;
- related configuration;
- related incident;
- related experiment;
- related authority review;
- parent/portfolio grouping where later required.

Linked Cases preserve independent governing-Configuration currentness. A Case relationship does not create joint Configuration ownership, silently transfer evidence, or resolve cross-Case dependency/equivalence semantics deferred under IRR-012.

## 20. Lifecycle Roles

At minimum:

### Case owner

Coordinates case progression and completeness.

### Value evaluator

Owns/produces Value Management Input.

### Risk evaluator

Owns/produces Risk Management Input.

### Decision authority

Authorizes the management judgment.

### Intervention owner

Implements required action.

### Evidence/authority owner

Maintains or resolves relevant evidence/authority where assigned.

### Reviewer/auditor

May inspect traceability and process integrity.

Detailed permissions are deferred to `PAIM_ROLES_AND_ACCOUNTABILITY_SPEC`.

For every lifecycle record or judgment that requires accountability, resolution must return exactly one accountable Role Assignment or one explicitly governed accountable mechanism, explicit vacancy/not established, or explicit incompatible-accountability conflict. Multiple compatible role performers may contribute, but an unqualified peer set is not treated as co-accountable. Broad and narrow Role Assignments have no implicit precedence.

## 21. Minimum Lifecycle Events

The system should preserve events for:

- case opened;
- configuration defined/versioned;
- Value Input created/ready/frozen/reused/rejected/withdrawn/superseded and Value Acceptance/Selection history;
- Risk Input created/ready/frozen/reused/rejected/withdrawn/superseded and Risk Acceptance/Selection history;
- Evidence Applicability finalized/corrected/superseded/withdrawn and lane-level fitness determination;
- ready-for-integration declared;
- integration completed;
- decision authorized;
- intervention opened/completed/failed;
- operating state changed;
- reassessment trigger raised;
- case reopened;
- successor decision authorized;
- case closed;
- case superseded.

A platform may implement these as event records, audit entries, or equivalent durable history. Every lifecycle-state change must preserve the immutable Lifecycle Transition Event required by `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, §5.1.

## 22. Lifecycle Integrity Checks

Before important transitions, the system should be able to detect:

### Before READY_FOR_INTEGRATION

- missing governing Configuration;
- conflicting governing Configurations for the same Case/effective time;
- non-governing proposed, experimental, alternative, or fallback Configuration offered as the governing Configuration;
- missing, ineligible, or conflicting Value Input Acceptance/Selection;
- missing, ineligible, or conflicting Risk Input Acceptance/Selection;
- mismatched configuration;
- missing boundaries;
- missing provenance;
- unrepresented material authority gap;
- selected Input rejected/withdrawn before readiness or reused without a new acceptance;
- material Evidence Applicability absent, conflicting, not applicable, refresh-required, or narrower than the claimed Input Boundary;
- `INDETERMINATE` material Evidence without the separate bounded lane-level fitness determination;
- acceptance or Applicability accountability vacant, conflicting, unrelated in scope, or inferred from permission/authorship;
- missing or conflicting accountable assignment/mechanism for a required materiality, identity-continuity, or lifecycle judgment.

### Before DECIDED

- missing integration record;
- missing decision authority;
- missing Integrated Operating Boundary;
- missing rationale;
- unclassified material uncertainty.

### Before OPERATING_OBSERVING

- exact Obligation Set absent or conflicting;
- required-before aggregate `NOT_ESTABLISHED`, `INCOMPLETE`, `BLOCKED`, or `CONFLICT`;
- `COMPLETED` Intervention lacking an eligible exact Completion Acceptance;
- Completion Acceptance accountability vacant, conflicting, delegated through an invalid chain, or unrelated in scope;
- incompatible current replacement/reuse relationship;
- configuration not aligned with decision;
- required controls absent;
- prohibited activity unresolved;
- effective successor/amendment Decision changed the prerequisite package;
- Prerequisite Evaluation Basis missing or incomplete;
- Activation Authorization missing, out of scope, or inferred from a checklist, ownership, permission, or technical principal; or
- pre-authorized mechanism lacking exact governed organizational rule/version/scope/authority provenance.

### Before CLOSED

- unresolved intervention status;
- missing closure authority/reason;
- missing successor linkage where superseded.

These are management-system integrity checks, not universal automated approval rules.

## 23. Human Judgment Points

The lifecycle should not automate away judgment.

Human/accountable judgment is especially required for:

- defining whether a configuration change is material;
- deciding whether evidence is sufficient for integration;
- classifying uncertainty relative to a decision;
- choosing among alternatives;
- selecting operating state;
- authorizing decision;
- deciding whether reassessment changes the boundary/state;
- determining whether a case should close or be superseded.

Every required judgment must preserve the accountable Role Assignment or accountable mechanism, scope, rationale, effective time, recorded time, and history where the governing specification requires it. Technical principal identity, software permission, role participation, and accountability remain distinct; none establishes Decision Authority without the complete Decision Authorization Basis.

## 24. Platform Implications

A future platform will likely require:

- case dashboard;
- lifecycle status;
- transition controls;
- role-based actions;
- configuration/version view;
- readiness indicators;
- decision authorization;
- intervention tracking;
- reassessment queue;
- history/audit view.

This specification does not prescribe the UI.

## 25. Behavioral Test Candidates

Future system testing should include:

1. Attempt integration without a Risk Input → system should not represent the case as ready.
2. Change configuration materially after decision → prior evidence/decision should not silently transfer.
3. Resolve an authority gap → case should support reassessment.
4. Remove a required control → current boundary/decision should be flagged for reassessment.
5. Complete a learning experiment → linked blocked decision should become eligible for reconsideration.
6. Attempt to overwrite a historical decision → system should preserve prior record.
7. Close a case with incomplete mandatory intervention → system should surface the inconsistency.
8. Propose institutionalization from bounded continuation → case should reopen/reassess rather than silently change operating state.
9. Present two governing Configurations for one Case/effective time → guarded progression should remain blocked with explicit conflict.
10. Present only a proposed/experimental/fallback alternative → it should not satisfy the governing-Configuration guard.
11. Require independent concurrent governing Configurations → use linked Cases and preserve one owning Case per Configuration identity.
12. Require a materiality or identity-continuity judgment with vacant or conflicting accountability → block the dependent transition and preserve the unresolved outcome.

Expected detailed behavior will be defined in the system behavioral validation strategy.

## 26. Open Questions

The following remain intentionally open for later specifications:

- exact material-change test for configuration;
- formal evidence maturity states;
- exact authorization/signature model;
- organization-specific workflow presentation around the canonical transition contract;
- closure/retention requirements;
- cross-case portfolio relationships;
- notification/escalation timing;
- system-generated vs. human-entered triggers.

## 27. Completion Impact

This specification materially advances the **Management Entry and Intake** and **Case Lifecycle** gaps identified in the completion baseline.

It does not complete:

- Managed Configuration specification;
- Evidence/Authority model;
- record schemas;
- platform workflow implementation;
- human validation.

## 28. Next Specification

Create:

`PAIM_MANAGED_CONFIGURATION_SPEC_v0.1.md`

This should define:

- configuration identity;
- configuration elements;
- versioning;
- material change;
- predecessor/successor relationships;
- evidence applicability;
- boundary relationships;
- current/effective configuration semantics.

## 29. Repository Placement

```text
400. Practical AI Management/
└── system/
    └── specifications/
        └── PAIM_CASE_LIFECYCLE_SPEC_v0.1.md
```

## 30. Conclusion

The PAIM case lifecycle converts the analytical method into a durable management process.

It ensures that a PAIM decision is not an isolated document but part of a traceable sequence:

> **management issue → bounded configuration → evidence → integration → authorized decision → intervention → operation → observation → reassessment → successor decision or closure**

That lifecycle is a foundational requirement for the eventual PAIM platform.
