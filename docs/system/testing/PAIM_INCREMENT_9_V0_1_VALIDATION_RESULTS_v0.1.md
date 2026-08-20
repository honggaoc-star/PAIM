# PAIM Increment 9 v0.1 Validation Results

## 1. Result and evidence identity

**Campaign result:** PASS

**Execution date:** 2026-08-19

**Frozen plan commit:** `90fc285` (`Freeze Increment 9 validation plan`)

**Validated source commit:** `221b7ad3832a0e28b9bf77b4938030fa2b871e8b`

**Starting checkpoint:** `62c5d807c2cfec4d13c0f4c9d4f15280511327db`

**Campaign branch:** `validation/increment-9-v0-1-release-gate`

The campaign executed the frozen bounded claim and denominator in
`PAIM_INCREMENT_9_V0_1_INTEGRATED_VALIDATION_PLAN_v0.1.md`. The tested source commit contains one
validation-driven correction described in §8. No governing PAIM specification was changed.

| Identity | Observed value |
|---|---|
| Application | `paim 0.1.0` |
| Python | `3.14.6` |
| uv | `0.12.5` |
| Alembic | `0008_increment_8 (head)` |
| Full-suite population | 245 tests |
| Local persistence | SQLite with foreign keys enabled |

## 2. Command evidence

Every required command completed successfully against the validated source commit. Test durations
are wall-clock pytest durations and include Windows/SQLite contention from concurrently executing
independent gates.

| Gate | Result |
|---|---|
| `uv lock --check` | PASS — 18 locked packages resolved without lock mutation |
| `uv run --locked pytest` | PASS — 245 passed in 1088.08s |
| Core contract/identity/time/transaction command | PASS — 22 passed in 70.94s |
| Increment 2 focused command | PASS — 17 passed in 108.16s |
| Increment 3 focused command | PASS — 12 passed in 86.40s |
| Increment 4 focused command | PASS — 19 passed in 150.10s |
| Increment 5 focused command | PASS — 21 passed in 173.66s |
| Increment 6 focused command | PASS — 47 passed in 362.04s |
| Increment 7 focused command | PASS — 64 passed in 290.92s |
| Increment 8 focused command | PASS — 22 passed in 179.93s |
| Increment 9 focused command | PASS — 4 passed in 28.92s |
| Migration/schema focused command | PASS — 16 passed in 69.12s |
| `uv run --locked ruff format --check .` | PASS — 108 files formatted |
| `uv run --locked ruff check .` | PASS |
| `uv run --locked mypy src/paim` | PASS — 43 source files |
| `git diff --check` | PASS |
| Tracked-file high-confidence secret pattern scan | PASS — no matches |

The full suite includes the contract, unit, integration, longitudinal-conflict, migration, schema,
security, recovery, degraded-operation, and operational tests. The focused commands were also run
independently; their counts overlap the 245-test full-suite population and are not additive.

## 3. Practitioner walkthrough I9-P1

**Objective:** take one bounded Case from governed Configuration through authorized target operation
and linked Learning using the authenticated local gateway.

**Starting fixture:** a new local database at Alembic head, one enabled principal resolved to one
Actor, no Case or domain records, and only explicit bootstrap/admin access.

**Observed gateway actions and checkpoints:**

1. authenticated principal/Actor resolution and scoped command grants;
2. Case, finalized governing Configuration, typed substantive Roles, and exact histories;
3. Evidence with provenance and exact Configuration-Version Applicability;
4. separate accepted/frozen Value and Risk inputs, preserving their independent histories;
5. Integration, uncertainty classification, immutable Boundary, Decision, and Authorization Basis;
6. Intervention obligation, Completion Result, accountable Completion Acceptance, prerequisite
   evaluation, Activation Authorization, and target operation;
7. decision-specific Learning; and
8. reconstruction of the exact Evidence, analytical-input, Decision, Intervention, and audit basis.

**Result:** PASS. No software permission substituted for PAIM authority; no Value/Risk collapse,
implicit currentness, or history rewrite occurred.

