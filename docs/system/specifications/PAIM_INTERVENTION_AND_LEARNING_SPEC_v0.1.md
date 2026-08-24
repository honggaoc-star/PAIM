# PAIM Intervention and Learning Specification v0.1

## Status

Implementation-independent system specification for **Intervention, Execution, Decision-Specific Learning, and their relationship to management decisions** in Practical AI Management (PAIM).

This specification derives from:

- `PAIM_SYSTEM_ARCHITECTURE_v0.1.md`
- `PAIM_SYSTEM_COMPLETION_BASELINE_GAP_MAP_v0.1.md`
- `PAIM_CASE_LIFECYCLE_SPEC_v0.1.md`
- `PAIM_MANAGED_CONFIGURATION_SPEC_v0.1.md`
- `PAIM_EVIDENCE_AND_AUTHORITY_SPEC_v0.1.md`
- `PAIM_VALUE_RISK_INTERFACE_SPEC_v0.1.md`
- `PAIM_INTEGRATION_AND_DECISION_SPEC_v0.1.md`
- `PAIM_MINIMUM_MANAGEMENT_CASE_v0.3.md`
- `PAIM_PRACTITIONER_PLAYBOOK_v0.2.md`
- IET 001–004 validation findings.

It defines what the PAIM system must preserve after a management judgment has been authorized: what must change, who owns the change, how implementation status is tracked, what evidence must be generated, and how learning remains tied to future decisions.

It does not prescribe project-management software, workflow technology, notification mechanisms, or user-interface design.

**Normative cross-cutting contract:** `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md` governs authoritative Intervention/Learning identity and versions, finalization, status events, recorded/effective time, correction/supersession/withdrawal, exact history, lifecycle effects of blocked/failed/cancelled subordinate records, and operation under the current Decision while target intervention is incomplete.

## 1. Purpose

A PAIM decision is incomplete if it does not lead to action where action is required.

The system must be able to answer:

> **What changes because of this decision?**

> **Who is responsible?**

> **What configuration is supposed to operate afterward?**

> **Which controls must remain or change?**

> **What is prohibited?**

> **What happens if implementation fails or cannot be completed?**

> **What evidence must be generated because a stronger or different decision remains blocked?**

Intervention converts judgment into managed operational change.

Learning converts uncertainty into a deliberate evidence-generation process.

## 2. Intervention Principle

The relationship is:

```text
Authorized Management Decision
            |
            v
     Intervention Requirement
            |
            v
      Intervention Record
            |
            v
   Operational Configuration
            |
            v
 Observation / Evidence Generation
            |
            v
          Learning
            |
            v
       Reassessment
```

Not every decision requires a large intervention.

A decision to continue an already-aligned configuration may require only confirmation of existing conditions and observation.

A decision to constrain, redesign, suspend, or scale may require substantial intervention.

## 3. Intervention Is Distinct from the Decision

The Management Decision Record states **what management has decided**.

The Intervention Record states **how that judgment is implemented operationally**.

Example:

```text
Decision:
Continue only within bounded public-information research.

Intervention:
Restrict eligible assignment categories,
retain analyst verification,
establish escalation for excluded work,
and configure the operating workflow accordingly.
```

The system must not merge the two into an ambiguous action paragraph.

## 4. Intervention Identity

Every material Intervention Record should have a durable identity.

Minimum identity fields:

- Intervention ID
- Intervention Version ID
- Case ID
- Decision ID/version
- Configuration ID/version
- intervention version
- title
- status
- owner
- date created
- target/effective date where relevant
- completion date where relevant
- recorded time and effective time/interval
- predecessor/successor intervention where applicable

## 5. Intervention Status

The normative PAIM v0.1 implementation statuses are exactly:

- `PROPOSED`;
- `PLANNED`;
- `IN_PROGRESS`;
- `BLOCKED`;
- `PARTIALLY_COMPLETED`;
- `COMPLETED`;
- `FAILED`;
- `CANCELLED`; and
- `SUPERSEDED`.

