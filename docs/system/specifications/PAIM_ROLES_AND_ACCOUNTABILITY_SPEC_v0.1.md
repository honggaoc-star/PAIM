# PAIM Roles and Accountability Specification v0.1

## Status

Implementation-independent system specification for **roles, decision rights, analytical responsibilities, execution ownership, and accountability** in Practical AI Management (PAIM).

This specification derives from the PAIM system architecture and the system specifications for case lifecycle, managed configuration, evidence/authority, Value/Risk interfaces, integration/decision, intervention/learning, reassessment, and the Management Register.

It defines what accountability relationships PAIM must preserve. It does not prescribe organizational titles, staffing models, identity systems, or software permissions.

## 1. Purpose

PAIM requires explicit accountability without assuming that every organization has the same structure.

The system must be able to answer:

> **Who owns this management case?**

> **Who produced the Value conclusion?**

> **Who produced the Risk conclusion?**

> **Who has authority to make the management decision?**

> **Who must implement the intervention?**

> **Who owns unresolved evidence or authority questions?**

> **Who can review whether the record is traceable and procedurally sound?**

A role may be performed by an individual, organizational role, committee, team, or defined external party where appropriate.

## 2. Accountability Principle

PAIM distinguishes **responsibility for analysis**, **authority for judgment**, and **ownership of execution**.

Conceptually:

```text
Case Owner
    |
    +----> Value Evaluator
    |
    +----> Risk Evaluator
    |
    +----> Evidence / Authority Owners
    |
    v
PAIM Integration
    |
    v
Decision Authority
    |
    v
Intervention Owner(s)
    |
    v
Operation / Learning / Reassessment
```

These responsibilities may be combined in small organizations, but their functions should remain distinguishable.

## 3. Role Identity

A role assignment should support:

- Role Assignment ID
- Case ID
- role type
- person/team/organizational role
- effective period where relevant
- delegated-from relationship where relevant
- status
- scope
- assigned by/source
- predecessor/successor assignment

The platform may later bind these assignments to authenticated users.

## 4. Core PAIM Roles

The minimum role model includes:

1. Case Owner
2. Value Evaluator
3. Risk Evaluator
4. Subject-Matter Contributor
5. Decision Authority
6. Intervention Owner
7. Evidence Owner
8. Authority Owner
9. Reviewer/Auditor
10. System Administrator

Not every case requires a different person for every role.

## 5. Case Owner

### Purpose

Coordinates the PAIM case as a management process.

### Responsibilities

- maintain the management question;
- ensure the Managed Configuration is defined;
- coordinate required analytical inputs;
- identify missing ownership;
- track case lifecycle;
- coordinate integration readiness;
- ensure interventions and reassessment are not orphaned;
- preserve case completeness.

### Does not inherently have authority to

- determine the Value conclusion;
- determine the Risk conclusion;
- authorize the management decision;
- resolve governing authority.

Those rights require separate assignment or delegation.

## 6. Value Evaluator

### Purpose

Owns or produces the Value Management analysis/input.

### Responsibilities

- evaluate Value evidence;
- establish Finding;
- establish Value Boundary;
- preserve Value uncertainty;
- establish Value Implication;
- maintain provenance;
- freeze/refresh input according to process.

### Accountability rule

The Value Evaluator should not alter the Value conclusion merely to conform to the Risk conclusion or desired PAIM decision.

## 7. Risk Evaluator

### Purpose

Owns or produces the Risk Management analysis/input.

### Responsibilities

- identify material adverse pathways;
- evaluate controls/residual exposure;
- establish Finding;
- establish Risk Boundary;
- preserve Risk uncertainty;
- establish Risk Implication;
- maintain provenance;
- freeze/refresh input.

### Accountability rule

The Risk Evaluator should not weaken or strengthen the Risk conclusion merely to preserve the Value case or desired management outcome.

## 8. Analytical Independence

PAIM requires functional analytical independence even where organizational roles overlap.

At minimum:

- Value and Risk conclusions remain separately attributable;
- one conclusion cannot silently overwrite the other;
- disagreements remain visible;
- frozen inputs remain historically intact.

Separate people are preferable where independence is important and feasible, but PAIM does not require universal organizational separation.

## 9. Same-Person Role Combination

