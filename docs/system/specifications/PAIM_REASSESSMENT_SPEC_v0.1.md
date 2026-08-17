# PAIM Reassessment Specification v0.1

## Status

Implementation-independent system specification for **Reassessment** in Practical AI Management (PAIM).

This specification derives from:

- `PAIM_SYSTEM_ARCHITECTURE_v0.1.md`
- `PAIM_SYSTEM_COMPLETION_BASELINE_GAP_MAP_v0.1.md`
- `PAIM_CASE_LIFECYCLE_SPEC_v0.1.md`
- `PAIM_MANAGED_CONFIGURATION_SPEC_v0.1.md`
- `PAIM_EVIDENCE_AND_AUTHORITY_SPEC_v0.1.md`
- `PAIM_VALUE_RISK_INTERFACE_SPEC_v0.1.md`
- `PAIM_INTEGRATION_AND_DECISION_SPEC_v0.1.md`
- `PAIM_INTERVENTION_AND_LEARNING_SPEC_v0.1.md`
- `PAIM_MINIMUM_MANAGEMENT_CASE_v0.3.md`
- `PAIM_PRACTITIONER_PLAYBOOK_v0.2.md`

It defines how PAIM determines whether a current management judgment remains supportable after new evidence, changed conditions, intervention results, authority changes, incidents, learning, or proposed changes in operating state.

It does not prescribe scheduling software, monitoring technology, notification mechanisms, or user-interface design.

## 1. Purpose

PAIM decisions are current judgments, not permanent approvals.

The system must be able to answer:

> **What changed?**

> **Does the current decision still apply to the current configuration?**

> **Which evidence, authority, controls, boundaries, or uncertainties must be reconsidered?**

> **May operation continue while reassessment occurs?**

> **Does management need a successor decision?**

Reassessment closes the PAIM management loop.

## 2. Reassessment Principle

```text
Current Decision
      |
      v
Operation / Intervention / Learning
      |
      v
Trigger or New Information
      |
      v
REASSESSMENT_DUE
      |
      v
Reassessment
      |
      +--> Current decision remains supportable
      |
      +--> Decision modified / successor decision
      |
      +--> Configuration changed
      |
      +--> Stronger state supported
      |
      +--> Narrower state required
      |
      +--> Suspend / discontinue
      |
      +--> More evidence / authority required
```

Reassessment must preserve the prior decision and its historical basis.

## 3. Reassessment Identity

Every material reassessment should have a durable identity.

Minimum fields:

- Reassessment ID
- Case ID
- current Decision ID/version
- current Configuration ID/version
- trigger ID/type
- status
- owner/coordinator
- date initiated
- date completed
- predecessor/successor reassessment where relevant

## 4. Reassessment Status

Possible statuses include:

- due;
- opened;
- evidence refresh in progress;
- ready for integration;
- decision pending;
- completed;
- cancelled with rationale;
- superseded.

The exact platform vocabulary may later be refined.

## 5. Trigger Types

Reassessment may be triggered by:

### 5.1 Incident or material error

Examples:

- harmful outcome;
- material incorrect result;
- significant customer/operational failure;
- control escape.

### 5.2 Value change

Examples:

- realized value materially below expectation;
- cost increases;
- substitution no longer occurs;
- new value becomes demonstrated;
- capacity benefit disappears.

### 5.3 Risk change

Examples:

- new adverse pathway;
- higher residual exposure;
- new error class;
- control effectiveness changes.

### 5.4 Control change/failure

Examples:

- verification removed;
- review burden changed;
- threshold changed;
- escalation unavailable;
- control fails in operation.

### 5.5 Configuration change

Examples:

- new model/provider;
- broader scope;
- new user population;
- new data;
- increased AI authority;
- new operating conditions.

### 5.6 Authority change

Examples:

- new governing requirement;
- contract change;
- policy change;
- unresolved authority resolved;
- authority conflict discovered.

### 5.7 Capacity/operating-condition change

Examples:

- review overload;
- staffing reduction;
- downstream bottleneck;
- production environment change.

### 5.8 Learning completion

A Learning Item produces evidence relevant to a blocked or conditional decision.

