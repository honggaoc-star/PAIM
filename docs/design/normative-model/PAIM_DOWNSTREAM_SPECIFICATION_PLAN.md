# PAIM Downstream Specification Plan

## Purpose and gate

This plan identifies coordinated normative changes that would be required to implement the
[Normative Model Redesign Proposal](PAIM_NORMATIVE_MODEL_REDESIGN_PROPOSAL.md). It does not edit or
authorize edits to any controlling specification. Each gate requires a separate bounded issue,
independent review, and clean-main checkpoint.

The revisions must be designed as one coherent contract set even if reviewed in bounded PRs. No
specification may silently reinterpret a current record before migration/compatibility semantics
are accepted.

## Recommended order

### Gate 1 — Common integrity and semantic-era contract

Revise:

- `docs/system/specifications/PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`;
- `docs/system/architecture/PAIM_SYSTEM_ARCHITECTURE_v0.1.md`; and
- `docs/system/testing/PAIM_SYSTEM_BEHAVIORAL_VALIDATION_STRATEGY_v0.1.md`.

Define common envelopes/selectors for prospective practical-role relationships, Responsibility,
Work, Review Point, required-review constraint, Case Continuity Determination, semantic contract
version, exact context sets, dual-time reconstruction, legacy/new conflict, and non-authoritative
read composition. Preserve current record families and no-silent-fallback rules.

Exit gate: exact identity/currentness/history/conflict behavior and legacy preservation have
normative examples and hard-oracle plans. No code.

### Gate 2 — Responsibility and accountability contract

Revise:

- `PAIM_ROLES_AND_ACCOUNTABILITY_SPEC_v0.1.md`; and
- relevant accountability sections in Evidence/Authority, Value-Risk, Integration/Decision,
  Intervention/Learning, and Reassessment specifications.

Define Case Practical Role Relationship, controlled Responsibility kinds and per-kind context
schemas, Responsibility Assignment Basis, current selector, vacancy/conflict, delegation,
reassignment, supersession, genuine mechanisms, and separation from access/authority. Declare the
prospective disposition of Role Assignment and the bounded `Applicability Owner` legacy adapter.

Exit gate: every governed obligation resolves through one explicit target-model rule; Decision
Authority remains separate; no free-form role/compatibility key carries a new obligation.

### Gate 3 — Continuing Case and Configuration continuity contract

Revise:

- `PAIM_CASE_LIFECYCLE_SPEC_v0.1.md`;
- `PAIM_MANAGED_CONFIGURATION_SPEC_v0.1.md`;
- Integrity lifecycle sections; and
- Case/Configuration accountability sections.

Define the three continuity statuses, closure/reopening/supersession, Case Continuity Determination,
same/new-Case criteria, treatment of remaining operation/action/learning/review obligations,
subordinate-state composition, and legacy lifecycle compatibility. Keep current management position
derived and Decision-bound history reconstructable.

Exit gate: ongoing management, discontinued use with remaining obligations, true closure,
successor Case, and concurrent subordinate work all have exact examples without a universal
workflow phase.

### Gate 4 — Responsibility & Case Work specification

Create a dedicated controlling specification, provisionally:

- `PAIM_RESPONSIBILITY_AND_CASE_WORK_SPEC_v0.1.md`.

Coordinate revisions to Roles/Accountability and Integrity. Define derived-work boundary, Work
identity/Version, exact context packet, request/assignment basis, coordination states, prerequisite,
due/expected time, governed result/return, reassignment/delegation/cancellation/supersession,
stale-context fail-closed behavior, access filtering, notes boundary, and no domain-result
substitution.

Exit gate: Harborlight prerequisite, cross-person handoff, independent prerequisites, stale work,
vacancy/conflict, and same-Actor multiple-Responsibility examples have hard oracles. No generic
workflow or notification implementation.

### Gate 5 — Continuing review and review-timing contract

Revise:

- `PAIM_REASSESSMENT_SPEC_v0.1.md`;
- `PAIM_INTERVENTION_AND_LEARNING_SPEC_v0.1.md`;
- `PAIM_EVIDENCE_AND_AUTHORITY_SPEC_v0.1.md`;
- `PAIM_INTEGRATION_AND_DECISION_SPEC_v0.1.md`;
- relevant Case/Integrity sections; and
- Roles/Responsibility obligation taxonomy.

