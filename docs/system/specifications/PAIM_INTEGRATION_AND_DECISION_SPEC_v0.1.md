# PAIM Integration and Decision Specification v0.1

## Status

Implementation-independent system specification for **PAIM Decision Integration, Management Judgment, and Authorization**.

This specification derives from:

- `PAIM_SYSTEM_ARCHITECTURE_v0.1.md`
- `PAIM_SYSTEM_COMPLETION_BASELINE_GAP_MAP_v0.1.md`
- `PAIM_CASE_LIFECYCLE_SPEC_v0.1.md`
- `PAIM_MANAGED_CONFIGURATION_SPEC_v0.1.md`
- `PAIM_EVIDENCE_AND_AUTHORITY_SPEC_v0.1.md`
- `PAIM_VALUE_RISK_INTERFACE_SPEC_v0.1.md`
- `PAIM_MINIMUM_MANAGEMENT_CASE_v0.3.md`
- `PAIM_PRACTITIONER_PLAYBOOK_v0.2.md`
- IET 001–004 validation findings.

It defines what the PAIM system must preserve when independent Value and Risk conclusions become an accountable management decision.

It does not prescribe software implementation, UI design, database schemas, or a universal decision algorithm.

**Normative cross-cutting contract:** `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md` governs authoritative record history/currentness, the immutable hybrid Integrated Operating Boundary Snapshot, Decision Authorization Basis, bounded-proceed authority, and exact Decision reconstruction. Where this specification uses `current`, `frozen`, `authorized`, `amendment`, or `successor`, the cross-cutting contract supplies the controlling integrity semantics.

## 1. Purpose

PAIM Decision Integration converts independent, configuration-bound Value and Risk Management Inputs into a management judgment.

The system must answer:

> **Given the frozen Value and Risk conclusions, governing constraints, authority state, controls, uncertainty, and credible alternatives, what should management do with this configuration now?**

The output is not a blended analytical score.

It is an accountable decision with:

- an Integrated Operating Boundary;
- an operating state;
- rationale;
- conditions and limits;
- intervention requirements;
- learning/reassessment implications;
- identified decision authority.

## 2. Integration Principle

PAIM Integration must preserve the contributing analytical conclusions before management judgment is applied.

Conceptually:

```text
Frozen Value Management Input
              |
              +------------------+
                                 |
                                 v
                         PAIM Integration
                                 ^
                                 |
              +------------------+
              |
Frozen Risk Management Input

plus:
- constraints
- authority / authority gaps
- Control Dependencies
- uncertainty
- alternatives
- interaction analysis
              |
              v
      Management Judgment
              |
              v
     Authorized Decision
```

## 3. Integration Identity

Every Integration Record should have a durable identity.

Minimum fields:

- Integration ID
- Integration Version ID
- Case ID
- Managed Configuration ID/version
- Value Input ID/version
- Value Input Acceptance/Selection ID/version
- Risk Input ID/version
- Risk Input Acceptance/Selection ID/version
- exact material Evidence Applicability and lane-level fitness basis for each selected Input
- integration version
- status
- integrator/owner
- date initiated
- date completed
- recorded time and effective time/interval
- predecessor/successor integration where applicable

## 4. Integration Status

Possible statuses include:

- draft;
- ready;
- in progress;
- completed;
- decision pending;
- superseded;
- withdrawn.

A completed integration is not itself an authorized management decision until the Decision Record is created/approved.

## 5. Integration Readiness

Before substantive integration, the system should confirm:

- exactly one governing Managed Configuration Version exists for the Case/effective time;
- exactly one eligible selected/frozen Value Input Version and exact Value Acceptance/Selection Version exist for this bounded Integration path/use;
- exactly one eligible selected/frozen Risk Input Version and exact Risk Acceptance/Selection Version exist for this bounded Integration path/use;
- both selected Inputs and both acceptances bind to the same exact governing Configuration Version;
- Value Boundary is explicit;
- Risk Boundary is explicit;
- material uncertainty is represented;
- provenance exists;
- every Evidence item declared material to either acceptance/use has a current exact-context Evidence Applicability result and an eligible accountable lane-level fitness treatment;
- established constraints are available;
- material authority gaps are explicit;
- decision authority is identified or its absence is explicit.

Readiness does not require Value and Risk agreement.