Overdue or other attention state is a status event/attention condition, not a completion outcome. Intervention implementation status, Completion Result, Completion Acceptance, prerequisite satisfaction, and Activation Authorization are separate facts. `COMPLETED` never means accepted complete by itself.

A completed decision does not imply that its intervention has been completed.

Status changes do not mutate finalized intervention content. A substantive change to scope, target configuration, required control, completion criteria, fallback, or management consequence creates a new immutable Intervention version under `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, §3.

## 6. Provenance of Intervention Content

PAIM must distinguish at least three sources of intervention content.

### Evidence-supported requirement

A condition directly supported by contributing evidence, governing authority, or the analytical boundary.

Example:

> Analyst verification must remain because the current Risk finding depends on it.

### PAIM management judgment

A condition selected by management during integration.

Example:

> Limit operation to selected assignment classes.

### Proposed intervention design

An implementation choice selected to operationalize the judgment.

Example:

> Route excluded assignments to a named external-provider workflow.

The platform should not present practitioner-designed implementation details as though they were established facts.

## 7. Intervention Scope

An intervention may affect:

- Managed Configuration;
- AI authority;
- human authority;
- task/scope;
- information/data;
- controls;
- threshold;
- escalation/review;
- provider/model;
- workload/capacity;
- operating state;
- external sourcing;
- monitoring;
- authority resolution;
- system access;
- other management conditions.

## 8. Target Configuration

Where intervention changes the configuration, the Intervention Record must identify the intended target configuration/version.

Example:

```text
Current configuration: CFG-001 v1
Decision: constrain and redesign
Target configuration: CFG-001 v2
```

The intervention should not silently mutate the historical configuration.

Material configuration change follows `PAIM_MANAGED_CONFIGURATION_SPEC_v0.1.md`.

## 9. Intervention Requirements

For each material intervention, record:

- what changes;
- why;
- provenance category;
- owner;
- target configuration;
- controls retained;
- controls added/changed/removed;
- prohibited activities;
- escalation/fallback;
- completion criteria;
- dependencies;
- implementation status;
- evidence generated;
- reassessment consequence.

## 10. Intervention Ownership

Every material intervention should have an accountable owner or explicitly unresolved ownership.

Ownership may belong to:

- case owner;
- business/process owner;
- technical owner;
- control owner;
- external-provider manager;
- other accountable role.

Detailed role permissions are deferred to `PAIM_ROLES_AND_ACCOUNTABILITY_SPEC_v0.1.md`.

## 11. Completion Criteria

An intervention should not be marked complete solely because work was attempted.

Completion criteria should state what must be true operationally.

Examples:

- prohibited scope removed;
- required review active;
- target threshold implemented;
- fallback available;
- human final authority restored;
- new configuration deployed;
- evidence-generation mechanism active.

Completion criteria may be qualitative or quantitative.

### 11.1 Decision-to-Intervention Obligation and Obligation Set

Every authorized Decision Version must have one authoritative **Decision-to-Intervention Obligation Set Version**, including when the set explicitly contains no obligations. The set and each contained **Obligation Version** have stable record identity, immutable version identity, effective/recorded time, current-selection, correction, amendment, supersession, and exact-history semantics under the Integrity specification.

An Obligation Version binds at minimum:

- exact Decision ID/Version;
- exact target Configuration ID/Version;
- exact Intervention ID and required Intervention Version, or one explicit allowed successor/replacement relationship;
- requirement type;
- completion criteria or exact governing Intervention-Version reference;
- relevant Boundary clauses, Decision conditions, controls, and prohibitions;
- rationale and provenance;
- effective and recorded time; and
- predecessor, amendment, supersession, replacement, and reuse relationships where applicable.

The requirement belongs to the exact Decision obligation package. It is not a Configuration-global or Intervention-global property and does not transfer to another Decision implicitly.

The normative v0.1 requirement types are exactly:

- `REQUIRED_BEFORE_OPERATION` — target operation is blocked until the obligation is satisfied;
- `REQUIRED_AFTER_OPERATION` — initial target operation may precede completion only when the exact Decision explicitly permits that timing and retains its conditions; and
- `OPTIONAL` — the Intervention does not block target activation and never becomes mandatory through age, operator preference, or software configuration.

Learning remains a separate record family and is not another Intervention requirement type.

### 11.2 Completion Result

A **Completion Result** has stable identity and immutable Versions. A finalized Completion Result Version contains at minimum:

- exact Intervention Version;
- exact Obligation Version;
- exact Decision and target Configuration Versions;
- criterion-by-criterion results using exactly `MET`, `NOT_MET`, or `INDETERMINATE`;
- exact Evidence Record/Version references and provenance;
- performer/attestor actor;
- limitations, residual exposure, and fallback/remediation state;
- effective and recorded time; and
- immutable correction/supersession history.

Every required criterion must be `MET` before a Completion Acceptance may be eligible. This is a mechanical eligibility condition only. Work status, evidence presence, or all-`MET` criteria never creates Completion Acceptance.

### 11.3 Completion Acceptance

A **Completion Acceptance** has stable identity and immutable Versions distinct from the Completion Result. Its minimum content is:

- exact Obligation, Intervention Version, and Completion Result Version;
- exact Decision and target Configuration Versions;
- exact material Boundary/condition references;
- outcome exactly `ACCEPTED` or `REJECTED`;
- rationale, exceptions, and limitations;
- accountable actor plus exact applicable Role Assignment Version or explicitly governed organizational mechanism;
- exact delegation/supersession provenance where used;
- effective and recorded time; and
- correction, withdrawal, and supersession history.

For one exact obligation, effective time, and optional knowledge cutoff, authoritative selection returns one eligible Acceptance, `ACCEPTANCE NOT ESTABLISHED`, or `COMPLETION ACCEPTANCE CONFLICT — UNRESOLVED`. No newest, specificity, breadth, ownership, directory, hierarchy, row-order, or software-permission winner is permitted.

Acceptance accountability and any delegation must be valid at the Acceptance effective time. Later routine role expiry does not rewrite a historically valid Acceptance. A corrected, withdrawn, or superseded Acceptance is prospectively ineligible for a future activation, while the historical basis remains reconstructable.

### 11.4 Per-obligation result

The normative per-obligation results are exactly `SATISFIED`, `NOT_ESTABLISHED`, `INCOMPLETE`, `BLOCKED`, and `CONFLICT`:

| Current authoritative facts | Obligation result |
|---|---|
| `COMPLETED` plus one eligible current `ACCEPTED` Acceptance for the exact Completion Result | `SATISFIED` |
| `COMPLETED` plus no eligible Acceptance | `NOT_ESTABLISHED` |
| `COMPLETED` plus current `REJECTED` Acceptance | `BLOCKED` |
| `PROPOSED`, `PLANNED`, `IN_PROGRESS`, or `PARTIALLY_COMPLETED` | `INCOMPLETE` |
| `BLOCKED`, `FAILED`, or `CANCELLED` without one valid current replacement | `BLOCKED` |
| `SUPERSEDED` required Intervention without one exact valid current replacement relationship | `NOT_ESTABLISHED` |
| incompatible current results, Acceptances, obligations, or replacements | `CONFLICT` |

A `SUPERSEDED` predecessor is excluded prospectively only through one exact valid current replacement. Two incompatible replacements are `CONFLICT`; no valid replacement is `NOT_ESTABLISHED`. Historical predecessors remain reconstructable.

### 11.5 Aggregate prerequisite satisfaction

For one exact Decision Version, target Configuration Version, effective time, and optional knowledge cutoff, select one eligible current Obligation Set, explicit absence, or explicit conflict. Evaluate every current `REQUIRED_BEFORE_OPERATION` obligation using an all-of rule. PAIM v0.1 does not define one-of-N groups, ordered prerequisites, condition expressions, recurrence, or a generic workflow language.

The normative aggregate results are exactly `SATISFIED`, `NOT_REQUIRED`, `NOT_ESTABLISHED`, `INCOMPLETE`, `BLOCKED`, and `CONFLICT`. Derivation is staged rather than scored:

1. Obligation Set conflict returns `CONFLICT`; absence returns `NOT_ESTABLISHED`.
2. One explicit eligible set with zero required-before obligations returns `NOT_REQUIRED`; missing data never does.
3. Any required relationship/result/Acceptance/replacement conflict returns `CONFLICT`.
4. Required exact source absence returns `NOT_ESTABLISHED`.
5. Any terminal unsatisfied required-before obligation returns `BLOCKED`.
6. Any remaining non-terminal unsatisfied required-before obligation returns `INCOMPLETE`.
7. Only all required-before obligations `SATISFIED` returns aggregate `SATISFIED`.

Every contributing result and diagnostic remains available; the aggregate is not a universal Intervention score.

### 11.6 Prerequisite Evaluation Basis

Current aggregate satisfaction is deterministically derived from authoritative Obligation Set/Obligation, Intervention, Completion Result, Completion Acceptance, replacement, and reuse records. Any cache or projection is non-authoritative and rebuildable.

Every target activation retains one immutable **Prerequisite Evaluation Basis** containing the exact relied-upon versions, per-obligation and aggregate results, effective time, recorded time, and knowledge cutoff sufficient for historical reconstruction.

### 11.7 Fallback, remediation, and replacement

Fallback or remediation satisfies an obligation only through an explicit replacement/successor relationship and its own exact Completion Result plus eligible Completion Acceptance. If it changes operating state, Boundary, target Configuration, or a substantive Decision condition, an authorized successor/amendment Decision is required. The label `fallback` never supplies authority or satisfaction.

### 11.8 Successor Decision and reuse

Every substantive successor/amendment Decision has its own exact Obligation Set. Prior Completion Results or Acceptances never carry forward silently. Reuse requires an exact accountable continued-validity determination covering unchanged relevant Configuration content, Boundary/conditions, completion criteria, Evidence applicability, and acceptance scope. A changed target Configuration requires explicit coverage of the new Version. Absent eligible reuse, the successor obligation is `NOT_ESTABLISHED`.

Removal, replacement, and reuse operate prospectively and preserve predecessor history. Later role, Evidence, Intervention, Acceptance, Decision, or obligation change never rewrites the historical Decision or activation basis.

### 11.9 Required-after-operation and optional commitments

Incomplete `REQUIRED_AFTER_OPERATION` does not block initial activation only under the exact Decision permission and retained timing/conditions. It remains a mandatory visible commitment; later overdue, blocked, failed, cancelled, or materially partial state creates attention through existing extension points but does not silently change the Decision.

A required-after Obligation without that exact Decision permission or required timing/conditions makes the Obligation Set ineligible for activation and returns aggregate `NOT_ESTABLISHED`; the platform must not silently treat the item as optional.

Incomplete `OPTIONAL` never blocks activation. Neither category resolves Reassessment, Interim Operating Disposition, Observation, Register, or operating-state-ranking semantics.

### 11.10 Prospective Intervention Responsibilities

After explicit cutover, `PERFORM_INTERVENTION` binds the exact owning Case, Decision Version,
target Configuration Version, Intervention Version, and Decision-to-Intervention Obligation
Version. `ACCEPT_INTERVENTION_COMPLETION` additionally binds the exact Completion Result Version.
The two Responsibilities resolve independently. Intervention performance, authorship, ownership,
Work assignment, access, or practical role does not establish Completion Acceptance accountability.

Work may coordinate performance or acceptance but cannot create a Completion Result or Completion
Acceptance. Assignment creates neither, and it grants no Decision or Activation Authority. Existing
Role Assignment behavior remains controlling for each consumer until its explicit cutover.

## 12. Intervention Dependencies

An intervention may depend on:

- another intervention;
- authority resolution;
- technical change;
- provider action;
- staffing/capacity;
- evidence availability;
- training;
- control implementation;
- external sourcing.

The system should preserve dependencies where they affect readiness or operation.

## 13. Blocked Intervention

If intervention cannot proceed, record:

- blocking condition;
- affected decision/configuration;
- owner;
- operational consequence;
- whether current operation may continue;
- escalation required;
- reassessment required.

A blocked intervention must not disappear into a generic overdue status.

## 14. Failed Intervention

A failed intervention occurs when implementation does not achieve the required operational condition.

Possible responses include:

- remediate;
- restore prior configuration;
- invoke fallback;
- suspend;
- redesign;
- reopen PAIM decision.

Failure should be treated as management evidence.

## 15. Partial Completion

Partial completion must remain visible when some but not all required conditions are implemented.

The system should identify:

- completed elements;
- incomplete elements;
- whether operation is permitted;
- residual exposure;
- required escalation/reassessment.

## 16. Fallback

A fallback is a defined operational alternative used when the authorized configuration cannot operate within its boundary.

Examples:

- manual processing;
- external provider;
- human-only review;
- prior validated configuration;
- temporary suspension.

Fallback is not automatically risk-free or value-neutral.

Its evidence and limitations should remain explicit.

## 17. Remediation

Remediation is action intended to restore the current configuration to the authorized boundary after a failure, deviation, or incident.

Remediation should identify:

- deviation;
- required corrective action;
- owner;
- completion criteria;
- evidence of restoration;
- reassessment requirement.

## 18. Boundary Breach

A boundary breach occurs when operation moves outside the current Integrated Operating Boundary.

Examples:

- unsupported assignment type;
- missing required control;
- increased AI authority;
- workload beyond supported capacity;
- prohibited information use;
- unapproved threshold change.

A material breach should be capable of triggering:

- intervention;
- fallback;
- suspension;
- reassessment;
- incident handling where relevant.

## 19. Learning Principle

PAIM learning is not generic monitoring.

A Learning Item should answer:

> **What do we need to learn because a decision is blocked, conditional, or potentially revisable?**

The canonical relationship is:

```text
Missing Evidence
      |
      v
