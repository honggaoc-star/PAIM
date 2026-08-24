# PAIM System Behavioral Validation Strategy v0.1

## Status

Implementation-independent validation strategy for the observable behavior of the Practical AI Management (PAIM) system.

This strategy derives from:

- `PAIM_SYSTEM_ARCHITECTURE_v0.1.md`
- `PAIM_SYSTEM_COMPLETION_BASELINE_GAP_MAP_v0.1.md`
- `PAIM_CASE_LIFECYCLE_SPEC_v0.1.md`
- `PAIM_MANAGED_CONFIGURATION_SPEC_v0.1.md`
- `PAIM_EVIDENCE_AND_AUTHORITY_SPEC_v0.1.md`
- `PAIM_VALUE_RISK_INTERFACE_SPEC_v0.1.md`
- `PAIM_INTEGRATION_AND_DECISION_SPEC_v0.1.md`
- `PAIM_INTERVENTION_AND_LEARNING_SPEC_v0.1.md`
- `PAIM_REASSESSMENT_SPEC_v0.1.md`
- `PAIM_MANAGEMENT_REGISTER_SPEC_v0.1.md`
- `PAIM_ROLES_AND_ACCOUNTABILITY_SPEC_v0.1.md`
- `PAIM_RESPONSIBILITY_AND_CASE_WORK_SPEC_v0.1.md`
- Phase II validation findings from IET 001–004.

It defines how PAIM should be tested as an integrated management system through controlled inputs, observable outputs, state transitions, invariants, and human-facing behavior.

It does not prescribe a specific software test framework or implementation technology.

**Normative cross-cutting test contract:** `../specifications/PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md` defines the hard integrity behavior for authoritative record history/currentness, Integrated Operating Boundary Snapshots, case transitions, Decision Authorization Basis, and Interim Operating Disposition. Behavioral tests must use those rules as oracles without replacing the human judgments reserved there.

Gate 1 adds prospective reusable hard-oracle categories for semantic-contract identity, exact
context sets, selector outcomes, non-authoritative read composition, dual-time reconstruction,
semantic transactions, migration/compatibility, and access/non-disclosure. Those oracles apply to a
later record family only when its separately accepted Gate 2–6 contract adopts them. They do not
change current v0.1 expected behavior or define later substantive payloads.

The accelerated Gate-2/4 contract now adopts that machinery for prospective Case Practical Role
Relationship, Responsibility, Responsibility Assignment Basis, and durable Work families. §9B
defines their normative oracles. This adoption changes no current v0.1 implementation expectation
until a separately accepted implementation/migration contract declares an exact consumer cutover.

**Bounded v0.1 validation scope:** the human-accepted
`../../engineering/PAIM_V0_1_RELEASE_SCOPE_DECISION_IRR_009_IRR_014_v0.1.md` establishes that
IRR-009 and IRR-014 each remain `OPEN — SEMANTICS UNDESIGNED` while each has bounded-v0.1
product-gate status `CLOSED BY DESIGN — OUTSIDE V0.1 CLAIM`. Consequently, v0.1 validation must
directly prove the fail-closed absence of first-class Observation/automatic telemetry conversion
and operating-state relation/ranking/escalation. Exact manual/external Trigger provenance and
exact-state, exact-scope restrictive intersection/suspension remain in scope. Sections retaining
Observation-family or state-relation test ideas mark them as post-v0.1 extension scenarios; they are
not Increment 9 expectations.

## 1. Purpose

The central validation question is:

> **Does the integrated PAIM system behave appropriately when material inputs, evidence, authority, controls, configurations, uncertainty, and management states change?**

Formal human testing is intentionally deferred until the integrated practitioner-facing platform is sufficiently complete.

The testing strategy therefore distinguishes:

1. component verification;
2. system behavioral testing;
3. interface/usability testing;
4. human practitioner validation;
5. longitudinal/field validation.

## 2. Validation Philosophy

PAIM should be tested primarily through its observable behavior.

Conceptually:

```text
Controlled Inputs / Scenario
          |
          v
      PAIM System
          |
          v
Observable Outputs / State Changes /
Questions / Boundaries / Decisions /
Interventions / Learning / Reassessment
```

Human testers should not need to understand PAIM's internal development history or navigate its Markdown specification repository.

The development artifacts define expected system behavior; they are not the human-test interface.

## 3. Black-Box Orientation

The eventual platform should permit systematic probing of the relationship between:

- case inputs;
- configuration;
- evidence;
- authority;
- Value/Risk inputs;
- controls;
- uncertainty;
- operating-state proposals;
- observed events;

and:

- system readiness;
- boundary changes;
- required questions;
- management attention;
- interventions;
- learning;
- reassessment;
- decision status.

The objective is not to infer one hidden numerical decision rule.

The objective is to determine whether the system responds coherently, traceably, and conservatively where evidence is insufficient.

## 4. Test Layers

### 4.1 Specification-level verification

Question:

> Does each system component conform to its specification?

Examples:

- configuration versioning;
- input freeze behavior;
- decision immutability;
- authority-gap persistence;
- reassessment linkage.

### 4.2 Integrated behavioral testing

Question:

> When components interact, does PAIM preserve the intended management behavior?

Examples:

- control changes trigger evidence applicability review;
- Decision-Limiting Uncertainty may block an exact proposed operating state; v0.1 does not infer a
  stronger-state relation;
- new evidence produces successor inputs rather than rewriting prior ones.

### 4.3 Practitioner-interface testing

Question:

> Does the platform expose the right information and judgment points without requiring artifact reconstruction?

### 4.4 Human practitioner validation

Question:

> Can a human practitioner use the integrated system correctly, efficiently, and meaningfully?

### 4.5 Longitudinal validation

Question:

> Does PAIM continue to preserve traceability and decision quality over time as configurations, evidence, authority, and decisions change?

## 5. Test Object

The primary test object is not an AI model.

It is the **PAIM management system** operating on bounded AI-management cases.

A test case should therefore include some combination of:

- management question;
- Managed Configuration;
- evidence;
- authority;
- Value Input;
- Risk Input;
- controls;
- uncertainty;
- alternatives;
- current decision;
- intervention;
- learning;
- reassessment trigger.

## 6. Scenario Family Design

Tests should be organized into scenario families that isolate one or a few variables.

A strong scenario family uses a common base case and modifies controlled dimensions.

Example:

```text
Base case
  |
  +-- Variant A: Risk increases
  +-- Variant B: Value decreases
  +-- Variant C: required control removed
  +-- Variant D: authority gap resolved
  +-- Variant E: exact different operating state proposed (no rank inferred)
```

This makes the input/output relationship easier to study.

## 7. Baseline Scenario

Each family should begin with a stable baseline.

The baseline should identify:

- exact configuration;
- evidence;
- authority state;
- Value/Risk inputs;
- current boundary;
- operating state;
- decision;
- active controls;
- uncertainty;
- intervention/learning state.

The baseline output becomes the comparison point for controlled variants.

## 8. Controlled Variable Changes

