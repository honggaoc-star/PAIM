# PAIM Increment 9 v0.1 Integrated Validation Plan

## 1. Status and frozen basis

**Status:** frozen before campaign execution or result judgment

**Authorized by:** GitHub Issue #69

**Starting checkpoint:** `main` at
`62c5d807c2cfec4d13c0f4c9d4f15280511327db` (merged PR #68)

**Campaign branch:** `validation/increment-9-v0-1-release-gate`

This plan freezes the bounded Increment 9 campaign. Later result evidence may record an execution
deviation or a validation-driven correction, but must not silently change this claim, denominator,
oracle, pathway, finding-classification rule, or release criterion.

**Runtime reconciliation note:** Issue #75 reconciles execution onto accepted `main` at
`8fa187857d404242568dd24f0abac4b2995f9b6d`. The controlling runtime is CPython `>=3.12,<3.13`,
with CPython `3.12.13` as the exact reference interpreter and `uv==0.12.5`. This execution note does
not alter the frozen claim, pathways, oracles, practitioner protocol, denominator, or verdict rule.

## 2. Controlling sources and precedence

The campaign applies, in descending precedence for this scope:

1. current governing specifications under `docs/system/specifications/`;
2. `../../engineering/PAIM_V0_1_RELEASE_SCOPE_DECISION_IRR_009_IRR_014_v0.1.md`;
3. `../../engineering/PAIM_IMPLEMENTATION_SEQUENCE_AND_P1_GATES_v0.1.md`;
4. `../../engineering/PAIM_PLATFORM_ARCHITECTURE_v0.1.md`;
5. `PAIM_SYSTEM_BEHAVIORAL_VALIDATION_STRATEGY_v0.1.md`;
6. `PAIM_CODEX_IMPLEMENTATION_READINESS_REVIEW_v0.1.md` for historical finding provenance;
7. `../../engineering/PAIM_INCREMENT_8_OPERATIONAL_READINESS_ASSESSMENT_v0.1.md`;
8. `../../operations/PAIM_LOCAL_OPERATIONAL_APPLICATION_v0.1.md`; and
9. implementation, migrations, tests, reports/exports, and operational/recovery facilities at the
   starting checkpoint.

Historical findings remain historical. No result may rewrite them as though later authority existed
at their original checkpoint.

## 3. Frozen v0.1 claim under test

> **PAIM v0.1 is a complete functional local governed PAIM application for the implemented
> management lifecycle. It supports authenticated local operation, provenance-preserving
> manual/external intake, access segmentation, recovery, and explicit degraded behavior. The
> lifecycle includes Case and Configuration governance; Evidence and Authority; independent Value
> and Risk inputs; Integration, Boundary, Decision, and Authorization; Intervention, Activation,
> and Learning; explicit-event Reassessment and restrictive interim operation; and source-traceable
> Management Register outputs.**
>
> **PAIM v0.1 does not provide first-class Observation persistence or continuous telemetry
> automation, and it does not infer operating-state strength, breadth, severity, ranking, priority,
> or escalation. Those capabilities remain semantically undesigned post-v0.1 extensions.
> Unsupported requests are explicit and fail closed.**

The campaign may validate only this claim. Product polish, live providers, cloud/distributed/HA or
multi-tenant infrastructure, generic workflow, Observation semantics, and operating-state relation
semantics are outside it.

## 4. Fixed status and completion denominator

- PAIM v0.1 scope is complete.
- The campaign begins at approximately 92% against the accepted bounded
  complete-functional-v0.1 denominator.
- IRR-009 semantic/design status is `OPEN — SEMANTICS UNDESIGNED`; bounded-v0.1 product-gate
  status is `CLOSED BY DESIGN — OUTSIDE V0.1 CLAIM`.
- IRR-014 semantic/design status is `OPEN — SEMANTICS UNDESIGNED`; bounded-v0.1 product-gate
  status is `CLOSED BY DESIGN — OUTSIDE V0.1 CLAIM`.
- The remaining denominator components are integrated/practitioner validation and final
  traceability/release evidence.
- Only a fully passing campaign permits 100% and a release verdict.

## 5. Execution identity and evidence discipline

The result artifact must retain:

- source commit before campaign changes and final source commit;
- Python, uv, application, Alembic-head, and schema identities;
- exact command and suite identity with pass/fail/count/duration where available;
- stable scenario and fixture IDs from this plan;
- relevant checksums, manifests, revision IDs, counts, and bounded reason codes;
- practitioner observations and exact finding classifications; and
- clean-tree and diff-integrity evidence.

Machine usernames, home paths, tokens, credential values, payload bodies, and unnecessary machine
identifiers must not be retained. Temporary databases and operational output remain outside Git.

## 6. Gateway practitioner pathways

All pathway evidence must traverse `OperationalApplication` authentication, prospective session
validation, software-access checks, and `run_command`/typed operational methods. Service-only setup
is not sufficient pathway evidence.

### I9-P1 — Case to authorized operation

One structured walkthrough must prove:

1. exact principal-to-Actor resolution and bounded access;
2. Case and governing Configuration establishment;
3. Evidence/Authority provenance and Applicability boundaries;
4. independent Value/Risk intake, acceptance/selection/freeze, and handoff;
5. Integration and uncertainty treatment;
6. finalized immutable Boundary;
7. proposed then authorized Decision with exact Authorization Basis;
8. Intervention Obligation, Completion Result, and accountable Completion Acceptance;
9. exact prerequisite evaluation and explicit Activation Authorization;
10. target operation only after every guard passes;
11. Learning linkage without automatic Decision change; and
12. deterministic reconstruction of the exact authoritative basis.

### I9-P2 — Trigger to completed Reassessment

One structured walkthrough must prove:

1. exact manual/external source occurrence to proposed intake;
2. explicit promotion to Trigger without Observation;
3. Trigger Determination, identity-only replay, and mismatch behavior;
4. Reassessment membership, coverage, accountability, concurrency, and overlap conflict;
5. exact-scope restrictive disposition intersection;
6. affected-scope-only suspension for indeterminate combined effect;
7. no operating-state rank or strongest-state inference;
8. exactly one completion outcome;
9. no-lost-trigger coverage and longitudinal history; and
10. effective-time and knowledge-time reconstruction.

### I9-P3 — Multi-Case Register to owning-domain action

One structured walkthrough must prove:

1. deterministic exact-source Register derivation and current/conflict/informational/historical/
   stale behavior;
2. exact Shared Dependency identity/equivalence;
3. access-filtered cross-Case views with no hidden identifiers, facts, or counts;
4. descriptive aggregation with no transfer of authority, applicability, satisfaction, outcome, or
   closure;
5. no semantic/AI similarity as authority and no universal score/presentation-derived priority;
6. contextual launch returning to the exact owning-domain command;
7. generic Register resolution remaining unavailable; and
8. deterministic report/export/notification manifest reconstruction.

## 7. Release-blocking excluded-boundary oracles

### I9-B1 — IRR-009 Observation boundary

The campaign must prove:

1. first-class Observation persistence/automation requests fail explicitly;
2. telemetry/log/metric/alert/intake arrival creates no Evidence, Trigger, Register attention, or
   substantive authority automatically;
3. exact external occurrence → proposed provenance-preserving intake → explicit practitioner
   promotion → Trigger succeeds without Observation;
4. exact replay identity, not provider/text/time/category similarity, controls idempotency; and
5. reports, exports, notifications, health, and operational counters make no continuous-monitoring
   claim.

### I9-B2 — IRR-014 operating-state boundary

The campaign must prove:

1. exact operating-state identity is preserved/displayed with no rank;
2. enum order, label, color, numeric code, queue order, recency, notification frequency, and workflow
   position create no strength, severity, breadth, priority, or escalation meaning;
3. deterministic exact-scope restrictive intersection applies every explicit restriction;
4. indeterminate combined effect suspends only the affected scope; and
5. report/export/notification output makes no ranked-state or inferred-escalation claim.

Failure of I9-B1 or I9-B2 blocks release.

## 8. Integrated validation matrix

| Evidence family | Frozen minimum |
|---|---|
| I9-RG — regression | `uv lock --check`; full locked pytest; each focused Increment 1–8 file/family; focused Increment 9 suite; Ruff format/lint; strict mypy. |
| I9-HO — hard behavioral oracles | Every in-claim hard oracle applicable to the three pathways; B1/B2 substitute fail-closed evidence for excluded positive semantics. |
| I9-MI — metamorphic/invariance | Principal/access; Case/Configuration Version; Evidence/Authority Version/Applicability; Value/Risk selection; Decision/Boundary/authority; Intervention prerequisite/acceptance; Trigger replay/knowledge; Reassessment scope/membership; projection watermark/rule Version; backup checksum/schema; presentation invariance. |
| I9-SA — security/access | Bad/unmapped/disabled identity; administrator is not substantive authority; Case/Configuration segmentation; Register/report/export non-leakage; bounded protected-source indicators; secret/config/audit/log/output scan. |
| I9-RD — recovery/durability | SQLite-safe backup; separate restore; checksum/manifest/schema/integrity/FK; authoritative/Register reconstruction; tamper/incompatibility rejection; restart preservation. |
| I9-DO — degraded operation | Authentication/access unavailable; database/integrity unavailable; required authority/proof unavailable; intake quarantine; delivery retry; stale Register; backup failure; restore rejection; no fabricated success or broadened authority. |
| I9-DT — dual-time/history | Representative correction, supersession, withdrawal, expiry, revocation, effective-time, and knowledge-time behavior across the three pathways without historical rewrite. |
| I9-SC — schema/migration | Empty database to head; supported prior revision `0007_increment_7` to head; programmatic tables/constraints/indexes/triggers/FK enforcement. |
| I9-OP — operational evidence | Application/schema/suite identity; manifests/checksums; audit/counters; exact scenario mapping; final commit and clean-tree basis. |

## 9. Required command set

The campaign must execute and report at minimum:

```text
uv lock --check
uv run --locked pytest
uv run --locked pytest tests/contract tests/unit/test_identity_and_immutability.py tests/unit/test_time_and_selection.py tests/integration/test_transactions_idempotency_and_audit.py
uv run --locked pytest tests/integration/test_increment_2_foundation.py
uv run --locked pytest tests/integration/test_increment_3_foundation.py
uv run --locked pytest tests/integration/test_increment_4_foundation.py
uv run --locked pytest tests/integration/test_increment_5_intervention_learning.py
uv run --locked pytest tests/integration/test_increment_6_reassessment.py
uv run --locked pytest tests/integration/test_increment_7_management_register.py
uv run --locked pytest tests/integration/test_increment_8_operational.py tests/unit/test_increment_8_configuration_cli.py
uv run --locked pytest tests/integration/test_increment_9_validation.py
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked mypy src/paim
```

Alembic/schema, backup/restore/rebuild, security/leakage, and `git diff --check` evidence must also be
run explicitly or through named focused tests whose assertions and output identify the drill.

## 10. Practitioner-study protocol

The validating practitioner may perform all three walkthroughs, but each is independent and uses a
separate task objective, starting fixture, and observation record. For I9-P1, I9-P2, and I9-P3 the
results must capture:

1. task objective;
2. starting state/fixture;
3. expected semantic checkpoints;
4. observed gateway/operator actions;
5. result;
6. confusion/friction;
7. exactly one finding classification where a finding exists;
8. release severity; and
9. remediation disposition.

The only permitted finding classifications are:

- `RELEASE-BLOCKING SEMANTIC FAILURE`;
- `RELEASE-BLOCKING OPERATIONAL/SECURITY FAILURE`;
- `NON-BLOCKING USABILITY/DOCUMENTATION DEFECT`;
- `POST-V0.1 ENHANCEMENT`; or
- `EXPECTED V0.1 BOUNDARY — PASS`.

Practitioner preference cannot change semantics. Usability success cannot cure semantic failure,
and deliberate governance friction is not itself a semantic defect.

## 11. Pass, remediation, and stop rules

- A hard oracle passes only on exact observable evidence; absence of a failing example is
  insufficient.
- Any semantic regression, access leakage, authority broadening, recovery corruption, fabricated
  degraded success, lost history, or B1/B2 failure blocks release.
- Validation-driven correction is permitted only when it restores already-governing v0.1 behavior,
  test accuracy, security/recovery integrity, operator wording, or release traceability.
- A defect needing new semantics, record families, authority policy, Observation design, or state
  relation design produces `PAIM V0.1 NOT RELEASED — HUMAN DESIGN DECISION REQUIRED`; expansion
  stops.
- A correctable defect must be documented, corrected narrowly, and have focused plus full regression
  evidence rerun.
- No release verdict is written before all evidence families and practitioner walkthroughs are
  classified.

## 12. Final traceability and verdict rule

The release-gate decision must map every in-claim P1 capability to accepted specification,
implementation increment, and passing validation. It must separately retain the two-dimensional
IRR-009/014 status and direct B1/B2 evidence, all three pathway verdicts, regression/security/access/
recovery/degraded/history evidence, practitioner classifications, residual limitations, and final
source/clean-tree basis.

The final artifact must end with exactly one verdict:

- **PAIM V0.1 RELEASED — BOUNDED CLAIM VALIDATED**
- **PAIM V0.1 NOT RELEASED — RELEASE-BLOCKING DEFECTS REMAIN**
- **PAIM V0.1 NOT RELEASED — HUMAN DESIGN DECISION REQUIRED**

Only the first verdict permits 100% completion against the fixed bounded denominator. This plan,
its execution, and a draft PR do not themselves declare release.
