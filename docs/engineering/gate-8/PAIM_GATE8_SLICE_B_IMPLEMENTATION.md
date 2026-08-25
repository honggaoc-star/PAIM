# Gate 8 Slice B — Continuing Case Implementation Boundary

## Supported prospective behavior

Slice B adds prospective Case continuity under the accepted Gate-3 contract. A natural
`open_case` command atomically creates one bounded Case, its initial Managed Configuration and
governing designation, the initial `OPEN` continuity Version, and the exact continuity
Responsibility, assignment, Assignment Basis, semantic metadata, audit, and replay facts needed to
manage it. The only stored prospective continuity statuses are `OPEN`, `CLOSED`, and
`SUPERSEDED`.

Accountable commands support closure, reopening, supersession with one named successor,
`NEW_CASE_REQUIRED` routing, and same-Case Configuration succession. They revalidate software
access, one exact current status, Responsibility, assignment, substantive authority source,
context, expected Versions, and available-family guards inside the outer semantic transaction.
Failure appends no authoritative fact. A successor Configuration never retargets historical Work,
Responsibility, or other exact-context sources.

## Practitioner read boundary

`PractitionerQueryService` composes non-authoritative immutable Home, Case, and Task values from an
access-filtered prospective source population:

- Home returns unranked visible Responsibility vacancy/conflict/assignment and durable Work
  attention relevant to the Actor;
- Case returns exact Case continuity, governing Configuration one/absence/conflict,
  Responsibility/Work position, and a source manifest; and
- Task returns one exact current Work/Responsibility context, ordinary-language question,
  consequence, return path, permitted action, and the access/Responsibility/authority boundary.

The compositions persist no master Case position and reconstruct entirely from authoritative
facts after restart. Hidden Cases are removed before aggregation, so they cannot affect visible
counts, conflicts, ordering, relationships, participants, attention, or manifests.

## Schema and migration

Alembic head `0011_gate8_case_continuity` is additive after
`0010_gate8_responsibility_work`. It adds immutable projections for continuity status,
determination, explicit Case relationships, and same-Case Configuration lineage, with exact FKs,
controlled-value checks, selection indexes, and append-only triggers. It performs no prospective
backfill. Downgrade is refused after any Slice-B fact exists.

Legacy lifecycle phases remain exact legacy history behind a bounded read adapter. They are never
mapped to prospective continuity status and a failed prospective command never falls back to a
legacy transition.

## Explicit limits

Slice B composes only common semantics, Responsibility, Work, Case, and Configuration sources. It
does not implement or infer Slice-C+ assessment adequacy/reliance, prospective Decision,
continuing review/timing, quantitative claims, complete then-versus-now views, scheduler or
notifications, multi-user deployment, analytics/Observation/telemetry, Harborlight runtime
mutation, or release readiness.