### 5.9 Proposed stronger operating state

Examples:

- experiment → continuation;
- continuation → targeted scale;
- targeted scale → institutionalization;
- institutionalization → broader deployment.

A stronger state may require reassessment even when the configuration itself has not changed.

### 5.10 Scheduled review

Management may establish a periodic reassessment cadence.

PAIM does not prescribe a universal calendar interval.

## 6. Event-Driven vs. Scheduled Reassessment

### Event-driven

Triggered because something materially changed or new evidence became available.

### Scheduled

Triggered because management previously chose a review interval.

Event-driven reassessment should not wait for the next scheduled review when the trigger is material.

## 7. Trigger Record

A material trigger should support:

- Trigger ID
- type
- date/time
- source
- description
- affected configuration
- affected decision
- affected boundary/control/evidence/authority
- severity/materiality assessment where relevant
- whether current operation may continue
- required immediate action
- reassessment status

## 8. Materiality

Not every new observation requires full reassessment.

The system should distinguish:

- informational update;
- monitor;
- analytical refresh;
- formal reassessment;
- immediate intervention/suspension plus reassessment.

Materiality remains a management judgment informed by the current decision and boundary.

## 9. Immediate Operating Disposition

When reassessment is triggered, the system should record whether operation:

- continues unchanged temporarily;
- continues under narrower conditions;
- uses fallback;
- is partially suspended;
- is fully suspended;
- requires immediate remediation;
- cannot proceed pending authority/evidence.

This is an interim management disposition, not necessarily the successor PAIM decision.

## 10. Reassessment Scope

The reassessment should identify which components require review:

- Managed Configuration;
- evidence;
- authority;
- Value Input;
- Risk Input;
- Control Dependencies;
- uncertainty;
- Integrated Operating Boundary;
- operating state;
- intervention;
- learning plan.

Not every reassessment requires complete reconstruction of every component.

## 11. Configuration Review

Ask:

- Is the current configuration still the configuration governed by the decision?
- Has a material change occurred?
- Is a new version required?
- Is a new configuration identity required?
- Which historical evidence remains applicable?

If configuration changes materially, follow `PAIM_MANAGED_CONFIGURATION_SPEC_v0.1.md`.

## 12. Evidence Review

Ask:

- What new evidence exists?
- Is prior evidence stale, contradicted, superseded, or still applicable?
- Has evidence maturity changed?
- Has a prior estimate become observed?
- Has a prior unknown been resolved?
- Has new uncertainty appeared?

Historical evidence remains preserved.

## 13. Authority Review

Ask:

- Has governing authority changed?
- Has `AUTHORITY UNRESOLVED` been resolved?
- Has a new authority gap appeared?
- Does authority now block or permit a different decision?
- Has authority applicability changed because the configuration changed?

Authority changes may require immediate boundary changes even if Value/Risk evidence is unchanged.

## 14. Value Input Review

Possible outcomes:

- current Value Input remains applicable;
- refresh required;
- successor Value Input required;
- Value Boundary changes;
- Value Implication changes.

The historical frozen input remains linked to the prior decision.

## 15. Risk Input Review

Possible outcomes:

- current Risk Input remains applicable;
- refresh required;
- successor Risk Input required;
- Risk Boundary changes;
- Risk Implication changes.

The historical frozen input remains linked to the prior decision.

## 16. Analytical Independence During Reassessment

If both Value and Risk require refresh, preserve analytical independence.

The system should not rewrite one leg merely to maintain the prior decision.

A reassessment may legitimately produce a different conflict structure than the original case.

## 17. Control Dependency Review

Ask:

- Are required controls still present?
- Are they effective under current conditions?
- Has their burden changed?
- Has capacity changed?
- Does the Value conclusion still depend on them?
- Does the Risk conclusion still depend on them?
- Does the Integrated Operating Boundary still require them?

A missing boundary-critical control is a strong reassessment signal.

## 18. Uncertainty Reclassification

Reassessment may change uncertainty from:

- Accepted → Decision-Limiting;
- Decision-Limiting → Accepted;
- unresolved → resolved;
- known → newly uncertain.

