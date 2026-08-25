# PAIM Migration / Semantic-Era Cutover Plan

## Decision and invariant

Use an additive, forward-only, per-family/per-consumer cutover from the current Alembic head
`0008_increment_8`. Preserve every v0.1 row and meaning. No bulk semantic reinterpretation,
synthetic backfill, or “new table empty, therefore use legacy” fallback is permitted.

This plan does not execute a migration. Revision names below are proposed implementation slices,
not committed Alembic identifiers.

## Supported starting points

Gate-8 implementation must support and test:

1. a fresh empty database upgraded through `0001`–`0008` and every new revision to head;
2. an exact released v0.1 database at `0008_increment_8`;
3. each immediately preceding new revision for bounded rolling development/forward repair; and
4. verified backups of supported revisions through restore-to-new-target and forward upgrade.

Direct upgrade from `0001`–`0007` remains the existing Alembic chain through `0008`; new revisions
must not create a second shortcut path. Unknown, dirty, future, or unsupported revisions fail
startup compatibility checks without writing.

## Expand, validate, activate

Each cutover uses three separable operations:

1. **Expand schema** — add tables, indexes, constraints, and immutable triggers. Existing rows and
   consumers remain untouched.
2. **Validate** — check schema inventory, foreign keys, immutable triggers, legacy table counts,
   exact record/version digests, semantic-contract definitions, and adapter fixtures. A failure
   leaves consumer cutover inactive.
3. **Activate consumer** — append an explicit semantic-consumer cutover Version in an
   administrative migration/command authorized by its implementation issue. Application startup
   requires the declared adapter/contract. Missing declaration never triggers fallback.

Schema availability is not semantic adoption. A family begins producing prospective metadata only
after its writer and every required reader pass conformance and its consumer cutover is explicit.

## Proposed migration sequence

| Proposed revision | Additive content | Activation boundary |
|---|---|---|
| `0009_gate7_common_semantics` | semantic-contract registry, Version metadata, exact context sets/members, cutover declarations, append-only triggers/indexes | no domain consumer active |
| `0010_gate8_responsibility_work` | practical-role, Responsibility, Assignment Basis/assignment, Work, result/return tables | new prospective Cases only after Slice A passes |
| `0011_gate8_case_continuity` | prospective Case Continuity Status/Determination and exact Case/Configuration relationship projections; implemented replacement for the earlier proposed `0011_gate7_case_continuity` placeholder | Slice-B-created prospective Cases only; no legacy backfill or phase mapping |
| `0012_gate8_assessment_review` | prospective independent Value/Risk candidate, readiness, adequacy, reliance, dispositions, and exact basis links; implemented replacement for the earlier proposed `0012_gate7_assessment_review` placeholder | prospective Slice-C-created assessments only after both lanes pass; no legacy backfill |
| `0013_gate8_integration_decision_basis` | implemented prospective Integration and Decision Versions, exact relied-chain basis links, authority/Responsibility bindings, authorization and confirmation facts; replaces the proposed `0013_gate7_integration_decision_basis` placeholder | new prospective Integration/Decision only after Slice D passes; no legacy backfill |
| `0014_gate8_continuing_review` | implemented Planned Review Point, Required Review Constraint, explicit event-attention, Review Episode, and exact result-link projections; replaces the proposed `0014_gate7_continuing_review` placeholder | prospective continuing-review consumers only after Slice E passes; no cadence, scheduler, substantive inference, or legacy backfill |
| `0015_gate8_quantitative_claims` | implemented typed optional quantitative claim, exact source/Applicability links, and explicit comparability basis; replaces the proposed `0015_gate7_quantitative_claims` placeholder | prospective optional-claim consumers only after Slice F passes; no backfill, mandatory quantification, scoring, ranking, or Value-minus-Risk netting |
| `0016_gate7_reconstruction_support` | only indexes/manifests needed by proven read plans; no summary truth | then/now query after Slice G passes |

Exact numbering may change if Gate 8 splits reviews, but dependency order and semantic boundaries may
not. Migrations contain no practitioner or authority judgment.

## Legacy preservation by family

| Legacy source | Preserved meaning | Prospective behavior |
|---|---|---|
| Role Assignment/Version, target, compatibility key, delegation | Exact v0.1 accountability record and history | bounded read adapter may satisfy only an explicitly enumerated legacy obligation/consumer; never creates Responsibility |
| Multi-phase Case lifecycle/status events | Exact v0.1 phase history | displayed as legacy phase/history; never mapped globally to `OPEN`, `CLOSED`, or `SUPERSEDED` |
| Analytical Input finalization and existing readiness-like state | Exact v0.1 input history | remains candidate provenance; no Readiness Event is invented |
| Lane Fitness | Exact v0.1 material-evidence fitness judgment | never treated as Assessment Adequacy |
| Acceptance/Selection and freeze | Exact v0.1 bounded selection/freeze | never treated as Reliance Designation |
| Scheduled-like Trigger, due, Learning, or Work facts | Their exact current family meaning | never treated as Planned Review Point/Required Constraint/Work without explicit prospective record |
| Existing Integration/Boundary/Decision/Confirmation | Exact v0.1 basis and authorization history | reconstructed through legacy adapter; no prospective relied chain is invented |
| Quantities inside analytical JSON/narrative | Original content only | never promoted to typed Quantitative Claim without a new attributable prospective act |