Blocked / Conditional Decision
      |
      v
Learning Item
      |
      v
Evidence Generation
      |
      v
Reassessment
      |
      v
Decision May Change
```

## 20. Learning Item Identity

Every material Learning Item should have:

- Learning Item ID
- Case ID
- Decision ID/version
- Configuration ID/version
- related uncertainty
- blocked/conditional decision
- status
- owner
- date created
- target/review date where relevant
- evidence-generation method
- completion/result linkage

## 21. Learning Item Status

Possible statuses include:

- proposed;
- active;
- awaiting evidence;
- completed;
- inconclusive;
- cancelled;
- superseded.

Completion does not necessarily mean the uncertainty is resolved.

## 22. Learning Item Content

Minimum content:

- missing evidence;
- uncertainty addressed;
- decision currently blocked/conditional;
- evidence to generate;
- proposed method;
- owner;
- observation period/condition where relevant;
- decision that may change;
- completion condition;
- known limitations.

## 23. Learning Design Provenance

The system should distinguish:

### Evidence-required learning

The analytical record establishes that particular evidence is required.

### Practitioner-proposed learning design

Management/practitioners choose how to generate that evidence.

Example:

```text
Evidence requirement:
Prospective evidence of selective-control effectiveness.

Proposed learning design:
Run a bounded 1,000-case prospective experiment.
```

The experiment size/design is not automatically an evidence-supported requirement unless separately established.

## 24. Learning and Decision-Limiting Uncertainty

Decision-Limiting Uncertainty should normally link to one or more:

- Learning Items;
- Authority Gaps;
- external evidence dependencies.

The system should make visible when a blocked decision has no path to evidence generation or authority resolution.

## 25. Learning and Accepted Uncertainty

Accepted Uncertainty may also generate observation or learning.

The difference is that the current decision may proceed.

The system should preserve:

- why accepted now;
- what is being observed;
- what change would make it Decision-Limiting.

## 26. Observation vs. Learning

Observation tracks signals relevant to whether the current decision remains valid.

Learning is targeted evidence generation tied to a decision question.

Example:

```text
Observation:
Track factual-error rate.