The test harness should eventually support deliberate variation of:

### Value

- stronger/weaker realized value;
- expected vs. realized value;
- cost change;
- control burden;
- capacity effect;
- lost substitution.

### Risk

- new adverse pathway;
- stronger/weaker control evidence;
- higher residual exposure;
- new error class;
- reduced review effectiveness.

### Controls

- remove control;
- weaken control;
- add control;
- change threshold;
- exceed control capacity.

### Authority

- introduce unresolved authority;
- resolve authority;
- add prohibition;
- add mandatory control;
- change decision authority.

### Configuration

- change model/provider;
- change scope;
- increase autonomy;
- add data class;
- change user population;
- change operating conditions.

### Uncertainty

- increase uncertainty;
- resolve uncertainty;
- convert Accepted to Decision-Limiting;
- complete learning.

### Operating state

- exact state identity A;
- exact state identity B;
- exact proposed state change;
- exact structured scope restriction; and
- indeterminate combined restrictive effect.

Labels such as experiment, continuation, scale, institutionalization, or broader deployment may be
fixture data, but their names and ordering carry no v0.1 semantic relation.

## 9. Expected Behavioral Invariants

Certain PAIM behaviors should remain invariant across scenarios.

### 9.1 Historical immutability

Prior frozen inputs and authorized decisions remain unchanged after later evidence or decisions.

### 9.2 Configuration binding

Evidence, Value/Risk inputs, and decisions remain linked to the configuration/version they govern.

### 9.3 Analytical independence

Value and Risk conclusions are not rewritten during integration.

### 9.4 Authority explicitness

Missing authority remains explicit and never becomes implied permission.

### 9.5 Decision traceability

Every current decision remains linked to evidence, inputs, rationale, authority, boundary, and uncertainty.

### 9.6 Reassessment linkage

Material change produces reassessment rather than silent continuation.

### 9.7 No universal-score substitution

A high-level indicator cannot replace the underlying management reasoning.

### 9.8 Deterministic currentness

Authoritative current records are selected only for explicit scope and time. Absence and incompatible overlap remain explicit; the system never selects silently by recency or convenience.

### 9.9 Boundary integrity

Every authorized Decision binds one immutable Integrated Operating Boundary Snapshot. Mechanical checks apply only to structured/testable clauses; narrative clauses require accountable determination and are never silently treated as satisfied.

### 9.10 Authorization integrity

Every authorized Decision binds a valid Decision Authorization Basis covering the exact Decision scope and effective time. `AUTHORITY UNRESOLVED` and `DECISION AUTHORITY UNRESOLVED` never imply permission.

### 9.11 Transition integrity

Every case lifecycle transition follows the canonical source-to-target table, preserves its Transition Event, and satisfies mandatory guards.

### 9.12 Reassessment outcome integrity

Opening reassessment does not silently alter operation. Every completed Reassessment produces either an explicit unchanged-Decision confirmation or an authorized successor/amendment Decision; interim change is time-bounded and authorized.

## 9A. Gate-1 common-integrity hard-oracle families

### 9A.1 Oracle setup discipline

Every Gate-1 oracle must name:

- source Semantic Contract ID/Version and any prospective/adapted consumer contract;
- exact Record IDs, Version IDs, typed context members, effective time, known-at cutoff, Actor,
  access context, and idempotency identity relevant to the scenario;
- authoritative state and audit digest before the action;
- expected visible result and expected hidden/non-disclosed result; and
- exact post-state, including zero mutation on failure.

Fixture convenience, row order, current software version, record recency, or display order cannot be
part of a substantive oracle unless the owning contract explicitly gives it meaning.

### 9A.2 Semantic-era preservation and no reinterpretation

| Scenario | Hard oracle |
|---|---|
| Read one legacy Fitness Version through its original contract after a prospective adequacy contract exists | The fact renders as legacy Fitness with its original outcome/basis; no adequacy fact is created or implied. |
| Interpret a legacy Version that predates an explicit semantic-contract field | Exact family/revision mapping identifies the original contract without mutating the Version or supplying a prospective envelope/payload. |
| Read legacy Acceptance/Selection, Role Assignment, or Case lifecycle through a named adapter | Output labels exact legacy source Version and adapter contract; stored fact and historical meaning remain unchanged. |
| Correct or create an explicit successor across semantic eras where the owning contract permits continuity | Both Versions and exact typed cross-era relationship remain; each Version uses its own contract; the successor does not rewrite its predecessor. |
| Two incompatible cross-era facts are otherwise eligible and the owning contract defines no precedence | Selector returns explicit conflict; neither newer era nor recorded time wins. |
| Prospective guard fails while a legacy path could have succeeded | Prospective operation fails with zero mutation; no legacy fallback or synthesized prospective fact occurs. |
| Recover/restore data using newer software | Every historical Version retains the semantic contract and interpretation it had before recovery. |

### 9A.3 Authoritative-envelope hard oracles

- Two different finalized payloads cannot share one Version identity or canonical checksum where a
  checksum is contractually required.
- Missing a family-required envelope element fails before authoritative mutation; omission of a
  family-declared inapplicable element does not fabricate a gap.
- Presence of Actor, source, context, or eligibility metadata does not establish accountability,
  authority, Applicability, or eligibility without the owning substantive rule.
- Status/correction/supersession relationships retain exact source/target Versions, contract
  identities, effective/recorded time, and attribution.

### 9A.4 Exact context-set canonicalization and identity

For the same unordered typed membership submitted in different input/storage orders:

> canonical representation, checksum, and semantic context identity are identical.

For an owning contract that declares one ordered member role, changing the valid ordinal changes
the canonical representation. Ordering other unordered roles has no effect.

Additional hard oracles:

- exact duplicate membership is rejected with zero mutation;
- two Versions of one Record in a single-role context fail or return explicit conflict unless the
  owning contract expressly permits distinct roles;
- unknown member role, contradictory role, wrong Case/Configuration where the owning contract
  requires coherence, or missing exact Version fails closed;
- an inaccessible member cannot be used to commit and does not leak identity, type, count, role, or
  conflict contribution;
- context membership alone creates no Applicability, responsibility, authority, adequacy,
  materiality, causality, comparability, priority, or Decision; and
- an independently identified Context Set cannot be created merely for implementation convenience
  where the owning contract requires only an embedded immutable component.

### 9A.5 Deterministic selector outcomes

For one fixed scope, effective time, known-at cutoff, access context, and family contract:

| Eligible state | Required result |
|---|---|
| exactly one eligible fact | that exact Version |
| zero eligible facts | explicit family-specific `NOT ESTABLISHED`/absence |
| two incompatible eligible facts with no authoritative relation | explicit `CONFLICT — UNRESOLVED` |
| compatible plurality expressly allowed in distinguishable scopes | deterministic exact set defined by the owning contract |

Permuting row/input/display order must not change any result. Changing only recency, semantic era,
specificity, breadth, role hierarchy, strongest-state label, software permission, or identifier must
not create a winner. Explicit valid supersession/delegation/coordination changes the result only as
the owning contract specifies. Stale, withdrawn, cancelled, expired, corrected, and superseded
treatment must each have a family-owned oracle before implementation.

