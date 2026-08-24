# PAIM Normative Migration & Compatibility Assessment

## Purpose and immutable baselines

This assessment defines how a later implementation could move prospectively toward the Issue #127
target without rewriting history. It performs no migration.

The following remain immutable:

- the released `v0.1.0` tag and its source semantics;
- every existing authoritative Record, Version, status event, relationship, audit fact, effective
  time, recorded time, and original meaning;
- existing databases unless a separately authorized, tested migration creates additive structures;
- the historical Increment 9 evidence; and
- the Harborlight reference content, fixture, and live owner-review state.

New contracts may supersede old operational paths prospectively. They must never claim that legacy
records meant something they did not.

## Migration principles

1. **Add, do not recast.** New record families and links are additive. No legacy row is rewritten
   into a new concept.
2. **Declare semantic eras.** Queries and audit identify the governing contract/version for each
   fact and action.
3. **Adapt explicitly.** A compatibility adapter is per obligation/family, not a universal string
   mapping.
4. **Fail closed across eras.** Missing context, competing old/new candidates, or ambiguous mapping
   produces absence/conflict.
5. **Cut over prospectively.** New writes switch only after accepted specifications, migration,
   production commands, hard oracles, and rollback evidence exist.
6. **Preserve reconstruction.** Effective-time and known-at queries return the facts PAIM knew under
   the contract in effect at that time.

## Existing Role Assignments

Legacy Role Assignment Versions retain their actor/function, free-form role, one typed target,
Case context, accountable flag, compatibility key, delegation, interval, status, source, and
history. They remain the authoritative basis for historical acts that cited them.

The target Responsibility family is not populated by mechanically renaming all Role Assignments.
Many legacy assignments lack exact obligation kind, purpose/use, assessed scope, multi-Version
context, and assignment basis. Automatic conversion would fabricate meaning.

### Compatibility adapter

For each legacy-supported obligation, a revised specification may define an explicit adapter that:

- names the exact eligible legacy role/function values;
- reconstructs only context already established by the governing record/action;
- retains the exact Role Assignment Version as legacy provenance;
- applies the original effective interval/delegation/currentness rules;
- returns one eligible legacy basis, vacancy, or conflict; and
- never makes the adapter output a reusable Responsibility for a different obligation.

After a declared cutoff, new assignments use controlled Responsibility. During overlap, the
selector must define whether one new Responsibility supersedes an exact legacy assignment. Without
an explicit relationship, incompatible legacy/new results are conflict; recency or new-model
preference does not select a winner.

## `Applicability Owner`

`Applicability Owner` remains a legacy compatibility label used by the current browser path. It is
not promoted to practical role or canonical Responsibility kind.

Historical Applicability results keep their cited assignments. Existing operational behavior may
continue through the exact old contract until cutover. The adapter may evaluate that label only for
the same legacy Applicability action and target set. It cannot infer Evidence, Input, purpose, or
assessed scope beyond facts already bound by the action.

New assignments after cutover use `JUDGE_EVIDENCE_APPLICABILITY` Responsibility with the complete
exact obligation context. The preserved Harborlight vacancy is not filled or reclassified by this
design.

## Practical roles and participants

No practical-role relationship is backfilled from Case Owner, Value/Risk Evaluator, access,
authorship, or historical action. Those signals can appear as separately labeled historical
relationships in a read view, but cannot pretend that the organization assigned Case Coordinator,
Assessor, or Reviewer.

Organizations may prospectively establish Case Practical Role Relationships after implementation.
Participant lists before that point remain derived from exact legacy sources with source labels.

## Existing Value/Risk readiness, Fitness, and Selection

Every current fact remains authoritative:

- producer `ready` events;
- immutable Input Versions and freeze events;
- Fitness determinations and their exact material-Evidence basis;
- lane Acceptance/Selection Versions and candidate dispositions;
- refresh, withdrawal, correction, and supersession history; and
- independent Value and Risk selection.

The proposed `Finish assessment`, neutral assessment-adequacy, and reliance-designation language is
prospective. It does not globally rename `Fitness`, reinterpret its historical outcomes, combine
old events, or rename stored Acceptance/Selection records. Authorized history always retains each
legacy term, exact basis, and original semantic-era meaning; a compatibility read may explain the
corresponding practitioner consequence without asserting that a legacy Fitness fact is a new
adequacy determination.

No existing one-candidate acceptance is considered automatic and no missing adequacy or reliance
fact is synthesized. Prospective adequacy uses its own neutral three-outcome contract and explicit
limitations. A new atomic one-candidate review action, if accepted, applies only to new commands
with separate exact adequacy-review and reliance Responsibilities and all-or-nothing guards. Legacy
Fitness and Acceptance/Selection remain independently reconstructable.

## Existing quantitative and qualitative Value/Risk content

Existing Input content, Evidence, Learning, measures, estimates, assumptions, and provenance retain
their current representation and meaning. Migration must not parse prose or numeric-looking values
into new typed quantitative claims, infer units/periods/baselines, convert qualitative conclusions
to ratings, or synthesize observations, targets, thresholds, causality, ROI, or Risk scores.