Learning:
Determine whether a selective verification redesign is sufficient for normal operation.
```

The same evidence may contribute to both.

## 27. Learning Evidence

Evidence generated by a Learning Item becomes an Evidence Record under `PAIM_EVIDENCE_AND_AUTHORITY_SPEC_v0.1.md`.

The Learning Item should link to:

- generated Evidence Record(s);
- result;
- limitations;
- affected uncertainty;
- reassessment trigger.

## 28. Learning Completion

A Learning Item may complete as:

- supports stronger decision;
- supports current decision only;
- supports narrower decision;
- contradicts prior assumption;
- inconclusive;
- reveals new uncertainty;
- reveals new authority question.

The system should not force every completed learning activity into a favorable result.

### 28.1 Prospective Learning Responsibility

After explicit cutover, `OBTAIN_LEARNING_EVIDENCE` binds the exact owning Case, Decision Version,
target Configuration Version, Learning Item Version, required Evidence/result contract, and time.
The Responsibility and any Work coordinate acquisition; only the Evidence and Learning commands
create their governed results. Completion does not interpret Learning, change a Decision, establish
causality, or complete an independent prerequisite.

## 29. Intervention and Learning Interaction

Intervention and learning may occur together.

Example:

```text
Intervention:
Use stronger universal control now.