For either lane, selection returns one eligible accepted/frozen Input plus its Acceptance/Selection Version, explicit `INPUT SELECTION NOT ESTABLISHED`, or explicit `INPUT SELECTION CONFLICT — UNRESOLVED`. No newest/latest/owner/status/row-order result or shared Value/Risk acceptance shortcut is permitted.

An Input that is rejected for the bounded use, withdrawn before readiness, superseded without an explicit reuse acceptance, or subject to unresolved material `REFRESH REQUIRED` is ineligible. Later withdrawal, correction, supersession, Evidence change, or Applicability change does not rewrite a historical Integration/Decision basis.

Material-Evidence handoff behavior is:

- Applicability absence, unresolved conflict, `NOT_APPLICABLE`, or unresolved `REFRESH REQUIRED` blocks when the Evidence is required for the selected Input's Finding, Boundary, or Implication.
- `CONDITIONALLY_APPLICABLE` or `PARTIALLY_APPLICABLE` supports only within its recorded scope/conditions and cannot support a broader contributing Boundary.
- `INDETERMINATE` is neither globally eligible nor globally blocked. The exact accountable lane-level fitness determination states whether the bounded analytical use remains supportable and why; it blocks when decision-limiting to that Input/use.
- Evidence linked as limitation, dissent, or conflict remains visible without being misrepresented as favorable support.

PAIM may check these records mechanically but must not compute a universal evidence-sufficiency/confidence score. General management-level Accepted versus Decision-Limiting Uncertainty classification remains an Integration judgment under §10.

### 5.1 Prospective Integration Responsibility

After explicit cutover, `COMPLETE_VALUE_RISK_INTEGRATION` binds the exact owning Case, governing
Configuration Version, bounded use, and current Value and Risk Input plus Acceptance/Selection
Versions. The same Responsibility may be held by a Case Coordinator or Assessor only through its
own valid assignment basis. It permits no stale lane substitution and does not create Integration,
Boundary, proposal, Decision Authority, or authorization. Contextual Work completes only by linking
the exact Integration Version created through this specification.

## 6. Frozen Input Display

The system should display the contributing conclusions without rewriting them.

At minimum:

```text
VALUE FINDING
[verbatim or authoritative frozen content]

VALUE BOUNDARY
[authoritative content]

VALUE UNCERTAINTY
[authoritative content]

VALUE IMPLICATION
[verbatim frozen implication]

RISK FINDING
[authoritative content]

RISK BOUNDARY
[authoritative content]

RISK UNCERTAINTY
[authoritative content]

RISK IMPLICATION
[verbatim frozen implication]
```

IET 004 demonstrated that paraphrase drift can occur even when the final judgment remains reasonable.

The authoritative frozen Implications should therefore remain visible during integration.

## 7. Constraints

Integration must identify actually established constraints relevant to the decision.

Possible sources include:

- organizational policy;
- contractual obligation;
- legal/regulatory requirement;
- safety requirement;
- information/data restriction;
- authorization limit;
- mandatory oversight;
- other binding requirements.

A plausible constraint is not an established constraint.

## 8. Authority Gaps

Where authority needed for a decision is missing:

> **AUTHORITY UNRESOLVED**

The Integration Record should identify:

- authority question;
- decision affected;
- configuration/scope affected;
- authority/evidence needed;
- whether the current bounded decision may proceed;
- rationale.

PAIM may support a narrower decision while a broader decision remains blocked by unresolved authority.

## 9. Control Dependency Analysis

For each material control, integration should determine:

- control identity;
- Risk function;
- Value function/burden;
- whether Value depends on it;
- whether Risk depends on it;
- whether the final boundary depends on it;
- what changes if the control changes;
- whether reassessment is required.

The system should support questions such as:

> **Would removing this control improve apparent Value while invalidating the Risk conclusion?**

> **Does preserving the Risk conclusion impose a burden that materially changes Value?**

## 10. Uncertainty Classification

PAIM Integration classifies material contributing uncertainty relative to the management decision.

### Accepted Uncertainty

> **What remains unknown but does not prevent the decision being made now?**

Record:

- uncertainty;
- why compatible with current decision;
- observation needed;
- condition that would make it decision-limiting.

### Decision-Limiting Uncertainty

> **What remains unknown that prevents a stronger, broader, or different decision?**

Record:

- uncertainty;
- blocked decision/state;
- evidence/authority needed;
- learning/reassessment relationship.