### 9A.6 Access-filtered non-authoritative read composition

Construct a source population containing visible and hidden facts, including a hidden conflict.

Hard oracles:

- access filtering occurs before selection, grouping, counting, blocker/conflict labelling, and
  participant/work/current-position composition;
- the restricted view exposes no hidden ID, fact, count, scope, timing, type, plurality, or changed
  shape while avoiding a false assertion of substantive absence;
- the fully authorized view retains the exact conflict and source Versions;
- identical visible sources, query, access context, known-at/effective-at basis, and composition-rule
  Version produce identical semantic output and source manifest;
- cache/export/notification/label/queue order does not mutate source truth or authorize a command;
- changing only presentation order or wording changes no authoritative digest; and
- a downstream command using a stale presentation reconstructs authoritative context, fails closed,
  and creates no mutation.
- an Actor lacking access to one command-required hidden source receives a non-disclosing failure;
  the command neither ignores the source nor reveals which source exists.

### 9A.7 Dual-time and Decision-bound reconstruction

Use a Decision bound to exact source Versions, then record a correction effective before the
Decision but learned afterward, a later quantitative observation, and later
Responsibility/Work/Review facts.

Required results:

- exact Decision-bound view returns the exact Versions originally relied upon;
- effective-at viewed with current knowledge may show the later correction, clearly labelled later
  knowledge;
- known-at the Decision cutoff excludes every later-recorded fact;
- later observation does not rewrite the earlier estimate/target or infer Decision error;
- later responsibility/work/review does not alter earlier accountability state;
- every Version is interpreted under its own Semantic Contract ID/Version; and
- no view claims knowledge of an unrecorded external fact.

### 9A.8 Semantic transaction atomicity and replay

For a semantic transaction intended to create two separate authoritative facts and their audit
links:

1. With all exact guards valid, both facts and complete audit linkage commit once; each retains its
   own identity and semantics.
2. If the second write, audit write, access check, accountability/authority check, or any stale or
   conflict guard fails, neither fact commits and the pre-state digest is unchanged.
3. Exact replay with the same key, Actor, contract, context checksum, and intent returns the original
   outcome without duplicate facts/events.
4. Reusing the key with changed Actor, contract, context, or intent fails with zero mutation.
5. Concurrent incompatible attempts produce one complete winner plus explicit stale/conflict failure,
   or no winner; never partial interleaving.

Transaction audit must reconstruct the natural action and grouped outputs without treating the two
facts as one merged judgment. These oracles define atomic behavior only; they do not define a
future `Complete Value review` or any other Gate 2–6 command.

### 9A.9 Legacy/new coexistence, upgrade, and recovery

- An empty store and every supported prior revision upgrade to the prospective-capable integrity
  revision without changing legacy semantic digests.
- No upgrade creates Responsibility, continuity, Work, Review Timing, adequacy/reliance, or typed
  quantitative claims from legacy records/UI state.
- Adapter output is deterministic, source-labelled, access-safe, and non-authoritative unless a
  later owning contract explicitly says otherwise.
- Backup/restore and rollback preserve IDs, Versions, checksums, relationships, audit, semantic
  contracts, and historical reconstruction.
- Unsupported adapter/contract pair, ambiguous cross-era state, or missing migration rule fails
  explicitly with zero domain mutation.

### 9A.10 Product-to-integrity negative oracles

The UI/read model must not expose semantic-contract keys, canonicalization, selector algorithms,
transaction choreography, or raw context IDs in ordinary work merely because the integrity layer
requires them. Hiding machinery must not hide genuine absence, conflict, limitations, consequence,
or attribution.

No Gate-1 mechanism may be used as an oracle for:

- a Responsibility kind or assignee;
- Case continuity outcome;
- Case Work state/result;
- planned/required Review meaning;
- assessment adequacy, reliance, or readiness;
- quantitative Value/Risk payload meaning;
- management priority, authority, or Decision.

Any test expecting one of those outcomes belongs to Gate 2–6 and remains invalid until its owning
specification is accepted.

## 9B. Accelerated Gate-2/4 Responsibility and Case Work hard oracles

These are implementation-independent oracles for the contract in
`PAIM_RESPONSIBILITY_AND_CASE_WORK_SPEC_v0.1.md`. They authorize no implementation or fixture
mutation.

### 9B.1 Responsibility identity, context, and resolution

1. Canonically identical obligation signatures with differently ordered context inputs resolve to
   the same exact signature; a changed Evidence, target, Configuration, purpose/use, scope, Case,
   semantic-contract Version, or other required member resolves a different obligation.
2. One eligible Responsibility Version returns that Version. Zero returns `RESPONSIBILITY NOT
   ESTABLISHED`. Two incompatible co-current Versions return `RESPONSIBILITY CONFLICT —
   UNRESOLVED` with no winner by specificity, breadth, recency, practical role, hierarchy, access,
   software permission, workload, or row order.
3. One Actor may hold Case coordination, Value, Risk, and information-review Responsibilities;
   every Responsibility and Value/Risk/result Version remains independent and exactly attributable.
4. Case Coordinator, Assessor, Reviewer, participant, author, owner, administrator, and visible user
   labels create no Responsibility or substantive authority.

### 9B.2 Assignment-basis and history oracles

1. Establishment succeeds only with an exact effective in-scope Responsibility Assignment Basis.
   Practical role or software permission alone fails with zero mutation.
2. Delegation preserves the full exact chain and does not broaden scope. Missing, expired, revoked,
   unrelated, incomplete, or conflicting links fail closed.
3. Reassignment, withdrawal, and supersession append exact history; expiry without successor creates
   vacancy. Effective-at/known-at reads preserve the prior historically valid holder.
4. A multi-fact assignment transaction commits Responsibility, relationships, audit, and intended
   events all or none. Exact replay returns the original identities; a changed context or intended
   fact is not replay.

### 9B.3 Legacy and semantic-era oracles

1. Every legacy Role Assignment Version and historically valid result remains byte-/field-exact and
   is interpreted under its original contract.
2. Before a consumer's declared cutover, its current legacy selector controls. After cutover, new
   writes require Responsibility; a prospective failure never retries through legacy behavior.
3. No adapter synthesizes Responsibility or missing context. Cross-era incompatible eligible
   candidates produce conflict absent an explicit valid displacement/supersession relation.
4. `Applicability Owner` is accepted only by the named bounded pre-cutover adapter; no prospective
   practical role or obligation kind with that name exists.

### 9B.4 Derived-versus-durable Work and result separation

1. A waiting act whose request/assignment/handoff/due/result-return history need not persist is
   derived without Work ID, assignee, due time, or completion state.
2. A cross-person request requiring persisted handoff and return creates one durable Work identity
   with the exact Responsibility, context packet, requester/basis, required result contract, and
   return.