The system should preserve why classification changed.

## 19. Integrated Operating Boundary Review

Ask:

> **Is the current Integrated Operating Boundary still supportable?**

Possible outcomes:

- unchanged;
- narrowed;
- broadened;
- conditioned differently;
- replaced by transitional boundary;
- no longer supportable.

A broadened boundary requires evidence/authority supporting the broader decision.

## 20. Operating-State Review

Ask whether the current operating state remains supported.

Possible changes:

- experiment → continuation;
- continuation → targeted scale;
- scale → institutionalization;
- institutionalization → broader deployment;
- any state → constrain;
- any state → controlled transition;
- any state → suspend;
- any state → discontinue.

A state change should be explicit and authorized.

## 21. Reassessment Integration

When material analytical changes exist, PAIM Integration should be performed again using current/frozen successor inputs.

The prior Integration Record remains historical.

The reassessment integration should identify:

- what changed;
- what did not change;
- new constraints/authority;
- changed controls;
- changed uncertainty;
- changed alternatives;
- interaction analysis;
- proposed successor judgment.

## 22. Reassessment Outcomes

A completed reassessment may conclude:

### Confirm

Current decision remains supportable without substantive change.

### Confirm with conditions

Current decision remains supportable but conditions/interventions change.

### Modify boundary

Operating Boundary narrows or broadens.

### Modify operating state

A different operating state is authorized.

### Redesign / experiment

A new configuration requires evidence generation.

### Suspend

Operation stops temporarily.

### Discontinue

Configuration is retired.

### Insufficient evidence / authority

Current or stronger decision cannot be supported; fallback or constrained operation may be required.

## 23. Successor Decision

If the management judgment changes materially, create a successor Management Decision Record.

```text
Decision D1
   |
Reassessment R1
   |
Decision D2
```

D1 remains immutable and historically authoritative for its period.

D2 becomes current according to its effective status/date.

## 24. Decision Confirmation

If reassessment confirms the current decision, the system should still preserve a Reassessment Record showing:

- trigger;
- evidence reviewed;
- authority reviewed;
- rationale;
- confirmation;
- next triggers/learning.

Do not silently mark the case unchanged without a record.

## 25. Reassessment Record

Minimum content:

### Identity
- Reassessment ID
- Case ID
- prior Decision ID
- Configuration ID/version
- trigger
- dates
- owner/status

### Review
- configuration review
- evidence review
- authority review
- Value review
- Risk review
- controls
- uncertainty
- boundary
- operating state

### Outcome
- conclusion
- rationale
- current/successor decision
- intervention
- learning
- next triggers

## 26. Reassessment and Intervention

Intervention may be:

- completed before reassessment;
- triggered by reassessment;
- modified by reassessment;
- failed and causing reassessment.

The system should preserve these relationships.

## 27. Reassessment and Learning

Learning completion should not automatically change a decision.

It creates evidence for reassessment.

The reassessment determines management significance.

Likewise, inconclusive learning may leave the blocked decision blocked.

## 28. Reassessment and Boundary Breach

A material boundary breach should create a trigger.

The immediate response may include:

- stop out-of-bound activity;
- invoke fallback;
- remediate;
- narrow operation;
- suspend;
- reassess.

The system should distinguish the breach response from the final reassessment outcome.

## 29. Reassessment and Incident

Incident handling may exist outside PAIM.

PAIM requires the management significance of a material incident to be assessed against:

- current configuration;
- current boundary;
- controls;
- Risk finding;
- Value finding where relevant;
- current decision.

The platform may later integrate with incident-management systems.

## 30. Reassessment and Authority Resolution

When an Authority Gap resolves:

- create/update Authority Record;
- preserve prior gap;
- identify decisions previously blocked;
- determine whether reassessment is required;
- do not automatically authorize the stronger decision.

Authority resolution removes one barrier; Value/Risk evidence may still be insufficient.

## 31. Reassessment and Stronger Decision Requests

A request for institutionalization, expansion, or increased autonomy is itself a reassessment trigger when the current decision did not authorize that state.

The system should ask:

