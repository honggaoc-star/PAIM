# Gate 8 Slice C — Value/Risk Finish, Adequacy, and Reliance

## Supported prospective behavior

Slice C adds prospective, independent `VALUE` and `RISK` assessment-review lanes under the
accepted Gate-6 contract. `finish_assessment` is the natural lane action that atomically creates
one immutable prospective assessment candidate and its separately identified Readiness fact. It
requires one exact current `OPEN` Case, governing Configuration Version, semantic context,
information/Applicability manifest, lane Responsibility, eligible current assignment, and active
assignment-authority basis. Readiness means only that the exact assessment is ready for
independent review.

The neutral adequacy action records exactly one of `ADEQUATE`, `NOT_ADEQUATE`, or
`INDETERMINATE` for the exact assessment, Readiness, Configuration, bounded decision use, scope,
and information basis. Adequacy does not endorse the Case, accept Risk, designate actual use,
grant authority, or make a Decision.

Reliance is a separate accountable act. It designates one exact current assessment only when its
exact Adequacy outcome is `ADEQUATE`. Every other materially competing adequate candidate must
have an explicit disposition; no recency, magnitude, favorability, ownership, role, rank, score,
or row order supplies a winner. Incompatible co-current Reliance designations remain an explicit
conflict.

Where one Actor independently holds both exact Responsibilities, `complete_review` commits the
Adequacy and Reliance facts in one semantic transaction while retaining their separate identities
and bases. A guard failure creates neither fact. Where Actors differ, the two production actions
remain separate and existing durable Case Work coordinates the handoff.

## Currentness, history, and practitioner composition

All Slice-C writes use expected-Version, effective-time, knowledge-cutoff, semantic-context,
access, accountability, and replay guards. Corrections append explicit successor history. They do
not rewrite or retarget an earlier Readiness, Adequacy, or Reliance basis. Selectors discard a
designation whose exact assessment has become stale, preserve the earlier result for historical
reconstruction, and return one, absence, or conflict without an incidental winner.

`PractitionerQueryService` extends the access-filtered Home and Case compositions with separate
ordinary-language Value and Risk positions. Home exposes only visible, unranked lane work that is
actually due. Case reports assessment, readiness, adequacy, and reliance independently with exact
source manifests. The read composition follows authoritative Version selection and dependent-basis
currentness; it does not choose by record recency or fabricate prospective state from legacy
sources. Existing Task composition carries the substantive question, needed instruction,
consequence, return path, and the software-access/Responsibility/authority boundary from exact
durable Work.

## Schema and migration

Alembic head `0012_gate8_assessment_review` is additive after
`0011_gate8_case_continuity`. It adds separate record/Version projections for prospective
assessment candidates, Readiness, Adequacy, and Reliance. Exact foreign keys, lane/outcome checks,
selection indexes, and append-only update/delete triggers support the four authoritative families.
The migration performs no prospective backfill and refuses destructive downgrade after any Slice-C
fact exists.

Legacy Value/Risk Inputs, Fitness, Acceptance/Selection, Integration, and Decision records retain
their original names, meanings, identities, and histories. They are never copied, mapped, or used
as fallback prospective Readiness, Adequacy, or Reliance facts.

## Explicit limits

Slice C exposes the exact relied Value and Risk bases for a later consumer but does not implement
prospective Integration or Decision consumption. It also does not implement continuing review or
timing, quantitative claims/comparison, complete then-versus-now reconstruction, Harborlight
runtime mutation, scheduler/notifications, organization-local networking, analytics,
Observation/telemetry, later UI slices, or release work.