**Confusion/friction:** none classified. The pathway intentionally requires several explicit
governance records; this was consistent with the frozen claim.

**Finding:** none.

## 4. Practitioner walkthrough I9-P2

**Objective:** take an exact external occurrence through explicit Trigger promotion, accountable
determination, bounded concurrent Reassessment, restrictive interim operation, and completed
Reassessment.

**Starting fixture:** a separately established authorized Decision/Configuration context with
Trigger Determiner, Reassessment Owner, and Reassessment Coordination Authority assignments.

**Observed gateway actions and checkpoints:**

1. an external occurrence entered as non-authoritative proposed intake;
2. exact replay returned the same intake identity, while a similar distinct occurrence retained a
   distinct identity;
3. explicit practitioner promotion created the Trigger without an Observation Record;
4. Trigger Determination and immutable Reassessment membership established coverage;
5. overlapping Reassessments produced `REASSESSMENT OVERLAP CONFLICT — UNRESOLVED` until an exact,
   accountable coexistence determination existed;
6. advancement to a new Reassessment Version required prospective exact-version coordination
   revalidation;
7. two explicit state identities remained unordered, all explicit restrictions were intersected,
   and only the indeterminate overlapping scope was suspended;
8. Confirmation produced exactly one completed outcome and satisfied the exact Trigger; and
9. histories, provenance, coverage, effective context, and knowledge context remained
   reconstructable.

**Result:** PASS.

**Confusion/friction:** an initial campaign oracle expected overlap to reject Reassessment creation.
The governing contract instead preserves both analyses and blocks affected disposition/completion
until coordination. The oracle was corrected before result judgment; PAIM behavior was unchanged.

**Finding:** none against the product. The explicit-version revalidation is deliberate governance,
not a usability defect.

## 5. Practitioner walkthrough I9-P3

**Objective:** derive a multi-Case Management Register from exact authoritative sources, prove
Shared Dependency grouping and access non-leakage, retain outputs, and launch an exact owning-domain
action.

**Starting fixture:** two Cases and Configurations with separate unresolved Authority Gaps, one
immutable Dependency Candidate Set, one stable Shared Dependency, and one accountable
`EQUIVALENT` determination.

**Observed gateway actions and checkpoints:**

1. the complete view contained both exact Case-local concern entries and one descriptive Shared
   Dependency group;
2. denying access to one Case removed its entry and all identifiers/facts/counts while retaining an
   explicitly access-filtered visible group;
3. grouping preserved Case-local authority, status, applicability, outcome, and closure;
4. JSON/CSV outputs retained manifest checksum, rule Version, effective/knowledge context, and
   access context;
5. local notification delivery retained the exact manifest basis;
6. `ASSIGN_OWNER` returned an authoritative owning-family command contract with the exact source
   Version basis; and
7. generic Register resolution remained unavailable.

**Result:** PASS after the bounded correction in §8.

**Finding F-I9-001:** automatic Register population did not initially resolve an accepted exact
Candidate Set and Equivalence Determination back to its exact source Versions; grouping worked only
when a dependency Version had already been embedded in source content.

**Classification:** `RELEASE-BLOCKING SEMANTIC FAILURE`.

**Release severity:** blocking until corrected and fully regressed.

**Disposition:** CLOSED in validated source commit `221b7ad`. The Register now resolves only current,
exact Candidate Set members through one current `EQUIVALENT` determination to one current exact
Shared Dependency Version. Missing, conflicting, non-equivalent, withdrawn, stale, or inconsistent
bindings establish no group. Source records are not rewritten, and no authority or outcome is
transferred.

## 6. Excluded-boundary results

### I9-B1 — Observation

**Classification:** `EXPECTED V0.1 BOUNDARY — PASS`.

- Observation Record/automation and telemetry-to-Evidence/Trigger/Register capabilities raise
  explicit unsupported-capability results.