After a coordinated cutover, new typed claims may be created prospectively through governed
production paths. A legacy fact may be cited as exact provenance and, only through an explicit
accountable new act, represented in the new contract with its original source, limitations, and
semantic-era relationship intact. The original record is never rewritten. Absence of a legacy
number does not become an inadequacy finding, and presence of a number does not establish
Applicability, adequacy, materiality, comparability, or authority.

Compatibility reads label legacy content as legacy rather than pretending it satisfies the new
context contract. Expected/target values and later observations remain temporally separate. No
upgrade calculates a universal Value score, Risk score, net score, ROI, ranking, causal conclusion,
or Decision-quality judgment.

## Existing Case lifecycle and Decisions

Legacy Case lifecycle Transition Events remain valid and current runtime selection continues until
coordinated specification/code cutover. They are not rewritten as `OPEN`, `CLOSED`, or
`SUPERSEDED` target-model events.

A compatibility read composes:

- the original lifecycle phase under its source contract;
- current subordinate Decision, operation, Intervention, Learning, and Reassessment facts; and
- the proposed practitioner explanation.

Any future continuity-status initialization must use an explicit migration determination/rule that
does not infer closure or operation from one legacy phase. Legacy `SUPERSEDED` can map only because
it already retains a named successor and terminal meaning; every other mapping needs exact guards
and migration evidence.

Existing Decisions, Confirmations, successors, Boundaries, and Authorization Bases are untouched.

## Existing Trigger and Reassessment records

Existing scheduled-review Triggers remain Triggers under their original contract. They are not
retroactively converted into Review Points. Their Trigger Determinations, Memberships, Trigger
Sets, coverage, Reassessments, coordination, Interim Operating Dispositions, Confirmations, and
successor Decisions remain unchanged.

After cutover:

- new Review Points create only derived due attention;
- a practitioner-started review may establish a new exact Trigger sourced from that Review Point;
- existing event-driven Trigger behavior continues; and
- no source is deduplicated across old/new eras by text, date, or inferred similarity.

An old future scheduled Trigger may be retained to completion or explicitly superseded by a new
Review Point/Trigger relationship under a separately specified migration command. It is never
silently deleted.

## Existing Intervention and Learning records

Intervention Owner, Completion Acceptor, Learning owner, due/review dates, results, and histories
retain their existing semantics. Historical ownership is not converted into Responsibility.

Prospectively, new exact Responsibilities may govern performance, Completion Acceptance, or
Learning evidence work. Existing Intervention/Learning records can be linked to new Work only for
new coordination needs; Work cannot recreate or complete their results. Learning target dates may
coexist with a Case-level Review Point and do not become required-review constraints without an
applicable governing source.

## Harborlight preservation

The Harborlight Scenario-A content and current fixture/live owner-review state receive:

- no new Responsibility or practical-role relationship;
- no legacy-role rewrite;
- no Work Item;
- no Review Point or required-review constraint;
- no readiness or Selection change; and
- no Case continuity transition.

The current Applicability responsibility vacancy remains evidence for future implementation tests.
A later authorized exercise must use production migration/setup paths and record new facts
prospectively rather than repair history.

## Database and API compatibility strategy

A later implementation should use additive migrations:

1. add new tables/constraints/indexes and semantic contract-version identifiers;
2. retain all legacy tables and foreign keys required for historical reads;
3. implement new typed ports/commands without changing legacy command meaning;
4. add per-family compatibility selectors returning source era and exact basis;
5. dual-read before cutover; avoid dual-write unless one atomic command explicitly creates both
   records for compatibility and proves no semantic duplication;
6. cut new writes to new contracts by explicit application version/migration state; and
7. validate upgrade from empty DB and every supported prior revision, rollback/recovery, foreign
   keys, indexes, triggers, point-in-time reads, and no-mutation failure paths.

API/read models should preserve legacy identity and source terminology in authorized history while
ordinary practitioner presentation may translate meaning. Exports must not flatten old and new
facts into an indistinguishable row.

## Compatibility risks and required oracles

Hard-oracle coverage must prove:

- legacy historical acts resolve against the exact original Role Assignment Version;
- ambiguous Role Assignment cannot become a new Responsibility;
- legacy/new accountable overlap produces conflict absent explicit supersession;
- `Applicability Owner` is accepted only on the bounded legacy path;
- no practical role is inferred from access or old role strings;
- no legacy readiness/Fitness/Selection fact is combined, invented, or reordered;
- no legacy numeric/prose content is parsed into a typed claim, inferred unit/context, score,
  causal conclusion, or retrospective inadequacy;
- old scheduled Triggers remain reconstructable and are not auto-converted;
- new Review Point arrival creates no Trigger/domain mutation;
- legacy lifecycle and target continuity views both reconstruct without hindsight contamination;
- Harborlight record counts and semantic digest remain unchanged by documentation/design work; and
- v0.1.0 source and release evidence remain unchanged.

## Cutover gate

No cutover occurs until coordinated specifications, architecture, migrations, commands, read-side
adapters, automated tests, operational upgrade/recovery evidence, and an explicit owner acceptance
issue all pass. UI redesign follows the stable production capability; it cannot be the migration
mechanism.
