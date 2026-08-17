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
- predecessor/successor intervention where applicable

## 5. Intervention Status

Possible statuses include:

- proposed;
- planned;
- in progress;
- blocked;
- partially completed;
- completed;
- failed;
- cancelled;
- superseded.

The exact platform vocabulary may later be refined.

A completed decision does not imply that its intervention has been completed.

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

Detailed reassessment behavior is defined next in `PAIM_REASSESSMENT_SPEC_v0.1.md`.

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

1. Decision requires a new control; operation cannot enter authorized state until implemented.
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
