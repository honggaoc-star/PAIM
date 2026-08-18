# PAIM Case Lifecycle Specification v0.1

## Status

Implementation-independent system specification for the lifecycle of a Practical AI Management (PAIM) case.

This specification derives from:

- `PAIM_SYSTEM_ARCHITECTURE_v0.1.md`
- `PAIM_SYSTEM_COMPLETION_BASELINE_GAP_MAP_v0.1.md`
- `PAIM_MINIMUM_MANAGEMENT_CASE_v0.3.md`
- `PAIM_PRACTITIONER_PLAYBOOK_v0.2.md`

It defines **what lifecycle behavior the PAIM system must support**. It does not prescribe software implementation.

**Normative cross-cutting contract:** `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md` governs authoritative record identity/version/currentness, the complete allowed lifecycle transition table and guards, Decision Authorization Basis, operation during intervention/reassessment, and Interim Operating Disposition. This specification continues to govern the substantive meaning of each case state.

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