Learning:
Test selective control redesign.

Future decision:
Determine whether lower-burden configuration can replace universal control.
```

This pattern was important in Type A conflict validation.

## 30. Intervention and Operating State

Different operating states may imply different intervention burdens.

Case lifecycle state `INTERVENTION_IN_PROGRESS` may coexist with continued operation under the prior/current authorized Decision. The target configuration must not become operating merely because intervention has begun. The governing coexistence and transition rules are in `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, §§5.3 and 5.6.

Satisfied prerequisites alone never authorize target operation. Entry into `OPERATING_OBSERVING` requires the exact Prerequisite Evaluation Basis and Activation Authorization governed by the Case Lifecycle and Integrity specifications. Activation authority is either an applicable Decision Authority acting explicitly or a genuine governed organizational activation mechanism explicitly pre-authorized in the exact Decision Authorization Basis, with its rule/version/scope/authority retained. A technical/software rule, checklist, Case Owner, Intervention Owner, administrator permission, or technical principal alone is not such a mechanism.

Examples:

### Experiment

- establish bounded test configuration;
- define safeguards;
- define evidence-generation plan.

### Bounded continuation

- preserve current controls/boundary;
- correct deviations;
- observe.

### Targeted scale

- implement capacity/control changes;
- verify evidence applicability to expanded scope.

