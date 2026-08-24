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

**Normative cross-cutting contract:** `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md` governs authoritative Reassessment identity/version/history, operation during reassessment, the Interim Operating Disposition, Decision Confirmation, and the mandatory successor/amendment rule for any changed operating state, Integrated Operating Boundary, or substantive Decision condition.

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

Every material Reassessment has a stable Reassessment ID and immutable Reassessment Version IDs under the common integrity contract.

One Reassessment identity binds exactly:

- one owning Case;
- one initiating governing Decision Version;
- one governing/target Configuration Version;
- one explicit purpose and structured affected scope sufficient for overlap checks;
- one Reassessment Owner accountability relationship;
- one lifecycle/status history; and
- predecessor/successor Reassessment identity where relevant.

Every finalized Reassessment Version additionally binds one complete immutable **Trigger Set** containing exact Trigger Version IDs and exact Trigger-to-Reassessment Membership Version IDs, plus its content, status at finalization where applicable, recorded time, effective time/interval, and exact relied-upon records.

Adding or removing an eligible Trigger from an open Reassessment creates a successor Reassessment Version and a successor immutable Trigger Set. The predecessor Version and Trigger Set remain unchanged. Analytical refresh within the same Case, initiating Decision, target Configuration, substantive purpose/scope, and Trigger Set retains the Reassessment identity but creates any new content/basis Version required by the integrity contract.

Changing Case, initiating Decision Version, governing/target Configuration Version, or substantive purpose/scope requires a new/successor Reassessment identity. It must not be represented merely as another Version of the prior identity.

If the governing Decision or Configuration is absent or conflicting, a proposed initiation may preserve that explicit absence/conflict. It cannot become `OPEN` and must not invent an identity or Version to satisfy the fields above.

## 4. Reassessment Status

The v0.1 Reassessment statuses are exactly:

- `PROPOSED` — identity/scope is recorded, but opening context or accountability is not yet established;
- `OPEN` — exact context, Reassessment Owner, and Trigger Set are established;
- `ANALYSIS_IN_PROGRESS` — accountable review has begun;
- `AWAITING_DECISION_AUTHORITY` — review is ready for its outcome path, but required confirmation/successor authority is not established;
- `BLOCKED_CONFLICT` — an explicit Trigger, membership, grouping, overlap, coverage, authority, accountability, or currentness conflict blocks the affected action;
- `COMPLETED_CONFIRMED` — the Reassessment atomically produced its immutable unchanged-Decision Confirmation;
- `COMPLETED_SUCCESSOR_DECISION` — the Reassessment atomically produced its authorized successor/amendment Decision path;
- `CANCELLED` — accountable termination without completion; and
- `SUPERSEDED` — accountable prospective replacement by one named successor Reassessment.

`REASSESSMENT_DUE` and `REOPENED` are Case lifecycle states, not Reassessment statuses. `REASSESSMENT_REQUIRED_UNASSIGNED` is a Trigger coverage state, not a Reassessment status. Blocked, conflicting, unassigned, awaiting authority, or otherwise unresolved work is never completed.

Allowed prospective progress is `PROPOSED` → `OPEN` → `ANALYSIS_IN_PROGRESS` → `AWAITING_DECISION_AUTHORITY` → exactly one completion status. `OPEN`, `ANALYSIS_IN_PROGRESS`, and `AWAITING_DECISION_AUTHORITY` may enter or leave `BLOCKED_CONFLICT` only through a recorded resolution/status event that preserves the conflict history. Any non-terminal active status may become `CANCELLED` or `SUPERSEDED` only under §38.6. Terminal statuses do not reopen; continuing work uses an explicitly linked successor Reassessment.

