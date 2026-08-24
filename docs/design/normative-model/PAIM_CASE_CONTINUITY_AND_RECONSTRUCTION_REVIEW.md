# PAIM Case Continuity & Historical Reconstruction Review

## Purpose and current-contract boundary

This review evaluates how a Case can remain meaningful across repeated Decisions and review without
becoming an indefinitely mutated container. It proposes future semantics only. Current
[Case Lifecycle](../../system/specifications/PAIM_CASE_LIFECYCLE_SPEC_v0.1.md),
[Managed Configuration](../../system/specifications/PAIM_MANAGED_CONFIGURATION_SPEC_v0.1.md), and
[Integrity](../../system/specifications/PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md)
contracts remain controlling.

## Assessment of the current model

The current model has strong foundations:

- stable Case identity and immutable Versions;
- exact Configuration ownership and successor history;
- separate Decision, operation, Intervention, Learning, Trigger, and Reassessment records;
- explicit closure/reopening/supersession events; and
- dual-time and Decision-basis reconstruction.

Its single canonical lifecycle, however, mixes a Case's long-term continuity with one workflow
phase. `EVIDENCE_ANALYSIS`, `READY_FOR_INTEGRATION`, `INTERVENTION_IN_PROGRESS`,
`OPERATING_OBSERVING`, `REASSESSMENT_DUE`, and `REOPENED` can describe true conditions but cannot
represent all concurrent work without one phase hiding another. A continuing Case can operate,
learn, perform an Intervention, refresh Value, and coordinate a Reassessment at the same time.

The target should preserve those exact subordinate states but stop treating one as the universal
Case state.

## Target Case identity

A Case is one bounded, continuing management subject:

- one materially coherent AI-related business use/question;
- its exact Configuration lineage;
- its independent Value and Risk history;
- its sequence of management Decisions and operating Boundaries;
- actions, outcomes, review, and Learning; and
- the organizational need to retain continuity among them.

Case title, provider, model, inventory identity, or shared evidence does not establish continuity.
One system can support multiple Cases; one Case can include multiple AI and non-AI components.

## Minimal continuity status

The prospective Case status vocabulary is intentionally small:

- `OPEN` — this Case identity remains available for continuing management. `OPEN` does not imply
  active work, operation, approval, or a missing Decision.
- `CLOSED` — an accountable determination establishes that no current operation and no remaining
  required PAIM management obligation continues under this identity. History remains retained and
  reconstructable.
- `SUPERSEDED` — one named successor Case prospectively carries the management subject; the
  predecessor is terminal for new work.

There is no universal `COMPLETED` Case. A Decision, Work Item, Intervention, Learning Item, or
Reassessment may complete. `ACTIVE` is too ambiguous to distinguish Case management, operation, or
work and is not needed. `REOPENED` becomes a Case continuity event/relationship plus exact new work
or Reassessment state, not a long-lived phase.

## When a Case truly ends

Stopping the AI-enabled use is a Decision/operating outcome, not automatically Case closure. The
Case remains `OPEN` while any required:

- Intervention, retirement, data/control disposition, or acceptance remains;
- outcome observation or Learning Item remains;
- review, Authority treatment, or contractual obligation remains;
- unresolved Trigger/Reassessment coverage remains; or
- successor routing is not established.

Closure requires an exact basis, responsible Actor/mechanism, effective/recorded time, treatment of
every continuing obligation, final Decision/operation relationship, and retention/successor facts.
Closure never deletes records or retrospectively ends authority outside its own scope.

A closed Case can return to `OPEN` only when an accountable Case Continuity Determination finds
that the same bounded management subject requires new work. The prior closure remains historical.
A superseded Case is not reopened.

## Same Case or new Case

Use the same Case when the bounded management subject remains coherent and new work is a
reconsideration, changed evidence, successor Configuration within that subject, changed operating
conditions, or later Decision about that same use.

Create a new Case when one or more changes make independent interpretation necessary, including:

- materially different business purpose or management question;
- materially different use/population/workflow with no defensible continuity;
- concurrent independently governed Configuration;
- Evidence that cannot reasonably carry across the claimed identity; or
- a successor that must retain its own responsibilities, authority, Decisions, and review.

Where the answer requires judgment, a **Case Continuity Determination** retains stable identity and
immutable Versions, source Case, candidate same/successor context, exact changed basis, outcome,
rationale, accountable Responsibility/mechanism, effective/recorded time, and any successor Case
relationship. Absence or conflict blocks routing; recency or similarity never decides it.

## Multiple management positions

PAIM does not need a master Management Position record. Each position is represented by the exact
authorized Decision and its Configuration, selected Value/Risk Inputs, Integration, Boundary,
Authority Basis, conditions, action/Intervention obligations, Learning, and review relationships.

An unchanged Decision after formal Reassessment is represented by exact Decision Confirmation. A
material change creates an authorized successor/amendment Decision. Earlier Decisions remain
authoritative for their effective periods. A current-position view selects and composes exact
current sources; absence/conflict remains visible.

## Current management position

The product concept remains a read composition, not a normative master record. Its projection basis
should include, subject to access:

- current Case continuity status and governing Configuration;
- exact current authorized Decision/Boundary and operation;
- independent current Value and Risk acceptances;
- current actions, Work, Interventions, and conditions;
- unresolved Evidence, Authority, Responsibility, conflict, or uncertainty;
- current Learning and realized Value/Risk information;
- planned and required review timing; and
- exact attention conditions.

The projection retains source Version IDs, effective time, optional known-at cutoff, rule Version,
and watermark. It cannot create authority, priority, closure, or a substantive conclusion. A
materialized cache may be rebuilt and is never write authority.

## View Case as it stood when a Decision was made

No new historical summary is needed. The Decision already binds the exact Integration, Boundary,
Configuration, selected frozen Value/Risk Inputs, and Authorization Basis. The common history
contract can reconstruct:

1. the exact basis explicitly bound to that Decision;
2. related Evidence Applicability, Authority/Gap, Responsibility/legacy Role Assignment,
   Intervention, and Learning Versions relied upon;
3. state effective at the Decision time using knowledge now available; and
4. state PAIM actually knew by the Decision's recorded-time cutoff.

The ordinary view should explain the then-known situation and later changes without requiring
practitioners to operate `effective_at`, `known_at`, Record ID, or Version ID controls. Authorized
inspection retains those details.

Later corrections can change today's best account of what was effective then, but they cannot
enter the `known_at` Decision-time view or rewrite the exact basis used. Then-versus-now comparison
must label which facts were learned later.

## Carry-forward through review

Focused review cites unaffected exact current Versions rather than copying them. A Version may be
carried forward only if its family-specific currentness, Configuration, scope, Applicability,
Fitness, authority, and conflict guards still pass for the new review/use. Historical acceptance is
provenance, not automatic current eligibility.

When a material Decision condition, Boundary, operating state, or Configuration changes, the
proper successor Decision path preserves the predecessor. Work or presentation cannot amend it.

## Relationship to subordinate lifecycles

The target keeps independent state and history for:

- Configuration;
- analytical Input/readiness/Fitness/use acceptance;
- Integration and Decision;
- Intervention and activation;
- Learning;
- Trigger and Reassessment;
- Work; and
- planned/required review timing.

The Case opening composes them into meaning such as `Operating under Decision D2`,
`Risk review waiting`, or `Planned review due`. It does not force them into one traffic light or
percentage-complete lifecycle.

## Compatibility boundary

Existing v0.1 lifecycle Transition Events remain valid historical facts and continue to govern
legacy runtime behavior until specifications and code are separately migrated. They must not be
rewritten into the proposed three-status model. A compatibility read adapter may translate current
legacy phase and subordinate records into practitioner explanation while identifying the source
contract and preserving conflicts.

## Non-goals

No universal lifecycle, master current-position record, automatic closure, indefinite same-Case
mutation, first-class Observation, scheduler, UI, schema, or migration is introduced here.
