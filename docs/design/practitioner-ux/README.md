# PAIM Task-Oriented Practitioner UX

## Status and authority

This directory records the design checkpoint produced from the Harborlight Scenario-A practitioner
exercise. It is an implementation-planning layer over existing PAIM capabilities, not a system
specification, runtime change, or empirical validation claim.

Issue #123 established the accepted Practitioner Operating Model checkpoint, and Issue #125
established the accepted Product Design Foundation above it. Issue #127 now records the proposed
Normative Model Redesign checkpoint. Further practitioner-UI implementation remains paused. These
design packages propose no domain, persistence, deployment, fixture, or UI change.

The current contracts under [`docs/system/`](../../system/) remain authoritative. If a proposal here
cannot preserve those contracts, it requires explicit semantic review before implementation.

## Governing principle

> The UI should help practitioners accomplish meaningful management work; it should not demonstrate
> how PAIM represents that work internally.

PAIM must continue to enforce exact identity, history, accountability, authority, and independent
Value/Risk semantics underneath. The interaction layer should carry known context, explain genuine
choices, and reveal machinery only when it helps a governance, audit, or diagnostic task.

## Design set

### Product Design Foundation

- [PAIM Product Design Foundation](PAIM_PRODUCT_DESIGN_FOUNDATION.md) defines the product purpose,
  central value of management continuity, practitioner-centered principles, product concepts,
  attention hierarchy, and relationship between product, operating-model, specification, UI, and
  engineering layers.
- [Continuing Value-Risk & Decision Lifecycle](PAIM_CONTINUING_VALUE_RISK_DECISION_LIFECYCLE.md)
  defines the continuing practitioner cycle, focused review, event- and time-driven attention,
  symmetric treatment of realized Value and Risk, and current-position composition boundary.
- [Decision Record, Audit & Learning Model](PAIM_DECISION_RECORD_AUDIT_AND_LEARNING_MODEL.md)
  distinguishes decision quality from outcome quality and defines Case, Decision, and
  organizational learning without turning history into authority.
- [Product Scope Boundary](PAIM_PRODUCT_SCOPE_BOUNDARY.md) identifies what PAIM owns, what it
  should integrate with, and the explicit anti-sprawl constraints.
- [Harborlight Product Journey](PAIM_HARBORLIGHT_PRODUCT_JOURNEY.md) illustrates continuing
  management using authoritative Scenario-A facts and clearly labeled constructed PAIM product
  extensions without mutating the reference Case.

The Product Design Foundation is the product-level governing reference above the accepted
Practitioner Operating Model. It does not replace the authoritative system specifications or
authorize implementation.

### Normative Model Redesign checkpoint

- [Normative Model Redesign package](../normative-model/) proposes the smallest integrated target
  for continuing Case semantics, practical roles, exact Responsibility, derived and durable Case
  Work, review timing, optional context-bound quantitative Value/Risk, readiness, neutral
  assessment adequacy, exact reliance, historical reconstruction, migration, and coordinated
  downstream specification gates.

The Issue #127 package is a prospective semantic design. Current system specifications remain
controlling, and no proposed concept is implemented or silently read into an existing record.

### Practitioner Operating Model checkpoint

- [Practitioner Operating Model](PAIM_PRACTITIONER_OPERATING_MODEL.md) defines the target audience,
  meaning of local, participant/practical-role/responsibility/authority separation, the two primary
  standing Case roles plus optional Reviewer, and product operating principles.
- [Role Consolidation Map](PAIM_ROLE_CONSOLIDATION_MAP.md) evaluates current named functions as
  the two primary standing Case roles, optional Reviewer, granular responsibilities, separate
  authority, organization-level technical functions, or consolidation candidates.
- [Case Work & Handoff Model](PAIM_CASE_WORK_AND_HANDOFF_MODEL.md) defines derived versus durable
  work, prerequisites, contextual handoffs, completion/return, communication, and notifications.
- [Architecture Feasibility & Gap Assessment](PAIM_PRACTITIONER_OPERATING_MODEL_ARCHITECTURE_GAP_ASSESSMENT.md)
  separates current read-composition support from normative, domain, schema, and future deployment
  work.
