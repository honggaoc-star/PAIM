# PAIM Assessment Adequacy & Reliance Necessity Review

## Purpose and current baseline

This review asks which existing Value/Risk transitions are genuine practitioner acts and which
engineering operations can be absorbed without semantic loss. It does not change the current
[Value-Risk Interface Specification](../../system/specifications/PAIM_VALUE_RISK_INTERFACE_SPEC_v0.1.md)
or implementation.

The current contract correctly separates analytical Input content, producer-declared `ready`,
lane Fitness, use-specific Acceptance/Selection, global freeze of the accepted Input Version, and
Decision. The prospective model preserves the necessary guarantees but reframes the independent
review neutrally: it is not support for a favorable Value case or proposed AI use.

## Decision summary

| Concept | Prospective normative recommendation | Practitioner action |
|---|---|---|
| Value/Risk analytical readiness | Retain as attributed event over one exact candidate Version | `Finish Value assessment` / `Finish Risk assessment` |
| Case `READY_FOR_INTEGRATION` | Derive from exact current prerequisites; do not maintain as a Case phase | no separate action |
| Work `READY` | Derive for ordinary work; persist only when durable coordination is required | show `Ready to…` meaning |
| Assessment adequacy for decision use | Prospectively replace Fitness as the neutral accountable judgment over one exact assessment, information basis, bounded use, and limitations | `Review whether this assessment is adequate for the management decision` |
| Reliance designation / competing-candidate choice | Retain an exact reliance fact; require explicit accountable choice when adequate candidates compete | normally part of `Complete Value review` / `Complete Risk review`; explicit choice when alternatives exist |
| Decision | Remain separate and separately authorized | proposal and authorization actions |

## Why analytical readiness is genuine

Readiness means the producer states that an exact Input is complete enough to leave drafting and
enter independent adequacy/use review:

> Is this the analytical position the producer is prepared to submit, with its Finding, Boundary,
> uncertainty, Implication, and provenance intact?

The attributed event preserves the exact Input ID/Version, producing Assessor Responsibility,
effective and recorded time, structural guards, and predecessor/correction/supersession history.
The practitioner action is **Finish assessment**, not `set status ready`. A material edit creates a
successor candidate; it does not rewrite or inherit the predecessor's readiness. Readiness does not
establish adequacy, reliance, Applicability, or authority.

## Neutral assessment adequacy

The independent reviewer asks:

> **Is this assessment adequate for use in the management decision?**

This is a quality-and-boundedness judgment about the exact Value or Risk assessment, not advocacy
for its conclusion. An assessment that finds small or highly uncertain Value can be adequate. An
assessment that finds substantial Risk can be adequate. Adequacy therefore never means that the
AI use is desirable, that the Case is supported, that Value outweighs Risk, or that a Decision
should proceed.

The reviewer considers, in context and with professional judgment, whether the assessment is
materially faithful to available information, complete enough on material considerations,
proportionate rather than exaggerated or understated, appropriate to its stated scope/use, and
transparent about material limitations and uncertainty. These are considerations, not a
mechanical checklist or a claim of objective proof.

A useful defensive formulation is: **Is there a material reason this exact assessment should not
be used as an input for this bounded management decision?** Such a reason may include material
inaccuracy, exaggeration or understatement, incompleteness, inappropriate scope, or concealed
uncertainty. The reviewer records the exact information/use basis, rationale, and material
limitations rather than merely asserting a favorable label.

## Smallest rigorous outcome model

The prospective authoritative outcome needs only three values:

- `ADEQUATE_FOR_DECISION_USE` — no identified material reason prevents this exact assessment from
  entering the stated decision process;
- `NOT_ADEQUATE_FOR_DECISION_USE` — an identified material reason currently prevents that use; and
- `INDETERMINATE` — available governing information/context does not permit the accountable
  judgment.

Material limitations remain explicit alongside any outcome. Thus practitioner wording may say
**adequate with limitations** without inventing a fourth authoritative state. “Additional work
needed” is a practitioner explanation of a remediable `NOT_ADEQUATE_FOR_DECISION_USE` result, not a
different quality verdict. This model preserves uncertainty and remediation without pretending
that the considerations are mechanically measurable.

The exact assessment Version, lane, Configuration, bounded use/purpose, assessed scope,
information/Applicability basis, reviewer Responsibility, Actor, effective/recorded time,
limitations, rationale, and predecessor/correction history remain authoritative.

## Distinct from Evidence Applicability

Evidence Applicability asks whether an exact item is relevant and usable for an exact target,
purpose, and assessed scope. Assessment adequacy asks whether the resulting assessment as a whole
is sufficiently faithful, complete, proportionate, scoped, and transparent to enter the decision
process. Exact Applicability judgments and the assessment's information basis can support the
adequacy review, but cannot answer it automatically. Adequacy cannot create or alter
Applicability.

Adequacy also does not select an assessment, freeze it for reliance, grant authority, compare
Value with Risk, or establish the management Decision.

## What existing Fitness guarantees remain necessary