3. Work cannot create Evidence Applicability, Value/Risk acceptance, Integration, Authority,
   Decision, Trigger Determination, Reassessment result, Intervention Completion Acceptance,
   Activation Authorization, or Learning interpretation. `COMPLETED` requires the exact eligible
   result Version already created by the owning domain command.
4. Cancelled/superseded Work retains its full history and result links. No percentage, inferred
   priority, rank, strongest-state, semantic similarity, generic task tree, workflow graph, or
   authoritative chat appears.

### 9B.5 Handoff, return, independence, and staleness

1. Same-Actor and different-Actor handoffs carry the same exact visible Case, Configuration,
   information/assessment, purpose/scope, prerequisite, Responsibility, required result, and return
   context. The receiver need not reconstruct already-governed context.
2. Linking one exact result recomposes the origin. It makes only its own prerequisite satisfied;
   another independent prerequisite remains independently visible and outstanding.
3. If a context Version, Responsibility, access fact, or required authority changes after review,
   commit fails with zero mutation. Old Work remains bound to old context; no silent retarget,
   status copy, or auto-completion occurs.
4. Result-link/completion commits all intended facts or none. Exact replay creates no duplicate
   result link, Work Version/status event, audit fact, or delivery intent.

### 9B.6 Access and non-disclosure

1. Access is evaluated before candidate selection, queue/participant composition, assignment,
   handoff, result link, and return.
2. A hidden Case, Actor, source, candidate, vacancy/conflict fact, global count, or context cannot be
   inferred from labels, explanations, ordering, timing, counts, or aggregates.
3. Responsibility does not grant access and access does not create Responsibility. A responsible
   but unauthorized Actor receives a safe denial and no access grant or domain mutation.

### 9B.7 Harborlight Scenario-A end-to-end oracle

Starting from the preserved stopping point and without mutating the live Case:

```text
two independent Value-review Applicability prerequisites
  -> first exact Responsibility is vacant
  -> authorized exact JUDGE_EVIDENCE_APPLICABILITY assignment
  -> durable contextual Work to same or different Actor
  -> owning Evidence command creates exact Applicability Version
  -> atomic Work result link and return
  -> originating Value review recomposes
  -> second Applicability prerequisite remains outstanding
```

The assignment makes no Applicability judgment, Work creates no result, and neither grants Decision
Authority. Repeat with conflicting co-current Responsibilities, invalid assignment basis, stale
Configuration/Evidence/Input, inaccessible source, cancelled/superseded Work, and failure on the
second intended write; each failure preserves all prior facts and produces no partial mutation.

## 10. Boundary-Sensitivity Tests

Boundary behavior is one of PAIM's most important observable properties.

Test questions include:

- Does the boundary narrow when Risk becomes more restrictive?
- Does the boundary broaden only when evidence/authority support it?
- Does removal of a required control make the prior boundary unsupported?
- Does scope expansion trigger new evidence requirements?
- Does an exact proposed operating-state change require a different Boundary based on explicit
  evidence and accountable judgment, without inferring rank from either state label?
- Are explicit exclusions preserved?

A system that preserves the same boundary regardless of material input changes is suspect.

## 11. Value-Constant / Risk-Variable Tests

Hold Value constant.

Vary Risk.

Expected behavior may include:

- unchanged Value Input;
- changed Risk Input;
- narrower Integrated Operating Boundary;
- new control condition;
- different alternative selected;
- stronger learning requirement;
- suspension or redesign if necessary.

The system must not rewrite Value because Risk changed.

## 12. Risk-Constant / Value-Variable Tests

Hold Risk constant.

Vary Value.

Expected behavior may include:

- unchanged Risk Input;
- different management attractiveness;
- changed alternative selection;
- possible discontinuation if Value no longer justifies operation;
- unchanged Risk conditions if those conditions still apply.

The system must not weaken Risk controls merely because Value improves.

## 13. Control Trade-Off Tests

Change a control that affects both Value and Risk.

Examples:

- universal verification;
- threshold;
- secondary review;
- analyst review burden;
- human handoff.

Test whether PAIM:

- preserves control dependency;
- identifies changed Value;
- identifies changed Risk;
- recognizes configuration trade-off;
- avoids treating the control only as cost or only as protection.

## 14. Authority Behavior Tests

Scenario variants should include:

### Missing authority

Expected:

`AUTHORITY UNRESOLVED`

### Authority resolved in favor of current scope

Expected:

- gap closed;
- current decision may remain;
- an exact proposed different state is not automatically approved; no strength relation is
  inferred.

### New prohibition

Expected:

- boundary/decision review;
- potentially immediate constraint/suspension.

### Decision authority unresolved

Expected:

- analysis may proceed;
- case cannot become `DECIDED`.

## 15. Uncertainty Behavior Tests

Tests should examine whether:

- Accepted Uncertainty permits bounded operation;
- the same uncertainty may be classified Decision-Limiting for an exact proposed state through
  accountable judgment, without a mechanical stronger-state comparison;
- resolved uncertainty can support reassessment;
- unresolved uncertainty is not silently removed;
- a completed Learning Item does not automatically change the decision without reassessment.

## 16. Operating-State Exactness and Post-v0.1 Escalation Tests

### 16.1 Bounded v0.1 exact-state oracles

Use the same Configuration and evidence while varying only exact operating-state identity and exact
structured scope. For bounded v0.1, prove that:

- identities are stored, displayed, filtered, grouped, reported, and exported exactly, with no rank;
- every change still requires an eligible authorized successor/amendment Decision;
- independently valid Interim Operating Dispositions combine through exact-scope restrictive
  intersection;
- determinable intersection applies every explicit restriction;
- indeterminate combined effect suspends only the affected scope; and
- enum order, labels, colors, numeric codes, queue order, recency, severity, and notification
  frequency never imply strength, breadth, restrictiveness, priority, or escalation.

### 16.2 Post-v0.1 state-relation extension scenarios

The earlier progression idea—experiment → bounded continuation → targeted scale →
institutionalization—is retained only as a future scenario family. It is not an ordering oracle.
After separate human acceptance of organization-configured state traits/relations, future tests may
ask whether evidence sufficient for one exact state is insufficient for a separately established
related state, including incomparable and indeterminate pairs. Those scenarios remain outside v0.1
and may not be used to infer the missing relation from labels or fixture order.

## 17. Configuration-Change Tests

Material configuration variants should test:

- increased AI authority;
- new task class;
- new data class;
- new model/provider;
- changed controls;
- changed capacity;
- new operating environment.

Expected behavior:

- applicability review;
- potential successor configuration;
- Value/Risk refresh;
- reassessment;
- no silent evidence transfer.

## 18. Evidence-Maturity Tests

Construct alternatives with different evidence maturity:

- demonstrated;
- supported;
- plausible;
- unknown.

Test whether the system:

- preserves maturity distinctions;
- prevents plausible redesign from inheriting demonstrated evidence;
- exposes missing evidence;
- ties learning to blocked decisions.

## 19. Conflict Tests

### Type A — Recommendation conflict