Status events do not mutate finalized Reassessment content. A Trigger Set, purpose/scope, rationale, conclusion, accountability, or other substantive-content change requires a new Reassessment Version. Finalized versions, status history, current selection, correction, and supersession follow `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, §3.

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

An authoritative Trigger has a stable Trigger ID and immutable Trigger Version IDs. One Trigger identity represents one established source occurrence, one exact affected/owning Case, and one declared management question. Every finalized Trigger Version retains at minimum:

- exact Trigger ID and Trigger Version ID;
- exact affected/owning Case;
- exact initiating/current governing Decision Version and governing Configuration Version when established, or explicit absence/conflict rather than invented identifiers;
- trigger type/category and declared management question/structured affected scope;
- exact existing PAIM source family, Record ID, and Record Version ID, or explicit human/external source system, source-event identity, actor/provenance, and received/knowledge time;
- description/rationale and exact affected boundary, control, Evidence, Authority, Intervention, Learning, or other references where known;
- effective time, recorded time, and source knowledge context;
- predecessor, correction, supersession, and withdrawal relationships; and
- one current accountable Trigger Determination under §8.

Exact replay identity is identity-level: the same established source occurrence identity, exact affected Case, declared management question, and command idempotency identity. Exact replay returns the original authoritative outcome or explicit payload mismatch; it does not create another Trigger.

A materially updated Version of the same established source occurrence, Case, and management question creates a successor Trigger Version and preserves its predecessor. A distinct management question creates a distinct Trigger identity only through an accountable determination. Similar text, category, timestamp, severity, provider name, source family, or software classification must not deduplicate or establish identity.

One external/provider/control/source event affecting multiple Cases creates distinct Case-scoped Trigger identities that cite the same exact source provenance. Each Case independently establishes its Trigger Determination, Reassessment, accountability, Decision, Configuration, Interim Operating Disposition, and outcome. Source similarity or a provider-name match does not create a Trigger for another Case and does not transfer authority, satisfaction, or outcome.

This contract does not create an Observation record, Observation identity/version/cardinality, retention rule, or automated Observation-to-Trigger conversion.

## 8. Materiality

Not every new observation requires full reassessment.

Every current Trigger has exactly one eligible accountable Trigger Determination, explicit `TRIGGER DETERMINATION NOT ESTABLISHED`, or `TRIGGER DETERMINATION CONFLICT — UNRESOLVED`. The determination outcomes are exactly:

- `INFORMATIONAL`;
- `MONITOR`;
- `ANALYTICAL_REFRESH`;
- `REASSESSMENT_REQUIRED`; and
- `IMMEDIATE_DISPOSITION_AND_REASSESSMENT`.

The determination retains its stable identity/immutable Version, exact Trigger Version, Case/Decision/Configuration context, outcome, rationale, actor, exact accountable Role Assignment Version or genuine governed mechanism Version/reference, exact delegation chain where used, effective time, recorded time, and correction/supersession/withdrawal history.

Materiality remains an accountable management judgment informed by the current Decision and Boundary. Source type, category, severity, timestamp, queue priority, text similarity, provider identity, row order, recency, hierarchy, breadth, specificity, ownership, technical principal, and software permission do not establish materiality or select a winner. Two incompatible eligible current determinations are conflict with all candidates retained; recency never resolves them.

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

Every operating effect in this section must be recorded and authorized through the Interim Operating Disposition contract in `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, §7, unless an authorized successor/amendment Decision is already effective. An Interim Operating Disposition may continue unchanged operation, narrow, invoke authorized fallback, remediate, or suspend, but it may not broaden the boundary, authorize a stronger state, remove a required control, resolve an Authority Gap, or permanently change Decision conditions.

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

This outcome confirms the existing Decision without a successor only when the change is a non-substantive implementation detail that remains within the exact operating state, Integrated Operating Boundary, configuration, required controls, authority conditions, and substantive Decision conditions. Otherwise it is an authorized successor/amendment Decision under `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, §§7.5–7.6.

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

If the management judgment changes materially, create a successor Management Decision Record. Any change to operating state, Integrated Operating Boundary, governed configuration, or substantive Decision condition is material for this rule and requires an authorized successor/amendment Decision even when the prior Decision remains otherwise supportable.

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

- exact immutable Trigger Set and Membership Versions;
- evidence reviewed;
- authority reviewed;
- rationale;
- confirmation;
- next triggers/learning.

The completed Reassessment must also create the immutable Decision Confirmation defined in `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, §7.5, binding the unchanged Decision and Boundary Snapshot. Every completed Reassessment has exactly one outcome path: unchanged-Decision confirmation or authorized successor/amendment Decision.

Do not silently mark the case unchanged without a record.

## 25. Reassessment Record

Minimum content:

### Identity
- Reassessment ID/Version
- exact owning Case ID
- exact initiating governing Decision ID/Version
- exact governing/target Configuration ID/Version
- explicit purpose and structured affected scope
- exact immutable Trigger Set and Membership Versions
- effective/recorded/knowledge context
- exact Reassessment Owner accountability
- status and predecessor/successor history

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
- Decision Confirmation or successor/amendment Decision
- ended/superseding Interim Operating Disposition
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