The prospective concept retains the existing requirements for exact Input and use binding,
material information/Applicability basis, independent Value/Risk lanes, accountable attribution,
explicit limitations and rationale, currentness/conflict guards, dual-time history, and no
inference from readiness or uniqueness. It reframes the judgment from “supportable” Fitness to
neutral adequacy and replaces outcome vocabulary prospectively.

Legacy Fitness records keep their original names, outcomes, and semantics. They may be displayed
with an explanation of their historical contract, but are never relabeled as new adequacy facts or
reinterpreted retroactively.

## Adequacy establishes eligibility; reliance remains consequential

Adequacy establishes that an exact assessment is eligible to enter the management decision
process. A separate reliance designation still has independent management meaning because it:

- names the exact assessment the Case will use for one exact lane/use;
- freezes that exact Version and its adequacy and material Applicability basis for reconstruction;
- records the accountable act and time at which reliance began; and
- records non-selected/dissenting/rejected candidate dispositions when alternatives exist.

It is not retained merely because the current architecture has Acceptance/Selection. Without the
reliance fact, adequacy alone would silently turn eligibility into current use and would not answer
which exact Version controlled Integration and Decision history.

## One-candidate alternatives evaluated

| Alternative | Evaluation |
|---|---|
| Adequacy followed by a separately presented reliance action | Semantically safe and required when the responsible Actors differ or a separate choice remains, but needlessly exposes two system-shaped steps when one Actor can make both judgments together. |
| One natural confirmation with separate adequacy and reliance facts | **Recommended.** It preserves the independent quality and reliance meanings, accountability, exact freeze, and history while presenting the practitioner consequence once. |
| Derive or absorb reliance when only one adequate candidate exists | Rejected. Adequacy establishes eligibility, while reliance establishes actual bounded use and the frozen historical basis. Candidate count cannot supply that accountable act. |

This conclusion is based on the independent meaning of reliance, not on preserving the current
Acceptance/Selection architecture for its own sake.

## Multiple adequate candidates

When two or more current candidates are adequate for the same lane/use, explicit accountable
choice is mandatory. The practitioner reviews each exact candidate's Finding, Boundary,
uncertainty, Implication, adequacy basis, limitations, and provenance. The system records one
relied-on candidate and material candidate dispositions. No newest, strongest, broadest, owner,
row-order, score, or software winner exists; incompatible co-current reliance designations produce
explicit conflict. Value and Risk choices remain independent and are not the Decision.

## Exactly one adequate candidate

Uniqueness never supplies a reliance judgment automatically. However, exposing two consecutive
system operations adds no practitioner value when one natural accountable confirmation can state
both genuine consequences. The preferred prospective action is **Complete Value review** or
**Complete Risk review**, with confirmation such as:

> You are concluding that this assessment is adequate for the stated decision use and, because no
> separate candidate choice is required, designating this exact assessment as the one this Case
> will use for that lane. Its recorded limitations remain part of the decision basis.

One interaction may atomically commit separate adequacy and reliance facts only when exactly one
candidate is adequate for the exact lane/Configuration/use, the same Actor holds separately valid
adequacy-review and reliance Responsibilities, the confirmation exposes both consequences, all
Applicability/currentness/scope/conflict guards pass, and failure creates neither fact. The facts
retain separate identity, exact basis, attribution, and time because later history must distinguish
quality eligibility from actual reliance.

If Responsibilities differ, the outcome is not adequate or is indeterminate, alternatives compete,
or any guard is unresolved, the acts remain separate. The product asks for explicit choice only
when there is a real choice and never derives reliance from candidate count.

## Reuse

Reuse of a historical frozen assessment requires current adequacy and a new explicit reliance
designation for the exact Configuration/use, material Applicability basis, accountability,
limitations, rationale, and time. Prior Fitness, adequacy, Acceptance/Selection, or reliance is
provenance only. Absence of `refresh required` and uniqueness do not establish current reuse.

## Product presentation

Ordinary UI should expose the assessment content, neutral adequacy question, material limitations,
exact choice only when alternatives genuinely exist, reliance consequence, and any vacancy,
conflict, stale context, or adverse/indeterminate outcome in ordinary language. It should normally
offer **Complete Value review** or **Complete Risk review**, not `Fitness`, `Selection`, `freeze`,
compatibility keys, status events, or current-selection algorithms.

## History and hard boundaries

Existing readiness, Fitness, Acceptance/Selection, freeze, rejection, withdrawal, refresh, and
supersession facts remain valid in their original semantic era. No missing fact is synthesized and
no legacy event is combined or renamed retroactively.

- Readiness is not assessment adequacy.
- Assessment adequacy is not Evidence Applicability.
- Adequacy/eligibility is not reliance designation.
- Reliance designation is not Decision.
- Adequacy is neutral to favorable or unfavorable Value/Risk conclusions.
- Value and Risk are never jointly reviewed or designated for reliance.
- One candidate is not an automatic winner.
- UI composition never drops accountability, exact use, limitations, freeze, or historical basis.