- No Observation table or accepted Register source exists.
- Intake arrival creates no substantive Evidence, Trigger, Register concern, or authority.
- Explicit external occurrence → proposed intake → practitioner promotion → Trigger passed.
- Exact replay identity controlled idempotency; similar text/source category did not.
- Outputs, health, and audit made no continuous-monitoring claim.

IRR-009 remains `OPEN — SEMANTICS UNDESIGNED` and its bounded-v0.1 product gate remains
`CLOSED BY DESIGN — OUTSIDE V0.1 CLAIM`.

### I9-B2 — operating-state relation

**Classification:** `EXPECTED V0.1 BOUNDARY — PASS`.

- Ranking and strength-inference capabilities raise explicit unsupported-capability results.
- Exact values `state-a` and `state-z` remained an unordered set; labels and lexical order selected
  no winner.
- Structured allowed actions and required controls were intersected by exact scope.
- Indeterminate combined state effect suspended only the overlapping scope.
- Register and output contracts exposed no rank, severity, priority, or inferred escalation.

IRR-014 remains `OPEN — SEMANTICS UNDESIGNED` and its bounded-v0.1 product gate remains
`CLOSED BY DESIGN — OUTSIDE V0.1 CLAIM`.

## 7. Cross-cutting evidence

| Family | Result and retained evidence |
|---|---|
| Security/access | PASS — bad authentication rejected; principal remained Actor-bound; permission remained distinct from substantive authority; Case/Configuration denial removed hidden Register identifiers, facts, and counts; audit details contained no credential-field material. |
| Recovery/durability | PASS — online backup, checksum/manifest/table counts, separate restore, authentication and history after restart, integrity/readiness, tamper rejection, and incompatible-revision rejection. |
| Degraded operation | PASS — missing spool produced explicit `DEGRADED` readiness without loss or fabricated delivery; unavailable/unsupported semantic capabilities failed closed. Existing Increment 8 hard oracles cover quarantine, retry, stale projections, backup failure, and access/database failures. |
| Dual time/history | PASS — immutable exact Versions, current-selection conflict, correction/supersession/withdrawal/expiry/revocation suites, exact Reassessment Version revalidation, Trigger coverage history, and Register effective/knowledge/rule/watermark basis. |
| Schema/migration | PASS — empty SQLite database to `0008_increment_8`; each supported prior revision through head including `0007_increment_7`; expected tables, constraints, indexes, append-only triggers, and foreign-key enforcement. |
| Output/rebuild | PASS — deterministic source-selected Register, checksummed manifest, JSON/CSV reconstruction basis, delivery intent/attempt, backup verification, and access-context enforcement. |
| Boundary discipline | PASS — no Increment 9 schema or new semantic family; no Observation approximation; no operating-state ordering; no generic Register resolution. |

## 8. Validation-driven change control

The campaign made only these bounded changes after the plan freeze:

1. added gateway-level Increment 9 hard-oracle walkthrough tests;
2. parameterized existing test builders so the walkthroughs use the actual
   `OperationalApplication` service and authenticated Actor instead of creating test-only parallel
   services/Actors; and
3. corrected F-I9-001 by deriving Shared Dependency bindings from already-governing exact Candidate
   Set and Equivalence records.

The correction introduced no new record family, schema, authority policy, source mutation,
semantic matching, implicit winner, cross-Case authority, Observation behavior, or state relation.
Focused Increment 7/8/9 gates, schema tests, static checks, and the full 245-test suite all passed
after the correction.

## 9. Residual limitations and result

The released bounded claim excludes first-class Observation persistence, continuous telemetry
automation, operating-state ranking/strength/breadth/severity/priority/escalation inference, live
provider adapters, distributed/cloud/HA or multi-tenant topology, a polished browser/mobile UI,
and generic workflow/Register resolution. These are post-v0.1 extensions, not hidden failures.

No release-blocking defect remains in the frozen v0.1 claim. The campaign supports 100% completion
against the fixed bounded complete-functional-v0.1 denominator and the release verdict recorded in
`../../engineering/PAIM_V0_1_RELEASE_GATE_DECISION_v0.1.md`.
