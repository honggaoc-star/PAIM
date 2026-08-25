# Gate 8 Slice F — Optional quantitative Value/Risk claims

## Implemented boundary

Slice F adds prospective, append-only Quantitative Claim Records/Versions and explicit
Comparability Records/Versions. Claims retain their exact Case, governing Configuration,
semantic context, Value or Risk lane, claim role, construct and metric, supplied decimal text,
representation, units and bases, time basis, population, method, provenance, Applicability,
uncertainty, limitations, accountability, and optional assessment or Review Episode link.

A correction remains one exact Claim Record only when its Case, Configuration, context, lane,
claim role, construct, metric, quantity semantics, unit/basis, population/denominator, time
basis/horizon, method, and optional assessment/review identity remain unchanged. The successor
may correct the supplied value, measurement period, sources, uncertainty, assumptions, or
limitations; it cannot silently repurpose the Record as a different claim.

The six controlled claim roles are estimate/expectation, target/objective, observed result,
threshold/constraint, Risk estimate, and cost/resource measure. Quantification remains optional.
An assessment, review, Integration, or Decision neither requires nor follows from a claim.

## Comparison boundary

The comparison service first rejects clear mechanical mismatches across exact context, lane,
construct/metric, quantity representation, unit/currency/scale, direction, population/base,
time basis/horizon, baseline, gross/net, nominal/real, and method. Passing those checks does not
establish substantive comparability. A practitioner with a current Responsibility, assignment,
and quantitative authority source must explicitly establish `COMPARABLE` or `NOT_COMPARABLE`.

Only an explicitly comparable scalar expected/target and observed pair receives exact Decimal
arithmetic, with the expectation/target on the left and observed result on the right so the
difference is always `observed - expected`. The selected Comparability Version is revalidated as
the exact oriented pair and governed context at the requested effective/known time. A zero
baseline suppresses ratio and percentage change. No comparison infers
causation, success, materiality, adequacy, reliance, Decision quality, priority, score, ranking,
or Value-minus-Risk netting.

## Access and practitioner composition

Claim authorization uses one complete read-side source closure before selection, comparison, or
practitioner composition. That closure includes the Claim Version, governing Configuration,
exact context Versions, explicit source and Applicability links, optional assessment and Review
Episode links, substantive claim authority, Responsibility, Assignment, Assignment Basis, and
the assignment-authority source. If any required source is malformed or hidden, the claim is not
safely available; absence remains distinct from non-disclosure. Hidden sources therefore do not
leak labels, counts, dates, deltas, comparison availability, or highlights. Practitioner
highlights are composed only from a population authorized over that full closure and expose
supplied meaning and caveats, not a scorecard or generic numeric alert.

## Persistence and compatibility

Migration `0015_gate8_quantitative_claims` is additive from
`0014_gate8_continuing_review`. It creates typed claim, exact basis-link, and comparability
tables with foreign keys, checks, indexes, and append-only triggers. It performs no prospective
backfill and refuses destructive downgrade after Slice-F facts exist. Legacy and Harborlight
records are not mutated. This slice does not claim Slice G reconstruction, Slice H integrated UI,
multi-user deployment, scheduler/notification behavior, or release readiness.