Value and Risk support materially different management actions.

Expected:

- both inputs preserved;
- conflict explicit;
- alternatives generated;
- no averaging-away;
- accountable management judgment.

### Type B — Configuration trade-off

A configuration change improves one analytical dimension while worsening another.

Expected:

- trade-off explicitly represented;
- control dependency visible;
- alternative configurations compared.

## 20. Compatible-Input Tests

Value and Risk both support similar action.

Expected:

- independent reinforcement preserved;
- PAIM still establishes final boundary;
- agreement does not eliminate uncertainty, authority, or control analysis.

## 21. Missing-Evidence Tests

Remove material evidence.

Expected behavior may include:

- input cannot be frozen;
- integration readiness blocked;
- uncertainty becomes Decision-Limiting;
- the exact proposed state may be blocked through accountable evidence/authority judgment, with no
  strength relation inferred;
- learning generated.

The system should prefer explicit insufficiency over fabricated certainty.

## 22. Stale-Evidence Tests

Change conditions so previously current evidence becomes stale or uncertain.

Expected:

- evidence refresh required;
- input applicability review;
- reassessment;
- historical decision retained.

## 23. Intervention Tests

The IRR-010 hard-oracle set must test exact Decision/target-Configuration binding, dual time, history, accountability, and activation atomicity. Expected results are normative:

1. `REQUIRED_BEFORE_OPERATION` with Completion Result/evidence but no Acceptance returns per-obligation `NOT_ESTABLISHED`; activation is blocked.
2. The same exact obligation with one eligible accountable `ACCEPTED` Acceptance returns `SATISFIED`.
3. Two required-before obligations with one satisfied and one incomplete return aggregate `INCOMPLETE`; activation is blocked.
4. Incompatible eligible Acceptances return `COMPLETION ACCEPTANCE CONFLICT — UNRESOLVED`, per-obligation/aggregate `CONFLICT`, and block activation.
5. An acceptor assignment valid only for an unrelated Intervention, Decision, Configuration, or Case is ineligible; accountability/Acceptance remains not established.
6. Intervention Owner self-acceptance without a separately applicable Completion Acceptor assignment/mechanism is ineligible. The same actor may be eligible only when both exact functions and relationships are independently established and retained.
7. Incomplete `REQUIRED_AFTER_OPERATION` does not block initial activation only when the exact Decision permits post-operation completion and retains timing/conditions.
8. Incomplete `OPTIONAL` does not block activation and never becomes mandatory through age, preference, or software configuration.
9. `PARTIALLY_COMPLETED` returns `INCOMPLETE`; `FAILED` or `CANCELLED` without valid replacement returns `BLOCKED`; none is satisfied.
10. An accepted fallback/replacement within the existing Decision/Boundary determines prospective satisfaction only through one exact replacement relationship and its own Completion Result/Acceptance; predecessor history remains. Substantive change requires a successor Decision.
11. A successor Decision that changes a requirement has its own Obligation Set and receives no silent carry-forward; absent eligible continued-validity determination, its obligation is `NOT_ESTABLISHED`.
12. Software permission or technical-principal identity alone cannot accept completion or authorize activation.
13. One explicit eligible Obligation Set containing zero required-before obligations returns `NOT_REQUIRED`.
14. Missing Obligation Set returns `NOT_ESTABLISHED`, never `NOT_REQUIRED`.
15. Two incompatible current replacement relationships return `CONFLICT` with no newest/specificity winner.
16. Later routine acceptor-role expiry does not rewrite a historically valid Acceptance; a withdrawn/superseded Acceptance is ineligible for future activation.
17. Completion accepted for the wrong Decision Version or target Configuration Version is ineligible.
18. Completion Acceptance alone does not authorize activation; missing Activation Authorization blocks with no partial operating/transition state.
19. A purported pre-authorized mechanism without exact genuine organizational rule/version/scope/authority in the Decision Authorization Basis is invalid.
20. A genuine governed organizational mechanism with exact retained rule/version/scope/authority, all target guards, and atomic Prerequisite Evaluation/Activation/Transition basis is eligible.

Additional metamorphic checks must show that changing only an exact relied-upon Decision, target Configuration, Boundary, obligation, Completion Result, Acceptance, replacement, or activation-mechanism Version changes prospective eligibility without rewriting historical activation. Test results must retain all contributing diagnostics rather than only a Boolean or universal score.

## 24. Learning Tests

Test whether:

- Decision-Limiting Uncertainty generates a Learning Item;
- Learning Item is tied to a blocked decision;
- practitioner-designed method remains distinguishable from evidence requirement;
- inconclusive learning leaves uncertainty unresolved;
- favorable learning creates evidence for reassessment rather than automatic decision change.

## 25. Reassessment Tests

Every scenario preserves the prior Decision and its exact historical basis, uses exact effective/recorded/knowledge context, preserves Value/Risk independence, and returns explicit absence/conflict rather than a heuristic winner.

The hard-oracle Reassessment scenario set is:

1. **One Trigger → one Reassessment:** one Case-scoped Trigger, one eligible Trigger Determination, one `OPEN` Reassessment Version, one immutable membership, and `LINKED_ACTIVE` coverage.
2. **Two compatible Triggers before start:** same context proves only potential compatibility. One eligible grouping determination may create one first Reassessment Version binding both exact Trigger Versions; otherwise they remain unassigned/separate.
3. **Second compatible Trigger after open:** eligible grouping plus a successor Reassessment Version atomically binds the expanded exact Trigger Set; the predecessor Set remains unchanged.
4. **Exact replay:** same source occurrence/Case/question/idempotency identity returns the original Trigger outcome or payload mismatch and creates no duplicate.
5. **Materially changed source Version:** same occurrence/Case/question creates a successor Trigger Version; a distinct question needs accountable new identity. Prior Version remains.
6. **One source event affects two Cases:** distinct Case-scoped Triggers cite the same exact source provenance; no cross-Case merge, outcome, authority, or satisfaction transfer.
7. **Unrelated same-Case Triggers:** no grouping by recency, category, severity, or source similarity; each remains independently covered/unassigned.
8. **Non-overlapping concurrent Reassessments:** coexistence requires mechanically disjoint structured scope or one eligible coordination determination.
9. **Overlapping concurrent Reassessments:** return `REASSESSMENT OVERLAP CONFLICT — UNRESOLVED`; neither completes or changes disposition for affected overlap by last-writer-wins.
10. **Attempted Trigger consumption:** one Reassessment cannot consume another's Trigger absent exact Membership, coordination, successor Reassessment Version, and preserved prior relationship.
11. **Merge request:** reject as unsupported in v0.1 without changing either identity, Trigger Set, status, or history.
12. **Cancellation/supersession:** preserve all Reassessment/Trigger history and atomically establish compatible prospective coverage for every unresolved Trigger.
13. **Trigger correction/withdrawal after completion:** historical completed basis remains; corrected/withdrawn Version is prospectively ineligible and may create new attention/Trigger.
14. **Eligible requiring Trigger unassigned:** return `REASSESSMENT_REQUIRED_UNASSIGNED`; the Trigger remains in authoritative queries without relying on a UI queue.
15. **Exactly one completion path:** commit `COMPLETED_CONFIRMED` plus Confirmation or `COMPLETED_SUCCESSOR_DECISION` plus authorized successor bundle atomically; zero/both are rejected.
16. **First same-Decision Reassessment completes:** another does not auto-close and must prospectively revalidate current governance, scope, coverage, accountability, and authority.
17. **Successor Decision becomes effective:** predecessor-bound open work remains historical and cannot complete as current; explicit successor Reassessment/rebase and Trigger carry-forward are required.
18. **Conflicting Interim Operating Dispositions:** apply exact determinable restrictive intersection; suspend affected scope if indeterminate; use no state ranking.
19. **Explicit operating-state value:** carry/compare identity and exact authorized applicability only; stronger/broader/priority inference is unavailable.
20. **Existing/external source without Observation:** exact Evidence, Authority Gap, Intervention/Learning, Configuration, or explicit human/external provenance can source a Trigger; no Observation is created.
21. **Queue/timestamp/severity coordination attempt:** has no authoritative effect and cannot group, prioritize, cancel, supersede, or merge.
22. **Later role expiry versus withdrawal/revocation:** routine later expiry preserves valid historical action; withdrawal/revocation/supersession is prospective and blocks future reliance.
23. **Unauthorized duplicate/coordination action:** returns accountability not established/conflict; software permission or Case ownership cannot substitute.
24. **No Management Register:** Case-scoped Trigger selection, coverage, concurrency, disposition, and completion remain deterministic from authoritative records.