Define Planned Review Point, required-review constraint, exact source/Applicability, structured
temporal operators, constraint intersection/conflict, planning Responsibility and authority
boundary, Decision/Configuration change, arrival-as-attention, practitioner-started Review Point
Trigger, focused refresh, realized Value/Risk symmetry, next-point establishment, and legacy
scheduled-Trigger treatment. Define expectation-versus-experience comparison only for exact
comparable constructs, scopes, methods, periods, baselines, Configurations, provenance, and
Applicability; preserve estimate/target/observation/threshold distinctions, later knowledge, and no
automatic causality, materiality, priority, or Decision-error inference.

Exit gate: event-before-plan, required-before-planned, missed planned review, empty required-window
intersection, no-material-change review, focused one-lane refresh, successor Decision, and no
automatic mutation; comparable and non-comparable expected/observed claims; different measure
horizons; and no hindsight rewrite have normative examples and test plans.

### Gate 6 — Value/Risk readiness, assessment adequacy, and reliance hardening

Revise:

- `PAIM_VALUE_RISK_INTERFACE_SPEC_v0.1.md`;
- `PAIM_EVIDENCE_AND_AUTHORITY_SPEC_v0.1.md` and
  `PAIM_INTERVENTION_AND_LEARNING_SPEC_v0.1.md` for quantitative source/observation context;
- relevant Roles/Responsibility and Integrity sections;
- Case readiness composition; and
- Integration current-basis guards.

Define `Finish assessment`, exact candidate finalization/readiness history, successor-on-edit,
neutral assessment adequacy for decision use, its exact information/Applicability basis and
three-outcome-plus-limitations model, and exact reliance designation. Define separately accountable
adequacy and reliance facts, the permitted atomic **Complete Value/Risk review** conditions for one
adequate candidate, explicit choice/dispositions for multiple adequate candidates, reuse, and
legacy Fitness and Acceptance/Selection compatibility without retroactive reinterpretation.

Define optional typed quantitative Value/Risk claims for estimate/expectation, target/objective,
observed result, threshold/constraint, bounded Risk estimate, and cost/resource measure. Specify the
smallest context-sensitive contract for construct, representation/range/distribution, unit,
direction, scope/population, period, comparator/baseline, coverage, provenance,
uncertainty/limitations, and method/assumptions. Preserve claim-type identity, exact lane,
Configuration, relationships, dual time, qualitative legitimacy, and explicit inability to
estimate. Do not force every context field when immaterial or create a mandatory UI questionnaire.

Exit gate: Value/Risk independence; favorable, unfavorable, and uncertain assessments capable of
adequacy on neutral quality grounds; inaccurate/incomplete/overstated/hidden-uncertainty adverse
outcomes; Applicability/adequacy separation; one/multiple candidates; separate Responsibilities;
atomic rollback; reuse; stale context; exact freeze/history; and no automatic reliance or Selection
have hard oracles. Quantitative oracles cover meaningful quantitative and legitimate qualitative
Inputs; missing material context and false precision; target/Evidence, estimate/observation,
observation/causality, threshold/prediction, and measure/judgment separation; independent Value/Risk
measures; cost/benefit separation; no universal ROI, probability × impact, score, ranking, or
automated Decision; and later observations that do not rewrite Decision-time knowledge.

### Gate 7 — Architecture and implementation-readiness review

Only after Gates 1-6 are accepted, revise:

- `docs/engineering/PAIM_PLATFORM_ARCHITECTURE_v0.1.md` or an explicit successor;
- implementation sequencing and dependency gates;
- migration/compatibility plan;
- security/access model;
- validation strategy; and
- operational upgrade/recovery plan.

Decide module ownership, commands, semantic transactions, persistence constraints/indexes,
selectors, read adapters, audit/provenance, concurrency behavior, migrations from every supported
revision, and failure recovery. This gate may split implementation into bounded increments but may
not weaken the coordinated semantics. It must decide whether typed quantitative content is an
embedded versioned component or a related stable Record family based on identity/reuse/history
needs; it may not introduce one mandatory measure schema or top-level score.