### Institutionalization

- establish durable ownership/process;
- ensure evidence and authority support the stronger state.

### Suspension

- stop relevant operation;
- preserve evidence;
- define remediation/reassessment.

### Discontinuation

- retire configuration;
- close/supersede case;
- preserve history.

## 31. Intervention Integrity Checks

The system should surface:

- decision requires intervention but none exists;
- intervention has no owner;
- target configuration undefined;
- required control omitted;
- intervention marked complete without completion criteria;
- blocked intervention with operation continuing outside boundary;
- failed intervention with no escalation/reassessment;
- prohibited activity still active;
- fallback unavailable where required.

These checks support management integrity rather than replace judgment.

## 32. Learning Integrity Checks

The system should surface:

- Decision-Limiting Uncertainty with no evidence/authority path;
- Learning Item not tied to a decision;
- learning method presented as evidence-supported when practitioner-designed;
- completed Learning Item with no resulting evidence;
- evidence generated but not linked to reassessment;
- blocked decision changed without resolving relevant uncertainty;
- learning result silently overwriting historical evidence.

## 33. Overdue Intervention

The platform should eventually support attention to overdue intervention.

The system specification requires only that overdue status can be represented and related to:

- decision;
- boundary;
- operational consequence;
- escalation;
- reassessment.

No universal deadline is prescribed.

## 34. Overdue Learning

Learning may be overdue relative to a management commitment or decision condition.

The system should distinguish:

- overdue but current decision still supportable;
- overdue and stronger decision remains blocked;
- overdue and current decision now requires reassessment.

## 35. Intervention History

Intervention history should remain non-destructive.

