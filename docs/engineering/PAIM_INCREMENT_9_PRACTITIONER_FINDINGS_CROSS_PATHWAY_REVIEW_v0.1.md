# PAIM Increment 9 Practitioner Findings Cross-Pathway Review v0.1

## 1. Evidence basis

This review implements GitHub Issues #76 and #78. Its controlling practitioner-study evidence is
draft PR #70, reconciled with accepted `main` through validation source commit
`d1bca218f641ef8bef9b2385e96446383ccdb8e8`, especially:

- `docs/system/testing/PAIM_INCREMENT_9_V0_1_VALIDATION_RESULTS_v0.1.md`;
- `docs/engineering/PAIM_V0_1_RELEASE_GATE_DECISION_v0.1.md`;
- the frozen Increment 9 validation plan at commit `90fc285`;
- retained I9-P1, I9-P2, and I9-P3 artifacts and exact practitioner statements; and
- the accepted CPython 3.12 runtime and migration evidence on `main`.

All three human pathways and automated gates are complete in PR #70. The practitioner recorded
eight findings, all classified `NON-BLOCKING USABILITY/DOCUMENTATION DEFECT`, and observed no
release-blocking semantic or operational/security failure. PR #77 supplied the bounded
documentation remediation, and the subsequently completed practitioner confirmation tested the
five properties required by §9. This review preserves every original classification and failed
attempt; it does not rewrite historical evidence.

## 2. Original findings

| Finding | Practitioner classification | Practitioner disposition |
|---|---|---|
| I9-P1-F1 — workflow not sufficiently self-guiding | `NON-BLOCKING USABILITY/DOCUMENTATION DEFECT` | Explain action sequence, authority prerequisites, and next steps |
| I9-P1-F2 — procedure/environment assumptions caused interruptions | `NON-BLOCKING USABILITY/DOCUMENTATION DEFECT` | Harden runtime, PowerShell, encoding, quoting, verifier, and state guidance |
| I9-P2-F1 — tooling too fragile and shell-dependent | `NON-BLOCKING USABILITY/DOCUMENTATION DEFECT` | Use self-contained persisted reconstruction, locked runtime, production modules/enums, stable comparisons |
| I9-P2-F2 — access prerequisites not discoverable | `NON-BLOCKING USABILITY/DOCUMENTATION DEFECT` | Separate command permission from exact Case/Configuration visibility |
| I9-P2-F3 — outputs weak at next-action guidance | `NON-BLOCKING USABILITY/DOCUMENTATION DEFECT` | Explain required next actions, prerequisites, and authority dependencies |
| I9-P3-F1 — Register semantics not sufficiently self-explanatory | `NON-BLOCKING USABILITY/DOCUMENTATION DEFECT` | Explain lifecycle, exact grouping, access filtering, and contextual action |
| I9-P3-F2 — verifier used broad semantic keys | `NON-BLOCKING USABILITY/DOCUMENTATION DEFECT` | Require exact persisted Version identity for temporal reconstruction |
| I9-P3-F3 — self-contained persisted reconstruction improved execution | `NON-BLOCKING USABILITY/DOCUMENTATION DEFECT` | Make that pattern standard and avoid ephemeral shell state |

## 3. Consolidated themes

The evidence supports four themes without erasing the eight original findings:

1. **Workflow and next-action discoverability:** I9-P1-F1, I9-P2-F3, and I9-P3-F1.
2. **Procedure fragility and ephemeral shell state:** I9-P1-F2, I9-P2-F1, and I9-P3-F3.
3. **Access-prerequisite discoverability:** I9-P2-F2.
4. **Exact persisted identity/version discipline:** I9-P3-F2.

Themes 1 and 2 recur across all pathways. Themes 3 and 4 are distinct because confusing access
layers can cause an otherwise valid command to fail, while broad identity selection can produce an
incorrect historical conclusion even when access is valid.

## 4. Root-cause distinction

The completed pathways demonstrated correct governed behavior: Value and Risk remained separate;
authority was not inferred from software permission; exact provenance, histories, and access
boundaries were preserved; Register grouping required exact governed relationships; and excluded
IRR-009/IRR-014 behavior failed closed.

