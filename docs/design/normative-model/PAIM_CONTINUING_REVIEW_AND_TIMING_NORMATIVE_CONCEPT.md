# PAIM Continuing Review & Review Timing Normative Concept

## Purpose and boundary

This document makes the accepted continuing-review principle normatively supportable without
creating a universal lifecycle or automatic periodic reassessment. It proposes future contracts;
the current [Reassessment](../../system/specifications/PAIM_REASSESSMENT_SPEC_v0.1.md),
[Intervention and Learning](../../system/specifications/PAIM_INTERVENTION_AND_LEARNING_SPEC_v0.1.md),
and other system specifications remain controlling.

## Governing principle

> The organization or practitioner should generally determine when the Case should be reviewed
> again, subject to applicable governing requirements and earlier event-driven review. PAIM should
> not impose a universal review frequency.

The target uses one revisable **next review point**, not a perpetual cadence. A pilot may move from
monthly to quarterly review and later to annual review as context changes. Each point is an exact
historical fact, not a mutable calendar preference.

## Two review origins

### Event-driven review

A potentially meaningful occurrence may arise from a provider/model, use, workflow, control,
policy, Authority, incident, outcome, new Evidence, realized Value, emerging Risk, Intervention,
Learning, Configuration, or another exact source. Existing Trigger provenance and accountable
Trigger Determination provide the right semantic base:

```text
source occurrence
  -> exact Case-scoped Trigger
  -> accountable significance/materiality determination
  -> informational handling, monitoring, focused work, or Reassessment
```

Source category, severity, recency, similarity, or display position never determines materiality.
An event that matters should not wait for the planned review point.

### Time-driven review

A Review Point reaching its date/window creates **review attention**, not a Trigger or conclusion:

```text
Review Point due
  -> derived attention
  -> practitioner begins review
  -> exact Trigger sourced from Review Point when the review is established
  -> accountable Trigger Determination
  -> no follow-up, focused work, or formal Reassessment
```

This preserves the existing determination vocabulary while preventing the calendar from making a
substantive judgment. The UI need not expose the word `Trigger` for a routine review.

## Planned Review Point

A future authoritative **Planned Review Point** should preserve:

- stable Review Point ID and immutable Version ID;
- exact owning Case;
- exact current Decision Version and governing Configuration Version where established;
- review purpose and bounded scope;
- target date/time or bounded review window;
- responsible review-planning Responsibility Version;
- Actor or exact governed mechanism that established/changed it;
- Responsibility Assignment Basis and, when the point is a Decision condition, the applicable
  Decision Authority/Authorization Basis;
- rationale only when it carries substantive meaning;
- source/basis, including prior review/Decision/Learning where applicable;
- effective time, recorded time, and optional knowledge cutoff;
- predecessor, change, supersession, cancellation, completion/acknowledgment, and reason; and
- exact review Trigger/Work/Reassessment relationship when later created.

For one exact Case/Decision/Configuration/purpose and time, selection returns one eligible point,
absence, or explicit conflict. The target does not require every Case to have a planned point.

## Who may establish or change a plan

Planning review is an exact Responsibility. The assigned Actor may set or move the next planned
point within the limits of the Responsibility Assignment Basis and all governing constraints.
Case Coordinator orientation alone is insufficient.

When a review date is itself a substantive Decision condition or Boundary clause, changing it
requires the authority and successor/amendment path required to change that condition. A planning
Responsibility cannot silently amend a Decision. A practitioner may choose an earlier point where
all constraints permit; choosing a later point cannot waive a requirement.

## Required Review Constraint

A **required review** is not a stricter flavor of practitioner plan. It comes from an applicable
governing source such as:

- policy or Authority;
- contract or external requirement;
- authorized Decision condition;
- Integrated Operating Boundary clause; or
- another exact organizational rule.

The minimum normalized constraint preserves:

- stable identity and immutable Version;
- exact source Record Version and Authority/provenance;
- exact Case, Decision, Configuration, and affected scope;
- exact Applicability determination and limitations;
- temporal operator: `BY`, `NOT_BEFORE`, or `WINDOW`;
- date/time or window endpoints and timezone;
- effective/recorded interval;
- predecessor, correction, supersession, withdrawal, and history; and
- any exact accountable interpretation required to normalize a narrative source.

A source document's presence does not establish Applicability. A normalized constraint does not
create broader Authority than its source.