A small organization may assign one person multiple roles.

Example:

```text
Person A:
- Case Owner
- Value Evaluator
- Integration Facilitator
```

The system should still record the distinct functions.

Where the same person performs Value and Risk evaluation, the record should make that visible.

This does not automatically invalidate the case, but it changes the independence evidence.

## 10. Subject-Matter Contributor

### Purpose

Provides specialized operational, technical, legal, financial, security, customer, data, or other relevant expertise.

### Responsibilities

- contribute evidence/context;
- identify limitations;
- answer domain questions;
- support configuration definition;
- support intervention/learning design.

### Limitation

A contributor does not automatically own the analytical conclusion or management decision.

## 11. Decision Authority

### Purpose

Makes or authorizes the PAIM management judgment.

### Responsibilities

- review the integration record;
- understand material Value/Risk conclusions;
- consider constraints and authority gaps;
- consider uncertainty and alternatives;
- authorize the operating state and Integrated Operating Boundary;
- accept conditions/limits;
- authorize intervention.

### Required property

Decision authority must be established by organizational governance, delegation, policy, role, committee charter, or another legitimate mechanism.

PAIM does not invent decision authority.

## 12. Decision Authority Gap

If the appropriate decision authority is not established:

> **DECISION AUTHORITY UNRESOLVED**

The case should record:

- decision requiring authority;
- authority mechanism needed;
- current owner for resolution;
- whether analysis may continue;
- whether operation may continue;
- status.

A case cannot become `DECIDED` without an identifiable authorization basis.

## 13. Delegated Authority

Decision authority may be delegated.

A delegation should identify:

- delegating authority;
- delegated role/person;
- scope;
- limits;
- effective period;
- decisions covered;
- conditions;
- source/provenance.

Delegated authority should not be inferred merely because a person participates in the case.

## 14. Committee Decision Authority

A committee may act as Decision Authority.

The system should be able to represent:

- committee identity;
- decision mechanism;
- required participation/quorum where organizationally relevant;
- authorization result;
- date;
- dissent/exception where recorded.

Detailed governance mechanics are organization-specific.

## 15. Intervention Owner

### Purpose

Owns implementation of one or more required interventions.

### Responsibilities

- plan implementation;
- execute required change;
- report status;
- identify blockers;
- demonstrate completion criteria;
- invoke escalation/fallback where required.

An Intervention Owner does not automatically have authority to change the underlying PAIM decision.

## 16. Evidence Owner

### Purpose

Maintains or produces evidence required by the case.

Possible responsibilities:

- evidence collection;
- source maintenance;
- measurement;
- provenance;
- refresh;
- learning evidence generation.

Evidence ownership does not imply authority to determine the analytical conclusion.

## 17. Authority Owner

### Purpose

Owns resolution or maintenance of governing-authority questions.

Possible examples:

- legal;
- compliance;
- privacy;
- security;
- contract owner;
- policy owner;
- delegated governance function.

### Responsibilities

- identify governing source;
- resolve Authority Gap where possible;
- maintain applicability;
- identify change/supersession.

Authority ownership does not imply PAIM Decision Authority unless separately assigned.

## 18. Reviewer / Auditor

### Purpose

Provides independent or second-line inspection of process integrity, traceability, or compliance with PAIM requirements.

Possible responsibilities:

- inspect evidence/provenance;
- inspect configuration binding;
- inspect frozen-input integrity;
- inspect authorization;
- inspect intervention completion;
- inspect reassessment history;
- identify process exceptions.

### Limitation

Reviewer/Auditor should not silently rewrite analytical or management records.

Findings should be recorded as review evidence, exceptions, or triggers.

## 19. System Administrator

### Purpose

Maintains the technical PAIM platform.

Possible responsibilities:

- account/access administration;
- configuration of platform settings;
- technical support;
- system availability;
- data administration according to policy.

### Critical separation

System Administrator status must not inherently grant authority to:

- change analytical conclusions;
- authorize PAIM decisions;
- resolve authority questions;
- alter historical records.

Technical privilege and management authority are distinct.

## 20. Integration Facilitator

An organization may assign an Integration Facilitator even if not treated as a mandatory core role.

Possible responsibilities:

- organize PAIM integration;
- ensure frozen inputs are preserved;
- facilitate alternatives/interaction analysis;
- document proposed judgment.

The facilitator does not automatically become Decision Authority.

## 21. Reassessment Owner

A reassessment may be coordinated by the Case Owner or a separately assigned Reassessment Owner.

Responsibilities include:

- triage trigger;
- coordinate evidence/configuration review;
- identify analytical refresh;
- move case toward successor decision.

The role may be optional as a separate designation.

## 22. Role-to-Record Accountability

| Record | Primary accountable role |
|---|---|
| PAIM Case Record | Case Owner |
| Managed Configuration Record | Case Owner / designated configuration owner |
| Evidence Record | Evidence Owner / producer |
| Authority Record/Gap | Authority Owner |
| Value Management Input | Value Evaluator |
| Risk Management Input | Risk Evaluator |
| PAIM Integration Record | Integration owner/facilitator |
| Management Decision Record | Decision Authority |
| Intervention Record | Intervention Owner |
| Learning Item | assigned learning/evidence owner |
| Reassessment Record | Case/Reassessment Owner |
| Management Register | derived system view; management ownership |

This table defines default accountability, not mandatory organizational staffing.

## 23. Role Conflicts

Potential conflicts include:

- Value Evaluator pressured to preserve a desired business case;
- Risk Evaluator pressured to approve deployment;
- Intervention Owner self-certifying effectiveness without appropriate evidence;
- System Administrator altering substantive records;
- Decision Authority also acting as sole evidence producer;
- Authority Owner benefiting from a particular interpretation.

PAIM should make role combinations visible rather than assuming conflicts do not exist.

## 24. Separation-of-Role Principles

PAIM should preserve the following distinctions where feasible:

### Analysis vs. decision

Analytical contributors provide conclusions; Decision Authority owns the management judgment.

### Evidence vs. conclusion

Evidence producer does not automatically determine what the evidence means.

### Decision vs. implementation

Decision Authority authorizes; Intervention Owner implements.

### Technical administration vs. substantive authority

Platform access does not confer management authority.

### Review vs. record mutation

Auditors/reviewers identify issues; they do not silently alter historical records.

## 25. Minimum Separation Requirements

PAIM does not impose universal segregation-of-duties rules.

However, the system should require explicit attribution for:

- Value Input;
- Risk Input;
- Management Decision;
- Intervention ownership;
- authority resolution.

If the same person occupies multiple roles, the record should show that fact.

## 26. Role Assignment Scope

A role assignment may be scoped to:

- one case;
- one configuration;
- one decision;
- one intervention;
- one authority domain;
- one business unit;
- organization-wide function.

The system should not assume organization-wide authority from a case-specific assignment.

## 27. Role Assignment Status

Possible statuses:

- proposed;
- active;
- temporarily delegated;
- expired;
- revoked;
- superseded.

Historical assignments should remain inspectable for prior decisions.

## 28. Accountability During Absence or Change

When an accountable role changes:

- preserve prior assignment history;
- assign successor;
- identify open obligations;
- transfer ownership explicitly;
- do not silently orphan interventions, learning items, or authority gaps.

## 29. Accountability for Shared Controls

A shared control may support multiple PAIM configurations.

The system should be able to identify:

- control owner;
- configurations dependent on control;
- capacity;
- failures;
- changes;
- reassessment exposure.

This supports the Management Register's cross-case dependency view.

## 30. Accountability for Provider/Model Dependencies

Where a provider/model is shared across configurations, an organization may assign a common dependency owner.

That owner may coordinate:

- provider changes;
- service incidents;
- model updates;
- contract issues;
- cross-case reassessment.

This role does not replace individual Case Owners or Decision Authorities.

## 31. Accountability for Learning

Every material Learning Item should have an owner.

The owner is accountable for:

- evidence-generation activity;
- status;
- limitations;
- result delivery.

The owner does not automatically decide whether the evidence changes the PAIM decision.

## 32. Accountability for Reassessment

Every material reassessment should have a coordinator/owner.

The Decision Authority remains accountable for any successor management judgment.

## 33. Escalation

The system should support escalation when:

- Decision Authority unresolved;
- intervention blocked;
- authority unresolved;
- boundary breach;
- reassessment overdue;
- role owner unavailable;
- analytical conflict cannot be operationalized;
- shared capacity/control dependency affects multiple cases.

