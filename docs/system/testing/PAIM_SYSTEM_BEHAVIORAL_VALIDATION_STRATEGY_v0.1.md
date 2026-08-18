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
- Phase II validation findings from IET 001–004.

It defines how PAIM should be tested as an integrated management system through controlled inputs, observable outputs, state transitions, invariants, and human-facing behavior.

It does not prescribe a specific software test framework or implementation technology.

**Normative cross-cutting test contract:** `../specifications/PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md` defines the hard integrity behavior for authoritative record history/currentness, Integrated Operating Boundary Snapshots, case transitions, Decision Authorization Basis, and Interim Operating Disposition. Behavioral tests must use those rules as oracles without replacing the human judgments reserved there.

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
- Decision-Limiting Uncertainty blocks stronger states;
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
  +-- Variant E: stronger operating state proposed
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

- experiment;
- continuation;
- scale;
- institutionalization;
- broader deployment.

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

## 10. Boundary-Sensitivity Tests

Boundary behavior is one of PAIM's most important observable properties.

Test questions include:

- Does the boundary narrow when Risk becomes more restrictive?
- Does the boundary broaden only when evidence/authority support it?
- Does removal of a required control make the prior boundary unsupported?
- Does scope expansion trigger new evidence requirements?
- Does a stronger operating state require a stronger/broader boundary?
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
- stronger state not automatically approved.

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
- the same uncertainty becomes Decision-Limiting for a stronger state;
- resolved uncertainty can support reassessment;
- unresolved uncertainty is not silently removed;
- a completed Learning Item does not automatically change the decision without reassessment.

## 16. Operating-State Escalation Tests

Use the same configuration/evidence and vary the proposed operating state.

Example:

```text
Experiment
→ Bounded continuation
→ Targeted scale
→ Institutionalization
```

Test whether evidence considered sufficient for a weaker state becomes insufficient for a stronger state.

This directly targets the operating-state semantic issue exposed in IET 004.

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
- stronger state blocked;
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
35. A completed Reassessment sourced by incident, control failure, provider/model change, authority resolution, capacity change, completed Learning, explicit stronger-state request, or scheduled review preserves exact Trigger provenance and uses the same cardinality/concurrency rules.

Metamorphic checks must show that changing only the exact Case, Decision Version, Configuration Version, Trigger Version, source Version, structured scope, membership, Trigger Determination, accountable assignment/mechanism, delegation link, effective time, knowledge cutoff, or successor-Decision effective time changes prospective eligibility as specified without rewriting historical results.

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
- document reason.

Do not silently rewrite the test oracle to make current software pass.

## 40. Test Evidence

Each formal test should preserve:

- Test ID
- system/platform version
- scenario version
- input state
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

1. core behavioral invariants pass;
2. known critical implementation defects are resolved;
3. test scenarios are frozen;
4. human instructions are independent of development artifacts;
5. UI is stable enough that method behavior can be distinguished from unfinished implementation;
6. expected observations are defined in advance where practical.

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
- telemetry;
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

Do **not** begin coding immediately.

The next artifact should be:

`PAIM_PLATFORM_ARCHITECTURE_v0.1.md`

under:

```text
platform/
└── architecture/
```

Before freezing that architecture, perform a **Codex implementation-readiness review** of the PAIM system architecture and specification set.

The review should ask:

> **Can these requirements be implemented consistently without inventing missing system behavior?**

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