The same uncertainty may change classification when the proposed decision changes.

## 11. Integrated Operating Boundary

The Integration Record must establish:

> **Under exactly what conditions is the combined PAIM decision supportable?**

Conceptually:

```text
B_PAIM =
Value Boundary
∩ Risk Boundary
∩ Established Constraints
∩ Required Control Conditions
∩ Decision-specific limits
```

This is conceptual, not a requirement for mathematical computation.

The boundary used for authorization must be finalized as the immutable hybrid Integrated Operating Boundary Snapshot defined in `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, §4. The Snapshot preserves structured references where integrity behavior is expected and narrative clauses where accountable human judgment remains necessary. It is not a universal score.

## 12. Boundary Content

The Integrated Operating Boundary may include:

- permitted activities;
- excluded activities;
- users/populations;
- complexity;
- information/data;
- AI authority;
- human authority;
- required controls;
- escalation/review;
- thresholds;
- provider/model conditions;
- capacity;
- geography;
- operating conditions;
- fallback;
- authority conditions.

The boundary should be inspectable without reconstructing the full analytical record.

Every material clause must have the identity, effect, provenance, verification mode, and structured or narrative representation required by `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, §§4.2–4.6.

## 13. Boundary Relationship to Managed Configuration

The proposed Managed Configuration may be broader than the authorized Integrated Operating Boundary.

Possible outcomes:

- configuration fully supported;
- configuration narrowed;
- configuration conditioned;
- experimental subset authorized;
- transition configuration authorized;
- configuration not supported;
- fallback only.

The final decision must not silently imply that the entire proposed configuration is authorized when only a subset is supported.

Boundary comparison uses `UNCHANGED`, `NARROWED`, `BROADENED`, `MIXED`, or `INDETERMINATE` under `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, §4.7. A broadened or mixed boundary requires an authorized successor/amendment Decision; `INDETERMINATE` requires accountable review and is not treated as unchanged.

## 14. Alternatives

Integration must consider credible alternatives appropriate to the management problem.

Alternatives may include:

- continue unchanged;
- narrow scope;
- change controls;
- change AI/human authority;
- change threshold;
- redesign workflow;
- hybrid operation;
- targeted experiment;
- external sourcing;
- fallback;
- suspend;
- discontinue.

For each material alternative, record:

- configuration;
- operating state;
- Value implication;
- Risk implication;
- controls;
- evidence maturity;
- uncertainty;
- authority implications;
- management disposition.

## 15. Evidence Maturity Across Alternatives

Alternatives may have asymmetric evidence maturity.

Example:

```text
A — demonstrated Value / insufficient control
B — demonstrated stronger control / impaired Value
C — plausible reconciliation / unvalidated
D — fallback / different trade-offs
```

PAIM must preserve these differences.

A plausible redesign must not inherit demonstrated evidence from another configuration.

## 16. Interaction Analysis

PAIM uses four interaction categories.

### Reinforcement

Where do Value and Risk independently support the same action, boundary, or condition?

### Conflict

Where do they support materially different actions?

### Constraint

Where does one finding limit what can reasonably be inferred or done based on the other?

### Configuration Trade-off

What configuration change improves one side while weakening the other?

The system should support explicit recording of all four rather than forcing one overall relationship label.

## 17. No Universal Score Requirement

PAIM does not require a universal Value/Risk score.

The system should not force:

- numerical aggregation;
- weighted average;
- risk-adjusted Value score;
- traffic-light result as the sole decision basis.

Organizations may use domain-specific metrics, but the PAIM decision must remain reconstructable from evidence, boundaries, uncertainty, alternatives, and judgment.

## 18. Proposed Management Judgment

Before authorization, the Integration Record may contain a proposed judgment.

Minimum content:

- proposed action;
- proposed operating state;
- proposed Integrated Operating Boundary;
- rationale;
- Value evidence relied upon;
- Risk evidence relied upon;
- Accepted Uncertainty;
- Decision-Limiting Uncertainty;
- conditions/limits;
- intervention required;
- learning/reassessment implications.

A proposed judgment is not yet the authorized decision.

## 19. Operating State

The decision should explicitly identify the selected operating state.

Possible states include:

- experiment;
- bounded continuation;
- targeted scale;
- institutionalized use;
- broader deployment;
- controlled transition/redesign;
- suspended;
- discontinued.

The system should permit additional organization-specific states if their meaning is defined.

## 20. Operating-State Semantics

Phase II exposed variation in how independent evaluators distinguish bounded continuation from institutionalization.

Therefore:

- the state must be explicit;
- the rationale must explain why the evidence supports that state;
- a stronger state may require stronger/different evidence;
- the platform should not infer institutionalization automatically from recurring successful operation.

A later human/system validation program should test operating-state interpretation.

## 21. Management Decision Record

Once authorized, create a durable Management Decision Record.

Minimum fields:

### Identity
- Decision ID
- Decision Version ID
- Case ID
- Configuration ID/version
- Integration ID/version
- decision version
- status
- decision date
- decision authority
- Integrated Operating Boundary Snapshot ID/version
- Decision Authorization Basis ID/version
- recorded time and effective time/interval

### Judgment
- decision/action
- selected operating state
- Integrated Operating Boundary
- rationale

### Basis
- Value Input ID/version
- Risk Input ID/version
- established constraints
- authority state
- Accepted Uncertainty
- Decision-Limiting Uncertainty
- alternatives considered

### Consequence
- conditions/limits
- intervention required
- exact Decision-to-Intervention Obligation Set ID/version, including an explicit zero-required-before set where applicable
- `REQUIRED_AFTER_OPERATION` timing/conditions and optional commitments
- any genuine governed organizational activation mechanism pre-authorized through the exact Decision Authorization Basis
- learning items
- reassessment triggers
- successor/predecessor decision relationship

## 22. Decision Authority

The system must identify who or what organizational mechanism is authorized to make the decision.

Possible authority structures include:

- named individual;
- role;
- committee;
- delegated approval chain;
- other defined mechanism.

Detailed role/permission design is deferred to `PAIM_ROLES_AND_ACCOUNTABILITY_SPEC`.

A case cannot become `DECIDED` without an identifiable authorization basis.

The identifiable basis must be preserved as the Decision Authorization Basis defined in `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, §6. It binds the exact Decision version to the legitimate authority mechanism, Role Assignment/delegation, scope, limits, effective period, authority identity, and authorization event.