Escalation destination is organization-specific.

## 34. Role Exceptions

Organizations may require exceptions to normal role separation.

A role exception should identify:

- exception;
- reason;
- scope;
- approving authority where required;
- compensating review where used;
- duration.

PAIM does not prescribe universal exception approval rules.

## 35. Permissions Implications

Future platform permissions should derive from roles but must not assume one-to-one equivalence.

Possible actions include:

- view;
- create;
- edit draft;
- freeze;
- supersede;
- authorize;
- assign;
- close;
- administer.

A user may need different permissions across different cases.

Detailed authorization design belongs in platform architecture.

## 36. Historical Record Protection

No role should be able to silently rewrite authoritative historical records.

Corrections, supersession, and successor records should remain traceable.

Even Decision Authority should not overwrite a prior authorized decision without history.

## 37. Management Register Accountability

The Management Register is a derived view.

Management users may use it for prioritization and portfolio action.

The register itself should not create hidden substantive authority.

Portfolio-level decisions should be represented through appropriate decision/authority records.

## 38. Human Validation Implications

Future human testing should examine whether practitioners can correctly identify:

- their role;
- what they are responsible for;
- what they may decide;
- what requires escalation;
- when another role is required;
- whether role overlap creates confusion.

Role clarity is a system-usability question, not merely a documentation question.

## 39. Role Integrity Checks

The system should surface:

- case with no Case Owner;
- decision with no Decision Authority;
- intervention with no owner;
- Authority Gap with no owner where resolution is required;
- frozen input with no analytical owner/source;
- expired/revoked authority used for current decision;
- technical administrator making substantive changes without assigned role;
- role assignment outside its scope;
- orphaned obligations after role change.

These checks support accountability; they do not replace organizational governance.

## 40. Behavioral Test Candidates

Future tests should include:

1. Same person acts as Value and Risk Evaluator; system records overlap explicitly.
2. Decision Authority is missing; integration may proceed but case cannot become `DECIDED`.
3. Delegated authority expires before authorization.
4. Intervention Owner changes mid-implementation.
5. System Administrator attempts substantive decision modification.
6. Reviewer identifies a frozen-input integrity issue without editing the input.
7. Shared control owner reports failure affecting multiple cases.
8. Authority Owner resolves an Authority Gap but does not automatically authorize expansion.
9. Decision Authority changes; prior decision remains attributable to prior authority.
10. Learning Item becomes orphaned after staff change and is surfaced.

## 41. Open Questions

Deferred to platform/organizational design:

- exact permission matrix;
- identity provider;
- approval/signature technology;
- committee quorum rules;
- formal segregation-of-duties requirements;
- external-user roles;
- delegated authority hierarchy;
- emergency authority;
- organization-wide role templates;
- privacy/access segmentation.

## 42. Completion Impact

This specification completes the principal accountability layer required by the implementation-independent PAIM management system.

The major remaining system-design artifact before platform architecture is the behavioral validation strategy.

## 43. Next Artifact

Create under `system/testing/`:

`PAIM_SYSTEM_BEHAVIORAL_VALIDATION_STRATEGY_v0.1.md`

It should formalize:

- black-box/input-output testing;
- scenario families;
- controlled variable changes;
- expected invariant behavior;
- boundary sensitivity;
- authority behavior;
- uncertainty behavior;
- configuration-change behavior;
- longitudinal/reassessment behavior;
- human-system testing principles;
- separation of system behavior from UI usability.

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
        ├── PAIM_INTERVENTION_AND_LEARNING_SPEC_v0.1.md
        ├── PAIM_REASSESSMENT_SPEC_v0.1.md
        ├── PAIM_MANAGEMENT_REGISTER_SPEC_v0.1.md
        └── PAIM_ROLES_AND_ACCOUNTABILITY_SPEC_v0.1.md
```

## 45. Conclusion

The Roles and Accountability specification establishes a central PAIM principle:

> **The person who analyzes, the person who decides, the person who implements, and the person who administers the platform are not automatically the same authority—even when one individual performs multiple functions.**

Making those functions explicit allows PAIM to remain usable in small organizations while preserving accountability and analytical integrity in larger ones.
