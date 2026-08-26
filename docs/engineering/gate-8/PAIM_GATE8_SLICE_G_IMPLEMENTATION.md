# Gate 8 Slice G — Then-versus-now reconstruction and Decision audit

## Implemented boundary

Slice G adds a non-authoritative reconstruction service over the existing exact Version graph. It
does not persist a management position, historical snapshot, audit narrative, timeline, change
result, master status, or duplicate Decision truth. An ordinary governed command remains the only
way to create authoritative PAIM facts.

The service supports explicit effective-time and knowledge-time cutoffs for:

- an exact authorized Decision-time position;
- a current Case management position;
- a mechanical then-versus-now comparison;
- a derived Decision-audit narrative;
- a deterministic, dual-time-aware visible Case timeline; and
- one composition suitable for a later History / What changed? practitioner view.

## Exact Decision-bound reconstruction

Decision-time reconstruction begins with one exact authorized prospective Decision Version. It
follows that Decision's exact authorization, Integration, governing Configuration, independent
Value and Risk assessment/readiness/adequacy/reliance chains, information/Applicability bases,
Responsibility, Assignment, Assignment Basis, assignment-authority source, substantive authority,
exact context, and safely knowable review/quantitative facts at the requested cutoff. Current
selectors never replace a bound historical Version on the “then” side.

A source recorded after the requested knowledge cutoff cannot enter that historical position. An
internally incomplete bound graph returns an explicit reconstruction problem. A hidden required
source returns no bounded content or source manifest; it is never translated into absence,
conflict, a change indicator, a date, a count, or a suggestive placeholder.

## Current composition and comparison

The current position uses common record/scope selection and the accepted prospective selectors.
It first resolves the independent current relied Value and Risk bases, then recognizes only an
Integration bound to both exact bases and only an authorized Decision bound to that Integration.
Preserved stale Integrations and Decisions therefore remain historical evidence without becoming
current conflicts. True lane absence and explicit lane conflict remain distinct states.
Independent records that legitimately coexist—such as Required Review Constraints, quantitative
claims, Responsibilities, and Work—are selected per stable Record. Integration and Decision
conflicts remain explicit scope-level conflicts. Responsibility/Work appears only when linked to
the reconstructed management basis; unrelated obligations are not pulled into the audit view.

Comparison is exact-identity comparison only. It may state that a Configuration, Value basis, Risk
basis, Integration, Decision, review basis, quantitative basis, or linked Responsibility/Work basis
changed. It never says the later state is better or worse, attributes cause, judges Decision
quality, requires a successor Decision, nets Value and Risk, or creates retrospective attention.
Optional quantitative history includes explicit comparability Versions; numeric differences remain
governed by the Slice-F comparison contract. A differing quantitative source set is not reported
as a quantitative change unless an explicit visible Slice-F comparability basis is established.

## Timeline, narrative, and provenance

Every returned section carries exact visible Record/Version family and dual-time provenance.
Timeline ordering is deterministic by effective time, recorded time, and Version identity. A
hidden item is omitted together with its entire source closure and leaves no redacted row or global
count. The practitioner narrative uses only visible Decision content and exact accountable and
authority sources. It carries the Decision effective/recorded times, exact Responsibility,
Assignment, Assignment Basis, authority, Integration, relied lanes, visible successor, subsequent
change, and continuing-review provenance. Missing rationale is not invented.

Legacy history is neither backfilled nor reinterpreted. Prospective reconstruction does not fall
back to legacy Acceptance/Fitness/Selection semantics. Harborlight is not mutated by Slice G.

## Persistence and measured query support

Migration `0016_gate8_reconstruction_support` is additive from
`0015_gate8_quantitative_claims`. It adds only
`ix_versions_reconstruction_cutoff(recorded_at_us, effective_from_us, record_id)`, supporting the
measured dual-time history scan. The migration adds no table, fact, backfill, snapshot, or summary
truth. Its downgrade removes only that index and cannot destroy authoritative history.

## Current limits

Slice G does not implement Slice-H integrated UI or Harborlight runtime validation, background
review scheduling, notifications, multi-user deployment, telemetry/Observation, analytics,
causality, quality scoring, mandatory quantification, Value-minus-Risk netting, or release work.
