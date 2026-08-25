# Gate 8 Slice E — Continuing Review and Review Timing

## Implemented boundary

Slice E adds prospective continuing-review capability to an already authorized Slice-D Decision.
It keeps four things separate: a practitioner-selected Planned Review Point, governing Required
Review Constraints, explicit event-based review attention, and the Review Episode that coordinates
the bounded review. A date or event can call for attention; neither creates an Assessment,
Adequacy, Reliance, Integration, or Decision conclusion.

Natural commands establish or succeed a plan, establish/succeed/withdraw an exact applicable
constraint, record an accepted event attention fact, begin a focused Review Episode, and complete
that Episode. Commands carry semantic metadata, exact context, Version history, Work/result links,
and audit facts through one outer transaction. Exact replay returns its original outcome. Mismatched
replay, stale predecessor, inaccessible source, accountability vacancy/conflict, or invalid
authority/basis fails with no partial semantic mutation.

Constraint withdrawal is a successor Version of the exact same Required Review Constraint Record;
the prior active Version remains historically reconstructable. A completed Review Episode records
an exact `ADDRESSED_EVENT_ORIGIN` link for each event-attention Version it actually originated from.
That link removes only the exact visible consumed event from current attention composition. It does
not delete the event, resolve unrelated events, infer resolution from time, or project a later
completion backward into an earlier knowledge-time view.

Review scope is explicit. A Value-only refresh does not refresh Risk, and vice versa. Prior facts
remain historical bases rather than being copied forward automatically. Completion requires
exactly one separately established Slice-D continuation path: an unchanged authorized-Decision
confirmation or an explicitly authorized successor Decision. Completing a Review Episode never
authorizes or changes a Decision by itself. An optional next Planned Review Point is committed
atomically with completion under its own planning Responsibility.

## Read composition and timing

Home and Case compose review position from exact visible source Versions; no authoritative master
Case status is persisted. Case composition may show the next planned point, the mechanically
intersected required window, an open focused review, the last visible completion, and ordinary
language attention reasons. Home shows review attention only when a visible plan is due, a visible
required window is due or conflicting, or an explicit visible governed event calls for review.
There is no ranking or inferred urgency.

Every exact source is access-filtered before dates, counts, conflicts, attention, or action context
are composed. If a visible composition depends on a hidden source, dates and detailed state are
withheld as status not safely available. Effective-time and knowledge-time selectors preserve the
plan, constraint, event, and Review Episode that was legitimately knowable at the requested cutoff;
later successors or completion results are never projected backward.

## Persistence and migration

Migration `0014_gate8_continuing_review` additively introduces append-only records/projections for:

- Planned Review Point Versions;
- Required Review Constraint Versions;
- explicit review-attention event Versions;
- Review Episode Versions and exact result links.

The migration replaces the Gate-7 `0014_gate7_continuing_review` placeholder. It supports fresh to
head and exact `0013_gate8_integration_decision_basis` to head, performs no prospective backfill,
and prohibits destructive downgrade after Slice-E facts exist. Foreign keys, checks, selection
indexes, append-only triggers, and foreign-key enforcement remain part of the migration oracle.

## Deliberate exclusions

Slice E does not implement a universal cadence, scheduler, notifications, polling, Observation,
telemetry, analytics monitoring, quantitative claims/comparison, a complete then-versus-now UI,
Harborlight runtime validation, multi-user deployment, or Slice F and later work.
