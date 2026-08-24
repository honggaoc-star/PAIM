# PAIM Continuing Value-Risk & Decision Lifecycle

## Purpose and boundary

This companion to the [Product Design Foundation](PAIM_PRODUCT_DESIGN_FOUNDATION.md) describes the
practitioner model for continuing management. It does not add lifecycle states, records,
automatic Triggers, Observation semantics, telemetry, scores, or implementation behavior. The
authoritative contracts remain the
[Value-Risk Interface Specification](../../system/specifications/PAIM_VALUE_RISK_INTERFACE_SPEC_v0.1.md),
[Reassessment Specification](../../system/specifications/PAIM_REASSESSMENT_SPEC_v0.1.md), and other
[system specifications](../../system/specifications/).

The foundation adopts the RWR-derived continuing-review principle as product direction. PAIM does
not thereby implement Return-Weighted Risk, adopt an RWR calculation, or claim empirical
validation of RWR or PAIM.

## Foundational proposition

> A point-in-time Value-Risk assessment is not adequate for an AI-related business decision whose
> information, use, conditions, performance, and consequences continue to change.

PAIM should help an organization maintain a legitimate current position without pretending that
the original Decision is permanent or that every later change invalidates everything already
known.

## Practitioner cycle

```text
Consider
   -> Assess Value & Risk
   -> Decide
   -> Act
   -> Observe
   -> Learn / Review
   -> Continue / Adjust / Stop
   -> Observe ...
```

The cycle is deliberately not a one-way workflow. A Case may pause, revisit a narrower question,
continue under existing conditions, produce a successor Decision, or stop. Independent work may
proceed at different times. No arrow authorizes the next act, establishes responsibility, or
implies that PAIM may perform a management judgment automatically.

### Consider

Define the business question, bounded Configuration, intended use, plausible alternatives,
stakeholders, information needs, uncertainty, responsibility, and authority questions. A product
name or inventory entry is not a sufficient management object.

### Assess Value and Risk

Develop Value and Risk independently for the same bounded context. Each lane retains its own
information, Applicability, reasoning, Fitness, Selection, uncertainty, attribution, and history.
Shared evidence does not merge the lanes, and neither lane repairs absence or conflict in the
other.

### Decide

Bring exact current selected Value and Risk bases into Integration, establish the Boundary,
compare feasible alternatives, and make a separate accountable and authorized Decision. PAIM
does not calculate a universal correct answer.

### Act

Translate the Decision into explicit conditions, responsibilities, interventions, acceptances,
and activation or other authorized action where applicable. Software permission and assignment
do not substitute for substantive authority.

### Observe

Attend to what is happening in operation: realized Value, emerging or realized Risk, control
performance, use changes, boundary conditions, implementation outcomes, new information, and
external changes. This product concept does not imply that the current release has first-class
Observation persistence or continuous telemetry.

### Learn and review

Judge what later information means for the exact current Case and Decision. Learning informs
review but never changes a Decision automatically. Historical experience becomes available
information; current applicability, relevance, and sufficiency remain current judgments.

### Continue, adjust, or stop

An accountable review may confirm the existing Decision, require focused new work, produce an
authorized successor or amendment, narrow or suspend operation through an applicable governed
path, or lead to stopping. The product must preserve the prior legitimate position regardless of
the later outcome.

## Continuing an existing Case

When an organization returns to an existing Case, the ordinary sequence should be:

```text
operating experience or elapsed time
   -> identify changed or newly relevant information
   -> locate the affected current basis
   -> perform focused independent Value and/or Risk review
   -> confirm the current Decision or establish an authorized change
```

PAIM should carry forward exact state that remains legitimately current: Configuration,
applicable information, accepted analytical inputs, Boundary, Decision, conditions,
responsibilities, and unresolved questions. Carry-forward is not copying. It is continued reliance
on the same exact authoritative basis after the relevant currentness and applicability conditions
remain satisfied.

The practitioner should focus on what changed and why it matters. A new vendor version may affect
Risk without changing the intended Value pathway. Evidence of unrealized benefit may affect Value
without implying that a control failed. A change in authority can affect operation even when both
analytical lanes remain substantively unchanged. If both lanes require refresh, they remain
independent.

No mechanical full reassessment is required merely because review occurs. Conversely, a narrow
review must not be used to avoid reconsidering a materially affected basis.

## Event-driven and time-driven review

### Event-driven review

A potentially material occurrence may arise from operation, a provider, a control, a boundary
condition, new evidence, an Authority change, an Intervention result, Learning, or another
source. The event's existence, category, recency, or severity does not by itself establish that
reassessment is required. The supported governing path retains exact provenance and an explicit
accountable determination.

### Time-driven review

Elapsed time or a scheduled review point may prompt practitioners to ask whether the current
basis still holds. The schedule is an attention aid and expected reconsideration point, not proof
that information is stale, a Decision is invalid, or a full reassessment must occur. The review
may conclude that nothing material changed, that focused work is needed, or that a successor
Decision is required.

Time-driven review must preserve the same standards for exact identity, current basis,
accountability, authority, and history as event-driven review. This document does not add a
scheduled-review record or scheduler.

## Symmetry of realized Value and Risk

PAIM should make two continuing questions equally visible:

- Is the expected Value being realized, for whom, through the expected pathway, under the stated
  conditions and costs?
- What Risks are emerging or being realized, and are the required controls and boundaries still
  effective?

Realized Value can be absent, delayed, displaced, unevenly distributed, or attributable to a
different change. Risk can be absent, latent, controlled, emergent, or outside the observed
period. Neither favorable outcomes nor a lack of observed harm proves the original reasoning
sound. Neither disappointing outcomes nor realized harm proves it was unsound when made.

Value and Risk must not be combined into a net score, strongest-state rule, ranking, or automated
continue/stop recommendation. The accountable management Decision considers both without erasing
either.

## Current management position through the cycle

At any point, the product may compose a current position from exact authoritative sources:

- the use and governing Configuration;
- current Value and Risk positions;
- the current authorized Decision, rationale, Boundary, conditions, and alternatives;
- actions and obligations arising from the Decision;
- realized outcomes and later information that are actually recorded and visible;
- unresolved uncertainty, information, responsibility, authority, or conflict;
- the review basis and what currently needs attention.

This composition is a view, not a universal Case status or new truth record. If sources conflict,
the view shows conflict. If a fact is absent, it remains absent. If access filtering hides a
source, the composition must not leak its existence through labels, counts, or conclusions.

## Non-inference rules

The continuing lifecycle never permits PAIM to infer:

- current applicability from historical use;
- Value from the absence of observed Risk;
- acceptable Risk from realized Value;
- decision quality from outcome quality;
- a Trigger or materiality from telemetry or event similarity;
- review priority from severity, recency, breadth, role, or presentation;
- responsibility or authority from identity, access, ownership, or prior action;
- a changed Decision from completed Learning; or
- closure because work, notification, or review activity occurred.

## Product questions for later design

Separately bounded work may ask how practitioners:

- see the current position and the exact basis that changed;
- distinguish a review reminder from a substantive concern;
- record realized Value with discipline comparable to Risk;
- initiate focused Value, Risk, authority, boundary, or implementation review;
- compare the Decision-time Case with current knowledge; and
- carry learning into a future assessment without turning precedent into authority.

Those are design questions, not capabilities authorized by this document.