Additional negative and metamorphic hard oracles are:

25. Two incompatible eligible current Trigger Determinations return `TRIGGER DETERMINATION CONFLICT — UNRESOLVED`; recency never selects.
26. Exact same Case/Decision/Configuration context without eligible grouping does not group Triggers.
27. Missing or indeterminate affected scope cannot prove non-overlap and returns overlap conflict absent eligible coordination.
28. Cancelling/superseding a Reassessment with an unresolved Trigger and no atomic compatible coverage disposition fails with no partial status/coverage change.
29. Two incompatible current coverage results return `TRIGGER COVERAGE CONFLICT — UNRESOLVED`; no desirable-status winner exists.
30. Two distinct Trigger identities claimed as duplicates require one eligible identity-level Duplicate Disposition naming the canonical Trigger; semantic similarity or missing authority fails.
31. A fabricated/free-form governed-mechanism token cannot authorize Trigger Determination, grouping, duplicate disposition, coordination, cancellation, supersession, or coverage action.
32. A genuine governed mechanism is eligible only with exact identity, rule/version, scope, authority source, actor/function where applicable, limits, effective period, and history.
33. A stale expected Reassessment/Trigger Set/current-selection precondition rejects rather than silently rebasing concurrent membership or completion.
34. A future-effective successor Decision changes eligibility only at its effective time; queries at different knowledge cutoffs reconstruct what PAIM knew without rewriting history.
35. A completed Reassessment sourced by incident, control failure, provider/model change, authority resolution, capacity change, completed Learning, a source-described state-change request naming an exact proposed state, or scheduled review preserves exact Trigger provenance and uses the same cardinality/concurrency rules; PAIM infers no stronger-state relation.

Metamorphic checks must show that changing only the exact Case, Decision Version, Configuration Version, Trigger Version, source Version, structured scope, membership, Trigger Determination, accountable assignment/mechanism, delegation link, effective time, knowledge cutoff, or successor-Decision effective time changes prospective eligibility as specified without rewriting historical results.

### 25.1 Bounded v0.1 Observation and operating-state exclusion oracles

Increment 9 must include direct hard oracles proving all of the following:

1. A request for a first-class Observation record or Observation/telemetry automation fails
   explicitly and creates no authoritative record.
2. Arrival of telemetry, logs, metrics, alerts, incidents, or proposed intake does not automatically
   become Evidence, Trigger, or Register attention.
3. An exact manual/external source occurrence can enter proposed provenance-preserving intake and,
   only after an explicit practitioner owning-domain command succeeds, source a Trigger without
   creating Observation identity.
4. Provider identity, text similarity, timestamps, category, or other semantic resemblance never
   deduplicates source occurrences or Triggers; exact replay identity is the only idempotency basis.
5. Exact operating-state identities are preserved and exposed without rank, severity, priority, or
   escalation inference.
6. Exact-scope Interim Operating Disposition intersection applies all explicit restrictions; an
   indeterminate combined effect suspends only the affected scope.
7. Enum order, labels, colors, numeric codes, queue order, recency, severity, and notification
   frequency have no substantive state relation or priority effect.
8. No UI, report, export, notification, test verdict, or release statement claims first-class
   Observation/automatic conversion or operating-state relation/ranking/escalation.

The first-class longitudinal Observation, conversion, retention/correction, and
organization-configured state-relation scenarios remain preserved as post-v0.1 extension suites.
They must stay disabled until separate accepted design/specification/implementation gates define
their records, authority, history, and exact oracles; no future suite may reinterpret v0.1 history.

### 25.2 Preserved post-v0.1 Observation extension scenarios

After IRR-009 receives separate substantive design authority, a future suite should test stable
Observation and Version identity, exact source/Configuration/Boundary provenance, effective and
knowledge time, correction/supersession/currentness, retention, conflict, accountable linkage or
conversion to Evidence/Trigger, Register eligibility, replay/quarantine, and historical
reconstruction. It must distinguish telemetry arrival, proposed intake, authoritative Observation,
Evidence, and Trigger without automatic promotion. These scenarios are deliberately retained for
future design traceability and are outside the v0.1 Increment 9 campaign.

## 26. Portfolio Tests

Across multiple cases, test whether the Management Register surfaces:

- unresolved authority;
- overdue intervention;
- reassessment due;
- boundary breach;
- shared provider dependency;
- shared capacity/control bottleneck;
- closed vs. active cases;
- multiple active configurations under one case.

### 26.1 IRR-012 hard-oracle scenarios

The following are normative hard oracles for the accepted Management Register contract:

1. **Unresolved Authority Gap:** one `CURRENT_ATTENTION` concern cites the exact Gap Version and context.
2. **Authority Gap resolution:** current unresolved attention ends prospectively; the unresolved historical view remains exactly reconstructable.
3. **Same Evidence source, different Case Applicability:** Case/target concerns remain independent; Evidence-source equality does not establish Shared Dependency.
4. **Same exact Shared Dependency identity:** descriptive cross-Case grouping and exact counts are permitted without authority/applicability/closure transfer.
5. **Similar provider names only:** no dependency identity or authoritative group is inferred.
6. **Blocked Intervention obligation:** current attention cites exact Obligation, Intervention, aggregate result, requirement type, and consequence.
7. **Required-before satisfied, required-after incomplete:** activation history remains unchanged; the required-after commitment retains its separate deterministic attention treatment.
8. **`REASSESSMENT_REQUIRED_UNASSIGNED`:** exact Trigger Version and coverage result remain visible current work.
9. **Trigger Coverage conflict:** every candidate/reason remains visible; no winner or disappearing Trigger.
10. **Active and completed Reassessments with shared provenance:** active work is current as applicable; completed work is historical; provenance does not merge identity/outcome.
11. **Provider name shared across Cases only:** no grouping identity is inferred.
12. **Shared Dependency with different owning authorities:** descriptive group preserves each independent authority/accountability result.
13. **Prospective source supersession:** successor truth becomes current; predecessor becomes `SUPERSEDED_HISTORICAL`; earlier views remain exact.
14. **Upstream current-selection conflict:** concern is `CURRENT_CONFLICT` with all candidates; newest never wins.
15. **Projection behind source high-water mark:** output is visibly stale/inconsistent or rebuilt before claiming current; commands re-evaluate authoritative facts.
16. **User dismisses unresolved row:** only optional personal presentation state changes; organizational concern and source remain unresolved.
17. **Sort by age:** presentation order changes with no substantive priority/state/authority effect.
18. **Sort by explicit authoritative due date:** presentation remains faithful to exact dates and retains sort basis; no new priority meaning.
19. **Similar semantic text without exact dependency:** no automatic grouping; semantic similarity is ineligible.
20. **Accountable equivalence:** group retains stable Shared Dependency ID, exact Candidate Set Version, Equivalence Determination Version, rationale, actor/accountability, and dual time.
21. **Incompatible equivalence determinations:** `SHARED DEPENDENCY EQUIVALENCE CONFLICT — UNRESOLVED`; no combined winner; constituents remain independently visible.
22. **Affected-Case count:** exact constituent set and descriptive count are retained; count is not risk, severity, materiality, or priority.
23. **One constituent Case resolves:** that concern resolves historically; another unresolved constituent keeps the group partially unresolved; no cross-Case satisfaction.
24. **All constituents resolve:** group leaves current attention prospectively and exact historical membership/basis remains reconstructable.
25. **Register launches Reassessment:** the exact Trigger/Reassessment commands and all accountability/current-governance guards apply.
26. **Register attempts blocked-Intervention resolution without Acceptance:** rejected/no authoritative effect; attention remains until the owning Completion contract is satisfied.
27. **Different operating-state values:** values display/group only by exact identity; no strength, severity, priority, or winner is inferred.
28. **Unaccepted external Observation-like data:** no authoritative concern entry is created; UI context is clearly non-authoritative.
29. **Notification intent from unresolved work:** intent retains exact concern basis; generation/delivery/retry never changes source or concern state.
30. **Historical as-of Register view:** exact source Versions, conflicts, Candidate Set and determinations, active rule Versions, effective/knowledge time, high-water/watermark, constituent membership, filters, grouping, and ordering are reproduced.

Additional negative oracles must reject mutable/free-form/transient `DEPENDENCY_CANDIDATE_SET` targets; Candidate Set membership mutation after finalization; accountability resolved from recomputed query membership; similarity/name/owner/software equivalence; broad/narrow/recency accountability winner; generic Register resolution; cross-Case transfer; universal scoring; and use of a stale projection as guarded-command authority.

## 27. Role/Accountability Tests

Test:

- same person fills Value and Risk roles;
- Decision Authority missing;
- delegated authority expired;
- Intervention Owner changes;
- System Administrator attempts substantive change;
- Reviewer detects issue without editing authoritative record.

Expected behavior is explicit attribution and integrity, not automatic rejection of every role overlap.

## 28. Negative Tests

The platform should deliberately be tested with invalid or inconsistent inputs.

Examples:

- Value and Risk bound to different configurations;
- missing provenance;
- missing decision authority;
- decision broader than boundary;
- intervention marked complete without criteria;
- superseded input used as current;
- unresolved authority omitted;
- historical decision overwritten.
- incompatible current versions silently resolved by newest timestamp;
- lifecycle transition not allowed by the canonical transition table;
- Decision authorized through an expired, revoked, or out-of-scope delegation;
- narrative boundary clause treated as satisfied without accountable determination;
- Interim Operating Disposition broadens operation or continues after expiry;
- completed Reassessment has neither unchanged-Decision confirmation nor successor Decision.

Expected behavior:

- prevent, block, or visibly flag inconsistent state;
- preserve historical records;
- require accountable correction.

## 29. Metamorphic Testing

PAIM is well suited to metamorphic testing, where a controlled input change should imply a directional behavioral change even when no single "correct" final decision exists.

Examples:

### Remove a required control

Expected relation:

> System should not produce a broader/more permissive boundary than before solely because the control disappeared.

### Resolve a Decision-Limiting Uncertainty favorably

Expected relation:

> A previously blocked stronger state may become eligible for consideration, but should not become automatically authorized.

This relation is a post-v0.1 extension scenario only. For v0.1, substitute an exact proposed state
and verify only that accountable evidence/authority evaluation may change eligibility and that no
automatic authorization or inferred state relation occurs.

### Increase AI authority

Expected relation:

> Evidence/authority requirements should stay the same or become stronger, not weaker, absent countervailing evidence.

This is particularly useful for black-box testing.

## 30. Invariance Testing

Some changes should not alter substantive behavior.

Examples:

- rename a case;
- change formatting;
- correct non-substantive metadata;
- change an administrative owner with no authority/control effect.

Expected:

- no analytical/decision change solely from non-material administrative variation.

## 31. Surrogate Behavioral Models

Human or analytical testers may construct empirical surrogate models of PAIM behavior by observing many controlled scenarios.

Possible goals:

- identify which variables drive boundary changes;
- identify when the system requests reassessment;
- detect unexpected discontinuities;
- compare similar cases;
- test whether operating-state escalation behaves consistently.

The surrogate is a validation aid, not a replacement for PAIM.

## 32. Test Oracles

Not every PAIM scenario has a single correct decision.

Therefore test oracles should include multiple forms.

### Hard oracle

A required invariant.

Example:

> Authorized historical decisions must not be overwritten.

### Directional oracle

Expected direction of change.

Example:

> Removing a boundary-critical control should not justify broader operation.

### Constraint oracle

A condition that must remain true.

Example:

> Unresolved authority must remain explicit.

### Reasoning oracle

The system must expose specified reasoning elements even if multiple final judgments are defensible.

Example:

> Type A conflict must preserve both contributing implications.

## 33. Human-System Validation

Human testing should begin only when the integrated platform can present a coherent workflow.

The human tester should interact with:

- case intake;
- configuration;
- contextual evidence/authority;
- Value/Risk inputs;
- integration;
- decision;
- intervention;
- learning;
- reassessment;
- register.

The tester should not be asked to reconstruct development artifacts.

## 34. Human Test Questions

Human validation should examine:

### Comprehension

Do testers understand what the system is asking?

### Judgment placement

Does PAIM ask humans to exercise judgment at appropriate points?

### Traceability

Can testers understand why the system reached its current management state?

