# PAIM Increment 5 Intervention Design Decision v0.1

## 1. Purpose and baseline

This artifact presents the bounded PAIM design-authority choices needed to resolve **IRR-010 — Intervention prerequisite and completion acceptance semantics** before Increment 5 implementation begins. It is a design-analysis and recommendation artifact, not a governing specification and not an implementation contract by itself. The recommendations become normative only through later accepted specification hardening.

The baseline is the clean PAIM engineering checkpoint at merge commit `b6c6625c16a1ee434563e41dfd5b37bf2c075cf4`, after accepted Increments 1–4. APRM is outside scope.

The analysis is governed by:

- `PAIM_IMPLEMENTATION_SEQUENCE_AND_P1_GATES_v0.1.md`, especially §§3.2, 4.6, 5, 6.3, 7, and 10.3;
- `PAIM_CODEX_IMPLEMENTATION_READINESS_REVIEW_v0.1.md`, IRR-010;
- `PAIM_INTERVENTION_AND_LEARNING_SPEC_v0.1.md`, especially §§2–18, 29–31, and 35–41;
- `PAIM_CASE_LIFECYCLE_SPEC_v0.1.md`, especially §§9–11, 16, and 20–23;
- `PAIM_INTEGRATION_AND_DECISION_SPEC_v0.1.md`, especially §§21–30;
- `PAIM_ROLES_AND_ACCOUNTABILITY_SPEC_v0.1.md`, especially §§11, 15, 22–28, 35, and 39; and
- `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, especially §§2.3, 3, 5, 8–11.

Current governing specifications control where they already state an invariant. This artifact does not reopen accepted identity, versioning, Configuration ownership, Decision authorization, Role Assignment, conflict, historical-reconstruction, or Value/Risk semantics.

The proposed v0.1 package is deliberately bounded:

1. classify each exact Decision-to-Intervention obligation;
2. separate implementation status, completion evidence, accountable completion acceptance, and prerequisite satisfaction;
3. use a deterministic all-required-before-operation guard;
4. require explicit acceptance accountability and explicit activation authority;
5. preserve replacement, fallback, successor-Decision, and historical semantics; and
6. leave unrelated Learning, Observation, Reassessment, Register, and operating-state ordering questions deferred.

## 2. IRR-010 original ambiguity

The original readiness review identified a gap between individual Intervention status and the lifecycle guard for target operation. One Decision may identify several Interventions, but the specifications do not yet determine:

- which Interventions must complete before target operation;
- which obligations may complete after target operation or remain optional;
- whether one completed item can release a target when other items remain open;
- whether alternatives, order, or conditions change the aggregate rule;
- what constitutes completion evidence;
- who accepts that evidence and completion criteria;
- whether an Intervention Owner may self-certify completion;
- whether partial, failed, cancelled, blocked, replacement, or fallback work can satisfy an obligation;
- whether a current authorized Decision plus satisfied prerequisites is enough to activate operation; and
- how obligations and accepted completions behave under a successor Decision or target Configuration change.

The ambiguity is material because the existing lifecycle already says:

- `DECIDED` may move to `INTERVENTION_IN_PROGRESS` when the Decision identifies prerequisite or material implementation actions;
- `INTERVENTION_IN_PROGRESS` may move to `OPERATING_OBSERVING` only when all prerequisite Interventions are accepted complete and target Configuration/Boundary alignment is confirmed; and
- blocked, failed, cancelled, or materially partial prerequisite Interventions prevent target operation.

Without IRR-010, an implementation could incorrectly equate `completed` status with accepted completion, choose one of several obligations by convenience, allow an owner or administrator to activate its own work, or silently reuse a prior completion under a changed Decision.

## 3. Fixed upstream invariants from Increments 1–4

The following are fixed constraints, not open design choices.

### 3.1 Identity, version, time, and history

- Intervention is an authoritative record family with stable Record ID and immutable Version IDs.
- Finalized Intervention plans and completion results are immutable. Substantive changes create a new version; status history does not rewrite content.
- Effective time and recorded time are distinct.
- Correction, amendment, supersession, withdrawal, and point-in-time reconstruction preserve predecessors and exact relied-upon versions.
- Absence and conflict remain explicit. No newest, narrowest, broadest, most permissive, or row-order winner is allowed.

### 3.2 Exact Decision and Configuration binding

- An authorized Decision binds an exact Decision Version, Configuration Version, Integration, Boundary Snapshot, and Decision Authorization Basis.
- A material target Configuration change does not mutate the prior Configuration or Decision.
- The Intervention must identify its exact Decision Version and intended target Configuration Version.
- Prior/current operation during target Intervention remains governed by the exact Decision, Boundary, Configuration, and any Interim Operating Disposition that authorize that continuing operation.
- Starting an Intervention does not authorize the target Configuration to operate.

### 3.3 Lifecycle separation

- Case lifecycle state, AI operating state, Configuration status, Intervention status, and acceptance status are separate dimensions.
- `INTERVENTION_IN_PROGRESS` describes management workflow and may coexist with continued prior operation.
- Target operation is blocked while any prerequisite Intervention is blocked, failed, cancelled, or materially partial.
- `OPERATING_OBSERVING` requires exact target Configuration/Boundary alignment and accepted completion of all prerequisite Interventions.

### 3.4 Accountability and authority

- Technical principal, PAIM actor, Role Assignment, accountable assignment/mechanism, Decision Authority, and software permission are separate facts.
- A Role Assignment has one typed target. Configuration-, Decision-, and Intervention-scoped assignments retain owning-Case context without becoming Case-scoped.
- Broad and narrow assignments have no implicit precedence. Accountability returns one eligible assignment/mechanism, vacancy/not established, or explicit conflict.
- Explicit supersession, delegation, or an accepted versioned policy is required to displace competing accountability.
- Intervention Owner implements, reports status, identifies blockers, and demonstrates completion criteria. Ownership does not automatically confer completion-acceptance authority or Decision Authority.
- Decision Authority authorizes the management judgment and Intervention requirement but does not automatically become the completion acceptor unless separately established for that function.

### 3.5 Human judgment boundary

- Software may validate record completeness, exact references, status, scope, time, currentness, and conflict.
- Software cannot infer substantive completion acceptance merely from work status or the existence of evidence.
- A governed organizational mechanism may make a determination only when the rule and its authority are explicitly established and retained as the basis.
- Learning evidence or an Intervention status change cannot silently change an authorized Decision.

## 4. Genuine human design choices

The following choices require PAIM design authority. Sections 5–12 analyze them in detail.

| ID | Human choice | Realistic alternatives | Recommended v0.1 posture | Reversible without data-model breakage? |
|---|---|---|---|---|
| D1 | Requirement vocabulary | Binary prerequisite/not-prerequisite; three explicit types; extensible conditional taxonomy | Three explicit types: `REQUIRED_BEFORE_OPERATION`, `REQUIRED_AFTER_OPERATION`, `OPTIONAL` | Yes, if type is versioned and not encoded as a Boolean |
| D2 | Requirement scope and reuse | Configuration-global requirement; exact Decision obligation; implicit multi-Decision reuse | Exact Decision-Version-to-Intervention obligation bound to target Configuration Version; reuse only through a separate explicit determination | Yes; later richer relationships can extend the obligation record |
| D3 | Multiple-prerequisite aggregation | All-of; grouped one-of-N/ordered/conditional graph; discretionary case-level declaration | All current `REQUIRED_BEFORE_OPERATION` obligations must be accepted complete; defer groups/order/conditions | Yes, if obligations have stable identity and relationships |
| D4 | Completion inference | Status implies completion; evidence mechanically implies acceptance; separate accountable acceptance | Separate work status, completion result/evidence, completion acceptance, and derived prerequisite result | No safe simplification later; separation is foundational |
| D5 | Completion acceptor | Intervention Owner by default; Decision Authority by default; separate acceptance function | Separate `Intervention Completion Acceptor` function resolved through exact Role Assignment or governed mechanism | Yes; organizations can assign that function to existing roles |
| D6 | Self-acceptance | Always permit owner; universally prohibit owner; permit only with separately established acceptance authority | Permit the same actor only when a separate applicable acceptance assignment/mechanism is proved and both functions are recorded | Yes; later segregation policy can be stricter |
| D7 | Status and prerequisite outcomes | One combined status; free-text judgment; separate deterministic vocabularies | Separate implementation, acceptance, obligation, and aggregate results | Extensible if vocabularies are versioned |
| D8 | Aggregate persistence | Stored mutable summary; purely derived query; authoritative sources plus derived result and immutable activation snapshot | Combination: authoritative obligations/results/acceptances, deterministic derivation, immutable activation basis | Yes; projection technology remains replaceable |
| D9 | Activation authority | Automatic on checklist completion; fresh Decision every time; explicit activation authorization under the existing Decision | Explicit activation event authorized by applicable Decision Authority or an activation mechanism pre-authorized in the exact Decision | Yes; mechanism policy can evolve without changing history |
| D10 | Successor/fallback reuse | Silent carry-forward; never reuse; explicit continued-validity/replacement determination | Explicit reuse or replacement relationship, exact scope check, and accountable acceptance; successor Decision where substantive conditions change | Yes; explicit relationships support later richer policy |

The effects of those choices are explicit rather than implementation-driven:

| ID | Traceability and accountability effect | Operator-usability effect | Implementation-complexity effect |
|---|---|---|---|
| D1 | Preserves why an open item does or does not block operation. | Three recognizable labels distinguish release blockers, later commitments, and optional work. | One versioned enum; much smaller than a condition language. |
| D2 | Prevents Configuration-global or cross-Decision authority leakage and retains exact reuse provenance. | Operators can see both the reused work and the new Decision obligation. | Requires an obligation relationship and explicit reuse record rather than a mutable Intervention flag. |
| D3 | Makes every blocking item inspectable and prevents discretionary waiver by omission. | Produces a predictable checklist while retaining item diagnostics. | A deterministic set fold; grouped expressions are deferred. |
| D4 | Separates performer claim, evidence, accountable judgment, and guard result. | Shows precisely whether work, evidence, or acceptance is still missing. | Requires separate record families/relationships but avoids later migration out of an overloaded status. |
| D5 | Assigns one exact accountable acceptance result without making an existing role silently authoritative. | Organizations may staff the function with a familiar role while users see which function they exercised. | Reuses accepted typed Role Assignment/current-selection semantics. |
| D6 | Makes same-person overlap visible and authorized instead of assumed. | Supports small teams without hiding a conflict-of-role fact. | One additional eligibility check; stricter organization policy can layer on later. |
| D7 | Prevents operational status from overwriting acceptance or prerequisite facts. | Gives distinct, actionable reasons such as incomplete, blocked, or conflict. | Several small controlled vocabularies replace ambiguous free text. |
| D8 | Reconstructs the exact release basis while keeping projections rebuildable. | Users receive a current result plus exact contributing items. | Requires an immutable activation snapshot but no mutable aggregate authority table. |
| D9 | Prevents a technical checklist or owner assertion from authorizing operation. | Adds a clear release event and permits pre-authorized straight-through release where governance allows it. | One activation authority/basis path; avoids duplicating the entire Decision. |
| D10 | Preserves prior validity and successor accountability without forcing needless rework. | Clearly distinguishes reused, replaced, and newly required work. | Requires exact relationship and continued-validity evaluation; avoids blanket cloning or silent carry-forward. |

No recommendation is selected merely because it is easier to implement. The package prioritizes decision traceability, accountable operational release, usable deterministic guard behavior, and future extensibility without a generic workflow engine.

## 5. Intervention requirement-type analysis

### 5.1 Alternatives

**Alternative A — Boolean prerequisite flag.** An Intervention either blocks operation or does not. This is easy to display, but it loses the distinction between a mandatory post-operation commitment and a discretionary item. Operators cannot tell whether a non-blocking open item is overdue mandatory work or merely optional.

**Alternative B — Three explicit types.** Use `REQUIRED_BEFORE_OPERATION`, `REQUIRED_AFTER_OPERATION`, and `OPTIONAL`. This directly answers the activation question while preserving mandatory post-operation work. It is understandable to operators and provides stable traceability without prescribing workflow order.

**Alternative C — Rich conditional taxonomy.** Add one-of-N, ordered, conditional, phase-specific, recurring, and state-dependent types. This could model complex programs but would force premature decisions about expression syntax, dependency evaluation, and state ordering, approaching a generic workflow engine and entangling IRR-014.

### 5.2 Recommended type semantics

Adopt Alternative B for v0.1:

| Requirement type | Meaning | Initial target-operation effect |
|---|---|---|
| `REQUIRED_BEFORE_OPERATION` | The exact target Configuration may not enter operation until this obligation is satisfied. | Blocks until accepted complete or validly replaced and satisfied |
| `REQUIRED_AFTER_OPERATION` | The exact Decision permits initial target operation before completion, but completion remains a mandatory current commitment under the Decision's stated timing/condition. | Does not block initial activation; later failure/overdue status creates attention and may trigger reassessment or an authorized operating response |
| `OPTIONAL` | Management records the Intervention as desirable or contingent but does not make it a condition of current target operation. | Does not block activation and is never counted as a mandatory prerequisite |

Learning is not a fourth Intervention requirement type. A Learning Item remains a distinct record family with its own status, evidence, and Decision relationship.

### 5.3 Exact requirement identity and scope

The requirement is an authoritative **Decision-to-Intervention Obligation Version**, not a mutable property of the Intervention and not a Configuration-global label. Minimum binding should include:

- Obligation ID and immutable Obligation Version ID;
- exact Decision ID/Version;
- exact target Configuration ID/Version;
- exact Intervention ID and required Intervention Version or allowed successor relationship;
- requirement type;
- rationale and provenance;
- completion criteria or exact reference to their governing Intervention Version;
- timing/condition for `REQUIRED_AFTER_OPERATION` where material;
- exact Boundary clauses, Decision conditions, controls, or prohibitions implemented;
- effective/recorded time; and
- predecessor, amendment, supersession, replacement, or reuse relationships.

The Decision Version owns the normative requirement. The Configuration Version is the operational target. Both are required: Decision-only binding would obscure what is being activated, while Configuration-only binding would silently transfer obligations between management judgments.

### 5.4 Reuse across Decisions

One Intervention may support more than one Decision obligation, but it does not satisfy them implicitly. Each Decision Version has a separate obligation and a separate explicit reuse/continued-validity determination that cites:

- the prior Intervention Version;
- the prior accepted Completion Result and Completion Acceptance Versions;
- unchanged completion criteria and relevant target Configuration content;
- exact scope/boundary/control applicability to the new obligation;
- accountable reuse determination; and
- effective/recorded time.

This preserves operator usability—rework is not required merely for formalism—without allowing stale completion to cross a changed Decision boundary silently.

### 5.5 Tradeoff and reversibility

The three-type vocabulary adds one explicit relationship record and clearer UI state, but avoids the much greater cost of later disentangling mandatory-post-operation work from optional work. A future accepted version can add conditional/group metadata without rewriting v0.1 history because type and relationships are versioned.

## 6. Prerequisite aggregation analysis

### 6.1 Alternatives

**Alternative A — Conjunction/all-of.** Every current `REQUIRED_BEFORE_OPERATION` obligation for the exact Decision and target Configuration must be satisfied. This is deterministic, auditable, and consistent with the existing phrase “all interventions designated as prerequisites.”

**Alternative B — Native groups, sequence, and conditions.** Support one-of-N groups, ordered dependencies, and conditional prerequisites as activation expressions. This is expressive but requires a condition language, authoritative condition evaluation, group versioning, and conflict semantics not fixed by the current specifications.

**Alternative C — One case-level human declaration that prerequisites are done.** A human may declare the overall set complete despite individual statuses. This is usable in the short term but hides which obligation was waived, replaced, or accepted and weakens hard-oracle behavior.

### 6.2 Recommended v0.1 aggregation

Adopt Alternative A. For one exact Decision Version, target Configuration Version, effective time, and knowledge cutoff:

1. select the exact current Obligation Set Version;
2. preserve explicit absence or conflict in selecting that set;
3. select every current `REQUIRED_BEFORE_OPERATION` Obligation Version in the set;
4. derive the result of each obligation from its exact current Intervention, Completion Result, and Completion Acceptance;
5. return aggregate `SATISFIED` only when every required-before obligation is `SATISFIED`; and
6. retain all contributing results and diagnostics rather than returning only a Boolean.

There is no “most important completed Intervention” shortcut and no waiver by Case Owner, Intervention Owner, software administrator, or row order.

### 6.3 Necessary now versus deferred

Necessary for v0.1:

- stable Obligation and Obligation Set identity/version;
- all-of aggregation;
- explicit replacement/supersession;
- exact dependencies as traceable references;
- absence/conflict behavior;
- separate post-operation and optional treatment.

Deferred:

- one-of-N groups;
- condition-expression language;
- ordered execution as an activation rule;
- recurring prerequisites;
- dependency cycle policy;
- dynamic state-ranked obligations; and
- generic workflow orchestration.

An organization needing one-of-N in v0.1 should authorize one selected replacement Intervention/obligation through an explicit Decision amendment or a replacement relationship already within the Decision's permitted alternatives. The platform must not interpret several candidates as an implicit group.

## 7. Completion evidence vs acceptance

### 7.1 Four separate layers

The recommended model preserves four distinct facts:

1. **Work performed / implementation state.** The current Intervention status and implementation history show planned, in-progress, partial, blocked, completed, failed, cancelled, or superseded work.
2. **Completion Result and evidence.** A finalized Completion Result Version states criterion-by-criterion claimed results, exact evidence references, target Configuration Version, actor/source, limitations, effective/recorded time, and any residual condition.
3. **Accountable Completion Acceptance.** A separate immutable Acceptance Version states whether the cited Completion Result satisfies the exact Obligation under its Decision, Configuration, Boundary, and acceptance scope.
4. **Prerequisite-satisfaction result.** A deterministic result is derived from the current exact obligation, implementation, completion, acceptance, replacement, and conflict facts.

An Intervention may be `completed` at layer 1 while layer 3 remains absent or rejected. In that case the prerequisite is not satisfied.

### 7.2 Alternatives for inference

**Alternative A — `completed` implies accepted.** This is simple but permits the performer or project system to release operation without accountable evaluation of criteria.

**Alternative B — Evidence mechanically implies acceptance.** This can be appropriate for narrow machine-verifiable checks, but a generic rule would convert evidence availability into substantive judgment and cannot handle qualitative criteria or evidence limitations safely.

**Alternative C — Separate acceptance, with explicit governed mechanisms permitted.** Human or organizational accountability remains visible. Software may validate mechanical facts and may execute an explicitly governed acceptance mechanism, but the mechanism's authority, rule version, inputs, outcome, and scope are retained.

Adopt Alternative C.

### 7.3 Minimum Completion Result

A finalized Completion Result should include:

- Completion Result ID/Version;
- exact Intervention and Intervention Version;
- exact Obligation ID/Version;
- exact Decision and target Configuration Versions;
- every completion criterion and result (`MET`, `NOT_MET`, or `INDETERMINATE`), without a universal score;
- exact Evidence Record/Version references and provenance;
- performer/attestor actor;
- limitations, residual exposure, and fallback/remediation state;
- effective and recorded time; and
- correction/supersession relationships.

All criteria claimed as required must be `MET` before an acceptance can be eligible. Mechanical eligibility does not itself create acceptance.

### 7.4 Minimum Completion Acceptance

A Completion Acceptance should include:

- Acceptance ID/Version;
- exact Obligation, Intervention Version, and Completion Result Version;
- exact Decision, target Configuration, and material Boundary/condition references;
- outcome `ACCEPTED` or `REJECTED`;
- rationale and exceptions/limitations;
- accountable PAIM actor and exact applicable Role Assignment Version or governed organizational mechanism;
- delegation/supersession relationship where relied upon;
- effective and recorded time; and
- correction, withdrawal, or supersession history.

Absence of an eligible current Acceptance is `ACCEPTANCE NOT ESTABLISHED`; incompatible eligible Acceptances are `COMPLETION ACCEPTANCE CONFLICT — UNRESOLVED`. Neither is acceptance.

## 8. Completion accountability

### 8.1 Alternatives

**Alternative A — Intervention Owner accepts by default.** This is operationally convenient and may fit small organizations, but it collapses execution and acceptance and contradicts the existing warning against self-certified effectiveness.

**Alternative B — Decision Authority accepts every completion.** This creates strong continuity with the Decision but burdens Decision Authority with implementation verification and may confuse authorization of management judgment with inspection of technical or operational completion.

**Alternative C — Separate completion-acceptance function.** The exact Decision/obligation identifies the acceptance function. An existing Intervention Owner, Configuration Owner, Decision Authority, control owner, independent reviewer, or governed organizational mechanism may fulfill it only through a separately applicable assignment/mechanism.

Adopt Alternative C.

### 8.2 Applicable accountability

Introduce the substantive function name **Intervention Completion Acceptor**. It need not require a new person or universal organizational title. It is a separately resolved accountability relationship for the exact completion obligation.

For a Role-Assignment path, applicable typed targets for the obligation are:

- the exact Intervention;
- the exact Decision;
- the exact target Configuration; and
- that Configuration's owning Case.

The assignment remains scoped to its own typed target. A Case assignment applicable to the obligation does not become Intervention- or Configuration-scoped. Organization/business-unit authority may be used only through an explicitly established mapping or governed mechanism; PAIM must not invent organization identities from text.

Resolution at the Acceptance effective time returns exactly:

- one eligible accountable assignment or one explicitly governed mechanism;
- `COMPLETION ACCEPTANCE ACCOUNTABILITY NOT ESTABLISHED`; or
- `COMPLETION ACCEPTANCE ACCOUNTABILITY CONFLICT — UNRESOLVED`.

Broad/narrow overlap has no implicit winner. Recency, specificity, role hierarchy, directory group, technical permission, Intervention ownership, or Decision participation cannot resolve vacancy or conflict.

### 8.3 Self-acceptance

Three possible policies are realistic:

- always permit the Intervention Owner to accept;
- universally prohibit any same-person ownership and acceptance; or
- permit the same actor only when both functions are independently established and retained.

Recommend the third. It supports small organizations without making ownership self-authorizing. The record must cite:

1. the Intervention Owner assignment/mechanism for execution; and
2. the separate applicable Completion Acceptor assignment/mechanism for acceptance.

The overlap remains visible. A later organization-specific segregation policy may prohibit or require review without changing the base data model.

### 8.4 Delegation, vacancy, and conflict

- Delegated acceptance requires exact delegation-version linkage, scope/limits, effective period, and history.
- Expired, revoked, superseded, unrelated-scope, or incomplete delegation is ineligible.
- Vacancy blocks satisfaction; it does not convert completed work into accepted work.
- Competing applicable accountable assignments/mechanisms produce explicit conflict unless an exact supersession, delegation, or accepted versioned policy resolves them.
- Software permission allows an attempt to record acceptance but never supplies the substantive accountability.

## 9. Status/fallback/supersession semantics

### 9.1 Separate implementation and acceptance states

The Intervention implementation vocabulary should be fixed for v0.1 as:

- `PROPOSED`;
- `PLANNED`;
- `IN_PROGRESS`;
- `BLOCKED`;
- `PARTIALLY_COMPLETED`;
- `COMPLETED`;
- `FAILED`;
- `CANCELLED`; and
- `SUPERSEDED`.

Overdue is an attention/status event, not a completion outcome. Remediation and fallback are Intervention relationships/types, not euphemisms for success.

Completion Acceptance is separately:

- not established (derived absence);
- `ACCEPTED`;
- `REJECTED`; or
- conflict (derived incompatible current Acceptances).

### 9.2 Effect on a required-before-operation obligation

| Intervention/acceptance situation | Obligation effect |
|---|---|
| `COMPLETED` + eligible current `ACCEPTED` exact Completion Result | `SATISFIED` |
| `COMPLETED` + no eligible Acceptance | `NOT_ESTABLISHED` |
| `COMPLETED` + `REJECTED` Acceptance | `BLOCKED` |
| `PROPOSED`, `PLANNED`, `IN_PROGRESS`, or `PARTIALLY_COMPLETED` | `INCOMPLETE` |
| `BLOCKED`, `FAILED`, or `CANCELLED` without valid current replacement | `BLOCKED` |
| Incompatible current completion results, Acceptances, obligations, or replacements | `CONFLICT` |
| `SUPERSEDED` with one exact valid current replacement | predecessor excluded prospectively; replacement determines result |
| `SUPERSEDED` without an eligible replacement where the obligation remains current | `NOT_ESTABLISHED` or `BLOCKED`, according to the explicit obligation relationship; never satisfied |

### 9.3 Fallback and remediation

Fallback may satisfy a prerequisite only when all of the following hold:

- the fallback Intervention is explicitly related as the replacement/successor for the exact obligation;
- the existing Decision and Boundary already authorize the fallback as an allowed implementation path, or an authorized successor/amendment Decision establishes it;
- the replaced Intervention/obligation relationship states prospective effect and preserves history;
- the fallback has its own Completion Result and eligible Completion Acceptance; and
- the exact target Configuration and conditions align with the activation being attempted.

If fallback changes operating state, Boundary, target Configuration, or a substantive Decision condition, a successor/amendment Decision is mandatory. Calling an alternative “fallback” never avoids Decision authorization.

Remediation does not retroactively turn a failed result into success. It is a new or successor Intervention whose accepted completion may prospectively satisfy the obligation through an explicit relationship.

### 9.4 Required-after-operation and optional states

- An incomplete `REQUIRED_AFTER_OPERATION` Intervention does not block initial activation when the exact Decision explicitly permits post-operation completion.
- It remains visible as a mandatory commitment. Blocked, failed, cancelled, overdue, or materially partial status creates management attention and may require reassessment or an authorized operating response under existing contracts.
- An incomplete `OPTIONAL` Intervention never blocks activation and does not become mandatory through age or operator expectation.
- Neither category silently changes the Decision, Boundary, or operating permission.

## 10. Aggregate prerequisite-satisfaction model

### 10.1 Authoritative sources and derived result

Three alternatives exist:

1. store one mutable aggregate checkbox;
2. derive everything dynamically with no historical activation basis; or
3. store authoritative source records, derive the result deterministically, and retain the exact result snapshot used by an activation event.

Adopt the third.

Authoritative records are the Decision/Obligation Set, Obligation Versions, Intervention Versions/status events, Completion Results, Completion Acceptances, replacement/reuse relationships, and their accountability provenance. The aggregate is a deterministic query for an exact scope/effective time/knowledge cutoff. A cache or projection is non-authoritative and rebuildable.

The activation event must retain an immutable **Prerequisite Evaluation Basis** containing the exact versions and derived results it relied upon. This supports historical proof even when obligations, acceptors, evidence, or roles later change.

### 10.2 Result vocabulary

Per-obligation results:

- `SATISFIED`;
- `NOT_ESTABLISHED`;
- `INCOMPLETE`;
- `BLOCKED`; or
- `CONFLICT`.

Aggregate results:

- `SATISFIED` — every current required-before obligation is satisfied;
- `NOT_REQUIRED` — an exact eligible Obligation Set explicitly contains no required-before obligations;
- `NOT_ESTABLISHED` — the required Obligation Set or a required exact relationship/result/acceptance is absent;
- `INCOMPLETE` — the set is established and at least one required-before obligation remains in a non-terminal incomplete implementation state, with no conflict or blocking terminal result;
- `BLOCKED` — the set is established and at least one required-before obligation is rejected, blocked, failed, cancelled, or lacks a valid replacement after a terminal failure; or
- `CONFLICT` — the governing set or any required obligation/result/acceptance/replacement has incompatible current candidates.

`NOT_REQUIRED` is not inferred from missing records. It requires an explicit eligible Decision obligation declaration.

### 10.3 Deterministic evaluation order

The result is not a universal severity score. It is derived in stages:

1. exact Decision/Configuration/Obligation Set selection: conflict → `CONFLICT`; absence → `NOT_ESTABLISHED`;
2. empty explicit required-before set → `NOT_REQUIRED`;
3. per-obligation current relationship selection: any conflict → `CONFLICT`;
4. exact required source absence → `NOT_ESTABLISHED`;
5. any terminal unsatisfied required result → `BLOCKED`;
6. any non-terminal unsatisfied required result → `INCOMPLETE`; otherwise
7. all required-before obligations → `SATISFIED`.

The evaluation returns every contributing diagnostic, so the summary never hides simultaneous incomplete or blocked items.

## 11. Target-operation activation guard

### 11.1 Activation alternatives

**Alternative A — Automatic activation when the aggregate becomes satisfied.** This is operationally efficient but treats a derived technical event as authority to begin operation and risks activation from late data ingestion or self-certified evidence.

**Alternative B — Require a newly authorized successor Decision for every activation.** This is strongly controlled but duplicates the existing Decision when that Decision already authorizes the target subject to prerequisites.

**Alternative C — Explicit Activation Authorization under the exact existing Decision.** The activation is a separate authoritative event. It is authorized either by the applicable Decision Authority at activation time or by an exact governed activation mechanism explicitly pre-authorized in the Decision Authorization Basis. The system may execute the pre-authorized mechanism mechanically only after all guards pass.

Adopt Alternative C.

### 11.2 Minimum guard

The exact target Configuration may enter `OPERATING_OBSERVING` only when all of the following are true for the activation effective time and knowledge cutoff:

1. exactly one eligible authorized Decision governs the target activation context; absence or Decision conflict blocks;
2. the Decision binds the exact target Configuration Version and finalized Boundary Snapshot;
3. the exact current Obligation Set for that Decision/Configuration is established without conflict;
4. aggregate required-before-operation result is `SATISFIED` or explicit `NOT_REQUIRED`;
5. every satisfied obligation cites an exact current Completion Result and eligible Completion Acceptance, with accountability valid at the Acceptance effective time;
6. no current Acceptance, obligation, replacement, Decision, target Configuration, or Boundary conflict exists;
7. the target Configuration demonstrably aligns with the Decision, Boundary clauses, required controls, prohibited activities, and accepted completion basis;
8. no effective successor/amendment Decision has superseded or changed the target prerequisites;
9. required-after-operation obligations are identified with their Decision-permitted post-operation timing/conditions but need not yet be complete;
10. optional obligations need not be complete;
11. an explicit Activation Authorization is valid for the exact Decision, target Configuration, operating state, Boundary, effective time, and Prerequisite Evaluation Basis; and
12. the immutable lifecycle Transition Event records the actor/mechanism, guard results, exact versions, rationale, effective time, and recorded time.

### 11.3 Authority and role timing

Completion acceptance authority must have been valid for the exact obligation at the Acceptance effective time. A later routine role change does not rewrite a historical Acceptance, just as later authority change does not rewrite a historical Decision. However, a withdrawn, corrected, or superseded Acceptance is not a current eligible basis for future activation.

Activation authority must be valid at activation effective time. It is satisfied by either:

- the applicable Decision Authority through an explicit activation event; or
- an organizational activation mechanism whose rule, scope, criteria, and authority were explicitly included in the exact Decision Authorization Basis.

A Case Owner or workflow mechanism may record the lifecycle transition after guards and activation authority are established. Case ownership, Intervention ownership, a completed checklist, system-administrator rights, or a technical principal alone cannot authorize operation.

### 11.4 Prior operation

Where prior operation continues during target Intervention, the activation guard applies only to the target Configuration. Prior operation remains governed by its own exact current Decision/Boundary and any Interim Operating Disposition. Completion of target prerequisites does not broaden or rewrite the prior permission.

## 12. Decision successor/amendment behavior

### 12.1 Alternatives

**Alternative A — Silent carry-forward.** Any prior accepted Intervention remains accepted for a successor Decision unless manually revoked. This is convenient but unsafe when scope, Boundary, criteria, or target Configuration changed.

**Alternative B — Never reuse.** Every successor Decision requires new work and acceptance. This is traceable but imposes needless duplication where the same operational fact remains valid.

**Alternative C — Explicit continued-validity determination.** The successor Decision creates its own Obligation Set and each reused completion is linked through an accountable, exact continued-validity determination.

Adopt Alternative C.

### 12.2 Required behavior

- Every substantive Decision amendment is a new authorized successor Decision Version and has its own exact Obligation Set Version.
- Prior obligations, Interventions, Completion Results, and Acceptances remain reconstructable for the prior Decision's effective period.
- Nothing carries forward merely because IDs, titles, owners, or target labels look similar.
- A successor may reuse a prior accepted completion only through an exact continued-validity determination that proves unchanged relevant Configuration content, Boundary/condition coverage, criteria, evidence applicability, and acceptance scope.
- The successor Decision must explicitly reference the reuse determination or an exact obligation relationship that does so.
- Reuse accountability follows the Completion Acceptor model; the successor Decision Authority remains responsible for authorizing the successor requirement package and any substantive operational change.
- If the target Configuration Version changes, prior completion is provenance only unless the continued-validity determination explicitly covers the changed version.
- If a successor removes an obligation, the predecessor remains historical; removal applies prospectively and requires the successor Decision basis.
- If a prior Intervention is technically valid but no eligible reuse determination exists, the successor obligation is `NOT_ESTABLISHED`, not satisfied.

### 12.3 Non-substantive Intervention changes

Scheduling, owner, or implementation-method changes may remain within an existing Decision only where the governing Integrity contract permits and where they do not weaken completion criteria, required controls, Boundary, target Configuration, or substantive Decision conditions. The rationale and exact successor Intervention Version remain recorded. A convenience label cannot make a substantive change non-substantive.

## 13. Learning boundary and deferred questions

IRR-010 does not authorize opportunistic redesign of Learning. The following Learning semantics are already fixed and must remain untouched:

- Learning is distinct from Intervention, generic monitoring, and the Decision.
- A Learning Item binds exact Case, Decision Version, Configuration Version, uncertainty/question, owner, method, and result/evidence linkage.
- Decision-Limiting Uncertainty should have an explicit evidence, Authority Gap, or Learning path where management intends future reconsideration.
- Learning-generated material becomes Evidence under the Evidence/Authority specification.
- Learning completion may be favorable, unfavorable, narrower, inconclusive, or reveal new uncertainty/authority; completion is not automatically success.
- Learning evidence or result never silently changes a Decision, operating state, Boundary, or uncertainty classification.
- Learning and Intervention may coexist and retain separate identities/statuses.
- Learning and Intervention history remains immutable and point-in-time reconstructable.

Explicitly deferred:

- **IRR-009:** whether Observation is a separate authoritative record, monitoring automation, and Observation-to-Evidence/Trigger linkage;
- **IRR-011:** Trigger/Reassessment cardinality, merge, deduplication, concurrency, and closure coordination;
- **IRR-012:** Management Register population, aggregation, and shared-dependency identity;
- **IRR-014:** stronger/broader operating-state traits, relations, ranking, and state-derived automation;
- learning experiment templates, quantitative experiment design, cadence, and project-management integration;
- generic dependency/notification/escalation workflow; and
- Reassessment and Interim Operating Disposition design beyond invoking already-governed attention/trigger paths.

Increment 5 implementation may later implement only the already-fixed bounded Learning record/history/evidence-link behavior authorized by its own issue. This IRR-010 decision package does not open that work automatically.

## 14. Hard-oracle scenarios

| # | Scenario | Required v0.1 result and exact reason |
|---:|---|---|
| 1 | One required-before-operation Intervention; Completion Result/evidence present; no Completion Acceptance | Obligation `NOT_ESTABLISHED`; aggregate not satisfied; target activation blocked. Evidence cannot infer acceptance. |
| 2 | Same Intervention with one valid applicable accountable `ACCEPTED` Completion Acceptance | Obligation `SATISFIED`; aggregate `SATISFIED` if no other required-before items; activation still requires all other guard facts and Activation Authorization. |
| 3 | Two required-before-operation Interventions; one accepted complete, one incomplete | Second obligation `INCOMPLETE`; aggregate `INCOMPLETE`; target activation blocked. No partial aggregate release. |
| 4 | Two required Interventions with incompatible current completion Acceptances | At least the affected obligation and aggregate are `CONFLICT`; target activation blocked. No winner by recency, scope specificity, hierarchy, or permission. |
| 5 | Intervention complete but accepted by an actor whose assignment is only for unrelated Configuration B | Acceptance ineligible; accountability/acceptance `NOT_ESTABLISHED`; obligation not satisfied; activation blocked. |
| 6 | Intervention Owner self-accepts without separately established acceptance authority | Blocked as `NOT_ESTABLISHED`. If the same actor has a separate applicable Completion Acceptor assignment/mechanism, both roles and exact provenance are retained and self-acceptance may be eligible. |
| 7 | Required-after-operation Intervention incomplete; Decision explicitly permits post-operation completion | Does not enter required-before aggregate and does not block initial activation. It remains a mandatory visible commitment; later blocked/failed/overdue state creates attention without silently changing the Decision. |
| 8 | Optional Intervention incomplete | Does not block activation and does not become required by age, owner preference, or software configuration. |
| 9 | Required-before Intervention is partial, failed, or cancelled | `PARTIALLY_COMPLETED` → `INCOMPLETE`; `FAILED`/`CANCELLED` without valid replacement → `BLOCKED`; none satisfies the prerequisite. |
| 10 | Fallback Intervention is accepted under an explicit replacement/supersession relationship | If within the existing Decision/Boundary and exactly linked to the obligation, the accepted fallback successor determines the prospective obligation result; predecessor history remains. If it changes substantive conditions, activation is blocked until an authorized successor Decision exists. |
| 11 | Prior Decision's Intervention was accepted; successor Decision changes the requirement | No carry-forward. Successor obligation is `NOT_ESTABLISHED` until new completion/acceptance or an exact eligible continued-validity determination is recorded. Prior Decision reconstruction remains unchanged. |
| 12 | A software-permitted technical principal records completion or attempts activation without substantive accountability/authority | The record attempt may be attributable, but it cannot create eligible Completion Acceptance or Activation Authorization. Prerequisite remains unsatisfied or activation unauthorized; operation is blocked. |

Additional boundary oracles required by the package:

- an explicit Obligation Set with zero required-before items yields `NOT_REQUIRED`; missing obligation data yields `NOT_ESTABLISHED`;
- one valid replacement excludes its superseded predecessor prospectively; two incompatible replacements yield `CONFLICT`;
- later expiry of the acceptor's Role Assignment does not rewrite a historically valid Acceptance, but a withdrawn/superseded Acceptance cannot support a later activation;
- an accepted completion for the wrong Decision Version or target Configuration Version is ineligible;
- Completion Acceptance does not itself authorize activation; and
- activation under a pre-authorized mechanism retains the exact mechanism/rule version and Prerequisite Evaluation Basis.

## 15. Recommended v0.1 decision package

The recommended package is:

1. **Requirement types:** exactly `REQUIRED_BEFORE_OPERATION`, `REQUIRED_AFTER_OPERATION`, and `OPTIONAL` for v0.1.
2. **Requirement identity:** authoritative versioned Decision-to-Intervention Obligation, bound to exact Decision and target Configuration Versions.
3. **Aggregation:** conjunction of every current required-before obligation; no implicit groups, ordering, conditional expressions, or discretionary override.
4. **Completion separation:** implementation status, Completion Result/evidence, Completion Acceptance, and prerequisite result are separate.
5. **No inferred acceptance:** software may validate eligibility but cannot infer substantive acceptance; explicitly governed mechanisms are allowed only with retained authority and rule provenance.
6. **Acceptance accountability:** separate Intervention Completion Acceptor function resolved for exact Intervention/Decision/Configuration/owning-Case targets as one assignment/mechanism, vacancy, or conflict.
7. **Self-acceptance:** permitted only when the same actor separately holds eligible execution and acceptance relationships; overlap is retained and organization policy may be stricter.
8. **Failure semantics:** partial, blocked, failed, cancelled, and rejected states never silently satisfy; fallback/remediation requires explicit replacement and accepted completion.
9. **Aggregate model:** authoritative source records plus deterministic derived result; activation records an immutable exact Prerequisite Evaluation Basis.
10. **Activation:** explicit Activation Authorization by applicable Decision Authority or an exact mechanism pre-authorized in the Decision Authorization Basis; satisfied prerequisites alone do not activate operation.
11. **Successors:** every successor Decision has its own obligation set; reuse requires an accountable exact continued-validity determination.
12. **History:** later role, evidence, Intervention, acceptance, or Decision changes operate prospectively and never rewrite prior activation/Decision reconstruction.

This package is internally coherent: it prevents self-certified release without requiring a universal segregation rule, supports small organizations through separate role assignments held by one actor, gives operators a deterministic activation answer, and avoids encoding a generic workflow engine.

## 16. Remaining deferred questions

The following remain deliberately open after IRR-010:

- one-of-N and grouped prerequisite sets;
- formal ordered/conditional dependency language;
- recurring or continuously revalidated activation prerequisites;
- organization-specific acceptance quorum/signature technology;
- quantitative completion scoring or universal metrics;
- universal segregation-of-duties policy;
- project-management, notification, deadline, escalation, and external-provider task integration;
- whether Interventions may span multiple Cases as one authoritative obligation;
- automatic Observation/monitoring semantics (IRR-009);
- Trigger/Reassessment concurrency and merge behavior (IRR-011);
- Management Register aggregation (IRR-012);
- operating-state ranking/stronger-state inference (IRR-014);
- full Reassessment, Interim Operating Disposition, Observation persistence, and Management Register implementation; and
- generic workflow or policy-expression engines.

If a concrete v0.1 case requires one of these unresolved semantics, the system must expose the gap and block the dependent automatic behavior rather than invent a permissive default.

## 17. Proposed specification-hardening impact

No governing specification is changed by this artifact. If the recommended package is accepted, a separate bounded hardening issue should make coordinated normative changes as follows.

### 17.1 Primary owners

**`PAIM_INTERVENTION_AND_LEARNING_SPEC_v0.1.md`**

- define Obligation/Obligation Set identity and the three requirement types;
- fix Intervention implementation statuses;
- define Completion Result and Completion Acceptance identity/content/history;
- define replacement, fallback, remediation, and continued-validity behavior;
- define per-obligation and aggregate results; and
- preserve the Learning boundary and named deferrals.

**`PAIM_CASE_LIFECYCLE_SPEC_v0.1.md`**

- harden `DECIDED` → `INTERVENTION_IN_PROGRESS`/`OPERATING_OBSERVING` routing;
- replace “required intervention incomplete” with the exact aggregate and activation guard;
- require Prerequisite Evaluation Basis and Activation Authorization in the Transition Event; and
- preserve prior-operation coexistence under its own exact Decision/Boundary.

### 17.2 Conforming owners

**`PAIM_INTEGRATION_AND_DECISION_SPEC_v0.1.md`**

- require the authorized Decision to declare the exact Obligation Set, post-operation commitments, and any pre-authorized activation mechanism;
- define successor-Decision obligation/reuse treatment; and
- distinguish Decision authorization from completion acceptance and activation authorization.

**`PAIM_ROLES_AND_ACCOUNTABILITY_SPEC_v0.1.md`**

- define the Intervention Completion Acceptor function;
- add exact applicable target/accountability resolution, delegation, vacancy, conflict, and self-acceptance rules; and
- add negative integrity/test cases for unrelated scope and software permission.

### 17.3 Cross-cutting conformance

**`PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`** should be amended only where needed to state cross-cutting identity/history, exact activation-basis reconstruction, current-selection, semantic-transaction, and lifecycle invariants. It should not duplicate the substantive Intervention definitions.

The Behavioral Validation Strategy should later add the 12 hard-oracle scenarios and exact expected results. The implementation sequence/gate artifact should record IRR-010 closure only after the governing hardening is accepted and independently re-reviewed.

No code, migration, test, runtime, dependency, Reassessment, Observation, Register, or operating-state-ranking change should accompany the specification-hardening issue.

## 18. Final recommendation

PAIM design authority should accept the recommended v0.1 package in §15 and authorize a separate, coordinated specification-hardening issue before any Increment 5 implementation.

The central decision is:

> A target Configuration may operate only under an exact authorized Decision and explicit Activation Authorization after every exact `REQUIRED_BEFORE_OPERATION` obligation is supported by a finalized Completion Result and one eligible accountable Completion Acceptance. Work status, evidence presence, Intervention ownership, technical permission, or one completed item among several never supplies that result by itself.

This resolves the core IRR-010 ambiguity while preserving fixed Increments 1–4 semantics, human accountability, deterministic guard behavior, operator clarity, historical reconstruction, and bounded future extensibility. IRR-009, IRR-011, IRR-012, and IRR-014 remain explicitly deferred.
