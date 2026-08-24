# PAIM Normative Model Redesign

## Status and authority

This directory contains the Issue #127 semantic-design checkpoint. It proposes the smallest
prospective normative model needed to support the accepted
[Product Design Foundation](../practitioner-ux/PAIM_PRODUCT_DESIGN_FOUNDATION.md) and
[Practitioner Operating Model](../practitioner-ux/PAIM_PRACTITIONER_OPERATING_MODEL.md).

The package is not a controlling system specification, migration, implementation plan, or
authorization to change code, persistence, UI, deployment, fixtures, or release state. Current
[system specifications](../../system/specifications/) remain controlling until coordinated
revisions are separately approved.

## Design package

- [PAIM Normative Model Redesign Proposal](PAIM_NORMATIVE_MODEL_REDESIGN_PROPOSAL.md) integrates
  the target concepts, boundaries, end-to-end examples, and product-to-normative traceability.
- [Responsibility & Case Work Normative Concept](PAIM_RESPONSIBILITY_AND_CASE_WORK_NORMATIVE_CONCEPT.md)
  defines practical-role relationships, exact Responsibility, derived work, durable Case Work,
  handoff, result, return, and stale-context behavior.
- [Continuing Review & Review Timing Normative Concept](PAIM_CONTINUING_REVIEW_AND_TIMING_NORMATIVE_CONCEPT.md)
  distinguishes event-driven review, planned review, required review, focused review, and
  practitioner-determined next review points.
- [Readiness & Selection Necessity Review](PAIM_READINESS_AND_SELECTION_NECESSITY_REVIEW.md)
  identifies which existing acts carry genuine management meaning and which system operations may
  be absorbed into practitioner actions.
- [Case Continuity & Historical Reconstruction Review](PAIM_CASE_CONTINUITY_AND_RECONSTRUCTION_REVIEW.md)
  proposes a continuing Case identity/status model and preserves then-versus-now reconstruction.
- [Migration & Compatibility Assessment](PAIM_NORMATIVE_MIGRATION_AND_COMPATIBILITY_ASSESSMENT.md)
  protects v0.1.0, legacy Role Assignments, existing records, and Harborlight state.
- [Downstream Specification Plan](PAIM_DOWNSTREAM_SPECIFICATION_PLAN.md) identifies the exact
  coordinated specification gates and recommended order before implementation.

## Controlling rule

If this proposal differs from a current system contract, the difference is a future specification
gate, not a reinterpretation of current behavior. No downstream work begins automatically after
this checkpoint.