- [Harborlight Operating-Model Walkthrough](PAIM_HARBORLIGHT_OPERATING_MODEL_WALKTHROUGH.md) tests
  one-person, small-team, current-vacancy, combined-responsibility, and conflict paths without
  mutating the reference Case.
- [Next UI Redesign Design Brief](PAIM_NEXT_UI_REDESIGN_DESIGN_BRIEF.md) compares practitioner-
  centered Case alternatives and defines implementation entry criteria.

### Earlier task-oriented UX package

- [Pre-UX-1 semantic decisions](PAIM_PRE_UX1_SEMANTIC_DECISIONS.md) resolves the five presentation
  questions that must remain bounded by the system specifications before UX-1 implementation.
- [Scenario-A UX findings](PAIM_HARBORLIGHT_SCENARIO_A_UX_FINDINGS.md) separates observed friction
  from proposed responses.
- [Practitioner UX principles](PAIM_TASK_ORIENTED_UX_PRINCIPLES.md) defines reusable interaction
  rules and hard constraints.
- [Practitioner-language standard](PAIM_PRACTITIONER_LANGUAGE_STANDARD.md) defines the durable
  editorial layers, vocabulary treatment, safeguard rules, component guidance, reference-case
  guidance, and PR checklist that gate UX-3 and later practitioner-facing work.
- [Scenario-A task flow and wireframes](PAIM_HARBORLIGHT_SCENARIO_A_TASK_FLOW.md) specifies the
  end-to-end practitioner experience without pre-deciding an outcome.
- [Information architecture](PAIM_TASK_ORIENTED_INFORMATION_ARCHITECTURE.md) locates ordinary work,
  governance trace, technical inspection, help, and reconstruction.
- [Provisional vocabulary classification](PAIM_SCENARIO_A_VOCABULARY_CLASSIFICATION.md) assigns
  candidate terms to practitioner, contextual, governance/audit, or engineering audiences.
- [Task-to-capability mapping](PAIM_TASK_TO_GOVERNED_CAPABILITY_MAPPING.md) shows how simplified
  interactions preserve separate governed acts and records.
- [Semantic review and implementation decomposition](PAIM_TASK_ORIENTED_UX_IMPLEMENTATION_PLAN.md)
  records UX-1 implementation status, unresolved questions, and bounded follow-on increments.

UX-1 is the implemented read-only orientation and vocabulary increment. UX-2 is the implemented
task-oriented `What we know` workspace: it separates available information, deterministically
explicit unavailable information, requirements/authority sources, and unresolved review work while
retaining the existing governed records and commands. Issue #115 establishes the cross-cutting
practitioner-language standard. UX-3 is the implemented independent Value/Risk workflow over the
unchanged Input, readiness, Applicability, Fitness, and Acceptance/Selection capabilities. It does
not authorize UX-4, M1D, or any domain-semantic extension. UX-3A is the implemented cross-cutting
refinement that carries an exact ready assessment's explicitly linked information into independent
Applicability review tasks and translates shared confirmations around practitioner actions and
consequences. It adds no persisted workflow/progress state and makes no Applicability, Fitness, or
Selection judgment. UX-3B resolves covered judgment accountability from authoritative Role
Assignments, presents vacancy/conflict explicitly, and removes arbitrary accountability text from
Applicability, Fitness, and Acceptance/Selection finalization. It adds no Role Assignment,
accountable-mechanism model, UX-4 work, or M1D behavior.

Issue #125 adds the Product Design Foundation above the accepted Issue #123 operating-model
checkpoint. Issue #127 evaluates the interacting target normative concepts together before any
specification change. Issue #123 supersedes the assumption that UX-4 should begin next. Its
checkpoint distinguishes
practical roles from granular responsibilities and separately governed authority, and documents why
durable cross-practitioner work cannot be implemented as presentation-only state. No UX-4, M1D,
Role Assignment UI, Case Work, or organization-local deployment work is authorized by these docs.

## Exercise boundary

The baseline is the disposable Scenario-A fixture and the stopping point before the practitioner
created Applicability, Value/Risk, Fitness, Selection, Integration, Boundary, proposal, or
authorization records. This design does not mutate that fixture, use later Harborlight scenarios,
or treat the exercise as proof that any proposed response will work.