## 23. Authorization

Authorization should preserve:

- decision authority;
- date/time;
- decision content/version;
- conditions;
- any dissent/exception record where the organization requires it.

The platform may later implement signatures, approvals, or workflow actions.

This specification requires traceable authorization, not a particular signature technology.

Decision authorization, Completion Acceptance, and Activation Authorization are distinct authoritative facts. Satisfied Intervention prerequisites do not themselves authorize operation.

Where a Decision pre-authorizes an activation mechanism, the Decision Authorization Basis must identify a genuine governed organizational authority mechanism and retain its exact rule/version, scope, authority source, limits, and effective period. A software checklist, workflow transition, technical rule, Case Owner, Intervention Owner, administrator permission, or technical principal is not an organizational activation mechanism and cannot self-authorize operation.

When another authority question remains unresolved, only an established Decision Authority whose own scope covers the exact narrower Decision and the bounded-proceed determination may authorize proceeding. The requirements in `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, §6.4 apply; the Authority Gap remains unresolved and visible.

### 23.1 Responsibility remains outside Decision Authority

Prospective Responsibility and Case Work do not replace, infer, delegate, or satisfy Decision
Authority. A participant may coordinate Integration, prepare a proposal, or receive contextual Work
without authority to authorize it. Authorization continues to require the exact complete Decision
Authorization Basis and exact current Integration/Boundary/proposal chain. Assignment or Work
completion creates no Decision and grants no authority.


## 24. Decision Status

Possible statuses include:

- proposed;
- pending authorization;
- authorized/current;
- superseded;
- withdrawn;
- expired where organization rules require;
- closed with case.

The current decision must be distinguishable from historical decisions.

Authoritative current selection follows `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, §3.11. An overlap or incompatible current result is explicit conflict, not a latest-version choice.

## 25. Decision Immutability

An authorized decision must not be silently edited.

If the decision changes:

1. preserve the original;
2. create an amendment/successor decision;
3. identify reason;
4. identify changed configuration/evidence/authority;
5. link reassessment;
6. establish effective status.

Administrative corrections should also remain traceable where material.