Every version and relationship in the chain must remain exactly retrievable under `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, §§3.11–3.12. Reassessment workflow state may coexist with operation only under the current Decision/Boundary and any current authorized Interim Operating Disposition.

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

## 38. Trigger, Membership, Concurrency, and Coverage Contract

### 38.1 Many-to-many membership and immutable Trigger Set

Trigger-to-Reassessment cardinality is many-to-many. One Trigger may feed multiple Reassessments only for explicitly distinguishable scopes/purposes or explicit successor coordination. One Reassessment may bind multiple Trigger Versions.

Every Trigger-to-Reassessment Membership is authoritative and versioned. It retains stable Membership ID, immutable Membership Version ID, exact Trigger Version, exact Reassessment identity/Version, membership purpose/scope, accountable grouping/coordination determination where required, effective/recorded time, and correction/supersession/withdrawal history.

Every finalized Reassessment Version binds its complete immutable exact Trigger Set. One Reassessment must not silently consume another's Trigger. Adding or removing membership from an open Reassessment atomically creates the Membership fact and successor Reassessment Version/Trigger Set, or creates neither.

### 38.2 Grouping and duplicate disposition

Software may mechanically establish exact Case, initiating Decision Version, governing/target Configuration Version, and structured affected-scope facts. It must not semantically group Triggers. Same exact context establishes only potential compatibility.

An authoritative **Trigger Grouping/Compatibility Determination** retains exact Trigger Versions, target Reassessment identity/Version, exact context and structured scope, outcome/rationale, actor, one eligible accountable assignment or governed mechanism, delegation where used, effective/recorded time, and immutable history. Selection returns one eligible determination, `TRIGGER GROUPING NOT ESTABLISHED`, or `TRIGGER GROUPING CONFLICT — UNRESOLVED`.

Different Cases, initiating Decision Versions, target Configuration Versions, or substantively unrelated purposes are mechanically incompatible for one Reassessment identity. Timestamp, severity, category, source similarity, scope breadth, owner, queue priority, and software permission never establish compatibility or select a winner.

Exact idempotent replay under §7 creates no second Trigger and requires no substantive duplicate disposition. A claim that two distinct Trigger identities represent one management obligation requires an authoritative **Duplicate Disposition** by Reassessment Coordination Authority. It names the exact canonical Trigger Version and prospective coverage basis and returns one eligible disposition, `DUPLICATE DISPOSITION NOT ESTABLISHED`, or `DUPLICATE DISPOSITION CONFLICT — UNRESOLVED`. Semantic similarity alone is ineligible.

### 38.3 Concurrent Reassessments and overlap

Multiple open Reassessments may coexist in one Case only when:

1. their declared structured affected scopes are mechanically disjoint; or
2. one eligible accountable compatibility/coordination determination establishes coexistence for the exact Versions, context, scope, and time.

A shared Trigger, shared affected exact record/scope, competing proposed Decision consequence, or missing/indeterminate scope is `REASSESSMENT OVERLAP CONFLICT — UNRESOLVED` absent an eligible coordination determination. Conflict preserves both analyses/history and blocks completion and scope-changing Interim Operating Disposition action for the affected overlap.

Creation time, recency, severity, owner, role hierarchy, broader/narrower scope, row order, and software priority never establish non-overlap or select a Reassessment winner.

### 38.4 No merge in v0.1

`MERGED` is not a PAIM v0.1 Reassessment status or action. No Reassessment absorption operation exists. Coordination is exactly one of:

- explicit non-overlapping coexistence;
- authorized cancellation; or
- authorized history-preserving supersession.

Any future merge is outside Increment 6. If later accepted, it must create a new successor Reassessment preserving every predecessor identity/Version, Trigger relationship, accountability, rationale, and time. It must not absorb or destructively collapse a predecessor.

### 38.5 Trigger coverage and no-lost-trigger invariant

For each current eligible Trigger whose current Trigger Determination is `REASSESSMENT_REQUIRED` or `IMMEDIATE_DISPOSITION_AND_REASSESSMENT`, authoritative selection at an exact effective time and optional knowledge cutoff returns exactly one compatible **Trigger Coverage State**:

- `REASSESSMENT_REQUIRED_UNASSIGNED` — visible and awaiting accountable assignment;
- `LINKED_ACTIVE` — linked to at least one eligible active Reassessment, with multiple links permitted only for distinguishable scope or eligible coordination;
- `BLOCKED_CONFLICT` — assignment, grouping, overlap, authority, accountability, or currentness conflict prevents valid active coverage;
- `SATISFIED_BY_COMPLETED_REASSESSMENT` — an exact completed outcome explicitly covers the Trigger Version; or
- `DUPLICATE_DISPOSITIONED` — an eligible identity-level duplicate disposition names the canonical Trigger and exact prospective coverage basis.

No eligible requiring Trigger may be absent from this result. More than one incompatible current coverage result is `TRIGGER COVERAGE CONFLICT — UNRESOLVED`; the system must not select by recency, status desirability, or convenience. A corrected, withdrawn, or superseded Trigger Version is prospectively ineligible, while all historical coverage remains exactly reconstructable.

Queues, dashboards, notifications, and Register views are derived and cannot substitute for this invariant.

### 38.6 Cancellation and supersession

`CANCELLED` and `SUPERSEDED` are explicit accountable prospective actions, never automatic consequences of a newer Decision, Configuration, Trigger, Reassessment, source correction, duplicate claim, or later row.

Cancellation ends planned work without a completed Reassessment outcome. It retains exact Reassessment/Trigger scope, rationale, actor, accountable assignment/mechanism and delegation, effective/recorded time, and history. Supersession additionally names exactly one successor Reassessment identity/Version and replacement scope. Neither means the predecessor was invalid historically.

One Reassessment cannot close another. Before cancellation or supersession commits, every unresolved eligible Trigger in the predecessor Trigger Set must atomically retain or acquire one compatible prospective coverage result under §38.5. Failure leaves the Reassessment and all Trigger coverage unchanged.

### 38.7 Accountability

Trigger Determination uses the substantive `Trigger Determiner` function. Reassessment content/status progression uses `Reassessment Owner`. Grouping, duplicate disposition, compatibility/overlap coordination, cancellation, supersession, and Trigger coverage transfer use `Reassessment Coordination Authority`.

Each action resolves exactly one eligible accountable Role Assignment or genuine governed organizational mechanism, explicit not established, or explicit conflict under `PAIM_ROLES_AND_ACCOUNTABILITY_SPEC_v0.1.md`. The applicable typed target set is the exact initiating Decision, exact target Configuration, and owning Case; the exact Intervention is additionally applicable only when it is the Trigger source/scope. Assignments retain their own target type and are never converted into another scope.

No broad/narrow, recency, specificity, hierarchy, ownership, technical-principal, administrator, queue, or software-permission winner exists. Delegation and governed mechanisms must be exact, versioned, scoped, time-valid, complete, and fail closed. Decision Authority remains separately required for Interim Operating Dispositions and successor/amendment Decisions under the existing Authorization Basis contracts.

Later routine role expiry does not rewrite a historically valid Reassessment action. Expiry, revocation, withdrawal, or supersession is prospective for future actions.

### 38.8 Completion and concurrent current-governance validation

Immediately before completion, the platform revalidates at the completion effective time and knowledge cutoff:

- exact current Decision and governing Configuration;
- exact Reassessment Version and Trigger Set;
- Trigger Determinations and coverage;
- grouping/coordination and absence of unresolved overlap;
- Reassessment Owner accountability and required delegation/mechanism; and
- Decision/confirmation authority required by the governing contracts.

Completion is one semantic transaction producing exactly `COMPLETED_CONFIRMED` plus its immutable Decision Confirmation, or `COMPLETED_SUCCESSOR_DECISION` plus the authorized successor/amendment Decision, Boundary Snapshot, and Decision Authorization Basis. Zero paths, both paths, or any blocked/unresolved basis is invalid and commits no partial completed state.

If one concurrent Reassessment confirms the same Decision unchanged, others do not automatically close. They may continue only after prospective revalidation. If a successor/amendment Decision becomes effective, an open predecessor-bound Reassessment remains historical analysis but cannot complete as current against stale governance. Prospective continuation requires an accountable coordination determination, a new/successor Reassessment identity bound to the current Decision/Configuration, explicit Trigger carry-forward memberships, and explicit predecessor cancellation/supersession where applicable.

A future-effective successor changes eligibility only from its effective time. Recorded time and knowledge cutoff remain independently queryable.

### 38.9 Concurrent Interim Operating Dispositions

Each Reassessment may support its own historical and current eligible Interim Operating Dispositions. Independently valid current dispositions may coexist. Effective operation remains the exact current Decision/Boundary intersected with every applicable valid restrictive disposition under the Integrity specification, §7.

The determinable intersection applies; an indeterminate intersection suspends affected scope pending authorized determination. Expiry is prospective. Strongest state, severity, newest, ordinal, broader/narrower, and IRR-014 ranking are never used.

### 38.10 Dual-time and historical reconstruction

All Trigger, Determination, Membership, Trigger Set, Grouping/Compatibility, Duplicate Disposition, Coverage, Reassessment Version/status, cancellation/supersession, Interim Disposition, and outcome selection reuses the common integrity kernel. Commands depending on current state carry expected-Version/current-selection preconditions; stale commands reject or surface conflict and never silently rebase.

Historical reconstruction retains the exact Trigger Set and memberships; Trigger Determinations and coverage; grouping, duplicate, and coordination determinations; Reassessment Versions/status events; analytical inputs; Evidence/Authority; Value/Risk refreshes; Decision/Configuration/Boundary; accountability/delegation/mechanisms; Interim Dispositions; effective, recorded, and knowledge context; and exactly one completed outcome basis.

Later correction, withdrawal, role expiry, supersession, cancellation, or successor Decision never rewrites prior knowledge-time or completed basis. Prospective eligibility remains fail-closed.

### 38.11 Deferred boundaries

- **IRR-009:** no Observation identity/version/cardinality, persistence, retention, or automated Observation-to-Trigger conversion is defined. Allowed sources are exact existing PAIM records and explicit human/external events with retained provenance.
- **IRR-012:** accepted Management Register projection may surface exact Trigger, Reassessment, and Interim Operating Disposition facts and Shared Dependency groups, but it never substitutes for Case-scoped selection, coverage, coordination, completion, authority, or outcome and never creates Register-driven workflow.
- **IRR-014:** exact operating-state values may be retained and compared only for identity and exact authorized applicability. No stronger, broader, more-restrictive, escalation-rank, automatic-target-state, priority, materiality, or grouping inference is permitted.

### 38.12 Prospective Trigger and Reassessment Responsibilities

After explicit consumer cutover under `PAIM_RESPONSIBILITY_AND_CASE_WORK_SPEC_v0.1.md`:

- `DETERMINE_TRIGGER` binds the exact Trigger Version, owning Case, initiating Decision and target
  Configuration Versions when established, and declared management question/scope;
- `LEAD_REASSESSMENT` binds the exact Reassessment Version, immutable Trigger Set Version,
  Decision Version, Configuration Version, and declared scope; and
- `COORDINATE_REASSESSMENT` binds every exact Reassessment/Trigger Set Version participating in
  the grouping, duplicate, coexistence, overlap, cancellation, supersession, or coverage question.

Each kind resolves separately. Case coordination, source authorship, queue assignment, practical
role, access, or another Reassessment Responsibility is not a substitute. Work may carry exact
context and return but cannot create a Trigger Determination, Reassessment, coordination
determination, Interim Operating Disposition, confirmation, or successor Decision. This section
does not introduce Gate-5 planned-review or review-timing semantics.

## 39. Open Questions

Deferred to later specifications/platform design:

- formal trigger severity taxonomy;
- automatic vs. human trigger generation;
- reassessment service levels;
- notification timing;
- incident-system integration;
- evidence refresh workflow;
- organization-specific scheduling and presentation of future-effective successor decisions;
- portfolio-level reassessment;
- closure/retention policy.

### 39.1 IRR-012 Register conformance

The Register projects `REASSESSMENT_REQUIRED_UNASSIGNED`, `BLOCKED_CONFLICT`, Trigger Determination/Coverage conflict, eligible active or overdue Reassessment, owner vacancy/conflict, overlap conflict, and outcome-blocked work as exact current attention. Completed, cancelled, and superseded Reassessments are historical unless another current concern cites them.

Every current Interim Operating Disposition exact-scope partition remains independently visible. Suspension or indeterminate intersection affects only its exact scope; the Register never globally intersects disjoint scope or ranks operating-state values. Dashboard/queue order, severity, timestamps, provider identity, Shared Dependency groups, and notification state cannot group Triggers, select coverage, coordinate Reassessments, close work, or transfer outcomes across Cases. Register actions opening a Trigger/Reassessment invoke the exact Increment 6 commands and all accountability/current-governance guards.

## 40. Completion Impact

This specification completes the core closed-loop management sequence:

> **Case → Configuration → Evidence/Authority → Value/Risk → Integration/Decision → Intervention/Learning → Reassessment**

The remaining major system specifications are increasingly portfolio/governance oriented rather than core single-case logic.

## 41. Next Specification

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

## 42. Repository Placement

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

## 43. Conclusion

The Reassessment specification makes PAIM explicitly longitudinal.

Its central rule is:

> **New evidence or changed conditions do not rewrite the old decision. They trigger a traceable reconsideration of whether that decision still applies.**

This closes the single-case management loop and prepares PAIM for portfolio-level management across many AI configurations.