## Per-family and per-consumer cutover order

1. Register common prospective contracts and canonicalization version; activate no consumers.
2. Enable Responsibility/Work writers for deliberately created prospective contexts; legacy Role
   queries remain available only to legacy consumers.
3. Enable prospective continuity for new Cases created through the natural open-Case command.
4. Enable Finish/Adequacy/Reliance for new prospective lane candidates. Cut over both lanes under
   the same release so Value and Risk capability stays symmetric, while their records remain
   independent.
5. Enable prospective Integration/Decision only after it can require exact prospective relied
   chains; legacy Decisions remain read/reconstructable through their adapter.
6. Enable continuing-review/timing for prospective Case/Decision contexts.
7. Enable optional Quantitative Claims and exact comparisons.
8. Enable complete current-position and then/now compositions only after every included family has
   an explicit source adapter and access oracle.

No consumer may accept “either prospective or whatever legacy row looks current.” It accepts a
declared semantic contract or calls a named legacy adapter.

## Application compatibility behavior

At startup the application verifies:

- exact Alembic head expected by the binary;
- required tables, columns, indexes, constraints, foreign keys, and immutable triggers;
- semantic-contract definition digests bundled with the binary;
- every active consumer cutover has exactly one supported contract/adapter;
- canonicalization version support; and
- absence of incomplete migration/cutover markers.

At command time the application includes contract and context identity in preconditions and the
idempotency digest. Mixed semantic eras, unsupported adapter results, missing metadata, or an
ambiguous legacy/prospective basis fail closed before mutation.

## Upgrade procedure

For every supported database:

1. stop PAIM writers and verify repository/runtime/schema identity;
2. run health, SQLite `quick_check`, foreign-key check, and append-only trigger inventory;
3. create an application-consistent SQLite backup and sidecar manifest;
4. record database byte checksum, schema revision, table counts, and a semantic digest over ordered
   legacy record/version/relationship/status/audit identities and content hashes;
5. restore the backup to a disposable target and verify it before touching the active file;
6. execute reviewed Alembic upgrade once;
7. verify new schema inventory and repeat all integrity/digest checks;
8. run adapter and cross-era read oracles against the upgraded copy or approved staging copy;
9. activate only the separately authorized consumers for that release; and
10. retain backup/manifest and publish the new health/schema evidence.

Migration scripts never read browser session state, infer Actor/Responsibility, or synthesize a
domain outcome.

## Recovery and rollback

Prefer forward repair after a released additive migration. A down migration is allowed only when
the affected prospective tables are provably empty, no consumer cutover was activated, and the
downgrade preserves every authoritative and audit fact. Once prospective writes exist, dropping or
rewriting them is prohibited.

If validation fails before activation, stop with the expanded schema inactive and issue a forward
corrective revision. If the active database is damaged or migration validation cannot establish
integrity, leave it untouched, restore the verified pre-upgrade backup to a new target, verify the
manifest/checksums/foreign keys/schema, and repoint only through the existing guarded restore
procedure. Never overwrite the sole database during verification.

Replaying commands after restore uses persisted idempotency identities. Payload mismatch remains an
error; replay cannot duplicate authoritative facts.

## Harborlight disposition

The existing Harborlight reference documents, disposable fixtures, and any historical live owner-
review state remain unchanged and legacy. Gate 8 must not migrate them into prospective meaning or
use them as backfill templates.

After the relevant slices are independently accepted, a separate authorized validation issue may
create a fresh disposable prospective Harborlight fixture through production commands. That fixture
must coexist with legacy Harborlight evidence and prove no cross-era reinterpretation or source
mutation.

## Required migration evidence

Every revision and consumer activation must publish:

- empty-to-head and each supported-prior-to-head results;
- exact schema/table/index/constraint/trigger inventory;
- foreign-key enforcement and violation count;
- legacy row counts and semantic digest unchanged;
- prospective metadata completeness for new rows and absence on untouched legacy rows;
- adapter one/absence/conflict and no-silent-fallback results;
- idempotent retry and mismatched-payload rejection;
- backup/restore/forward-repair evidence; and
- `git diff --check`, full regression, Ruff, mypy, and locked dependency results.

## Stop conditions

Stop migration design or execution if any step would require rewriting legacy content, inferring a
prospective fact, making a legacy adapter implicit, weakening a foreign key/immutability guard,
losing an audit/idempotency fact, or using an in-place destructive rollback.
