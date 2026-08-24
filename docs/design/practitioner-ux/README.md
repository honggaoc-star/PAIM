# PAIM Task-Oriented Practitioner UX

## Status and authority

This directory records the design checkpoint produced from the Harborlight Scenario-A practitioner
exercise. It is an implementation-planning layer over existing PAIM capabilities, not a system
specification, runtime change, or empirical validation claim.

The current contracts under [`docs/system/`](../../system/) remain authoritative. If a proposal here
cannot preserve those contracts, it requires explicit semantic review before implementation.

## Governing principle

> The UI should help practitioners accomplish meaningful management work; it should not demonstrate
> how PAIM represents that work internally.

PAIM must continue to enforce exact identity, history, accountability, authority, and independent
Value/Risk semantics underneath. The interaction layer should carry known context, explain genuine
choices, and reveal machinery only when it helps a governance, audit, or diagnostic task.

## Design set

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
Selection judgment.

## Exercise boundary

The baseline is the disposable Scenario-A fixture and the stopping point before the practitioner
created Applicability, Value/Risk, Fitness, Selection, Integration, Boundary, proposal, or
authorization records. This design does not mutate that fixture, use later Harborlight scenarios,
or treat the exercise as proof that any proposed response will work.