- Is existing evidence sufficient for the stronger state?
- Does the boundary change?
- Does uncertainty become Decision-Limiting?
- Does authority change?
- Are controls/capacity sufficient?

## 32. Reassessment and Closure

A reassessment may determine that the case should close because:

- configuration is discontinued;
- management issue no longer exists;
- successor case fully replaces it;
- no continuing PAIM management is required.

Closure follows `PAIM_CASE_LIFECYCLE_SPEC_v0.1.md`.

## 33. Longitudinal History

The system should support reconstruction of:

```text
Configuration v1
  |
Value/Risk Inputs v1
  |
Decision D1
  |
Intervention
  |
Observations / Learning
  |
Reassessment R1
  |
Configuration v2
  |
Value/Risk Inputs v2
  |
Decision D2
```

This longitudinal chain is a core distinction between PAIM as a management system and a one-time assessment.

## 34. Reassessment Integrity Checks

The system should surface:

- material trigger with no reassessment status;
- current operation outside boundary;
- configuration changed but old inputs treated as current without review;
- authority changed but decision not reviewed;
- Decision-Limiting Uncertainty resolved but blocked decision never reconsidered where intended;
- required control failed with no reassessment;
- stronger operating state adopted without successor decision;
- successor decision created without preserving prior decision;
- reassessment marked complete without outcome/rationale.

## 35. Human Judgment Points

Human/accountable judgment remains necessary for:

- trigger materiality;
- interim operating disposition;
- evidence applicability;
- configuration materiality;
- authority interpretation;
- uncertainty reclassification;
- boundary revision;
- operating-state change;
- successor judgment;
- closure.

## 36. Platform Implications

A future platform will likely require:

- reassessment queue;
- trigger records;
- current-decision view;
- changed-since-decision summary;
- evidence/authority refresh indicators;
- configuration diff;
- Value/Risk refresh status;
- interim disposition;
- successor decision workflow;
- longitudinal timeline/history.

This specification does not prescribe UI.

## 37. Behavioral Test Candidates

Future tests should include:

1. New incident triggers reassessment and temporary fallback.
2. New evidence strengthens Value but Risk remains unchanged.
3. Control failure changes Risk and narrows the boundary.
4. Authority gap resolves but stronger state remains blocked by evidence.
5. Learning completes and supports a redesign.
6. Model/provider changes; prior evidence applicability becomes uncertain.
7. Workload exceeds supported capacity.
8. Management requests institutionalization from bounded continuation.
9. Reassessment confirms current decision unchanged.
10. Reassessment produces successor decision while preserving prior history.
11. Scheduled reassessment occurs with no material change.
12. Boundary breach is remediated but still requires recorded review.

## 38. Open Questions

Deferred to later specifications/platform design:

- formal trigger severity taxonomy;
- automatic vs. human trigger generation;
- reassessment service levels;
- notification timing;
- incident-system integration;
- evidence refresh workflow;
- decision effective-date handling;
- simultaneous reassessments;
- portfolio-level reassessment;
- closure/retention policy.

## 39. Completion Impact

This specification completes the core closed-loop management sequence:

> **Case → Configuration → Evidence/Authority → Value/Risk → Integration/Decision → Intervention/Learning → Reassessment**

The remaining major system specifications are increasingly portfolio/governance oriented rather than core single-case logic.

## 40. Next Specification

Create:

`PAIM_MANAGEMENT_REGISTER_SPEC_v0.1.md`

It should formalize the cross-case management view:

- AI configuration inventory;
- current decisions/operating states;
- unresolved authority;
- Decision-Limiting Uncertainty;
- intervention status;
- reassessment queue;
- boundary breaches;
- evidence maturity;
- provider/model concentration;
- management attention indicators.

## 41. Repository Placement

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
        └── PAIM_REASSESSMENT_SPEC_v0.1.md
```

## 42. Conclusion

The Reassessment specification makes PAIM explicitly longitudinal.

Its central rule is:

> **New evidence or changed conditions do not rewrite the old decision. They trigger a traceable reconsideration of whether that decision still applies.**

This closes the single-case management loop and prepares PAIM for portfolio-level management across many AI configurations.