### Burden

How much effort is required?

### Error modes

Where do testers make mistakes?

### Behavioral expectations

Do testers predict how PAIM should respond to controlled changes?

### Trust calibration

Do testers appropriately distinguish system guidance from management authority?

## 35. Human Black-Box Test Design

A human test may use paired or sequential scenarios.

Example:

```text
Scenario A:
Bounded continuation supported.

Scenario B:
Same case, required control removed.

Question:
What changes in PAIM behavior?
```

This reduces the need for testers to understand internal documents and focuses attention on observable management behavior.

## 36. UI Usability vs. PAIM Behavioral Validity

The testing program must distinguish:

### UI usability failure

Example:

Tester cannot find the authority panel.

### PAIM behavioral failure

Example:

System silently treats unresolved authority as permission.

### Documentation/guidance failure

Example:

Tester sees the feature but misunderstands Accepted vs. Decision-Limiting Uncertainty.

These should not be conflated.

## 37. Test Data Strategy

Early testing should use synthetic or representative cases that avoid unnecessary confidentiality.

A test library should eventually include:

- compatible inputs;
- Type A conflict;
- Type B trade-off;
- evidence insufficiency;
- authority gap;
- control failure;
- reassessment;
- provider/model change;
- portfolio concentration.

Real cases may be introduced later under appropriate governance.

## 38. Regression Testing

Once platform behavior is implemented, validated scenario families should become regression tests.

A change to software should not silently alter established management behavior.

Regression should cover:

- lifecycle;
- configuration binding;
- evidence applicability;
- frozen inputs;
- decisions;
- interventions;
- reassessment;
- register behavior.

## 39. Versioned Expected Behavior

Behavioral expectations should be versioned.

If PAIM method/system rules change intentionally:

- preserve old test result;
- update specification;
- create new expected behavior;
- bind the new expectation to its exact Semantic Contract ID/Version and applicable record-family
  cutover; and
- document reason.

Do not silently rewrite the test oracle to make current software pass. Legacy and prospective
expectations may coexist; test selection follows the exact semantic contracts in the fixture rather
than assuming the newest expectation applies retroactively.

## 40. Test Evidence

Each formal test should preserve:

- Test ID
- system/platform version
- Semantic Contract ID/Version for every governed family under test
- scenario version
- input state
- exact context/query/access basis and effective-at/known-at cutoff where applicable
- controlled change
- expected behavior/oracle
- observed behavior
- result
- deviation
- interpretation
- follow-up action.

## 41. Verdict Categories

Possible test verdicts:

- PASS
- PASS WITH QUALIFICATION
- FAIL
- INCONCLUSIVE
- TEST ADMINISTRATION FAILURE

Administration failures should remain separate from system-behavior failures, consistent with IET experience.

## 42. Failure Classification

Behavioral failures may be classified as:

- specification violation;
- implementation defect;
- ambiguous specification;
- missing system requirement;
- UI/usability issue;
- data/test-fixture issue;
- administration issue.

This supports disciplined correction.

## 43. Platform Readiness for Human Testing

The platform is ready for formal human testing when, at minimum:

- end-to-end case lifecycle works;
- configuration/versioning works;
- evidence/authority can be surfaced contextually;
- Value/Risk inputs can be created/frozen;
- integration/decision workflow works;
- intervention/learning works;
- reassessment works;
- Management Register works;
- history/traceability works;
- major behavioral scenario families pass.

A polished visual design is desirable but not the only readiness criterion.

## 44. Human Validation Gate

Formal human validation should be authorized only after:

1. this v0.1 consistency reconciliation is independently reviewed and merged;
2. a separate bounded Increment 9 issue freezes the exact v0.1 claim under test;
3. that issue freezes the three practitioner pathways—Case-to-authorized-operation,
   Trigger-to-Reassessment-completion, and multi-Case Register-to-contextual-owning-domain-action—
   and hard oracles including both excluded boundaries;
4. regression, security, access, recovery, degraded-operation, and historical-reconstruction
   evidence requirements are frozen;
5. core behavioral invariants pass and known critical implementation defects are resolved;
6. test scenarios and expected outcomes are frozen, and human instructions are independent of
   development artifacts;
7. the interface is stable enough that method behavior can be distinguished from unfinished
   implementation;
8. practitioner-study and usability evidence are defined, with usability findings explicitly
   separated from semantic failures; and
9. final traceability and release-verdict evidence are defined.

This consistency update does not authorize Increment 9. Scope completion is not validation or
release completion.

## 45. Codex / Engineering Validation Role

Once platform development begins, Codex or another repository-aware engineering agent can assist with:

- translating specifications into automated tests;
- building scenario fixtures;
- checking state-transition invariants;
- regression testing;
- identifying ambiguous implementation requirements;
- inspecting code/specification mismatches.

Engineering agents should not redefine PAIM behavior merely to simplify implementation.

## 46. Immediate Pre-Platform Review

Before substantial coding, the full system specification set should undergo an implementation-readiness review focused on:

- ambiguous records;
- unclear identifiers;
- conflicting state definitions;
- undefined cardinality;
- supersession/versioning;
- missing invariants;
- impossible transitions;
- unclear ownership;
- testability.

This review should identify engineering ambiguity without redesigning the PAIM method.

## 47. Open Questions

Deferred until platform architecture/test implementation:

- exact automated test framework;
- scenario storage format;
- UI-testing technology;
- property-based test coverage;
- test-data generator;
- simulation engine;
- human-study instrumentation;
- post-v0.1 Observation/telemetry extension design and instrumentation (outside the v0.1 claim);
- quantitative usability metrics;
- regression cadence;
- release-gate thresholds.

## 48. Completion Impact

With this strategy, the implementation-independent PAIM system design now covers:

- architecture;
- lifecycle;
- configuration;
- evidence/authority;
- Value/Risk interface;
- integration/decision;
- intervention/learning;
- reassessment;
- management register;
- roles/accountability;
- behavioral validation.

This substantially completes the system-specification layer required before platform architecture.

## 49. Recommended Next Step

After independent Gate-2/4 acceptance, add Responsibility or Case Work implementation/conformance
tests only through a separately authorized architecture/implementation gate. Gate 3, Gate 5, and
Gate 6 remain unstarted by these oracles. Do not use the common or Gate-2/4 oracles to imply their
Case-continuity, review-timing, readiness/adequacy/reliance, or quantitative Value/Risk semantics.

## 50. Repository Placement

```text
400. Practical AI Management/
└── system/
    └── testing/
        └── PAIM_SYSTEM_BEHAVIORAL_VALIDATION_STRATEGY_v0.1.md
```

## 51. Conclusion

PAIM human validation should test the integrated management system through its observable behavior, not through the practitioner's ability to reconstruct internal development documents.

The central validation model is:

> **controlled management inputs → PAIM system behavior → observable decision boundaries, actions, learning, and reassessment**

This creates a rigorous path from specification to platform implementation to black-box behavioral testing and, ultimately, meaningful human practitioner validation.
