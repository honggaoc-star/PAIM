# PAIM Quantitative Value & Risk Normative Concept

## Purpose and boundary

This document defines the prospective capability for preserving quantifiable Value and Risk where
the available information and method make quantification meaningful. It does not require a number,
rating, probability, monetary amount, common scale, or calculation for every assessment. A bounded
qualitative conclusion, including that no defensible quantitative estimate is currently available,
is a legitimate analytical result.

This is semantic design only. Current [system specifications](../../system/specifications/) remain
controlling. No schema, analytics, UI, RWR calculation, scoring, ranking, or automated Decision rule
is introduced.

## Core principle

> Preserve meaningful quantities with enough context to remain interpretable and auditable; never
> manufacture a number or false precision.

Value and Risk retain independent Inputs, methods, uncertainty, accountability, history, and
reliance. Quantitative content may inform their later Integration, but PAIM never normalizes the two
lanes onto a universal scale, subtracts Risk from Value, or computes a net recommendation.

## Typed quantitative claims

The target contract must distinguish at least these meanings:

| Claim type | Meaning | Required semantic boundary |
|---|---|---|
| Estimate / expectation | A projected or modeled quantity under named assumptions | not an observed result or target |
| Target / objective | An outcome the organization seeks | not Evidence that the outcome will occur or has occurred |
| Observed result | A quantity observed for a bounded population and period | not automatic causal attribution to the AI use |
| Threshold / constraint | A legitimately established level that may require review or action | not a prediction; requires its exact governing source, scope, Applicability, and consequence |
| Risk estimate | A defensible likelihood/frequency, impact/exposure, affected-population, loss-range, control-performance, incident-rate, or other bounded Risk quantity | not a universal probability-times-impact score or statement of acceptable Risk |
| Cost/resource measure | Implementation, review, operating, training, capacity, or other bounded cost/resource quantity relevant to Value | not an automatic ROI or net-Value calculation |

One claim can cite relationships to another type, but their identities and meanings remain separate.
A target can be compared with an observation only after exact comparability is established; it does
not become Evidence merely because it is numeric. An estimate that later receives an observation is
not rewritten into the observation.

## Smallest rigorous claim context

A quantitative claim preserves the smallest context necessary for its particular meaning. The core
is:

- claim type and measure/construct;
- value, range, distribution, or bounded qualitative-plus-quantitative representation;
- unit when a numeric representation has one;
- exact Value or Risk lane and owning Input/Information/Learning context;
- Configuration, purpose/use, scope/population, source/provenance, and effective/recorded time;
- uncertainty and material limitations; and
- the exact relationships needed to reconstruct what the claim supported.

Where material to interpretation, it also preserves direction, estimate/observation period,
comparator or baseline, sample/coverage basis, and method/assumptions. A threshold additionally
preserves the exact governing source, Applicability, operator, scope, and authorized consequence. A
missing field is not filled by assumption: either it is inapplicable, explicitly unknown, or a
material limitation affecting adequacy.

This is a normative record contract, not a mandatory long-form questionnaire. Practitioner
interaction should ask natural questions, carry already established context, and request only the
missing material context for the claim at hand.

## Value capability

A Value assessment may preserve expected and realized benefits in bounded measures such as time,
cost, capacity, throughput, revenue, quality/error outcomes, or customer/business outcomes. It may
combine qualitative and quantitative reasoning. PAIM does not require Value to be monetary, does
not treat ROI as the canonical representation, and does not infer that a larger number is more
valuable across different scopes or constructs.

Material costs/resources remain separately identifiable from benefits so the Value assessor can
judge whether expected or realized benefit remains meaningful. PAIM may reproduce a calculation
made under a separately accepted exact method, but does not automatically calculate universal ROI,
net Value, or a ranking.

## Risk capability

A Risk assessment may preserve defensible likelihood/frequency ranges, impact/exposure, affected
population, loss ranges, control performance, incident rates, or another bounded measure. It may
also state that likelihood or impact cannot currently be estimated reliably. Absence of a number is
not incompleteness when quantification is not reasonably supportable.

PAIM does not require probability × impact, ordinal heat-map multiplication, one generic Risk
score, or a conversion that conceals uncertainty, affected parties, controls, or scope. A quantified
Risk does not establish that the Risk is acceptable.

## Relationship to information and assessment adequacy

The presence of a number never establishes Evidence Applicability, assessment adequacy,
materiality, Value, acceptable Risk, causality, Decision, review priority, or authority. Exact
information and Applicability remain independently governed.

Neutral assessment-adequacy review evaluates quantitative content as part of the exact assessment.
A material number may make the assessment not adequate for decision use when it is unsupported,
falsely precise, exaggerated or understated, inappropriately generalized, missing a necessary
scope/comparator/period, or obscures material uncertainty. Conversely, lack of quantification does
not make an assessment inadequate when a defensible quantity is unavailable or immaterial. The
reviewer evaluates the assessment; the reviewer is not required to manufacture a number or support
the proposed AI use.

## Expectation-versus-experience review

Where exact comparability is established, continuing review may compare:

- expected Value with realized Value;
- expected Risk/control behavior with observed experience;
- estimated cost/resource use with observed cost/resource use; and
- targets or thresholds with observations.

Matching labels or units are insufficient. The comparison preserves and checks exact construct,
scope/population, method, period, baseline/comparator, Configuration, provenance, and Applicability.
When those differ materially, PAIM presents the claims separately or records the accountable
comparability limitation; it does not silently normalize them.

Prediction/estimate error is not automatically Decision error. Later observations remain later
knowledge and do not rewrite whether the estimate, adequacy review, reliance, or Decision was
reasonable on the information available at the time. An observed result also does not establish
causal attribution to the AI use without a separately adequate method and evidence basis.

## Timing and learning

Measures mature on different horizons. The initial target does not create a separate schedule for
every metric. Case/Decision-level next review plus bounded due or expected points on Learning,
Information, and Work are sufficient unless a separately applicable requirement establishes a
specific constraint.

Typed claims and exact context should support later, separately authorized retrospective analysis
of expected versus observed Value/Risk within and across Cases. Such analysis must remain
access-filtered, context-preserving, and non-causal/non-authoritative unless a separate accepted
method establishes otherwise. This proposal implements no analytics.

## Hard boundaries

- Quantification is optional where meaningful, never forced.
- Target is not Evidence; estimate is not observation; observation is not causation; threshold is
  not prediction; measure is not management judgment.
- No quantity creates Applicability, adequacy, materiality, authority, priority, or Decision.
- Value and Risk quantities remain independent and are never reduced to a universal or net score.
- Qualitative uncertainty and inability to estimate remain first-class analytical results.
- Exact context and later knowledge are preserved; history is never rewritten by outcomes.