The recurring causes were practitioner procedure, tooling assumptions, and documentation:

- state was carried in ephemeral PowerShell variables instead of durable artifacts;
- some scripts invoked a bare interpreter or imported test helpers;
- PowerShell version, BOM, quoting, and console encoding assumptions were unsafe;
- successful append-only grants or domain commits were followed by verifier failures;
- access guidance omitted exact Case/Configuration visibility prerequisites;
- a temporal verifier selected by broad `question_id` rather than exact Version IDs; and
- exact outputs exposed audit state but did not explain the next owning action.

No evidence supports changing domain semantics, schemas, the access resolver, authority rules, or
the CLI command model for v0.1. A generic workflow engine or inferred next-step engine would exceed
the accepted product boundary.

## 5. Per-finding disposition and traceability

| Finding | Implemented remediation | Direct confirmation evidence | Closure state |
|---|---|---|---|
| I9-P1-F1 | Next-action sequences and authority boundaries in guide §§4–7, 9 | Practitioner correctly named the contextual owning action and its non-inference boundaries without hidden guidance | `CLOSED — DOCUMENTATION REMEDIATION CONFIRMED` |
| I9-P1-F2 | Locked runtime, BOM-free artifacts, stable encoding, stop/reconstruct rules in guide §§2–3, 8–9 | Locked CPython 3.12.13 invocation was clear and succeeded; persisted reconstruction worked without shell identity state | `CLOSED — DOCUMENTATION REMEDIATION CONFIRMED` |
| I9-P2-F1 | Self-contained stages, persisted reconstruction, production-only imports/enums in guide §§2–3 | Practitioner used the locked runtime and persisted context without corrective guidance or cross-stage identity variables | `CLOSED — DOCUMENTATION REMEDIATION CONFIRMED` |
| I9-P2-F2 | Command/read/accountability/authority matrix in guide §4 | Practitioner identified all three exact access prerequisites and distinguished them from accountability and authority | `CLOSED — DOCUMENTATION REMEDIATION CONFIRMED` |
| I9-P2-F3 | Boundary prerequisites and next actions in guide §§5–7, 9 | Practitioner identified `ASSIGN_OWNER` → `commit_role_assignment` and what PAIM must not infer or mutate | `CLOSED — DOCUMENTATION REMEDIATION CONFIRMED` |
| I9-P3-F1 | Register lifecycle, grouping, filtering, and contextual action in guide §7 | Practitioner correctly described the Register action boundary, including no assignment, closure, ranking, priority, or semantic inference | `CLOSED — DOCUMENTATION REMEDIATION CONFIRMED` |
| I9-P3-F2 | Exact persisted Version selection and temporal verification in guide §§2, 8 | Practitioner supplied the exact Record, predecessor Version, and current Version and rejected broad semantic keys | `CLOSED — DOCUMENTATION REMEDIATION CONFIRMED` |
| I9-P3-F3 | Persisted artifacts as continuity authority in guide §§2–3 | Practitioner reconstructed the complete context without cross-stage PowerShell identity variables | `CLOSED — DOCUMENTATION REMEDIATION CONFIRMED` |

Each closure is supported by the original statement, the directly corresponding PR #77
documentation, and the practitioner's actual bounded-confirmation answer. The four consolidated
themes remain the traceability structure; closure does not erase the original findings or residual
v0.1 limitations.

## 6. Remediation implemented and deferred

Implemented in this issue:

1. `docs/operations/PAIM_V0_1_PRACTITIONER_PATHWAYS_v0.1.md`, a durable production-only guide for
   all three pathways;
2. explicit `uv run --locked`, `paim.*`-only, production-enum, UTF-8/BOM, and encoding-stable rules;
3. a self-contained five-part stage contract using persisted configuration/artifacts/database;
4. an access/accountability/authority matrix and exact visibility prerequisites;
5. next-action tables for every major lifecycle boundary and Management Register contextual action;
6. exact persisted identity and temporal reconstruction rules; and
7. links from the existing operator guide and repository README.

Deferred beyond bounded v0.1 remediation:

- browser or richer interactive UI;
- generic workflow/next-step engine;
- new CLI commands solely to duplicate existing typed production commands;
- inferred remediation, authority, ranking, priority, or semantic matching;
- first-class Observation or operating-state relation design; and
- rewriting historical walkthrough transcripts.

No Python source, database migration, governing specification, or executable behavior changes.

## 7. Release-blocking assessment

The practitioner classified every finding as non-blocking and completed all three governed
objectives. Automated and human evidence found no release-blocking semantic or operational/security
failure. The defects materially affected efficiency, discoverability, and independence from expert
guidance, but corrections did not require a semantic or product-behavior change.

Documentation remediation is therefore proportionate for bounded v0.1. The practitioner confirmed
that the consolidated guide made all five targeted properties clear enough to use without
undisclosed corrective instructions. All eight original findings are closed on that bounded basis.
No new release-blocking defect emerged.

## 8. Regression evidence

Issue #78 reran the complete executable release gate because PR #70 also contains the Increment 9
implementation and was reconciled onto newer `main`. The locked CPython 3.12.13 campaign passed
250/250 tests, focused Increment 1–9 gates, 16 migration/schema tests, nine recovery/security/
degraded/boundary tests, Ruff over 70 tracked Python files, strict mypy over 43 source files, the
tracked-source secret scan, and `git diff --check`. Fresh inventory confirmed Alembic
`0008_increment_8`, 136 tables, 97 check constraints, 429 foreign keys, 58 indexes, 268 triggers,
enabled production foreign-key enforcement, zero foreign-key violations, and `quick_check = ok`.

## 9. Bounded human revalidation — completed

The completed confirmation remained limited to the five agreed properties and did not repeat
I9-P1, I9-P2, or I9-P3.

Preparation may reuse a safe existing study database or a disposable fixture. The facilitator
provides only:

- a configuration path;
- the credential environment-variable name and protected value source; and
- one BOM-free JSON context artifact containing exact Case, Configuration, source Record, source
  Version, and current owning-action identities.

The practitioner used only the new guide to:

1. run the locked-runtime/import preflight;
2. reopen the configuration and context artifact without restoring cross-stage shell variables;
3. identify the exact `COMMAND`, `CASE_READ`, and `CONFIGURATION_READ` prerequisites for the stated
   action and distinguish them from accountability and substantive authority;
4. identify which exact Version IDs, not broad semantic keys, control a supplied historical query;
5. follow the relevant pathway table to name the correct next owning action and explain what PAIM
   must not infer or mutate; and
6. run one read-only production health/reconstruction check appropriate to the fixture.

The practitioner reported that all five properties were clear enough to use without undisclosed
corrective instructions. Locked execution used CPython 3.12.13 and reached `READY`. Exact access
prerequisites were correctly separated from accountability and authority; persisted context
replaced shell identity variables; exact Record/Version identities controlled history; and the
contextual owning action and prohibited inferences were correctly identified.

The missing earlier credential in a new shell was classified by the practitioner as expected
ephemeral-secret behavior, not a PAIM defect. A fresh disposable credential was used without
recovering or persisting the old secret. The fixture verifier's tuple/JSON-array mismatch remains
unclassified procedural evidence and is not converted into a finding.

## 10. Residual v0.1 limitations

Even after confirmation, PAIM v0.1 remains a local CLI and typed-gateway application with
documentation-led navigation. It does not provide a polished self-service interface or automatic
workflow guidance. Operators must understand exact Record/Version identity and organizational Role/
authority prerequisites. Unsupported Observation, telemetry automation, operating-state ranking,
semantic dependency matching, and generic Register resolution remain explicit fail-closed
boundaries.

These limitations must appear in release wording. The guide reduces avoidable procedure fragility;
it does not claim to remove every usability cost identified by the practitioner.

## 11. PR #70 and release-gate implications

PR #70 remains draft and unmerged. Issue #78 reconciled it with accepted `main`, preserved all
historical evidence, recorded the bounded confirmation, and closed the eight findings only where
the original statement, remediation, and confirmation directly align. The release-gate artifact is
prepared for independent review; this review does not authorize autonomous merge or post-v0.1 work.