Example:

```text
INT-001 v1 — planned
INT-001 v2 — revised implementation
INT-001 — completed

or

INT-001 — failed
   |
   v
INT-002 — remediation
```

Historical status transitions should remain inspectable.

The physical representation may use status events or immutable versions, but it must reproduce the common history semantics in `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, §§3.5–3.12.

## 36. Learning History

Learning history should preserve:

- original question;
- original uncertainty;
- proposed method;
- evidence generated;
- result;
- interpretation;
- successor learning if needed;
- decision changed or unchanged.

## 37. Relationship to Reassessment

Intervention or Learning may trigger reassessment when:

- intervention fails;
- intervention materially changes configuration;
- required control cannot be implemented;
- learning completes;
- learning contradicts prior evidence;
- new uncertainty emerges;
- boundary breach occurs;
- fallback becomes persistent.

An Intervention, Completion Result/Acceptance, replacement/reuse outcome, activation event, or Learning result becomes a Trigger source only through an exact authoritative handoff under `PAIM_REASSESSMENT_SPEC_v0.1.md`. The Trigger retains this source record family, stable Record ID, exact Record Version ID, owning/affected Case, declared management question, effective/recorded/knowledge context, and separate accountable Trigger Determination.

Completion, failure, cancellation, activation, favorable Learning, source similarity, category, severity, or software status does not by itself create Trigger materiality, grouping, Reassessment membership, Decision change, or cross-Case propagation. Exact replay is idempotent; a materially updated Version of the same established source occurrence/Case/question creates a successor Trigger Version. Existing Increment 5 records remain authoritative sources and are not redesigned by this handoff.

No Observation record or automated Observation-to-Trigger conversion is introduced. Detailed Trigger and Reassessment behavior is governed by `PAIM_REASSESSMENT_SPEC_v0.1.md`.

## 38. Human Judgment Points

Human/accountable judgment remains necessary for:

- designing intervention;
- assigning ownership;
- determining completion;
- selecting fallback;
- deciding whether failure is material;
- designing learning;
- interpreting learning results;
- determining whether evidence is sufficient to reconsider a decision;
- deciding whether current operation may continue during remediation.

## 39. Platform Implications

A future platform will likely require:

- intervention list/workspace;
- ownership/status;
- target configuration linkage;
- completion criteria;
- dependency tracking;
- blocked/failed attention;
- fallback/remediation view;
- Learning Item workspace;
- uncertainty linkage;
- evidence-generation tracking;
- result/evidence linkage;
- reassessment handoff.

This specification does not prescribe UI or project-management tooling.

## 40. Behavioral Test Candidates

Future tests should include:

1. Decision requires a new control; target operation cannot activate until the exact required-before obligation is `COMPLETED`, supported by an all-`MET` Completion Result, and has one eligible `ACCEPTED` Completion Acceptance plus valid Activation Authorization.
2. Intervention becomes blocked; system surfaces operational consequence.
3. Intervention fails; reassessment is triggered.
4. Partial implementation leaves a required control absent.
5. Boundary breach invokes fallback.
6. Decision-Limiting Uncertainty creates a Learning Item.
7. Learning completes favorably and enables reassessment of a stronger state.
8. Learning is inconclusive and blocked decision remains blocked.
9. Learning contradicts prior evidence.
10. Practitioner proposes arbitrary monitoring cadence; system preserves it as practitioner design rather than evidence requirement.
11. Fallback persists long enough to become a new management configuration question.
12. Learning evidence is generated but not yet interpreted; decision should not silently change.

## 40A. Gate-5 Learning horizons and review relationship

Learning Items may retain exact target/due points, observation periods, and expected result timing
when justified by their own Decision question and source. Different items may mature at different
horizons. These facts are not a metric calendar, universal cadence, Planned Review Point, Required
Review Constraint, Trigger, materiality judgment, priority, or Decision condition by inference.

One Case/Decision-level Planned Review Point may cite exact Learning Versions as basis. A Learning
due point may contribute derived attention only as its owning contract permits. A Required Review
Constraint exists only from an independently applicable governing source normalized under the
Reassessment specification, §38A. Completion, lateness, favorable result, unfavorable result, or
inconclusive result does not automatically create a Trigger, Reassessment, Review Episode outcome,
Decision Confirmation, or successor Decision.

Review may compare expected and observed Learning claims only through the exact comparability
contract in the Evidence/Authority and Reassessment specifications. It must preserve method,
scope, period, baseline, Configuration, provenance, uncertainty, and Applicability. Later Learning
is later knowledge and cannot rewrite the earlier Decision basis. No causal, materiality,
Decision-error, or management-action inference follows from completion or variance.

Review-related Work may coordinate evidence generation or focused follow-up but does not replace a
Learning result, Evidence record, Trigger Determination, Reassessment, or Decision. Gate 5 creates
no per-metric schedule, notification service, automatic escalation, or Observation/telemetry
family.

## 41. Open Questions

Deferred to later specifications/platform design:

- whether interventions can span multiple cases;
- formal dependency graph;
- notification/escalation rules;
- project-management integration;
- intervention approval workflow;
- quantitative completion metrics;
- learning experiment templates;
- monitoring automation;
- incident-management integration;
- external-provider task integration.

IRR-012 Management Register semantics are normatively hardened in the Management Register, Integrity, Roles/Accountability, and conforming specifications, subject to independent Increment 7 gate-closure re-review. IRR-009 Observation persistence and IRR-014 operating-state ranking remain explicitly deferred. This specification does not define a universal Intervention score, universal segregation-of-duties rule, or generic workflow/condition/dependency engine.

### 41.1 IRR-012 Register conformance

The Register reports the exact Obligation/aggregate and Learning results already governed here. `INCOMPLETE`, `BLOCKED`, `CONFLICT`, and `NOT_ESTABLISHED` create attention according to exact requirement type; Completion without eligible Completion Acceptance remains attention. `SATISFIED` and `NOT_REQUIRED` retain their exact upstream meanings. Required-after and optional treatment never rewrites target activation history.

Active, blocked, failed, inconclusive, overdue, or required incomplete Learning creates attention only where its authoritative record gives it that meaning. Learning completion never changes a Decision automatically. Cross-Case Shared Dependency grouping never transfers Intervention completion, Completion Acceptance, prerequisite satisfaction, activation, replacement/reuse, Learning outcome, ownership, or authority.

## 42. Completion Impact

This specification advances the system beyond decision-making into operational execution and evidence generation.

It substantially defines:

- intervention;
- implementation status;
- fallback/remediation;
- boundary breach response;
- Learning Items;
- decision-specific evidence generation;
- intervention/learning provenance.

## 43. Next Specification

Create:

`PAIM_REASSESSMENT_SPEC_v0.1.md`

It should formalize:

- reassessment identity/status;
- trigger types;
- event-driven vs. scheduled reassessment;
- evidence refresh;
- configuration review;
- authority review;
- uncertainty reclassification;
- current-decision validity;
- successor decisions;
- closure/supersession;
- longitudinal history.

## 44. Repository Placement

```text
400. Practical AI Management/
└── system/
    └── specifications/
        ├── PAIM_CASE_LIFECYCLE_SPEC_v0.1.md
        ├── PAIM_MANAGED_CONFIGURATION_SPEC_v0.1.md
        ├── PAIM_EVIDENCE_AND_AUTHORITY_SPEC_v0.1.md
        ├── PAIM_VALUE_RISK_INTERFACE_SPEC_v0.1.md
        ├── PAIM_INTEGRATION_AND_DECISION_SPEC_v0.1.md
        └── PAIM_INTERVENTION_AND_LEARNING_SPEC_v0.1.md
```

## 45. Conclusion

The Intervention and Learning specification completes the transition from **decision** to **managed action and evidence generation**.

Its central rule is:

> **PAIM should not stop at deciding what to do. It must preserve what management changes, who owns it, whether it was actually implemented, what remains unknown, and what evidence could change the next decision.**

This is essential for PAIM to function as a continuing management system rather than a one-time analytical exercise.
