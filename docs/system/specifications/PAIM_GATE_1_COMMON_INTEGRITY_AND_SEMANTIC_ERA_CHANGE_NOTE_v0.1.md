# PAIM Gate 1 Common Integrity & Semantic-Era Change Note v0.1

## Status and purpose

This note records the bounded controlling-specification change authorized by Issue #129. It is an
on-ramp to the revised [System Record and Decision Integrity Specification](PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md),
[System Architecture](../architecture/PAIM_SYSTEM_ARCHITECTURE_v0.1.md), and
[Behavioral Validation Strategy](../testing/PAIM_SYSTEM_BEHAVIORAL_VALIDATION_STRATEGY_v0.1.md).
Those documents control; this note does not add a fourth contract.

Gate 1 establishes only shared integrity machinery needed by multiple prospective concepts. It
does not activate a new substantive record family, change a current v0.1 command, migrate data, or
authorize implementation.

## What Gate 1 adds

- exact Semantic Contract ID/Version bound per adopting immutable Version/event;
- conditional common authoritative-envelope vocabulary;
- immutable typed exact context sets;
- family-owned selection with common one/absent/conflict mechanics;
- access-filtered, deterministic, non-authoritative read composition;
- hardened effective-at, known-at, and exact Decision-bound reconstruction;
- all-or-nothing semantic-transaction vocabulary with exact replay/idempotency;
- explicit legacy adapter, migration, recovery, access, and no-silent-fallback rules; and
- reusable implementation-independent hard-oracle categories.

## What remains unchanged

Every existing v0.1 record retains its exact identity, Version, checksum, relationships, audit,
name, outcome, and original semantics. Gate 1 does not rename or reinterpret legacy Fitness,
Acceptance/Selection, Role Assignment, Case lifecycle, Trigger/Reassessment, or another existing
fact. Current v0.1 selectors and commands remain governed by their current specifications.

No prospective write begins merely because Gate 1 exists. A later owning contract must explicitly
adopt the common machinery and define its payload, eligibility, accountability/authority,
currentness, coexistence/conflict, access, migration, and transaction semantics.

## Semantic-era compatibility decision

Semantic era is bound per immutable Version/event because a stable Record may have an explicitly
permitted successor under a later contract while its historical Versions retain their earlier
meaning. There is no global era switch and no `newer era wins` rule.

A compatibility adapter is named, versioned, source-labelled, bounded, and read-safe. It may
explain or project a legacy fact but cannot manufacture a prospective fact or become write
authority unless a later substantive specification grants one exact effect. A failed prospective
path never retries as legacy behavior.

Cross-era eligible facts may coexist. The later owning contract must explicitly define whether
they are compatible, conflicting, displaced, or connected by valid supersession/delegation. In the
absence of that rule, incompatible candidates produce explicit conflict.

## Common-versus-substantive ownership

| Gate-1 common machinery | Later owning contract must still define |
|---|---|
| Semantic contract identity and historical interpretation | substantive meaning and allowed cross-era continuity |
| Envelope identity/time/provenance vocabulary | required fields, payload, finalization, and guards |
| Exact typed context-set mechanics | member roles, Case/Configuration coherence, and what the context concerns |
| One/absent/conflict selector shape | exact scope, eligibility, plurality, authority/coordination, and stale treatment |
| Non-authoritative read-composition rules | source families and practitioner meaning |
| Effective-at/known-at reconstruction discipline | the exact links each family must preserve |
| Atomic semantic-transaction mechanics | command guard, intended facts, accountability, authority, and outcome |

Context membership never creates Applicability, responsibility, authority, adequacy, reliance,
materiality, causality, comparability, priority, or Decision. The integrity layer identifies and
protects a fact; it does not make the substantive judgment.

## Gates unresolved at Gate-1 acceptance

- Gate 2: Responsibility kinds and assignment semantics;
- Gate 3: Case continuity statuses and determinations;
- Gate 4: Case Work payload, state, result, and return;
- Gate 5: Planned Review Point and required-review constraints; and
- Gate 6: readiness, assessment adequacy, reliance, and quantitative Value/Risk payloads.

None begins automatically after Gate 1. Gates 1–6 remain one coordinated redesign delivered in
bounded, independently reviewed increments.

## Subsequent gate status

Issue #131 subsequently adopts the Gate-1 machinery for prospective Responsibility, Case Practical
Role Relationship, Responsibility Assignment Basis, and durable Work through
`PAIM_RESPONSIBILITY_AND_CASE_WORK_SPEC_v0.1.md` and the coordinated Roles, Integrity,
Architecture, domain-accountability, and Validation revisions. That bounded Gate-2/4 adoption does
not alter what Gate 1 established, activate a consumer cutover, or begin Gate 3, 5, or 6.

Issue #133 subsequently adopts the same machinery for prospective Case Continuity Status/Event and
Case Continuity Determination, coordinating exact Configuration lineage and Responsibility/Work
no-retarget behavior. That Gate-3 adoption likewise activates no consumer cutover and does not begin
Gate 5, Gate 6, or implementation.

Issue #135 subsequently adopts the machinery for prospective Planned Review Point, Required Review
Constraint, and Review Episode, coordinating attention-only arrival, constraint intersection,
focused review, Decision authority, and dual-time reconstruction. That Gate-5 adoption activates no
consumer cutover and does not begin Gate 6 or implementation.

## Implementation and migration boundary

Gate 1 specifies behavior but makes no domain, schema, migration, code, UI, scheduler,
notification, deployment, analytics, Harborlight, release, or tag change. Before implementation,
the architecture/readiness gate must decide physical module and persistence shape, supported
contract catalog, canonicalization, selectors, transactions, adapters, access enforcement,
upgrade/recovery paths, and hard-oracle tests.

Every supported prior revision requires an explicit upgrade and compatibility path. Upgrade,
rollback, backup/restore, or repair cannot reinterpret a historical fact under the software's
current contract. No bulk rewrite or synthesis is permitted for convenience.

## Review checkpoint

Gate 1 is internally bounded when:

- every prospective fact is interpretable under its own contract;
- no era, timestamp, role, specificity, breadth, permission, storage, or presentation rule invents
  a winner;
- context sets are exact but semantically neutral;
- read compositions are access-filtered, reproducible, traceable, and non-authoritative;
- later knowledge does not contaminate earlier known-at or Decision-bound history;
- semantic transactions preserve separate facts while committing all or none;
- all failure paths leave prior authoritative state unchanged;
- legacy/new coexistence and no silent fallback are explicit; and
- Gate 2–6 payload semantics remain outside Gate 1.