### Gate 8 — Domain/persistence implementation

Implement production capabilities in dependency order:

1. integrity/semantic-era primitives and migrations;
2. Responsibility and practical-role relationships;
3. Case continuity selectors/events;
4. Case Work and result/return;
5. Review timing/constraint composition;
6. optional typed quantitative-claim/context capability;
7. readiness/assessment-adequacy/reliance commands; and
8. access-filtered practitioner read composition.

Every increment requires empty/prior-revision migration tests, hard semantic oracles, full
regression, dual-time reconstruction, zero-mutation failures, and compatibility evidence. No broad
UI redesign begins during this gate.

### Gate 9 — Practitioner expression

Only after stable production capabilities and owner acceptance may a bounded UI issue address:

- Case orientation/current management position;
- people, Responsibilities, and Work;
- contextual handoffs and returns;
- next planned/required review explanations; and
- natural optional quantitative capture and comparable expectation-versus-experience explanation
  without a mandatory long form or false precision; and
- simplified **Finish assessment** and **Complete Value/Risk review** actions that preserve neutral
  adequacy and exact reliance consequences.

The UI must expose practitioner action and meaning, not the new machinery. UX-4, M1D, and
organization-local deployment remain separate decisions.

## Cross-specification traceability matrix

| Target concept | Primary future specification | Required coordinated specifications |
|---|---|---|
| Case continuity and same/new Case | Case Lifecycle | Managed Configuration, Integrity, Roles/Responsibility, Reassessment |
| Practical role and Responsibility | Roles & Accountability | new Responsibility/Case Work, Integrity, every governed-result family |
| Durable Work | new Responsibility & Case Work | Integrity, access, domain result specifications |
| Planned Review Point | Reassessment or dedicated continuing-review section | Case, Decision, Learning, Responsibility, Integrity |
| Required review constraint | Evidence & Authority / continuing-review section | Decision/Boundary, Reassessment, Integrity, Responsibility |
| Focused review | Reassessment | Value-Risk, Evidence/Authority, Case, Decision, Learning |
| Readiness | Value-Risk Interface | Responsibility, Integrity, Case composition |
| Optional typed quantitative Value/Risk claims | Value-Risk Interface | Evidence & Authority, Intervention & Learning, Integration/Decision, Reassessment, Integrity, Responsibility |
| Exact expectation-versus-experience comparison | Continuing review/Reassessment | Value-Risk, Evidence/Authority, Learning, Decision, Integrity |
| Assessment adequacy | Value-Risk Interface | Responsibility, Evidence Applicability, Integration, Integrity |
| Reliance designation / competing-candidate choice | Value-Risk Interface | Responsibility, assessment adequacy, Evidence Applicability, Integration, Integrity |
| Migration/semantic eras | Integrity and platform architecture | all changed specifications and operations |

## Required review artifacts per gate

Every specification PR should include:

- explicit old-versus-target semantics;
- record identity/Version/currentness/history contract;
- effective/recorded-time examples;
- accountability and authority treatment;
- absence/conflict and no-winner rules;
- access/non-disclosure implications;
- legacy compatibility and migration impact;
- mechanical versus human judgment boundary;
- hard-oracle test matrix; and
- explicit non-goals.

## Stop conditions

Stop and return to product/design authority if a proposed revision would:

- collapse Value and Risk;
- make responsibility an authority or permission bundle;
- make Work a substitute for governed results;
- turn review timing into automatic materiality or Decision;
- infer Selection from uniqueness;
- force quantification, infer missing quantitative context, or introduce a universal Value, Risk,
  net, ROI, ranking, causal, priority, or Decision-quality score;
- require rewriting v0.1.0 or Harborlight history;
- introduce a universal workflow, cadence, score, or priority; or
- require UI state to fill a missing normative fact.

## Current checkpoint

Issues #129, #131, #133, and #135 complete Gates 1, accelerated 2/4, 3, and 5 respectively as
prospective specification contracts. They activate no consumer cutover or implementation. Gate 6
does not start automatically after Gate-5 acceptance.
