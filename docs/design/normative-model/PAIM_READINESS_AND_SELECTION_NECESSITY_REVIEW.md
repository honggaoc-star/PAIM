# PAIM Readiness & Selection Necessity Review

## Purpose and current baseline

This review asks which existing transitions are genuine practitioner acts and which engineering
operations can be absorbed without semantic loss. It does not change the current
[Value-Risk Interface Specification](../../system/specifications/PAIM_VALUE_RISK_INTERFACE_SPEC_v0.1.md)
or implementation.

The current contract correctly separates:

- analytical Input content;
- producer-declared `ready`;
- lane Fitness for exact information/use;
- use-specific Acceptance/Selection;
- global freeze of the exact accepted Input Version; and
- Decision.

The redesign should simplify interaction, not collapse these meanings.

## Decision summary

| Concept | Normative recommendation | Practitioner action |
|---|---|---|
| Value/Risk analytical readiness | Retain as attributed event over one exact candidate Version | `Finish Value assessment` / `Finish Risk assessment` |
| Case `READY_FOR_INTEGRATION` | Treat prospectively as derived current-position/readiness composition, not a practitioner-maintained Case phase | no separate action |
| Work `READY` | Derive from exact prerequisites for ordinary work; durable coordination state only when a Work Item exists | show `Ready to…` meaning |
| Fitness | Retain as independent accountable support judgment | `Review whether this assessment is supportable for this use` |
| Input Acceptance/Selection | Retain explicit use acceptance; simplify one-candidate interaction but never auto-select | `Accept this assessment for…` or explicit choice |
| Decision | Remains separate and separately authorized | proposal and authorization actions |

## Why analytical readiness is genuine

Readiness means the producer states that an exact Input is complete enough to leave drafting and
enter independent support/use review. It answers a real question that Fitness cannot answer:

> Is this the analytical position the producer is prepared to submit, with its Finding, Boundary,
> uncertainty, Implication, and provenance intact?

The assertion must remain attributable because another practitioner should not silently decide
that unfinished analysis is ready. It must be reconstructable because later review should know
which exact content the producer submitted.

## Recommended readiness contract

The future contract should preserve:

- exact Value or Risk Input ID/Version;
- readiness outcome and effective/recorded time;
- producing Assessor Responsibility Version;
- Actor and rationale only where substantively useful;
- exact completeness/structural guards;
- predecessor/correction/supersession history; and
- later status relationship without rewriting the event.

The practitioner action is **Finish assessment**, not `set status ready`. One semantic transaction
may finalize the candidate Input Version and append the readiness event. The UI absorbs IDs,
status-event construction, currentness checks, and return routing.

A material content edit after readiness creates a successor candidate Input Version. The earlier
Version and readiness event remain historical; the successor is not ready until its producer
finishes it. A non-substantive correction follows the common correction contract. Readiness does
not freeze the Input for Decision reliance, establish Fitness, accept it, or create authority.

## Analogous readiness transitions

- **Case readiness:** the current `READY_FOR_INTEGRATION` state is a composition of exact selected
  Value/Risk Inputs, Configuration, Evidence/Applicability/Fitness, Authority Gaps, and guards. In
  the target continuing Case model it should be derived rather than a user-maintained Case phase.
- **Work readiness:** for derived work it is always computed. For durable Work, `READY` is a
  coordination state backed by exact prerequisites and revalidated at commit; it is not a
  substantive domain judgment.
- **Integration completion, Intervention Completion Result, Reassessment readiness for authority,
  and other family states:** each retains its existing family-specific substantive meaning. They
  must be reviewed in their own specification and not renamed or deleted through a generic rule.

No cross-domain universal `ready` concept is proposed.

## Why Fitness remains separate

Fitness judges whether the exact Input and its material information basis are supportable for the
declared lane, Configuration, bounded use/purpose, and limitations. The producer's readiness cannot
make Evidence applicable or answer that accountable support question. A favorable Fitness outcome
does not select the Input and cannot be inferred from one available candidate.

## Selection is really use acceptance

The current combined `Acceptance/Selection` family performs two connected functions:

1. accountable acceptance of an exact Input for an exact bounded use; and
2. selection among candidate Inputs when more than one is materially eligible.

The first function exists even when there is only one candidate. The act freezes the exact Input
for reliance, binds Fitness and material Applicability, establishes the use/purpose, and records
accountability and history. Uniqueness alone cannot supply consent to rely on it.

The future specification should use the practitioner concept **Input use acceptance** while
retaining explicit selection semantics where competing candidates exist. Renaming must be
prospective; legacy Acceptance/Selection records retain their original name and meaning.

## Multiple supportable candidates

When two or more current candidates are supportable for the same lane/use:

- explicit accountable choice is mandatory;
- the practitioner reviews each exact candidate's Finding, Boundary, uncertainty, Implication,
  Fitness, and relevant provenance;
- one accepted candidate and material non-selected/dissenting/rejected dispositions are recorded;
- no newest, strongest, broadest, owner, row-order, or software winner exists; and
- incompatible co-current acceptances produce explicit conflict.

The choice remains independent in Value and Risk. It is not the management Decision.

## One supportable candidate

One candidate does not authorize automatic selection. The smallest legitimate action is an
explicit confirmation:

> Accept this exact assessment for this bounded use, with these limitations and consequences.

The interaction may be combined with Fitness completion only when:

- exactly one candidate remains for the exact lane/Configuration/use/purpose;
- the Fitness outcome is supportable under the current contract;
- the same Actor has separately valid Fitness and Input-acceptance Responsibilities;
- the confirmation shows both genuine judgments and the freeze/reliance consequence;
- both authoritative records retain separate identity, basis, attribution, and time;
- all currentness, Applicability, scope, and conflict guards pass atomically; and
- failure creates neither record.

If the responsibilities differ, Fitness is non-supportable/indeterminate, the candidate set is
materially plural, or any guard is unresolved, the acts remain separate. No governing rule makes
uniqueness sufficient by itself.

## Reuse

Reuse of a frozen historical Input requires a new explicit use acceptance with current
Configuration/use, Fitness, material Applicability, accountability, rationale, and time. Prior
acceptance is provenance only. Absence of `refresh required` or the existence of one frozen Input
does not establish reuse.

## Product presentation

Ordinary UI should expose:

- the assessment content the practitioner is finishing;
- whether support review is needed and why;
- the exact candidate choice only when genuine alternatives exist;
- the limitations and consequence of accepting for use; and
- vacancy, conflict, stale context, or non-supportable result in practitioner language.

It should not expose status-event machinery, freeze commands, compatibility keys, current-selection
algorithms, UUID assembly, or separate steps merely because persistence uses them.

## History and migration

Existing ready, Fitness, Acceptance/Selection, freeze, rejection, withdrawal, refresh, and
supersession facts remain valid. No legacy event is combined retroactively. Prospective UI
composition may present old records in the new practitioner language while retaining exact source
identity and the original semantics in history.

## Hard boundaries

- Readiness is not Fitness.
- Fitness is not Input use acceptance.
- Input use acceptance is not Decision.
- Value and Risk are never jointly accepted.
- One candidate is not an automatic winner.
- UI simplification never drops accountability, exact use, freeze, or historical basis.