## Combining multiple requirements

All applicable constraints remain visible and are conjoined mechanically:

- multiple `BY` constraints produce the intersection ending at the earliest deadline, while every
  source remains retained;
- `NOT_BEFORE` and `BY` constraints define an allowed window when compatible;
- explicit windows are intersected with all other constraints; and
- an empty or indeterminate intersection returns
  `REQUIRED REVIEW TIMING CONFLICT — UNRESOLVED`.

This is constraint intersection, not a strongest-source or recency winner. Scope differences remain
separate. A human determination may be required when narrative requirements cannot be normalized;
PAIM cannot invent a safe date.

The read composition may say `Next planned review: November 30` and
`Review required by: December 31`, but it retains every exact source and conflict underneath.

## Plan compliance and changing context

A planned point is compliant only when it lies within every applicable required window for the
same scope. An earlier point satisfies a `BY` constraint unless another applicable constraint
prohibits it. A noncompliant plan remains recorded and visible; PAIM does not silently replace it.

If the governing Decision, Configuration, use, or review purpose changes before the point:

- the old Review Point remains bound to its original context;
- current selection re-evaluates its eligibility;
- an accountable or explicitly pre-authorized rule appends cancellation/supersession when its
  context becomes obsolete;
- a successor point, if needed, binds the new exact context; and
- required constraints are independently re-evaluated for Applicability.

No Review Point silently retargets to a successor Decision. A required source is not cancelled
merely because the practitioner plan changed.

## Arrival is attention, not conclusion

When a point arrives, PAIM must not infer:

- Evidence expiration or staleness;
- material change;
- Trigger existence before the practitioner establishes review;
- need for full Reassessment;
- Decision invalidity;
- operating suspension;
- priority among Cases or Work;
- continue/adjust/stop outcome; or
- compliance violation merely because a planned point was missed.

Missing a **required** review may create an explicit unsatisfied requirement or governing concern
according to its source contract, but the calendar still does not decide the operational response.

## Focused review and legitimate carry-forward

Review begins by identifying what changed, what was learned, and which exact basis may be affected.
Unaffected exact current state may be carried forward only after its normal currentness,
Applicability, and scope guards continue to pass. Carry-forward is continued reliance on the same
Version, not copying it into a new review package.

Possible accountable Trigger Determination outcomes remain:

- informational/no substantive follow-up;
- monitoring;
- focused analytical refresh;
- formal Reassessment; or
- immediate disposition plus Reassessment.

Focused refresh may create Value-only, Risk-only, Evidence, Authority, Configuration,
Intervention, or Learning work. If both analytical lanes are affected they remain independent. A
changed management position requires Decision Confirmation or an authorized successor path under
the governing contracts; review Work never changes it automatically.

## Realized Value and Risk symmetry

Every continuing review should ask independently:

- whether expected Value is being realized, through the expected pathway and conditions; and
- whether Risk, controls, boundaries, and adverse pathways are behaving as expected.

Failure to realize Value can justify review even when Risk remains within tolerance. Greater Value
does not erase increased Risk. The review model preserves two Inputs, two Fitness/acceptance paths,
and no combined score or automatic disposition.

## Learning horizons

Different questions mature at different times. Task efficiency might be interpretable after 30
days while end-to-end business Value needs 90 days. The smallest initial model does not create a
schedule for each metric. It uses:

- one Case/Decision-level next Review Point for the current management position; and
- bounded target/due or observation-period facts on existing Learning Items, Evidence-generation
  work, or durable Work when separately justified.

Those due points may generate attention and contribute information at the next review. They do not
become automatic assessment outcomes or review requirements without an applicable source.

## Review completion and the next point

A review episode preserves its exact source Trigger/Review Point, information considered,
determination, focused work or Reassessment, accountable Actor, effective/recorded time, and
Decision outcome relationship. It may establish the next planned Review Point in the same
practitioner confirmation only if both facts are separately validated and committed atomically.

The resulting Decision may remain unchanged through exact Confirmation or change through an
authorized successor. Confirmation uses the separately valid accountability and authority path
required by the governing contract. Learning completion alone does neither.

## Non-goals

No scheduler, reminder service, universal cadence, review-frequency field, automatic Trigger,
automatic Reassessment, automatic Decision, metric calendar, notification system, or UI is
introduced by this design.
