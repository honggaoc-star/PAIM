# PAIM Increment 9 v0.1 Validation Results

## 1. Reconciliation status and evidence identity

**Automated integrated evidence:** PASSED

**Human practitioner walkthroughs:** I9-P1 COMPLETED; I9-P2 AND I9-P3 NOT YET EXECUTED

**Reconciliation date:** 2026-08-20

**Frozen plan commit:** `90fc285` (`Freeze Increment 9 validation plan`)

**Original Increment 9 implementation commit:**
`221b7ad3832a0e28b9bf77b4938030fa2b871e8b`

**CPython 3.12 reconciled source commit:**
`427dec0bbb5f77129e2128c11c0340b56cd2ebcd`

**Accepted runtime starting checkpoint:**
`8fa187857d404242568dd24f0abac4b2995f9b6d` (merged PR #74)

**Campaign branch:** `validation/increment-9-v0-1-release-gate`

Issue #75 reconciled the substantive Increment 9 implementation and F-I9-001 correction onto the
accepted CPython 3.12 runtime baseline. The historical PR #70 commits remain intact and are parents
of the reconciled source commit. No governing specification or database migration changed.

The four automated Increment 9 gateway tests provide integrated behavioral evidence. They do not
constitute human practitioner evidence and do not support a final release verdict.

| Identity | Observed value |
|---|---|
| Application | `paim 0.1.0` |
| Python | `3.12.13` (conda-forge build, 64-bit) |
| SQLite | `3.53.1` |
| uv | `0.12.5` (`210d1f678`) |
| Alembic | `0008_increment_8` (head) |
| Locked packages | 19 |
| Lock SHA-256 | `E8BA6A8F9428C61A475C106745C8B857F2291C4DEA9B366E98EE8C69D2F853C7` |
| Full-suite population | 250 tests |
| Local persistence | SQLite with runtime foreign keys enabled |

Locked direct identities were PAIM `0.1.0`, Alembic `1.19.1`, SQLAlchemy `2.0.52`, uuid6
`2025.0.1`, pytest `9.1.1`, mypy `1.20.2`, and Ruff `0.16.3`.

## 2. Automated command evidence

Every required automated command completed successfully against the reconciled source. Focused
counts overlap the 250-test full-suite population and are not additive.

| Gate | Result |
|---|---|
| `uv lock --check` | PASS — 19 packages resolved without lock mutation |
| locked sync/import smoke | PASS — PAIM imported under Python 3.12.13 / SQLite 3.53.1 |
| `uv run --locked pytest` | PASS — 250 passed in 787.09s |
| Increment 1 contract/identity/time/transaction | PASS — 25 passed in 40.27s |
| Increment 2 focused command | PASS — 17 passed in 63.25s |
| Increment 3 focused command | PASS — 12 passed in 46.73s |
| Increment 4 focused command | PASS — 19 passed in 71.95s |
| Increment 5 focused command | PASS — 21 passed in 85.29s |
| Increment 6 focused command | PASS — 47 passed in 185.86s |
| Increment 7 focused command | PASS — 64 passed in 159.84s |
| Increment 8 focused command | PASS — 24 passed in 103.16s |
| Increment 9 automated command | PASS — 4 passed in 20.35s |
| Migration/schema focused command | PASS — 16 passed in 48.34s |
| Recovery/security/degraded/boundary assurance command | PASS — 9 passed in 38.37s |
| tracked-Python Ruff format check | PASS — 70 files |
| tracked-Python Ruff lint | PASS — 70 files |
| `uv run --locked mypy src/paim` | PASS — 43 source files |
| tracked-source high-confidence secret scan | PASS — no matches |
| `git diff --check` | PASS |

Repository-wide Ruff traversal used the complete tracked-Python file list because inaccessible old,
ignored pytest temporary directories are not repository source. No tracked Python file was omitted.

## 3. Automated integrated pathway evidence

### I9-P1 automated gateway oracle

**Status:** `AUTOMATED INTEGRATED EVIDENCE — PASSED`

The automated gateway oracle traversed authenticated Case/Configuration establishment, exact
Evidence and Authority handling, independent Value/Risk intake and freeze, Integration, Boundary,
Decision and Authorization Basis, Intervention, Completion Acceptance, Activation, Learning, and
authoritative reconstruction. Software access did not substitute for substantive authority, and no
Value/Risk collapse or history rewrite occurred.

### I9-P2 automated gateway oracle

**Status:** `AUTOMATED INTEGRATED EVIDENCE — PASSED`

The automated gateway oracle traversed exact external occurrence intake, explicit Trigger
promotion, accountable determination, Reassessment membership and coverage, overlap conflict,
prospective exact-version coordination, restrictive interim operation, exactly one completion
outcome, no-lost-trigger coverage, and dual-time reconstruction. Exact operating-state identities
remained unordered.

### I9-P3 automated gateway oracle

**Status:** `AUTOMATED INTEGRATED EVIDENCE — PASSED`

The automated gateway oracle derived a multi-Case Register from exact authoritative sources,
validated exact Shared Dependency identity/equivalence, access-filtered hidden data, retained
deterministic output/manifest basis, launched the exact owning-domain command, and kept generic
Register resolution unavailable.

These automated results establish correctness evidence for the pathways. They do not record a
human operator's actions, comprehension, confusion, friction, or usability judgment.

## 4. Human practitioner walkthroughs

### I9-P1 — Case to authorized operation

**Status:** `HUMAN PRACTITIONER WALKTHROUGH — COMPLETED WITH NON-BLOCKING FINDINGS`

**Practitioner:** one human practitioner, completing only the I9-P1 pathway before independent
assessment and before I9-P2.

**Task objective:** Take one PAIM Case from creation through authorized bounded operation and
Learning linkage while preserving the governing Configuration, independent Value/Risk histories,
substantive authority basis, prerequisite and completion evidence, activation history, and exact
knowledge-time reconstruction.

**Starting state/fixture:** A new isolated local study workspace and empty SQLite database were
created from source commit `cd361fe63a0208187b535842c0059c8bb5ebd554` on the campaign branch.
The accepted CPython 3.12.13 environment, SQLite 3.53.1, uv 0.12.5, locked dependency set, and PAIM
import were verified before bootstrap. The walkthrough did not reuse automated-test actors or
fixtures.

**Expected semantic checkpoints:** The walkthrough retained the twelve frozen I9-P1 checkpoints:
exact principal-to-Actor resolution and bounded software access; Case and governing Configuration;
Evidence/Authority provenance and Applicability; independent Value/Risk intake, acceptance,
selection, freeze, and handoff; Integration and uncertainty; finalized Boundary; proposed and
authorized Decision with exact Authorization Basis; Intervention, Completion Result, and accountable
Completion Acceptance; exact prerequisites and explicit Activation Authorization; operation only
after all guards; Learning without automatic Decision change; and deterministic authoritative
reconstruction.

**Observed gateway/operator actions:** The practitioner completed bootstrap and READY health,
created and mapped the practitioner Actor, established bounded access, and created the Case and
governing Configuration. The guided pathway then established Evidence/Authority and Applicability,
independent Value and Risk inputs and accepted frozen selections, Integration and uncertainty
records, a finalized Boundary, a proposed then authorized Decision with exact authority basis, an
Intervention Obligation, Completion Evidence and Result, accountable Completion Acceptance,
prerequisite satisfaction, explicit Activation Authorization, target operation, and a linked
Learning record. Final inspection reported READY health, 225 operational audit facts, no credential
content in audit facts, no Authority Gaps, and the required critical actions for Decision
authorization, completion acceptance, activation authorization, and Learning creation.

**Deterministic reconstruction result:** Reconstruction returned 28 exact Versions. Current Value
and Risk selections were exact, independent, and frozen. At the pre-acceptance knowledge cutoff,
both selection states were `INPUT SELECTION NOT ESTABLISHED`. The authorized Decision reconstructed
exactly; at the pre-authorization cutoff it was `AUTHORIZED DECISION NOT ESTABLISHED`. The Case
lifecycle reconstructed as `decided` before activation and as `operating_observing` afterward.
Learning did not create or alter a Decision.

**Result:** The practitioner reported: “Yes. I ultimately accomplished the objective of taking a
PAIM Case from creation through authorized bounded operation and Learning linkage.” The pathway
completed, but required substantial guidance and several corrections. The practitioner did not
observe a release-blocking semantic failure or a release-blocking operational/security failure.

**Semantic and authority observations:** Once exercised in sequence, the practitioner generally
understood that Value and Risk remained separate; Evidence Applicability and acceptance/freeze were
distinct from the analytical inputs; proposed and authorized Decisions were different states; and
Intervention, Completion Result, accountable Acceptance, prerequisite satisfaction, and Activation
Authorization were separate steps. Learning without automatic Decision change was understandable.
Knowledge-time reconstruction was conceptually clear, though its operational mechanics were less
intuitive. Software permission did not appear to create substantive Decision authority, and
accountable role assignment, Decision authority, completion acceptance authority, and activation
authority remained separate. These distinctions were not all readily discoverable from the current
interface without the guided procedure.

**Confusion/friction and output quality:** The practitioner reported substantial operational
friction from the Git executable path, an unsupported PowerShell API, UTF-8 BOM rejection, quoting
failures, an incorrect verifier expectation, and loss of a required Stage 21 variable. Although the
issues were recoverable without changing PAIM semantics, together they made the walkthrough more
difficult and time-consuming than the underlying management process. Outputs supplied enough exact
information to verify success and record bindings once the practitioner knew what to inspect, but
did not adequately identify the appropriate next practitioner action. The output was therefore
adequate for verification and audit inspection, but not self-guiding.

**Confidence:** The practitioner reported reasonably high confidence that PAIM preserved the
governing Configuration, independent Value/Risk histories, authority basis, authorized Decision,
prerequisites, and activation history. Staged verification and reconstruction materially supported
that confidence. Confidence in the governed behavior was higher than confidence in operating it
without expert guidance.

#### I9-P1-F1 — Practitioner workflow is not sufficiently self-guiding

- **Classification:** `NON-BLOCKING USABILITY/DOCUMENTATION DEFECT`
- **Release severity:** Non-blocking for the bounded v0.1 claim, provided v0.1 is explicitly
  understood as the current local governed application rather than a polished self-service product.
- **Remediation disposition:** Improve practitioner-facing guidance so the required action sequence,
  authority prerequisites, and next steps can be discovered without relying on a separately supplied
  22-stage procedure.

#### I9-P1-F2 — Walkthrough procedure/environment assumptions caused repeated interruptions

- **Classification:** `NON-BLOCKING USABILITY/DOCUMENTATION DEFECT`
- **Release severity:** Non-blocking because the issues were corrected without changing PAIM
  semantics and the pathway ultimately completed.
- **Remediation disposition:** Correct and harden practitioner walkthrough/setup instructions for
  environment prerequisites, PowerShell compatibility, encoding, quoting, verifier expectations,
  and preservation of required variables and state.

The practitioner concluded that the walkthrough increased confidence that PAIM's governance
distinctions are implemented rather than merely documentary. The difference between correct
implementation and easy practitioner operation is material, but for bounded v0.1 was classified as
a usability/documentation issue rather than a governing-model failure.

### I9-P2 — Trigger to completed Reassessment

**Status:** `HUMAN PRACTITIONER WALKTHROUGH — NOT YET EXECUTED`

No human actions or observations are recorded. This walkthrough begins only after I9-P1 is
completed and recorded.

### I9-P3 — Multi-Case Register to owning-domain action

**Status:** `HUMAN PRACTITIONER WALKTHROUGH — NOT YET EXECUTED`

No human actions or observations are recorded. This walkthrough begins only after I9-P2 is
completed and recorded.

Automated test actors are not practitioners. No finding classification, friction statement, or
human pass result will be inferred from the automated evidence.

## 5. F-I9-001 reconciliation

The original Increment 9 campaign found that automatic Register population did not resolve an
accepted exact Candidate Set and Equivalence Determination back to its exact source Versions.
F-I9-001 was classified `RELEASE-BLOCKING SEMANTIC FAILURE` and corrected in `221b7ad`.

The correction remains unchanged after reconciliation. It resolves only current exact Candidate Set
members through one current `EQUIVALENT` determination to one current exact Shared Dependency
Version. Missing, conflicting, non-equivalent, withdrawn, stale, or inconsistent bindings establish
no group. Case-local source records are preserved; no authority, applicability, satisfaction,
outcome, or closure transfers; no semantic/AI similarity matching occurs; and effective-time and
knowledge-time selection remains deterministic.

The full 250-test suite plus the focused Increment 7, Increment 8, and Increment 9 gates passed on
CPython 3.12.13. F-I9-001 therefore remains technically closed at this automated checkpoint; the
later human study may produce separate findings that must be recorded independently.

## 6. Excluded-boundary results

### I9-B1 — IRR-009 Observation boundary

**Automated classification:** `EXPECTED V0.1 BOUNDARY — PASS`

- first-class Observation persistence/automation requests failed explicitly;
- no Observation table or accepted Register source exists;
- intake arrival created no Evidence, Trigger, Register concern, or substantive authority;
- explicit external occurrence to proposed intake to explicit authorized promotion to Trigger
  passed without Observation;
- exact replay identity, not semantic similarity, controlled idempotency; and
- outputs and health behavior made no continuous-monitoring claim.

IRR-009 remains `OPEN — SEMANTICS UNDESIGNED` and `CLOSED BY DESIGN — OUTSIDE V0.1 CLAIM` for the
bounded product gate.

### I9-B2 — IRR-014 operating-state relation boundary

**Automated classification:** `EXPECTED V0.1 BOUNDARY — PASS`

- ranking and strength-inference requests failed explicitly;
- exact operating-state values remained an unordered set;
- labels, lexical order, presentation order, and recency selected no winner;
- explicit restrictions were intersected by exact scope;
- indeterminate combined effect suspended only the affected scope; and
- Register/output contracts exposed no inferred rank, severity, priority, or escalation.

IRR-014 remains `OPEN — SEMANTICS UNDESIGNED` and `CLOSED BY DESIGN — OUTSIDE V0.1 CLAIM` for the
bounded product gate.

## 7. Schema, recovery, security, and repository evidence

The migration/schema gate upgraded an empty database and every supported prior revision, including
`0007_increment_7`, to `0008_increment_8`. A separate fresh-database inventory reported 136 tables,
97 check constraints, 429 foreign keys, 58 indexes, 268 triggers, `PRAGMA foreign_keys = 1`, and
`PRAGMA quick_check = ok`. Increment 9 introduced no migration.

The focused assurance gate passed application-consistent backup, checksum/manifest evidence,
separate restore, restart/authentication/history reconstruction, tamper rejection, incompatible
revision rejection, authentication failures, hidden-Case identifier/fact/count non-leakage,
configuration/CLI secret hygiene, database-unavailable behavior, explicit degraded readiness, and
the excluded-boundary failures. No degraded state fabricated semantic success or broadened
authority.

## 8. Reconciliation change control

The reconciled branch preserves:

1. the frozen Increment 9 plan;
2. all four automated Increment 9 gateway hard-oracle tests;
3. the bounded F-I9-001 correction and regression coverage;
4. security/access/recovery/degraded/boundary evidence;
5. IRR-009 and IRR-014 two-dimensional status; and
6. the bounded v0.1 claim and non-goals.

Issue #75 changed no governing specification, schema migration, record family, authority policy,
Observation semantics, operating-state relation, or product feature. It merged the accepted CPython
3.12 baseline into the existing PR #70 branch, reran the complete automated gate, and corrected
stale evidence/release wording.

## 9. Remaining release gate

Automated correctness, regression, boundary, security, recovery, degraded-operation, migration, and
static evidence is green. Human I9-P1 evidence is complete with two non-blocking
usability/documentation findings. Human usability/understandability evidence remains absent for
I9-P2 and I9-P3. Therefore PAIM v0.1 validation and release remain pending, completion must remain
below 100%, and no final release verdict is authorized at this checkpoint.

**INCREMENT 9 AUTOMATED EVIDENCE RECONCILED ON CPYTHON 3.12 — HUMAN PRACTITIONER VALIDATION PENDING**