Corrections and amendments follow `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, §§3.7–3.8. Every substantive amendment is an authorized successor Decision version; the prior authorized Decision remains immutable.

## 26. Decision Supersession

Example:

```text
Decision D1
  |
  | reassessment
  v
Decision D2
```

D2 may supersede D1 for current operation.

D1 remains the authoritative historical decision for its period/configuration.

Every substantive successor/amendment Decision has its own exact Obligation Set. Prior Completion Results and Acceptances do not carry forward. Reuse requires an exact accountable continued-validity determination covering unchanged relevant Configuration content, Boundary/conditions, completion criteria, Evidence applicability, and acceptance scope. A changed target Configuration requires explicit coverage of the new Version; absent eligible reuse, the successor obligation is `NOT_ESTABLISHED`.

## 27. Decision and Intervention

A decision may require intervention before the authorized configuration is operational.

The Decision Record should link to one or more Intervention Records.

The normative relationship is the versioned Decision-to-Intervention Obligation Set and its exact Obligation Versions defined by the Intervention and Learning specification. Requirement type belongs to the exact Decision/target-Configuration obligation package, not globally to the Intervention or Configuration. The v0.1 types are exactly `REQUIRED_BEFORE_OPERATION`, `REQUIRED_AFTER_OPERATION`, and `OPTIONAL`.

Examples:

- implement control;
- narrow scope;
- change threshold;
- restore human review;
- stop prohibited activity;
- begin redesign experiment;
- establish fallback.

The case lifecycle may remain `INTERVENTION_IN_PROGRESS` until required actions are complete.

Target operation requires the exact all-of prerequisite result and Activation Authorization governed by the Intervention, Case Lifecycle, and Integrity specifications. `COMPLETED` status, evidence presence, Completion Acceptance, or a completed checklist alone does not authorize activation.

## 28. Decision and Learning

Decision-Limiting Uncertainty should generate explicit Learning Items where management intends to preserve the possibility of a stronger/broader/different future decision.

Example:

```text
Current decision: bounded continuation
Blocked decision: institutionalization
Missing evidence: long-term control performance
Learning item: collect evidence
Reassessment trigger: evidence complete
```

## 29. Decision and Reassessment

Every current decision should identify what could cause reconsideration.

Possible triggers:

- incident;
- Value change;
- Risk change;
- control failure/change;
- configuration change;
- provider/model change;
- authority resolution/change;
- capacity change;
- learning completion;
- proposed stronger operating state;
- scheduled review.

Multiple Reassessments may concern the same initiating Decision only under the exact scope/coexistence contract in `PAIM_REASSESSMENT_SPEC_v0.1.md`, §38. One Reassessment's completion never automatically closes, confirms, cancels, supersedes, rebases, or transfers Trigger coverage for another.

Before an unchanged-Decision Confirmation or successor/amendment Decision is committed, the Reassessment completion operation must prospectively revalidate the exact current Decision and governing Configuration, exact Trigger Set and coverage, absence of unresolved grouping/overlap/coordination conflict, Reassessment accountability, and required authority at the completion effective time and optional knowledge cutoff.

If one concurrent Reassessment confirms the current Decision unchanged, another may continue only after that prospective revalidation. If a successor/amendment Decision becomes effective, predecessor-bound Reassessment work remains historical but cannot complete as current against the stale Decision/Configuration context. Continuing it prospectively requires an explicit accountable coordination determination, a new/successor Reassessment identity bound to the current Decision/Configuration, exact Trigger carry-forward relationships, and explicit predecessor cancellation/supersession where applicable.

A future-effective successor affects Reassessment eligibility only from its effective time. Recorded time and knowledge cutoff remain independently reconstructable. No completion, Decision, creation time, recency, or row order is an implicit winner.

## 30. Interim and Transitional Decisions

PAIM explicitly supports interim decisions.

Examples:

- controlled transition;
- redesign experiment;
- temporary fallback;
- bounded continuation pending evidence;
- temporary suspension.

An interim state is not a methodological failure.

It may be the most evidence-consistent management judgment.

## 31. Disagreement and Dissent

The system should permit management disagreement to remain inspectable where material.

Possible content:

- alternative judgment proposed;
- dissenting rationale;
- unresolved management question;
- additional authority required.

This should not force consensus by rewriting analytical inputs.

Detailed organizational governance is deferred.

Non-selected, dissenting, or rejected-for-use Value/Risk candidates and material Evidence limitations remain linked and inspectable. They do not satisfy the one selected Input requirement and are not erased by selection.

## 32. Decision Explanation

A practitioner or later reviewer should be able to answer:

- What did management decide?
- What exact configuration did the decision cover?
- Why?
- What Value evidence mattered?
- What Risk evidence mattered?
- What authority applied?
- What remained uncertain?
- What alternatives were considered?
- What was excluded?
- What action followed?
- What could change the decision?

If these cannot be reconstructed, the Decision Record is incomplete.

## 33. Integration Integrity Checks

Before integration completion, surface:

- missing frozen Value Input;
- missing frozen Risk Input;
- missing or conflicting Value Acceptance/Selection Version;
- missing or conflicting Risk Acceptance/Selection Version;
- configuration mismatch;
- missing contributing Boundary;
- missing provenance;
- material authority gap omitted;
- material uncertainty omitted;
- alternative presented as demonstrated when only plausible;
- frozen implication paraphrase drift.
- selected Input rejected/withdrawn before readiness or reused without a new use-specific acceptance;
- material Evidence Applicability absent, conflicting, not applicable, refresh-required, or narrower than the claimed contributing Boundary;
- `INDETERMINATE` Evidence lacking the separate exact lane-level fitness determination;
- acceptance or Applicability accountability vacant, conflicting, or out of scope;
- non-selected/dissenting Input or Evidence limitation hidden from the handoff;
- analytical acceptance treated as Decision Authority.

## 34. Decision Integrity Checks

Before authorization, surface:

- no decision authority;
- no Integrated Operating Boundary;
- no rationale;
- no selected operating state;
- no link to frozen inputs;
- unclassified material uncertainty;
- decision broader than supported boundary;
- required control absent from proposed configuration;
- unresolved authority treated as resolved;
- exact Obligation Set omitted, including omission of an explicit zero-required-before set;
- intervention requirement omitted where configuration must change;
- required-after timing/conditions or successor-obligation treatment omitted; or
- purported pre-authorized activation mechanism lacks genuine governed organizational rule/version/scope/authority provenance.

These checks do not replace human judgment.

## 35. Human Judgment Points

Accountable human judgment remains central for:

- determining material constraints;
- classifying uncertainty;
- generating alternatives;
- interpreting interaction;
- selecting the Integrated Operating Boundary;
- choosing operating state;
- deciding whether authority gaps permit a bounded decision;
- authorizing the final judgment;
- deciding when a successor decision is required.

## 36. Platform Implications

A future platform will likely require:

- integration workspace;
- side-by-side frozen inputs;
- verbatim Implication display;
- constraints/authority view;
- Control Dependency view;
- uncertainty classification;
- boundary builder/view;
- alternatives comparison;
- interaction table;
- proposed decision;
- authorization workflow;
- immutable decision history;
- successor decision/reassessment linkage.

This specification does not prescribe UI.

## 37. Behavioral Test Candidates

Future tests should include:

1. Value and Risk reinforce continuation but Risk narrows the boundary.
2. Value prefers A while Risk rejects A.
3. A stronger control makes the Value case negative.
4. A redesign is plausible but unvalidated.
5. Authority is unresolved only for expansion; bounded continuation remains possible.
6. Same evidence, proposed state changes from continuation to institutionalization.
7. Remove a required control after decision and trigger reassessment.
8. Attempt to authorize a decision broader than the Integrated Operating Boundary.
9. Attempt to edit an authorized historical decision.
10. Introduce new evidence and create a successor decision without rewriting the prior one.
11. Paraphrase frozen Value/Risk Implications inaccurately and verify authoritative text remains visible.
12. Compare multiple defensible judgments from the same evidence and inspect rationale.
13. Select one accepted Value and one accepted Risk Input for the same exact Configuration Version and confirm analytical handoff eligibility.
14. Create competing Value acceptances for one use and block on explicit conflict.
15. Withdraw a selected Input before readiness and block; change it after a historical Decision and preserve reconstruction.
16. Reuse a frozen Input only through a new Acceptance/Selection Version.
17. Reject conditional/partial Evidence as support for a broader contributing Boundary.
18. Require an exact lane-level fitness determination for `INDETERMINATE` Evidence and exercise both supportable and blocked outcomes.

## 37A. Gate-5 Decision-bound review timing and outcome boundary

A Planned Review Point may bind the exact current Decision Version, governing Configuration
Version, review purpose, and affected scope. It is a separate authoritative fact and does not
become Decision content merely because it cites the Decision. When a review date/window is itself
an authorized Decision condition or Integrated Operating Boundary clause, establishing or changing
that timing requires the exact Decision Authority/Authorization Basis and successor/amendment path
required to change the source. `PLAN_NEXT_REVIEW` Responsibility, Case Coordinator orientation,
software permission, or an earlier/later calendar choice cannot amend it.

Required Review Constraints sourced from Decision conditions or Boundary clauses retain the exact
source Version, Applicability, scope, and temporal operator under the Reassessment specification,
§38A. Changing a practitioner plan does not waive or modify them. A successor Decision or
Configuration makes no predecessor-bound Review Point current by inference and creates no silent
retargeting or constraint carry-forward.

A completed no-material-change or focused Review Episode does not itself confirm the Decision.
The current management position remains unchanged only through an exact separately valid Decision
Confirmation. Any changed operating state, Boundary, condition, or substantive judgment requires
an authorized successor/amendment Decision. Review timing, lateness, Learning completion,
Reassessment completion, or favorable/unfavorable quantitative variance never supplies Decision
Authority or infers Decision error.

When one natural confirmation completes a Review Episode, confirms a Decision unchanged, and/or
establishes the next Planned Review Point, every intended fact retains its own identity, exact
context, Responsibility/accountability, authority, and guards and commits in one declared semantic
transaction or not at all. No fact substitutes for another.

## 38. Open Questions

Deferred to later specifications/platform design:

- formal operating-state definitions;
- decision approval/signature technology;
- dissent workflow;
- multiple simultaneous decision authorities;
- delegated authority hierarchy;
- automated readiness checks;
- organization-specific additional boundary clause types and presentation;
- decision expiry;
- exception/waiver handling;
- organization-specific decision taxonomy.

### 38.1 IRR-012 Register conformance

The Register projects the exact current Integration, Decision, Boundary, and Authorization Basis position and preserves required absence, conflict, Authority Gaps, accepted uncertainty, Decision-Limiting uncertainty, conditions, due/breached/blocking facts, and source Versions. It never supplies a missing current Decision, resolves uncertainty/conflict, changes a Boundary, authorizes operation, accepts residual concern generically, or treats a proposed Configuration as authorized.

Accepted uncertainty and operating-state values may be displayed by exact identity only. Shared Dependency grouping and descriptive counts do not transfer Decision effect or Decision Authority across Cases and do not infer stronger, broader, or restrictive state relations under IRR-014.

## 39. Completion Impact

This specification completes the first five foundational specification areas identified as the initial platform-design gate:

1. Case Lifecycle
2. Managed Configuration
3. Evidence and Authority
4. Value/Risk Interface
5. Integration and Decision

These are now defined at v0.1 at an implementation-independent level.

This does not mean platform architecture should begin immediately without review, but the minimum conceptual gate is now substantially satisfied.

## 40. Next Specification

Continue the system layer with:

`PAIM_INTERVENTION_AND_LEARNING_SPEC_v0.1.md`

It should formalize:

- intervention identity/status;
- evidence-supported requirements vs. practitioner design;
- ownership;
- configuration changes;
- completion criteria;
- fallback/remediation;
- Learning Items;
- decision-specific evidence generation;
- observation relationships;
- failure/overdue handling.

## 41. Repository Placement

```text
400. Practical AI Management/
└── system/
    └── specifications/
        ├── PAIM_CASE_LIFECYCLE_SPEC_v0.1.md
        ├── PAIM_MANAGED_CONFIGURATION_SPEC_v0.1.md
        ├── PAIM_EVIDENCE_AND_AUTHORITY_SPEC_v0.1.md
        ├── PAIM_VALUE_RISK_INTERFACE_SPEC_v0.1.md
        └── PAIM_INTEGRATION_AND_DECISION_SPEC_v0.1.md
```

## 42. Conclusion

The Integration and Decision specification establishes the central management conversion in PAIM:

> **Independent analytical conclusions become an accountable organizational judgment without being collapsed, rewritten, or hidden behind a universal score.**

With this specification, the foundational path from case entry through configuration, evidence, analytical inputs, integration, and authorized decision is now defined at the system level.
